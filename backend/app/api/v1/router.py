"""
API v1 路由聚合
"""
from fastapi import APIRouter
from .mpc import router as mpc_router
from .edr import router as edr_router

router = APIRouter()

# 注册 MPC 验证路由
router.include_router(mpc_router, prefix="/mpc", tags=["MPC验证"])

# 注册 EDR 公开信息分析路由
router.include_router(edr_router, prefix="/edr", tags=["EDR公开信息分析"])

