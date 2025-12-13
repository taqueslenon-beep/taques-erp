"""
database.py - Funções de acesso a dados do módulo de Prazos.

Gerencia busca e cache de prazos do Firestore.
"""

import time
import threading
from typing import List, Dict, Any, Optional
from ...firebase_config import get_db, ensure_firebase_initialized, get_auth
from ...storage import obter_display_name
from ...core import (
    get_users_list,
    get_clients_list,
    get_cases_list,
    get_display_name as get_display_name_core,
)


# =============================================================================
# CACHE EM MEMÓRIA
# =============================================================================

# Cache de prazos (TTL 5 minutos)
_cache_prazos = None
_cache_timestamp = None
_cache_lock = threading.Lock()
CACHE_DURATION = 300  # 5 minutos em segundos

# Cache para selects (TTL 5 minutos)
_cache_usuarios_select = None
_cache_usuarios_select_ts = None
_cache_clientes_select = None
_cache_clientes_select_ts = None
_cache_casos_select = None
_cache_casos_select_ts = None
CACHE_SELECT_DURATION = 300  # 5 minutos


def listar_prazos() -> List[Dict[str, Any]]:
    """
    Busca todos os prazos cadastrados no Firestore.

    Retorna:
        Lista de dicionários com dados dos prazos, ordenada por prazo_fatal
        (mais próximo primeiro).

    Tratamento de erros:
        - Retorna lista vazia em caso de erro
        - Loga erro no console
        - Retorna cache antigo se disponível
    """
    global _cache_prazos, _cache_timestamp

    now = time.time()

    # Verifica cache sem lock (leitura rápida)
    if _cache_prazos is not None and _cache_timestamp is not None:
        if now - _cache_timestamp < CACHE_DURATION:
            return _cache_prazos

    # Usa lock para evitar múltiplas consultas simultâneas
    with _cache_lock:
        # Verifica novamente dentro do lock
        if _cache_prazos is not None and _cache_timestamp is not None:
            if now - _cache_timestamp < CACHE_DURATION:
                return _cache_prazos

        # Consulta Firestore
        try:
            print("[PRAZOS] Carregando prazos do Firestore...")
            db = get_db()
            collection_name = 'prazos'
            docs = db.collection(collection_name).stream()

            prazos = []
            for doc in docs:
                prazo = doc.to_dict()
                prazo['_id'] = doc.id  # Guarda o ID do documento
                prazos.append(prazo)

            # Ordena por prazo_fatal (mais próximo primeiro)
            prazos.sort(key=lambda p: p.get('prazo_fatal', 0))

            # Atualiza cache
            _cache_prazos = prazos
            _cache_timestamp = time.time()

            print(f"[PRAZOS] {len(prazos)} prazos carregados com sucesso")
            return prazos

        except Exception as e:
            print(f"[ERROR] Erro ao buscar prazos do Firestore: {e}")
            import traceback
            traceback.print_exc()
            # Retorna cache antigo se houver erro
            if _cache_prazos is not None:
                return _cache_prazos
            return []


def buscar_prazo_por_id(prazo_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um prazo específico por ID no Firestore.

    Args:
        prazo_id: ID do documento no Firestore

    Returns:
        Dicionário com dados do prazo ou None se não encontrado
    """
    try:
        db = get_db()
        doc_ref = db.collection('prazos').document(prazo_id)
        doc = doc_ref.get()

        if doc.exists:
            prazo = doc.to_dict()
            prazo['_id'] = doc.id
            return prazo
        else:
            return None

    except Exception as e:
        print(f"[ERROR] Erro ao buscar prazo {prazo_id} do Firestore: {e}")
        return None


def criar_prazo(dados: Dict[str, Any]) -> str:
    """
    Cria um novo prazo no Firestore.

    Args:
        dados: Dicionário com dados do prazo

    Returns:
        ID do documento no Firestore
    """
    try:
        db = get_db()

        # Remove _id dos dados (é metadado)
        prazo_para_salvar = {k: v for k, v in dados.items() if k != '_id'}

        # Adiciona timestamps
        now = time.time()
        prazo_para_salvar['criado_em'] = now
        prazo_para_salvar['atualizado_em'] = now

        # Salva no Firestore
        doc_ref = db.collection('prazos').add(prazo_para_salvar)
        prazo_id = doc_ref[1].id

        # Invalida cache
        invalidar_cache_prazos()

        return prazo_id

    except Exception as e:
        print(f"[ERROR] Erro ao criar prazo no Firestore: {e}")
        raise


def atualizar_prazo(prazo_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza um prazo existente no Firestore.

    Args:
        prazo_id: ID do documento no Firestore
        dados: Dicionário com dados atualizados do prazo

    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        db = get_db()

        # Remove _id dos dados (é metadado)
        prazo_para_salvar = {k: v for k, v in dados.items() if k != '_id'}

        # Atualiza timestamp
        prazo_para_salvar['atualizado_em'] = time.time()

        db.collection('prazos').document(prazo_id).update(prazo_para_salvar)

        # Invalida cache
        invalidar_cache_prazos()

        return True

    except Exception as e:
        print(f"[ERROR] Erro ao atualizar prazo {prazo_id} no Firestore: {e}")
        return False


def excluir_prazo(prazo_id: str) -> bool:
    """
    Exclui um prazo do Firestore.

    Args:
        prazo_id: ID do documento no Firestore

    Returns:
        True se excluído com sucesso, False caso contrário
    """
    try:
        db = get_db()
        db.collection('prazos').document(prazo_id).delete()

        # Invalida cache
        invalidar_cache_prazos()

        return True

    except Exception as e:
        print(f"[ERROR] Erro ao excluir prazo {prazo_id} do Firestore: {e}")
        return False


def listar_prazos_por_status(status: str) -> List[Dict[str, Any]]:
    """
    Lista prazos filtrados por status.

    Args:
        status: Status do prazo ('pendente' ou 'concluido')

    Returns:
        Lista de prazos com o status especificado
    """
    todos_prazos = listar_prazos()
    # Filtra de forma case-insensitive
    return [p for p in todos_prazos if p.get('status', '').lower() == status.lower()]


def listar_prazos_por_responsavel(user_id: str) -> List[Dict[str, Any]]:
    """
    Lista prazos de um responsável específico.

    Args:
        user_id: ID do usuário responsável

    Returns:
        Lista de prazos onde o usuário é responsável
    """
    todos_prazos = listar_prazos()
    return [
        p for p in todos_prazos
        if user_id in (p.get('responsaveis') or [])
    ]


def invalidar_cache_prazos():
    """
    Invalida o cache de prazos, forçando nova busca no Firestore.
    """
    global _cache_prazos, _cache_timestamp

    with _cache_lock:
        _cache_prazos = None
        _cache_timestamp = None


# =============================================================================
# FUNÇÕES AUXILIARES PARA SELECTS (COM CACHE)
# =============================================================================

def buscar_usuarios_para_select() -> Dict[str, str]:
    """
    Busca lista de usuários do Firebase Auth formatados para uso em selects.

    Usa cache de 5 minutos para evitar múltiplas consultas.
    Busca nomes de exibição em batch (uma consulta Firestore) ao invés de N+1.

    Returns:
        Dicionário mapeando uid para "Nome (email)" para cada usuário ativo.
    """
    global _cache_usuarios_select, _cache_usuarios_select_ts

    now = time.time()

    # Verifica cache
    if _cache_usuarios_select is not None and _cache_usuarios_select_ts is not None:
        if now - _cache_usuarios_select_ts < CACHE_SELECT_DURATION:
            return _cache_usuarios_select

    try:
        print("[PRAZOS] Carregando usuários para select...")

        # Garante que Firebase está inicializado
        ensure_firebase_initialized()

        # Obtém instância do Auth
        auth_instance = get_auth()

        # Buscar nomes de exibição em BATCH (uma única consulta Firestore)
        db = get_db()
        users_docs = {}
        try:
            for doc in db.collection('users').stream():
                users_docs[doc.id] = doc.to_dict() or {}
        except Exception as e:
            print(f"[PRAZOS] Aviso: não foi possível carregar coleção users: {e}")

        # Lista usuários do Firebase Auth
        opcoes = {}
        page = auth_instance.list_users()

        while page:
            for user in page.users:
                # Ignora usuários desativados
                if user.disabled:
                    continue

                # Busca nome do cache local (sem consulta adicional)
                user_data = users_docs.get(user.uid, {})
                display_name = (
                    user_data.get('display_name') or
                    user_data.get('nome') or
                    user_data.get('name') or
                    user.display_name or
                    (user.email.split('@')[0] if user.email else '-')
                )

                email = user.email or ''

                # Formato: "Nome (email)"
                display = f"{display_name} ({email})" if email else display_name
                opcoes[user.uid] = display

            try:
                page = page.get_next_page()
            except StopIteration:
                break
            except Exception:
                break

        # Ordena alfabeticamente pelo nome
        opcoes = dict(sorted(opcoes.items(), key=lambda x: x[1].lower()))

        # Atualiza cache
        _cache_usuarios_select = opcoes
        _cache_usuarios_select_ts = time.time()

        print(f"[PRAZOS] {len(opcoes)} usuários carregados para select")
        return opcoes

    except Exception as e:
        print(f"[PRAZOS] Erro ao buscar usuários do Firebase Auth: {e}")
        import traceback
        traceback.print_exc()
        # Retorna cache antigo se disponível
        if _cache_usuarios_select is not None:
            return _cache_usuarios_select
        return {}


def buscar_clientes_para_select() -> Dict[str, str]:
    """
    Busca lista de PESSOAS (módulo Visão Geral) para uso no select de Clientes.

    Usa cache de 5 minutos para evitar múltiplas consultas.

    Returns:
        Dicionário mapeando pessoa_id para "Nome" para cada pessoa cadastrada.
    """
    global _cache_clientes_select, _cache_clientes_select_ts

    now = time.time()

    # Verifica cache
    if _cache_clientes_select is not None and _cache_clientes_select_ts is not None:
        if now - _cache_clientes_select_ts < CACHE_SELECT_DURATION:
            return _cache_clientes_select

    try:
        print("[PRAZOS] Carregando clientes para select...")

        db = get_db()
        docs = db.collection('vg_pessoas').stream()

        opcoes = {}
        for doc in docs:
            pessoa = doc.to_dict() or {}
            pessoa_id = doc.id

            # Prioridade para nome_exibicao, depois full_name
            nome = (
                pessoa.get('nome_exibicao') or
                pessoa.get('full_name') or
                pessoa.get('apelido') or
                '(sem nome)'
            )

            opcoes[pessoa_id] = nome

        # Ordena alfabeticamente pelo nome
        opcoes = dict(sorted(opcoes.items(), key=lambda x: x[1].lower()))

        # Atualiza cache
        _cache_clientes_select = opcoes
        _cache_clientes_select_ts = time.time()

        print(f"[PRAZOS] {len(opcoes)} clientes carregados para select")
        return opcoes

    except Exception as e:
        print(f"[PRAZOS] Erro ao buscar pessoas: {e}")
        import traceback
        traceback.print_exc()
        # Retorna cache antigo se disponível
        if _cache_clientes_select is not None:
            return _cache_clientes_select
        return {}


def buscar_casos_para_select() -> Dict[str, str]:
    """
    Busca lista de CASOS do workspace Visão Geral para uso em selects.

    Usa cache de 5 minutos para evitar múltiplas consultas.

    Returns:
        Dicionário mapeando caso_id para "Título" para cada caso cadastrado.
    """
    global _cache_casos_select, _cache_casos_select_ts

    now = time.time()

    # Verifica cache
    if _cache_casos_select is not None and _cache_casos_select_ts is not None:
        if now - _cache_casos_select_ts < CACHE_SELECT_DURATION:
            return _cache_casos_select

    try:
        print("[PRAZOS] Carregando casos para select...")

        db = get_db()
        docs = db.collection('vg_casos').stream()

        opcoes = {}
        for doc in docs:
            caso = doc.to_dict() or {}
            caso_id = doc.id

            # Campo de título em vg_casos
            titulo = caso.get('titulo') or caso.get('title') or '(sem título)'

            opcoes[caso_id] = titulo

        # Ordena alfabeticamente pelo título
        opcoes = dict(sorted(opcoes.items(), key=lambda x: x[1].lower()))

        # Atualiza cache
        _cache_casos_select = opcoes
        _cache_casos_select_ts = time.time()

        print(f"[PRAZOS] {len(opcoes)} casos carregados para select")
        return opcoes

    except Exception as e:
        print(f"[PRAZOS] Erro ao buscar casos: {e}")
        import traceback
        traceback.print_exc()
        # Retorna cache antigo se disponível
        if _cache_casos_select is not None:
            return _cache_casos_select
        return {}


def invalidar_cache_selects():
    """
    Invalida o cache de todos os selects, forçando nova busca.
    """
    global _cache_usuarios_select, _cache_usuarios_select_ts
    global _cache_clientes_select, _cache_clientes_select_ts
    global _cache_casos_select, _cache_casos_select_ts

    _cache_usuarios_select = None
    _cache_usuarios_select_ts = None
    _cache_clientes_select = None
    _cache_clientes_select_ts = None
    _cache_casos_select = None
    _cache_casos_select_ts = None


# =============================================================================
# ESTATÍSTICAS DE PRAZOS PARA PAINEL
# =============================================================================

def obter_estatisticas_prazos_mes() -> Dict[str, Any]:
    """
    Obtém estatísticas de prazos do mês atual para o painel.

    Calcula:
    - Prazos pendentes do mês
    - Prazos atrasados (prazo fatal < hoje e status pendente)
    - Prazos concluídos no mês
    - Total de prazos do mês

    Returns:
        Dicionário com estatísticas:
        {
            'pendentes': int,
            'atrasados': int,
            'concluidos': int,
            'total_mes': int,
            'mes_nome': str,
            'ano': int
        }
    """
    from datetime import datetime, date

    try:
        # Buscar todos os prazos (usa cache)
        todos_prazos = listar_prazos()

        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)

        # Nomes dos meses em português
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

        # Contadores
        pendentes = 0
        atrasados = 0
        concluidos = 0
        total_mes = 0

        for prazo in todos_prazos:
            prazo_fatal_ts = prazo.get('prazo_fatal')
            status = prazo.get('status', 'pendente').lower()

            if not prazo_fatal_ts:
                continue

            try:
                # Converter timestamp para date
                if isinstance(prazo_fatal_ts, (int, float)):
                    data_fatal = datetime.fromtimestamp(prazo_fatal_ts).date()
                else:
                    continue

                # Verificar se é do mês atual
                if data_fatal.month == hoje.month and data_fatal.year == hoje.year:
                    total_mes += 1

                    if status == 'concluido':
                        concluidos += 1
                    elif data_fatal < hoje:
                        atrasados += 1
                    else:
                        pendentes += 1

            except Exception:
                continue

        return {
            'pendentes': pendentes,
            'atrasados': atrasados,
            'concluidos': concluidos,
            'total_mes': total_mes,
            'mes_nome': meses_pt.get(hoje.month, ''),
            'ano': hoje.year
        }

    except Exception as e:
        print(f"[PRAZOS] Erro ao obter estatísticas do mês: {e}")
        import traceback
        traceback.print_exc()
        return {
            'pendentes': 0,
            'atrasados': 0,
            'concluidos': 0,
            'total_mes': 0,
            'mes_nome': '',
            'ano': 0
        }
