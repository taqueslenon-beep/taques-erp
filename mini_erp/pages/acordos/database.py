"""
database.py - Operações de banco de dados para o módulo de Acordos.

Este módulo contém:
- Funções CRUD (create, read, update, delete)
- Funções de busca e filtro
- Integração com Firestore (coleção: "agreements")
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ...core import (
    invalidate_cache, get_cases_list, get_processes_list, 
    get_clients_list, get_opposing_parties_list, get_users_list
)
from ...firebase_config import get_db


# =============================================================================
# FUNÇÕES DE ACESSO A DADOS
# =============================================================================

def get_all_acordos() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os acordos do Firestore.
    
    Returns:
        Lista de dicionários com dados dos acordos
    """
    try:
        db = get_db()
        docs = db.collection('agreements').stream()
        acordos = []
        for doc in docs:
            acordo = doc.to_dict()
            acordo['_id'] = doc.id  # Guarda o ID do documento
            acordos.append(acordo)
        return acordos
    except Exception as e:
        print(f"Erro ao buscar acordos: {e}")
        import traceback
        traceback.print_exc()
        return []


def listar_acordos() -> List[Dict[str, Any]]:
    """
    Lista todos os acordos formatados para exibição na tabela.
    
    Returns:
        Lista de dicionários com campos: data, titulo, partes_envolvidas, status, _id
    """
    try:
        acordos = get_all_acordos()
        from ...core import get_clients_list, get_opposing_parties_list, get_display_name
        
        rows = []
        for acordo in acordos:
            # Formata data de celebração
            data_celebracao = acordo.get('data_celebracao') or acordo.get('data_assinatura', '')
            data_display = ''
            if data_celebracao:
                # Tenta converter de ISO para DD/MM/AAAA
                try:
                    from datetime import datetime
                    if '-' in data_celebracao and len(data_celebracao) >= 10:
                        dt = datetime.strptime(data_celebracao[:10], '%Y-%m-%d')
                        data_display = dt.strftime('%d/%m/%Y')
                    elif '/' in data_celebracao:
                        data_display = data_celebracao
                except:
                    data_display = data_celebracao
            
            # Formata partes envolvidas (agregadas)
            partes = []
            
            # Busca clientes
            clientes_ids = acordo.get('clientes_ids', [])
            if clientes_ids:
                clients_list = get_clients_list()
                for cliente_id in clientes_ids:
                    for cliente in clients_list:
                        if cliente.get('_id') == cliente_id:
                            partes.append(get_display_name(cliente))
                            break
            
            # Busca parte contrária
            parte_contraria_id = acordo.get('parte_contraria')
            if parte_contraria_id:
                all_people = get_clients_list() + get_opposing_parties_list()
                for pessoa in all_people:
                    if pessoa.get('_id') == parte_contraria_id:
                        partes.append(get_display_name(pessoa))
                        break
            
            # Busca outros envolvidos
            outros_envolvidos_ids = acordo.get('outros_envolvidos', [])
            if outros_envolvidos_ids:
                all_people = get_clients_list() + get_opposing_parties_list()
                for pessoa_id in outros_envolvidos_ids:
                    for pessoa in all_people:
                        if pessoa.get('_id') == pessoa_id:
                            partes.append(get_display_name(pessoa))
                            break
            
            partes_envolvidas = ', '.join(partes) if partes else '-'
            
            rows.append({
                '_id': acordo.get('_id', ''),
                'data': data_display,
                'data_sort': data_celebracao or '',  # Para ordenação
                'titulo': acordo.get('titulo', 'Sem título'),
                'partes_envolvidas': partes_envolvidas,
                'status': acordo.get('status', 'Rascunho'),
            })
        
        # Ordena por data (mais recente primeiro) ou título
        rows.sort(key=lambda r: (r.get('data_sort') or '', r.get('titulo', '').lower()), reverse=True)
        return rows
    except Exception as e:
        print(f"Erro ao listar acordos: {e}")
        import traceback
        traceback.print_exc()
        return []


def buscar_acordos(termo: str) -> List[Dict[str, Any]]:
    """
    Busca acordos por termo (título, número, etc).
    
    Args:
        termo: Termo de busca
    
    Returns:
        Lista de acordos encontrados
    """
    if not termo:
        return listar_acordos()
    
    termo_lower = termo.lower().strip()
    todos_acordos = listar_acordos()
    
    # Filtra por título ou cliente
    resultados = []
    for acordo in todos_acordos:
        titulo = (acordo.get('titulo') or '').lower()
        cliente = (acordo.get('cliente') or '').lower()
        
        if termo_lower in titulo or termo_lower in cliente:
            resultados.append(acordo)
    
    return resultados


def get_acordo_by_id(acordo_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um acordo pelo ID (alias para buscar_acordo_por_id).
    
    Args:
        acordo_id: ID do acordo
    
    Returns:
        Dicionário do acordo ou None se não encontrado
    """
    return buscar_acordo_por_id(acordo_id)


def buscar_acordo_por_id(acordo_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um acordo completo pelo ID, incluindo todas as cláusulas.
    
    Args:
        acordo_id: ID do acordo
    
    Returns:
        Dicionário do acordo completo ou None se não encontrado
    """
    try:
        db = get_db()
        doc = db.collection('agreements').document(acordo_id).get()
        if doc.exists:
            acordo = doc.to_dict()
            acordo['_id'] = doc.id
            # Garante que arrays existem
            if 'clientes_ids' not in acordo:
                acordo['clientes_ids'] = []
            if 'outros_envolvidos' not in acordo:
                acordo['outros_envolvidos'] = []
            if 'clausulas' not in acordo:
                acordo['clausulas'] = []
            return acordo
        return None
    except Exception as e:
        print(f"Erro ao buscar acordo {acordo_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_acordos_by_status(status: str) -> List[Dict[str, Any]]:
    """
    Busca acordos filtrados por status.
    
    Args:
        status: Status do acordo (Rascunho, Ativo, Arquivado, Cancelado)
    
    Returns:
        Lista de acordos com o status especificado
    """
    try:
        db = get_db()
        query = db.collection('agreements').where('status', '==', status)
        docs = query.stream()
        acordos = []
        for doc in docs:
            acordo = doc.to_dict()
            acordo['_id'] = doc.id
            acordos.append(acordo)
        return acordos
    except Exception as e:
        print(f"Erro ao buscar acordos por status {status}: {e}")
        return []


def get_acordos_by_cliente(cliente_id: str) -> List[Dict[str, Any]]:
    """
    Busca acordos filtrados por cliente.
    
    Args:
        cliente_id: ID do cliente
    
    Returns:
        Lista de acordos do cliente especificado
    """
    try:
        db = get_db()
        query = db.collection('agreements').where('cliente_id', '==', cliente_id)
        docs = query.stream()
        acordos = []
        for doc in docs:
            acordo = doc.to_dict()
            acordo['_id'] = doc.id
            acordos.append(acordo)
        return acordos
    except Exception as e:
        print(f"Erro ao buscar acordos do cliente {cliente_id}: {e}")
        return []


# =============================================================================
# FUNÇÕES DE CRIAÇÃO E ATUALIZAÇÃO
# =============================================================================

def create_acordo(acordo_data: Dict[str, Any]) -> str:
    """
    Cria um novo acordo no Firestore.
    
    Args:
        acordo_data: Dados do acordo a criar
    
    Returns:
        ID do acordo criado
    """
    try:
        # Gera ID único se não fornecido
        if 'id' not in acordo_data or not acordo_data['id']:
            acordo_data['id'] = str(uuid.uuid4())
        
        # Define datas de criação e atualização
        now = datetime.utcnow().isoformat()
        acordo_data['data_criacao'] = acordo_data.get('data_criacao', now)
        acordo_data['data_atualizacao'] = now
        
        # Define status padrão se não fornecido
        if 'status' not in acordo_data or not acordo_data['status']:
            acordo_data['status'] = 'Rascunho'
        
        # Remove _id do acordo antes de salvar (é metadado interno)
        # Nota: Os _id das cláusulas dentro do array 'clausulas' são preservados
        # pois fazem parte dos dados da cláusula, não são metadados do documento
        doc_id = acordo_data.pop('_id', None) or acordo_data['id']
        
        # Salva no Firestore (inclui todas as cláusulas com seus IDs e metadados)
        db = get_db()
        db.collection('agreements').document(doc_id).set(acordo_data)
        
        # Invalida cache
        invalidate_cache('agreements')
        
        return doc_id
    except Exception as e:
        print(f"Erro ao criar acordo: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erro ao criar acordo: {str(e)}")


def atualizar_acordo(acordo_id: str, acordo_data: Dict[str, Any]) -> bool:
    """
    Atualiza um acordo existente (alias para update_acordo).
    
    Args:
        acordo_id: ID do acordo
        acordo_data: Dados atualizados do acordo
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    # Chama a função interna update_acordo_internal para evitar recursão
    return update_acordo_internal(acordo_id, acordo_data)


def update_acordo_internal(acordo_id: str, acordo_data: Dict[str, Any]) -> bool:
    """
    Atualiza um acordo existente (função interna).
    
    Args:
        acordo_id: ID do acordo
        acordo_data: Dados atualizados do acordo
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        # Atualiza data de atualização
        acordo_data['data_atualizacao'] = datetime.utcnow().isoformat()
        
        # Remove _id e id dos dados (não devem ser atualizados)
        acordo_data.pop('_id', None)
        acordo_data.pop('id', None)
        
        # Atualiza no Firestore
        db = get_db()
        db.collection('agreements').document(acordo_id).update(acordo_data)
        
        # Invalida cache
        invalidate_cache('agreements')
        
        return True
    except Exception as e:
        print(f"Erro ao atualizar acordo {acordo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_acordo(acordo_id: str, acordo_data: Dict[str, Any]) -> bool:
    """Alias para atualizar_acordo."""
    return atualizar_acordo(acordo_id, acordo_data)


def deletar_acordo(acordo_id: str) -> bool:
    """
    Remove um acordo do Firestore.
    
    Args:
        acordo_id: ID do acordo a remover
    
    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        db.collection('agreements').document(acordo_id).delete()
        
        # Invalida cache
        invalidate_cache('agreements')
        
        return True
    except Exception as e:
        print(f"Erro ao deletar acordo {acordo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def delete_acordo(acordo_id: str) -> bool:
    """Alias para deletar_acordo."""
    return deletar_acordo(acordo_id)


# =============================================================================
# FUNÇÕES DE BUSCA PARA FORMULÁRIO
# =============================================================================

def listar_casos() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os casos para seleção no formulário.
    
    Returns:
        Lista de dicionários com dados dos casos
    """
    return get_cases_list()


def listar_processos() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os processos para seleção no formulário.
    
    Returns:
        Lista de dicionários com dados dos processos
    """
    return get_processes_list()


def listar_usuarios() -> List[Dict[str, Any]]:
    """
    Retorna lista de todos os usuários do sistema para seleção de responsável.
    
    Returns:
        Lista de dicionários com dados dos usuários
    """
    return get_users_list()


def listar_pessoas_como_clientes() -> List[Dict[str, Any]]:
    """
    Retorna lista de pessoas que são clientes para seleção múltipla.
    
    Returns:
        Lista de dicionários com dados dos clientes
    """
    clientes = get_clients_list()
    # Adiciona tipo para identificação
    return [{**cliente, '_tipo': 'cliente'} for cliente in clientes]


def listar_todas_pessoas() -> List[Dict[str, Any]]:
    """
    Retorna lista combinada de todas as pessoas (clientes e partes contrárias).
    
    Returns:
        Lista de dicionários com dados das pessoas
    """
    pessoas = []
    # Adiciona clientes
    for cliente in get_clients_list():
        pessoas.append({**cliente, '_tipo': 'cliente'})
    # Adiciona partes contrárias
    for parte in get_opposing_parties_list():
        pessoas.append({**parte, '_tipo': 'parte_contraria'})
    return pessoas


def listar_pessoas() -> List[Dict[str, Any]]:
    """
    DEPRECATED: Use listar_todas_pessoas() ou listar_pessoas_como_clientes()
    
    Retorna lista combinada de clientes e partes contrárias para seleção.
    
    Returns:
        Lista de dicionários com dados das pessoas
    """
    return listar_todas_pessoas()


def buscar_caso_por_id(caso_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um caso pelo ID.
    
    Args:
        caso_id: ID ou slug do caso
    
    Returns:
        Dicionário do caso ou None se não encontrado
    """
    casos = get_cases_list()
    for caso in casos:
        if caso.get('_id') == caso_id or caso.get('slug') == caso_id:
            return caso
    return None


def buscar_processo_por_id(processo_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um processo pelo ID.
    
    Args:
        processo_id: ID do processo
    
    Returns:
        Dicionário do processo ou None se não encontrado
    """
    processos = get_processes_list()
    for processo in processos:
        if processo.get('_id') == processo_id:
            return processo
    return None

