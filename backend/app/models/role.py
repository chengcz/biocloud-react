from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Boolean, Table, Column, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, DataScopeType

if TYPE_CHECKING:
    from app.models.user import UserModel
    from app.models.dept import DeptModel


# 角色-权限 关联表
role_to_permission = Table(
    "sys_role_to_permission",
    BaseModel.metadata,
    Column("role_id", Integer, ForeignKey("sys_role.id"), primary_key=True, comment="角色ID"),
    Column("permission_id", Integer, ForeignKey("sys_permission.id"), primary_key=True, comment="权限ID"),
    comment="角色-权限关联表"
)

# 角色-用户 关联表
role_to_user = Table(
    "sys_role_to_sys_user",
    BaseModel.metadata,
    Column("role_id", Integer, ForeignKey("sys_role.id"), primary_key=True, comment="角色ID"),
    Column("user_id", Integer, ForeignKey("sys_user.id"), primary_key=True, comment="用户ID"),
    comment="角色-用户关联表"
)

# 角色-部门 关联表
role_to_dept = Table(
    "sys_role_to_sys_dept",
    BaseModel.metadata,
    Column("role_id", Integer, ForeignKey("sys_role.id"), primary_key=True, comment="角色ID"),
    Column("dept_id", Integer, ForeignKey("sys_dept.id"), primary_key=True, comment="部门ID"),
    comment="角色-部门关联表"
)


class PermissionModel(BaseModel):
    """权限表"""
    __tablename__ = "sys_permission"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="权限标识")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限名称")
    description: Mapped[str | None] = mapped_column(String(255), comment="权限描述")

    # 关系
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=role_to_permission,
        back_populates="permissions"
    )


class RoleModel(BaseModel):
    """
    角色表模型

    支持角色继承和数据权限范围
    """
    __tablename__ = "sys_role"

    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="角色名称")
    role_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="角色标识")
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_role.id"),
        comment="父角色ID(用于角色继承)"
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否超级管理员")
    data_scope_type: Mapped[DataScopeType] = mapped_column(
        SQLEnum(DataScopeType),
        nullable=False,
        default=DataScopeType.SELF,
        comment="数据权限范围"
    )
    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")

    # 关系
    permissions: Mapped[list["PermissionModel"]] = relationship(
        secondary=role_to_permission,
        back_populates="roles"
    )
    users: Mapped[list["UserModel"]] = relationship(
        secondary=role_to_user,
        back_populates="roles"
    )
    depts: Mapped[list["DeptModel"]] = relationship(
        secondary=role_to_dept,
        back_populates="roles"
    )
    parent: Mapped["RoleModel | None"] = relationship(
        remote_side="RoleModel.id",
        foreign_keys=[parent_id]
    )