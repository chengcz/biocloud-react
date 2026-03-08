"""User management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.api.deps import get_db, get_current_user, PaginationParams, CheckPermission
from app.models import UserModel, DeptModel, RoleModel, PermissionModel
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    DeptCreate,
    DeptUpdate,
    DeptResponse,
    DeptTreeResponse,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionResponse,
)
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundException, ConflictException

router = APIRouter(prefix="/users", tags=["User Management"])


# ============ User Endpoints ============

@router.get("", response_model=dict)
async def list_users(
    pagination: PaginationParams = Depends(),
    dept_id: int = None,
    status: str = None,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List users with pagination"""
    query = select(UserModel).where(UserModel.del_flag == "0")

    if dept_id:
        query = query.where(UserModel.dept_id == dept_id)
    if status:
        query = query.where(UserModel.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.offset(pagination.offset).limit(pagination.limit).order_by(UserModel.id.desc())
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("user:create"))
):
    """Create new user"""
    # Check username uniqueness
    result = await db.execute(
        select(UserModel).where(UserModel.user_name == request.username)
    )
    if result.scalar_one_or_none():
        raise ConflictException("Username already exists")

    # Create user
    user = UserModel(
        user_name=request.username,
        password_hash=get_password_hash(request.password),
        name=request.name,
        email=request.email,
        phone=request.phone,
        dept_id=request.dept_id,
        post_id=request.post_id,
        leader_id=request.leader_id,
        status="active",
        del_flag="0"
    )

    # Assign roles
    if request.role_ids:
        result = await db.execute(
            select(RoleModel).where(RoleModel.id.in_(request.role_ids))
        )
        user.roles = list(result.scalars().all())

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserModel = Depends(get_current_user)
):
    """Get user by ID"""
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.del_flag == "0")
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User")

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("user:update"))
):
    """Update user"""
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.del_flag == "0")
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User")

    # Update fields
    update_data = request.model_dump(exclude_unset=True, exclude={"role_ids"})

    for field, value in update_data.items():
        setattr(user, field, value)

    # Update roles
    if request.role_ids is not None:
        result = await db.execute(
            select(RoleModel).where(RoleModel.id.in_(request.role_ids))
        )
        user.roles = list(result.scalars().all())

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("user:delete"))
):
    """Delete user (soft delete)"""
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.del_flag == "0")
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User")

    user.del_flag = "1"
    await db.commit()

    return {"message": "User deleted successfully"}


# ============ Department Endpoints ============

dept_router = APIRouter(prefix="/departments", tags=["Department Management"])


@dept_router.get("", response_model=List[DeptTreeResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: UserModel = Depends(get_current_user)
):
    """List all departments as tree structure"""
    result = await db.execute(
        select(DeptModel).where(DeptModel.del_flag == "0").order_by(DeptModel.order_num)
    )
    departments = result.scalars().all()

    # Build tree
    dept_map = {d.id: DeptTreeResponse.model_validate(d) for d in departments}
    roots = []

    for dept in departments:
        dept_response = dept_map[dept.id]

        # Count users in this department
        count_result = await db.execute(
            select(func.count()).where(
                UserModel.dept_id == dept.id,
                UserModel.del_flag == "0"
            )
        )
        dept_response.user_count = count_result.scalar() or 0

        if dept.parent_id is None:
            roots.append(dept_response)
        elif dept.parent_id in dept_map:
            dept_map[dept.parent_id].children.append(dept_response)

    return roots


@dept_router.post("", response_model=DeptResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    request: DeptCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("dept:create"))
):
    """Create department"""
    dept = DeptModel(
        name=request.name,
        parent_id=request.parent_id,
        leader_user_id=request.leader_user_id,
        order_num=request.order_num,
        status="active",
        del_flag="0"
    )

    db.add(dept)
    await db.commit()
    await db.refresh(dept)

    return dept


@dept_router.put("/{dept_id}", response_model=DeptResponse)
async def update_department(
    dept_id: int,
    request: DeptUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("dept:update"))
):
    """Update department"""
    result = await db.execute(
        select(DeptModel).where(DeptModel.id == dept_id, DeptModel.del_flag == "0")
    )
    dept = result.scalar_one_or_none()

    if not dept:
        raise NotFoundException("Department")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dept, field, value)

    await db.commit()
    await db.refresh(dept)

    return dept


@dept_router.delete("/{dept_id}")
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("dept:delete"))
):
    """Delete department (soft delete)"""
    result = await db.execute(
        select(DeptModel).where(DeptModel.id == dept_id, DeptModel.del_flag == "0")
    )
    dept = result.scalar_one_or_none()

    if not dept:
        raise NotFoundException("Department")

    # Check if has children
    child_result = await db.execute(
        select(DeptModel).where(
            DeptModel.parent_id == dept_id,
            DeptModel.del_flag == "0"
        )
    )
    if child_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with children"
        )

    dept.del_flag = "1"
    await db.commit()

    return {"message": "Department deleted successfully"}


# ============ Role Endpoints ============

role_router = APIRouter(prefix="/roles", tags=["Role Management"])


@role_router.get("", response_model=List[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: UserModel = Depends(get_current_user)
):
    """List all roles"""
    result = await db.execute(
        select(RoleModel).where(RoleModel.del_flag == "0").order_by(RoleModel.id)
    )
    return list(result.scalars().all())


@role_router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("role:create"))
):
    """Create role"""
    role = RoleModel(
        name=request.name,
        role_key=request.role_key,
        parent_id=request.parent_id,
        data_scope_type=request.data_scope_type,
        remark=request.remark,
        status="active",
        del_flag="0"
    )

    # Assign permissions
    if request.permission_ids:
        result = await db.execute(
            select(PermissionModel).where(PermissionModel.id.in_(request.permission_ids))
        )
        role.permissions = list(result.scalars().all())

    # Assign departments
    if request.dept_ids:
        result = await db.execute(
            select(DeptModel).where(DeptModel.id.in_(request.dept_ids))
        )
        role.depts = list(result.scalars().all())

    db.add(role)
    await db.commit()
    await db.refresh(role)

    return role


@role_router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    request: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("role:update"))
):
    """Update role"""
    result = await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.del_flag == "0")
    )
    role = result.scalar_one_or_none()

    if not role:
        raise NotFoundException("Role")

    update_data = request.model_dump(exclude_unset=True, exclude={"permission_ids", "dept_ids"})

    for field, value in update_data.items():
        setattr(role, field, value)

    if request.permission_ids is not None:
        result = await db.execute(
            select(PermissionModel).where(PermissionModel.id.in_(request.permission_ids))
        )
        role.permissions = list(result.scalars().all())

    if request.dept_ids is not None:
        result = await db.execute(
            select(DeptModel).where(DeptModel.id.in_(request.dept_ids))
        )
        role.depts = list(result.scalars().all())

    await db.commit()
    await db.refresh(role)

    return role


@role_router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(CheckPermission("role:delete"))
):
    """Delete role (soft delete)"""
    result = await db.execute(
        select(RoleModel).where(RoleModel.id == role_id, RoleModel.del_flag == "0")
    )
    role = result.scalar_one_or_none()

    if not role:
        raise NotFoundException("Role")

    role.del_flag = "1"
    await db.commit()

    return {"message": "Role deleted successfully"}