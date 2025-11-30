#!/usr/bin/env python3
"""
Script para corrigir nomes de partes contrárias nos processos.

PROBLEMA IDENTIFICADO:
Os processos estão salvando nomes completos das partes contrárias ao invés de usar
a regra centralizada de nome_exibicao. Isso causa inconsistências na exibição.

SOLUÇÃO:
1. Busca todos os processos no Firestore
2. Para cada processo, verifica os campos 'opposing_parties' e 'clients'
3. Substitui nomes completos pelos nomes de exibição corretos usando get_display_name()
4. Atualiza os documentos no Firestore

Uso:
    python3 scripts/fix_opposing_party_names.py [--dry-run] [--verbose]
    
Opções:
    --dry-run: Apenas simula as mudanças sem salvar no Firestore
    --verbose: Exibe detalhes de cada processo processado
"""

import sys
import os
import argparse
from typing import Dict, Any, List, Tuple

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db
from mini_erp.core import get_clients_list, get_opposing_parties_list, get_display_name
from google.cloud.firestore import SERVER_TIMESTAMP


def find_person_by_name(full_name: str, clients: List[Dict], opposing: List[Dict]) -> Tuple[str, str]:
    """
    Busca uma pessoa pelo nome completo e retorna o nome de exibição.
    
    Faz busca inteligente considerando variações de nome.
    
    Args:
        full_name: Nome completo a buscar
        clients: Lista de clientes
        opposing: Lista de outros envolvidos
        
    Returns:
        Tupla (nome_exibicao, tipo_pessoa) ou (nome_original, 'not_found')
    """
    def normalize_name(name: str) -> str:
        """Normaliza nome para comparação (remove parênteses, espaços extras, etc)"""
        import re
        # Remove conteúdo entre parênteses
        name = re.sub(r'\s*\([^)]*\)\s*', '', name)
        # Remove espaços extras
        name = ' '.join(name.split())
        return name.strip()
    
    full_name_normalized = normalize_name(full_name)
    
    # Busca em clientes
    for client in clients:
        client_full_name = client.get('full_name') or client.get('name', '')
        client_normalized = normalize_name(client_full_name)
        
        # Busca exata primeiro
        if client_full_name == full_name:
            return get_display_name(client), 'client'
        # Busca normalizada
        elif client_normalized == full_name_normalized:
            return get_display_name(client), 'client'
    
    # Busca em outros envolvidos
    for op in opposing:
        op_full_name = op.get('full_name') or op.get('name', '')
        op_normalized = normalize_name(op_full_name)
        
        # Busca exata primeiro
        if op_full_name == full_name:
            return get_display_name(op), 'opposing_party'
        # Busca normalizada
        elif op_normalized == full_name_normalized:
            return get_display_name(op), 'opposing_party'
    
    # Não encontrou - retorna nome original
    return full_name, 'not_found'


def process_name_list(names: List[str], clients: List[Dict], opposing: List[Dict], verbose: bool = False) -> Tuple[List[str], List[Dict]]:
    """
    Processa uma lista de nomes e converte para nomes de exibição.
    
    Args:
        names: Lista de nomes completos
        clients: Lista de clientes
        opposing: Lista de outros envolvidos
        verbose: Se deve exibir detalhes
        
    Returns:
        Tupla (lista_nomes_exibicao, lista_mudancas)
    """
    display_names = []
    changes = []
    
    for name in names:
        if not name:
            continue
            
        display_name, person_type = find_person_by_name(name, clients, opposing)
        
        if display_name != name:
            changes.append({
                'original': name,
                'display_name': display_name,
                'person_type': person_type
            })
            if verbose:
                print(f"    🔄 '{name}' → '{display_name}' ({person_type})")
        
        display_names.append(display_name)
    
    return display_names, changes


def fix_process_names(process_id: str, process_data: Dict[str, Any], clients: List[Dict], opposing: List[Dict], dry_run: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """
    Corrige os nomes em um processo específico.
    
    Args:
        process_id: ID do processo
        process_data: Dados do processo
        clients: Lista de clientes
        opposing: Lista de outros envolvidos
        dry_run: Se True, apenas simula
        verbose: Se deve exibir detalhes
        
    Returns:
        Dicionário com estatísticas da correção
    """
    stats = {
        'process_id': process_id,
        'title': process_data.get('title', 'Sem título'),
        'changes_made': False,
        'opposing_changes': [],
        'client_changes': [],
        'errors': []
    }
    
    try:
        updates = {}
        
        # Processa opposing_parties
        opposing_parties = process_data.get('opposing_parties', [])
        if opposing_parties:
            new_opposing, opposing_changes = process_name_list(opposing_parties, clients, opposing, verbose)
            if opposing_changes:
                updates['opposing_parties'] = new_opposing
                stats['opposing_changes'] = opposing_changes
                stats['changes_made'] = True
        
        # Processa clients
        process_clients = process_data.get('clients', [])
        if process_clients:
            new_clients, client_changes = process_name_list(process_clients, clients, opposing, verbose)
            if client_changes:
                updates['clients'] = new_clients
                stats['client_changes'] = client_changes
                stats['changes_made'] = True
        
        # Aplica mudanças se não for dry-run
        if updates and not dry_run:
            updates['updated_at'] = SERVER_TIMESTAMP
            db = get_db()
            db.collection('processes').document(process_id).update(updates)
            
        return stats
        
    except Exception as e:
        stats['errors'].append(str(e))
        return stats


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Corrige nomes de partes contrárias nos processos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python3 scripts/fix_opposing_party_names.py --dry-run --verbose
  python3 scripts/fix_opposing_party_names.py
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Apenas simula as mudanças sem salvar no Firestore'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true', 
        help='Exibe detalhes de cada processo processado'
    )
    
    args = parser.parse_args()
    
    print("🚀 Iniciando correção de nomes de partes contrárias nos processos")
    print(f"Modo: {'SIMULAÇÃO' if args.dry_run else 'EXECUÇÃO'}")
    
    if not args.dry_run:
        print("\n⚠️  Executando modificações no Firestore...")
    
    try:
        # Carrega dados de pessoas
        print("\n📋 Carregando dados de pessoas...")
        clients = get_clients_list()
        opposing = get_opposing_parties_list()
        print(f"  • {len(clients)} clientes carregados")
        print(f"  • {len(opposing)} outros envolvidos carregados")
        
        # Busca todos os processos
        print("\n📋 Carregando processos...")
        db = get_db()
        processes_docs = list(db.collection('processes').stream())
        print(f"  • {len(processes_docs)} processos encontrados")
        
        # Estatísticas globais
        total_processes = len(processes_docs)
        processes_with_changes = 0
        total_opposing_changes = 0
        total_client_changes = 0
        total_errors = 0
        all_changes = []
        
        # Processa cada processo
        print(f"\n🔧 Processando processos...")
        for doc in processes_docs:
            process_data = doc.to_dict()
            process_id = doc.id
            
            if args.verbose:
                print(f"\n  📄 Processo: {process_data.get('title', 'Sem título')} (ID: {process_id})")
            
            stats = fix_process_names(process_id, process_data, clients, opposing, args.dry_run, args.verbose)
            
            if stats['changes_made']:
                processes_with_changes += 1
                total_opposing_changes += len(stats['opposing_changes'])
                total_client_changes += len(stats['client_changes'])
                all_changes.append(stats)
                
                if not args.verbose:
                    print(f"  ✅ {stats['title']}: {len(stats['opposing_changes'])} partes contrárias + {len(stats['client_changes'])} clientes corrigidos")
            
            if stats['errors']:
                total_errors += len(stats['errors'])
                print(f"  ❌ Erro em {stats['title']}: {', '.join(stats['errors'])}")
        
        # Relatório final
        print(f"\n{'='*60}")
        print(f"📊 RELATÓRIO FINAL {'(SIMULAÇÃO)' if args.dry_run else '(EXECUTADO)'}")
        print(f"{'='*60}")
        print(f"Total de processos analisados: {total_processes}")
        print(f"Processos com mudanças: {processes_with_changes}")
        print(f"Total de partes contrárias corrigidas: {total_opposing_changes}")
        print(f"Total de clientes corrigidos: {total_client_changes}")
        
        if total_errors > 0:
            print(f"❌ Erros encontrados: {total_errors}")
        
        # Detalhes das mudanças mais comuns
        if all_changes:
            print(f"\n📋 Exemplos de correções realizadas:")
            change_examples = {}
            for process_stats in all_changes[:5]:  # Mostra apenas os primeiros 5
                for change in process_stats['opposing_changes'] + process_stats['client_changes']:
                    original = change['original']
                    display = change['display_name']
                    if original != display:
                        change_examples[f"{original} → {display}"] = change['person_type']
            
            for change_text, person_type in list(change_examples.items())[:10]:
                print(f"  • {change_text} ({person_type})")
        
        print(f"\n{'✅ Processamento concluído com sucesso!' if total_errors == 0 else '⚠️ Processamento concluído com erros.'}")
        
        if args.dry_run and processes_with_changes > 0:
            print("\n💡 Para executar as mudanças, rode o script sem --dry-run")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
