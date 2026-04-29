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

    # Check if gzipped
    if file_path.endswith(".gz"):
        return parse_vcf_gz(file_path)
    else:
        return parse_vcf_plain(file_path)


def parse_vcf_plain(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse plain text VCF file.

    Args:
        file_path: Path to plain text VCF file

    Returns:
        tuple: (variants list, metadata dict)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return parse_vcf_content(f)


def parse_vcf_gz(file_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse gzipped VCF file.

    Args:
        file_path: Path to gzipped VCF file

    Returns:
        tuple: (variants list, metadata dict)
    """
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        return parse_vcf_content(f)


def parse_vcf_content(file_obj) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse VCF content from file object.

    Args:
        file_obj: File object (open file or StringIO)

    Returns:
        tuple: (variants list, metadata dict)
    """
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

        # Header lines
        if row[0].startswith("##"):
            metadata["header_lines"].append(row[0])
            # Parse metadata from header
            if row[0].startswith("##fileformat="):
                metadata["fileformat"] = row[0].split("=")[1]
            elif row[0].startswith("##fileDate="):
                metadata["fileDate"] = row[0].split("=")[1]
            elif row[0].startswith("##reference="):
                metadata["reference"] = row[0].split("=")[1]
            continue

        # Column header line (#CHROM POS ID REF ALT QUAL FILTER INFO SAMPLE...)
        if row[0].startswith("#"):
            row[0] = row[0][1:]  # Remove leading #
            columns = [c.lower() for c in row]
            metadata["columns"] = columns

            # Extract sample names (columns after INFO)
            if len(columns) > 8:
                metadata["sample_names"] = columns[8:]
            continue

        # Data rows
        if len(row) < 8:
            logger.warning(f"Skipping malformed VCF row: {row}")
            continue

        # Parse standard columns
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

        # Parse sample data if present
        if len(row) > 8 and metadata["sample_names"]:
            variant["samples"] = {}
            for i, sample_name in enumerate(metadata["sample_names"]):
                if i + 8 < len(row):
                    variant["samples"][sample_name] = row[i + 8]

        variants.append(variant)

    logger.info(f"Parsed {len(variants)} variants from VCF file")
    return variants, metadata


def parse_info_field(info_str: str) -> dict[str, Any]:
    """
    Parse VCF INFO field into dictionary.

    Args:
        info_str: INFO field string (e.g., "DP=100;AF=0.5;DB")

    Returns:
        dict: Parsed INFO field as key-value pairs
    """
    if info_str == "." or not info_str:
        return {}

    info_dict = {}
    for item in info_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            # Handle multiple values (comma-separated)
            if "," in value:
                info_dict[key] = value.split(",")
            else:
                info_dict[key] = value
        else:
            # Flag field (no value)
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

    Raises:
        ValueError: If variant count exceeds max_variants
    """
    variants, metadata = parse_vcf_file(file_path)

    if len(variants) > max_variants:
        logger.warning(
            f"VCF file contains {len(variants)} variants, "
            f"limiting to {max_variants}"
        )
        variants = variants[:max_variants]

    # Simplify to VEP input format
    simplified = []
    for v in variants:
        # Handle multi-allelic variants (split ALT by comma)
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
    """
    Validate that file is a proper VCF format.

    Args:
        file_path: Path to VCF file

    Returns:
        bool: True if valid VCF format
    """
    try:
        variants, metadata = parse_vcf_file(file_path)

        # Check for required metadata
        if not metadata.get("columns"):
            logger.warning("VCF file missing column header")
            return False

        # Check for minimum columns
        required = ["chrom", "pos", "ref", "alt"]
        columns = metadata.get("columns", [])
        for col in required:
            if col not in columns:
                logger.warning(f"VCF file missing required column: {col}")
                return False

        # Check for at least one variant
        if not variants:
            logger.warning("VCF file contains no variants")
            return False

        return True

    except Exception as e:
        logger.error(f"VCF validation failed: {e}")
        return False


def parse_vcf_string(content: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse VCF content from string.

    Args:
        content: VCF file content as string

    Returns:
        tuple: (variants list, metadata dict)
    """
    f = StringIO(content)
    return parse_vcf_content(f)