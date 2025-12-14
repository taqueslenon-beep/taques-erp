"""
Módulo de acesso a dados para Grupos de Relacionamento.
Usa coleção Firebase: vg_grupos_relacionamento
"""
from typing import List, Optional
from datetime import datetime
from ....firebase_config import get_db
from .models_grupo import GrupoRelacionamento


# Nome da coleção Firebase para grupos de relacionamento
COLECAO_GRUPOS = 'vg_grupos_relacionamento'


def _converter_timestamps(documento: dict) -> dict:
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
    campos_data = ['created_at', 'updated_at']

    for campo in campos_data:
        if campo in dados and dados[campo] is not None:
            try:
                # Se for DatetimeWithNanoseconds ou datetime, converter para string
                if hasattr(dados[campo], 'isoformat'):
                    dados[campo] = dados[campo].isoformat()
                elif hasattr(dados[campo], 'strftime'):
                    dados[campo] = dados[campo].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    dados[campo] = str(dados[campo])
            except Exception:
                dados[campo] = None

    return dados


def criar_grupo(grupo: GrupoRelacionamento) -> str:
    """
    Cria um novo grupo de relacionamento no Firestore.

    Args:
        grupo: Instância de GrupoRelacionamento a ser criada

    Returns:
        ID do documento criado ou string vazia em caso de erro
    """
    try:
        # Valida dados antes de salvar
        valido, mensagem_erro = grupo.validar()
        if not valido:
            print(f"Erro de validação ao criar grupo: {mensagem_erro}")
            return ""

        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return ""

        # Atualiza timestamps
        grupo.created_at = datetime.now()
        grupo.updated_at = datetime.now()

        # Converte para dicionário (sem _id)
        dados = grupo.to_dict()
        dados.pop('_id', None)  # Remove _id se existir

        # Cria documento
        doc_ref = db.collection(COLECAO_GRUPOS).add(dados)

        # Retorna o ID do documento criado
        return doc_ref[1].id

    except Exception as e:
        print(f"Erro ao criar grupo: {e}")
        import traceback
        traceback.print_exc()
        return ""


def obter_grupo(grupo_id: str) -> Optional[GrupoRelacionamento]:
    """
    Busca um grupo de relacionamento específico pelo ID.

    Args:
        grupo_id: ID do documento no Firebase

    Returns:
        Instância de GrupoRelacionamento ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_GRUPOS).document(grupo_id).get()

        if doc.exists:
            dados = doc.to_dict()
            dados['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            dados = _converter_timestamps(dados)
            return GrupoRelacionamento.from_dict(dados)

        return None

    except Exception as e:
        print(f"Erro ao buscar grupo {grupo_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def listar_grupos(apenas_ativos: bool = True) -> List[GrupoRelacionamento]:
    """
    Retorna todos os grupos de relacionamento.

    Args:
        apenas_ativos: Se True, retorna apenas grupos ativos

    Returns:
        Lista de instâncias de GrupoRelacionamento
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        # Monta query
        query = db.collection(COLECAO_GRUPOS)
        
        # Filtra por ativos se solicitado
        if apenas_ativos:
            query = query.where('ativo', '==', True)

        docs = query.stream()
        grupos = []

        for doc in docs:
            dados = doc.to_dict()
            dados['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            dados = _converter_timestamps(dados)
            grupo = GrupoRelacionamento.from_dict(dados)
            grupos.append(grupo)

        # Ordena por nome
        grupos.sort(key=lambda g: g.nome.lower())

        return grupos

    except Exception as e:
        print(f"Erro ao listar grupos: {e}")
        import traceback
        traceback.print_exc()
        return []


def atualizar_grupo(grupo_id: str, dados: dict) -> bool:
    """
    Atualiza um grupo de relacionamento existente.

    Args:
        grupo_id: ID do documento no Firebase
        dados: Dicionário com dados a atualizar

    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        # Adiciona timestamp de atualização
        dados['updated_at'] = datetime.now()

        # Remove _id dos dados (não deve ser atualizado)
        dados.pop('_id', None)

        # Valida dados se nome estiver sendo atualizado
        if 'nome' in dados:
            nome = dados.get('nome', '').strip()
            if not nome or len(nome) < 2:
                print("Erro: Nome do grupo inválido")
                return False

        # Atualiza documento
        db.collection(COLECAO_GRUPOS).document(grupo_id).update(dados)

        return True

    except Exception as e:
        print(f"Erro ao atualizar grupo {grupo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def excluir_grupo(grupo_id: str) -> bool:
    """
    Remove um grupo de relacionamento (soft delete - marca como inativo).

    Args:
        grupo_id: ID do documento no Firebase

    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        # Soft delete: marca como inativo ao invés de deletar
        dados = {
            'ativo': False,
            'updated_at': datetime.now()
        }

        db.collection(COLECAO_GRUPOS).document(grupo_id).update(dados)

        return True

    except Exception as e:
        print(f"Erro ao excluir grupo {grupo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def contar_grupos(apenas_ativos: bool = True) -> int:
    """
    Retorna o total de grupos cadastrados.

    Args:
        apenas_ativos: Se True, conta apenas grupos ativos

    Returns:
        Número total de grupos
    """
    try:
        db = get_db()
        if not db:
            return 0

        # Monta query
        query = db.collection(COLECAO_GRUPOS)
        
        # Filtra por ativos se solicitado
        if apenas_ativos:
            query = query.where('ativo', '==', True)

        # Conta documentos na coleção
        docs = query.stream()
        return sum(1 for _ in docs)

    except Exception as e:
        print(f"Erro ao contar grupos: {e}")
        return 0


def buscar_grupo_por_nome(nome: str) -> Optional[GrupoRelacionamento]:
    """
    Busca um grupo pelo nome (case-insensitive).

    Args:
        nome: Nome do grupo a buscar

    Returns:
        Instância de GrupoRelacionamento ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            return None

        # Busca por nome (case-insensitive)
        nome_normalizado = nome.strip().lower()
        
        docs = db.collection(COLECAO_GRUPOS).where('ativo', '==', True).stream()
        
        for doc in docs:
            dados = doc.to_dict()
            if dados.get('nome', '').strip().lower() == nome_normalizado:
                dados['_id'] = doc.id
                dados = _converter_timestamps(dados)
                return GrupoRelacionamento.from_dict(dados)

        return None

    except Exception as e:
        print(f"Erro ao buscar grupo por nome '{nome}': {e}")
        return None


def contar_pessoas_por_grupo(grupo_id: str) -> int:
    """
    Conta quantas pessoas estão vinculadas a um grupo.

    Args:
        grupo_id: ID do grupo

    Returns:
        Número de pessoas vinculadas ao grupo
    """
    try:
        from .database import listar_pessoas
        pessoas = listar_pessoas()
        return sum(1 for p in pessoas if p.get('grupo_id') == grupo_id)
    except Exception as e:
        print(f"Erro ao contar pessoas do grupo {grupo_id}: {e}")
        return 0


def inicializar_grupo_schmidmeier() -> Optional[str]:
    """
    Inicializa o grupo "Schmidmeier" se não existir.
    Esta função verifica se o grupo já existe antes de criar.

    Returns:
        ID do grupo (existente ou recém-criado) ou None em caso de erro
    """
    try:
        # Verifica se grupo já existe
        grupo_existente = buscar_grupo_por_nome('Schmidmeier')
        if grupo_existente:
            return grupo_existente._id
        
        # Cria grupo se não existir
        grupo_schmidmeier = GrupoRelacionamento(
            nome='Schmidmeier',
            descricao='Grupo empresarial Schmidmeier - Cliente principal',
            icone='🇩🇪',
            cor='#2E7D32',  # Verde escuro
            ativo=True,
        )
        
        grupo_id = criar_grupo(grupo_schmidmeier)
        if grupo_id:
            print(f"Grupo 'Schmidmeier' criado com sucesso (ID: {grupo_id})")
            return grupo_id
        else:
            print("Erro ao criar grupo 'Schmidmeier'")
            return None
            
    except Exception as e:
        print(f"Erro ao inicializar grupo Schmidmeier: {e}")
        import traceback
        traceback.print_exc()
        return None

