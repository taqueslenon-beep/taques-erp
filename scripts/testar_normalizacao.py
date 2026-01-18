#!/usr/bin/env python3
"""
Script para testar a normalização melhorada
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.core import get_processes_list, get_opposing_parties_list, invalidate_cache
from mini_erp.pages.painel.data_service import PainelDataService

# Força atualização do cache
invalidate_cache('processes')
invalidate_cache('opposing_parties')
invalidate_cache('cases')
invalidate_cache('clients')

processos = get_processes_list()
opposing_parties = get_opposing_parties_list()
cases = get_processes_list()  # Usando processos como fallback
clients = []

# Criar data service
ds = PainelDataService(cases, processos, clients, opposing_parties)

# Testar normalização
testes = [
    'Polícia Militar Ambiental de Canoinhas',
    'Polícia',
    'Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renováveis',
    'IBAMA',
    'MPSC',
    'PMA/SC',
]

print("\n" + "="*60)
print("TESTE DE NORMALIZAÇÃO")
print("="*60)

for nome in testes:
    normalizado = ds._normalize_opposing_name(nome)
    print(f"  '{nome}' → '{normalizado}'")

# Testar contagem
print("\n" + "="*60)
print("CONTAGEM NORMALIZADA")
print("="*60)

resultado = ds.get_processes_by_opposing_party_filtered('todos')
print(f"\nTotal de partes contrárias únicas: {len(resultado)}")
print("\nTop 15:")
for nome, count in resultado[:15]:
    print(f"  - {nome}: {count} processos")























