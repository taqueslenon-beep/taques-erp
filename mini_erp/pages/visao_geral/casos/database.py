"""
Módulo de acesso a dados para Casos do workspace Visão Geral.
Usa coleção Firebase: vg_casos
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ....firebase_config import get_db

# Nome da coleção Firebase para este workspace
COLECAO_CASOS = 'vg_casos'


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
    campos_data = ['created_at', 'updated_at', 'data_criacao', 'data_atualizacao']

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


def listar_casos() -> List[Dict[str, Any]]:
    """
    Retorna todos os casos da coleção vg_casos.

    Returns:
        Lista de dicionários com dados dos casos
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        docs = db.collection(COLECAO_CASOS).stream()
        casos = []

        for doc in docs:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            caso = _converter_timestamps(caso)
            casos.append(caso)

        # Ordena por data de criação (mais recente primeiro)
        casos.sort(key=lambda c: c.get('created_at', ''), reverse=True)

        return casos

    except Exception as e:
        print(f"Erro ao listar casos: {e}")
        return []


def buscar_caso(caso_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um caso específico pelo ID.

    Args:
        caso_id: ID do documento no Firebase

    Returns:
        Dicionário com dados do caso ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_CASOS).document(caso_id).get()

        if doc.exists:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            caso = _converter_timestamps(caso)
            return caso

        return None

    except Exception as e:
        print(f"Erro ao buscar caso {caso_id}: {e}")
        return None


def criar_caso(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria um novo caso na coleção.

    Args:
        dados: Dicionário com dados do caso

    Returns:
        ID do documento criado ou None em caso de erro
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        # Adiciona timestamps
        dados['created_at'] = datetime.now()
        dados['updated_at'] = datetime.now()

        # Remove _id se existir
        dados.pop('_id', None)

        # Cria documento
        doc_ref = db.collection(COLECAO_CASOS).add(dados)

        return doc_ref[1].id

    except Exception as e:
        print(f"Erro ao criar caso: {e}")
        return None


def atualizar_caso(caso_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza um caso existente.

    Args:
        caso_id: ID do documento no Firebase
        dados: Dicionário com dados a atualizar

    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        dados['updated_at'] = datetime.now()
        dados.pop('_id', None)

        db.collection(COLECAO_CASOS).document(caso_id).update(dados)

        return True

    except Exception as e:
        print(f"Erro ao atualizar caso {caso_id}: {e}")
        return False


def excluir_caso(caso_id: str) -> bool:
    """
    Remove um caso da coleção.

    Args:
        caso_id: ID do documento no Firebase

    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        db.collection(COLECAO_CASOS).document(caso_id).delete()

        return True

    except Exception as e:
        print(f"Erro ao excluir caso {caso_id}: {e}")
        return False


def contar_casos() -> int:
    """
    Retorna o total de casos cadastrados.

    Returns:
        Número total de casos
    """
    try:
        db = get_db()
        if not db:
            return 0

        docs = db.collection(COLECAO_CASOS).stream()
        return sum(1 for _ in docs)

    except Exception as e:
        print(f"Erro ao contar casos: {e}")
        return 0


def listar_casos_por_nucleo(nucleo: str) -> List[Dict[str, Any]]:
    """
    Lista casos filtrados por núcleo.

    Args:
        nucleo: Nome do núcleo (Ambiental, Cobranças, Generalista)

    Returns:
        Lista de casos do núcleo especificado
    """
    try:
        db = get_db()
        if not db:
            return []

        docs = db.collection(COLECAO_CASOS).where('nucleo', '==', nucleo).stream()
        casos = []

        for doc in docs:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            caso = _converter_timestamps(caso)
            casos.append(caso)

        casos.sort(key=lambda c: c.get('created_at', ''), reverse=True)
        return casos

    except Exception as e:
        print(f"Erro ao listar casos por núcleo: {e}")
        return []


def listar_casos_por_status(status: str) -> List[Dict[str, Any]]:
    """
    Lista casos filtrados por status.

    Args:
        status: Status do caso (Em andamento, Suspenso, Arquivado, Encerrado)

    Returns:
        Lista de casos com o status especificado
    """
    try:
        db = get_db()
        if not db:
            return []

        docs = db.collection(COLECAO_CASOS).where('status', '==', status).stream()
        casos = []

        for doc in docs:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            caso = _converter_timestamps(caso)
            casos.append(caso)

        casos.sort(key=lambda c: c.get('created_at', ''), reverse=True)
        return casos

    except Exception as e:
        print(f"Erro ao listar casos por status: {e}")
        return []
