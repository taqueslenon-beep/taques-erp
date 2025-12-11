"""
Módulo de modelos e constantes para Pessoas do workspace Visão Geral.
Define tipos de dados, constantes e estruturas usadas no módulo.
"""
from typing import TypedDict, List, Optional, Any

# =============================================================================
# CONSTANTES - TIPOS DE PESSOA
# =============================================================================

# Opções de tipo de pessoa (PF = Pessoa Física, PJ = Pessoa Jurídica)
TIPO_PESSOA_OPTIONS = ['PF', 'PJ']

# Labels para exibição
TIPO_PESSOA_LABELS = {
    'PF': 'Pessoa Física',
    'PJ': 'Pessoa Jurídica',
}

TIPO_PESSOA_PADRAO = 'PF'

# =============================================================================
# CONSTANTES - TIPOS DE FILIAL (para PJ)
# =============================================================================

TIPO_FILIAL_OPTIONS = ['Matriz', 'Filial']

# =============================================================================
# CONSTANTES - TIPOS DE VÍNCULOS
# =============================================================================

TIPOS_VINCULO = [
    'Pai', 'Mãe', 'Filho(a)', 'Irmão(ã)', 'Cônjuge', 'Avô(ó)', 'Neto(a)',
    'Tio(a)', 'Sobrinho(a)', 'Primo(a)', 'Sócio(a)', 'CNPJ relacionado',
    'Representante legal', 'Procurador', 'Outro'
]

# =============================================================================
# TIPOS ESTRUTURADOS (TypedDict)
# =============================================================================


class Socio(TypedDict, total=False):
    """Estrutura de um sócio/proprietário de PJ."""
    full_name: str
    cpf: str
    participacao: str  # Participação societária (%)


class Vinculo(TypedDict, total=False):
    """Estrutura de um vínculo entre pessoas."""
    pessoa_id: str     # ID da pessoa vinculada
    pessoa_nome: str   # Nome da pessoa vinculada
    tipo: str          # Tipo do vínculo (de TIPOS_VINCULO)


class Pessoa(TypedDict, total=False):
    """Estrutura de uma pessoa no sistema."""
    _id: str
    full_name: str           # Nome completo / Razão social
    nome_exibicao: str       # Nome de exibição (obrigatório)
    apelido: str             # Apelido / Nome fantasia
    tipo_pessoa: str         # 'PF' ou 'PJ'

    # Documentos
    cpf: str                 # CPF (apenas dígitos)
    cnpj: str                # CNPJ (apenas dígitos)
    cpf_cnpj_formatado: str  # Documento formatado para exibição

    # Contato
    email: str
    telefone: str
    endereco: str

    # Campos específicos de PJ
    tipo_filial: str         # 'Matriz' ou 'Filial'
    socios: List[Socio]

    # Vínculos com outras pessoas
    vinculos: List[Vinculo]

    # Metadata
    observacoes: str
    created_at: Any
    updated_at: Any


# =============================================================================
# DEFINIÇÕES DE COLUNAS PARA TABELAS
# =============================================================================

COLUNAS_TABELA_PESSOAS = [
    {'name': 'nome_exibicao', 'label': 'Nome de Exibição', 'field': 'nome_exibicao', 'align': 'left', 'sortable': True},
    {'name': 'tipo_pessoa', 'label': 'Tipo', 'field': 'tipo_pessoa', 'align': 'center', 'sortable': True},
    {'name': 'cpf_cnpj', 'label': 'CPF/CNPJ', 'field': 'cpf_cnpj_formatado', 'align': 'left'},
    {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
    {'name': 'telefone', 'label': 'Telefone', 'field': 'telefone', 'align': 'left'},
    {'name': 'actions', 'label': 'Ações', 'field': 'actions', 'align': 'center'},
]

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================


def formatar_cpf(cpf: str) -> str:
    """Formata CPF no padrão 000.000.000-00."""
    if not cpf:
        return ''
    # Remove caracteres não numéricos
    digitos = ''.join(filter(str.isdigit, cpf))
    if len(digitos) != 11:
        return digitos
    return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ no padrão 00.000.000/0000-00."""
    if not cnpj:
        return ''
    # Remove caracteres não numéricos
    digitos = ''.join(filter(str.isdigit, cnpj))
    if len(digitos) != 14:
        return digitos
    return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'


def formatar_documento(pessoa: dict) -> str:
    """Formata CPF ou CNPJ para exibição baseado no tipo de pessoa."""
    tipo = pessoa.get('tipo_pessoa', 'PF')
    if tipo == 'PJ':
        return formatar_cnpj(pessoa.get('cnpj', ''))
    return formatar_cpf(pessoa.get('cpf', ''))


def formatar_telefone(telefone: str) -> str:
    """Formata telefone no padrão brasileiro."""
    if not telefone:
        return ''
    # Remove caracteres não numéricos
    digitos = ''.join(filter(str.isdigit, telefone))
    if len(digitos) == 11:
        return f'({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}'
    elif len(digitos) == 10:
        return f'({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}'
    return telefone


def criar_pessoa_vazia() -> dict:
    """Retorna um dicionário com estrutura padrão de pessoa vazia."""
    return {
        'full_name': '',
        'nome_exibicao': '',
        'apelido': '',
        'tipo_pessoa': TIPO_PESSOA_PADRAO,
        'cpf': '',
        'cnpj': '',
        'email': '',
        'telefone': '',
        'endereco': '',
        'tipo_filial': 'Matriz',
        'socios': [],
        'vinculos': [],
        'observacoes': '',
    }


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO
# =============================================================================


def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF pelos dígitos verificadores.

    Args:
        cpf: CPF a validar (pode ter formatação)

    Returns:
        True se válido, False se inválido
    """
    if not cpf:
        return False

    # Remove formatação
    digitos = ''.join(filter(str.isdigit, cpf))

    # Deve ter 11 dígitos
    if len(digitos) != 11:
        return False

    # Não pode ser sequência repetida
    if len(set(digitos)) == 1:
        return False

    # Calcula primeiro dígito verificador
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto

    if int(digitos[9]) != dv1:
        return False

    # Calcula segundo dígito verificador
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto

    return int(digitos[10]) == dv2


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ pelos dígitos verificadores.

    Args:
        cnpj: CNPJ a validar (pode ter formatação)

    Returns:
        True se válido, False se inválido
    """
    if not cnpj:
        return False

    # Remove formatação
    digitos = ''.join(filter(str.isdigit, cnpj))

    # Deve ter 14 dígitos
    if len(digitos) != 14:
        return False

    # Não pode ser sequência repetida
    if len(set(digitos)) == 1:
        return False

    # Calcula primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(digitos[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto

    if int(digitos[12]) != dv1:
        return False

    # Calcula segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(digitos[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto

    return int(digitos[13]) == dv2


def validar_email(email: str) -> bool:
    """
    Valida formato básico de email.

    Args:
        email: Email a validar

    Returns:
        True se válido, False se inválido
    """
    if not email:
        return True  # Email é opcional

    import re
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))


def extrair_digitos(valor: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    if not valor:
        return ''
    return ''.join(filter(str.isdigit, valor))


def validar_pessoa(dados: dict) -> tuple:
    """
    Valida os dados de uma pessoa antes de salvar.

    Args:
        dados: Dicionário com dados da pessoa

    Returns:
        Tupla (valido: bool, mensagem_erro: str ou None)
    """
    # Nome completo obrigatório
    full_name = dados.get('full_name', '').strip()
    if not full_name:
        return False, 'Nome completo é obrigatório.'

    if len(full_name) < 3:
        return False, 'Nome completo deve ter pelo menos 3 caracteres.'

    # Nome de exibição obrigatório
    nome_exibicao = dados.get('nome_exibicao', '').strip()
    if not nome_exibicao:
        return False, 'Nome de exibição é obrigatório.'

    # Tipo de pessoa
    tipo_pessoa = dados.get('tipo_pessoa', 'PF')
    if tipo_pessoa not in TIPO_PESSOA_OPTIONS:
        return False, 'Tipo de pessoa inválido.'

    # Validação de documento baseada no tipo
    if tipo_pessoa == 'PF':
        cpf = dados.get('cpf', '')
        if cpf and not validar_cpf(cpf):
            return False, 'CPF inválido.'
    else:  # PJ
        cnpj = dados.get('cnpj', '')
        if cnpj and not validar_cnpj(cnpj):
            return False, 'CNPJ inválido.'

    # Validação de email
    email = dados.get('email', '')
    if email and not validar_email(email):
        return False, 'Email inválido.'

    return True, None
