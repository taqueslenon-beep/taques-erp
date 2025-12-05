"""
database.py - Operações de banco de dados para o módulo de Processos.

Este módulo contém:
- Funções wrapper para operações CRUD via core
- Sincronização de processos com casos
- Acesso a listas de dados
"""

from typing import List, Dict, Any, Optional, Tuple
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
from ...auth import get_current_user
from .password_security import encrypt_password, decrypt_password
from google.cloud.firestore import SERVER_TIMESTAMP


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


def get_processes_with_children() -> List[Dict[str, Any]]:
    """
    Retorna processos agrupados por hierarquia (pai + desdobramentos).
    
    Estrutura de retorno:
    [
        {
            'processo_principal': {id: '123', titulo: 'Processo 1', ...},
            'desdobramentos': [
                {id: '456', titulo: 'Desdobramento 1', ...},
                {id: '789', titulo: 'Desdobramento 2', ...}
            ]
        },
        {
            'processo_principal': {id: '999', titulo: 'Processo 2', ...},
            'desdobramentos': []
        }
    ]
    
    Returns:
        Lista de dicionários com processo principal e seus desdobramentos
    """
    all_processes = get_processes_list()
    
    # Criar mapa de processos por ID para busca rápida
    process_map = {p.get('_id'): p for p in all_processes if p.get('_id')}
    
    # Separar processos principais (sem parent_ids ou parent_ids vazio)
    # e processos filhos (com parent_ids não vazio)
    main_processes = []
    child_processes = []
    
    for proc in all_processes:
        parent_ids = proc.get('parent_ids', [])
        # Compatibilidade: verificar também parent_id (campo antigo)
        if not parent_ids:
            old_parent_id = proc.get('parent_id')
            if old_parent_id:
                parent_ids = [old_parent_id]
        
        # Se não tem parent_ids ou parent_ids está vazio, é processo principal
        if not parent_ids or (isinstance(parent_ids, list) and len(parent_ids) == 0):
            main_processes.append(proc)
        else:
            child_processes.append(proc)
    
    # Agrupar desdobramentos por processo pai
    # Um desdobramento pode ter múltiplos pais, mas vamos agrupar pelo primeiro pai
    children_by_parent = {}
    for child in child_processes:
        parent_ids = child.get('parent_ids', [])
        if not parent_ids:
            old_parent_id = child.get('parent_id')
            if old_parent_id:
                parent_ids = [old_parent_id]
        
        # Agrupa pelo primeiro pai (ou pode ser modificado para agrupar por todos os pais)
        if parent_ids:
            first_parent_id = parent_ids[0]
            if first_parent_id not in children_by_parent:
                children_by_parent[first_parent_id] = []
            children_by_parent[first_parent_id].append(child)
    
    # Construir estrutura hierárquica
    result = []
    for main_proc in main_processes:
        proc_id = main_proc.get('_id')
        desdobramentos = children_by_parent.get(proc_id, [])
        
        result.append({
            'processo_principal': main_proc,
            'desdobramentos': desdobramentos
        })
    
    return result


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


def duplicar_processo(id_processo_original: str) -> Tuple[Optional[str], str]:
    """
    Duplica um processo no Firestore, criando uma cópia com novo ID e timestamps atualizados.
    
    Campos que NÃO são copiados (resetados):
    - _id (ID do documento - gerado automaticamente)
    - id (campo legado - removido)
    - created_at, updated_at, criado_em, atualizado_em (resetados para agora)
    
    Campos que SÃO copiados:
    - Título (com sufixo "[CÓPIA]")
    - Tipo de processo
    - Data de abertura (mantida - é dado importante)
    - Partes envolvidas (clientes, parte contrária, outros envolvidos)
    - Vínculos (casos, processos pais)
    - Status (mantido)
    - Descrições/comentários
    - Todos os outros campos do processo
    
    Args:
        id_processo_original: ID do documento do processo original no Firestore
    
    Returns:
        Tupla (novo_id, mensagem):
        - novo_id: ID do novo processo criado ou None se falhou
        - mensagem: Mensagem de sucesso ou erro
    """
    try:
        db = get_db()
        
        # Buscar processo original
        doc_ref = db.collection('processes').document(id_processo_original)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None, "Processo não encontrado"
        
        dados_original = doc.to_dict()
        
        # Criar cópia dos dados
        dados_copia = dados_original.copy()
        
        # Remover campos que não devem ser duplicados
        campos_nao_copiar = [
            '_id',           # ID do documento (gerado automaticamente)
            'id',            # Campo legado
            'created_at',    # Timestamp de criação
            'updated_at',    # Timestamp de atualização
            'criado_em',    # Timestamp legado
            'atualizado_em' # Timestamp legado
        ]
        
        for campo in campos_nao_copiar:
            dados_copia.pop(campo, None)
        
        # Adicionar sufixo ao título
        titulo_original = dados_copia.get('title', 'Processo')
        # Evita adicionar múltiplos sufixos se já tiver "[CÓPIA]"
        if '[CÓPIA]' not in titulo_original:
            dados_copia['title'] = f"{titulo_original} [CÓPIA]"
        else:
            # Se já tem [CÓPIA], adiciona número sequencial
            dados_copia['title'] = f"{titulo_original} [CÓPIA 2]"
        
        # Atualizar campo de busca
        if 'title' in dados_copia:
            dados_copia['title_searchable'] = dados_copia['title'].lower()
        
        # Adicionar timestamps novos
        agora = datetime.now()
        dados_copia['created_at'] = agora.isoformat()
        dados_copia['updated_at'] = agora.isoformat()
        dados_copia['criado_em'] = agora.isoformat()
        dados_copia['atualizado_em'] = agora.isoformat()
        
        # Resetar status para "Aberto" (opcional - pode manter o status original)
        # Comentado para manter o status original
        # dados_copia['status'] = 'Aberto'
        
        # Salvar usando save_process do core (garante validações e sincronização)
        # Mas precisamos obter o ID depois
        novo_titulo = dados_copia.get('title', '')
        save_process_to_firestore(dados_copia, doc_id=None, sync=True)
        
        # Buscar o ID do novo documento criado
        # Busca pelo título exato (que tem [CÓPIA]) criado recentemente
        novo_id = None
        
        # Busca processos com o título exato criados nos últimos 3 segundos
        query = db.collection('processes').where('title', '==', novo_titulo).stream()
        processos_encontrados = []
        
        for doc in query:
            doc_data = doc.to_dict()
            # Verifica se foi criado recentemente (últimos 3 segundos)
            created_at = doc_data.get('created_at') or doc_data.get('criado_em', '')
            if created_at:
                try:
                    from datetime import datetime as dt
                    # Parse do timestamp
                    if isinstance(created_at, str):
                        # Remove timezone se presente
                        created_at_clean = created_at.replace('Z', '').split('+')[0].split('.')[0]
                        doc_time = dt.fromisoformat(created_at_clean)
                    else:
                        doc_time = created_at
                    
                    # Calcula diferença
                    if hasattr(doc_time, 'tzinfo') and doc_time.tzinfo:
                        doc_time = doc_time.replace(tzinfo=None)
                    time_diff = abs((agora - doc_time).total_seconds())
                    
                    if time_diff < 3:  # Criado nos últimos 3 segundos
                        processos_encontrados.append((doc.id, doc_data, time_diff))
                except Exception as ex:
                    print(f"[DUPLICAR_PROCESSO] Erro ao processar timestamp: {ex}")
                    pass
        
        # Se encontrou processos, pega o mais recente (menor time_diff)
        if processos_encontrados:
            processos_encontrados.sort(key=lambda x: x[2])  # Ordena por time_diff (mais recente primeiro)
            novo_id = processos_encontrados[0][0]
        
        # Se ainda não encontrou, busca qualquer processo com [CÓPIA] no título criado recentemente
        if not novo_id:
            # Busca todos os processos com [CÓPIA] no título
            all_processes = db.collection('processes').stream()
            for doc in all_processes:
                if doc.id == id_processo_original:
                    continue  # Pula o processo original
                
                doc_data = doc.to_dict()
                doc_title = doc_data.get('title', '')
                if '[CÓPIA]' in doc_title:
                    created_at = doc_data.get('created_at') or doc_data.get('criado_em', '')
                    if created_at:
                        try:
                            from datetime import datetime as dt
                            if isinstance(created_at, str):
                                created_at_clean = created_at.replace('Z', '').split('+')[0].split('.')[0]
                                doc_time = dt.fromisoformat(created_at_clean)
                            else:
                                doc_time = created_at
                            
                            if hasattr(doc_time, 'tzinfo') and doc_time.tzinfo:
                                doc_time = doc_time.replace(tzinfo=None)
                            time_diff = abs((agora - doc_time).total_seconds())
                            
                            if time_diff < 5:  # Criado nos últimos 5 segundos
                                novo_id = doc.id
                                break
                        except:
                            pass
        
        # Invalida cache para forçar recarregamento
        invalidate_cache('processes')
        
        print(f"[DUPLICAR_PROCESSO] Processo {id_processo_original} duplicado com sucesso. Novo ID: {novo_id}")
        return novo_id, "Processo duplicado com sucesso!"
    
    except Exception as e:
        error_msg = f"Erro ao duplicar processo: {str(e)}"
        print(f"[DUPLICAR_PROCESSO] ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return None, error_msg


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


def sanitize_for_firestore(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza dados antes de enviar ao Firestore.
    Remove valores None e converte para tipos válidos.
    
    Args:
        data: Dicionário com dados a sanitizar
    
    Returns:
        Dicionário sanitizado sem valores None
    """
    sanitized = {}
    
    for key, value in data.items():
        # Ignora campos com valor None
        if value is None:
            continue
        
        # Listas: garante que são listas válidas e remove None internos
        if isinstance(value, list):
            sanitized_list = [v for v in value if v is not None]
            sanitized[key] = sanitized_list if sanitized_list else []
        
        # Strings: remove espaços extras e converte None para string vazia
        elif isinstance(value, str):
            sanitized[key] = value.strip() if value.strip() else ''
        
        # Dicionários: sanitiza recursivamente
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_firestore(value)
        
        # Booleanos: mantém como está
        elif isinstance(value, bool):
            sanitized[key] = value
        
        # Números: mantém como está
        elif isinstance(value, (int, float)):
            sanitized[key] = value
        
        # Outros tipos: converte para string se possível
        else:
            try:
                sanitized[key] = str(value) if value else ''
            except Exception:
                # Se não conseguir converter, ignora o campo
                continue
    
    return sanitized


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
        if 'title' not in doc_data or not doc_data.get('title'):
            doc_data['title'] = title_value
        if 'process_title' not in doc_data or not doc_data.get('process_title'):
            doc_data['process_title'] = title_value
        
        # Garantir que link está presente (múltiplos campos para compatibilidade)
        link_value = doc_data.get('link_do_processo') or doc_data.get('link', '') or ''
        doc_data['link_do_processo'] = link_value
        doc_data['link'] = link_value  # Também salvar como 'link'
        
        # Garantir que número está presente
        number_value = doc_data.get('process_number') or doc_data.get('number', '') or ''
        doc_data['number'] = number_value
        doc_data['process_number'] = number_value  # Compatibilidade
        
        # Garantir que listas não sejam None
        if 'parte_ativa' not in doc_data or doc_data.get('parte_ativa') is None:
            doc_data['parte_ativa'] = []
        if 'parte_passiva' not in doc_data or doc_data.get('parte_passiva') is None:
            doc_data['parte_passiva'] = []
        if 'outros_envolvidos' not in doc_data or doc_data.get('outros_envolvidos') is None:
            doc_data['outros_envolvidos'] = []
        if 'processos_pais' not in doc_data or doc_data.get('processos_pais') is None:
            doc_data['processos_pais'] = []
        if 'cases' not in doc_data or doc_data.get('cases') is None:
            doc_data['cases'] = []
        if 'scenarios' not in doc_data or doc_data.get('scenarios') is None:
            doc_data['scenarios'] = []
        if 'protocols' not in doc_data or doc_data.get('protocols') is None:
            doc_data['protocols'] = []
        
        # Adiciona timestamps
        doc_data['created_at'] = datetime.now().isoformat()
        doc_data['updated_at'] = datetime.now().isoformat()
        
        # Garante que status existe
        if 'status' not in doc_data or not doc_data.get('status'):
            doc_data['status'] = 'ativo'
        
        # Sanitiza dados antes de salvar (remove None e converte tipos)
        doc_data = sanitize_for_firestore(doc_data)
        
        print(f"[CRIAR_ACOMPANHAMENTO] Link a salvar: '{doc_data.get('link')}' ou '{doc_data.get('link_do_processo')}'")
        print(f"[CRIAR_ACOMPANHAMENTO] Número a salvar: '{doc_data.get('number')}' ou '{doc_data.get('process_number')}'")
        print(f"[CRIAR_ACOMPANHAMENTO] Dados finais a salvar:")
        print(f"  - title: {doc_data.get('title')}")
        print(f"  - process_title: {doc_data.get('process_title')}")
        print(f"  - status: {doc_data.get('status')}")
        print(f"  - Total de campos: {len(doc_data)}")
        
        # Validação final: verifica se há campos problemáticos
        problematic_fields = []
        for key, value in doc_data.items():
            if value is None:
                problematic_fields.append(key)
        
        if problematic_fields:
            print(f"[CRIAR_ACOMPANHAMENTO] ⚠️  AVISO: Campos com None encontrados após sanitização: {problematic_fields}")
            # Remove campos None restantes
            doc_data = {k: v for k, v in doc_data.items() if v is not None}
        
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
        link_value = updates.get('link_do_processo') or updates.get('link', '') or ''
        updates['link_do_processo'] = link_value
        updates['link'] = link_value  # Também salvar como 'link' para compatibilidade
        
        # Número do processo
        number_value = updates.get('process_number') or updates.get('number', '') or ''
        updates['number'] = number_value
        updates['process_number'] = number_value  # Compatibilidade
        
        # Garantir que listas não sejam None
        if 'parte_ativa' in updates and updates.get('parte_ativa') is None:
            updates['parte_ativa'] = []
        if 'parte_passiva' in updates and updates.get('parte_passiva') is None:
            updates['parte_passiva'] = []
        if 'outros_envolvidos' in updates and updates.get('outros_envolvidos') is None:
            updates['outros_envolvidos'] = []
        if 'processos_pais' in updates and updates.get('processos_pais') is None:
            updates['processos_pais'] = []
        if 'cases' in updates and updates.get('cases') is None:
            updates['cases'] = []
        if 'scenarios' in updates and updates.get('scenarios') is None:
            updates['scenarios'] = []
        if 'protocols' in updates and updates.get('protocols') is None:
            updates['protocols'] = []
        
        # Remove campos que não devem ser atualizados diretamente
        updates.pop('_id', None)
        updates.pop('id', None)
        updates.pop('created_at', None)
        
        # Sanitiza dados antes de atualizar (remove None e converte tipos)
        updates = sanitize_for_firestore(updates)
        
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Link a salvar: '{updates.get('link')}' ou '{updates.get('link_do_processo')}'")
        print(f"[ATUALIZAR_ACOMPANHAMENTO] Número a salvar: '{updates.get('number')}' ou '{updates.get('process_number')}'")
        
        # Validação final: verifica se há campos problemáticos
        problematic_fields = []
        for key, value in updates.items():
            if value is None:
                problematic_fields.append(key)
        
        if problematic_fields:
            print(f"[ATUALIZAR_ACOMPANHAMENTO] ⚠️  AVISO: Campos com None encontrados após sanitização: {problematic_fields}")
            # Remove campos None restantes
            updates = {k: v for k, v in updates.items() if v is not None}
        
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


# =============================================================================
# FUNÇÕES DE BANCO DE DADOS PARA SENHAS DE PROCESSOS
# =============================================================================

def get_process_passwords(process_id: str, collection_name: str = 'processes') -> List[Dict[str, Any]]:
    """
    Obtém todas as senhas cadastradas para um processo ou acompanhamento.
    
    Args:
        process_id: ID do processo/acompanhamento no Firestore
        collection_name: Nome da coleção ('processes' ou 'third_party_monitoring')
    
    Returns:
        Lista de dicionários com dados das senhas (senha descriptografada)
    """
    if not process_id:
        return []
    
    try:
        db = get_db()
        senhas_ref = db.collection(collection_name).document(process_id).collection('senhas_processo')
        docs = senhas_ref.order_by('data_criacao', direction='DESCENDING').stream()
        
        senhas = []
        for doc in docs:
            senha_data = doc.to_dict()
            senha_data['id'] = doc.id
            
            # Descriptografa a senha para exibição
            senha_criptografada = senha_data.get('senha', '')
            if senha_criptografada:
                senha_data['senha'] = decrypt_password(senha_criptografada)
            else:
                senha_data['senha'] = ''
            
            senhas.append(senha_data)
        
        return senhas
    
    except Exception as e:
        print(f"Erro ao buscar senhas do {collection_name} {process_id}: {e}")
        import traceback
        traceback.print_exc()
        return []


def save_process_password(process_id: str, password_data: Dict[str, Any], password_id: Optional[str] = None, collection_name: str = 'processes') -> Tuple[bool, Optional[str], str]:
    """
    Salva ou atualiza uma senha de processo ou acompanhamento.
    
    Args:
        process_id: ID do processo/acompanhamento no Firestore
        password_data: Dicionário com dados da senha:
            - titulo: str (obrigatório)
            - usuario: str (opcional)
            - senha: str (obrigatório, será criptografada)
            - link_acesso: str (opcional)
            - observacoes: str (opcional)
        password_id: ID da senha para atualização (None para criar nova)
        collection_name: Nome da coleção ('processes' ou 'third_party_monitoring')
    
    Returns:
        Tupla (sucesso: bool, senha_id: Optional[str], mensagem: str)
    """
    if not process_id:
        return False, None, "ID do processo/acompanhamento não fornecido"
    
    # Validação de campos obrigatórios
    if not password_data.get('titulo'):
        return False, None, "Título da senha é obrigatório"
    
    if not password_data.get('senha'):
        return False, None, "Senha é obrigatória"
    
    try:
        db = get_db()
        
        # Obter usuário atual
        current_user = get_current_user()
        user_id = current_user.get('uid') if current_user else 'sistema'
        
        # Preparar dados para salvar
        senha_para_salvar = {
            'titulo': password_data.get('titulo', '').strip(),
            'usuario': password_data.get('usuario', '').strip(),
            'senha': encrypt_password(password_data.get('senha', '')),  # Criptografa antes de salvar
            'link_acesso': password_data.get('link_acesso', '').strip(),
            'observacoes': password_data.get('observacoes', '').strip(),
            'data_atualizacao': SERVER_TIMESTAMP,
        }
        
        # Obter referência da subcoleção
        senhas_ref = db.collection(collection_name).document(process_id).collection('senhas_processo')
        
        if password_id:
            # Atualização
            senha_doc = senhas_ref.document(password_id)
            
            # Verificar se existe
            if not senha_doc.get().exists:
                return False, None, "Senha não encontrada"
            
            # Atualizar apenas campos modificados (preserva data_criacao e criado_por)
            senha_doc.update(senha_para_salvar)
            senha_id_final = password_id
            mensagem = "Senha atualizada com sucesso!"
        else:
            # Criação
            senha_para_salvar['data_criacao'] = SERVER_TIMESTAMP
            senha_para_salvar['criado_por'] = user_id
            
            doc_ref = senhas_ref.document()
            doc_ref.set(senha_para_salvar)
            senha_id_final = doc_ref.id
            mensagem = "Senha cadastrada com sucesso!"
        
        return True, senha_id_final, mensagem
    
    except Exception as e:
        print(f"Erro ao salvar senha do {collection_name} {process_id}: {e}")
        import traceback
        traceback.print_exc()
        return False, None, f"Erro ao salvar senha: {str(e)}"


def delete_process_password(process_id: str, password_id: str, collection_name: str = 'processes') -> Tuple[bool, str]:
    """
    Exclui uma senha de processo ou acompanhamento.
    
    Args:
        process_id: ID do processo/acompanhamento no Firestore
        password_id: ID da senha a ser excluída
        collection_name: Nome da coleção ('processes' ou 'third_party_monitoring')
    
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    """
    if not process_id or not password_id:
        return False, "ID do processo/acompanhamento ou da senha não fornecido"
    
    try:
        db = get_db()
        senha_doc = db.collection(collection_name).document(process_id).collection('senhas_processo').document(password_id)
        
        # Verificar se existe
        if not senha_doc.get().exists:
            return False, "Senha não encontrada"
        
        # Excluir
        senha_doc.delete()
        
        return True, "Senha excluída com sucesso!"
    
    except Exception as e:
        print(f"Erro ao excluir senha {password_id} do {collection_name} {process_id}: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Erro ao excluir senha: {str(e)}"


