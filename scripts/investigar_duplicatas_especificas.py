#!/usr/bin/env python3
"""
Script para investigar duplicatas específicas: "Polícia" e "Instituto"
"""

import sys
import os
from collections import Counter

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.core import get_processes_list, get_opposing_parties_list, get_display_name, invalidate_cache


def investigar_duplicatas():
    """Investiga duplicatas específicas."""
    print("\n" + "="*60)
    print("INVESTIGAÇÃO: DUPLICATAS ESPECÍFICAS")
    print("="*60)
    
    # Força atualização do cache
    invalidate_cache('processes')
    invalidate_cache('opposing_parties')
    
    processos = get_processes_list()
    opposing_parties = get_opposing_parties_list()
    
    print(f"\n✓ Total de processos: {len(processos)}")
    print(f"✓ Total de partes contrárias cadastradas: {len(opposing_parties)}")
    
    # Coletar todas as partes contrárias dos processos
    print("\n" + "-"*60)
    print("1. TODAS AS OCORRÊNCIAS DE 'POLÍCIA' NOS PROCESSOS")
    print("-"*60)
    
    ocorrencias_policia = []
    for proc in processos:
        for opposing in proc.get('opposing_parties', []):
            if opposing and 'polícia' in opposing.lower():
                ocorrencias_policia.append({
                    'nome_salvo': opposing,
                    'processo': proc.get('title', 'Sem título'),
                    'processo_id': proc.get('_id', 'Sem ID')
                })
    
    print(f"\nTotal de ocorrências com 'polícia': {len(ocorrencias_policia)}")
    
    # Agrupar por nome exato
    nomes_policia = Counter([o['nome_salvo'] for o in ocorrencias_policia])
    print("\nNomes diferentes encontrados:")
    for nome, count in nomes_policia.most_common():
        print(f"  - '{nome}': {count} processos")
    
    # Verificar correspondências na lista de opposing_parties
    print("\n" + "-"*60)
    print("2. PARTES CONTRÁRIAS CADASTRADAS COM 'POLÍCIA'")
    print("-"*60)
    
    partes_policia = []
    for opposing in opposing_parties:
        full_name = (opposing.get('full_name') or '').strip()
        name = (opposing.get('name') or '').strip()
        nome_exibicao = (opposing.get('nome_exibicao') or '').strip()
        display_name = (opposing.get('display_name') or '').strip()
        nickname = (opposing.get('nickname') or '').strip()
        
        if ('polícia' in full_name.lower() or 
            'polícia' in name.lower() or 
            'polícia' in nome_exibicao.lower() or 
            'polícia' in display_name.lower() or
            'polícia' in nickname.lower()):
            partes_policia.append({
                '_id': opposing.get('_id', 'Sem ID'),
                'full_name': full_name,
                'name': name,
                'nome_exibicao': nome_exibicao,
                'display_name': display_name,
                'nickname': nickname,
                'display_name_final': get_display_name(opposing)
            })
    
    print(f"\nTotal de partes contrárias cadastradas com 'polícia': {len(partes_policia)}")
    for parte in partes_policia:
        print(f"\n  ID: {parte['_id']}")
        print(f"  full_name: '{parte['full_name']}'")
        print(f"  name: '{parte['name']}'")
        print(f"  nome_exibicao: '{parte['nome_exibicao']}'")
        print(f"  display_name: '{parte['display_name']}'")
        print(f"  nickname: '{parte['nickname']}'")
        print(f"  → Nome de exibição final: '{parte['display_name_final']}'")
    
    # Investigar "Instituto"
    print("\n" + "-"*60)
    print("3. TODAS AS OCORRÊNCIAS DE 'INSTITUTO' NOS PROCESSOS")
    print("-"*60)
    
    ocorrencias_instituto = []
    for proc in processos:
        for opposing in proc.get('opposing_parties', []):
            if opposing and 'instituto' in opposing.lower():
                ocorrencias_instituto.append({
                    'nome_salvo': opposing,
                    'processo': proc.get('title', 'Sem título'),
                    'processo_id': proc.get('_id', 'Sem ID')
                })
    
    print(f"\nTotal de ocorrências com 'instituto': {len(ocorrencias_instituto)}")
    
    # Agrupar por nome exato
    nomes_instituto = Counter([o['nome_salvo'] for o in ocorrencias_instituto])
    print("\nNomes diferentes encontrados:")
    for nome, count in nomes_instituto.most_common():
        print(f"  - '{nome}': {count} processos")
    
    # Verificar correspondências na lista de opposing_parties
    print("\n" + "-"*60)
    print("4. PARTES CONTRÁRIAS CADASTRADAS COM 'INSTITUTO'")
    print("-"*60)
    
    partes_instituto = []
    for opposing in opposing_parties:
        full_name = (opposing.get('full_name') or '').strip()
        name = (opposing.get('name') or '').strip()
        nome_exibicao = (opposing.get('nome_exibicao') or '').strip()
        display_name = (opposing.get('display_name') or '').strip()
        nickname = (opposing.get('nickname') or '').strip()
        
        if ('instituto' in full_name.lower() or 
            'instituto' in name.lower() or 
            'instituto' in nome_exibicao.lower() or 
            'instituto' in display_name.lower() or
            'instituto' in nickname.lower()):
            partes_instituto.append({
                '_id': opposing.get('_id', 'Sem ID'),
                'full_name': full_name,
                'name': name,
                'nome_exibicao': nome_exibicao,
                'display_name': display_name,
                'nickname': nickname,
                'display_name_final': get_display_name(opposing)
            })
    
    print(f"\nTotal de partes contrárias cadastradas com 'instituto': {len(partes_instituto)}")
    for parte in partes_instituto:
        print(f"\n  ID: {parte['_id']}")
        print(f"  full_name: '{parte['full_name']}'")
        print(f"  name: '{parte['name']}'")
        print(f"  nome_exibicao: '{parte['nome_exibicao']}'")
        print(f"  display_name: '{parte['display_name']}'")
        print(f"  nickname: '{parte['nickname']}'")
        print(f"  → Nome de exibição final: '{parte['display_name_final']}'")
    
    # Testar normalização
    print("\n" + "-"*60)
    print("5. TESTE DE NORMALIZAÇÃO")
    print("-"*60)
    
    def normalizar_nome(opposing_name: str) -> str:
        """Normaliza nome usando a mesma lógica do data_service."""
        if not opposing_name or not opposing_name.strip():
            return "Sem identificação"
        
        opposing_name_clean = opposing_name.strip()
        
        for opposing in opposing_parties:
            full_name = (opposing.get('full_name') or '').strip()
            name = (opposing.get('name') or '').strip()
            nome_exibicao = (opposing.get('nome_exibicao') or '').strip()
            display_name = (opposing.get('display_name') or '').strip()
            nickname = (opposing.get('nickname') or '').strip()
            
            if (opposing_name_clean.lower() == full_name.lower() or 
                opposing_name_clean.lower() == name.lower() or 
                opposing_name_clean.lower() == nome_exibicao.lower() or 
                opposing_name_clean.lower() == display_name.lower() or
                opposing_name_clean.lower() == nickname.lower()):
                display = get_display_name(opposing)
                return display if display else opposing_name_clean
        
        return opposing_name_clean
    
    print("\nTestando normalização para 'Polícia':")
    for nome in set([o['nome_salvo'] for o in ocorrencias_policia]):
        normalizado = normalizar_nome(nome)
        print(f"  '{nome}' → '{normalizado}'")
    
    print("\nTestando normalização para 'Instituto':")
    for nome in set([o['nome_salvo'] for o in ocorrencias_instituto]):
        normalizado = normalizar_nome(nome)
        print(f"  '{nome}' → '{normalizado}'")
    
    print("\n" + "="*60)
    print("INVESTIGAÇÃO CONCLUÍDA")
    print("="*60 + "\n")


if __name__ == '__main__':
    try:
        investigar_duplicatas()
    except Exception as e:
        print(f"\n❌ Erro durante investigação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)















