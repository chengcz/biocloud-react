"""Annotation Cache Model

Stores cached VEP annotation results.
NO user_id - annotations are shared globally across all clients.
"""

from sqlalchemy import String, Integer, Text, JSON, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from models.base import BaseModel


class AnnotationResult(BaseModel):
    """
    VEP annotation result cache.

    Stores annotation results for variants to avoid redundant VEP calls.
    NO user tracking - annotations are shared globally.
    """
    __tablename__ = "vep_annotation_result"

    # Variant identification
    variant_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Hash of chrom+pos+ref+alt+species for deduplication"
    )
    species: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Genome assembly (GRCh37, GRCh38)"
    )

    # Variant coordinates
    chrom: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Chromosome name (e.g., '1', 'chr1')"
    )
    pos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Position in genome"
    )
    ref: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reference allele"
    )
    alt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Alternate allele"
    )

    # VEP annotation columns (extracted from transcript_consequences)
    consequence: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Most severe consequence term (from consequence_terms array)"
    )
    codons: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Reference and variant codons (e.g., aTg/aCg)"
    )
    gene_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Ensembl Gene ID (e.g., ENSG00000178821)"
    )
    gene_symbol: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Gene symbol/name (e.g., BRCA1)"
    )
    transcript_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Ensembl Transcript ID (e.g., ENST00000310991)"
    )
    exon: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Exon number out of total (e.g., 1/5)"
    )
    intron: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Intron number out of total (e.g., 2/4)"
    )
    hgvsc: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="HGVS cDNA notation (e.g., ENST00000310991.8:c.422T>C)"
    )
    hgvsp: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="HGVS protein notation (e.g., ENSP00000311122.3:p.Met141Thr)"
    )
    impact: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Impact level: HIGH, MODERATE, LOW, MODIFIER"
    )
    biotype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Transcript biotype (e.g., protein_coding)"
    )
    protein_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Ensembl Protein ID (e.g., ENSP00000311122)"
    )
    sift_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="SIFT score (0.0-1.0, lower = more damaging)"
    )
    polyphen_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="PolyPhen score (0.0-1.0, higher = more damaging)"
    )
    amino_acids: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Reference/variant amino acids (e.g., M/T)"
    )

    # Annotation data (full JSON backup)
    annotation_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Full VEP annotation JSON (backup + non-standard fields)"
    )

    # NO user_id field - open access, shared cache

    # Composite unique constraint to prevent duplicate annotations
    __table_args__ = (
        UniqueConstraint("variant_hash", "species", name="uq_variant_species"),
    )