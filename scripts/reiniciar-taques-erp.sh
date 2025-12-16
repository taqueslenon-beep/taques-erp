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

# Configurações
PROJECT_DIR="/Users/lenontaques/Documents/taques-erp"
PORTA=8081
MAX_TENTATIVAS=15

# Função para verificar se servidor está respondendo
verificar_servidor() {
    curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORTA" 2>/dev/null | grep -q "200\|302"
}

# 1. Mata TODOS os processos Python do projeto
pkill -9 -f "python.*taques-erp" 2>/dev/null
pkill -9 -f "python.*iniciar.py" 2>/dev/null
pkill -9 -f "python.*dev_server" 2>/dev/null
pkill -9 -f "python.*mini_erp" 2>/dev/null

# 2. Aguarda processos morrerem completamente
sleep 2

# 3. Libera porta se ainda estiver ocupada
lsof -ti:$PORTA | xargs kill -9 2>/dev/null
sleep 1

# 4. Inicia o servidor em background (com DEV_SERVER=true para evitar abertura automática)
cd "$PROJECT_DIR" || exit 1
source .venv/bin/activate
DEV_SERVER=true python3 iniciar.py > /dev/null 2>&1 &

# 5. Aguarda servidor iniciar (com timeout)
tentativa=0
while [ $tentativa -lt $MAX_TENTATIVAS ]; do
    sleep 1
    if verificar_servidor; then
        # 6. Abre UMA única aba no navegador
        open "http://localhost:$PORTA"
        echo "✅ Servidor TAQUES-ERP reiniciado!"
        exit 0
    fi
    tentativa=$((tentativa + 1))
done

echo "⚠️ Servidor iniciado mas não respondeu em $MAX_TENTATIVAS segundos"
exit 1
