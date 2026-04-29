"""VEP Runner Service

Executes VEP (Variant Effect Predictor) command-line tool for variant annotation.
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

from app.config.settings import settings

logger = logging.getLogger(__name__)


def load_species_config() -> dict:
    """
    Load species configuration from YAML file.

    Returns:
        dict: Species configuration with GRCh37 and GRCh38 settings
    """
    config_path = Path(settings.SPECIES_CONFIG_PATH)
    if not config_path.exists():
        # Try relative to backend directory
        config_path = Path(__file__).parent.parent.parent / "config" / "species.yaml"

    if not config_path.exists():
        logger.warning(f"Species config not found at {config_path}, using defaults")
        return {
            "species": [
                {
                    "name": "GRCh37",
                    "assembly": "GRCh37",
                    "vep_cache_dir": "/data/vep_data/GRCh37",
                    "fasta_file": "/data/vep_data/GRCh37/GRCh37.fa",
                    "gff_file": "/data/vep_data/GRCh37/GRCh37.gff3",
                    "enabled": True,
                },
                {
                    "name": "GRCh38",
                    "assembly": "GRCh38",
                    "vep_cache_dir": "/data/vep_data/GRCh38",
                    "fasta_file": "/data/vep_data/GRCh38/GRCh38.fa",
                    "gff_file": "/data/vep_data/GRCh38/GRCh38.gff3",
                    "enabled": True,
                },
            ],
            "defaults": {
                "distance": 500,
                "output_format": "json",
                "hgvs": True,
                "hgvsg": True,
                "symbol": True,
                "domains": True,
                "protein": True,
                "numbers": True,
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


def build_vep_command(species_config: dict, cache_mode: bool = True) -> list[str]:
    """
    Build VEP command with appropriate flags.

    Args:
        species_config: Species configuration dict
        cache_mode: Use VEP cache (True) or reference files (False)

    Returns:
        list: VEP command arguments
    """
    defaults = load_species_config().get("defaults", {})

    # Basic VEP command
    cmd = [
        "vep",
        "--force",
        "--no_stats",
        "--no_progress",
    ]

    # Add default flags from config
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

    # Distance parameter
    cmd.extend(["--distance", str(defaults.get("distance", 500))])

    # Output format
    cmd.extend(["--output_format", "json"])

    if cache_mode:
        # Use cache directory (offline mode)
        vep_cache_dir = species_config.get("vep_cache_dir", "")
        if vep_cache_dir and os.path.exists(vep_cache_dir):
            cmd.extend([
                "--dir", vep_cache_dir,
                "--offline",
                "--cache",
                "--refseq",
            ])
        else:
            logger.warning(f"VEP cache dir not found: {vep_cache_dir}, using reference files")
            # Fall back to reference files
            fasta_file = species_config.get("fasta_file", "")
            gff_file = species_config.get("gff_file", "")
            if fasta_file:
                cmd.extend(["--fasta", fasta_file])
            if gff_file:
                cmd.extend(["--gff", gff_file])
    else:
        # Use reference files directly
        fasta_file = species_config.get("fasta_file", "")
        gff_file = species_config.get("gff_file", "")
        if fasta_file:
            cmd.extend(["--fasta", fasta_file])
        if gff_file:
            cmd.extend(["--gff", gff_file])

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

        # VCF format: chrom pos id ref alt qual filter info
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

    # Generate variant input
    input_data = generate_variant_input(variants)

    # Create temp files for input and output
    temp_dir = tempfile.gettempdir()
    timestamp = int(time.time() * 1000)
    input_file = os.path.join(temp_dir, f"vep_input_{timestamp}.txt")
    output_file = os.path.join(temp_dir, f"vep_output_{timestamp}.json")
    warning_file = os.path.join(temp_dir, f"vep_output_{timestamp}_warnings.txt")

    try:
        # Write input file
        with open(input_file, "w") as f:
            f.write(input_data)

        # Add input and output to command
        cmd.extend(["--input_file", input_file])
        cmd.extend(["-o", output_file])

        # Execute VEP asynchronously
        logger.info(f"Executing VEP command for {len(variants)} variants")
        logger.debug(f"VEP command: {' '.join(cmd)}")

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
            logger.error(f"VEP failed with return code {process.returncode}: {error_msg}")
            raise RuntimeError(f"VEP annotation failed: {error_msg}")

        # Read output
        if not os.path.exists(output_file):
            raise RuntimeError(f"VEP output file not created: {output_file}")

        with open(output_file, "r") as f:
            results = json.load(f)

        logger.info(f"VEP annotation completed: {len(results)} results")

        # Log warnings if any
        if os.path.exists(warning_file):
            with open(warning_file, "r") as f:
                warnings = f.read()
            if warnings:
                logger.warning(f"VEP warnings: {warnings}")

        return results

    except asyncio.TimeoutError:
        logger.error(f"VEP execution timed out after {settings.VEP_TIMEOUT}s")
        raise RuntimeError(f"VEP annotation timed out after {settings.VEP_TIMEOUT} seconds")

    finally:
        # Cleanup temp files
        for file_path in [input_file, output_file, warning_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    logger.warning(f"Failed to remove temp file {file_path}: {e}")


def parse_vep_result(vep_result: dict[str, Any]) -> dict[str, Any]:
    """
    Parse single VEP result to extract key annotation fields.

    Args:
        vep_result: Raw VEP result dict

    Returns:
        dict: Structured annotation with key fields
    """
    # Extract most severe consequence
    transcript_consequences = vep_result.get("transcript_consequences", [])
    most_severe = None
    if transcript_consequences:
        # Sort by consequence rank (lower is more severe)
        most_severe = min(
            transcript_consequences,
            key=lambda x: x.get("consequence_rank", 999)
        )

    return {
        "id": vep_result.get("id", ""),
        "variant": vep_result.get("variant", ""),
        "most_severe_consequence": vep_result.get("most_severe_consequence", ""),
        "gene_symbol": most_severe.get("gene_symbol", "") if most_severe else "",
        "transcript_id": most_severe.get("transcript_id", "") if most_severe else "",
        "consequence_terms": most_severe.get("consequence_terms", []) if most_severe else [],
        "impact": most_severe.get("impact", "") if most_severe else "",
        "hgvs_c": most_severe.get("hgvs_c", "") if most_severe else "",
        "hgvs_p": most_severe.get("hgvs_p", "") if most_severe else "",
        "hgvsg": vep_result.get("hgvsg", ""),
        "full_result": vep_result,
    }