"""
EDR Lite 引擎

企业公开信息分析的主引擎，整合搜索和分析功能
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .search import TavilySearchClient
from .analyzer import RiskAnalyzer
from .llm_client import DeepSeekClient
from .cache import EDRCache

logger = logging.getLogger(__name__)


class EDRLiteEngine:
    """EDR Lite 公开信息分析引擎"""
    
    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        cache_hours: int = 24
    ):
        self.search_client = TavilySearchClient(api_key=tavily_api_key)
        self.llm_client = DeepSeekClient(api_key=deepseek_api_key)
        self.analyzer = RiskAnalyzer(llm_client=self.llm_client)
        self.cache = EDRCache(cache_hours=cache_hours)
        
        # 存储分析任务
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    async def analyze_company(
        self,
        company_name: str,
        include_reputation: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        分析企业风险画像
        
        Args:
            company_name: 公司名称
            include_reputation: 是否包含口碑分析
            progress_callback: 进度回调函数 (stage, progress)
            use_cache: 是否使用缓存（默认启用）
        
        Returns:
            完整的风险分析结果
        """
        # 检查缓存
        if use_cache:
            cached_result = self.cache.get(company_name)
            if cached_result:
                logger.info(f"返回缓存结果: {company_name}")
                if progress_callback:
                    progress_callback("从缓存加载", 100)
                return cached_result
        
        task_id = f"edr_{datetime.now().strftime('%Y%m%d%H%M%S')}_{company_name[:10]}"
        
        self.tasks[task_id] = {
            "task_id": task_id,
            "company_name": company_name,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": 0,
            "current_stage": "初始化"
        }
        
        try:
            # 阶段1: 搜索企业基础信息
            self._update_progress(task_id, "搜索企业基础信息", 10, progress_callback)
            company_info = await self.search_client.search_company_info(company_name)
            
            # 阶段2: 搜索企业新闻
            self._update_progress(task_id, "搜索企业新闻动态", 30, progress_callback)
            news_info = await self.search_client.search_company_news(company_name)
            
            # 阶段3: 搜索企业口碑（可选）
            reputation_info = None
            if include_reputation:
                self._update_progress(task_id, "搜索企业口碑评价", 50, progress_callback)
                reputation_info = await self.search_client.search_company_reputation(company_name)
            
            # 阶段4: AI 分析
            self._update_progress(task_id, "AI 深度分析中", 70, progress_callback)
            analysis_result = await self.analyzer.analyze_company(
                company_name=company_name,
                company_info=company_info,
                news_info=news_info,
                reputation_info=reputation_info
            )
            
            # 完成
            self._update_progress(task_id, "分析完成", 100, progress_callback)
            
            # 构建最终结果
            result = {
                "task_id": task_id,
                "success": True,
                "company_name": company_name,
                "analysis": analysis_result.get("analysis", ""),
                "score": analysis_result.get("score", 0),
                "risk_level": analysis_result.get("risk_level", "未知"),
                "sources": {
                    "company_info": len(company_info.get("results", [])),
                    "news": len(news_info.get("results", [])),
                    "reputation": len(reputation_info.get("results", [])) if reputation_info else 0
                },
                "analyzed_at": datetime.now().isoformat(),
                "from_cache": False
            }
            
            # 保存到缓存
            if use_cache:
                self.cache.set(company_name, result)
            
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = result
            
            return result
            
        except Exception as e:
            logger.error(f"企业分析失败: {e}")
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = str(e)
            
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "company_name": company_name
            }
    
    def _update_progress(
        self,
        task_id: str,
        stage: str,
        progress: int,
        callback: Optional[Callable[[str, int], None]] = None
    ):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]["current_stage"] = stage
            self.tasks[task_id]["progress"] = progress
        
        if callback:
            callback(stage, progress)
        
        logger.info(f"[{task_id}] {stage} - {progress}%")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    async def quick_search(self, company_name: str) -> Dict[str, Any]:
        """
        快速搜索企业信息（不进行 AI 分析）
        
        Args:
            company_name: 公司名称
        
        Returns:
            搜索结果
        """
        company_info = await self.search_client.search_company_info(company_name)
        news_info = await self.search_client.search_company_news(company_name)
        
        return {
            "company_name": company_name,
            "company_info": company_info.get("results", []),
            "news": news_info.get("results", []),
            "searched_at": datetime.now().isoformat()
        }

