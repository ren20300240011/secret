"""
DeepSeek LLM 客户端

用于企业风险分析的大语言模型调用
"""
import os
import logging
import httpx
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY 未设置，LLM 分析功能将不可用")
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "deepseek-chat",
        temperature: float = 0.0,  # 设为0保证结果可复现
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek Chat API
        
        Args:
            messages: 消息列表
            model: 模型名称 (deepseek-chat 或 deepseek-reasoner)
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            API 响应
        """
        if not self.api_key:
            return {"error": "DEEPSEEK_API_KEY 未设置", "content": ""}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "content": content,
                    "model": model,
                    "usage": data.get("usage", {})
                }
        except httpx.TimeoutException:
            logger.error("DeepSeek API 请求超时")
            return {"error": "请求超时", "content": ""}
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API HTTP 错误: {e}")
            return {"error": str(e), "content": ""}
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return {"error": str(e), "content": ""}
    
    async def analyze(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        执行分析任务
        
        Args:
            prompt: 分析提示词
            system_prompt: 系统提示词
        
        Returns:
            分析结果文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        result = await self.chat(messages)
        return result.get("content", "")

