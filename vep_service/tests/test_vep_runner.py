"""Tests for VEP Runner Service"""

import pytest
from services.vep_runner import (
    load_species_config,
    get_species_config,
    build_vep_command,
    compute_variant_hash,
    generate_variant_input,
    extract_most_severe_consequence,
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


def test_extract_most_severe_consequence_basic():
    """Test basic field extraction from VEP result"""
    vep_result = {
        "most_severe_consequence": "missense_variant",
        "transcript_consequences": [
            {
                "gene_id": "ENSG00000178821",
                "gene_symbol": "BRCA1",
                "transcript_id": "ENST00000310991",
                "consequence_terms": ["missense_variant"],
                "impact": "MODERATE",
                "codons": "aTg/aCg",
                "hgvsc": "ENST00000310991.8:c.422T>C",
                "hgvsp": "ENSP00000311122.3:p.Met141Thr",
                "exon": "1/5",
                "sift_score": 0.22,
                "polyphen_score": 0.001,
            }
        ]
    }

    extracted = extract_most_severe_consequence(vep_result)

    assert extracted["consequence"] == "missense_variant"
    assert extracted["gene_id"] == "ENSG00000178821"
    assert extracted["gene_symbol"] == "BRCA1"
    assert extracted["codons"] == "aTg/aCg"
    assert extracted["hgvsc"] == "ENST00000310991.8:c.422T>C"
    assert extracted["hgvsp"] == "ENSP00000311122.3:p.Met141Thr"
    assert extracted["exon"] == "1/5"
    assert extracted["sift_score"] == 0.22
    assert extracted["impact"] == "MODERATE"


def test_extract_most_severe_consequence_empty():
    """Test extraction with empty transcript consequences"""
    vep_result = {
        "most_severe_consequence": "intergenic_variant",
        "transcript_consequences": []
    }

    extracted = extract_most_severe_consequence(vep_result)

    assert extracted["consequence"] == "intergenic_variant"
    assert extracted["gene_id"] is None
    assert extracted["transcript_id"] is None


def test_extract_most_severe_consequence_impact_ordering():
    """Test that most severe impact is selected"""
    vep_result = {
        "transcript_consequences": [
            {"impact": "LOW", "gene_symbol": "GENE_LOW"},
            {"impact": "HIGH", "gene_symbol": "GENE_HIGH"},
            {"impact": "MODERATE", "gene_symbol": "GENE_MOD"},
        ]
    }

    extracted = extract_most_severe_consequence(vep_result)

    # HIGH impact should be selected
    assert extracted["impact"] == "HIGH"
    assert extracted["gene_symbol"] == "GENE_HIGH"


def test_extract_most_severe_consequence_missing_fields():
    """Test extraction with partially missing VEP fields"""
    vep_result = {
        "transcript_consequences": [
            {
                "gene_id": "ENSG000001",
                "gene_symbol": "TESTGENE",
                # Missing: transcript_id, codons, hgvsc, etc.
            }
        ]
    }

    extracted = extract_most_severe_consequence(vep_result)

    assert extracted["gene_id"] == "ENSG000001"
    assert extracted["gene_symbol"] == "TESTGENE"
    assert extracted["transcript_id"] is None
    assert extracted["codons"] is None
    assert extracted["hgvsc"] is None