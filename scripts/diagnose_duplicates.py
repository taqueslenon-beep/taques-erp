#!/usr/bin/env python3
"""
Script de diagnóstico de duplicatas de casos.

Uso:
    python scripts/diagnose_duplicates.py          # Apenas análise
    python scripts/diagnose_duplicates.py --fix    # Corrige duplicatas
"""

import sys
import os

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Importa diretamente sem passar pelo __init__.py que carrega módulos de UI
# Isso evita problemas de import circular
import importlib

# Carrega duplicate_detection como módulo standalone
duplicate_detection_path = os.path.join(root_dir, 'mini_erp', 'pages', 'casos', 'duplicate_detection.py')
spec = importlib.util.spec_from_file_location("duplicate_detection", duplicate_detection_path)
duplicate_detection = importlib.util.module_from_spec(spec)

# Precisamos adicionar os módulos necessários ao sys.modules para imports relativos funcionarem
import mini_erp
import mini_erp.core
import mini_erp.pages
import mini_erp.pages.casos

sys.modules['mini_erp'] = mini_erp
sys.modules['mini_erp.core'] = mini_erp.core
sys.modules['mini_erp.pages'] = type(sys)('mini_erp.pages')  # Módulo dummy
sys.modules['mini_erp.pages.casos'] = type(sys)('mini_erp.pages.casos')  # Módulo dummy

spec.loader.exec_module(duplicate_detection)

find_duplicate_cases = duplicate_detection.find_duplicate_cases
deduplicate_cases = duplicate_detection.deduplicate_cases


def main():
    """Executa diagnóstico e opcionalmente corrige duplicatas."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnóstico de duplicatas de casos')
    parser.add_argument('--fix', action='store_true', help='Corrige duplicatas encontradas')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Apenas simula correções (padrão)')
    args = parser.parse_args()
    
    print("="*70)
    print("DIAGNÓSTICO DE DUPLICATAS DE CASOS")
    print("="*70)
    print()
    
    # Encontra duplicatas
    print("🔍 Buscando duplicatas...")
    duplicates = find_duplicate_cases()
    stats = duplicates['stats']
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Total de casos no banco: {stats['total_cases']}")
    print(f"   Grupos de duplicatas encontrados: {stats['total_duplicate_groups']}")
    print(f"   Total de casos duplicados: {stats['total_duplicate_cases']}")
    print(f"   Casos únicos após dedup: {stats['unique_cases_after_dedup']}")
    
    if stats['total_duplicate_cases'] == 0:
        print("\n✅ Nenhuma duplicata encontrada! Sistema está íntegro.")
        return 0
    
    print("\n" + "="*70)
    print("DETALHES DAS DUPLICATAS")
    print("="*70)
    
    # Mostra duplicatas por slug
    if duplicates['by_slug']:
        print("\n🔴 DUPLICATAS POR SLUG (mais crítico):")
        for slug, group in duplicates['by_slug'].items():
            print(f"\n   Slug: {slug}")
            for case in group:
                print(f"      - ID: {case.get('_firestore_id')} | Título: {case.get('title', 'Sem título')}")
    
    # Mostra duplicatas por título
    if duplicates['by_title']:
        print("\n🟡 DUPLICATAS POR TÍTULO:")
        for title, group in list(duplicates['by_title'].items())[:10]:  # Limita a 10
            print(f"\n   Título: {title}")
            for case in group:
                print(f"      - ID: {case.get('_firestore_id')} | Slug: {case.get('slug', 'Sem slug')}")
        if len(duplicates['by_title']) > 10:
            print(f"\n   ... e mais {len(duplicates['by_title']) - 10} grupo(s)")
    
    # Mostra duplicatas por nome+ano
    if duplicates['by_name_year']:
        print("\n🟠 DUPLICATAS POR NOME+ANO:")
        for key, group in list(duplicates['by_name_year'].items())[:10]:  # Limita a 10
            name, year = key.split('|')
            print(f"\n   Nome: {name} | Ano: {year}")
            for case in group:
                print(f"      - ID: {case.get('_firestore_id')} | Slug: {case.get('slug', 'Sem slug')}")
        if len(duplicates['by_name_year']) > 10:
            print(f"\n   ... e mais {len(duplicates['by_name_year']) - 10} grupo(s)")
    
    # Opção de correção
    if args.fix:
        print("\n" + "="*70)
        print("CORREÇÃO DE DUPLICATAS")
        print("="*70)
        
        dry_run = not args.dry_run if hasattr(args, 'dry_run') else True
        
        if dry_run:
            print("\n⚠️  MODO DRY-RUN: Nenhuma alteração será feita")
            print("   Execute com --fix --no-dry-run para aplicar correções")
        else:
            print("\n⚠️  ATENÇÃO: Esta operação irá modificar o banco de dados!")
            response = input("   Deseja continuar? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                print("   Operação cancelada.")
                return 1
        
        result = deduplicate_cases(dry_run=dry_run)
        
        if result['success']:
            print("\n✅ Operação concluída com sucesso!")
            print(f"   Ações realizadas: {len(result['actions'])}")
            return 0
        else:
            print("\n❌ Erro durante a correção")
            return 1
    else:
        print("\n" + "="*70)
        print("PRÓXIMOS PASSOS")
        print("="*70)
        print("\nPara corrigir duplicatas, execute:")
        print("   python scripts/diagnose_duplicates.py --fix --dry-run    # Simular")
        print("   python scripts/diagnose_duplicates.py --fix --no-dry-run # Aplicar")
        return 0


if __name__ == '__main__':
    sys.exit(main())

