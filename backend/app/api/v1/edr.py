"""
EDR 公开信息分析 API 路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio

from ...engines.edr import EDRLiteEngine

router = APIRouter()

# 初始化 EDR 引擎
edr_engine = EDRLiteEngine()


class AnalyzeCompanyRequest(BaseModel):
    """分析企业请求"""
    company_name: str = Field(..., min_length=2, max_length=100, description="公司名称")
    include_reputation: bool = Field(default=True, description="是否包含口碑分析")


class QuickSearchRequest(BaseModel):
    """快速搜索请求"""
    company_name: str = Field(..., min_length=2, max_length=100, description="公司名称")


# 存储异步任务结果
analysis_results: Dict[str, Any] = {}


async def run_analysis(task_id: str, company_name: str, include_reputation: bool):
    """后台执行分析任务"""
    result = await edr_engine.analyze_company(
        company_name=company_name,
        include_reputation=include_reputation
    )
    analysis_results[task_id] = result


@router.post("/analyze")
async def analyze_company(request: AnalyzeCompanyRequest, background_tasks: BackgroundTasks):
    """
    分析企业风险画像（异步）
    
    返回任务ID，可通过 /tasks/{task_id} 查询结果
    """
    from datetime import datetime
    task_id = f"edr_{datetime.now().strftime('%Y%m%d%H%M%S')}_{request.company_name[:10]}"
    
    # 初始化任务状态
    analysis_results[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "company_name": request.company_name
    }
    
    # 添加后台任务
    background_tasks.add_task(
        run_analysis,
        task_id,
        request.company_name,
        request.include_reputation
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"分析任务已创建，正在分析 {request.company_name}"
    }


@router.post("/analyze/sync")
async def analyze_company_sync(request: AnalyzeCompanyRequest):
    """
    分析企业风险画像（同步，等待完成）
    
    注意：此接口可能需要较长时间（30-60秒）
    """
    result = await edr_engine.analyze_company(
        company_name=request.company_name,
        include_reputation=request.include_reputation
    )
    
    return result


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取分析任务状态和结果"""
    # 先检查全局结果存储
    if task_id in analysis_results:
        result = analysis_results[task_id]
        if "analysis" in result:
            return {"success": True, "status": "completed", "result": result}
        return {"success": True, "status": "running", "task_id": task_id}
    
    # 检查引擎内部状态
    task_status = edr_engine.get_task_status(task_id)
    if task_status:
        return {"success": True, **task_status}
    
    raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/search")
async def quick_search(request: QuickSearchRequest):
    """
    快速搜索企业公开信息（不进行 AI 分析）
    """
    result = await edr_engine.quick_search(request.company_name)
    return {"success": True, **result}


@router.delete("/cache/{company_name}")
async def clear_company_cache(company_name: str):
    """清除指定公司的缓存"""
    count = edr_engine.cache.clear(company_name)
    return {
        "success": True,
        "message": f"已清除 {company_name} 的缓存" if count > 0 else "缓存不存在",
        "cleared": count
    }


@router.delete("/cache")
async def clear_all_cache():
    """清除所有缓存"""
    count = edr_engine.cache.clear()
    return {
        "success": True,
        "message": f"已清除 {count} 个缓存",
        "cleared": count
    }


@router.get("/cache")
async def list_cache():
    """列出所有缓存"""
    cached = edr_engine.cache.list_cached()
    return {
        "success": True,
        "count": len(cached),
        "items": cached
    }


@router.get("/health")
async def health_check():
    """EDR 模块健康检查"""
    import os
    
    tavily_configured = bool(os.getenv("TAVILY_API_KEY"))
    deepseek_configured = bool(os.getenv("DEEPSEEK_API_KEY"))
    
    return {
        "module": "EDR Lite",
        "status": "healthy" if (tavily_configured and deepseek_configured) else "degraded",
        "tavily_api": "configured" if tavily_configured else "missing",
        "deepseek_api": "configured" if deepseek_configured else "missing"
    }

