"""
Risk Orchestrator - 企业合作风险与信任评估系统

主入口文件
"""
import os

# 加载 .env 文件（必须在其他导入之前）
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .core.config import settings
from .api.v1 import router as api_v1_router

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# 获取前端目录路径
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

# 挂载静态文件
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """返回前端页面"""
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Welcome to Risk Orchestrator API",
        "docs": "/docs",
        "version": settings.VERSION
    }


@app.get("/edr")
async def edr_page():
    """EDR 公开信息分析页面"""
    edr_file = os.path.join(TEMPLATES_DIR, "edr.html")
    if os.path.exists(edr_file):
        return FileResponse(edr_file)
    return {"error": "EDR 页面未找到"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.VERSION}


# ============ 兼容旧 API 路径 (与 secret 项目保持一致) ============

from .api.v1.mpc import (
    create_session, join_session, upload_files, commit, reveal,
    get_session_status, get_levels, get_history, export_session,
    mpc_engine
)
from .models.schemas import (
    CreateSessionRequest, JoinSessionRequest, CommitRequest, RevealRequest
)


@app.post("/api/create_session")
async def compat_create_session(request: CreateSessionRequest):
    """兼容旧API: 创建会话"""
    return await create_session(request)


@app.post("/api/join_session")
async def compat_join_session(request: JoinSessionRequest):
    """兼容旧API: 加入会话"""
    return await join_session(request)


@app.post("/api/upload_files")
async def compat_upload_files(request: Request):
    """兼容旧API: 上传文件"""
    from fastapi import UploadFile, Form, File
    form = await request.form()
    session_id = form.get('session_id')
    role = form.get('role')
    bank_statement = form.get('bank_statement')
    commitment_letter = form.get('commitment_letter')
    
    return await upload_files(
        session_id=session_id,
        role=role,
        bank_statement=bank_statement,
        commitment_letter=commitment_letter
    )


@app.post("/api/commit")
async def compat_commit(request: CommitRequest):
    """兼容旧API: 提交承诺"""
    return await commit(request)


@app.post("/api/reveal")
async def compat_reveal(request: RevealRequest):
    """兼容旧API: 揭示结果"""
    return await reveal(request)


@app.get("/api/session_status")
async def compat_session_status(session_id: str):
    """兼容旧API: 获取会话状态"""
    return await get_session_status(session_id)


@app.get("/api/levels")
async def compat_levels():
    """兼容旧API: 获取档次信息"""
    return await get_levels()


@app.get("/api/history")
async def compat_history():
    """兼容旧API: 获取历史记录"""
    return await get_history()


@app.get("/api/export/{session_id}")
async def compat_export(session_id: str):
    """兼容旧API: 导出会话"""
    return await export_session(session_id)

