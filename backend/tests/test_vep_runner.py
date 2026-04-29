"""Tests for VEP Runner Service"""

import pytest
from unittest.mock import patch, AsyncMock
import asyncio

from app.services.vep_runner import (
    compute_variant_hash,
    generate_variant_input,
    load_species_config,
    get_species_config,
    build_vep_command,
)


class TestComputeVariantHash:
    """Tests for variant hash computation"""

    def test_hash_consistency(self):
        """Same variant should produce same hash"""
        hash1 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        hash2 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        assert hash1 == hash2

    def test_hash_different_chrom(self):
        """Different chromosome should produce different hash"""
        hash1 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        hash2 = compute_variant_hash("2", 100, "A", "T", "GRCh37")
        assert hash1 != hash2

    def test_hash_different_pos(self):
        """Different position should produce different hash"""
        hash1 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        hash2 = compute_variant_hash("1", 200, "A", "T", "GRCh37")
        assert hash1 != hash2

    def test_hash_different_ref_alt(self):
        """Different alleles should produce different hash"""
        hash1 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        hash2 = compute_variant_hash("1", 100, "A", "G", "GRCh37")
        assert hash1 != hash2

    def test_hash_different_species(self):
        """Different species should produce different hash"""
        hash1 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        hash2 = compute_variant_hash("1", 100, "A", "T", "GRCh38")
        assert hash1 != hash2

    def test_hash_length(self):
        """Hash should be SHA256 (64 characters)"""
        hash_result = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        assert len(hash_result) == 64

    def test_hash_format(self):
        """Hash should be hexadecimal"""
        hash_result = compute_variant_hash("1", 100, "A", "T", "GRCh37")
        assert all(c in "0123456789abcdef" for c in hash_result)


class TestGenerateVariantInput:
    """Tests for VCF-style input generation"""

    def test_single_variant(self):
        """Single variant should produce correct format"""
        variants = [{"chrom": "1", "pos": 100, "ref": "A", "alt": "T"}]
        result = generate_variant_input(variants)
        assert result == "1\t100\t.\tA\tT\t.\t.\t."

    def test_multiple_variants(self):
        """Multiple variants should be newline separated"""
        variants = [
            {"chrom": "1", "pos": 100, "ref": "A", "alt": "T"},
            {"chrom": "2", "pos": 200, "ref": "C", "alt": "G"},
        ]
        result = generate_variant_input(variants)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "1\t100\t.\tA\tT\t.\t.\t."
        assert lines[1] == "2\t200\t.\tC\tG\t.\t.\t."

    def test_empty_list(self):
        """Empty list should produce empty string"""
        variants = []
        result = generate_variant_input(variants)
        assert result == ""


class TestLoadSpeciesConfig:
    """Tests for species configuration loading"""

    def test_returns_dict(self):
        """Should return dictionary"""
        config = load_species_config()
        assert isinstance(config, dict)

    def test_has_species_list(self):
        """Should have species list"""
        config = load_species_config()
        assert "species" in config
        assert isinstance(config["species"], list)

    def test_has_grch37(self):
        """Should include GRCh37"""
        config = load_species_config()
        species_names = [s["name"] for s in config["species"]]
        assert "GRCh37" in species_names

    def test_has_grch38(self):
        """Should include GRCh38"""
        config = load_species_config()
        species_names = [s["name"] for s in config["species"]]
        assert "GRCh38" in species_names

    def test_has_defaults(self):
        """Should have default settings"""
        config = load_species_config()
        assert "defaults" in config
        assert "distance" in config["defaults"]


class TestGetSpeciesConfig:
    """Tests for specific species config retrieval"""

    def test_get_grch37(self):
        """Should get GRCh37 config"""
        config = get_species_config("GRCh37")
        assert config["name"] == "GRCh37"
        assert config["assembly"] == "GRCh37"

    def test_get_grch38(self):
        """Should get GRCh38 config"""
        config = get_species_config("GRCh38")
        assert config["name"] == "GRCh38"
        assert config["assembly"] == "GRCh38"

    def test_invalid_species(self):
        """Should raise ValueError for invalid species"""
        with pytest.raises(ValueError, match="not found"):
            get_species_config("InvalidSpecies")


class TestBuildVepCommand:
    """Tests for VEP command building"""

    def test_basic_command_structure(self):
        """Should start with vep command"""
        species_config = {"name": "GRCh37", "vep_cache_dir": "/data/vep_data/GRCh37"}
        cmd = build_vep_command(species_config)
        assert cmd[0] == "vep"

    def test_includes_force_flag(self):
        """Should include --force flag"""
        species_config = {"name": "GRCh37"}
        cmd = build_vep_command(species_config)
        assert "--force" in cmd

    def test_includes_json_output(self):
        """Should include JSON output format"""
        species_config = {"name": "GRCh37"}
        cmd = build_vep_command(species_config)
        assert "--output_format" in cmd
        assert "json" in cmd

    def test_includes_distance(self):
        """Should include distance parameter"""
        species_config = {"name": "GRCh37"}
        cmd = build_vep_command(species_config)
        assert "--distance" in cmd


@pytest.mark.asyncio
class TestRunVepAnnotationAsync:
    """Tests for async VEP execution"""

    @patch("app.services.vep_runner.get_species_config")
    @patch("asyncio.create_subprocess_exec")
    async def test_timeout_handling(self, mock_subprocess, mock_species):
        """Should handle timeout gracefully"""
        mock_species.return_value = {"name": "GRCh37"}
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        from app.services.vep_runner import run_vep_annotation_async

        with pytest.raises(RuntimeError, match="timed out"):
            await run_vep_annotation_async([{"chrom": "1", "pos": 100, "ref": "A", "alt": "T"}], "GRCh37")