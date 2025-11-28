#!/bin/bash
# TAQUES ERP - Script de Inicialização (Mac)
# Duplo-clique para iniciar o sistema

cd "$(dirname "$0")"

# Ativa ambiente virtual se existir
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Inicia o sistema
python3 iniciar.py


