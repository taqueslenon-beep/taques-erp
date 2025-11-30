"""
business_logic.py - Lógica de negócio para o módulo de Acordos.

Este módulo contém:
- Validações de dados
- Geração de IDs únicos
- Formatação de datas
- Cálculos básicos
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import uuid
import re

from .models import STATUS_OPTIONS, STATUS_RASCUNHO


# =============================================================================
# VALIDAÇÕES
# =============================================================================

def validate_acordo(acordo_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida dados de um acordo antes de salvar.
    
    Args:
        acordo_data: Dicionário com dados do acordo
    
    Returns:
        Tupla (is_valid, error_message)
    """
    # Valida título
    titulo = acordo_data.get('titulo', '').strip()
    if not titulo:
        return False, 'Título do acordo é obrigatório!'
    
    # Valida casos vinculados (obrigatório)
    casos_vinculados = acordo_data.get('casos_vinculados', [])
    if not casos_vinculados or len(casos_vinculados) == 0:
        return False, 'Selecione pelo menos um caso vinculado!'
    
    # Valida processos vinculados (obrigatório)
    processos_vinculados = acordo_data.get('processos_vinculados', [])
    if not processos_vinculados or len(processos_vinculados) == 0:
        return False, 'Selecione pelo menos um processo vinculado!'
    
    # Valida data de celebração
    data_celebracao = acordo_data.get('data_celebracao')
    if data_celebracao:
        if not validate_date_iso_format(data_celebracao):
            return False, 'Data de celebração inválida! Use o formato YYYY-MM-DD.'
    
    # Valida clientes (obrigatório - múltiplo, mínimo 1)
    clientes_ids = acordo_data.get('clientes_ids', [])
    if not clientes_ids or len(clientes_ids) == 0:
        # Fallback para campo antigo (compatibilidade)
        cliente_id = acordo_data.get('cliente_id')
        if not cliente_id:
            return False, 'Selecione pelo menos um cliente!'
        clientes_ids = [cliente_id]
    
    # Valida parte contrária (obrigatório)
    parte_contraria = acordo_data.get('parte_contraria')
    if not parte_contraria:
        # Fallback para campo antigo (compatibilidade)
        parte_contraria = acordo_data.get('outra_parte')
        if not parte_contraria:
            return False, 'Selecione uma parte contrária!'
    
    # Valida que parte contrária não está entre os clientes
    if parte_contraria in clientes_ids:
        return False, 'Parte contrária não pode estar entre os clientes!'
    
    # Valida outros envolvidos (opcional, mas não podem ser clientes ou parte contrária)
    outros_envolvidos = acordo_data.get('outros_envolvidos', [])
    if outros_envolvidos:
        # Verifica duplicatas
        if parte_contraria in outros_envolvidos:
            return False, 'Parte contrária não pode estar entre os outros envolvidos!'
        # Verifica se algum envolvido está nos clientes
        for envolvido in outros_envolvidos:
            if envolvido in clientes_ids:
                return False, f'Outro envolvido não pode estar entre os clientes!'
    
    # Valida que IDs existem (validação básica - IDs não vazios)
    if not all(clientes_ids):
        return False, 'Um ou mais clientes selecionados são inválidos!'
    
    if not parte_contraria or not parte_contraria.strip():
        return False, 'Parte contrária selecionada é inválida!'
    
    # Valida status
    status = acordo_data.get('status', STATUS_RASCUNHO)
    if status not in STATUS_OPTIONS:
        return False, f'Status inválido! Use um dos seguintes: {", ".join(STATUS_OPTIONS)}'
    
    # Valida valor (se fornecido, deve ser numérico positivo)
    valor = acordo_data.get('valor')
    if valor is not None:
        try:
            valor_float = float(valor)
            if valor_float < 0:
                return False, 'Valor do acordo não pode ser negativo!'
        except (ValueError, TypeError):
            return False, 'Valor do acordo deve ser um número!'
    
    return True, ''


def validate_date_iso_format(date_str: str) -> bool:
    """
    Valida se a data está no formato ISO (YYYY-MM-DD).
    
    Args:
        date_str: String com a data
    
    Returns:
        True se válida, False caso contrário
    """
    if not date_str:
        return False
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, AttributeError):
        return False


def validate_date_format(date_str: str) -> bool:
    """
    Valida se a data está no formato DD/MM/AAAA.
    
    Args:
        date_str: String com a data
    
    Returns:
        True se válida, False caso contrário
    """
    if not date_str:
        return False
    
    # Verifica formato DD/MM/AAAA
    pattern = r'^\d{2}/\d{2}/\d{4}$'
    if not re.match(pattern, date_str):
        return False
    
    # Valida valores da data
    try:
        day, month, year = map(int, date_str.split('/'))
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        if year < 1900 or year > 2100:
            return False
        # Validação básica de dias por mês
        days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if day > days_in_month[month - 1]:
            return False
        return True
    except (ValueError, IndexError):
        return False


# =============================================================================
# GERAÇÃO DE IDs
# =============================================================================

def generate_acordo_id() -> str:
    """
    Gera um ID único para um acordo.
    
    Returns:
        String com ID único (UUID)
    """
    return str(uuid.uuid4())


# =============================================================================
# FORMATAÇÃO DE DATAS
# =============================================================================

def format_date_br(date_str: Optional[str] = None) -> str:
    """
    Formata datas para padrão brasileiro (DD/MM/AAAA).
    
    Args:
        date_str: Data em formato ISO ou DD/MM/AAAA
    
    Returns:
        Data formatada ou '-' se inválida
    """
    if not date_str:
        return '-'
    
    # Se já está no formato DD/MM/AAAA, retorna como está
    if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        return date_str
    
    # Tenta converter de ISO
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y')
    except (ValueError, AttributeError):
        pass
    
    # Tenta converter de formato YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except (ValueError, AttributeError):
        pass
    
    return date_str


def format_currency(value: Optional[float]) -> str:
    """
    Formata valor monetário para exibição (R$ X.XXX,XX).
    
    Args:
        value: Valor numérico
    
    Returns:
        String formatada ou '-' se None
    """
    if value is None:
        return '-'
    
    try:
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return '-'


# =============================================================================
# CÁLCULOS BÁSICOS
# =============================================================================

def calculate_total_value(acordos: list) -> float:
    """
    Calcula o valor total de uma lista de acordos.
    
    Args:
        acordos: Lista de dicionários de acordos
    
    Returns:
        Soma dos valores dos acordos
    """
    total = 0.0
    for acordo in acordos:
        valor = acordo.get('valor')
        if valor is not None:
            try:
                total += float(valor)
            except (ValueError, TypeError):
                pass
    return total


# =============================================================================
# VALIDAÇÕES DE CLÁUSULAS
# =============================================================================

def validar_clausula(clausula_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida dados de uma cláusula antes de salvar.
    
    Validações obrigatórias sempre:
    - Tipo de cláusula
    - Título
    - Status
    
    Validações condicionais:
    - Se status = "Cumprida": descrição de comprovação é obrigatória
    
    Validações opcionais (se preenchidos):
    - Prazos: se ambos preenchidos, prazo fatal deve ser após prazo de segurança
    - Link de comprovação: se preenchido, deve ser URL válida
    
    Args:
        clausula_data: Dicionário com dados da cláusula
    
    Returns:
        Tupla (is_valid, error_message)
    """
    from .models import CLAUSULA_STATUS_OPTIONS, CLAUSULA_TIPO_OPTIONS, CLAUSULA_STATUS_CUMPRIDA
    
    # Valida tipo de cláusula (obrigatório)
    tipo_clausula = clausula_data.get('tipo_clausula', '').strip()
    if not tipo_clausula:
        return False, 'Tipo de Cláusula é obrigatório!'
    if tipo_clausula not in CLAUSULA_TIPO_OPTIONS:
        return False, f'Tipo de Cláusula inválido! Use um dos seguintes: {", ".join(CLAUSULA_TIPO_OPTIONS)}'
    
    # Valida título (obrigatório)
    titulo = clausula_data.get('titulo', '').strip()
    if not titulo:
        return False, 'Título da cláusula é obrigatório!'
    if len(titulo) < 3:
        return False, 'Título da cláusula deve ter pelo menos 3 caracteres!'
    if len(titulo) > 200:
        return False, 'Título da cláusula deve ter no máximo 200 caracteres!'
    
    # Valida status (obrigatório)
    status = clausula_data.get('status', '').strip()
    if not status:
        return False, 'Selecione um status!'
    if status not in CLAUSULA_STATUS_OPTIONS:
        return False, f'Status inválido! Use um dos seguintes: {", ".join(CLAUSULA_STATUS_OPTIONS)}'
    
    # Validação condicional: se status = "Cumprida", descrição de comprovação é obrigatória
    if status == CLAUSULA_STATUS_CUMPRIDA:
        descricao_comprovacao = clausula_data.get('descricao_comprovacao', '').strip()
        if not descricao_comprovacao:
            return False, 'Descrição de Comprovação é obrigatória para cláusulas cumpridas!'
        if len(descricao_comprovacao) > 1000:
            return False, 'Descrição de Comprovação deve ter no máximo 1000 caracteres!'
        
        # Valida link de comprovação se preenchido
        link_comprovacao = clausula_data.get('link_comprovacao', '').strip()
        if link_comprovacao:
            if len(link_comprovacao) > 500:
                return False, 'Link de Comprovação deve ter no máximo 500 caracteres!'
            if not eh_url_valida(link_comprovacao):
                return False, 'Link de Comprovação deve ser uma URL válida (ex: https://exemplo.com)'
    
    # Valida prazos (opcionais, mas se ambos preenchidos, validar lógica)
    prazo_seguranca = clausula_data.get('prazo_seguranca', '').strip()
    prazo_fatal = clausula_data.get('prazo_fatal', '').strip()
    
    # Se ambos prazos preenchidos, validar formato e lógica
    if prazo_seguranca and prazo_fatal:
        try:
            # Tenta DD/MM/AAAA primeiro
            if '/' in prazo_seguranca:
                dt_seg = datetime.strptime(prazo_seguranca, '%d/%m/%Y')
            else:
                dt_seg = datetime.strptime(prazo_seguranca, '%Y-%m-%d')
            
            if '/' in prazo_fatal:
                dt_fatal = datetime.strptime(prazo_fatal, '%d/%m/%Y')
            else:
                dt_fatal = datetime.strptime(prazo_fatal, '%Y-%m-%d')
            
            # Valida que prazo fatal é após prazo de segurança
            if dt_fatal <= dt_seg:
                return False, 'Prazo fatal deve ser após prazo de segurança!'
        except ValueError:
            return False, 'Data inválida! Use o formato DD/MM/AAAA ou YYYY-MM-DD.'
    # Se apenas um prazo preenchido, validar formato
    elif prazo_seguranca:
        try:
            if '/' in prazo_seguranca:
                datetime.strptime(prazo_seguranca, '%d/%m/%Y')
            else:
                datetime.strptime(prazo_seguranca, '%Y-%m-%d')
        except ValueError:
            return False, 'Prazo de Segurança inválido! Use o formato DD/MM/AAAA ou YYYY-MM-DD.'
    elif prazo_fatal:
        try:
            if '/' in prazo_fatal:
                datetime.strptime(prazo_fatal, '%d/%m/%Y')
            else:
                datetime.strptime(prazo_fatal, '%Y-%m-%d')
        except ValueError:
            return False, 'Prazo Fatal inválido! Use o formato DD/MM/AAAA ou YYYY-MM-DD.'
    
    return True, ''


def eh_url_valida(url: str) -> bool:
    """
    Valida se uma string é uma URL válida.
    
    Args:
        url: String a validar
    
    Returns:
        True se for URL válida, False caso contrário
    """
    import re
    # Padrão básico: deve começar com http:// ou https:// e ter pelo menos um caractere após
    padrao = r'^https?://.+'
    return bool(re.match(padrao, url))


def formatar_data_para_exibicao(data: str) -> str:
    """
    Formata data de YYYY-MM-DD para DD/MM/AAAA para exibição.
    
    Args:
        data: Data em formato YYYY-MM-DD ou DD/MM/AAAA
    
    Returns:
        Data formatada em DD/MM/AAAA ou string original se inválida
    """
    if not data:
        return '-'
    
    # Se já está em DD/MM/AAAA, retorna como está
    if '/' in data and len(data) == 10:
        try:
            datetime.strptime(data, '%d/%m/%Y')
            return data
        except ValueError:
            pass
    
    # Tenta converter de YYYY-MM-DD
    try:
        dt = datetime.strptime(data, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        pass
    
    return data


def formatar_data_para_iso(data_br: str) -> str:
    """
    Converte data de formato brasileiro (DD/MM/AAAA) para ISO (YYYY-MM-DD).
    
    Args:
        data_br: Data em formato DD/MM/AAAA
    
    Returns:
        Data em formato YYYY-MM-DD ou string vazia se inválida
    """
    if not data_br or not data_br.strip():
        return ''
    
    data_br = data_br.strip()
    
    # Se já está em formato ISO, retorna como está
    if re.match(r'^\d{4}-\d{2}-\d{2}$', data_br):
        return data_br
    
    # Tenta converter de DD/MM/AAAA
    try:
        dt = datetime.strptime(data_br, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return ''


def validate_tipo_clausula(valor: str) -> Tuple[bool, str]:
    """
    Valida o tipo de cláusula.
    
    Args:
        valor: Tipo de cláusula (deve ser "Geral" ou "Específica")
    
    Returns:
        Tupla (is_valid, error_message)
    """
    from .models import CLAUSULA_TIPO_OPTIONS
    
    if not valor or not valor.strip():
        return False, 'Tipo de Cláusula é obrigatório!'
    
    valor = valor.strip()
    if valor not in CLAUSULA_TIPO_OPTIONS:
        return False, f'Tipo de Cláusula inválido! Use um dos seguintes: {", ".join(CLAUSULA_TIPO_OPTIONS)}'
    
    return True, ''


def validate_titulo_clausula(valor: str) -> Tuple[bool, str]:
    """
    Valida o título da cláusula.
    
    Args:
        valor: Título da cláusula
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if not valor or not valor.strip():
        return False, 'Título da Cláusula é obrigatório!'
    
    titulo = valor.strip()
    if len(titulo) < 3:
        return False, 'Título da Cláusula deve ter pelo menos 3 caracteres!'
    
    if len(titulo) > 200:
        return False, 'Título da Cláusula deve ter no máximo 200 caracteres!'
    
    return True, ''


def validate_datas_clausula(prazo_seg: Optional[str], prazo_fatal: Optional[str]) -> Tuple[bool, str]:
    """
    Valida os prazos da cláusula (formato e lógica).
    
    Args:
        prazo_seg: Prazo de segurança (DD/MM/AAAA ou YYYY-MM-DD)
        prazo_fatal: Prazo fatal (DD/MM/AAAA ou YYYY-MM-DD)
    
    Returns:
        Tupla (is_valid, error_message)
    """
    # Se ambos preenchidos, validar formato e lógica
    if prazo_seg and prazo_fatal:
        prazo_seg = prazo_seg.strip()
        prazo_fatal = prazo_fatal.strip()
        
        try:
            # Tenta DD/MM/AAAA primeiro
            if '/' in prazo_seg:
                dt_seg = datetime.strptime(prazo_seg, '%d/%m/%Y')
            else:
                dt_seg = datetime.strptime(prazo_seg, '%Y-%m-%d')
            
            if '/' in prazo_fatal:
                dt_fatal = datetime.strptime(prazo_fatal, '%d/%m/%Y')
            else:
                dt_fatal = datetime.strptime(prazo_fatal, '%Y-%m-%d')
            
            # Valida que prazo fatal é após prazo de segurança
            if dt_fatal <= dt_seg:
                return False, 'Prazo fatal deve ser após prazo de segurança!'
        except ValueError:
            return False, 'Data inválida! Use o formato DD/MM/AAAA ou YYYY-MM-DD.'
    
    # Se apenas um prazo preenchido, validar formato
    elif prazo_seg:
        prazo_seg = prazo_seg.strip()
        try:
            if '/' in prazo_seg:
                datetime.strptime(prazo_seg, '%d/%m/%Y')
            else:
                datetime.strptime(prazo_seg, '%Y-%m-%d')
        except ValueError:
            return False, 'Prazo de Segurança inválido! Use o formato DD/MM/AAAA ou YYYY-MM-DD.'
    
    elif prazo_fatal:
        prazo_fatal = prazo_fatal.strip()
        try:
            if '/' in prazo_fatal:
                datetime.strptime(prazo_fatal, '%d/%m/%Y')
            else:
                datetime.strptime(prazo_fatal, '%Y-%m-%d')
        except ValueError:
            return False, 'Prazo Fatal inválido! Use o formato DD/MM/AAAA ou YYYY-MM-DD.'
    
    return True, ''


def validate_comprovacao(status: str, descricao: Optional[str], link: Optional[str]) -> Tuple[bool, str]:
    """
    Valida campos de comprovação quando status = "Cumprida".
    
    Args:
        status: Status da cláusula
        descricao: Descrição de comprovação
        link: Link de comprovação
    
    Returns:
        Tupla (is_valid, error_message)
    """
    from .models import CLAUSULA_STATUS_CUMPRIDA
    
    # Se status não é "Cumprida", não precisa validar
    if status != CLAUSULA_STATUS_CUMPRIDA:
        return True, ''
    
    # Se status é "Cumprida", descrição é obrigatória
    if not descricao or not descricao.strip():
        return False, 'Descrição de Comprovação é obrigatória para cláusulas cumpridas!'
    
    descricao = descricao.strip()
    if len(descricao) > 1000:
        return False, 'Descrição de Comprovação deve ter no máximo 1000 caracteres!'
    
    # Valida link se preenchido
    if link and link.strip():
        link = link.strip()
        if len(link) > 500:
            return False, 'Link de Comprovação deve ter no máximo 500 caracteres!'
        if not eh_url_valida(link):
            return False, 'Link de Comprovação deve ser uma URL válida (ex: https://exemplo.com)'
    
    return True, ''

