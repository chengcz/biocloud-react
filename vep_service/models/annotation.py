"""Annotation Cache Model

Stores cached VEP annotation results.
NO user_id - annotations are shared globally across all clients.
"""

from sqlalchemy import String, Integer, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
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

    # Annotation data
    annotation_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="VEP annotation result as JSON"
    )

    # NO user_id field - open access, shared cache

    # Composite unique constraint to prevent duplicate annotations
    __table_args__ = (
        UniqueConstraint("variant_hash", "species", name="uq_variant_species"),
    )