"""
EDR 结果缓存模块

缓存企业分析结果，避免重复分析
"""
import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "edr_cache"

# 默认缓存有效期（小时）
DEFAULT_CACHE_HOURS = 24


class EDRCache:
    """EDR 分析结果缓存"""
    
    def __init__(self, cache_dir: Optional[Path] = None, cache_hours: int = DEFAULT_CACHE_HOURS):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_hours = cache_hours
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, company_name: str) -> str:
        """
        生成缓存键
        
        Args:
            company_name: 公司名称
        
        Returns:
            缓存键（哈希值）
        """
        # 使用公司名称的哈希作为文件名
        normalized_name = company_name.strip().lower()
        return hashlib.md5(normalized_name.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, company_name: str) -> Path:
        """获取缓存文件路径"""
        cache_key = self._get_cache_key(company_name)
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的分析结果
        
        Args:
            company_name: 公司名称
        
        Returns:
            缓存的结果，如果不存在或已过期则返回 None
        """
        cache_path = self._get_cache_path(company_name)
        
        if not cache_path.exists():
            logger.debug(f"缓存未命中: {company_name}")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # 检查是否过期
            cached_time = datetime.fromisoformat(cached_data.get('cached_at', ''))
            expiry_time = cached_time + timedelta(hours=self.cache_hours)
            
            if datetime.now() > expiry_time:
                logger.info(f"缓存已过期: {company_name}")
                cache_path.unlink()  # 删除过期缓存
                return None
            
            logger.info(f"缓存命中: {company_name} (缓存于 {cached_time})")
            
            # 标记为来自缓存
            result = cached_data.get('result', {})
            result['from_cache'] = True
            result['cached_at'] = cached_data.get('cached_at')
            
            return result
            
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return None
    
    def set(self, company_name: str, result: Dict[str, Any]) -> bool:
        """
        缓存分析结果
        
        Args:
            company_name: 公司名称
            result: 分析结果
        
        Returns:
            是否成功
        """
        cache_path = self._get_cache_path(company_name)
        
        try:
            cache_data = {
                'company_name': company_name,
                'cached_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=self.cache_hours)).isoformat(),
                'result': result
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已缓存分析结果: {company_name}")
            return True
            
        except Exception as e:
            logger.error(f"缓存写入失败: {e}")
            return False
    
    def clear(self, company_name: Optional[str] = None) -> int:
        """
        清除缓存
        
        Args:
            company_name: 公司名称，如果为 None 则清除所有缓存
        
        Returns:
            清除的缓存数量
        """
        if company_name:
            cache_path = self._get_cache_path(company_name)
            if cache_path.exists():
                cache_path.unlink()
                return 1
            return 0
        
        # 清除所有缓存
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        
        logger.info(f"已清除 {count} 个缓存文件")
        return count
    
    def list_cached(self) -> list:
        """列出所有缓存的公司"""
        cached = []
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cached.append({
                        'company_name': data.get('company_name'),
                        'cached_at': data.get('cached_at'),
                        'expires_at': data.get('expires_at')
                    })
            except:
                pass
        return cached

