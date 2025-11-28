# -*- coding: utf-8 -*-
"""
TAQUES ERP - Pacote Principal
=============================

Este módulo permite iniciar o servidor de duas formas:

1. python -m mini_erp.main  (recomendado)
2. python mini_erp/__init__.py
3. cd mini_erp && python __init__.py

O servidor será iniciado na porta 8081 (ou próxima disponível).
"""

import os
import sys

# Garante que o diretório raiz esteja no path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Quando executado diretamente (python __init__.py), inicia o servidor
if __name__ in {"__main__", "__mp_main__"}:
    # Importa e executa o main
    from mini_erp.main import start_server_safe
    start_server_safe()
