"""VCF Parser Service

Parses VCF (Variant Call Format) files for variant extraction.
"""

import csv
import gzip
import logging
import os
from io import StringIO
from typing import Any

logger = logging.getLogger(__name__)


def parse_vcf_file(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse a VCF file and extract variants.

    Handles both plain text (.vcf) and gzipped (.vcf.gz) files.

    Args:
        file_path: Path to VCF file

    Returns:
        tuple: (variants list, metadata dict)

    Raises:
        ValueError: If file format is invalid
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"VCF file not found: {file_path}")

    if file_path.endswith(".gz"):
        return parse_vcf_gz(file_path)
    else:
        return parse_vcf_plain(file_path)


def parse_vcf_plain(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse plain text VCF file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return parse_vcf_content(f)


def parse_vcf_gz(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse gzipped VCF file."""
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        return parse_vcf_content(f)


def parse_vcf_content(file_obj) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse VCF content from file object."""
    reader = csv.reader(file_obj, delimiter="\t", quotechar="\n")

    variants = []
    metadata = {
        "header_lines": [],
        "columns": [],
        "sample_names": [],
    }

    for row in reader:
        if not row:
            continue

        if row[0].startswith("##"):
            metadata["header_lines"].append(row[0])
            continue

        if row[0].startswith("#"):
            row[0] = row[0][1:]
            columns = [c.lower() for c in row]
            metadata["columns"] = columns
            if len(columns) > 8:
                metadata["sample_names"] = columns[8:]
            continue

        if len(row) < 8:
            logger.warning(f"Skipping malformed VCF row: {row}")
            continue

        variant = {
            "chrom": row[0],
            "pos": int(row[1]),
            "id": row[2],
            "ref": row[3],
            "alt": row[4],
            "qual": row[5],
            "filter": row[6],
            "info": parse_info_field(row[7]),
        }

        if len(row) > 8 and metadata["sample_names"]:
            variant["samples"] = {}
            for i, sample_name in enumerate(metadata["sample_names"]):
                if i + 8 < len(row):
                    variant["samples"][sample_name] = row[i + 8]

        variants.append(variant)

    logger.info(f"Parsed {len(variants)} variants from VCF file")
    return variants, metadata


def parse_info_field(info_str: str) -> dict[str, Any]:
    """Parse VCF INFO field into dictionary."""
    if info_str == "." or not info_str:
        return {}

    info_dict = {}
    for item in info_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            if "," in value:
                info_dict[key] = value.split(",")
            else:
                info_dict[key] = value
        else:
            info_dict[item] = True

    return info_dict


def extract_variants_from_vcf(
    file_path: str,
    max_variants: int = 1000
) -> list[dict[str, Any]]:
    """
    Extract variants from VCF file for annotation.

    Returns simplified variant list suitable for VEP input.

    Args:
        file_path: Path to VCF file
        max_variants: Maximum number of variants to extract

    Returns:
        list: Simplified variant dicts with chrom, pos, ref, alt
    """
    variants, metadata = parse_vcf_file(file_path)

    if len(variants) > max_variants:
        logger.warning(f"VCF file contains {len(variants)} variants, limiting to {max_variants}")
        variants = variants[:max_variants]

    simplified = []
    for v in variants:
        alts = v["alt"].split(",")
        for alt in alts:
            simplified.append({
                "chrom": v["chrom"],
                "pos": v["pos"],
                "ref": v["ref"],
                "alt": alt.strip(),
            })

    logger.info(f"Extracted {len(simplified)} variants for annotation")
    return simplified


def validate_vcf_format(file_path: str) -> bool:
    """Validate that file is a proper VCF format."""
    try:
        variants, metadata = parse_vcf_file(file_path)

        if not metadata.get("columns"):
            logger.warning("VCF file missing column header")
            return False

        required = ["chrom", "pos", "ref", "alt"]
        columns = metadata.get("columns", [])
        for col in required:
            if col not in columns:
                logger.warning(f"VCF file missing required column: {col}")
                return False

        if not variants:
            logger.warning("VCF file contains no variants")
            return False

        return True

    except Exception as e:
        logger.error(f"VCF validation failed: {e}")
        return False


def parse_vcf_string(content: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse VCF content from string."""
    f = StringIO(content)
    return parse_vcf_content(f)