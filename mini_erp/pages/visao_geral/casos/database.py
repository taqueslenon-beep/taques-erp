"""
Módulo de acesso a dados para Casos do workspace Visão Geral.
Usa coleção Firebase: vg_casos
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ....firebase_config import get_db
from ....models.prioridade import (
    validar_prioridade,
    normalizar_prioridade,
    PRIORIDADE_PADRAO
)

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

        # Garante que prioridade seja definida (default: P4)
        if 'prioridade' not in dados or not dados.get('prioridade'):
            dados['prioridade'] = PRIORIDADE_PADRAO
        else:
            # Normaliza a prioridade
            dados['prioridade'] = normalizar_prioridade(dados['prioridade'])

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
        
        # Normaliza prioridade se estiver presente
        if 'prioridade' in dados and dados.get('prioridade'):
            dados['prioridade'] = normalizar_prioridade(dados['prioridade'])
        
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
        status: Status do caso (Em andamento, Concluído, Concluído com pendências, Em monitoramento, Substabelecido)

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


# =============================================================================
# FUNÇÕES DE PRIORIDADE
# =============================================================================

def atualizar_prioridade_caso(caso_id: str, prioridade: str) -> bool:
    """
    Atualiza a prioridade de um caso específico.
    
    Args:
        caso_id: ID do caso no Firestore
        prioridade: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        True se atualização foi bem-sucedida, False caso contrário
    """
    if not caso_id:
        print("⚠️  ID do caso não fornecido")
        return False
    
    # Normaliza e valida a prioridade
    prioridade_normalizada = normalizar_prioridade(prioridade)
    
    if not validar_prioridade(prioridade_normalizada):
        print(f"⚠️  Prioridade inválida: {prioridade}")
        return False
    
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False
        
        case_ref = db.collection(COLECAO_CASOS).document(caso_id)
        
        # Verifica se o caso existe
        if not case_ref.get().exists:
            print(f"⚠️  Caso não encontrado: {caso_id}")
            return False
        
        # Atualiza a prioridade
        case_ref.update({
            'prioridade': prioridade_normalizada,
            'updated_at': datetime.now()
        })
        
        print(f"✅ Prioridade do caso {caso_id} atualizada para {prioridade_normalizada}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar prioridade do caso {caso_id}: {e}")
        return False


def listar_casos_por_prioridade(prioridade: str) -> List[Dict[str, Any]]:
    """
    Retorna lista de casos filtrados por prioridade.
    
    Args:
        prioridade: Código da prioridade (P1, P2, P3, P4)
    
    Returns:
        Lista de dicionários com dados dos casos da prioridade especificada
    """
    if not validar_prioridade(prioridade):
        print(f"⚠️  Prioridade inválida: {prioridade}")
        return []
    
    try:
        # Normaliza a prioridade
        prioridade_normalizada = normalizar_prioridade(prioridade)
        
        db = get_db()
        if not db:
            return []
        
        # Busca casos com a prioridade especificada
        docs = db.collection(COLECAO_CASOS).where('prioridade', '==', prioridade_normalizada).stream()
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
        print(f"⚠️  Erro ao listar casos por prioridade {prioridade}: {e}")
        return []


def contar_casos_por_prioridade() -> Dict[str, int]:
    """
    Retorna dicionário com contagem de casos por prioridade.
    
    Returns:
        Dicionário no formato: {'P1': 5, 'P2': 10, 'P3': 8, 'P4': 20}
    """
    try:
        db = get_db()
        if not db:
            return {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
        
        collection_ref = db.collection(COLECAO_CASOS)
        
        # Inicializa contadores
        contadores = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
        
        # Busca todos os casos
        docs = collection_ref.stream()
        
        for doc in docs:
            case_data = doc.to_dict()
            if case_data:
                prioridade = normalizar_prioridade(case_data.get('prioridade'))
                if prioridade in contadores:
                    contadores[prioridade] += 1
                else:
                    # Casos sem prioridade ou com prioridade inválida contam como P4
                    contadores['P4'] += 1
        
        return contadores
        
    except Exception as e:
        print(f"⚠️  Erro ao contar casos por prioridade: {e}")
        return {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
