"""VEP Annotation Cache Model

Stores cached VEP annotation results to avoid re-running VEP for identical variants.
"""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import UserModel


class AnnotationResult(BaseModel):
    """
    VEP annotation result cache

    Stores annotation results for variants to avoid redundant VEP calls.
    Uses composite unique constraint on (variant_hash, species) for deduplication.
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

    # User tracking
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_user.id"),
        nullable=True,
        index=True,
        comment="User who submitted the annotation request"
    )

    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship(
        foreign_keys=[user_id]
    )

    # Composite unique constraint to prevent duplicate annotations
    __table_args__ = (
        UniqueConstraint("variant_hash", "species", name="uq_variant_species"),
    )