from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.models.base import BaseModel


class AnalysisStatus(str, Enum):
    """分析状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisType(str, Enum):
    """分析类型"""
    # 转录组
    VOLCANO_PLOT = "volcano_plot"
    HEATMAP = "heatmap"
    GO_ENRICHMENT = "go_enrichment"
    KEGG_ENRICHMENT = "kegg_enrichment"
    # 基因组
    SNP_DENSITY = "snp_density"
    CIRCOS = "circos"
    VCF_ANALYSIS = "vcf_analysis"
    # 蛋白质组
    PROTEIN_NETWORK = "protein_network"
    # 微生物组
    TAXONOMY_PLOT = "taxonomy_plot"
    ALPHA_DIVERSITY = "alpha_diversity"
    BETA_DIVERSITY = "beta_diversity"


class UploadedFileModel(BaseModel):
    """上传文件表"""
    __tablename__ = "uploaded_files"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_user.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="存储文件名")
    original_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_type: Mapped[str] = mapped_column(String(50), comment="文件类型")
    file_size: Mapped[int] = mapped_column(Integer, comment="文件大小(字节)")
    storage_path: Mapped[str] = mapped_column(String(500), comment="存储路径")

    # 关系
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id])


class AnalysisModel(BaseModel):
    """分析任务表"""
    __tablename__ = "analyses"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_user.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
        comment="关联对话ID"
    )
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="SET NULL"),
        comment="关联消息ID"
    )
    analysis_type: Mapped[AnalysisType] = mapped_column(
        SQLEnum(AnalysisType),
        nullable=False,
        comment="分析类型"
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        comment="分析状态"
    )
    input_file_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        comment="输入文件ID"
    )
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, comment="分析参数")
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, comment="结果数据")
    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="错误信息")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="完成时间")

    # 关系
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id])
    conversation: Mapped[Optional["ConversationModel"]] = relationship(back_populates="analyses")
    input_file: Mapped[Optional["UploadedFileModel"]] = relationship(foreign_keys=[input_file_id])