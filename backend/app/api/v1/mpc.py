"""
MPC 私密验证 API 路由
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from werkzeug.utils import secure_filename

from ...core.config import settings
from ...engines.mpc import MPCVerificationEngine, LEVELS
from ...models.schemas import (
    CreateSessionRequest,
    JoinSessionRequest,
    CommitRequest,
    RevealRequest,
)
from ...services.session_storage import SessionStorage

router = APIRouter()

# 初始化 MPC 引擎和持久化存储
mpc_engine = MPCVerificationEngine()
session_storage = SessionStorage(settings.DATA_FOLDER)

# 启动时加载历史会话
session_storage.load_all_sessions(mpc_engine)


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS


@router.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """创建新的验证会话"""
    result = mpc_engine.create_session(
        company_name=request.company_name,
        privacy_level=request.privacy_level
    )
    
    if result['success']:
        # 持久化保存
        session_data = mpc_engine.get_session(result['session_id'])
        session_storage.save_session(result['session_id'], session_data)
    
    return result


@router.post("/sessions/join")
async def join_session(request: JoinSessionRequest):
    """加入已存在的会话"""
    result = mpc_engine.join_session(request.session_id, request.company_name)
    
    if result['success']:
        # 持久化保存
        session_data = mpc_engine.get_session(request.session_id)
        session_storage.save_session(request.session_id, session_data)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    
    return result


@router.post("/sessions/upload")
async def upload_files(
    session_id: str = Form(...),
    role: str = Form(...),
    bank_statement: UploadFile = File(...),
    commitment_letter: UploadFile = File(...)
):
    """上传银行流水和承诺书文件"""
    session = mpc_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 验证文件
    if not bank_statement.filename or not commitment_letter.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    
    if not (allowed_file(bank_statement.filename) and allowed_file(commitment_letter.filename)):
        raise HTTPException(status_code=400, detail="只支持 PDF、PNG、JPG、JPEG 格式")
    
    # 获取公司名称
    company = session[role]
    company_name = company.get('name', '未命名公司')
    
    # 创建会话专属文件夹
    session_folder = os.path.join(settings.DATA_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    # 获取文件扩展名
    bank_ext = os.path.splitext(bank_statement.filename)[1]
    commitment_ext = os.path.splitext(commitment_letter.filename)[1]
    
    # 生成清晰的文件名
    bank_filename = secure_filename(f"{company_name}_银行流水{bank_ext}")
    commitment_filename = secure_filename(f"{company_name}_承诺书{commitment_ext}")
    
    # 保存文件
    bank_path = os.path.join(session_folder, bank_filename)
    commitment_path = os.path.join(session_folder, commitment_filename)
    
    # 写入文件
    with open(bank_path, 'wb') as f:
        content = await bank_statement.read()
        f.write(content)
    
    with open(commitment_path, 'wb') as f:
        content = await commitment_letter.read()
        f.write(content)
    
    # 更新引擎状态
    result = mpc_engine.set_files_uploaded(
        session_id, role, bank_filename, commitment_filename
    )
    
    # 持久化保存
    session_data = mpc_engine.get_session(session_id)
    session_storage.save_session(session_id, session_data)
    
    return result


@router.post("/sessions/commit")
async def commit(request: CommitRequest):
    """提交承诺"""
    result = mpc_engine.commit(request.session_id, request.role, request.amount)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    # 持久化保存
    session_data = mpc_engine.get_session(request.session_id)
    session_storage.save_session(request.session_id, session_data)
    
    return result


@router.post("/sessions/reveal")
async def reveal(request: RevealRequest):
    """揭示并比较结果"""
    result = mpc_engine.reveal(request.session_id, request.role)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    # 持久化保存
    session_data = mpc_engine.get_session(request.session_id)
    session_storage.save_session(request.session_id, session_data)
    
    return result


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """获取会话状态"""
    result = mpc_engine.get_session_status(session_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    
    return result


@router.get("/levels")
async def get_levels():
    """获取所有档次信息"""
    return {
        'success': True,
        'levels': LEVELS
    }


@router.get("/history")
async def get_history():
    """获取历史会话记录"""
    return mpc_engine.get_history()


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    """导出指定会话的完整数据"""
    session_data = mpc_engine.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    export_data = {
        'session_id': session_id,
        'created_at': session_data.get('created_at'),
        'status': session_data.get('status'),
        'company_a': {
            'name': session_data['company_a'].get('name'),
            'level': session_data['company_a'].get('level_info'),
            'files': {
                'bank_statement': session_data['company_a'].get('bank_statement'),
                'commitment_letter': session_data['company_a'].get('commitment_letter')
            }
        },
        'company_b': {
            'name': session_data['company_b'].get('name'),
            'level': session_data['company_b'].get('level_info'),
            'files': {
                'bank_statement': session_data['company_b'].get('bank_statement'),
                'commitment_letter': session_data['company_b'].get('commitment_letter')
            }
        },
        'result': session_data.get('result')
    }
    
    return {
        'success': True,
        'data': export_data
    }

