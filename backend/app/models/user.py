from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean, Table, Column, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.dept import DeptModel
    from app.models.role import RoleModel


# 岗位表
class PostModel(BaseModel):
    """岗位表"""
    __tablename__ = "sys_post"

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="岗位名称")
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="岗位编码")
    dept_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_dept.id"),
        comment="所属部门ID"
    )
    order_num: Mapped[int] = mapped_column(Integer, default=0, comment="显示顺序")

    # 关系
    dept: Mapped[Optional["DeptModel"]] = relationship(foreign_keys=[dept_id])
    users: Mapped[list["UserModel"]] = relationship(back_populates="post")


# 用户表
class UserModel(BaseModel):
    """
    用户表模型

    支持三层权限结构：
    - 用户属于部门(dept)
    - 用户有岗位(post)
    - 用户有上级领导(leader)
    - 用户有多个角色(roles)
    """
    __tablename__ = "sys_user"

    # 基本信息
    user_name: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="用户账号"
    )
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="用户昵称")
    email: Mapped[Optional[str]] = mapped_column(String(50), index=True, comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment="手机号")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment="头像URL")
    sex: Mapped[Optional[str]] = mapped_column(String(10), comment="性别")

    # 密码和安全
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")

    # 组织关系
    dept_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_dept.id"),
        index=True,
        comment="部门ID"
    )
    post_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_post.id"),
        index=True,
        comment="岗位ID"
    )
    leader_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_user.id"),
        index=True,
        comment="上级领导ID"
    )

    # 登录信息
    login_ip: Mapped[Optional[str]] = mapped_column(String(128), comment="最后登录IP")
    login_date: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="最后登录时间")
    session_token: Mapped[Optional[str]] = mapped_column(String(255), comment="会话Token")

    # 关系
    dept: Mapped[Optional["DeptModel"]] = relationship(
        back_populates="users",
        foreign_keys=[dept_id]
    )
    post: Mapped[Optional["PostModel"]] = relationship(
        back_populates="users",
        foreign_keys=[post_id]
    )
    leader: Mapped[Optional["UserModel"]] = relationship(
        remote_side="UserModel.id",
        foreign_keys=[leader_id]
    )
    led_users: Mapped[list["UserModel"]] = relationship(
        back_populates="leader",
        foreign_keys=[leader_id]
    )
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary="sys_role_to_sys_user",
        back_populates="users"
    )


@event.listens_for(UserModel, 'before_insert')
@event.listens_for(UserModel, 'before_update')
def validate_user_name(mapper, connection, target):
    """校验用户名不能包含中文字符"""
    if target.user_name and any('\u4e00' <= char <= '\u9fff' for char in target.user_name):
        raise ValueError("用户名不能包含中文字符")