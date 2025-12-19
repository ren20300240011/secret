"""
密码学承诺方案模块

基于 SHA-256 的承诺方案，实现：
- 隐藏性：从承诺值无法推断出实际档次
- 绑定性：提交后无法修改档次等级
- 可验证性：揭示时可验证承诺的真实性
"""
import hashlib


def create_commitment(level: int, secret: str) -> str:
    """
    创建承诺值
    
    Args:
        level: 档次等级 (1-5)
        secret: 随机秘密值
    
    Returns:
        SHA-256 哈希值作为承诺
    """
    data = f"{level}:{secret}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def verify_commitment(commitment: str, level: int, secret: str) -> bool:
    """
    验证承诺
    
    Args:
        commitment: 原始承诺值
        level: 声称的档次等级
        secret: 声称的秘密值
    
    Returns:
        验证是否通过
    """
    return commitment == create_commitment(level, secret)

