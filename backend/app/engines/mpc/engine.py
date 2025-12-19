"""
MPC 私密验证引擎

基于安全多方计算的企业能力验证引擎
"""
import secrets
from typing import Dict, Any, Optional
from datetime import datetime

from .commitments import create_commitment, verify_commitment
from .levels import get_level


class MPCVerificationEngine:
    """MPC 私密验证引擎"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, company_name: str, privacy_level: str = 'detailed') -> Dict[str, Any]:
        """
        创建新的验证会话
        
        Args:
            company_name: 发起方公司名称
            privacy_level: 隐私级别
                - 'minimal': 仅显示比较结果（谁更高/相同），不透露具体档次
                - 'detailed': 显示双方具体档次等级
        
        Returns:
            会话信息
        """
        session_id = secrets.token_hex(16)
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'privacy_level': privacy_level,  # 隐私级别
            'company_a': {
                'name': company_name,
                'committed': False,
                'commitment': None,
                'level': None,
                'secret': None,
                'level_info': None,
                'files_uploaded': False,
                'bank_statement': None,
                'commitment_letter': None
            },
            'company_b': {
                'name': None,
                'committed': False,
                'commitment': None,
                'level': None,
                'secret': None,
                'level_info': None,
                'files_uploaded': False,
                'bank_statement': None,
                'commitment_letter': None
            },
            'status': 'waiting_for_b',
            'result': None
        }
        
        return {
            'success': True,
            'session_id': session_id,
            'role': 'company_a',
            'privacy_level': privacy_level
        }
    
    def join_session(self, session_id: str, company_name: str) -> Dict[str, Any]:
        """
        加入已存在的会话
        
        Args:
            session_id: 会话ID
            company_name: 加入方公司名称
        
        Returns:
            加入结果
        """
        if session_id not in self.sessions:
            return {
                'success': False,
                'message': '会话不存在或已过期'
            }
        
        session = self.sessions[session_id]
        
        if session['status'] != 'waiting_for_b':
            return {
                'success': False,
                'message': '此会话已经有两家公司参与'
            }
        
        session['company_b']['name'] = company_name
        
        return {
            'success': True,
            'session_id': session_id,
            'role': 'company_b',
            'company_a_name': session['company_a']['name'],
            'privacy_level': session.get('privacy_level', 'detailed')
        }
    
    def set_files_uploaded(self, session_id: str, role: str, 
                          bank_statement: str, commitment_letter: str) -> Dict[str, Any]:
        """
        标记文件已上传
        
        Args:
            session_id: 会话ID
            role: 角色 ('company_a' 或 'company_b')
            bank_statement: 银行流水文件名
            commitment_letter: 承诺书文件名
        
        Returns:
            操作结果
        """
        if session_id not in self.sessions:
            return {'success': False, 'message': '会话不存在'}
        
        session = self.sessions[session_id]
        company = session[role]
        company['files_uploaded'] = True
        company['bank_statement'] = bank_statement
        company['commitment_letter'] = commitment_letter
        
        return {
            'success': True,
            'message': '文件上传成功',
            'files': {
                'bank_statement': bank_statement,
                'commitment_letter': commitment_letter
            }
        }
    
    def commit(self, session_id: str, role: str, amount: float) -> Dict[str, Any]:
        """
        提交承诺
        
        Args:
            session_id: 会话ID
            role: 角色 ('company_a' 或 'company_b')
            amount: 流水金额
        
        Returns:
            提交结果
        """
        if session_id not in self.sessions:
            return {'success': False, 'message': '会话不存在'}
        
        session = self.sessions[session_id]
        company = session[role]
        
        # 检查是否已上传文件
        if not company.get('files_uploaded', False):
            return {
                'success': False,
                'message': '请先上传银行流水和承诺书'
            }
        
        # 计算档次
        level_info = get_level(amount)
        level = level_info['level']
        
        # 生成秘密值
        secret = secrets.token_hex(32)
        
        # 创建承诺
        commitment = create_commitment(level, secret)
        
        # 存储信息
        company['committed'] = True
        company['commitment'] = commitment
        company['level'] = level
        company['secret'] = secret
        company['level_info'] = level_info
        
        # 检查双方是否都已提交
        if session['company_a']['committed'] and session['company_b']['committed']:
            session['status'] = 'both_committed'
        
        return {
            'success': True,
            'commitment': commitment,
            'level_info': level_info,
            'status': session['status']
        }
    
    def reveal(self, session_id: str, role: str) -> Dict[str, Any]:
        """
        揭示并比较结果
        
        Args:
            session_id: 会话ID
            role: 角色
        
        Returns:
            比较结果
        """
        if session_id not in self.sessions:
            return {'success': False, 'message': '会话不存在'}
        
        session = self.sessions[session_id]
        
        # 允许 'both_committed' 或 'revealed' 状态访问结果
        if session['status'] not in ['both_committed', 'revealed']:
            return {
                'success': False,
                'message': '等待对方提交承诺'
            }
        
        # 如果已经计算过结果，直接返回
        if session['status'] == 'revealed' and session.get('result'):
            return {
                'success': True,
                'result': session['result']
            }
        
        # 验证承诺
        company_a = session['company_a']
        company_b = session['company_b']
        
        verify_a = verify_commitment(
            company_a['commitment'], 
            company_a['level'], 
            company_a['secret']
        )
        verify_b = verify_commitment(
            company_b['commitment'], 
            company_b['level'], 
            company_b['secret']
        )
        
        if not (verify_a and verify_b):
            return {'success': False, 'message': '承诺验证失败'}
        
        # 比较档次
        level_a = company_a['level']
        level_b = company_b['level']
        privacy_level = session.get('privacy_level', 'detailed')
        
        if level_a > level_b:
            comparison_result = 'a_higher'
            message = f"{company_a['name']} 的流水档次更高"
        elif level_a < level_b:
            comparison_result = 'b_higher'
            message = f"{company_b['name']} 的流水档次更高"
        else:
            comparison_result = 'equal'
            message = "两家公司处于相同的流水档次"
        
        # 根据隐私级别构建结果
        if privacy_level == 'minimal':
            # 最小披露模式：只显示比较结果，不透露具体档次
            result = {
                'comparison': comparison_result,
                'message': message,
                'privacy_level': 'minimal',
                'company_a': {
                    'name': company_a['name'],
                    'level_info': None  # 不透露具体档次
                },
                'company_b': {
                    'name': company_b['name'],
                    'level_info': None  # 不透露具体档次
                }
            }
        else:
            # 详细模式：显示双方档次
            result = {
                'comparison': comparison_result,
                'message': message,
                'privacy_level': 'detailed',
                'company_a': {
                    'name': company_a['name'],
                    'level_info': company_a['level_info']
                },
                'company_b': {
                    'name': company_b['name'],
                    'level_info': company_b['level_info']
                }
            }
        
        # 保存结果并更新状态
        session['status'] = 'revealed'
        session['result'] = result
        
        return {
            'success': True,
            'result': result
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话状态
        """
        if session_id not in self.sessions:
            return {'success': False, 'message': '会话不存在'}
        
        session = self.sessions[session_id]
        
        return {
            'success': True,
            'status': session['status'],
            'company_a_committed': session['company_a']['committed'],
            'company_b_committed': session['company_b']['committed'],
            'company_b_joined': session['company_b']['name'] is not None
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取完整会话数据
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话数据或 None
        """
        return self.sessions.get(session_id)
    
    def set_session(self, session_id: str, session_data: Dict[str, Any]):
        """
        设置会话数据（用于从持久化恢复）
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
        """
        self.sessions[session_id] = session_data
    
    def get_history(self) -> Dict[str, Any]:
        """
        获取所有已完成的历史会话
        
        Returns:
            历史会话列表
        """
        history = []
        for session_id, session_data in self.sessions.items():
            if session_data.get('status') == 'revealed' and session_data.get('result'):
                history.append({
                    'session_id': session_id,
                    'created_at': session_data.get('created_at'),
                    'company_a_name': session_data['company_a'].get('name'),
                    'company_b_name': session_data['company_b'].get('name'),
                    'result': session_data.get('result')
                })
        
        # 按创建时间倒序排列
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            'success': True,
            'count': len(history),
            'history': history
        }

