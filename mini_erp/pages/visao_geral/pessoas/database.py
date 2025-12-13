"""
Módulo de acesso a dados para Pessoas do workspace Visão Geral.
Usa coleção Firebase separada: vg_pessoas
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ....firebase_config import get_db

# Nome da coleção Firebase para este workspace
COLECAO_PESSOAS = 'vg_pessoas'
COLECAO_ENVOLVIDOS = 'vg_envolvidos'
COLECAO_PARCEIROS = 'vg_parceiros'


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


def listar_pessoas() -> List[Dict[str, Any]]:
    """
    Retorna todas as pessoas da coleção vg_pessoas.

    Returns:
        Lista de dicionários com dados das pessoas
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        docs = db.collection(COLECAO_PESSOAS).stream()
        pessoas = []

        for doc in docs:
            pessoa = doc.to_dict()
            pessoa['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            pessoa = _converter_timestamps(pessoa)
            pessoas.append(pessoa)

        # Ordena por nome de exibição (ou nome completo se não houver)
        pessoas.sort(key=lambda p: (p.get('nome_exibicao') or p.get('full_name') or '').lower())

        return pessoas

    except Exception as e:
        print(f"Erro ao listar pessoas: {e}")
        return []


def buscar_pessoa(pessoa_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma pessoa específica pelo ID.

    Args:
        pessoa_id: ID do documento no Firebase

    Returns:
        Dicionário com dados da pessoa ou None se não encontrada
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_PESSOAS).document(pessoa_id).get()

        if doc.exists:
            pessoa = doc.to_dict()
            pessoa['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            pessoa = _converter_timestamps(pessoa)
            return pessoa

        return None

    except Exception as e:
        print(f"Erro ao buscar pessoa {pessoa_id}: {e}")
        return None


def criar_pessoa(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria uma nova pessoa na coleção.

    Args:
        dados: Dicionário com dados da pessoa

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

        # Remove _id se existir (será gerado pelo Firebase)
        dados.pop('_id', None)

        # Cria documento
        doc_ref = db.collection(COLECAO_PESSOAS).add(dados)

        # Retorna o ID do documento criado
        return doc_ref[1].id

    except Exception as e:
        print(f"Erro ao criar pessoa: {e}")
        return None


def atualizar_pessoa(pessoa_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza uma pessoa existente.

    Args:
        pessoa_id: ID do documento no Firebase
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

        # Atualiza documento
        db.collection(COLECAO_PESSOAS).document(pessoa_id).update(dados)

        return True

    except Exception as e:
        print(f"Erro ao atualizar pessoa {pessoa_id}: {e}")
        return False


def excluir_pessoa(pessoa_id: str) -> bool:
    """
    Remove uma pessoa da coleção.

    Args:
        pessoa_id: ID do documento no Firebase

    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        db.collection(COLECAO_PESSOAS).document(pessoa_id).delete()

        return True

    except Exception as e:
        print(f"Erro ao excluir pessoa {pessoa_id}: {e}")
        return False


def buscar_pessoa_por_documento(cpf_cnpj: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma pessoa pelo CPF ou CNPJ.

    Args:
        cpf_cnpj: CPF ou CNPJ (apenas dígitos)

    Returns:
        Dicionário com dados da pessoa ou None se não encontrada
    """
    try:
        db = get_db()
        if not db:
            return None

        # Remove formatação do documento
        documento_limpo = ''.join(filter(str.isdigit, cpf_cnpj))

        # Busca por CPF
        docs = db.collection(COLECAO_PESSOAS).where('cpf', '==', documento_limpo).limit(1).stream()
        for doc in docs:
            pessoa = doc.to_dict()
            pessoa['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            pessoa = _converter_timestamps(pessoa)
            return pessoa

        # Busca por CNPJ
        docs = db.collection(COLECAO_PESSOAS).where('cnpj', '==', documento_limpo).limit(1).stream()
        for doc in docs:
            pessoa = doc.to_dict()
            pessoa['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            pessoa = _converter_timestamps(pessoa)
            return pessoa

        return None

    except Exception as e:
        print(f"Erro ao buscar pessoa por documento: {e}")
        return None


def contar_pessoas() -> int:
    """
    Retorna o total de pessoas cadastradas.

    Returns:
        Número total de pessoas
    """
    try:
        db = get_db()
        if not db:
            return 0

        # Conta documentos na coleção
        docs = db.collection(COLECAO_PESSOAS).stream()
        return sum(1 for _ in docs)

    except Exception as e:
        print(f"Erro ao contar pessoas: {e}")
        return 0


def listar_pessoas_colecao_people() -> List[Dict[str, Any]]:
    """
    Retorna todas as pessoas da coleção 'people' (principal do sistema).
    Usada para vincular clientes aos casos.

    Returns:
        Lista de dicionários com dados das pessoas
    """
    try:
        db = get_db()
        if not db:
            print("[ERRO] Conexão com Firebase não disponível")
            return []

        docs = db.collection('people').stream()
        pessoas = []

        for doc in docs:
            pessoa = doc.to_dict()
            pessoa['_id'] = doc.id

            # Monta nome de exibição
            nome = pessoa.get('name') or pessoa.get('full_name') or pessoa.get('display_name', '')
            apelido = pessoa.get('nickname', '')

            if not nome:
                continue

            # Formato para exibição
            if apelido and apelido != nome:
                nome_exibicao = f"{nome} ({apelido})"
            else:
                nome_exibicao = nome

            pessoa['nome_exibicao'] = nome_exibicao

            # Converte timestamps para evitar erro de serialização JSON
            pessoa = _converter_timestamps(pessoa)
            pessoas.append(pessoa)

        # Ordena alfabeticamente
        pessoas.sort(key=lambda p: (p.get('nome_exibicao') or '').upper())

        print(f"[PESSOAS] {len(pessoas)} pessoas carregadas da coleção 'people'")
        return pessoas

    except Exception as e:
        print(f"[ERRO] Falha ao listar pessoas da coleção 'people': {e}")
        import traceback
        traceback.print_exc()
        return []


# =============================================================================
# FUNÇÕES CRUD PARA OUTROS ENVOLVIDOS
# =============================================================================


def listar_envolvidos() -> List[Dict[str, Any]]:
    """
    Retorna todos os envolvidos da coleção vg_envolvidos.

    Returns:
        Lista de dicionários com dados dos envolvidos
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        docs = db.collection(COLECAO_ENVOLVIDOS).stream()
        envolvidos = []

        for doc in docs:
            envolvido = doc.to_dict()
            envolvido['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            envolvido = _converter_timestamps(envolvido)
            envolvidos.append(envolvido)

        # Ordena por nome de exibição (ou nome completo se não houver)
        envolvidos.sort(key=lambda e: (e.get('nome_exibicao') or e.get('nome_completo') or '').lower())

        return envolvidos

    except Exception as e:
        print(f"Erro ao listar envolvidos: {e}")
        return []


def buscar_envolvido(envolvido_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um envolvido específico pelo ID.

    Args:
        envolvido_id: ID do documento no Firebase

    Returns:
        Dicionário com dados do envolvido ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_ENVOLVIDOS).document(envolvido_id).get()

        if doc.exists:
            envolvido = doc.to_dict()
            envolvido['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            envolvido = _converter_timestamps(envolvido)
            return envolvido

        return None

    except Exception as e:
        print(f"Erro ao buscar envolvido {envolvido_id}: {e}")
        return None


def criar_envolvido(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria um novo envolvido na coleção.

    Args:
        dados: Dicionário com dados do envolvido

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

        # Garante que tipo_envolvido tenha um valor padrão se não fornecido
        if 'tipo_envolvido' not in dados or not dados.get('tipo_envolvido'):
            dados['tipo_envolvido'] = 'PF'

        # Remove _id se existir (será gerado pelo Firebase)
        dados.pop('_id', None)

        # Cria documento
        doc_ref = db.collection(COLECAO_ENVOLVIDOS).add(dados)

        # Retorna o ID do documento criado
        return doc_ref[1].id

    except Exception as e:
        print(f"Erro ao criar envolvido: {e}")
        return None


def atualizar_envolvido(envolvido_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza um envolvido existente.

    Args:
        envolvido_id: ID do documento no Firebase
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

        # Atualiza documento
        db.collection(COLECAO_ENVOLVIDOS).document(envolvido_id).update(dados)

        return True

    except Exception as e:
        print(f"Erro ao atualizar envolvido {envolvido_id}: {e}")
        return False


def excluir_envolvido(envolvido_id: str) -> bool:
    """
    Remove um envolvido da coleção.

    Args:
        envolvido_id: ID do documento no Firebase

    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        db.collection(COLECAO_ENVOLVIDOS).document(envolvido_id).delete()

        return True

    except Exception as e:
        print(f"Erro ao excluir envolvido {envolvido_id}: {e}")
        return False


def contar_envolvidos() -> int:
    """
    Retorna o total de envolvidos cadastrados.

    Returns:
        Número total de envolvidos
    """
    try:
        db = get_db()
        if not db:
            return 0

        # Conta documentos na coleção
        docs = db.collection(COLECAO_ENVOLVIDOS).stream()
        return sum(1 for _ in docs)

    except Exception as e:
        print(f"Erro ao contar envolvidos: {e}")
        return 0


# =============================================================================
# FUNÇÕES CRUD PARA PARCEIROS
# =============================================================================


def listar_parceiros() -> List[Dict[str, Any]]:
    """
    Retorna todos os parceiros da coleção vg_parceiros.

    Returns:
        Lista de dicionários com dados dos parceiros
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return []

        docs = db.collection(COLECAO_PARCEIROS).stream()
        parceiros = []

        for doc in docs:
            parceiro = doc.to_dict()
            parceiro['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            parceiro = _converter_timestamps(parceiro)
            parceiros.append(parceiro)

        # Ordena por nome de exibição (ou nome completo se não houver)
        parceiros.sort(key=lambda p: (p.get('nome_exibicao') or p.get('nome_completo') or '').lower())

        return parceiros

    except Exception as e:
        print(f"Erro ao listar parceiros: {e}")
        return []


def buscar_parceiro(parceiro_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um parceiro específico pelo ID.

    Args:
        parceiro_id: ID do documento no Firebase

    Returns:
        Dicionário com dados do parceiro ou None se não encontrado
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return None

        doc = db.collection(COLECAO_PARCEIROS).document(parceiro_id).get()

        if doc.exists:
            parceiro = doc.to_dict()
            parceiro['_id'] = doc.id
            # Converte timestamps para evitar erro de serialização JSON
            parceiro = _converter_timestamps(parceiro)
            return parceiro

        return None

    except Exception as e:
        print(f"Erro ao buscar parceiro {parceiro_id}: {e}")
        return None


def criar_parceiro(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria um novo parceiro na coleção.

    Args:
        dados: Dicionário com dados do parceiro

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

        # Garante que tipo_parceiro tenha um valor padrão se não fornecido
        if 'tipo_parceiro' not in dados or not dados.get('tipo_parceiro'):
            dados['tipo_parceiro'] = 'PF'

        # Remove _id se existir (será gerado pelo Firebase)
        dados.pop('_id', None)

        # Cria documento
        doc_ref = db.collection(COLECAO_PARCEIROS).add(dados)

        # Retorna o ID do documento criado
        return doc_ref[1].id

    except Exception as e:
        print(f"Erro ao criar parceiro: {e}")
        return None


def atualizar_parceiro(parceiro_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza um parceiro existente.

    Args:
        parceiro_id: ID do documento no Firebase
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

        # Atualiza documento
        db.collection(COLECAO_PARCEIROS).document(parceiro_id).update(dados)

        return True

    except Exception as e:
        print(f"Erro ao atualizar parceiro {parceiro_id}: {e}")
        return False


def excluir_parceiro(parceiro_id: str) -> bool:
    """
    Remove um parceiro da coleção.

    Args:
        parceiro_id: ID do documento no Firebase

    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        if not db:
            print("Erro: Conexão com Firebase não disponível")
            return False

        db.collection(COLECAO_PARCEIROS).document(parceiro_id).delete()

        return True

    except Exception as e:
        print(f"Erro ao excluir parceiro {parceiro_id}: {e}")
        return False


def contar_parceiros() -> int:
    """
    Retorna o total de parceiros cadastrados.

    Returns:
        Número total de parceiros
    """
    try:
        db = get_db()
        if not db:
            return 0

        # Conta documentos na coleção
        docs = db.collection(COLECAO_PARCEIROS).stream()
        return sum(1 for _ in docs)

    except Exception as e:
        print(f"Erro ao contar parceiros: {e}")
        return 0
