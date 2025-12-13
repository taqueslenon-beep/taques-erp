#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Reiniciar TAQUES-ERP
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🔄
# @raycast.packageName TAQUES-ERP

# Documentation:
# @raycast.description Reinicia o servidor do sistema TAQUES-ERP

# Mata processos Python do projeto
pkill -f "python.*taques-erp" 2>/dev/null
pkill -f "python.*iniciar.py" 2>/dev/null
pkill -f "python.*dev_server" 2>/dev/null
pkill -f "python.*mini_erp" 2>/dev/null

sleep 1

# Inicia o servidor
cd /Users/lenontaques/Documents/taques-erp
source .venv/bin/activate
python3 iniciar.py &

echo "✅ Servidor TAQUES-ERP reiniciado!"