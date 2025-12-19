"""
信用档次定义模块

定义企业流水的5个档次等级，用于私密比较
"""
from typing import Dict, Any, Optional

# 流水档次定义
LEVELS = [
    {
        "min": 100000,           # 10万
        "max": 1000000,          # 100万
        "level": 1,
        "name": "初创级",
        "description": "10万-100万"
    },
    {
        "min": 1000000,          # 100万
        "max": 10000000,         # 1000万
        "level": 2,
        "name": "成长级",
        "description": "100万-1000万"
    },
    {
        "min": 10000000,         # 1000万
        "max": 100000000,        # 1亿
        "level": 3,
        "name": "发展级",
        "description": "1000万-1亿"
    },
    {
        "min": 100000000,        # 1亿
        "max": 1000000000,       # 10亿
        "level": 4,
        "name": "成熟级",
        "description": "1亿-10亿"
    },
    {
        "min": 1000000000,       # 10亿
        "max": float('inf'),
        "level": 5,
        "name": "领军级",
        "description": "10亿以上"
    }
]


def get_level(amount: float) -> Dict[str, Any]:
    """
    根据金额确定档次
    
    Args:
        amount: 流水金额（元）
    
    Returns:
        档次信息字典
    """
    for level_info in LEVELS:
        if level_info["min"] <= amount < level_info["max"]:
            return level_info.copy()
    return LEVELS[0].copy()


def get_level_by_id(level_id: int) -> Optional[Dict[str, Any]]:
    """
    根据档次ID获取档次信息
    
    Args:
        level_id: 档次等级 (1-5)
    
    Returns:
        档次信息字典或 None
    """
    for level_info in LEVELS:
        if level_info["level"] == level_id:
            return level_info.copy()
    return None

