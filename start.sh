#!/bin/bash

echo "🚀 启动企业流水安全比较系统"
echo "================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

echo "✓ Python已安装: $(python3 --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo ""
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "📥 检查并安装依赖包..."
pip install -q -r requirements.txt
echo "✓ 依赖包已安装"

# 启动服务器
echo ""
echo "🌟 启动服务器..."
echo "================================"
echo ""
echo "✨ 系统已启动！请在浏览器中访问："
echo ""
echo "   👉 http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""
python app.py


