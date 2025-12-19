"""
搜索客户端模块

使用 Tavily API 进行企业公开信息搜索
"""
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TavilySearchClient:
    """Tavily 搜索客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("TAVILY_API_KEY 未设置，搜索功能将不可用")
    
    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            搜索结果
        """
        if not self.api_key:
            return {"results": [], "error": "TAVILY_API_KEY 未设置"}
        
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            
            # 限制查询长度
            if len(query) > 400:
                query = query[:397] + "..."
            
            response = client.search(
                query=query,
                max_results=max_results,
                include_answer=True,
                include_raw_content=True
            )
            
            return {
                "results": response.get("results", []),
                "answer": response.get("answer", ""),
                "query": query
            }
        except Exception as e:
            logger.error(f"Tavily 搜索失败: {e}")
            return {"results": [], "error": str(e)}
    
    async def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """
        搜索企业基础信息
        
        Args:
            company_name: 公司名称
        
        Returns:
            企业信息搜索结果
        """
        queries = [
            f"{company_name} 公司简介 注册信息 经营范围",
            f"{company_name} 企业信息 股东 法人"
        ]
        
        all_results = []
        for query in queries:
            result = await self.search(query, max_results=3)
            all_results.extend(result.get("results", []))
        
        return {
            "type": "company_info",
            "company_name": company_name,
            "results": all_results
        }
    
    async def search_company_news(self, company_name: str) -> Dict[str, Any]:
        """
        搜索企业相关新闻和舆情
        
        Args:
            company_name: 公司名称
        
        Returns:
            新闻搜索结果
        """
        queries = [
            f"{company_name} 最新新闻 动态",
            f"{company_name} 负面新闻 诉讼 纠纷"
        ]
        
        all_results = []
        for query in queries:
            result = await self.search(query, max_results=3)
            all_results.extend(result.get("results", []))
        
        return {
            "type": "news",
            "company_name": company_name,
            "results": all_results
        }
    
    async def search_company_reputation(self, company_name: str) -> Dict[str, Any]:
        """
        搜索企业口碑和评价
        
        Args:
            company_name: 公司名称
        
        Returns:
            口碑搜索结果
        """
        query = f"{company_name} 口碑 评价 信用评级"
        result = await self.search(query, max_results=5)
        
        return {
            "type": "reputation",
            "company_name": company_name,
            "results": result.get("results", [])
        }

