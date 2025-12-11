#!/usr/bin/env python3
"""
Script para diagnosticar problemas de duplicatas na contagem de processos por parte contrária.

Verifica:
1. Se há nomes duplicados (mesma entidade com nomes diferentes)
2. Se os nomes estão sendo normalizados corretamente
3. Compara contagem antes e depois da normalização
"""

import sys
import os
from collections import Counter

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.core import get_cases_list, get_processes_list, get_opposing_parties_list, get_display_name, invalidate_cache


def diagnosticar_parte_contraria():
    """Diagnostica problemas de duplicatas em partes contrárias."""
    print("\n" + "="*60)
    print("DIAGNÓSTICO: PROCESSOS POR PARTE CONTRÁRIA")
    print("="*60)
    
    # Força atualização do cache
    invalidate_cache('processes')
    invalidate_cache('opposing_parties')
    
    processos = get_processes_list()
    opposing_parties = get_opposing_parties_list()
    
    print(f"\n✓ Total de processos: {len(processos)}")
    print(f"✓ Total de partes contrárias cadastradas: {len(opposing_parties)}")
    
    # Coletar todos os nomes de partes contrárias dos processos
    print("\n" + "-"*60)
    print("1. NOMES SALVOS NOS PROCESSOS (ANTES DA NORMALIZAÇÃO)")
    print("-"*60)
    
    nomes_originais = []
    for proc in processos:
        for opposing in proc.get('opposing_parties', []):
            if opposing:
                nomes_originais.append(opposing.strip())
    
    contagem_original = Counter(nomes_originais)
    print(f"\nTotal de ocorrências (sem normalização): {len(nomes_originais)}")
    print(f"Partes contrárias únicas (sem normalização): {len(contagem_original)}")
    
    print("\nTop 10 partes contrárias (sem normalização):")
    for nome, count in contagem_original.most_common(10):
        print(f"  - {nome}: {count} processos")
    
    # Normalizar usando a mesma lógica do data_service
    print("\n" + "-"*60)
    print("2. NOMES NORMALIZADOS (APÓS NORMALIZAÇÃO)")
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
    
    nomes_normalizados = []
    mapeamento = {}
    for nome_original in nomes_originais:
        nome_norm = normalizar_nome(nome_original)
        nomes_normalizados.append(nome_norm)
        if nome_original != nome_norm:
            if nome_norm not in mapeamento:
                mapeamento[nome_norm] = []
            mapeamento[nome_norm].append(nome_original)
    
    contagem_normalizada = Counter(nomes_normalizados)
    print(f"\nTotal de ocorrências (com normalização): {len(nomes_normalizados)}")
    print(f"Partes contrárias únicas (com normalização): {len(contagem_normalizada)}")
    
    reducao = len(contagem_original) - len(contagem_normalizada)
    if reducao > 0:
        print(f"\n✓ Redução de {reducao} duplicatas após normalização!")
    
    print("\nTop 10 partes contrárias (com normalização):")
    for nome, count in contagem_normalizada.most_common(10):
        print(f"  - {nome}: {count} processos")
        if nome in mapeamento and len(mapeamento[nome]) > 1:
            print(f"    (agrupou: {', '.join(set(mapeamento[nome]))})")
    
    # Verificar duplicatas
    print("\n" + "-"*60)
    print("3. ANÁLISE DE DUPLICATAS")
    print("-"*60)
    
    if mapeamento:
        print(f"\n✓ Encontradas {len(mapeamento)} partes contrárias que foram normalizadas:")
        for nome_norm, nomes_orig in sorted(mapeamento.items(), key=lambda x: len(x[1]), reverse=True):
            if len(set(nomes_orig)) > 1:
                print(f"\n  {nome_norm}:")
                print(f"    Agrupou {len(set(nomes_orig))} nomes diferentes:")
                for nome_orig in sorted(set(nomes_orig)):
                    count = nomes_orig.count(nome_orig)
                    print(f"      - '{nome_orig}' ({count} ocorrências)")
    else:
        print("\n✓ Nenhuma normalização necessária (todos os nomes já estão corretos)")
    
    # Verificar partes contrárias sem correspondência
    print("\n" + "-"*60)
    print("4. PARTES CONTRÁRIAS SEM CORRESPONDÊNCIA")
    print("-"*60)
    
    nomes_sem_correspondencia = []
    for nome_original in set(nomes_originais):
        nome_norm = normalizar_nome(nome_original)
        # Se normalizou para o mesmo nome, pode não ter encontrado correspondência
        if nome_original == nome_norm:
            # Verifica se existe na lista de opposing_parties
            encontrado = False
            for opposing in opposing_parties:
                full_name = (opposing.get('full_name') or '').strip()
                name = (opposing.get('name') or '').strip()
                nome_exibicao = (opposing.get('nome_exibicao') or '').strip()
                display_name = (opposing.get('display_name') or '').strip()
                nickname = (opposing.get('nickname') or '').strip()
                
                if (nome_original.lower() == full_name.lower() or 
                    nome_original.lower() == name.lower() or 
                    nome_original.lower() == nome_exibicao.lower() or 
                    nome_original.lower() == display_name.lower() or
                    nome_original.lower() == nickname.lower()):
                    encontrado = True
                    break
            
            if not encontrado:
                nomes_sem_correspondencia.append(nome_original)
    
    if nomes_sem_correspondencia:
        print(f"\n⚠️  {len(nomes_sem_correspondencia)} nomes sem correspondência na lista de partes contrárias:")
        for nome in sorted(set(nomes_sem_correspondencia)):
            count = nomes_originais.count(nome)
            print(f"  - '{nome}' ({count} ocorrências)")
        print("\n  Esses nomes podem precisar ser cadastrados ou corrigidos nos processos.")
    else:
        print("\n✓ Todas as partes contrárias têm correspondência na lista cadastrada")
    
    print("\n" + "="*60)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("="*60 + "\n")


if __name__ == '__main__':
    try:
        diagnosticar_parte_contraria()
    except Exception as e:
        print(f"\n❌ Erro durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


