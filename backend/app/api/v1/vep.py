"""VEP Annotation API endpoints"""

import os
import tempfile
import time
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_active_user
from app.models import UserModel, AnnotationResult, VepTask, VepTaskStatus
from app.schemas.vep import (
    AnnotateRequest,
    AnnotateResponse,
    VariantAnnotation,
    TaskCreateResponse,
    TaskStatusResponse,
    SpeciesInfo,
    SpeciesListResponse,
)
from app.services.vep_runner import (
    load_species_config,
    get_species_config,
    run_vep_annotation_async,
    compute_variant_hash,
)
from app.services.vcf_parser import extract_variants_from_vcf, validate_vcf_format
from app.config.settings import settings

router = APIRouter(prefix="/vep", tags=["VEP Annotation"])


async def annotate_background_task(
    task_id: str,
    variants: List[dict],
    species: str,
    user_id: int
):
    """Background task for async annotation processing"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Create engine inside task to avoid passing credentials
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Update task status to running
            result = await db.execute(
                select(VepTask).where(VepTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task:
                task.task_status = VepTaskStatus.RUNNING.value
                task.start_time = datetime.now()
                await db.commit()

            # Run VEP annotation
            vep_results = await run_vep_annotation_async(variants, species)

            # Batch compute variant hashes
            variant_hashes = [
                compute_variant_hash(v["chrom"], v["pos"], v["ref"], v["alt"], species)
                for v in variants
            ]

            # Batch query all cached results (fixes N+1 query issue)
            cache_result = await db.execute(
                select(AnnotationResult).where(
                    AnnotationResult.variant_hash.in_(variant_hashes),
                    AnnotationResult.species == species
                )
            )
            cached_annotations = {a.variant_hash: a for a in cache_result.scalars().all()}

            # Process results and save to cache
            annotations = []
            new_annotations = []

            for i, vep_res in enumerate(vep_results):
                variant = variants[i]
                variant_hash = variant_hashes[i]

                cached = cached_annotations.get(variant_hash)

                if not cached:
                    # Collect new annotations for batch insert
                    new_annotations.append(AnnotationResult(
                        variant_hash=variant_hash,
                        species=species,
                        chrom=variant["chrom"],
                        pos=variant["pos"],
                        ref=variant["ref"],
                        alt=variant["alt"],
                        annotation_json=vep_res,
                        user_id=user_id,
                        status="active",
                        del_flag="0"
                    ))

                annotations.append({
                    "chrom": variant["chrom"],
                    "pos": variant["pos"],
                    "ref": variant["ref"],
                    "alt": variant["alt"],
                    "species": species,
                    "annotation": vep_res,
                    "cached": cached is not None
                })

            # Batch insert new annotations (single commit)
            if new_annotations:
                db.add_all(new_annotations)
                await db.commit()

            # Update task status to completed
            if task:
                task.task_status = VepTaskStatus.COMPLETED.value
                task.result_count = len(annotations)
                task.end_time = datetime.now()
                await db.commit()

        except Exception as e:
            # Update task status to failed
            if task:
                task.task_status = VepTaskStatus.FAILED.value
                task.error_message = str(e)
                task.end_time = datetime.now()
                await db.commit()


@router.post("/annotate", response_model=AnnotateResponse)
async def annotate_variants(
    request: AnnotateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Annotate genetic variants using VEP.

    Supports two modes:
    - sync: Returns results immediately (max 100 variants)
    - async: Creates background task, returns task_id for polling
    """
    start_time = time.time()
    species = request.species

    # Validate species
    try:
        get_species_config(species)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    variants = [{"chrom": v.chrom, "pos": v.pos, "ref": v.ref, "alt": v.alt} for v in request.variants]

    if request.mode == "async":
        # Create task record
        task = VepTask(
            task_id=str(uuid.uuid4()),
            task_status=VepTaskStatus.PENDING.value,
            input_data={"variants": variants},
            species=species,
            mode="async",
            user_id=current_user.id,
            status="active",
            del_flag="0"
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Launch background task
        background_tasks.add_task(
            annotate_background_task,
            task.task_id,
            variants,
            species,
            current_user.id
        )

        # Return task info
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "task_id": task.task_id,
                "status": "pending",
                "message": "Task created, poll for results",
                "total_variants": len(variants)
            }
        )

    # Sync mode - annotate immediately
    results = []
    cached_count = 0
    annotated_count = 0

    # Batch compute variant hashes
    variant_hashes = [
        compute_variant_hash(v["chrom"], v["pos"], v["ref"], v["alt"], species)
        for v in variants
    ]

    # Batch query all cached results (fixes N+1 query issue)
    cache_result = await db.execute(
        select(AnnotationResult).where(
            AnnotationResult.variant_hash.in_(variant_hashes),
            AnnotationResult.species == species
        )
    )
    cached_annotations = {a.variant_hash: a for a in cache_result.scalars().all()}

    # Identify variants that need annotation
    variants_to_annotate = []
    for i, variant in enumerate(variants):
        variant_hash = variant_hashes[i]
        cached = cached_annotations.get(variant_hash)

        if cached:
            results.append(VariantAnnotation(
                chrom=variant["chrom"],
                pos=variant["pos"],
                ref=variant["ref"],
                alt=variant["alt"],
                species=species,
                annotation=cached.annotation_json,
                cached=True
            ))
            cached_count += 1
        else:
            variants_to_annotate.append((i, variant, variant_hash))

    # Annotate remaining variants
    if variants_to_annotate:
        try:
            vep_results = await run_vep_annotation_async(
                [v[1] for v in variants_to_annotate], species
            )

            new_annotations = []
            for j, vep_res in enumerate(vep_results):
                i, variant, variant_hash = variants_to_annotate[j]

                # Collect for batch insert
                new_annotations.append(AnnotationResult(
                    variant_hash=variant_hash,
                    species=species,
                    chrom=variant["chrom"],
                    pos=variant["pos"],
                    ref=variant["ref"],
                    alt=variant["alt"],
                    annotation_json=vep_res,
                    user_id=current_user.id,
                    status="active",
                    del_flag="0"
                ))

                results.append(VariantAnnotation(
                    chrom=variant["chrom"],
                    pos=variant["pos"],
                    ref=variant["ref"],
                    alt=variant["alt"],
                    species=species,
                    annotation=vep_res,
                    cached=False
                ))
                annotated_count += 1

            # Batch insert (single commit)
            if new_annotations:
                db.add_all(new_annotations)
                await db.commit()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"VEP annotation failed: {str(e)}"
            )

    processing_time = (time.time() - start_time) * 1000

    return AnnotateResponse(
        results=results,
        cached_count=cached_count,
        annotated_count=annotated_count,
        total_count=len(variants),
        species=species,
        processing_time_ms=processing_time
    )


@router.post("/annotate/vcf", status_code=status.HTTP_202_ACCEPTED)
async def annotate_vcf_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    species: str = "GRCh37",
    mode: str = "async",
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Annotate variants from uploaded VCF file.

    Supports .vcf and .vcf.gz files.
    Max file size: 50MB
    """
    # Validate species
    try:
        get_species_config(species)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Validate file extension
    filename = file.filename or ""
    if not (filename.endswith(".vcf") or filename.endswith(".vcf.gz")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .vcf or .vcf.gz format"
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_VCF_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds limit ({settings.MAX_VCF_SIZE} bytes)"
        )

    # Save to temp file for parsing
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
    temp_file.write(content)
    temp_file.close()

    try:
        # Validate VCF format
        if not validate_vcf_format(temp_file.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid VCF file format"
            )

        # Extract variants
        variants = extract_variants_from_vcf(temp_file.name, max_variants=1000)

        if not variants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No variants found in VCF file"
            )

        # Create task record
        task = VepTask(
            task_id=str(uuid.uuid4()),
            task_status=VepTaskStatus.PENDING.value,
            input_data={"variants": variants, "filename": filename},
            species=species,
            mode=mode,
            user_id=current_user.id,
            status="active",
            del_flag="0"
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Launch background task
        background_tasks.add_task(
            annotate_background_task,
            task.task_id,
            variants,
            species,
            current_user.id
        )

        return TaskCreateResponse(
            task_id=task.task_id,
            status="pending",
            message="Task created, poll for results",
            total_variants=len(variants)
        )

    finally:
        # Cleanup temp file
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get annotation task status and results.

    Returns task status and results if completed.
    Only returns tasks owned by current user.
    """
    result = await db.execute(
        select(VepTask).where(
            VepTask.task_id == task_id,
            VepTask.user_id == current_user.id,
            VepTask.del_flag == "0"
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not owned by current user"
        )

    # Build response
    response = TaskStatusResponse(
        task_id=task.task_id,
        status=task.task_status,
        species=task.species,
        mode=task.mode,
        total_variants=len(task.input_data.get("variants", [])),
        result_count=task.result_count,
        error_message=task.error_message,
        create_time=task.create_time,
        start_time=task.start_time,
        end_time=task.end_time,
        results=None
    )

    # If completed, fetch results
    if task.task_status == VepTaskStatus.COMPLETED.value:
        # Get annotation results
        variants = task.input_data.get("variants", [])
        annotations = []

        for variant in variants:
            variant_hash = compute_variant_hash(
                variant["chrom"],
                variant["pos"],
                variant["ref"],
                variant["alt"],
                task.species
            )

            cache_result = await db.execute(
                select(AnnotationResult).where(
                    AnnotationResult.variant_hash == variant_hash,
                    AnnotationResult.species == task.species
                )
            )
            cached = cache_result.scalar_one_or_none()

            if cached:
                annotations.append(VariantAnnotation(
                    chrom=cached.chrom,
                    pos=cached.pos,
                    ref=cached.ref,
                    alt=cached.alt,
                    species=cached.species,
                    annotation=cached.annotation_json,
                    cached=True
                ))

        response.results = annotations

    return response


@router.get("/species", response_model=SpeciesListResponse)
async def get_species_list():
    """
    Get list of supported species/assembly configurations.

    Public endpoint - no authentication required.
    """
    config = load_species_config()
    species_list = []

    for sp in config.get("species", []):
        species_list.append(SpeciesInfo(
            name=sp.get("name", ""),
            assembly=sp.get("assembly", ""),
            alias=sp.get("alias"),
            description=sp.get("description", ""),
            enabled=sp.get("enabled", True)
        ))

    return SpeciesListResponse(
        species=species_list,
        default_species="GRCh37"
    )