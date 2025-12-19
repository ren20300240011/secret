"""
企业风险分析器

使用 DeepSeek 模型分析企业公开信息，生成风险画像
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .llm_client import DeepSeekClient

logger = logging.getLogger(__name__)


# 风险分析系统提示词
RISK_ANALYSIS_SYSTEM_PROMPT = """你是一位专业的企业风险分析师。你的任务是根据提供的公开信息，分析目标企业的风险状况。

分析维度包括：
1. 企业基础信息（注册时间、经营范围、规模等）
2. 舆情风险（负面新闻、法律纠纷、投诉等）
3. 经营风险（业务稳定性、行业地位等）
4. 信用风险（历史信用记录、合作口碑等）

评分标准说明（0-100分，分数越高表示企业越可靠、风险越低）：
- 90-100分：行业龙头、世界500强、国家级重点企业，信誉卓越
- 80-89分：大型知名企业、上市公司、行业领先者
- 70-79分：中大型企业、区域龙头、良好经营记录
- 60-69分：中型企业、经营稳定、无重大负面
- 50-59分：中小型企业、经营一般、存在小风险
- 40-49分：小型企业、信息不足或存在一定风险
- 40分以下：高风险企业、存在重大负面信息

请基于事实进行客观分析，对于没有明确信息的方面，标注为"信息不足"而不是臆测。
对于华为、腾讯、阿里巴巴等世界级巨头企业，应给予90分以上的高评分。
输出格式要求清晰、结构化，便于决策者快速理解。
"""

# 风险评分提示词模板
RISK_SCORING_PROMPT = """基于以下企业公开信息，请对 {company_name} 进行风险评估：

## 收集到的信息
{collected_info}

请按以下格式输出分析结果：

## 企业概况
简要描述企业的基本情况（2-3句话）

## 各维度评估

**重要：所有评分都是"安全可靠性分数"，分数越高表示该维度越安全可靠！**

### 1. 基础信息可靠性 (0-100分)
- 评分：XX分（信息越完整透明、企业历史越悠久稳定，分数越高）
- 分析：...

### 2. 舆情健康度 (0-100分)
- 评分：XX分（正面信息越多、负面信息越少，分数越高）
- 分析：...

### 3. 经营稳定性 (0-100分)
- 评分：XX分（经营越稳定、业务能力越强，分数越高）
- 分析：...

### 4. 信用可靠性 (0-100分)
- 评分：XX分（信用记录越好、无违约历史，分数越高）
- 分析：...

## 综合评分
- 总分：XX分（四项评分的加权平均，0-100分，分数越高表示企业越可靠）
- 风险等级：极低风险(90+)/低风险(80-89)/较低风险(70-79)/中等风险(60-69)/较高风险(50-59)/高风险(<50)

## 主要关注点
1. ...
2. ...

## 合作建议
基于以上分析，给出是否建议合作的结论和注意事项。
"""


class RiskAnalyzer:
    """企业风险分析器"""
    
    def __init__(self, llm_client: Optional[DeepSeekClient] = None):
        self.llm_client = llm_client or DeepSeekClient()
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        格式化搜索结果为文本
        
        Args:
            search_results: 搜索结果列表
        
        Returns:
            格式化的文本
        """
        formatted = []
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")
            
            formatted.append(f"### 来源 {i}: {title}")
            formatted.append(f"链接: {url}")
            formatted.append(f"内容摘要: {content}")
            formatted.append("")
        
        return "\n".join(formatted) if formatted else "未找到相关信息"
    
    async def analyze_company(
        self, 
        company_name: str,
        company_info: Dict[str, Any],
        news_info: Dict[str, Any],
        reputation_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析企业风险
        
        Args:
            company_name: 公司名称
            company_info: 企业基础信息搜索结果
            news_info: 新闻搜索结果
            reputation_info: 口碑搜索结果（可选）
        
        Returns:
            风险分析结果
        """
        # 整合所有搜索结果
        collected_info = []
        
        collected_info.append("### 企业基础信息")
        collected_info.append(self._format_search_results(company_info.get("results", [])))
        
        collected_info.append("\n### 相关新闻动态")
        collected_info.append(self._format_search_results(news_info.get("results", [])))
        
        if reputation_info:
            collected_info.append("\n### 企业口碑评价")
            collected_info.append(self._format_search_results(reputation_info.get("results", [])))
        
        collected_info_text = "\n".join(collected_info)
        
        # 构建分析提示词
        prompt = RISK_SCORING_PROMPT.format(
            company_name=company_name,
            collected_info=collected_info_text
        )
        
        # 调用 LLM 进行分析
        analysis_result = await self.llm_client.analyze(
            prompt=prompt,
            system_prompt=RISK_ANALYSIS_SYSTEM_PROMPT
        )
        
        # 解析评分（简单提取）
        score = self._extract_score(analysis_result)
        risk_level = self._get_risk_level(score)
        
        return {
            "company_name": company_name,
            "analysis": analysis_result,
            "score": score,
            "risk_level": risk_level,
            "analyzed_at": datetime.now().isoformat(),
            "sources_count": (
                len(company_info.get("results", [])) +
                len(news_info.get("results", [])) +
                len(reputation_info.get("results", []) if reputation_info else [])
            )
        }
    
    def _extract_score(self, analysis_text: str) -> int:
        """
        从分析文本中提取综合评分
        
        Args:
            analysis_text: 分析结果文本
        
        Returns:
            评分 (0-100)
        """
        import re
        
        # 尝试匹配 "总分：XX分" 或 "综合评分：XX" 模式（支持小数）
        patterns = [
            r"总分[：:]\s*(\d+\.?\d*)\s*分",
            r"综合评分[：:]\s*(\d+\.?\d*)",
            r"综合得分[：:]\s*(\d+\.?\d*)",
            r"总分[：:]\s*\*{0,2}(\d+\.?\d*)",  # 匹配 **98.5** 格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis_text)
            if match:
                score = float(match.group(1))
                return min(100, max(0, round(score)))
        
        # 如果没找到，返回默认值
        return 50
    
    def _get_risk_level(self, score: int) -> str:
        """
        根据评分确定风险等级
        
        Args:
            score: 评分 (0-100，越高风险越低)
        
        Returns:
            风险等级
        """
        if score >= 90:
            return "极低风险 ⭐"
        elif score >= 80:
            return "低风险"
        elif score >= 70:
            return "较低风险"
        elif score >= 60:
            return "中等风险"
        elif score >= 50:
            return "较高风险"
        else:
            return "高风险"

