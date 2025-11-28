#!/usr/bin/env python3
"""
Script para renumerar todos os casos após mudança no CASE_TYPE_PREFIX.

Este script deve ser executado uma única vez após a alteração do prefixo
de 'Futuro' de 3 para 2 em models.py.

Uso:
    python renumber_cases_script.py
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mini_erp.pages.casos.database import renumber_all_cases
from mini_erp.core import get_cases_list
from mini_erp.pages.casos.business_logic import get_case_type

def main():
    print("=" * 60)
    print("RENUMERAÇÃO DE CASOS - ATUALIZAÇÃO DE PREFIXOS")
    print("=" * 60)
    print()
    
    # Mostrar estatísticas antes
    cases = get_cases_list()
    antigos = [c for c in cases if get_case_type(c) == 'Antigo']
    novos = [c for c in cases if get_case_type(c) == 'Novo']
    futuros = [c for c in cases if get_case_type(c) == 'Futuro']
    
    print(f"📊 Estatísticas ANTES da renumeração:")
    print(f"   - CASOS ANTIGOS: {len(antigos)} casos")
    print(f"   - CASOS NOVOS: {len(novos)} casos")
    print(f"   - CASOS FUTUROS: {len(futuros)} casos")
    print()
    
    # Executar renumeração
    print("🔄 Iniciando renumeração de todos os casos...")
    print()
    renumber_all_cases()
    print()
    
    # Mostrar estatísticas depois
    cases = get_cases_list()
    antigos_after = [c for c in cases if get_case_type(c) == 'Antigo']
    novos_after = [c for c in cases if get_case_type(c) == 'Novo']
    futuros_after = [c for c in cases if get_case_type(c) == 'Futuro']
    
    print(f"📊 Estatísticas DEPOIS da renumeração:")
    print(f"   - CASOS ANTIGOS: {len(antigos_after)} casos (prefixo 1.X)")
    print(f"   - CASOS NOVOS: {len(novos_after)} casos (prefixo 2.X)")
    print(f"   - CASOS FUTUROS: {len(futuros_after)} casos (prefixo 2.X)")
    print()
    
    print("=" * 60)
    print("✅ RENUMERAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("Próximos passos:")
    print("1. Verifique a interface web em http://localhost:8081/casos")
    print("2. Confirme que CASOS FUTUROS agora usam prefixo 2.X")
    print("3. Teste a criação de novos casos de cada tipo")
    print()

if __name__ == '__main__':
    main()
