#!/usr/bin/env python3
"""
Script de backfill para popular o campo 'nome_exibicao' em registros existentes.

Este script:
1. Busca todos os clientes e outros envolvidos no Firestore
2. Para cada pessoa sem 'nome_exibicao', popula com base na prioridade:
   - display_name (se existir)
   - full_name (se existir)  
   - name (compatibilidade)
   - "Sem nome" (fallback)
3. Atualiza os documentos no Firestore
4. Gera relatório de mudanças

Uso:
    python scripts/backfill_display_names.py [--dry-run] [--verbose]
    
Opções:
    --dry-run: Apenas simula as mudanças sem salvar no Firestore
    --verbose: Exibe detalhes de cada registro processado
"""

import sys
import os
import argparse
from typing import Dict, Any, List

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db
from google.cloud.firestore import SERVER_TIMESTAMP


def get_display_name_priority(item: Dict[str, Any]) -> str:
    """
    Determina o nome de exibição seguindo a prioridade definida.
    
    Prioridade:
        1. display_name (se existir e não vazio)
        2. full_name (se existir e não vazio)
        3. name (compatibilidade, se existir e não vazio)
        4. "Sem nome" (fallback)
    
    Args:
        item: Dicionário com dados da pessoa
        
    Returns:
        Nome de exibição determinado pela prioridade
    """
    # Prioridade 1: display_name
    display_name = item.get('display_name', '').strip()
    if display_name:
        return display_name
    
    # Prioridade 2: full_name
    full_name = item.get('full_name', '').strip()
    if full_name:
        return full_name
    
    # Prioridade 3: name (compatibilidade)
    name = item.get('name', '').strip()
    if name:
        return name
    
    # Fallback
    return "Sem nome"


def process_collection(collection_name: str, dry_run: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """
    Processa uma coleção para popular nome_exibicao.
    
    Args:
        collection_name: Nome da coleção ('clients' ou 'opposing_parties')
        dry_run: Se True, apenas simula sem salvar
        verbose: Se True, exibe detalhes de cada registro
        
    Returns:
        Dicionário com estatísticas do processamento
    """
    db = get_db()
    collection_ref = db.collection(collection_name)
    
    # Busca todos os documentos
    docs = list(collection_ref.stream())
    
    stats = {
        'total': len(docs),
        'updated': 0,
        'already_had': 0,
        'errors': 0,
        'changes': []
    }
    
    print(f"\n📋 Processando coleção '{collection_name}' ({stats['total']} registros)")
    
    for doc in docs:
        try:
            data = doc.to_dict()
            doc_id = doc.id
            
            # Verifica se já tem nome_exibicao preenchido
            current_nome_exibicao = data.get('nome_exibicao', '').strip()
            
            if current_nome_exibicao:
                # Já tem nome_exibicao
                stats['already_had'] += 1
                if verbose:
                    print(f"  ✅ {doc_id}: já tem nome_exibicao = '{current_nome_exibicao}'")
                continue
            
            # Determina nome_exibicao baseado na prioridade
            new_nome_exibicao = get_display_name_priority(data)
            
            # Registra mudança
            change_info = {
                'doc_id': doc_id,
                'collection': collection_name,
                'old_nome_exibicao': current_nome_exibicao,
                'new_nome_exibicao': new_nome_exibicao,
                'source_field': None
            }
            
            # Identifica campo fonte
            if data.get('display_name', '').strip() == new_nome_exibicao:
                change_info['source_field'] = 'display_name'
            elif data.get('full_name', '').strip() == new_nome_exibicao:
                change_info['source_field'] = 'full_name'
            elif data.get('name', '').strip() == new_nome_exibicao:
                change_info['source_field'] = 'name'
            else:
                change_info['source_field'] = 'fallback'
            
            stats['changes'].append(change_info)
            
            if verbose:
                print(f"  🔄 {doc_id}: '{current_nome_exibicao}' → '{new_nome_exibicao}' (fonte: {change_info['source_field']})")
            
            # Atualiza documento (se não for dry-run)
            if not dry_run:
                update_data = {
                    'nome_exibicao': new_nome_exibicao,
                    'updated_at': SERVER_TIMESTAMP
                }
                
                # Também sincroniza display_name para compatibilidade
                if not data.get('display_name', '').strip():
                    update_data['display_name'] = new_nome_exibicao
                
                collection_ref.document(doc_id).update(update_data)
            
            stats['updated'] += 1
            
        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Erro ao processar {doc.id}: {e}")
    
    return stats


def generate_report(clients_stats: Dict[str, Any], opposing_stats: Dict[str, Any], dry_run: bool):
    """
    Gera relatório final do processamento.
    
    Args:
        clients_stats: Estatísticas da coleção clients
        opposing_stats: Estatísticas da coleção opposing_parties
        dry_run: Se foi execução de teste
    """
    total_records = clients_stats['total'] + opposing_stats['total']
    total_updated = clients_stats['updated'] + opposing_stats['updated']
    total_already_had = clients_stats['already_had'] + opposing_stats['already_had']
    total_errors = clients_stats['errors'] + opposing_stats['errors']
    
    print(f"\n{'='*60}")
    print(f"📊 RELATÓRIO FINAL {'(SIMULAÇÃO)' if dry_run else '(EXECUTADO)'}")
    print(f"{'='*60}")
    print(f"Total de registros processados: {total_records}")
    print(f"  • Clientes: {clients_stats['total']}")
    print(f"  • Outros envolvidos: {opposing_stats['total']}")
    print()
    print(f"Registros atualizados: {total_updated}")
    print(f"  • Clientes: {clients_stats['updated']}")
    print(f"  • Outros envolvidos: {opposing_stats['updated']}")
    print()
    print(f"Registros que já tinham nome_exibicao: {total_already_had}")
    print(f"  • Clientes: {clients_stats['already_had']}")
    print(f"  • Outros envolvidos: {opposing_stats['already_had']}")
    print()
    if total_errors > 0:
        print(f"❌ Erros encontrados: {total_errors}")
        print(f"  • Clientes: {clients_stats['errors']}")
        print(f"  • Outros envolvidos: {opposing_stats['errors']}")
        print()
    
    # Detalhes das mudanças por campo fonte
    all_changes = clients_stats['changes'] + opposing_stats['changes']
    if all_changes:
        print("📋 Origem dos nomes de exibição:")
        source_counts = {}
        for change in all_changes:
            source = change['source_field']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items()):
            source_label = {
                'display_name': 'Campo display_name existente',
                'full_name': 'Campo full_name',
                'name': 'Campo name (legado)',
                'fallback': 'Fallback "Sem nome"'
            }.get(source, source)
            print(f"  • {source_label}: {count} registros")
    
    print(f"\n{'✅ Processamento concluído com sucesso!' if total_errors == 0 else '⚠️ Processamento concluído com erros.'}")
    
    if dry_run:
        print("\n💡 Para executar as mudanças, rode o script sem --dry-run")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Backfill do campo nome_exibicao para pessoas existentes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/backfill_display_names.py --dry-run --verbose
  python scripts/backfill_display_names.py
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
        help='Exibe detalhes de cada registro processado'
    )
    
    args = parser.parse_args()
    
    print("🚀 Iniciando backfill de nome_exibicao para pessoas")
    print(f"Modo: {'SIMULAÇÃO' if args.dry_run else 'EXECUÇÃO'}")
    
    if not args.dry_run:
        print("\n⚠️  Executando modificações no Firestore...")
        # Removido input interativo para permitir execução automatizada
    
    try:
        # Processa clientes
        clients_stats = process_collection('clients', args.dry_run, args.verbose)
        
        # Processa outros envolvidos
        opposing_stats = process_collection('opposing_parties', args.dry_run, args.verbose)
        
        # Gera relatório
        generate_report(clients_stats, opposing_stats, args.dry_run)
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
