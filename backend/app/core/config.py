"""
系统配置模块
"""
import os
from typing import List

class Settings:
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "Risk Orchestrator"
    PROJECT_DESCRIPTION: str = "企业合作风险与信任评估系统"
    VERSION: str = "1.0.0"
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 文件上传配置
    UPLOAD_FOLDER: str = "uploads"
    DATA_FOLDER: str = "data"
    ALLOWED_EXTENSIONS: set = {"pdf", "png", "jpg", "jpeg"}
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 会话过期时间（秒）
    SESSION_EXPIRE_TIME: int = 3600  # 1小时
    
    def __init__(self):
        # 确保目录存在
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.DATA_FOLDER, exist_ok=True)


settings = Settings()

