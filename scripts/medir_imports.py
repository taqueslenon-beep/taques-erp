#!/usr/bin/env python3
"""Mede tempo de import dos módulos principais"""

import time

def medir(nome, func):
    inicio = time.time()
    func()
    fim = time.time()
    print(f"{nome}: {(fim-inicio)*1000:.0f}ms")

print("=" * 50)
print("MEDIÇÃO DE TEMPO DE IMPORTS")
print("=" * 50)

medir("firebase_config", lambda: __import__('mini_erp.firebase_config'))
medir("core", lambda: __import__('mini_erp.core'))
medir("auth", lambda: __import__('mini_erp.auth'))
medir("painel", lambda: __import__('mini_erp.pages.painel'))
medir("processos", lambda: __import__('mini_erp.pages.processos'))
medir("casos", lambda: __import__('mini_erp.pages.casos'))
medir("pessoas", lambda: __import__('mini_erp.pages.pessoas'))
medir("prazos", lambda: __import__('mini_erp.pages.prazos'))

print("=" * 50)










