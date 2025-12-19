"""
Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class SessionStatus(str, Enum):
    """会话状态枚举"""
    WAITING_FOR_B = "waiting_for_b"
    BOTH_COMMITTED = "both_committed"
    REVEALED = "revealed"


class ComparisonResult(str, Enum):
    """比较结果枚举"""
    HIGHER = "higher"
    LOWER = "lower"
    EQUAL = "equal"


# ============ Request Models ============

class PrivacyLevel(str, Enum):
    """隐私级别枚举"""
    MINIMAL = "minimal"    # 仅显示比较结果，不透露档次
    DETAILED = "detailed"  # 显示双方具体档次


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    company_name: str = Field(..., min_length=1, max_length=100, description="公司名称")
    privacy_level: str = Field(
        default="detailed", 
        pattern="^(minimal|detailed)$",
        description="隐私级别: minimal(仅比较结果) 或 detailed(显示档次)"
    )


class JoinSessionRequest(BaseModel):
    """加入会话请求"""
    session_id: str = Field(..., min_length=1, description="会话ID")
    company_name: str = Field(..., min_length=1, max_length=100, description="公司名称")


class CommitRequest(BaseModel):
    """提交承诺请求"""
    session_id: str = Field(..., description="会话ID")
    role: str = Field(..., pattern="^(company_a|company_b)$", description="角色")
    amount: float = Field(..., gt=0, description="流水金额")


class RevealRequest(BaseModel):
    """揭示结果请求"""
    session_id: str = Field(..., description="会话ID")
    role: str = Field(..., pattern="^(company_a|company_b)$", description="角色")


# ============ Response Models ============

class LevelInfo(BaseModel):
    """档次信息"""
    level: int = Field(..., ge=1, le=5, description="档次等级")
    name: str = Field(..., description="档次名称")
    description: str = Field(..., description="档次描述")
    min: float = Field(..., description="最小金额")
    max: float = Field(..., description="最大金额")


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    success: bool
    session_id: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None


class JoinSessionResponse(BaseModel):
    """加入会话响应"""
    success: bool
    session_id: Optional[str] = None
    role: Optional[str] = None
    company_a_name: Optional[str] = None
    message: Optional[str] = None


class CommitResponse(BaseModel):
    """提交承诺响应"""
    success: bool
    commitment: Optional[str] = None
    level_info: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    message: Optional[str] = None


class CompanyResult(BaseModel):
    """公司比较结果"""
    name: str
    level_info: Dict[str, Any]


class RevealResultData(BaseModel):
    """揭示结果数据"""
    comparison: str
    message: str
    company_a: CompanyResult
    company_b: CompanyResult


class RevealResponse(BaseModel):
    """揭示结果响应"""
    success: bool
    result: Optional[RevealResultData] = None
    message: Optional[str] = None


class SessionStatusResponse(BaseModel):
    """会话状态响应"""
    success: bool
    status: Optional[str] = None
    company_a_committed: Optional[bool] = None
    company_b_committed: Optional[bool] = None
    company_b_joined: Optional[bool] = None
    message: Optional[str] = None


class UploadFilesResponse(BaseModel):
    """文件上传响应"""
    success: bool
    message: str
    files: Optional[Dict[str, str]] = None


class LevelsResponse(BaseModel):
    """档次列表响应"""
    success: bool
    levels: List[Dict[str, Any]]


class HistoryItem(BaseModel):
    """历史记录项"""
    session_id: str
    created_at: str
    company_a_name: str
    company_b_name: str
    result: Dict[str, Any]


class HistoryResponse(BaseModel):
    """历史记录响应"""
    success: bool
    count: int
    history: List[HistoryItem]

