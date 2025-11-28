// 全局状态
let currentState = {
    sessionId: null,
    role: null,  // 'company_a' or 'company_b'
    companyName: null,
    committed: false,
    pollInterval: null,
    resultRevealed: false,  // 新增：防止重复显示结果
    filesUploaded: false,  // 文件是否已上传
    bankFile: null,  // 银行流水文件
    commitmentFile: null  // 承诺书文件
};

// 保存状态到 localStorage
function saveState() {
    const stateToSave = {
        sessionId: currentState.sessionId,
        role: currentState.role,
        companyName: currentState.companyName,
        committed: currentState.committed,
        resultRevealed: currentState.resultRevealed,
        timestamp: Date.now()
    };
    localStorage.setItem('secureComparisonState', JSON.stringify(stateToSave));
    console.log('💾 状态已保存');
}

// 从 localStorage 恢复状态
function loadState() {
    const saved = localStorage.getItem('secureComparisonState');
    if (saved) {
        try {
            const state = JSON.parse(saved);
            // 只恢复1小时内的会话
            if (Date.now() - state.timestamp < 3600000) {
                currentState.sessionId = state.sessionId;
                currentState.role = state.role;
                currentState.companyName = state.companyName;
                currentState.committed = state.committed;
                currentState.resultRevealed = state.resultRevealed;
                console.log('📥 已恢复会话状态:', state);
                return true;
            } else {
                console.log('⏰ 会话已过期（超过1小时）');
                localStorage.removeItem('secureComparisonState');
            }
        } catch (e) {
            console.error('恢复状态失败:', e);
        }
    }
    return false;
}

// 清除保存的状态
function clearState() {
    localStorage.removeItem('secureComparisonState');
    console.log('🗑️ 状态已清除');
}

// API基础URL
const API_BASE = '';

// 显示通知
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 切换场景
function showScene(sceneId) {
    // 隐藏所有场景
    document.querySelectorAll('.scene').forEach(scene => {
        scene.classList.remove('active');
    });
    
    // 显示指定场景
    document.getElementById(sceneId).classList.add('active');
    
    // 更新步骤指示器
    updateSteps(sceneId);
}

// 更新步骤指示器
function updateSteps(sceneId) {
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => step.classList.remove('active'));
    
    if (sceneId === 'scene-role' || sceneId === 'scene-create' || sceneId === 'scene-join') {
        document.getElementById('step1').classList.add('active');
    } else if (sceneId === 'scene-waiting' || sceneId === 'scene-input') {
        document.getElementById('step2').classList.add('active');
    } else if (sceneId === 'scene-result') {
        document.getElementById('step3').classList.add('active');
    }
}

// 选择角色
function selectRole(role) {
    if (role === 'create') {
        showScene('scene-create');
    } else if (role === 'join') {
        showScene('scene-join');
    }
}

// 返回角色选择
function backToRole() {
    showScene('scene-role');
}

// 创建会话
async function createSession() {
    const companyName = document.getElementById('company-name-create').value.trim();
    
    if (!companyName) {
        showToast('请输入公司名称', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/create_session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ company_name: companyName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.sessionId = data.session_id;
            currentState.role = data.role;
            currentState.companyName = companyName;
            currentState.committed = false;  // 重置提交状态
            currentState.resultRevealed = false;  // 重置结果显示状态
            currentState.filesUploaded = false;  // 重置文件上传状态
            currentState.bankFile = null;
            currentState.commitmentFile = null;
            saveState();  // 保存状态
            
            // 显示会话ID
            document.getElementById('session-id-display').textContent = data.session_id;
            showScene('scene-waiting');
            
            // 开始轮询等待对方加入
            startPolling();
            
            showToast('会话创建成功！', 'success');
        } else {
            showToast(data.message || '创建会话失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('网络错误，请重试', 'error');
    }
}

// 加入会话
async function joinSession() {
    const sessionId = document.getElementById('session-id-join').value.trim();
    const companyName = document.getElementById('company-name-join').value.trim();
    
    if (!sessionId || !companyName) {
        showToast('请填写所有信息', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/join_session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                session_id: sessionId,
                company_name: companyName 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.sessionId = data.session_id;
            currentState.role = data.role;
            currentState.companyName = companyName;
            currentState.committed = false;  // 重置提交状态
            currentState.resultRevealed = false;  // 重置结果显示状态
            currentState.filesUploaded = false;  // 重置文件上传状态
            currentState.bankFile = null;
            currentState.commitmentFile = null;
            saveState();  // 保存状态
            
            // 直接进入输入界面
            setupInputScene();
            showScene('scene-input');
            
            // 开始轮询检查对方状态
            startPolling();
            
            showToast('成功加入会话！', 'success');
        } else {
            showToast(data.message || '加入会话失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('网络错误，请重试', 'error');
    }
}

// 复制会话ID
function copySessionId() {
    const sessionId = document.getElementById('session-id-display').textContent;
    navigator.clipboard.writeText(sessionId).then(() => {
        showToast('会话ID已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败，请手动复制', 'error');
    });
}

// 开始轮询
function startPolling() {
    if (currentState.pollInterval) {
        clearInterval(currentState.pollInterval);
    }
    
    currentState.pollInterval = setInterval(checkSessionStatus, 2000);
}

// 停止轮询
function stopPolling() {
    if (currentState.pollInterval) {
        clearInterval(currentState.pollInterval);
        currentState.pollInterval = null;
    }
}

// 检查会话状态
async function checkSessionStatus() {
    if (!currentState.sessionId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/session_status?session_id=${currentState.sessionId}`);
        
        // 如果会话不存在（404），清除状态并提示用户
        if (response.status === 404) {
            console.log('⚠️ 会话已失效（服务器重启或会话过期）');
            stopPolling();
            clearState();
            showToast('会话已失效，请重新开始', 'error');
            
            // 3秒后自动返回首页
            setTimeout(() => {
                startOver();
            }, 3000);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 如果在等待界面，检查对方是否加入
            if (document.getElementById('scene-waiting').classList.contains('active')) {
                if (data.company_b_joined) {
                    stopPolling();
                    setupInputScene();
                    showScene('scene-input');
                    startPolling();
                }
            }
            
            // 如果在输入界面，更新状态
            if (document.getElementById('scene-input').classList.contains('active')) {
                updateCommitmentStatus(data);
                
                // 如果双方都已提交且当前用户也已提交，自动查看结果
                if (data.company_a_committed && data.company_b_committed && 
                    currentState.committed && !currentState.resultRevealed) {
                    console.log('🔍 轮询检测到双方都已提交，准备自动显示结果...');
                    currentState.resultRevealed = true;  // 标记为已显示
                    stopPolling();
                    
                    const submitBtn = document.getElementById('submit-btn');
                    submitBtn.textContent = '✓ 正在加载结果...';
                    submitBtn.disabled = true;
                    
                    setTimeout(() => {
                        revealResult();
                    }, 300);
                }
            }
        }
    } catch (error) {
        console.error('Polling error:', error);
    }
}

// 设置输入场景
function setupInputScene() {
    document.getElementById('current-session-id').textContent = currentState.sessionId;
    
    // 根据角色设置参与公司信息
    if (currentState.role === 'company_a') {
        document.getElementById('participants').textContent = `${currentState.companyName} (您) vs 等待对方...`;
    } else {
        document.getElementById('participants').textContent = `对方公司 vs ${currentState.companyName} (您)`;
    }
}

// 更新承诺状态
function updateCommitmentStatus(data) {
    const myStatus = document.getElementById('my-status');
    const otherStatus = document.getElementById('other-status');
    
    const isCompanyA = currentState.role === 'company_a';
    const myCommitted = isCompanyA ? data.company_a_committed : data.company_b_committed;
    const otherCommitted = isCompanyA ? data.company_b_committed : data.company_a_committed;
    
    if (myCommitted) {
        myStatus.textContent = '已提交';
        myStatus.className = 'status-badge committed';
    } else {
        myStatus.textContent = '未提交';
        myStatus.className = 'status-badge pending';
    }
    
    if (otherCommitted) {
        otherStatus.textContent = '已提交';
        otherStatus.className = 'status-badge committed';
    } else {
        otherStatus.textContent = '未提交';
        otherStatus.className = 'status-badge pending';
    }
}

// 处理文件选择
function handleFileSelect(type) {
    const fileInput = document.getElementById(`${type}-file`);
    const fileName = document.getElementById(`${type}-file-name`);
    const uploadArea = document.getElementById(`${type}-upload-area`);
    
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        
        // 检查文件大小
        if (file.size > 10 * 1024 * 1024) {
            showToast('文件大小不能超过10MB', 'error');
            fileInput.value = '';
            return;
        }
        
        // 检查文件类型
        const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            showToast('只支持 PDF、PNG、JPG 格式', 'error');
            fileInput.value = '';
            return;
        }
        
        // 更新UI
        fileName.textContent = file.name;
        fileName.classList.add('selected');
        uploadArea.classList.add('has-file');
        
        // 保存文件到状态
        if (type === 'bank') {
            currentState.bankFile = file;
        } else {
            currentState.commitmentFile = file;
        }
        
        console.log(`✅ ${type === 'bank' ? '银行流水' : '承诺书'}文件已选择:`, file.name);
    }
}

// 上传文件
async function uploadFiles() {
    if (!currentState.bankFile || !currentState.commitmentFile) {
        showToast('请选择银行流水和承诺书文件', 'error');
        return false;
    }
    
    const formData = new FormData();
    formData.append('session_id', currentState.sessionId);
    formData.append('role', currentState.role);
    formData.append('bank_statement', currentState.bankFile);
    formData.append('commitment_letter', currentState.commitmentFile);
    
    // 显示上传进度
    document.getElementById('upload-status').style.display = 'block';
    document.getElementById('upload-message').textContent = '正在上传文件...';
    
    try {
        const response = await fetch(`${API_BASE}/api/upload_files`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.filesUploaded = true;
            document.getElementById('progress-bar').style.width = '100%';
            document.getElementById('upload-message').textContent = '✅ 文件上传成功';
            showToast('文件上传成功！', 'success');
            return true;
        } else {
            document.getElementById('upload-message').textContent = `❌ ${data.message}`;
            showToast(data.message || '文件上传失败', 'error');
            return false;
        }
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('upload-message').textContent = '❌ 上传失败';
        showToast('网络错误，请重试', 'error');
        return false;
    }
}

// 提交金额
async function submitAmount() {
    // 如果按钮显示"查看比较结果"，直接显示结果
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn.textContent.includes('查看比较结果')) {
        currentState.resultRevealed = true;
        stopPolling();
        revealResult();
        return;
    }
    
    // 如果已经提交过，不要重复提交
    if (currentState.committed) {
        showToast('您已经提交过了，请等待对方提交', 'error');
        return;
    }
    
    // 检查文件
    if (!currentState.bankFile || !currentState.commitmentFile) {
        showToast('请先上传银行流水和承诺书', 'error');
        return;
    }
    
    const amount = parseFloat(document.getElementById('amount-input').value);
    
    if (!amount || amount <= 0) {
        showToast('请输入有效的流水金额', 'error');
        return;
    }
    
    if (amount < 100000) {
        showToast('流水金额不能低于10万元', 'error');
        return;
    }
    
    // 先上传文件
    if (!currentState.filesUploaded) {
        const uploaded = await uploadFiles();
        if (!uploaded) {
            return;
        }
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/commit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentState.sessionId,
                role: currentState.role,
                amount: amount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.committed = true;
            saveState();  // 保存状态
            
            // 更新状态显示
            document.getElementById('my-status').textContent = '已提交';
            document.getElementById('my-status').className = 'status-badge committed';
            
            // 禁用输入
            document.getElementById('amount-input').disabled = true;
            
            showToast(`承诺已提交！您的档次: ${data.level_info.name}`, 'success');
            
            // 【关键】先检查是否双方都已提交
            if (data.status === 'both_committed') {
                console.log('✅ 提交时检测到双方都已提交，立即显示结果');
                currentState.resultRevealed = true;
                stopPolling();  // 停止轮询
                
                // 更新按钮状态
                document.getElementById('submit-btn').textContent = '✓ 正在加载结果...';
                document.getElementById('submit-btn').disabled = true;
                
                // 立即显示结果
                setTimeout(() => {
                    revealResult();
                }, 500);
            } else {
                console.log('⏳ 提交成功，等待对方提交...');
                
                // 设置等待状态
                document.getElementById('submit-btn').disabled = true;
                document.getElementById('submit-btn').textContent = '✓ 已提交，等待对方...';
                
                // 确保轮询正在运行
                if (!currentState.pollInterval) {
                    console.log('🔄 轮询未启动，重新启动轮询...');
                    startPolling();
                }
            }
        } else {
            showToast(data.message || '提交失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('网络错误，请重试', 'error');
    }
}

// 揭示并查看结果
async function revealResult() {
    console.log('📊 开始获取比较结果...');
    console.log('会话ID:', currentState.sessionId);
    console.log('角色:', currentState.role);
    
    if (!currentState.sessionId || !currentState.role) {
        console.error('❌ 会话信息不完整');
        showToast('会话信息丢失，请重新开始', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/reveal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentState.sessionId,
                role: currentState.role
            })
        });
        
        console.log('API响应状态:', response.status);
        const data = await response.json();
        console.log('API响应数据:', data);
        
        if (data.success) {
            console.log('✅ 成功获取结果，准备显示...');
            displayResult(data.result);
            showScene('scene-result');
        } else {
            console.error('❌ API返回失败:', data.message);
            showToast(data.message || '获取结果失败', 'error');
            
            // 应急：显示手动重试按钮
            const submitBtn = document.getElementById('submit-btn');
            submitBtn.textContent = '⚠️ 点击重试查看结果';
            submitBtn.disabled = false;
            submitBtn.classList.add('btn-warning');
        }
    } catch (error) {
        console.error('❌ 网络请求异常:', error);
        showToast('网络错误，请重试', 'error');
        
        // 应急：显示手动重试按钮
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.textContent = '⚠️ 点击重试查看结果';
        submitBtn.disabled = false;
        submitBtn.classList.add('btn-warning');
    }
}

// 显示结果
function displayResult(result) {
    const resultIcon = document.getElementById('result-icon');
    const resultMessage = document.getElementById('result-message');
    
    // 设置图标和消息
    if (result.comparison === 'equal') {
        resultIcon.textContent = '🤝';
        resultMessage.textContent = result.message;
    } else if (result.comparison === 'higher') {
        resultIcon.textContent = '📈';
        resultMessage.textContent = result.message;
    } else {
        resultIcon.textContent = '📊';
        resultMessage.textContent = result.message;
    }
    
    // 显示公司A信息
    document.getElementById('company-a-name').textContent = result.company_a.name;
    document.getElementById('company-a-level').textContent = result.company_a.level_info.name;
    document.getElementById('company-a-desc').textContent = result.company_a.level_info.description;
    
    // 显示公司B信息
    document.getElementById('company-b-name').textContent = result.company_b.name;
    document.getElementById('company-b-level').textContent = result.company_b.level_info.name;
    document.getElementById('company-b-desc').textContent = result.company_b.level_info.description;
}

// 确认重新开始
function confirmStartOver() {
    if (confirm('确定要取消当前会话并重新开始吗？')) {
        startOver();
    }
}

// 重新开始
function startOver() {
    // 重置状态
    currentState = {
        sessionId: null,
        role: null,
        companyName: null,
        committed: false,
        pollInterval: null,
        resultRevealed: false,
        filesUploaded: false,
        bankFile: null,
        commitmentFile: null
    };
    clearState();  // 清除保存的状态
    
    // 重置表单
    document.getElementById('company-name-create').value = '';
    document.getElementById('company-name-join').value = '';
    document.getElementById('session-id-join').value = '';
    document.getElementById('amount-input').value = '';
    document.getElementById('amount-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('submit-btn').textContent = '🔒 加密并提交';
    
    // 重置文件上传
    if (document.getElementById('bank-file')) {
        document.getElementById('bank-file').value = '';
        document.getElementById('bank-file-name').textContent = '未选择文件';
        document.getElementById('bank-file-name').classList.remove('selected');
        document.getElementById('bank-upload-area').classList.remove('has-file');
    }
    
    if (document.getElementById('commitment-file')) {
        document.getElementById('commitment-file').value = '';
        document.getElementById('commitment-file-name').textContent = '未选择文件';
        document.getElementById('commitment-file-name').classList.remove('selected');
        document.getElementById('commitment-upload-area').classList.remove('has-file');
    }
    
    if (document.getElementById('upload-status')) {
        document.getElementById('upload-status').style.display = 'none';
        document.getElementById('progress-bar').style.width = '0%';
    }
    
    // 停止轮询
    stopPolling();
    
    // 返回初始场景
    showScene('scene-role');
}

// 验证会话是否有效
async function validateSession() {
    if (!currentState.sessionId) return false;
    
    try {
        const response = await fetch(`${API_BASE}/api/session_status?session_id=${currentState.sessionId}`);
        if (response.status === 404) {
            console.log('❌ 会话验证失败：会话不存在');
            return false;
        }
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('❌ 会话验证失败:', error);
        return false;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 安全流水比较系统已加载');
    
    // 尝试恢复会话状态
    if (loadState()) {
        console.log('🔄 检测到本地保存的会话，正在验证...');
        
        // 验证会话是否仍然有效
        const isValid = await validateSession();
        
        if (!isValid) {
            console.log('⚠️ 会话已失效（服务器重启或会话过期），清除本地状态');
            clearState();
            showToast('会话已过期，请重新开始', 'error');
            return;
        }
        
        console.log('✅ 会话验证成功，恢复状态...');
        
        // 如果已经提交，恢复到输入界面
        if (currentState.committed) {
            setupInputScene();
            showScene('scene-input');
            
            // 更新状态显示
            document.getElementById('my-status').textContent = '已提交';
            document.getElementById('my-status').className = 'status-badge committed';
            document.getElementById('amount-input').disabled = true;
            document.getElementById('submit-btn').textContent = '✓ 已提交，等待对方...';
            document.getElementById('submit-btn').disabled = true;
            
            // 重新启动轮询
            startPolling();
            
            showToast('会话已恢复，继续等待...', 'success');
        }
    }
});

