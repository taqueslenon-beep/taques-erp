"""
diagnostico_processo.py - Funções de diagnóstico para processos

Fornece ferramentas para diagnosticar problemas com processos que não aparecem na lista.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from ..core import get_db, get_processes_list, get_clients_list, invalidate_cache


def diagnosticar_processo_nao_aparece(
    titulo_ou_cliente: str,
    cliente_esperado: Optional[str] = None
) -> Dict[str, Any]:
    """
    Diagnostica por que um processo não aparece na lista.
    
    Args:
        titulo_ou_cliente: Título do processo ou nome do cliente para buscar
        cliente_esperado: Nome do cliente esperado (opcional)
    
    Returns:
        Dicionário com diagnóstico completo
    """
    diagnostico = {
        'titulo_buscado': titulo_ou_cliente,
        'cliente_esperado': cliente_esperado,
        'processos_encontrados_no_firestore': [],
        'processos_encontrados_na_lista': [],
        'processos_apos_formatacao': [],
        'problemas_identificados': [],
        'recomendacoes': []
    }
    
    try:
        db = get_db()
        
        # 1. Busca direta no Firestore por título
        print(f"\n[DIAGNÓSTICO] Buscando processos com título/cliente: '{titulo_ou_cliente}'")
        
        # Busca por título (case-insensitive)
        processos_firestore = []
        for doc in db.collection('processes').stream():
            proc_data = doc.to_dict()
            proc_data['_id'] = doc.id
            
            titulo = proc_data.get('title', '').upper()
            clientes = proc_data.get('clients', [])
            
            if titulo_ou_cliente.upper() in titulo:
                processos_firestore.append({
                    'id': doc.id,
                    'titulo': proc_data.get('title'),
                    'clientes': clientes,
                    'status': proc_data.get('status'),
                    'created_at': proc_data.get('created_at'),
                    'updated_at': proc_data.get('updated_at'),
                    'dados_completos': proc_data
                })
        
        diagnostico['processos_encontrados_no_firestore'] = processos_firestore
        
        # 2. Busca na lista de processos (com cache)
        processos_lista = get_processes_list()
        processos_na_lista = []
        
        for proc in processos_lista:
            titulo = (proc.get('title') or '').upper()
            clientes = proc.get('clients', [])
            
            if titulo_ou_cliente.upper() in titulo:
                processos_na_lista.append({
                    'id': proc.get('_id'),
                    'titulo': proc.get('title'),
                    'clientes': clientes,
                    'status': proc.get('status')
                })
        
        diagnostico['processos_encontrados_na_lista'] = processos_na_lista
        
        # 3. Busca por cliente específico
        if cliente_esperado:
            print(f"[DIAGNÓSTICO] Buscando processos do cliente: '{cliente_esperado}'")
            
            processos_cliente = []
            for proc in processos_lista:
                clientes = proc.get('clients', [])
                clientes_str = ' '.join(str(c) for c in clientes).upper()
                
                if cliente_esperado.upper() in clientes_str:
                    processos_cliente.append({
                        'id': proc.get('_id'),
                        'titulo': proc.get('title'),
                        'clientes': clientes,
                        'status': proc.get('status')
                    })
            
            diagnostico['processos_do_cliente'] = processos_cliente
        
        # 4. Identifica problemas
        problemas = []
        
        # Problema 1: Processo no Firestore mas não na lista
        ids_firestore = {p['id'] for p in processos_firestore}
        ids_lista = {p['id'] for p in processos_na_lista}
        ids_so_firestore = ids_firestore - ids_lista
        
        if ids_so_firestore:
            problemas.append({
                'tipo': 'CACHE_DESATUALIZADO',
                'descricao': f'Processo(s) existe(m) no Firestore mas não aparecem na lista (cache desatualizado)',
                'ids_afetados': list(ids_so_firestore),
                'solucao': 'Invalidar cache e recarregar lista'
            })
        
        # Problema 2: Processo sem clientes
        for proc in processos_firestore:
            clientes = proc.get('clientes', [])
            if not clientes or (isinstance(clientes, list) and len(clientes) == 0):
                problemas.append({
                    'tipo': 'SEM_CLIENTES',
                    'descricao': f"Processo '{proc.get('titulo')}' não tem clientes vinculados",
                    'id': proc['id'],
                    'solucao': 'Verificar se campo "clients" foi salvo corretamente'
                })
        
        # Problema 3: Processo com clientes mas cliente não encontrado
        if cliente_esperado:
            clientes_existentes = {c.get('_id') for c in get_clients_list()}
            clientes_nomes = {get_display_name(c) for c in get_clients_list()}
            
            for proc in processos_firestore:
                clientes = proc.get('clientes', [])
                if clientes:
                    for cliente_id in clientes:
                        if isinstance(cliente_id, str):
                            if cliente_id not in clientes_existentes:
                                problemas.append({
                                    'tipo': 'CLIENTE_NAO_ENCONTRADO',
                                    'descricao': f"Cliente ID '{cliente_id}' referenciado no processo mas não encontrado",
                                    'id_processo': proc['id'],
                                    'id_cliente': cliente_id,
                                    'solucao': 'Verificar se cliente existe ou se ID está correto'
                                })
        
        diagnostico['problemas_identificados'] = problemas
        
        # 5. Gera recomendações
        recomendacoes = []
        
        if problemas:
            for problema in problemas:
                if problema['tipo'] == 'CACHE_DESATUALIZADO':
                    recomendacoes.append('Invalidar cache de processos e recarregar página')
                elif problema['tipo'] == 'SEM_CLIENTES':
                    recomendacoes.append('Verificar modal de criação/edição - campo clientes pode não estar sendo salvo')
                elif problema['tipo'] == 'CLIENTE_NAO_ENCONTRADO':
                    recomendacoes.append('Verificar se cliente existe na coleção "clients"')
        else:
            recomendacoes.append('Nenhum problema identificado. Processo deve aparecer na lista.')
        
        diagnostico['recomendacoes'] = recomendacoes
        
        # 6. Imprime resumo
        print(f"\n{'='*60}")
        print(f"RESUMO DO DIAGNÓSTICO")
        print(f"{'='*60}")
        print(f"Título/Cliente buscado: '{titulo_ou_cliente}'")
        print(f"Processos encontrados no Firestore: {len(processos_firestore)}")
        print(f"Processos encontrados na lista: {len(processos_na_lista)}")
        print(f"Problemas identificados: {len(problemas)}")
        
        if processos_firestore:
            print(f"\nProcessos no Firestore:")
            for proc in processos_firestore:
                print(f"  - ID: {proc['id']}")
                print(f"    Título: {proc.get('titulo')}")
                print(f"    Clientes: {proc.get('clientes')}")
                print(f"    Status: {proc.get('status')}")
        
        if problemas:
            print(f"\nProblemas encontrados:")
            for prob in problemas:
                print(f"  - [{prob['tipo']}] {prob['descricao']}")
                print(f"    Solução: {prob['solucao']}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        diagnostico['erro'] = str(e)
        import traceback
        diagnostico['traceback'] = traceback.format_exc()
        print(f"[ERRO] Falha no diagnóstico: {e}")
        traceback.print_exc()
    
    return diagnostico


def diagnosticar_processo_por_id(process_id: str) -> Dict[str, Any]:
    """
    Diagnostica um processo específico pelo ID.
    
    Args:
        process_id: ID do processo no Firestore
    
    Returns:
        Dicionário com diagnóstico completo
    """
    diagnostico = {
        'process_id': process_id,
        'existe_no_firestore': False,
        'existe_na_lista': False,
        'dados_firestore': None,
        'dados_lista': None,
        'diferencas': [],
        'problemas': []
    }
    
    try:
        db = get_db()
        
        # Busca no Firestore
        doc = db.collection('processes').document(process_id).get()
        if doc.exists:
            diagnostico['existe_no_firestore'] = True
            diagnostico['dados_firestore'] = doc.to_dict()
        
        # Busca na lista
        processos = get_processes_list()
        proc_na_lista = next((p for p in processos if p.get('_id') == process_id), None)
        if proc_na_lista:
            diagnostico['existe_na_lista'] = True
            diagnostico['dados_lista'] = proc_na_lista
        
        # Compara dados
        if diagnostico['existe_no_firestore'] and not diagnostico['existe_na_lista']:
            diagnostico['problemas'].append('Processo existe no Firestore mas não na lista (cache desatualizado)')
        
        if not diagnostico['existe_no_firestore']:
            diagnostico['problemas'].append('Processo não existe no Firestore')
        
    except Exception as e:
        diagnostico['erro'] = str(e)
    
    return diagnostico


def forcar_invalidacao_cache_e_recarregar():
    """
    Força invalidação do cache e recarrega processos.
    Útil para resolver problemas de cache desatualizado.
    """
    print("[DIAGNÓSTICO] Invalidando cache de processos...")
    invalidate_cache('processes')
    invalidate_cache('clients')  # Também invalida clientes para garantir
    print("[DIAGNÓSTICO] Cache invalidado. Recarregue a página para ver mudanças.")


def verificar_processo_salvo_recentemente(minutos: int = 5) -> List[Dict[str, Any]]:
    """
    Busca processos salvos recentemente (últimos N minutos).
    
    Args:
        minutos: Quantos minutos atrás buscar (padrão: 5)
    
    Returns:
        Lista de processos salvos recentemente
    """
    processos_recentes = []
    
    try:
        db = get_db()
        agora = datetime.now()
        
        for doc in db.collection('processes').stream():
            proc_data = doc.to_dict()
            updated_at = proc_data.get('updated_at')
            
            if updated_at:
                # Converte timestamp para datetime se necessário
                if hasattr(updated_at, 'seconds'):
                    from datetime import timedelta
                    updated_dt = datetime.fromtimestamp(updated_at.seconds)
                    diferenca = (agora - updated_dt).total_seconds() / 60
                    
                    if diferenca <= minutos:
                        processos_recentes.append({
                            'id': doc.id,
                            'titulo': proc_data.get('title'),
                            'clientes': proc_data.get('clients', []),
                            'minutos_atras': round(diferenca, 1),
                            'dados': proc_data
                        })
        
        processos_recentes.sort(key=lambda x: x['minutos_atras'])
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar processos recentes: {e}")
    
    return processos_recentes


# Import necessário
from ..core import get_display_name



