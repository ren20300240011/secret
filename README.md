# 🏢 Risk Orchestrator

**企业合作风险与信任评估系统**

通过"公开信息分析(EDR) + 私密能力验证（MPC）"，在不泄露敏感数据的前提下，给出可决策的合作建议。

---

## 🎯 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Risk-Orchestrator                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌──────────────────────┐     ┌──────────────────────┐│
│   │   📡 公开信息分析      │     │   🔐 私密能力验证      ││
│   │   (EDR 深度研究)      │     │   (MPC 安全计算)      ││
│   │   ✅ 已完成           │     │   ✅ 已完成           ││
│   └──────────────────────┘     └──────────────────────┘│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## ✨ 功能特性

### 📡 EDR 公开信息分析模块

基于 DeepSeek AI 大模型的企业风险画像分析系统。

**功能特点**：
- 🔍 **多维度搜索**：通过 Tavily API 获取企业公开信息
- 🤖 **AI 智能分析**：DeepSeek 大模型深度解读企业风险
- 📊 **量化评分**：4大维度评估，综合风险评分
- 💾 **结果缓存**：支持分析结果复现，确保一致性
- 📄 **PDF 导出**：一键导出专业分析报告

**评估维度**：
| 维度 | 说明 |
|------|------|
| 🏢 基础信息可靠性 | 工商注册、资质、经营状态 |
| 💰 财务健康 | 公开财务信息、融资情况 |
| 📰 新闻舆情健康 | 媒体报道、舆情动态 |
| ⚖️ 法律合规 | 诉讼记录、行政处罚 |

### 🔐 MPC 私密能力验证模块

基于密码学安全多方计算的企业信用评级比较系统。两家公司可以在**不泄漏具体流水金额**的情况下，比较彼此的信用档次。

**核心原理**：

使用密码学承诺方案（Commitment Scheme）：

```
承诺值 = SHA256(档次等级 + 随机秘密值)
```

**特性**：
- **隐藏性**：从承诺值无法推断出实际档次
- **绑定性**：提交后无法修改档次等级
- **可验证性**：揭示时可验证承诺的真实性

**隐私级别选择**：

| 级别 | 说明 |
|------|------|
| 🔓 显示档次 | 双方可查看对方具体信用档次 |
| 🔒 最小披露 | 仅显示比较结果，不披露具体档次 |

**信用档次划分**：

| 档次 | 名称 | 流水范围 | 说明 |
|------|------|----------|------|
| 1️⃣ | 初创级 | 10万 - 100万 | 初创企业或小微企业 |
| 2️⃣ | 成长级 | 100万 - 1000万 | 成长期企业 |
| 3️⃣ | 发展级 | 1000万 - 1亿 | 发展期企业 |
| 4️⃣ | 成熟级 | 1亿 - 10亿 | 成熟期企业 |
| 5️⃣ | 领军级 | 10亿以上 | 行业领军企业 |

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- 现代浏览器（Chrome、Firefox、Safari、Edge）
- API 密钥：DeepSeek + Tavily（EDR 模块需要）

### 安装步骤

```bash
# 1. 进入项目目录
cd risk-orchestrator/backend

# 2. 创建并激活虚拟环境（推荐）
# 使用 venv:
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux

# 或使用 conda:
conda create -n risk python=3.11
conda activate risk

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（EDR 模块需要）
cp env.example .env
# 编辑 .env 文件，填入 API 密钥

# 5. 启动服务器
# Windows:
start.bat

# macOS/Linux:
./start.sh

# 或手动启动:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. 访问系统
# http://localhost:8000
```

### API 密钥获取

| 服务 | 获取地址 | 用途 |
|------|----------|------|
| DeepSeek | https://platform.deepseek.com/ | AI 风险分析 |
| Tavily | https://tavily.com/ | 公开信息搜索 |

---

## 📖 使用指南

### EDR 公开信息分析

1. 访问 http://localhost:8000/edr
2. 输入要分析的企业名称
3. 点击"开始分析"
4. 等待分析完成（约 30-60 秒）
5. 查看风险画像报告
6. 可选：导出 PDF 报告

### MPC 私密验证

#### 场景：公司 A 和公司 B 需要比较信用档次

**公司 A（发起方）**：
1. 访问 http://localhost:8000
2. 选择"创建新会话"
3. 填写公司名称
4. 选择隐私级别（显示档次/最小披露）
5. 获得会话 ID，发送给公司 B
6. 上传银行流水和承诺书
7. 填写流水金额，提交承诺
8. 等待对方完成，查看结果

**公司 B（加入方）**：
1. 访问 http://localhost:8000
2. 选择"加入会话"
3. 输入会话 ID
4. 填写公司名称
5. 上传银行流水和承诺书
6. 填写流水金额，提交承诺
7. 等待揭示，查看结果

> 💡 **提示**：可以使用两个浏览器标签页或隐私窗口模拟两家公司

---

## 📁 项目结构

```
risk-orchestrator/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   └── v1/
│   │   │       ├── edr.py    # EDR分析接口
│   │   │       ├── mpc.py    # MPC验证接口
│   │   │       └── router.py
│   │   ├── core/             # 核心配置
│   │   │   └── config.py
│   │   ├── engines/          # 引擎模块
│   │   │   ├── edr/          # EDR引擎
│   │   │   │   ├── analyzer.py    # AI分析
│   │   │   │   ├── cache.py       # 结果缓存
│   │   │   │   ├── engine.py      # 主引擎
│   │   │   │   ├── llm_client.py  # DeepSeek客户端
│   │   │   │   └── search.py      # Tavily搜索
│   │   │   └── mpc/          # MPC引擎
│   │   │       ├── commitments.py
│   │   │       ├── engine.py
│   │   │       └── levels.py
│   │   ├── models/           # 数据模型
│   │   │   └── schemas.py
│   │   ├── services/         # 业务服务
│   │   │   └── session_storage.py
│   │   └── main.py           # FastAPI入口
│   ├── frontend/
│   │   ├── static/
│   │   │   ├── edr.css / edr.js
│   │   │   └── style.css / script.js
│   │   └── templates/
│   │       ├── edr.html
│   │       └── index.html
│   ├── data/                 # 数据存储
│   │   └── edr_cache/        # EDR缓存
│   ├── templates/            # 文档模板
│   │   ├── 承诺书模板.md
│   │   └── 银行流水说明.md
│   ├── test_files/           # 测试文件
│   ├── env.example           # 环境变量示例
│   ├── requirements.txt
│   ├── start.bat / start.sh
│   └── test_edr.py           # EDR测试脚本
└── README.md
```

---

## 🔧 API 接口

### EDR 分析接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/v1/edr/analyze` | 分析企业风险 |
| GET | `/api/v1/edr/cache` | 获取缓存列表 |
| DELETE | `/api/v1/edr/cache/{company}` | 清除指定缓存 |

### MPC 验证接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/v1/mpc/sessions` | 创建验证会话 |
| POST | `/api/v1/mpc/sessions/join` | 加入会话 |
| POST | `/api/v1/mpc/sessions/upload` | 上传文件 |
| POST | `/api/v1/mpc/sessions/commit` | 提交承诺 |
| POST | `/api/v1/mpc/sessions/reveal` | 揭示结果 |
| GET | `/api/v1/mpc/sessions/{id}/status` | 获取状态 |
| GET | `/api/v1/mpc/levels` | 获取档次信息 |
| GET | `/api/v1/mpc/history` | 获取历史记录 |

### 兼容旧API

| 方法 | 路径 |
|-----|------|
| POST | `/api/create_session` |
| POST | `/api/join_session` |
| POST | `/api/upload_files` |
| POST | `/api/commit` |
| POST | `/api/reveal` |
| GET | `/api/session_status` |

---

## 🛡️ 安全保障

### MPC 模块

✅ **数据不离开客户端**：具体金额只在本地计算，从不发送到服务器  
✅ **加密承诺**：使用 SHA-256 哈希，无法从承诺值反推原始数据  
✅ **双盲提交**：双方必须同时提交，防止后提交方根据对方信息调整  
✅ **只显示档次**：服务器只存储和比较档次等级，不存储具体金额  
✅ **无法作弊**：承诺的绑定性确保提交后无法修改

### EDR 模块

✅ **仅使用公开信息**：不收集任何私密数据  
✅ **AI 辅助分析**：人工智能辅助，最终决策由人做出  
✅ **结果可追溯**：分析结果缓存，支持复现和审计

---

## 📋 文档模板

MPC 验证需要上传以下文件：

| 文件 | 说明 | 模板位置 |
|------|------|----------|
| 银行流水 | 企业银行账户流水记录 | [银行流水说明.md](backend/templates/银行流水说明.md) |
| 承诺书 | 流水真实性承诺书 | [承诺书模板.md](backend/templates/承诺书模板.md) |

> 💡 **测试提示**：`backend/test_files/` 目录下有测试用的模拟文件

---

## 🧪 测试

### EDR 模块测试

```bash
cd backend
python test_edr.py
```

### MPC 模块测试

1. 使用 `test_files/` 目录下的测试文件
2. 打开两个浏览器窗口模拟两家公司
3. 按照使用指南操作

---

## 📄 许可证

Apache 2.0

## 🙏 致谢

- 感谢刘文印老师的指导
- 感谢姚期智教授提出的"百万富翁问题"
