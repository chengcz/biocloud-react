"""Tests for VCF Parser Service"""

import pytest
import tempfile
import os
from services.vcf_parser import (
    parse_vcf_string,
    parse_info_field,
    extract_variants_from_vcf,
    validate_vcf_format,
)


def test_parse_info_field():
    """Test INFO field parsing"""
    info = parse_info_field("DP=100")
    assert info["DP"] == "100"

    info = parse_info_field("DP=100;AF=0.5")
    assert info["DP"] == "100"
    assert info["AF"] == "0.5"

    info = parse_info_field("DB")
    assert info["DB"] is True

    info = parse_info_field(".")
    assert info == {}


def test_parse_vcf_string():
    """Test VCF parsing from string"""
    vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\tDP=100
2\t200\t.\tG\tC\t.\tPASS\tDP=50"""

    variants, metadata = parse_vcf_string(vcf_content)

    assert len(variants) == 2
    assert variants[0]["chrom"] == "1"
    assert variants[0]["pos"] == 100


def test_extract_variants_from_vcf():
    """Test variant extraction"""
    vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\tDP=100"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
        f.write(vcf_content)
        temp_path = f.name

    try:
        variants = extract_variants_from_vcf(temp_path)
        assert len(variants) == 1
        assert variants[0]["chrom"] == "1"
    finally:
        os.unlink(temp_path)


def test_validate_vcf_format():
    """Test VCF format validation"""
    valid_vcf = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\tDP=100"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
        f.write(valid_vcf)
        temp_path = f.name

    try:
        assert validate_vcf_format(temp_path) is True
    finally:
        os.unlink(temp_path)