/**
 * EDR 企业风险画像分析 - 前端脚本
 */

const API_BASE = '';
let currentTaskId = null;
let pollInterval = null;

// ============ 工具函数 ============

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function showSection(sectionId) {
    ['search-section', 'progress-section', 'result-section', 'error-section'].forEach(id => {
        document.getElementById(id).style.display = id === sectionId ? 'block' : 'none';
    });
}

// ============ 分析流程 ============

async function startAnalysis() {
    const companyName = document.getElementById('company-input').value.trim();
    
    if (!companyName) {
        showToast('请输入企业名称', 'error');
        return;
    }
    
    // 显示进度
    showSection('progress-section');
    document.getElementById('analyzing-company').textContent = companyName;
    updateProgress(0, '初始化分析任务...');
    resetProgressSteps();
    
    try {
        // 先启动进度模拟
        simulateProgress();
        
        // 使用同步接口（等待完成）
        const response = await fetch(`${API_BASE}/api/v1/edr/analyze/sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: companyName,
                include_reputation: false
            })
        });
        
        const data = await response.json();
        
        // 停止模拟进度
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        
        if (data.success) {
            updateProgress(100, '分析完成');
            completeAllSteps();
            setTimeout(() => displayResult(data), 500);
        } else {
            showError(data.error || '分析失败，请重试');
        }
    } catch (error) {
        console.error('分析请求失败:', error);
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        showError('网络错误，请检查连接后重试');
    }
}

function simulateProgress() {
    let progress = 10;
    const stages = [
        { progress: 20, stage: '搜索企业基础信息...', step: 'step-info' },
        { progress: 40, stage: '搜索企业新闻动态...', step: 'step-news' },
        { progress: 60, stage: '搜索企业口碑评价...', step: 'step-reputation' },
        { progress: 80, stage: 'AI 深度分析中...', step: 'step-analysis' }
    ];
    let stageIndex = 0;
    
    pollInterval = setInterval(() => {
        if (stageIndex < stages.length && progress >= stages[stageIndex].progress) {
            const stage = stages[stageIndex];
            updateProgress(stage.progress, stage.stage);
            activateStep(stage.step);
            stageIndex++;
        }
        
        progress += Math.random() * 5;
        if (progress > 95) progress = 95;
        
        document.getElementById('progress-bar').style.width = `${progress}%`;
        document.getElementById('progress-text').textContent = `${Math.round(progress)}%`;
    }, 1000);
}

function updateProgress(percent, stage) {
    document.getElementById('progress-bar').style.width = `${percent}%`;
    document.getElementById('progress-text').textContent = `${percent}%`;
    document.getElementById('progress-stage').textContent = stage;
}

function resetProgressSteps() {
    ['step-info', 'step-news', 'step-reputation', 'step-analysis'].forEach(id => {
        document.getElementById(id).classList.remove('active', 'completed');
    });
}

function activateStep(stepId) {
    // 将之前的 active 变为 completed
    document.querySelectorAll('.progress-step.active').forEach(el => {
        el.classList.remove('active');
        el.classList.add('completed');
    });
    // 激活当前步骤
    document.getElementById(stepId).classList.add('active');
}

function completeAllSteps() {
    ['step-info', 'step-news', 'step-reputation', 'step-analysis'].forEach(id => {
        document.getElementById(id).classList.remove('active');
        document.getElementById(id).classList.add('completed');
    });
}

// ============ 结果显示 ============

// 保存当前分析的公司名称用于重新分析
let currentAnalyzedCompany = '';

function displayResult(data) {
    showSection('result-section');
    currentAnalyzedCompany = data.company_name;
    
    // 公司名称和元信息
    document.getElementById('result-company-name').textContent = data.company_name;
    document.getElementById('result-time').textContent = `分析时间: ${new Date(data.analyzed_at).toLocaleString()}`;
    
    const sources = data.sources || {};
    const totalSources = (sources.company_info || 0) + (sources.news || 0) + (sources.reputation || 0);
    document.getElementById('result-sources').textContent = `参考来源: ${totalSources} 条`;
    
    // 缓存状态显示
    const cacheStatus = document.getElementById('result-cache-status');
    const refreshBtn = document.getElementById('refresh-btn');
    if (data.from_cache) {
        cacheStatus.textContent = '📦 来自缓存';
        cacheStatus.classList.add('from-cache');
        refreshBtn.style.display = 'inline-block';
    } else {
        cacheStatus.textContent = '✨ 最新分析';
        cacheStatus.classList.remove('from-cache');
        refreshBtn.style.display = 'none';
    }
    
    // 评分
    const score = data.score || 50;
    const riskLevel = data.risk_level || '未知';
    
    document.getElementById('score-value').textContent = score;
    
    // 设置评分圆圈颜色
    const scoreCircle = document.getElementById('score-circle');
    scoreCircle.classList.remove('low-risk', 'medium-risk', 'high-risk');
    if (score >= 70) {
        scoreCircle.classList.add('low-risk');
    } else if (score >= 40) {
        scoreCircle.classList.add('medium-risk');
    } else {
        scoreCircle.classList.add('high-risk');
    }
    
    // 风险等级
    const riskBadge = document.querySelector('.risk-badge');
    riskBadge.textContent = riskLevel;
    riskBadge.classList.remove('low', 'medium', 'high');
    if (riskLevel.includes('低')) {
        riskBadge.classList.add('low');
    } else if (riskLevel.includes('高')) {
        riskBadge.classList.add('high');
    } else {
        riskBadge.classList.add('medium');
    }
    
    // 分析文本 - 解析 Markdown 为美化的 HTML
    const analysisHtml = parseMarkdownToHtml(data.analysis || '暂无详细分析');
    document.getElementById('analysis-text').innerHTML = analysisHtml;
    
    showToast('分析完成！', 'success');
}

/**
 * 将 Markdown 文本解析为美化的 HTML
 */
function parseMarkdownToHtml(markdown) {
    if (!markdown) return '<p>暂无详细分析</p>';
    
    // 按二级标题分割
    const sections = markdown.split(/^## /gm).filter(s => s.trim());
    let html = '';
    
    sections.forEach(section => {
        const lines = section.split('\n');
        const sectionTitle = lines[0].trim();
        const content = lines.slice(1).join('\n');
        
        // 检查是否是维度评估部分
        if (sectionTitle.includes('维度评估') || sectionTitle.includes('各维度')) {
            html += `<div class="report-section"><h2 class="section-title">${escapeHtml(sectionTitle)}</h2></div>`;
            html += '<div class="dimensions-grid">';
            html += parseDimensions(content);
            html += '</div>';
        } else if (sectionTitle.includes('企业概况')) {
            html += `<div class="report-section"><h2 class="section-title">${escapeHtml(sectionTitle)}</h2></div>`;
            html += `<div class="overview-block">${parseContent(content)}</div>`;
        } else if (sectionTitle.includes('综合评分')) {
            html += `<div class="report-section"><h2 class="section-title">${escapeHtml(sectionTitle)}</h2></div>`;
            html += `<div class="summary-block">${parseContent(content)}</div>`;
        } else if (sectionTitle.includes('合作建议')) {
            html += `<div class="report-section"><h2 class="section-title">💡 ${escapeHtml(sectionTitle)}</h2></div>`;
            html += `<div class="suggestion-block">${parseContent(content)}</div>`;
        } else {
            html += `<div class="report-section"><h2 class="section-title">${escapeHtml(sectionTitle)}</h2></div>`;
            html += `<div class="content-block">${parseContent(content)}</div>`;
        }
    });
    
    return `<div class="report-wrapper">${html}</div>`;
}

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * 解析维度评估部分
 */
function parseDimensions(content) {
    // 按 ### 分割维度
    const dims = content.split(/^### /gm).filter(d => d.trim());
    let html = '';
    
    dims.forEach(dim => {
        const lines = dim.split('\n');
        const titleLine = lines[0].trim();
        
        // 提取编号和标题
        const titleMatch = titleLine.match(/^(\d+)\.\s*(.+?)(?:\s*\(0-100分\))?$/);
        if (!titleMatch) return;
        
        const [, num, title] = titleMatch;
        const dimContent = lines.slice(1).join('\n');
        
        // 提取评分
        const scoreMatch = dimContent.match(/评分[：:]\s*(\d+\.?\d*)/);
        const score = scoreMatch ? scoreMatch[1] : '--';
        
        // 提取分析
        const analysisMatch = dimContent.match(/分析[：:]\s*(.+?)(?=\n\n|$)/s);
        const analysis = analysisMatch ? analysisMatch[1].trim() : '';
        
        // 根据分数决定颜色
        const scoreNum = parseFloat(score);
        let scoreClass = 'score-medium';
        if (scoreNum >= 80) scoreClass = 'score-high';
        else if (scoreNum < 60) scoreClass = 'score-low';
        
        html += `
            <div class="dimension-card">
                <div class="dim-header">
                    <span class="dim-num">${num}</span>
                    <span class="dim-title">${escapeHtml(title.trim())}</span>
                    <span class="dim-score ${scoreClass}">${score}<small>分</small></span>
                </div>
                <p class="dim-analysis">${escapeHtml(analysis).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</p>
            </div>
        `;
    });
    
    return html;
}

/**
 * 解析普通内容
 */
function parseContent(content) {
    let html = escapeHtml(content.trim());
    
    // 处理粗体
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // 处理列表
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul class="report-list">$1</ul>');
    
    // 处理数字列表
    html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li><span class="list-num">$1.</span> $2</li>');
    
    // 处理换行
    html = html.replace(/\n\n+/g, '</p><p>');
    html = html.replace(/\n/g, ' ');
    
    return `<p>${html}</p>`.replace(/<p>\s*<\/p>/g, '');
}

function showError(message) {
    showSection('error-section');
    document.getElementById('error-message').textContent = message;
}

// ============ 操作函数 ============

function newAnalysis() {
    showSection('search-section');
    document.getElementById('company-input').value = '';
    document.getElementById('company-input').focus();
}

async function refreshAnalysis() {
    if (!currentAnalyzedCompany) return;
    
    // 先清除缓存
    try {
        await fetch(`${API_BASE}/api/v1/edr/cache/${encodeURIComponent(currentAnalyzedCompany)}`, {
            method: 'DELETE'
        });
    } catch (e) {
        console.error('清除缓存失败:', e);
    }
    
    // 重新分析
    document.getElementById('company-input').value = currentAnalyzedCompany;
    startAnalysis();
}

function exportPDF() {
    // 检查库是否加载
    if (typeof html2pdf === 'undefined') {
        showToast('PDF 库加载失败，使用文本导出', 'error');
        exportText();
        return;
    }
    
    const companyName = document.getElementById('result-company-name').textContent || '未知企业';
    const score = document.getElementById('score-value').textContent || '--';
    const riskLevel = document.querySelector('.risk-badge').textContent || '未知';
    const analysisText = document.getElementById('analysis-text').innerText || '暂无分析内容';
    const resultTime = document.getElementById('result-time').textContent || '';
    
    // 创建 PDF 容器
    const pdfContainer = document.createElement('div');
    pdfContainer.id = 'pdf-export-container';
    pdfContainer.style.cssText = `
        position: fixed;
        left: -9999px;
        top: 0;
        width: 210mm;
        background: white;
        padding: 20mm;
        font-family: "Microsoft YaHei", "SimSun", sans-serif;
        color: #333;
        font-size: 12pt;
        line-height: 1.6;
    `;
    
    pdfContainer.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #3b82f6;">
            <h1 style="font-size: 20pt; color: #1e40af; margin: 0 0 8px 0;">企业风险画像分析报告</h1>
            <p style="color: #666; margin: 0; font-size: 10pt;">Risk Orchestrator EDR 模块</p>
        </div>
        
        <div style="display: table; width: 100%; margin-bottom: 20px; background: #f5f5f5; padding: 15px; border-radius: 5px;">
            <div style="display: table-row;">
                <div style="display: table-cell; width: 33%; vertical-align: top;">
                    <div style="color: #888; font-size: 9pt; margin-bottom: 3px;">分析企业</div>
                    <div style="font-size: 14pt; font-weight: bold; color: #333;">${companyName}</div>
                </div>
                <div style="display: table-cell; width: 33%; text-align: center; vertical-align: top;">
                    <div style="color: #888; font-size: 9pt; margin-bottom: 3px;">综合评分</div>
                    <div style="font-size: 20pt; font-weight: bold; color: #22c55e;">${score}<span style="font-size: 10pt;">分</span></div>
                </div>
                <div style="display: table-cell; width: 33%; text-align: right; vertical-align: top;">
                    <div style="color: #888; font-size: 9pt; margin-bottom: 3px;">风险等级</div>
                    <div style="font-size: 12pt; font-weight: bold; color: #3b82f6;">${riskLevel}</div>
                </div>
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h2 style="font-size: 12pt; color: #333; border-left: 3px solid #3b82f6; padding-left: 8px; margin: 0 0 10px 0;">详细分析报告</h2>
            <div style="font-size: 10pt; line-height: 1.8; color: #444; white-space: pre-wrap;">${analysisText}</div>
        </div>
        
        <div style="margin-top: 25px; padding-top: 12px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 8pt;">
            <p style="margin: 0;">本报告由 Risk Orchestrator 系统自动生成</p>
            <p style="margin: 3px 0 0 0;">${resultTime} | 仅供参考，不构成任何投资或合作建议</p>
        </div>
    `;
    
    document.body.appendChild(pdfContainer);
    
    showToast('正在生成 PDF...', 'info');
    
    // 等待一下让 DOM 渲染
    setTimeout(() => {
        const opt = {
            margin: 0,
            filename: `${companyName}_风险分析报告.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { 
                scale: 2,
                useCORS: true,
                logging: false,
                windowWidth: 794 // A4 宽度 in px at 96 DPI
            },
            jsPDF: { 
                unit: 'mm', 
                format: 'a4', 
                orientation: 'portrait' 
            }
        };
        
        html2pdf().set(opt).from(pdfContainer).save()
            .then(() => {
                document.body.removeChild(pdfContainer);
                showToast('PDF 导出成功！', 'success');
            })
            .catch(err => {
                document.body.removeChild(pdfContainer);
                console.error('PDF 导出失败:', err);
                showToast('PDF 导出失败，尝试文本导出', 'error');
                exportText();
            });
    }, 100);
}

function exportText() {
    const companyName = document.getElementById('result-company-name').textContent;
    const score = document.getElementById('score-value').textContent;
    const riskLevel = document.querySelector('.risk-badge').textContent;
    const analysis = document.getElementById('analysis-text').innerText;
    
    const report = `
================================================================================
                    企业风险画像分析报告
================================================================================

企业名称: ${companyName}
综合评分: ${score}分
风险等级: ${riskLevel}
生成时间: ${new Date().toLocaleString()}

================================================================================
                         详细分析
================================================================================

${analysis}

================================================================================
                  由 Risk Orchestrator EDR 模块生成
================================================================================
`;

    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyName}_风险分析报告.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('报告已导出（文本格式）', 'success');
}

// ============ 初始化 ============

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 EDR 企业风险画像分析已加载');
    
    // 回车触发搜索
    document.getElementById('company-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            startAnalysis();
        }
    });
});

