#!/bin/bash

# Script para reiniciar servidor TAQUES-ERP via Raycast
# Mata processos Python do projeto e reinicia o servidor

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Reiniciando servidor TAQUES-ERP...${NC}"

# Diretório do projeto
PROJECT_DIR="/Users/lenontaques/Documents/taques-erp"

# Mata processos Python do projeto
echo -e "${YELLOW}⏹️  Encerrando processos existentes...${NC}"

pkill -f "python.*taques-erp" 2>/dev/null
pkill -f "python.*iniciar.py" 2>/dev/null
pkill -f "python.*dev_server" 2>/dev/null
pkill -f "python.*mini_erp" 2>/dev/null

# Aguarda processos terminarem
sleep 1

# Verifica se ainda há processos rodando
if pgrep -f "python.*taques-erp\|python.*iniciar.py\|python.*dev_server\|python.*mini_erp" > /dev/null; then
    echo -e "${RED}⚠️  Alguns processos ainda estão rodando. Tentando forçar encerramento...${NC}"
    pkill -9 -f "python.*taques-erp" 2>/dev/null
    pkill -9 -f "python.*iniciar.py" 2>/dev/null
    pkill -9 -f "python.*dev_server" 2>/dev/null
    pkill -9 -f "python.*mini_erp" 2>/dev/null
    sleep 1
fi

# Muda para o diretório do projeto
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Erro: Não foi possível acessar o diretório do projeto${NC}"
    exit 1
}

# Ativa ambiente virtual se existir
if [ -d ".venv" ]; then
    echo -e "${YELLOW}🐍 Ativando ambiente virtual...${NC}"
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo -e "${YELLOW}🐍 Ativando ambiente virtual...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Ambiente virtual não encontrado. Usando Python do sistema.${NC}"
fi

# Inicia o servidor em background
echo -e "${GREEN}🚀 Iniciando servidor...${NC}"
python3 iniciar.py > /dev/null 2>&1 &

# Aguarda um pouco para o servidor iniciar
sleep 2

# Verifica se o servidor iniciou
if pgrep -f "python.*iniciar.py\|python.*dev_server\|python.*mini_erp" > /dev/null; then
    echo -e "${GREEN}✅ Servidor TAQUES-ERP reiniciado com sucesso!${NC}"
    echo -e "${GREEN}🌐 Acesse: http://localhost:8081${NC}"
else
    echo -e "${RED}❌ Erro: Servidor não iniciou corretamente${NC}"
    echo -e "${YELLOW}💡 Tente executar manualmente: python3 iniciar.py${NC}"
    exit 1
fi

