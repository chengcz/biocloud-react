"""Pydantic schemas for user management"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    name: str = Field(..., min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    sex: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)
    dept_id: Optional[int] = None
    post_id: Optional[int] = None
    leader_id: Optional[int] = None
    role_ids: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """User update schema"""
    name: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    sex: Optional[str] = None
    avatar: Optional[str] = None
    dept_id: Optional[int] = None
    post_id: Optional[int] = None
    leader_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    username: str = Field(alias="user_name")
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    sex: Optional[str] = None
    dept_id: Optional[int] = None
    post_id: Optional[int] = None
    leader_id: Optional[int] = None
    status: str
    login_ip: Optional[str] = None
    login_date: Optional[datetime] = None
    create_time: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class UserDetailResponse(UserResponse):
    """Detailed user response with relationships"""
    dept: Optional["DeptBrief"] = None
    post: Optional["PostBrief"] = None
    leader: Optional["UserBrief"] = None
    roles: List["RoleBrief"] = Field(default_factory=list)


class UserBrief(BaseModel):
    """Brief user info for nested responses"""
    id: int
    username: str = Field(alias="user_name")
    name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class DeptBase(BaseModel):
    """Base department schema"""
    name: str = Field(..., max_length=50)
    parent_id: Optional[int] = None
    order_num: int = 0


class DeptCreate(DeptBase):
    """Department creation schema"""
    leader_user_id: Optional[int] = None


class DeptUpdate(BaseModel):
    """Department update schema"""
    name: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    leader_user_id: Optional[int] = None
    order_num: Optional[int] = None
    status: Optional[str] = None


class DeptBrief(BaseModel):
    """Brief department info"""
    id: int
    name: str

    class Config:
        from_attributes = True


class DeptResponse(DeptBrief):
    """Department response schema"""
    parent_id: Optional[int] = None
    dept_path: str
    leader_user_id: Optional[int] = None
    order_num: int
    status: str
    create_time: datetime

    class Config:
        from_attributes = True


class DeptTreeResponse(DeptResponse):
    """Department tree response with children"""
    children: List["DeptTreeResponse"] = Field(default_factory=list)
    leader: Optional[UserBrief] = None
    user_count: int = 0


class PostBase(BaseModel):
    """Base post schema"""
    name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=64)
    dept_id: Optional[int] = None
    order_num: int = 0


class PostCreate(PostBase):
    """Post creation schema"""
    pass


class PostUpdate(BaseModel):
    """Post update schema"""
    name: Optional[str] = None
    code: Optional[str] = None
    dept_id: Optional[int] = None
    order_num: Optional[int] = None
    status: Optional[str] = None


class PostBrief(BaseModel):
    """Brief post info"""
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class PostResponse(PostBrief):
    """Post response schema"""
    dept_id: Optional[int] = None
    order_num: int
    status: str
    create_time: datetime

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema"""
    name: str = Field(..., max_length=30)
    role_key: str = Field(..., max_length=100)
    parent_id: Optional[int] = None
    data_scope_type: str = "self"
    remark: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation schema"""
    permission_ids: List[int] = []
    dept_ids: List[int] = []


class RoleUpdate(BaseModel):
    """Role update schema"""
    name: Optional[str] = None
    role_key: Optional[str] = None
    parent_id: Optional[int] = None
    data_scope_type: Optional[str] = None
    is_admin: Optional[bool] = None
    remark: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    dept_ids: Optional[List[int]] = None
    status: Optional[str] = None


class RoleBrief(BaseModel):
    """Brief role info"""
    id: int
    name: str
    role_key: str

    class Config:
        from_attributes = True


class RoleResponse(RoleBrief):
    """Role response schema"""
    parent_id: Optional[int] = None
    is_admin: bool
    data_scope_type: str
    remark: Optional[str] = None
    status: str
    create_time: datetime

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """Base permission schema"""
    key: str = Field(..., max_length=100)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    """Permission creation schema"""
    pass


class PermissionResponse(PermissionBase):
    """Permission response schema"""
    id: int
    status: str
    create_time: datetime

    class Config:
        from_attributes = True


# Update forward references
UserDetailResponse.model_rebuild()
DeptTreeResponse.model_rebuild()