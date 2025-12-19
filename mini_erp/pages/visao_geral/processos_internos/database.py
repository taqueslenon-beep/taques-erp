"""
Módulo de acesso a dados para Processos Internos.
Usa coleção Firebase: processos_internos
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ....firebase_config import get_db
from .models import validar_processo_interno
from .constants import COLECAO_PROCESSOS_INTERNOS


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
    campos_data = ['data_criacao', 'data_atualizacao']

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


def criar_processo_interno(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria um novo processo interno na coleção.

    Args:
        dados: Dicionário com dados do processo interno

    Returns:
        ID do documento criado ou None em caso de erro
    """
    try:
        # Valida dados
        valido, mensagem_erro = validar_processo_interno(dados)
        if not valido:
            print(f"Erro de validação: {mensagem_erro}")
            raise ValueError(mensagem_erro)

        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        # Adiciona timestamps
        agora = datetime.now()
        dados['data_criacao'] = agora
        dados['data_atualizacao'] = agora

        # Garante status padrão
        if 'status' not in dados or not dados['status']:
            dados['status'] = 'ativo'

        # Remove _id se existir (não deve ser enviado na criação)
        dados.pop('_id', None)

        # Cria documento
        doc_ref = db.collection(COLECAO_PROCESSOS_INTERNOS).add(dados)

        print(f"Processo interno criado com sucesso. ID: {doc_ref[1].id}")
        return doc_ref[1].id

    except ValueError as e:
        # Erro de validação - re-raise para ser tratado no frontend
        raise
    except Exception as e:
        print(f"Erro ao criar processo interno: {e}")
        import traceback
        traceback.print_exc()
        return None


def listar_processos_internos(
    filtros: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retorna todos os processos internos da coleção, opcionalmente filtrados.

    Args:
        filtros: Dicionário com filtros a aplicar:
            - busca: str - Busca em título
            - categoria: str - Filtra por categoria
            - prioridade: str - Filtra por prioridade
            - status: str - Filtra por status

    Returns:
        Lista de dicionários com dados dos processos internos
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        # Busca todos os documentos
        query = db.collection(COLECAO_PROCESSOS_INTERNOS)

        # Aplica filtros do Firestore (se possível)
        if filtros:
            if filtros.get('categoria'):
                query = query.where('categoria', '==', filtros['categoria'])
            if filtros.get('prioridade'):
                query = query.where('prioridade', '==', filtros['prioridade'])
            if filtros.get('status'):
                query = query.where('status', '==', filtros['status'])

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
                if busca not in titulo:
                    continue

            processos.append(processo)

        # Ordena por data de criação (mais recente primeiro)
        processos.sort(
            key=lambda p: p.get('data_criacao', ''),
            reverse=True
        )

        return processos

    except Exception as e:
        print(f"Erro ao listar processos internos: {e}")
        import traceback
        traceback.print_exc()
        return []


def obter_processo_interno(processo_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um processo interno específico pelo ID.

    Args:
        processo_id: ID do documento no Firebase

    Returns:
        Dicionário com dados do processo interno ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_PROCESSOS_INTERNOS).document(
            processo_id
        ).get()

        if doc.exists:
            processo = doc.to_dict()
            processo['_id'] = doc.id
            processo = _converter_timestamps(processo)
            return processo

        return None

    except Exception as e:
        print(f"Erro ao buscar processo interno {processo_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def atualizar_processo_interno(
    processo_id: str,
    dados: Dict[str, Any]
) -> bool:
    """
    Atualiza um processo interno existente.

    Args:
        processo_id: ID do documento no Firebase
        dados: Dicionário com campos a atualizar

    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        # Valida dados
        valido, mensagem_erro = validar_processo_interno(dados)
        if not valido:
            print(f"Erro de validação: {mensagem_erro}")
            raise ValueError(mensagem_erro)

        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        # Atualiza timestamp
        dados['data_atualizacao'] = datetime.now()

        # Remove _id se existir (não deve ser atualizado)
        dados.pop('_id', None)
        dados.pop('data_criacao', None)  # Não atualiza data_criacao

        # Atualiza documento
        db.collection(COLECAO_PROCESSOS_INTERNOS).document(
            processo_id
        ).update(dados)

        print(f"Processo interno {processo_id} atualizado com sucesso")
        return True

    except ValueError as e:
        # Erro de validação - re-raise para ser tratado no frontend
        raise
    except Exception as e:
        print(f"Erro ao atualizar processo interno {processo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def excluir_processo_interno(processo_id: str) -> bool:
    """
    Exclui um processo interno da coleção.

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

        db.collection(COLECAO_PROCESSOS_INTERNOS).document(
            processo_id
        ).delete()

        print(f"Processo interno {processo_id} excluído com sucesso")
        return True

    except Exception as e:
        print(f"Erro ao excluir processo interno {processo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

