#!/bin/bash
# Script para reiniciar o servidor forçando limpeza completa

echo "🛑 Parando todos os processos Python relacionados..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*dev_server" 2>/dev/null
pkill -f "nicegui" 2>/dev/null
sleep 2

echo "🧹 Limpando cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

echo "✅ Cache limpo"
echo ""
echo "🚀 Agora inicie o servidor manualmente:"
echo "   python3 -m mini_erp.main"
echo ""
echo "Ou:"
echo "   python3 dev_server.py"















