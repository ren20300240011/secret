from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# 文件上传配置
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'  # 存储会话数据
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# 存储会话数据（现在会持久化到文件）
sessions = {}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_session_to_file(session_id, session_data):
    """保存会话数据到JSON文件"""
    try:
        # 创建会话专属文件夹
        session_folder = os.path.join(DATA_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        # 保存会话信息
        session_file = os.path.join(session_folder, 'session.json')
        
        # 准备要保存的数据（排除不能序列化的字段）
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

def load_session_from_file(session_id):
    """从文件加载会话数据"""
    try:
        session_file = os.path.join(DATA_FOLDER, session_id, 'session.json')
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ 加载会话失败: {e}")
        return None

def load_all_sessions():
    """启动时加载所有保存的会话"""
    try:
        if not os.path.exists(DATA_FOLDER):
            return
        
        count = 0
        for session_id in os.listdir(DATA_FOLDER):
            session_folder = os.path.join(DATA_FOLDER, session_id)
            if os.path.isdir(session_folder):
                session_data = load_session_from_file(session_id)
                if session_data:
                    sessions[session_id] = session_data
                    count += 1
        
        print(f"✅ 已加载 {count} 个历史会话")
    except Exception as e:
        print(f"❌ 加载历史会话失败: {e}")

# 启动时加载历史会话
load_all_sessions()

# 流水档次定义
LEVELS = [
    {"min": 100000, "max": 1000000, "level": 1, "name": "初创级", "description": "10万-100万"},
    {"min": 1000000, "max": 10000000, "level": 2, "name": "成长级", "description": "100万-1000万"},
    {"min": 10000000, "max": 100000000, "level": 3, "name": "发展级", "description": "1000万-1亿"},
    {"min": 100000000, "max": 1000000000, "level": 4, "name": "成熟级", "description": "1亿-10亿"},
    {"min": 1000000000, "max": float('inf'), "level": 5, "name": "领军级", "description": "10亿以上"}
]

def get_level(amount):
    """根据金额确定档次"""
    for level_info in LEVELS:
        if level_info["min"] <= amount < level_info["max"]:
            return level_info
    return LEVELS[0]

def create_commitment(level, secret):
    """创建承诺：commitment = hash(level + secret)"""
    data = f"{level}:{secret}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def verify_commitment(commitment, level, secret):
    """验证承诺"""
    return commitment == create_commitment(level, secret)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create_session', methods=['POST'])
def create_session():
    """创建新的比较会话"""
    data = request.json
    company_name = data.get('company_name', '匿名公司')
    
    # 生成唯一会话ID
    session_id = secrets.token_hex(16)
    
    sessions[session_id] = {
        'session_id': session_id,
        'created_at': datetime.now().isoformat(),
        'company_a': {
            'name': company_name,
            'committed': False,
            'commitment': None,
            'level': None,
            'secret': None
        },
        'company_b': {
            'name': None,
            'committed': False,
            'commitment': None,
            'level': None,
            'secret': None
        },
        'status': 'waiting_for_b',  # waiting_for_b, both_committed, revealed
        'result': None
    }
    
    # 保存会话到文件
    save_session_to_file(session_id, sessions[session_id])
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'role': 'company_a'
    })

@app.route('/api/join_session', methods=['POST'])
def join_session():
    """加入已存在的会话"""
    data = request.json
    session_id = data.get('session_id')
    company_name = data.get('company_name', '匿名公司')
    
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'message': '会话不存在或已过期'
        }), 404
    
    session = sessions[session_id]
    
    if session['status'] != 'waiting_for_b':
        return jsonify({
            'success': False,
            'message': '此会话已经有两家公司参与'
        }), 400
    
    session['company_b']['name'] = company_name
    
    # 保存会话到文件
    save_session_to_file(session_id, session)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'role': 'company_b',
        'company_a_name': session['company_a']['name']
    })

@app.route('/api/upload_files', methods=['POST'])
def upload_files():
    """上传银行流水和承诺书文件"""
    session_id = request.form.get('session_id')
    role = request.form.get('role')
    
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'message': '会话不存在'
        }), 404
    
    # 检查文件
    if 'bank_statement' not in request.files or 'commitment_letter' not in request.files:
        return jsonify({
            'success': False,
            'message': '请同时上传银行流水和承诺书'
        }), 400
    
    bank_file = request.files['bank_statement']
    commitment_file = request.files['commitment_letter']
    
    # 验证文件
    if bank_file.filename == '' or commitment_file.filename == '':
        return jsonify({
            'success': False,
            'message': '请选择文件'
        }), 400
    
    if not (allowed_file(bank_file.filename) and allowed_file(commitment_file.filename)):
        return jsonify({
            'success': False,
            'message': '只支持 PDF、PNG、JPG、JPEG 格式'
        }), 400
    
    # 生成安全的文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    bank_filename = secure_filename(f"{session_id}_{role}_bank_{timestamp}_{bank_file.filename}")
    commitment_filename = secure_filename(f"{session_id}_{role}_commitment_{timestamp}_{commitment_file.filename}")
    
    # 保存文件
    bank_path = os.path.join(app.config['UPLOAD_FOLDER'], bank_filename)
    commitment_path = os.path.join(app.config['UPLOAD_FOLDER'], commitment_filename)
    
    bank_file.save(bank_path)
    commitment_file.save(commitment_path)
    
    # 保存文件信息到会话
    session = sessions[session_id]
    company = session[role]
    company['bank_statement'] = bank_filename
    company['commitment_letter'] = commitment_filename
    company['files_uploaded'] = True
    
    # 保存会话到文件
    save_session_to_file(session_id, session)
    
    return jsonify({
        'success': True,
        'message': '文件上传成功',
        'files': {
            'bank_statement': bank_filename,
            'commitment_letter': commitment_filename
        }
    })

@app.route('/api/commit', methods=['POST'])
def commit():
    """提交承诺"""
    data = request.json
    session_id = data.get('session_id')
    role = data.get('role')  # 'company_a' or 'company_b'
    amount = data.get('amount')
    
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'message': '会话不存在'
        }), 404
    
    session = sessions[session_id]
    company = session[role]
    
    # 检查是否已上传文件
    if not company.get('files_uploaded', False):
        return jsonify({
            'success': False,
            'message': '请先上传银行流水和承诺书'
        }), 400
    
    # 计算档次
    level_info = get_level(amount)
    level = level_info['level']
    
    # 生成秘密值
    secret = secrets.token_hex(32)
    
    # 创建承诺
    commitment = create_commitment(level, secret)
    
    # 存储信息
    company = session[role]
    company['committed'] = True
    company['commitment'] = commitment
    company['level'] = level
    company['secret'] = secret
    company['level_info'] = level_info
    
    # 检查双方是否都已提交
    if session['company_a']['committed'] and session['company_b']['committed']:
        session['status'] = 'both_committed'
    
    # 保存会话到文件
    save_session_to_file(session_id, session)
    
    return jsonify({
        'success': True,
        'commitment': commitment,
        'level_info': level_info,
        'status': session['status']
    })

@app.route('/api/reveal', methods=['POST'])
def reveal():
    """揭示并比较结果"""
    data = request.json
    session_id = data.get('session_id')
    role = data.get('role')
    
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'message': '会话不存在'
        }), 404
    
    session = sessions[session_id]
    
    # 允许 'both_committed' 或 'revealed' 状态访问结果
    if session['status'] not in ['both_committed', 'revealed']:
        return jsonify({
            'success': False,
            'message': '等待对方提交承诺'
        }), 400
    
    # 如果已经计算过结果，直接返回（避免重复计算）
    if session['status'] == 'revealed' and session.get('result'):
        return jsonify({
            'success': True,
            'result': session['result']
        })
    
    # 验证承诺
    company_a = session['company_a']
    company_b = session['company_b']
    
    verify_a = verify_commitment(company_a['commitment'], company_a['level'], company_a['secret'])
    verify_b = verify_commitment(company_b['commitment'], company_b['level'], company_b['secret'])
    
    if not (verify_a and verify_b):
        return jsonify({
            'success': False,
            'message': '承诺验证失败'
        }), 400
    
    # 比较档次
    level_a = company_a['level']
    level_b = company_b['level']
    
    if level_a > level_b:
        comparison_result = 'higher'
        message = f"{company_a['name']} 的流水档次更高"
    elif level_a < level_b:
        comparison_result = 'lower'
        message = f"{company_b['name']} 的流水档次更高"
    else:
        comparison_result = 'equal'
        message = "两家公司处于相同的流水档次"
    
    result = {
        'comparison': comparison_result,
        'message': message,
        'company_a': {
            'name': company_a['name'],
            'level_info': company_a['level_info']
        },
        'company_b': {
            'name': company_b['name'],
            'level_info': company_b['level_info']
        }
    }
    
    # 第一次计算时保存结果并更新状态
    session['status'] = 'revealed'
    session['result'] = result
    
    # 保存会话到文件
    save_session_to_file(session_id, session)
    
    return jsonify({
        'success': True,
        'result': result
    })

@app.route('/api/session_status', methods=['GET'])
def session_status():
    """获取会话状态"""
    session_id = request.args.get('session_id')
    
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'message': '会话不存在'
        }), 404
    
    session = sessions[session_id]
    
    return jsonify({
        'success': True,
        'status': session['status'],
        'company_a_committed': session['company_a']['committed'],
        'company_b_committed': session['company_b']['committed'],
        'company_b_joined': session['company_b']['name'] is not None
    })

@app.route('/api/levels', methods=['GET'])
def get_levels():
    """获取所有档次信息"""
    return jsonify({
        'success': True,
        'levels': LEVELS
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取所有历史会话记录"""
    try:
        history = []
        for session_id, session_data in sessions.items():
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
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/export/<session_id>', methods=['GET'])
def export_session(session_id):
    """导出指定会话的完整数据"""
    if session_id not in sessions:
        return jsonify({
            'success': False,
            'message': '会话不存在'
        }), 404
    
    try:
        session_data = sessions[session_id]
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
        
        return jsonify({
            'success': True,
            'data': export_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

