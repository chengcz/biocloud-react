"""Pydantic schemas for VEP annotation API"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VariantRequest(BaseModel):
    """Single variant for annotation"""
    chrom: str = Field(..., description="Chromosome name (e.g., '1', 'chr1')")
    pos: int = Field(..., ge=1, description="Position in genome (1-based)")
    ref: str = Field(..., min_length=1, description="Reference allele")
    alt: str = Field(..., min_length=1, description="Alternate allele")
    species: Optional[str] = Field(None, description="Species/assembly override (GRCh37/GRCh38)")


class AnnotateRequest(BaseModel):
    """Annotation request for multiple variants"""
    variants: List[VariantRequest] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of variants to annotate (max 1000)"
    )
    mode: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description="Annotation mode: sync (immediate) or async (background task)"
    )
    species: str = Field(
        default="GRCh37",
        description="Default genome assembly (GRCh37 or GRCh38)"
    )


class VariantAnnotation(BaseModel):
    """Single variant annotation result"""
    chrom: str
    pos: int
    ref: str
    alt: str
    species: str
    annotation: dict = Field(description="VEP annotation JSON")
    cached: bool = Field(description="Whether result was from cache")


class AnnotateResponse(BaseModel):
    """Annotation response for sync mode"""
    results: List[VariantAnnotation] = Field(description="Annotation results")
    cached_count: int = Field(description="Number of cached results")
    annotated_count: int = Field(description="Number of newly annotated")
    total_count: int = Field(description="Total variants processed")
    species: str = Field(description="Assembly used")
    processing_time_ms: Optional[float] = Field(None, description="Processing time")


class TaskCreateResponse(BaseModel):
    """Response for async task creation"""
    task_id: str = Field(description="Task UUID for polling")
    status: str = Field(default="pending", description="Initial task status")
    message: str = Field(default="Task created, poll for results", description="Status message")
    total_variants: int = Field(description="Number of variants submitted")


class TaskStatusResponse(BaseModel):
    """Task status response for polling"""
    task_id: str
    status: str = Field(description="pending/running/completed/failed")
    species: str
    mode: str
    total_variants: int
    result_count: Optional[int] = Field(None, description="Results available if completed")
    error_message: Optional[str] = Field(None, description="Error if failed")
    create_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: Optional[List[VariantAnnotation]] = Field(None, description="Results if completed")


class SpeciesInfo(BaseModel):
    """Species/assembly configuration info"""
    name: str = Field(description="Species name (GRCh37, GRCh38)")
    assembly: str = Field(description="Assembly version")
    alias: Optional[str] = Field(None, description="Common alias (hg19, hg38)")
    description: str = Field(description="Full description")
    enabled: bool = Field(description="Whether species is enabled")


class SpeciesListResponse(BaseModel):
    """List of supported species"""
    species: List[SpeciesInfo]
    default_species: str = Field(default="GRCh37", description="Default assembly")