#!/usr/bin/env python3
"""
Script temporário para testar o módulo de Inteligência em nova porta.
"""
import os
import sys

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

# Força reload de todos os módulos relacionados
import importlib

# Limpa qualquer cache
if 'mini_erp.pages.inteligencia' in sys.modules:
    del sys.modules['mini_erp.pages.inteligencia']
if 'mini_erp.pages.inteligencia.inteligencia_page' in sys.modules:
    del sys.modules['mini_erp.pages.inteligencia.inteligencia_page']
if 'mini_erp.pages.inteligencia.riscos_penais_carlos' in sys.modules:
    del sys.modules['mini_erp.pages.inteligencia.riscos_penais_carlos']

# Importa e verifica o código
from mini_erp.pages.inteligencia.inteligencia_page import inteligencia
import inspect

source = inspect.getsource(inteligencia)
if 'show_development' in source or 'Em desenvolvimento' in source.lower():
    print("❌ ERRO: Código antigo ainda presente!")
    print("Código encontrado:")
    for i, line in enumerate(source.split('\n'), 1):
        if 'show_development' in line or 'Em desenvolvimento' in line.lower():
            print(f"Linha {i}: {line}")
    sys.exit(1)
else:
    print("✅ Código verificado: sem 'Em desenvolvimento'")

# Agora inicia o servidor
from nicegui import ui
import mini_erp.pages

print("\n🚀 Iniciando servidor de teste na porta 8099...")
print("📱 Acesse: http://localhost:8099/inteligencia")

ui.run(
    port=8099,
    host='0.0.0.0',
    reload=False,  # Desabilita reload para garantir código limpo
    show=True,
    title='TAQUES-ERP - Teste Inteligência'
)



