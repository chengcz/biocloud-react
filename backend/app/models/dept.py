from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, event, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role import RoleModel
    from app.models.user import UserModel


class DeptModel(BaseModel):
    """
    部门表模型（层级结构）

    支持三层结构：组织 → 部门 → 亚组
    使用 dept_path 字段维护层级关系
    """
    __tablename__ = "sys_dept"

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="部门名称")
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_dept.id"),
        nullable=True,
        index=True,
        comment="父部门ID(None表示根部门)"
    )
    dept_path: Mapped[str] = mapped_column(
        String(500),
        default=".",
        index=True,
        comment="部门路径，格式：.父ID.当前ID. 例如：.1.5.12."
    )
    leader_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_user.id", use_alter=True, ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="负责人用户ID"
    )
    order_num: Mapped[int] = mapped_column(Integer, default=0, comment="显示顺序")

    # 关系
    parent: Mapped[Optional["DeptModel"]] = relationship(
        remote_side="DeptModel.id",
        back_populates="children",
        foreign_keys=[parent_id]
    )
    children: Mapped[list["DeptModel"]] = relationship(
        back_populates="parent",
        foreign_keys=[parent_id]
    )
    leader: Mapped[Optional["UserModel"]] = relationship(
        foreign_keys=[leader_user_id],
        post_update=True
    )
    users: Mapped[list["UserModel"]] = relationship(
        back_populates="dept",
        foreign_keys="UserModel.dept_id"
    )
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary="sys_role_to_sys_dept",
        back_populates="depts"
    )


@event.listens_for(DeptModel, "after_insert")
def update_dept_path_on_insert(mapper, connection, target):
    """新增部门时自动生成 dept_path"""
    if target.parent_id is None:
        dept_path = f".{target.id}."
    else:
        # 使用参数化查询防止 SQL 注入
        result = connection.execute(
            text("SELECT dept_path FROM sys_dept WHERE id = :parent_id"),
            {"parent_id": target.parent_id}
        )
        parent_path = result.scalar() or "."
        dept_path = f"{parent_path}{target.id}."

    # 使用参数化查询防止 SQL 注入
    connection.execute(
        text("UPDATE sys_dept SET dept_path = :dept_path WHERE id = :id"),
        {"dept_path": dept_path, "id": target.id}
    )