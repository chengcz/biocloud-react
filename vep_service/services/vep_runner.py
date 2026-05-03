"""VEP Runner Service

Executes VEP (Variant Effect Predictor) command-line tool for variant annotation.
Migrated from backend with NO user_id references.
"""

import asyncio
import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

from config.settings import settings

logger = logging.getLogger(__name__)


def load_species_config() -> dict:
    """
    Load species configuration from YAML file.

    Returns:
        dict: Species configuration with GRCh37 and GRCh38 settings
    """
    config_path = Path(settings.SPECIES_CONFIG_PATH)

    if not config_path.exists():
        logger.warning(f"Species config not found at {config_path}, using defaults")
        return {
            "species": [
                {
                    "name": "GRCh37",
                    "assembly": "GRCh37",
                    "vep_cache_dir": "/data/vep_data/GRCh37",
                    "fasta_file": "/data/vep_data/GRCh37/GRCh37.fa",
                    "enabled": True,
                },
                {
                    "name": "GRCh38",
                    "assembly": "GRCh38",
                    "vep_cache_dir": "/data/vep_data/GRCh38",
                    "fasta_file": "/data/vep_data/GRCh38/GRCh38.fa",
                    "enabled": True,
                },
            ],
            "defaults": {
                "distance": 500,
                "output_format": "json",
            },
        }

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def get_species_config(species_name: str) -> dict:
    """
    Get configuration for a specific species.

    Args:
        species_name: Species name (GRCh37 or GRCh38)

    Returns:
        dict: Species-specific configuration

    Raises:
        ValueError: If species not found or disabled
    """
    config = load_species_config()
    for species in config.get("species", []):
        if species["name"] == species_name:
            if not species.get("enabled", True):
                raise ValueError(f"Species {species_name} is disabled")
            return species

    raise ValueError(f"Species {species_name} not found in configuration")


def build_vep_command(species_config: dict) -> list[str]:
    """
    Build VEP command with appropriate flags.

    Args:
        species_config: Species configuration dict

    Returns:
        list: VEP command arguments
    """
    defaults = load_species_config().get("defaults", {})

    cmd = [
        "vep",
        "--force",
        "--no_stats",
        "--no_progress",
    ]

    if defaults.get("hgvs", True):
        cmd.append("--hgvs")
    if defaults.get("hgvsg", True):
        cmd.append("--hgvsg")
    if defaults.get("symbol", True):
        cmd.append("--symbol")
    if defaults.get("domains", True):
        cmd.append("--domains")
    if defaults.get("protein", True):
        cmd.append("--protein")
    if defaults.get("numbers", True):
        cmd.append("--numbers")

    cmd.extend(["--distance", str(defaults.get("distance", 500))])
    cmd.extend(["--output_format", "json"])

    vep_cache_dir = species_config.get("vep_cache_dir", "")
    if vep_cache_dir and os.path.exists(vep_cache_dir):
        cmd.extend([
            "--dir", vep_cache_dir,
            "--offline",
            "--cache",
            "--refseq",
        ])
    else:
        fasta_file = species_config.get("fasta_file", "")
        if fasta_file:
            cmd.extend(["--fasta", fasta_file])

    return cmd


def generate_variant_input(variants: list[dict[str, Any]]) -> str:
    """
    Generate VCF-style input for VEP from variant list.

    Args:
        variants: List of variant dicts with chrom, pos, ref, alt

    Returns:
        str: VCF-style input string
    """
    rows = []
    for v in variants:
        chrom = v.get("chrom", "")
        pos = str(v.get("pos", 0))
        ref = v.get("ref", "")
        alt = v.get("alt", "")
        row = f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t.\t.\t."
        rows.append(row)

    return "\n".join(rows)


def compute_variant_hash(chrom: str, pos: int, ref: str, alt: str, species: str) -> str:
    """
    Compute unique hash for variant identification.

    Args:
        chrom: Chromosome name
        pos: Position
        ref: Reference allele
        alt: Alternate allele
        species: Species name

    Returns:
        str: SHA256 hash for deduplication
    """
    variant_str = f"{chrom}:{pos}:{ref}:{alt}:{species}"
    return hashlib.sha256(variant_str.encode()).hexdigest()


IMPACT_ORDER = {"high": 0, "moderate": 1, "low": 2, "modifier": 3}


def extract_most_severe_consequence(vep_result: dict) -> dict:
    """
    Extract fields from the most severe transcript consequence.

    Args:
        vep_result: Single VEP annotation result (JSON dict)

    Returns:
        dict: Extracted fields for database columns
    """
    extracted = {
        "consequence": None,
        "codons": None,
        "gene_id": None,
        "gene_symbol": None,
        "transcript_id": None,
        "exon": None,
        "intron": None,
        "hgvsc": None,
        "hgvsp": None,
        "impact": None,
        "biotype": None,
        "protein_id": None,
        "sift_score": None,
        "polyphen_score": None,
        "amino_acids": None,
    }

    # Get most_severe_consequence from top-level
    if "most_severe_consequence" in vep_result:
        extracted["consequence"] = vep_result["most_severe_consequence"]

    # Find most severe transcript consequence
    transcript_consequences = vep_result.get("transcript_consequences", [])
    if not transcript_consequences:
        return extracted

    # Sort by impact (most severe first)
    def get_impact_rank(tc):
        impact = tc.get("impact", "modifier").lower()
        return IMPACT_ORDER.get(impact, 3)

    sorted_consequences = sorted(transcript_consequences, key=get_impact_rank)
    most_severe = sorted_consequences[0]

    # Extract fields from most severe transcript consequence
    extracted["gene_id"] = most_severe.get("gene_id")
    extracted["gene_symbol"] = most_severe.get("gene_symbol")
    extracted["transcript_id"] = most_severe.get("transcript_id")
    extracted["exon"] = most_severe.get("exon")
    extracted["intron"] = most_severe.get("intron")
    extracted["hgvsc"] = most_severe.get("hgvsc")
    extracted["hgvsp"] = most_severe.get("hgvsp")
    extracted["codons"] = most_severe.get("codons")
    extracted["amino_acids"] = most_severe.get("amino_acids")
    extracted["impact"] = most_severe.get("impact")
    extracted["biotype"] = most_severe.get("biotype")
    extracted["protein_id"] = most_severe.get("protein_id")

    # SIFT and PolyPhen scores
    if "sift_score" in most_severe:
        extracted["sift_score"] = float(most_severe["sift_score"])
    if "polyphen_score" in most_severe:
        extracted["polyphen_score"] = float(most_severe["polyphen_score"])

    # If consequence_terms exists, use first one as primary
    consequence_terms = most_severe.get("consequence_terms", [])
    if consequence_terms:
        extracted["consequence"] = consequence_terms[0]

    return extracted


async def run_vep_annotation_async(
    variants: list[dict[str, Any]],
    species: str = "GRCh37"
) -> list[dict[str, Any]]:
    """
    Execute VEP annotation asynchronously.

    Args:
        variants: List of variant dicts with chrom, pos, ref, alt
        species: Species name (GRCh37 or GRCh38)

    Returns:
        list: VEP annotation results as JSON dicts

    Raises:
        RuntimeError: If VEP execution fails
    """
    species_config = get_species_config(species)
    cmd = build_vep_command(species_config)

    input_data = generate_variant_input(variants)

    temp_dir = tempfile.gettempdir()
    timestamp = int(time.time() * 1000)
    input_file = os.path.join(temp_dir, f"vep_input_{timestamp}.txt")
    output_file = os.path.join(temp_dir, f"vep_output_{timestamp}.json")

    try:
        with open(input_file, "w") as f:
            f.write(input_data)

        cmd.extend(["--input_file", input_file])
        cmd.extend(["-o", output_file])

        logger.info(f"Executing VEP command for {len(variants)} variants")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=settings.VEP_TIMEOUT
        )

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode()
            logger.error(f"VEP failed: {error_msg}")
            raise RuntimeError(f"VEP annotation failed: {error_msg}")

        if not os.path.exists(output_file):
            raise RuntimeError(f"VEP output file not created: {output_file}")

        with open(output_file, "r") as f:
            results = json.load(f)

        logger.info(f"VEP annotation completed: {len(results)} results")
        return results

    except asyncio.TimeoutError:
        logger.error(f"VEP execution timed out after {settings.VEP_TIMEOUT}s")
        raise RuntimeError(f"VEP annotation timed out after {settings.VEP_TIMEOUT} seconds")

    finally:
        for file_path in [input_file, output_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    logger.warning(f"Failed to remove temp file {file_path}: {e}")