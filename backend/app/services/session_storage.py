"""
会话持久化存储服务
"""
import os
import json
from typing import Dict, Any, Optional


class SessionStorage:
    """会话数据持久化存储"""
    
    def __init__(self, data_folder: str):
        self.data_folder = data_folder
        os.makedirs(data_folder, exist_ok=True)
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        保存会话数据到JSON文件
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
        
        Returns:
            是否保存成功
        """
        try:
            # 创建会话专属文件夹
            session_folder = os.path.join(self.data_folder, session_id)
            os.makedirs(session_folder, exist_ok=True)
            
            # 保存会话信息
            session_file = os.path.join(session_folder, 'session.json')
            
            # 准备要保存的数据（排除不能序列化的字段如 secret）
            save_data = {
                'session_id': session_data.get('session_id'),
                'created_at': session_data.get('created_at'),
                'status': session_data.get('status'),
                'company_a': {
                    'name': session_data['company_a'].get('name'),
                    'committed': session_data['company_a'].get('committed', False),
                    'level': session_data['company_a'].get('level'),
                    'bank_statement': session_data['company_a'].get('bank_statement'),
                    'commitment_letter': session_data['company_a'].get('commitment_letter'),
                    'files_uploaded': session_data['company_a'].get('files_uploaded', False),
                    'level_info': session_data['company_a'].get('level_info')
                },
                'company_b': {
                    'name': session_data['company_b'].get('name'),
                    'committed': session_data['company_b'].get('committed', False),
                    'level': session_data['company_b'].get('level'),
                    'bank_statement': session_data['company_b'].get('bank_statement'),
                    'commitment_letter': session_data['company_b'].get('commitment_letter'),
                    'files_uploaded': session_data['company_b'].get('files_uploaded', False),
                    'level_info': session_data['company_b'].get('level_info')
                },
                'result': session_data.get('result')
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 会话已保存: {session_id}")
            return True
        except Exception as e:
            print(f"❌ 保存会话失败: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载会话数据
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话数据或 None
        """
        try:
            session_file = os.path.join(self.data_folder, session_id, 'session.json')
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"❌ 加载会话失败: {e}")
            return None
    
    def load_all_sessions(self, engine) -> int:
        """
        启动时加载所有保存的会话到引擎
        
        Args:
            engine: MPC引擎实例
        
        Returns:
            加载的会话数量
        """
        try:
            if not os.path.exists(self.data_folder):
                return 0
            
            count = 0
            for session_id in os.listdir(self.data_folder):
                session_folder = os.path.join(self.data_folder, session_id)
                if os.path.isdir(session_folder):
                    session_data = self.load_session(session_id)
                    if session_data:
                        engine.set_session(session_id, session_data)
                        count += 1
            
            print(f"✅ 已加载 {count} 个历史会话")
            return count
        except Exception as e:
            print(f"❌ 加载历史会话失败: {e}")
            return 0
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话数据
        
        Args:
            session_id: 会话ID
        
        Returns:
            是否删除成功
        """
        try:
            import shutil
            session_folder = os.path.join(self.data_folder, session_id)
            if os.path.exists(session_folder):
                shutil.rmtree(session_folder)
                return True
            return False
        except Exception as e:
            print(f"❌ 删除会话失败: {e}")
            return False

