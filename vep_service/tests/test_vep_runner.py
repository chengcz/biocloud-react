"""Tests for VEP Runner Service"""

import pytest
from app.services.vep_runner import (
    load_species_config,
    get_species_config,
    build_vep_command,
    compute_variant_hash,
    generate_variant_input,
)


def test_compute_variant_hash():
    """Test variant hash computation"""
    hash1 = compute_variant_hash("1", 100, "A", "T", "GRCh37")
    hash2 = compute_variant_hash("1", 100, "A", "T", "GRCh37")

    assert hash1 == hash2
    assert len(hash1) == 64

    hash3 = compute_variant_hash("1", 101, "A", "T", "GRCh37")
    assert hash1 != hash3

    hash4 = compute_variant_hash("1", 100, "A", "T", "GRCh38")
    assert hash1 != hash4


def test_generate_variant_input():
    """Test VCF-style input generation"""
    variants = [
        {"chrom": "1", "pos": 100, "ref": "A", "alt": "T"},
        {"chrom": "2", "pos": 200, "ref": "G", "alt": "C"},
    ]

    input_str = generate_variant_input(variants)

    assert "1\t100\t.\tA\tT\t.\t.\t." in input_str
    assert "2\t200\t.\tG\tC\t.\t.\t." in input_str
    assert len(input_str.split("\n")) == 2


def test_load_species_config():
    """Test species config loading"""
    config = load_species_config()

    assert "species" in config
    assert len(config["species"]) >= 2


def test_get_species_config_valid():
    """Test getting valid species config"""
    config = get_species_config("GRCh37")
    assert config["name"] == "GRCh37"


def test_get_species_config_invalid():
    """Test getting invalid species raises error"""
    with pytest.raises(ValueError, match="not found"):
        get_species_config("InvalidSpecies")


def test_build_vep_command():
    """Test VEP command building"""
    species_config = {
        "name": "GRCh37",
        "vep_cache_dir": "/data/vep_data/GRCh37",
    }

    cmd = build_vep_command(species_config)

    assert "vep" in cmd
    assert "--force" in cmd
    assert "--no_stats" in cmd