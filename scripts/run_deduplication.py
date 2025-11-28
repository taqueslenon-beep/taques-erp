#!/usr/bin/env python3
"""
Script para limpar casos duplicados no Firestore.
Executa UMA ÚNICA VEZ para limpar o banco.

USO:
    python scripts/run_deduplication.py          # Modo dry-run (apenas mostra)
    python scripts/run_deduplication.py --apply  # Aplica as correções
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.pages.casos.duplicate_detection import deduplicate_cases, find_duplicate_cases


def main():
    print("=" * 60)
    print("🔍 FERRAMENTA DE DEDUPLICAÇÃO DE CASOS")
    print("=" * 60)
    
    # Verifica argumentos
    apply_changes = "--apply" in sys.argv
    
    if not apply_changes:
        print("\n⚠️  MODO DRY-RUN (apenas análise)")
        print("   Para aplicar correções, execute: python scripts/run_deduplication.py --apply\n")
    else:
        print("\n⚡ MODO APLICAÇÃO - Correções serão aplicadas!\n")
        confirm = input("Tem certeza? Digite 'SIM' para confirmar: ")
        if confirm != "SIM":
            print("❌ Operação cancelada.")
            return
    
    # Primeiro mostra estatísticas
    print("\n📊 Analisando banco de dados...")
    duplicates = find_duplicate_cases()
    stats = duplicates['stats']
    
    print(f"\n   Total de casos: {stats['total_cases']}")
    print(f"   Grupos de duplicatas: {stats['total_duplicate_groups']}")
    print(f"   Casos duplicados: {stats['total_duplicate_cases']}")
    print(f"   Casos únicos após dedup: {stats['unique_cases_after_dedup']}")
    
    if stats['total_duplicate_cases'] == 0:
        print("\n✅ Nenhuma duplicata encontrada! Banco está limpo.")
        return
    
    # Mostra detalhes
    print("\n" + "-" * 60)
    
    if duplicates['by_slug']:
        print("📋 DUPLICATAS POR SLUG:")
        for slug, cases in list(duplicates['by_slug'].items())[:10]:
            print(f"\n   Slug: {slug}")
            for c in cases:
                print(f"      - ID: {c.get('_firestore_id', 'N/A')} | Título: {c.get('title', 'Sem título')}")
    
    if duplicates['by_title']:
        print("\n" + "-" * 60)
        print("📋 DUPLICATAS POR TÍTULO (mesmos IDs no Firestore):")
        count = 0
        for title, cases in duplicates['by_title'].items():
            # Verifica se são realmente duplicatas (IDs diferentes, mesmo título)
            unique_ids = set(c.get('_firestore_id') for c in cases)
            if len(unique_ids) > 1:
                count += 1
                if count <= 10:
                    print(f"\n   Título: {title}")
                    for c in cases:
                        print(f"      - ID: {c.get('_firestore_id', 'N/A')} | Slug: {c.get('slug', 'N/A')}")
        if count > 10:
            print(f"\n   ... e mais {count - 10} grupos de duplicatas por título")
    
    # Executa deduplicação
    print("\n" + "=" * 60)
    result = deduplicate_cases(dry_run=not apply_changes)
    
    if apply_changes and result['success']:
        print("\n✅ DEDUPLICAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   Ações executadas: {len(result['actions'])}")
    elif not apply_changes:
        print("\n📝 Análise concluída. Execute com --apply para corrigir.")


if __name__ == "__main__":
    main()

