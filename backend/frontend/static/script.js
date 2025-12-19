/**
 * Risk Orchestrator - 前端脚本
 * 
 * 基于 secret 项目的 MPC 验证前端
 */

// 全局状态
let currentState = {
    sessionId: null,
    role: null,  // 'company_a' or 'company_b'
    companyName: null,
    committed: false,
    pollInterval: null,
    resultRevealed: false,
    filesUploaded: false,
    bankFile: null,
    commitmentFile: null,
    privacyLevel: 'detailed'  // 隐私级别
};

// API基础URL
const API_BASE = '';

// ============ 状态管理 ============

function saveState() {
    const stateToSave = {
        sessionId: currentState.sessionId,
        role: currentState.role,
        companyName: currentState.companyName,
        committed: currentState.committed,
        resultRevealed: currentState.resultRevealed,
        timestamp: Date.now()
    };
    localStorage.setItem('riskOrchestratorState', JSON.stringify(stateToSave));
    console.log('💾 状态已保存');
}

function loadState() {
    const saved = localStorage.getItem('riskOrchestratorState');
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
                localStorage.removeItem('riskOrchestratorState');
            }
        } catch (e) {
            console.error('恢复状态失败:', e);
        }
    }
    return false;
}

function clearState() {
    localStorage.removeItem('riskOrchestratorState');
    console.log('🗑️ 状态已清除');
}

// ============ UI 工具函数 ============

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function showScene(sceneId) {
    document.querySelectorAll('.scene').forEach(scene => {
        scene.classList.remove('active');
    });
    document.getElementById(sceneId).classList.add('active');
    updateSteps(sceneId);
}

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

// ============ 角色选择 ============

function selectRole(role) {
    if (role === 'create') {
        showScene('scene-create');
    } else if (role === 'join') {
        showScene('scene-join');
    }
}

function backToRole() {
    showScene('scene-role');
}

// ============ 会话管理 ============

async function createSession() {
    const companyName = document.getElementById('company-name-create').value.trim();
    const privacyLevel = document.querySelector('input[name="privacy-level"]:checked')?.value || 'detailed';
    
    if (!companyName) {
        showToast('请输入公司名称', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/create_session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                company_name: companyName,
                privacy_level: privacyLevel
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.sessionId = data.session_id;
            currentState.role = data.role;
            currentState.companyName = companyName;
            currentState.committed = false;
            currentState.resultRevealed = false;
            currentState.filesUploaded = false;
            currentState.bankFile = null;
            currentState.commitmentFile = null;
            currentState.privacyLevel = privacyLevel;
            saveState();
            
            document.getElementById('session-id-display').textContent = data.session_id;
            showScene('scene-waiting');
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
            headers: { 'Content-Type': 'application/json' },
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
            currentState.committed = false;
            currentState.resultRevealed = false;
            currentState.filesUploaded = false;
            currentState.bankFile = null;
            currentState.commitmentFile = null;
            currentState.privacyLevel = data.privacy_level || 'detailed';
            saveState();
            
            setupInputScene();
            showScene('scene-input');
            startPolling();
            
            // 显示隐私级别提示
            const privacyMsg = data.privacy_level === 'minimal' 
                ? '🔐 最小披露模式（仅显示比较结果）' 
                : '📊 详细模式（显示双方档次）';
            showToast(`成功加入会话！${privacyMsg}`, 'success');
        } else {
            showToast(data.message || '加入会话失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('网络错误，请重试', 'error');
    }
}

function copySessionId() {
    const sessionId = document.getElementById('session-id-display').textContent;
    navigator.clipboard.writeText(sessionId).then(() => {
        showToast('会话ID已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败，请手动复制', 'error');
    });
}

// ============ 轮询 ============

function startPolling() {
    if (currentState.pollInterval) {
        clearInterval(currentState.pollInterval);
    }
    currentState.pollInterval = setInterval(checkSessionStatus, 2000);
}

function stopPolling() {
    if (currentState.pollInterval) {
        clearInterval(currentState.pollInterval);
        currentState.pollInterval = null;
    }
}

async function checkSessionStatus() {
    if (!currentState.sessionId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/session_status?session_id=${currentState.sessionId}`);
        
        if (response.status === 404) {
            console.log('⚠️ 会话已失效');
            stopPolling();
            clearState();
            showToast('会话已失效，请重新开始', 'error');
            setTimeout(() => startOver(), 3000);
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
                
                if (data.company_a_committed && data.company_b_committed && 
                    currentState.committed && !currentState.resultRevealed) {
                    console.log('🔍 双方都已提交，自动显示结果...');
                    currentState.resultRevealed = true;
                    stopPolling();
                    
                    const submitBtn = document.getElementById('submit-btn');
                    submitBtn.textContent = '✓ 正在加载结果...';
                    submitBtn.disabled = true;
                    
                    setTimeout(() => revealResult(), 300);
                }
            }
        }
    } catch (error) {
        console.error('Polling error:', error);
    }
}

function setupInputScene() {
    document.getElementById('current-session-id').textContent = currentState.sessionId;
    
    if (currentState.role === 'company_a') {
        document.getElementById('participants').textContent = `${currentState.companyName} (您) vs 等待对方...`;
    } else {
        document.getElementById('participants').textContent = `对方公司 vs ${currentState.companyName} (您)`;
    }
    
    // 显示隐私级别
    const privacyDisplay = document.getElementById('privacy-level-display');
    if (privacyDisplay) {
        if (currentState.privacyLevel === 'minimal') {
            privacyDisplay.innerHTML = '<span class="privacy-tag minimal">🔐 最小披露</span> 结果仅显示谁更高';
        } else {
            privacyDisplay.innerHTML = '<span class="privacy-tag detailed">📊 显示档次</span> 结果将显示双方档次';
        }
    }
}

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

// ============ 文件处理 ============

function handleFileSelect(type) {
    const fileInput = document.getElementById(`${type}-file`);
    const fileName = document.getElementById(`${type}-file-name`);
    const uploadArea = document.getElementById(`${type}-upload-area`);
    
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        
        if (file.size > 10 * 1024 * 1024) {
            showToast('文件大小不能超过10MB', 'error');
            fileInput.value = '';
            return;
        }
        
        const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            showToast('只支持 PDF、PNG、JPG 格式', 'error');
            fileInput.value = '';
            return;
        }
        
        fileName.textContent = file.name;
        fileName.classList.add('selected');
        uploadArea.classList.add('has-file');
        
        if (type === 'bank') {
            currentState.bankFile = file;
        } else {
            currentState.commitmentFile = file;
        }
        
        console.log(`✅ ${type === 'bank' ? '银行流水' : '承诺书'}文件已选择:`, file.name);
    }
}

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

// ============ 提交和揭示 ============

async function submitAmount() {
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn.textContent.includes('查看比较结果')) {
        currentState.resultRevealed = true;
        stopPolling();
        revealResult();
        return;
    }
    
    if (currentState.committed) {
        showToast('您已经提交过了，请等待对方提交', 'error');
        return;
    }
    
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
    
    if (!currentState.filesUploaded) {
        const uploaded = await uploadFiles();
        if (!uploaded) return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/commit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentState.sessionId,
                role: currentState.role,
                amount: amount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentState.committed = true;
            saveState();
            
            document.getElementById('my-status').textContent = '已提交';
            document.getElementById('my-status').className = 'status-badge committed';
            document.getElementById('amount-input').disabled = true;
            
            showToast(`承诺已提交！您的档次: ${data.level_info.name}`, 'success');
            
            if (data.status === 'both_committed') {
                console.log('✅ 双方都已提交，立即显示结果');
                currentState.resultRevealed = true;
                stopPolling();
                
                document.getElementById('submit-btn').textContent = '✓ 正在加载结果...';
                document.getElementById('submit-btn').disabled = true;
                
                setTimeout(() => revealResult(), 500);
            } else {
                console.log('⏳ 提交成功，等待对方提交...');
                document.getElementById('submit-btn').disabled = true;
                document.getElementById('submit-btn').textContent = '✓ 已提交，等待对方...';
                
                if (!currentState.pollInterval) {
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

async function revealResult() {
    console.log('📊 开始获取比较结果...');
    
    if (!currentState.sessionId || !currentState.role) {
        console.error('❌ 会话信息不完整');
        showToast('会话信息丢失，请重新开始', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/reveal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentState.sessionId,
                role: currentState.role
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ 成功获取结果');
            displayResult(data.result);
            showScene('scene-result');
        } else {
            console.error('❌ API返回失败:', data.message);
            showToast(data.message || '获取结果失败', 'error');
            
            const submitBtn = document.getElementById('submit-btn');
            submitBtn.textContent = '⚠️ 点击重试查看结果';
            submitBtn.disabled = false;
            submitBtn.classList.add('btn-warning');
        }
    } catch (error) {
        console.error('❌ 网络请求异常:', error);
        showToast('网络错误，请重试', 'error');
        
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.textContent = '⚠️ 点击重试查看结果';
        submitBtn.disabled = false;
        submitBtn.classList.add('btn-warning');
    }
}

function displayResult(result) {
    const resultIcon = document.getElementById('result-icon');
    const resultMessage = document.getElementById('result-message');
    
    // 设置结果图标
    if (result.comparison === 'equal') {
        resultIcon.textContent = '🤝';
    } else if (result.comparison === 'a_higher') {
        resultIcon.textContent = '📈';
    } else if (result.comparison === 'b_higher') {
        resultIcon.textContent = '📊';
    } else {
        resultIcon.textContent = '✅';
    }
    
    resultMessage.textContent = result.message;
    
    // 公司名称
    document.getElementById('company-a-name').textContent = result.company_a.name;
    document.getElementById('company-b-name').textContent = result.company_b.name;
    
    // 根据隐私级别显示档次信息
    if (result.privacy_level === 'minimal' || !result.company_a.level_info) {
        // 最小披露模式：隐藏具体档次
        document.getElementById('company-a-level').textContent = '🔒 已保密';
        document.getElementById('company-a-desc').textContent = '';
        document.getElementById('company-b-level').textContent = '🔒 已保密';
        document.getElementById('company-b-desc').textContent = '';
    } else {
        // 详细模式：显示档次
        document.getElementById('company-a-level').textContent = result.company_a.level_info.name;
        document.getElementById('company-a-desc').textContent = result.company_a.level_info.description;
        document.getElementById('company-b-level').textContent = result.company_b.level_info.name;
        document.getElementById('company-b-desc').textContent = result.company_b.level_info.description;
    }
}

// ============ 重置 ============

function confirmStartOver() {
    if (confirm('确定要取消当前会话并重新开始吗？')) {
        startOver();
    }
}

function startOver() {
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
    clearState();
    
    document.getElementById('company-name-create').value = '';
    document.getElementById('company-name-join').value = '';
    document.getElementById('session-id-join').value = '';
    document.getElementById('amount-input').value = '';
    document.getElementById('amount-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('submit-btn').textContent = '🔒 加密并提交';
    
    // 重置文件上传
    ['bank', 'commitment'].forEach(type => {
        const fileInput = document.getElementById(`${type}-file`);
        const fileName = document.getElementById(`${type}-file-name`);
        const uploadArea = document.getElementById(`${type}-upload-area`);
        if (fileInput) {
            fileInput.value = '';
            fileName.textContent = '未选择文件';
            fileName.classList.remove('selected');
            uploadArea.classList.remove('has-file');
        }
    });
    
    const uploadStatus = document.getElementById('upload-status');
    if (uploadStatus) {
        uploadStatus.style.display = 'none';
        document.getElementById('progress-bar').style.width = '0%';
    }
    
    stopPolling();
    showScene('scene-role');
}

// ============ 会话验证 ============

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

// ============ 初始化 ============

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Risk Orchestrator 已加载');
    
    if (loadState()) {
        console.log('🔄 检测到本地保存的会话，正在验证...');
        
        const isValid = await validateSession();
        
        if (!isValid) {
            console.log('⚠️ 会话已失效，清除本地状态');
            clearState();
            showToast('会话已过期，请重新开始', 'error');
            return;
        }
        
        console.log('✅ 会话验证成功，恢复状态...');
        
        if (currentState.committed) {
            setupInputScene();
            showScene('scene-input');
            
            document.getElementById('my-status').textContent = '已提交';
            document.getElementById('my-status').className = 'status-badge committed';
            document.getElementById('amount-input').disabled = true;
            document.getElementById('submit-btn').textContent = '✓ 已提交，等待对方...';
            document.getElementById('submit-btn').disabled = true;
            
            startPolling();
            showToast('会话已恢复，继续等待...', 'success');
        }
    }
});

