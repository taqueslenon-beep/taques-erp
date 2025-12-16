"""
Módulo de acesso a dados para Processos do workspace Visão Geral.
Usa coleção Firebase: vg_processos
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ....firebase_config import get_db
from .models import validar_processo

# Nome da coleção Firebase para este workspace
COLECAO_PROCESSOS = 'vg_processos'


def _converter_timestamps(documento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte campos DatetimeWithNanoseconds do Firebase para string ISO.
    Isso evita erros de serialização JSON no NiceGUI.

    Args:
        documento: Dicionário com dados do Firebase

    Returns:
        Dicionário com timestamps convertidos para string
    """
    if documento is None:
        return {}

    dados = dict(documento)

    # Campos que podem ser timestamp do Firebase
    campos_data = ['created_at', 'updated_at', 'data_abertura', 'data_ultima_movimentacao']

    for campo in campos_data:
        if campo in dados and dados[campo] is not None:
            try:
                if hasattr(dados[campo], 'isoformat'):
                    dados[campo] = dados[campo].isoformat()
                elif hasattr(dados[campo], 'strftime'):
                    dados[campo] = dados[campo].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    dados[campo] = str(dados[campo])
            except Exception:
                dados[campo] = None

    return dados


def listar_processos(filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Retorna todos os processos da coleção vg_processos, opcionalmente filtrados.

    Args:
        filtros: Dicionário com filtros a aplicar:
            - busca: str - Busca em título e número
            - area: str - Filtra por área
            - status: str - Filtra por status
            - tipo: str - Filtra por tipo (Judicial/Administrativo)
            - caso_id: str - Filtra por caso vinculado
            - grupo_nome: str - Filtra por grupo

    Returns:
        Lista de dicionários com dados dos processos
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        # Busca todos os documentos
        query = db.collection(COLECAO_PROCESSOS)

        # Aplica filtros do Firestore (se possível)
        if filtros:
            if filtros.get('area'):
                query = query.where('area', '==', filtros['area'])
            if filtros.get('status'):
                query = query.where('status', '==', filtros['status'])
            if filtros.get('tipo'):
                query = query.where('tipo', '==', filtros['tipo'])
            if filtros.get('caso_id'):
                query = query.where('caso_id', '==', filtros['caso_id'])
            if filtros.get('grupo_nome'):
                query = query.where('grupo_nome', '==', filtros['grupo_nome'])

        docs = query.stream()
        processos = []

        for doc in docs:
            processo = doc.to_dict()
            processo['_id'] = doc.id
            processo = _converter_timestamps(processo)

            # Aplica filtros em memória (busca textual)
            if filtros and filtros.get('busca'):
                busca = filtros['busca'].lower()
                titulo = (processo.get('titulo') or '').lower()
                numero = (processo.get('numero') or '').lower()
                if busca not in titulo and busca not in numero:
                    continue

            processos.append(processo)

        # Ordena por data de criação (mais recente primeiro)
        processos.sort(key=lambda p: p.get('created_at', ''), reverse=True)

        return processos

    except Exception as e:
        print(f"Erro ao listar processos: {e}")
        import traceback
        traceback.print_exc()
        return []


def buscar_processo(processo_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um processo específico pelo ID.

    Args:
        processo_id: ID do documento no Firebase

    Returns:
        Dicionário com dados do processo ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_PROCESSOS).document(processo_id).get()

        if doc.exists:
            processo = doc.to_dict()
            processo['_id'] = doc.id
            processo = _converter_timestamps(processo)
            return processo

        return None

    except Exception as e:
        print(f"Erro ao buscar processo {processo_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def criar_processo(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria um novo processo na coleção.

    Args:
        dados: Dicionário com dados do processo

    Returns:
        ID do documento criado ou None em caso de erro
    """
    try:
        # Valida dados
        valido, mensagem_erro = validar_processo(dados)
        if not valido:
            print(f"Erro de validação: {mensagem_erro}")
            return None

        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        # Adiciona timestamps
        dados['created_at'] = datetime.now()
        dados['updated_at'] = datetime.now()

        # Remove _id se existir
        dados.pop('_id', None)

        # Garante que listas não sejam None
        if 'clientes' not in dados:
            dados['clientes'] = []
        if 'clientes_nomes' not in dados:
            dados['clientes_nomes'] = []
        if 'processos_filhos_ids' not in dados:
            dados['processos_filhos_ids'] = []

        # Cria documento
        doc_ref = db.collection(COLECAO_PROCESSOS).add(dados)

        print(f"Processo criado com sucesso. ID: {doc_ref[1].id}")
        return doc_ref[1].id

    except Exception as e:
        print(f"Erro ao criar processo: {e}")
        import traceback
        traceback.print_exc()
        return None


def atualizar_processo(processo_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza um processo existente.

    Args:
        processo_id: ID do documento no Firebase
        dados: Dicionário com campos a atualizar

    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        # Valida dados
        valido, mensagem_erro = validar_processo(dados)
        if not valido:
            print(f"Erro de validação: {mensagem_erro}")
            return False

        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        # Atualiza timestamp
        dados['updated_at'] = datetime.now()

        # Remove _id se existir (não deve ser atualizado)
        dados.pop('_id', None)
        dados.pop('created_at', None)  # Não atualiza created_at

        # Atualiza documento
        db.collection(COLECAO_PROCESSOS).document(processo_id).update(dados)

        print(f"Processo {processo_id} atualizado com sucesso")
        return True

    except Exception as e:
        print(f"Erro ao atualizar processo {processo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def excluir_processo(processo_id: str) -> bool:
    """
    Exclui um processo da coleção.

    Args:
        processo_id: ID do documento no Firebase

    Returns:
        True se excluído com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        db.collection(COLECAO_PROCESSOS).document(processo_id).delete()

        print(f"Processo {processo_id} excluído com sucesso")
        return True

    except Exception as e:
        print(f"Erro ao excluir processo {processo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def contar_processos(filtros: Optional[Dict[str, Any]] = None) -> int:
    """
    Conta o total de processos, opcionalmente filtrados.

    Args:
        filtros: Dicionário com filtros a aplicar (mesmo formato de listar_processos)

    Returns:
        Número total de processos
    """
    try:
        processos = listar_processos(filtros)
        return len(processos)
    except Exception as e:
        print(f"Erro ao contar processos: {e}")
        return 0


def listar_processos_por_caso(caso_id: str) -> List[Dict[str, Any]]:
    """
    Lista todos os processos vinculados a um caso específico.

    Args:
        caso_id: ID do caso

    Returns:
        Lista de processos vinculados ao caso
    """
    try:
        filtros = {'caso_id': caso_id}
        return listar_processos(filtros)
    except Exception as e:
        print(f"Erro ao listar processos por caso {caso_id}: {e}")
        return []


def listar_processos_por_grupo(grupo_nome: str) -> List[Dict[str, Any]]:
    """
    Lista todos os processos de um grupo específico.

    Args:
        grupo_nome: Nome do grupo

    Returns:
        Lista de processos do grupo
    """
    try:
        filtros = {'grupo_nome': grupo_nome}
        return listar_processos(filtros)
    except Exception as e:
        print(f"Erro ao listar processos por grupo {grupo_nome}: {e}")
        return []


def listar_processos_pais() -> List[Dict[str, Any]]:
    """
    Lista todos os processos (para seleção de processo pai).
    Filtra o próprio processo se estiver editando.

    Returns:
        Lista de todos os processos
    """
    try:
        todos_processos = listar_processos()
        return todos_processos
    except Exception as e:
        print(f"Erro ao listar processos pais: {e}")
        return []



