#!/bin/bash
# Script para matar TODOS os processos Python relacionados ao servidor

echo "🛑 Matando TODOS os processos Python relacionados..."
echo ""

# Lista processos antes
echo "Processos encontrados:"
ps aux | grep -E "python.*main\.py|python.*dev_server|nicegui" | grep -v grep | awk '{print $2, $11, $12, $13}'

echo ""
echo "Matando processos..."

# Mata todos os processos Python que podem ser servidores
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "python.*dev_server" 2>/dev/null  
pkill -9 -f "nicegui" 2>/dev/null

# Mata processos específicos nas portas conhecidas
for port in 8081 8082 8083 8084 8085 8086 8087 8088 8089 8090 8091 8092 8093 8094 8095 8096 8097 8098 8099; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

sleep 2

echo ""
echo "✅ Processos finalizados"
echo ""
echo "🧹 Limpando cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

echo "✅ Pronto!"
echo ""
echo "🚀 Agora inicie o servidor:"
echo "   cd /Users/lenontaques/Documents/taques-erp"
echo "   python3 -m mini_erp.main"



