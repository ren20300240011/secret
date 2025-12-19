#!/bin/bash
echo "========================================"
echo " Risk Orchestrator - 启动服务器"
echo "========================================"
echo

# 创建必要目录
mkdir -p data uploads

echo "服务器地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo
echo "按 Ctrl+C 停止服务器"
echo
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
