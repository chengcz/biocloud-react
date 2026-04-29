"""Tests for VCF Parser Service"""

import gzip
import tempfile
import os

from app.services.vcf_parser import (
    parse_info_field,
    extract_variants_from_vcf,
    validate_vcf_format,
    parse_vcf_string,
)


class TestParseInfoField:
    """Tests for VCF INFO field parsing"""

    def test_empty_info(self):
        """Empty info should return empty dict"""
        result = parse_info_field(".")
        assert result == {}

    def test_single_key_value(self):
        """Single key=value should parse correctly"""
        result = parse_info_field("DP=100")
        assert result == {"DP": "100"}

    def test_multiple_key_values(self):
        """Multiple key=value pairs should parse correctly"""
        result = parse_info_field("DP=100;AF=0.5;DB")
        assert result == {"DP": "100", "AF": "0.5", "DB": True}

    def test_comma_separated_values(self):
        """Comma-separated values should become list"""
        result = parse_info_field("CSQ=A,B,C")
        assert result == {"CSQ": ["A", "B", "C"]}

    def test_flag_field(self):
        """Flag fields without value should be True"""
        result = parse_info_field("DB;CLNSIG")
        assert result == {"DB": True, "CLNSIG": True}

    def test_mixed_fields(self):
        """Mixed key=value and flags should parse correctly"""
        result = parse_info_field("DP=100;DB;AF=0.5")
        assert result == {"DP": "100", "DB": True, "AF": "0.5"}


class TestParseVcfString:
    """Tests for VCF string parsing"""

    def test_simple_vcf(self):
        """Simple VCF should parse correctly"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\tDP=100
2\t200\t.\tC\tG\t.\tPASS\tDP=50"""
        variants, metadata = parse_vcf_string(vcf_content)
        assert len(variants) == 2
        assert variants[0]["chrom"] == "1"
        assert variants[0]["pos"] == 100
        assert variants[0]["ref"] == "A"
        assert variants[0]["alt"] == "T"

    def test_vcf_with_samples(self):
        """VCF with sample columns should extract sample names"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tSAMPLE1\tSAMPLE2
1\t100\t.\tA\tT\t.\tPASS\tDP=100\t0/1\t0/0"""
        variants, metadata = parse_vcf_string(vcf_content)
        assert "SAMPLE1" in metadata["sample_names"]
        assert "SAMPLE2" in metadata["sample_names"]
        assert variants[0]["samples"]["SAMPLE1"] == "0/1"

    def test_vcf_metadata_extraction(self):
        """Should extract metadata from header"""
        vcf_content = """##fileformat=VCFv4.2
##fileDate=20240101
##reference=GRCh37
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\t."""
        variants, metadata = parse_vcf_string(vcf_content)
        assert metadata["fileformat"] == "VCFv4.2"
        assert metadata["fileDate"] == "20240101"
        assert metadata["reference"] == "GRCh37"

    def test_empty_vcf(self):
        """Empty VCF should return empty variants"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"""
        variants, metadata = parse_vcf_string(vcf_content)
        assert len(variants) == 0

    def test_multiallelic_variant(self):
        """Multi-allelic ALT should not be split in parsing"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT,G\t.\tPASS\t."""
        variants, metadata = parse_vcf_string(vcf_content)
        assert variants[0]["alt"] == "T,G"


class TestExtractVariantsFromVcf:
    """Tests for variant extraction"""

    def test_extract_simple_variants(self):
        """Should extract variants in simplified format"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\tDP=100
2\t200\t.\tC\tG\t.\tPASS\tDP=50"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            variants = extract_variants_from_vcf(f.name)
            os.unlink(f.name)

        assert len(variants) == 2
        assert variants[0] == {"chrom": "1", "pos": 100, "ref": "A", "alt": "T"}
        assert variants[1] == {"chrom": "2", "pos": 200, "ref": "C", "alt": "G"}

    def test_split_multiallelic(self):
        """Should split multi-allelic variants"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT,G\t.\tPASS\t."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            variants = extract_variants_from_vcf(f.name)
            os.unlink(f.name)

        assert len(variants) == 2
        assert variants[0] == {"chrom": "1", "pos": 100, "ref": "A", "alt": "T"}
        assert variants[1] == {"chrom": "1", "pos": 100, "ref": "A", "alt": "G"}

    def test_max_variants_limit(self):
        """Should limit variants to max_variants"""
        lines = ["##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
        for i in range(100):
            lines.append(f"1\t{i*100}\t.\tA\tT\t.\tPASS\t.")
        vcf_content = "\n".join(lines)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            variants = extract_variants_from_vcf(f.name, max_variants=50)
            os.unlink(f.name)

        assert len(variants) == 50


class TestValidateVcfFormat:
    """Tests for VCF format validation"""

    def test_valid_vcf(self):
        """Valid VCF should pass validation"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\t."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            is_valid = validate_vcf_format(f.name)
            os.unlink(f.name)

        assert is_valid is True

    def test_missing_column_header(self):
        """Missing column header should fail"""
        vcf_content = """##fileformat=VCFv4.2
1\t100\t.\tA\tT\t.\tPASS\t."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            is_valid = validate_vcf_format(f.name)
            os.unlink(f.name)

        assert is_valid is False

    def test_no_variants(self):
        """VCF with no variants should fail"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            is_valid = validate_vcf_format(f.name)
            os.unlink(f.name)

        assert is_valid is False

    def test_missing_required_columns(self):
        """Missing required columns should fail"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tQUAL\tFILTER\tINFO
1\t100\t.\tA\t.\tPASS\t."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vcf", delete=False) as f:
            f.write(vcf_content)
            f.flush()
            is_valid = validate_vcf_format(f.name)
            os.unlink(f.name)

        assert is_valid is False


class TestGzippedVcf:
    """Tests for gzipped VCF handling"""

    def test_gzipped_vcf_parsing(self):
        """Should parse gzipped VCF correctly"""
        vcf_content = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
1\t100\t.\tA\tT\t.\tPASS\tDP=100"""

        with tempfile.NamedTemporaryFile(suffix=".vcf.gz", delete=False) as f:
            with gzip.open(f.name, "wt") as gz:
                gz.write(vcf_content)
            f.flush()

            from app.services.vcf_parser import parse_vcf_file
            variants, metadata = parse_vcf_file(f.name)
            os.unlink(f.name)

        assert len(variants) == 1
        assert variants[0]["chrom"] == "1"