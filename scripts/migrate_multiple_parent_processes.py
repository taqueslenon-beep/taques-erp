"""
Script de migração: Múltiplos Processos Pai

OBJETIVO:
- Converter campo "parent_id" (string) para "parent_ids" (array)
- Garantir compatibilidade com processos existentes
- Criar backup antes da migração

USO:
    python scripts/migrate_multiple_parent_processes.py [--dry-run] [--backup]

OPÇÕES:
    --dry-run: Apenas simula a migração sem fazer alterações
    --backup: Cria backup completo antes de migrar
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db


def create_backup() -> str:
    """
    Cria backup completo de todos os processos antes da migração.
    
    Returns:
        Caminho do arquivo de backup criado
    """
    try:
        db = get_db()
        processes_ref = db.collection('processes')
        all_processes = []
        
        for doc in processes_ref.stream():
            process_data = doc.to_dict()
            process_data['_id'] = doc.id
            all_processes.append(process_data)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_processes_before_migration_{timestamp}.json'
        backup_path = os.path.join(os.path.dirname(__file__), '..', backup_file)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(all_processes, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Backup criado: {backup_path}")
        print(f"   Total de processos: {len(all_processes)}")
        return backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        import traceback
        traceback.print_exc()
        return None


def migrate_processes(dry_run: bool = False) -> Dict[str, Any]:
    """
    Migra processos de parent_id (string) para parent_ids (array).
    
    Args:
        dry_run: Se True, apenas simula sem fazer alterações
    
    Returns:
        Estatísticas da migração
    """
    stats = {
        'total_processed': 0,
        'migrated': 0,
        'already_migrated': 0,
        'no_parent': 0,
        'errors': []
    }
    
    try:
        db = get_db()
        processes_ref = db.collection('processes')
        
        print("\n🔍 Buscando processos para migração...")
        
        for doc in processes_ref.stream():
            stats['total_processed'] += 1
            process_id = doc.id
            process_data = doc.to_dict()
            
            # Verifica se já tem parent_ids (já migrado)
            if 'parent_ids' in process_data and isinstance(process_data.get('parent_ids'), list):
                stats['already_migrated'] += 1
                continue
            
            # Verifica se tem parent_id antigo
            old_parent_id = process_data.get('parent_id')
            
            if not old_parent_id:
                # Processo sem pai - apenas garante que parent_ids está vazio
                if not dry_run:
                    doc.reference.update({
                        'parent_ids': [],
                        'parent_id': None  # Mantém campo antigo para compatibilidade
                    })
                stats['no_parent'] += 1
                print(f"  ✓ Processo {process_id}: sem pai (parent_ids = [])")
            else:
                # Migra parent_id para parent_ids
                new_parent_ids = [old_parent_id] if old_parent_id else []
                
                if not dry_run:
                    doc.reference.update({
                        'parent_ids': new_parent_ids,
                        'parent_id': old_parent_id  # Mantém campo antigo para compatibilidade
                    })
                
                stats['migrated'] += 1
                print(f"  ✓ Processo {process_id}: migrado {old_parent_id} → {new_parent_ids}")
        
        return stats
    
    except Exception as e:
        error_msg = f"Erro durante migração: {e}"
        stats['errors'].append(error_msg)
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return stats


def validate_migration() -> bool:
    """
    Valida se a migração foi bem-sucedida.
    
    Returns:
        True se migração está correta, False caso contrário
    """
    try:
        db = get_db()
        processes_ref = db.collection('processes')
        
        issues = []
        
        for doc in processes_ref.stream():
            process_data = doc.to_dict()
            process_id = doc.id
            
            # Verifica se todos os processos têm parent_ids
            if 'parent_ids' not in process_data:
                issues.append(f"Processo {process_id}: falta campo 'parent_ids'")
            
            # Verifica se parent_ids é uma lista
            parent_ids = process_data.get('parent_ids')
            if parent_ids is not None and not isinstance(parent_ids, list):
                issues.append(f"Processo {process_id}: 'parent_ids' não é uma lista (tipo: {type(parent_ids)})")
            
            # Verifica consistência: se tem parent_id antigo, deve estar em parent_ids
            old_parent_id = process_data.get('parent_id')
            if old_parent_id and old_parent_id not in (parent_ids or []):
                issues.append(f"Processo {process_id}: parent_id '{old_parent_id}' não está em parent_ids")
        
        if issues:
            print(f"\n⚠️  Validação encontrou {len(issues)} problema(s):")
            for issue in issues[:10]:  # Mostra apenas os 10 primeiros
                print(f"  - {issue}")
            if len(issues) > 10:
                print(f"  ... e mais {len(issues) - 10} problema(s)")
            return False
        else:
            print("\n✅ Validação: todos os processos estão corretos!")
            return True
    
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal do script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migra processos de parent_id para parent_ids')
    parser.add_argument('--dry-run', action='store_true', help='Apenas simula sem fazer alterações')
    parser.add_argument('--backup', action='store_true', help='Cria backup antes de migrar')
    args = parser.parse_args()
    
    print("=" * 60)
    print("MIGRAÇÃO: Múltiplos Processos Pai")
    print("=" * 60)
    
    if args.dry_run:
        print("\n⚠️  MODO DRY-RUN: Nenhuma alteração será feita\n")
    
    # Criar backup se solicitado
    if args.backup and not args.dry_run:
        backup_path = create_backup()
        if not backup_path:
            print("\n❌ Falha ao criar backup. Abortando migração.")
            return
    
    # Executar migração
    print("\n🚀 Iniciando migração...")
    stats = migrate_processes(dry_run=args.dry_run)
    
    # Mostrar estatísticas
    print("\n" + "=" * 60)
    print("ESTATÍSTICAS DA MIGRAÇÃO")
    print("=" * 60)
    print(f"Total processado: {stats['total_processed']}")
    print(f"Migrados: {stats['migrated']}")
    print(f"Já migrados: {stats['already_migrated']}")
    print(f"Sem pai: {stats['no_parent']}")
    if stats['errors']:
        print(f"Erros: {len(stats['errors'])}")
        for error in stats['errors']:
            print(f"  - {error}")
    
    # Validar migração
    if not args.dry_run:
        print("\n🔍 Validando migração...")
        is_valid = validate_migration()
        
        if is_valid:
            print("\n✅ Migração concluída com sucesso!")
        else:
            print("\n⚠️  Migração concluída, mas foram encontrados problemas.")
            print("   Revise os erros acima e considere restaurar o backup se necessário.")
    else:
        print("\n✅ Simulação concluída. Execute sem --dry-run para aplicar as mudanças.")


if __name__ == '__main__':
    main()








