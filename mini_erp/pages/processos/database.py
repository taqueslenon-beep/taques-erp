"""
database.py - Operações de banco de dados para o módulo de Processos.

Este módulo contém:
- Funções wrapper para operações CRUD via core
- Sincronização de processos com casos
- Acesso a listas de dados
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Imports do core para operações de banco
from ...core import (
    get_processes_list,
    get_cases_list,
    get_clients_list,
    get_opposing_parties_list,
    save_data,
    sync_processes_cases,
    data,
    save_process as save_process_to_firestore,
    invalidate_cache,
)
from ...firebase_config import get_db


# =============================================================================
# FUNÇÕES DE ACESSO A DADOS
# =============================================================================

def get_all_processes() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os processos.
    
    Returns:
        Lista de dicionários com dados dos processos
    """
    return get_processes_list()


def get_all_cases() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os casos.
    
    Returns:
        Lista de dicionários com dados dos casos
    """
    return get_cases_list()


def get_all_clients() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os clientes.
    
    Returns:
        Lista de dicionários com dados dos clientes
    """
    return get_clients_list()


def get_all_opposing_parties() -> List[Dict[str, Any]]:
    """
    Retorna lista de todas as partes contrárias.
    
    Returns:
        Lista de dicionários com dados das partes contrárias
    """
    return get_opposing_parties_list()


def get_process_by_index(idx: int) -> Optional[Dict[str, Any]]:
    """
    Retorna um processo pelo índice.
    
    Args:
        idx: Índice do processo na lista
    
    Returns:
        Dicionário do processo ou None se índice inválido
    """
    processes = get_processes_list()
    if 0 <= idx < len(processes):
        return processes[idx]
    return None


# =============================================================================
# FUNÇÕES DE CRIAÇÃO E ATUALIZAÇÃO
# =============================================================================

def save_process(process_data: Dict[str, Any], edit_index: Optional[int] = None) -> str:
    """
    Salva ou atualiza um processo.
    
    Args:
        process_data: Dados do processo a salvar
        edit_index: Índice para edição (None para novo processo)
    
    Returns:
        Mensagem de sucesso
    """
    # Obtém o doc_id (_id) do processo
    # Prioridade: _id do process_data > _id do processo existente > None (novo processo)
    doc_id = process_data.get('_id')
    
    if not doc_id and edit_index is not None:
        processes = get_processes_list()
        if 0 <= edit_index < len(processes):
            existing_process = processes[edit_index]
            doc_id = existing_process.get('_id')
    
    if doc_id:
        message = 'Processo atualizado!'
    else:
        message = f'Processo "{process_data.get("title", "")}" cadastrado!'
    
    # Salva no Firestore usando a função do core
    # A função save_process_to_firestore gerencia a persistência corretamente
    save_process_to_firestore(process_data, doc_id=doc_id, sync=True)
    
    return message


def update_process_field(idx: int, field: str, value: Any) -> bool:
    """
    Atualiza um campo específico de um processo.
    
    Args:
        idx: Índice do processo
        field: Nome do campo a atualizar
        value: Novo valor
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        processes[idx][field] = value
        data['processes'] = processes
        save_data()
        return True
    
    return False


def delete_process(doc_id: str) -> Optional[str]:
    """
    Exclui um processo do Firestore pelo doc_id.
    
    Args:
        doc_id: ID do documento do processo no Firestore (campo _id)
    
    Returns:
        Título do processo excluído ou None se falhou
    """
    # Importação local para evitar conflito de nomes
    from ...core import delete_process as core_delete_process
    
    if not doc_id:
        return None
    
    # Busca o processo para retornar o título
    processes = get_processes_list()
    process_title = None
    for proc in processes:
        if proc.get('_id') == doc_id:
            process_title = proc.get('title', 'Processo')
            break
    
    # Deleta do Firestore usando a função do core
    try:
        core_delete_process(doc_id, sync=True)
        return process_title
    except Exception as e:
        print(f"Erro ao excluir processo {doc_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def restore_process(doc_id: str) -> bool:
    """
    Restaura um processo que foi marcado como deletado (soft delete).
    
    Args:
        doc_id: ID do documento do processo no Firestore
    
    Returns:
        True se restaurado com sucesso, False caso contrário
    """
    if not doc_id:
        return False
    
    try:
        db = get_db()
        doc_ref = db.collection('processes').document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"Processo {doc_id} não encontrado")
            return False
        
        # Remove campos de soft delete
        doc_ref.update({
            'isDeleted': False,
            'deletedAt': None,
            'deletedReason': None,
            'originalProcessId': None
        })
        
        # Invalida cache
        invalidate_cache('processes')
        
        print(f"Processo {doc_id} restaurado com sucesso")
        return True
    
    except Exception as e:
        print(f"Erro ao restaurar processo {doc_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# FUNÇÕES DE ACESSO A PROCESSOS
# =============================================================================

def update_process_access(idx: int, access_type: str, field: str, value: bool) -> bool:
    """
    Atualiza campo de acesso de um processo.
    
    Args:
        idx: Índice do processo
        access_type: Tipo de acesso ('lawyer', 'technicians', 'client')
        field: Campo ('requested' ou 'granted')
        value: Novo valor
    
    Returns:
        True se atualizado com sucesso
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        field_name = f'access_{access_type}_{field}'
        processes[idx][field_name] = value
        
        # Se concedido, automaticamente marca como solicitado
        if field == 'granted' and value:
            processes[idx][f'access_{access_type}_requested'] = True
        
        data['processes'] = processes
        save_data()
        return True
    
    return False


def update_process_access_comment(idx: int, access_type: str, comment: str) -> bool:
    """
    Atualiza comentário de acesso de um processo.
    
    Args:
        idx: Índice do processo
        access_type: Tipo de acesso ('lawyer', 'technicians', 'client')
        comment: Texto do comentário
    
    Returns:
        True se atualizado com sucesso
    """
    processes = get_processes_list()
    
    if 0 <= idx < len(processes):
        field_name = f'access_{access_type}_comment'
        processes[idx][field_name] = comment
        data['processes'] = processes
        save_data()
        return True
    
    return False


# =============================================================================
# FUNÇÕES DE SINCRONIZAÇÃO
# =============================================================================

def sync_all() -> None:
    """
    Sincroniza processos com casos.
    """
    sync_processes_cases()


def save_all() -> None:
    """
    Salva todos os dados.
    """
    save_data()


# =============================================================================
# FUNÇÕES DE OPÇÕES PARA SELECTS
# =============================================================================

def get_client_options() -> List[str]:
    """
    Retorna lista de nomes de clientes para select.
    
    Returns:
        Lista de nomes de clientes
    """
    return [c['name'] for c in get_clients_list()]


def get_opposing_options() -> List[str]:
    """
    Retorna lista de nomes de partes contrárias para select.
    
    Returns:
        Lista de nomes de partes contrárias
    """
    return [op['name'] for op in get_opposing_parties_list()]


def get_case_options() -> List[str]:
    """
    Retorna lista de títulos de casos para select.
    
    Returns:
        Lista de títulos de casos
    """
    return [c['title'] for c in get_cases_list()]


# =============================================================================
# FUNÇÕES DE VERIFICAÇÃO DE INTEGRIDADE
# =============================================================================

def verificar_integridade_processos() -> Dict[str, Any]:
    """
    Verifica integridade dos processos no banco de dados.
    
    Valida se todos os processos aparecem em todas as visualizações,
    identificando processos "fantasmas" que aparecem apenas em filtros específicos.
    
    Returns:
        Dicionário com resultados da verificação:
        - total_processos: int
        - processos_por_status: Dict[str, int]
        - processos_sem_status: List[Dict]
        - integridade_ok: bool
        - erros: List[str]
    """
    try:
        all_processes = get_all_processes()
        
        # Agrupar por status
        processos_por_status = {}
        processos_sem_status = []
        
        for proc in all_processes:
            status = proc.get('status') or ''
            if not status or (isinstance(status, str) and not status.strip()):
                processos_sem_status.append(proc)
                status = '(sem status)'
            
            if status not in processos_por_status:
                processos_por_status[status] = []
            processos_por_status[status].append(proc)
        
        # Verificar integridade: soma de processos por status deve ser igual ao total
        total_por_status = sum(len(procs) for procs in processos_por_status.values())
        total_geral = len(all_processes)
        
        # Buscar processo específico "RECURSO ESPECIAL"
        recurso_especial = None
        for proc in all_processes:
            if 'RECURSO ESPECIAL' in (proc.get('title') or '').upper():
                recurso_especial = proc
                break
        
        erros = []
        if total_por_status != total_geral:
            erros.append(f"Discrepância na soma de processos por status ({total_por_status} vs {total_geral})")
        
        if processos_sem_status:
            erros.append(f"{len(processos_sem_status)} processos sem status definido")
        
        if recurso_especial:
            status_recurso = recurso_especial.get('status') or ''
            if not status_recurso or (isinstance(status_recurso, str) and not status_recurso.strip()):
                erros.append("Processo 'RECURSO ESPECIAL' não tem status definido")
        
        return {
            'total_processos': total_geral,
            'processos_por_status': {k: len(v) for k, v in processos_por_status.items()},
            'processos_sem_status': processos_sem_status,
            'recurso_especial': recurso_especial,
            'integridade_ok': len(erros) == 0,
            'erros': erros
        }
    except Exception as e:
        return {
            'total_processos': 0,
            'processos_por_status': {},
            'processos_sem_status': [],
            'recurso_especial': None,
            'integridade_ok': False,
            'erros': [f"Erro ao verificar integridade: {e}"]
        }


# =============================================================================
# FUNÇÕES DE ACOMPANHAMENTO DE TERCEIROS
# =============================================================================

# Nome da coleção no Firestore
THIRD_PARTY_MONITORING_COLLECTION = 'third_party_monitoring'


def criar_acompanhamento(acompanhamento_data: Dict[str, Any]) -> str:
    """
    Cria um novo acompanhamento de terceiros no Firestore.
    
    Args:
        acompanhamento_data: Dicionário com dados do acompanhamento
            - title: str (obrigatório) - título do acompanhamento
            - link_do_processo: str
            - tipo_de_processo: str
            - data_de_abertura: str
            - parte_ativa: List[str] (obrigatório) - array de IDs/nomes
            - parte_passiva: List[str] (opcional)
            - outros_envolvidos: List[str] (opcional)
            - processos_pais: List[str] (opcional)
            - cases: List[str] (opcional)
            - status: str (padrão: 'ativo')
            - [outros campos das abas adicionais]
    
    Returns:
        ID do documento criado no Firestore
    
    Raises:
        ValueError: Se título não for fornecido
        Exception: Em caso de erro no Firestore
    """
    try:
        print(f"[CRIAR_ACOMPANHAMENTO] Iniciando criação de novo acompanhamento")
        print(f"[CRIAR_ACOMPANHAMENTO] Campos recebidos: {list(acompanhamento_data.keys())}")
        
        # Validação: título é obrigatório
        title_value = acompanhamento_data.get('title') or acompanhamento_data.get('process_title') or acompanhamento_data.get('titulo')
        if not title_value or not str(title_value).strip():
            error_msg = "Título do acompanhamento é obrigatório"
            print(f"[CRIAR_ACOMPANHAMENTO] ❌ {error_msg}")
            raise ValueError(error_msg)
        
        print(f"[CRIAR_ACOMPANHAMENTO] Título: '{title_value}'")
        
        db = get_db()
        
        # Gera ID único se não fornecido
        doc_id = acompanhamento_data.get('id') or str(uuid.uuid4())
        print(f"[CRIAR_ACOMPANHAMENTO] ID gerado: {doc_id}")
        
        # Prepara dados para salvar (usa todos os campos fornecidos)
        doc_data = acompanhamento_data.copy()
        
        # Remove o campo 'id' se existir (não salva como campo, é o ID do documento)
        doc_data.pop('id', None)
        doc_data.pop('_id', None)
        
        # Garante que título está presente (múltiplos campos para compatibilidade)
        if 'title' not in doc_data:
            doc_data['title'] = title_value
        if 'process_title' not in doc_data:
            doc_data['process_title'] = title_value
        
        # Garantir que link está presente (múltiplos campos para compatibilidade)
        link_value = doc_data.get('link_do_processo') or doc_data.get('link', '')
        if link_value:
            doc_data['link_do_processo'] = link_value
            doc_data['link'] = link_value  # Também salvar como 'link'
        
        # Garantir que número está presente
        number_value = doc_data.get('process_number') or doc_data.get('number', '')
        if number_value:
            doc_data['number'] = number_value
            doc_data['process_number'] = number_value  # Compatibilidade
        
        print(f"[CRIAR_ACOMPANHAMENTO] Link a salvar: '{doc_data.get('link')}' ou '{doc_data.get('link_do_processo')}'")
        print(f"[CRIAR_ACOMPANHAMENTO] Número a salvar: '{doc_data.get('number')}' ou '{doc_data.get('process_number')}'")
        
        # Adiciona timestamps
        doc_data['created_at'] = datetime.now().isoformat()
        doc_data['updated_at'] = datetime.now().isoformat()
        
        # Garante que status existe
        if 'status' not in doc_data:
            doc_data['status'] = 'ativo'
        
        print(f"[CRIAR_ACOMPANHAMENTO] Dados finais a salvar:")
        print(f"  - title: {doc_data.get('title')}")
        print(f"  - process_title: {doc_data.get('process_title')}")
        print(f"  - status: {doc_data.get('status')}")
        print(f"  - Total de campos: {len(doc_data)}")
        
        # Salva no Firestore
        doc_ref = db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id)
        doc_ref.set(doc_data)
        
        print(f"[CRIAR_ACOMPANHAMENTO] ✓ Documento salvo no Firestore")
        
        # Verifica se foi salvo corretamente
        doc_after = doc_ref.get()
        if doc_after.exists:
            doc_after_data = doc_after.to_dict()
            title_after = doc_after_data.get('title') or doc_after_data.get('process_title')
            link_after = doc_after_data.get('link') or doc_after_data.get('link_do_processo')
            number_after = doc_after_data.get('number') or doc_after_data.get('process_number')
            print(f"[CRIAR_ACOMPANHAMENTO] Verificação pós-salvamento:")
            print(f"  Título: '{title_after}'")
            print(f"  Link: '{link_after}'")
            print(f"  Número: '{number_after}'")
        else:
            print(f"[CRIAR_ACOMPANHAMENTO] ⚠️  AVISO: Documento não encontrado após salvar!")
        
        # Invalida cache
        invalidate_cache(THIRD_PARTY_MONITORING_COLLECTION)
        
        print(f"[CRIAR_ACOMPANHAMENTO] ✓ Acompanhamento criado com sucesso. ID: {doc_id}")
        return doc_id
    
    except ValueError:
        # Re-raise validações
        raise
    except Exception as e:
        print(f"[CRIAR_ACOMPANHAMENTO] ❌ ERRO ao criar acompanhamento: {e}")
        import traceback
        traceback.print_exc()
        raise


def obter_acompanhamentos_por_cliente(client_id: str) -> List[Dict[str, Any]]:
    """
    Obtém todos os acompanhamentos de terceiros vinculados a um cliente.
    
    Args:
        client_id: ID do cliente
    
    Returns:
        Lista de dicionários com dados dos acompanhamentos
    """
    try:
        db = get_db()
        
        # Busca acompanhamentos do cliente
        query = db.collection(THIRD_PARTY_MONITORING_COLLECTION).where('client_id', '==', client_id)
        docs = query.stream()
        
        acompanhamentos = []
        for doc in docs:
            item = doc.to_dict()
            item['_id'] = doc.id
            item['id'] = doc.id  # Mantém compatibilidade
            acompanhamentos.append(item)
        
        # Ordena por data de criação (mais recente primeiro)
        acompanhamentos.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return acompanhamentos
    
    except Exception as e:
        print(f"Erro ao obter acompanhamentos por cliente: {e}")
        import traceback
        traceback.print_exc()
        return []


def obter_todos_acompanhamentos() -> List[Dict[str, Any]]:
    """
    Obtém todos os acompanhamentos de terceiros cadastrados.
    
    Returns:
        Lista de dicionários com dados dos acompanhamentos
    """
    try:
        db = get_db()
        
        docs = db.collection(THIRD_PARTY_MONITORING_COLLECTION).stream()
        
        acompanhamentos = []
        for doc in docs:
            item = doc.to_dict()
            item['_id'] = doc.id
            item['id'] = doc.id  # Mantém compatibilidade
            acompanhamentos.append(item)
        
        return acompanhamentos
    
    except Exception as e:
        print(f"Erro ao obter todos os acompanhamentos: {e}")
        import traceback
        traceback.print_exc()
        return []


def contar_acompanhamentos_ativos(client_id: Optional[str] = None) -> int:
    """
    Conta o total de acompanhamentos ativos.
    
    Args:
        client_id: Opcional. Se fornecido, conta apenas do cliente específico
    
    Returns:
        Número de acompanhamentos ativos
    """
    try:
        db = get_db()
        
        # Constrói query
        query = db.collection(THIRD_PARTY_MONITORING_COLLECTION).where('status', '==', 'ativo')
        
        if client_id:
            query = query.where('client_id', '==', client_id)
        
        # Conta documentos (usa stream e conta manualmente - Firestore não tem count direto eficiente)
        docs = query.stream()
        count = sum(1 for _ in docs)
        
        return count
    
    except Exception as e:
        print(f"Erro ao contar acompanhamentos ativos: {e}")
        import traceback
        traceback.print_exc()
        return 0


def contar_todos_acompanhamentos(client_id: Optional[str] = None) -> int:
    """
    Conta o total de TODOS os acompanhamentos de terceiros (não apenas ativos).
    
    IMPORTANTE: Esta função conta TODOS os acompanhamentos, independente do status.
    Use esta função para exibição no card do painel.
    
    Args:
        client_id: Opcional. Se fornecido, conta apenas do cliente específico
    
    Returns:
        Número total de acompanhamentos de terceiros
    """
    try:
        db = get_db()
        
        # Constrói query (sem filtro de status)
        if client_id:
            query = db.collection(THIRD_PARTY_MONITORING_COLLECTION).where('client_id', '==', client_id)
        else:
            query = db.collection(THIRD_PARTY_MONITORING_COLLECTION)
        
        # Conta documentos (usa stream e conta manualmente - Firestore não tem count direto eficiente)
        docs = query.stream()
        count = sum(1 for _ in docs)
        
        print(f"[CONTAR ACOMPANHAMENTOS] Total encontrado: {count}")
        return count
    
    except Exception as e:
        print(f"[CONTAR ACOMPANHAMENTOS] Erro ao contar acompanhamentos: {e}")
        import traceback
        traceback.print_exc()
        return 0


def obter_acompanhamento_por_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém um acompanhamento específico pelo ID.
    
    Args:
        doc_id: ID do documento no Firestore
    
    Returns:
        Dicionário com dados do acompanhamento ou None se não encontrado
    """
    try:
        db = get_db()
        doc = db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id).get()
        
        if doc.exists:
            item = doc.to_dict()
            item['_id'] = doc.id
            item['id'] = doc.id  # Mantém compatibilidade
            return item
        
        return None
    
    except Exception as e:
        print(f"Erro ao obter acompanhamento por ID: {e}")
        import traceback
        traceback.print_exc()
        return None


def atualizar_acompanhamento(doc_id: str, updates: Dict[str, Any]) -> bool:
    """
    Atualiza um acompanhamento de terceiros existente.
    
    Args:
        doc_id: ID do documento no Firestore
        updates: Dicionário com campos a atualizar
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Iniciando atualização do documento {doc_id}")
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Campos a atualizar: {list(updates.keys())}")
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Título nos dados: {updates.get('title') or updates.get('process_title') or updates.get('titulo')}")
        
        db = get_db()
        
        # Validação: título deve existir
        title_value = updates.get('title') or updates.get('process_title') or updates.get('titulo')
        if not title_value or not str(title_value).strip():
            print(f"[ATUALIZAR_ACOMPANHAMENTO] ⚠️  AVISO: Título está vazio ou None!")
            print(f"[ATUALIZAR_ACOMPANHAMENTO] Campos disponíveis: {list(updates.keys())}")
        
        # Adiciona timestamp de atualização
        updates['updated_at'] = datetime.now().isoformat()
        
        # Garantir que campos críticos estejam presentes
        # Link do processo (múltiplos campos para compatibilidade)
        link_value = updates.get('link_do_processo') or updates.get('link', '')
        if link_value:
            updates['link_do_processo'] = link_value
            updates['link'] = link_value  # Também salvar como 'link' para compatibilidade
        
        # Número do processo
        number_value = updates.get('process_number') or updates.get('number', '')
        if number_value:
            updates['number'] = number_value
            updates['process_number'] = number_value  # Compatibilidade
        
        # Remove campos que não devem ser atualizados diretamente
        updates.pop('_id', None)
        updates.pop('id', None)
        updates.pop('created_at', None)
        
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Link a salvar: '{updates.get('link')}' ou '{updates.get('link_do_processo')}'")
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Número a salvar: '{updates.get('number')}' ou '{updates.get('process_number')}'")
        
        # Verifica se documento existe antes de atualizar
        doc_ref = db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"[ATUALIZAR_ACOMPANHAMENTO] ❌ Documento {doc_id} não existe na coleção {THIRD_PARTY_MONITORING_COLLECTION}")
            return False
        
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Documento encontrado. Atualizando...")
        
        # Atualiza no Firestore
        doc_ref.update(updates)
        
        print(f"[ATUALIZAR_ACOMPANHAMENTO] ✓ Documento atualizado com sucesso")
        
        # Verifica se atualização foi persistida
        doc_after = doc_ref.get()
        if doc_after.exists:
            doc_data = doc_after.to_dict()
            title_after = doc_data.get('title') or doc_data.get('process_title') or doc_data.get('titulo')
            print(f"[ATUALIZAR_ACOMPANHAMENTO] Verificação: Título após salvar: '{title_after}'")
        
        # Invalida cache
        invalidate_cache(THIRD_PARTY_MONITORING_COLLECTION)
        
        return True
    
    except Exception as e:
        print(f"[ATUALIZAR_ACOMPANHAMENTO] ❌ ERRO ao atualizar acompanhamento: {e}")
        import traceback
        traceback.print_exc()
        return False


def deletar_acompanhamento(doc_id: str) -> bool:
    """
    Exclui um acompanhamento de terceiros.
    
    Args:
        doc_id: ID do documento no Firestore
    
    Returns:
        True se excluído com sucesso, False caso contrário
    """
    try:
        db = get_db()
        db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id).delete()
        
        # Invalida cache
        invalidate_cache(THIRD_PARTY_MONITORING_COLLECTION)
        
        return True
    
    except Exception as e:
        print(f"Erro ao deletar acompanhamento: {e}")
        import traceback
        traceback.print_exc()
        return False


