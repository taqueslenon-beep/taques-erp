"""
Módulo de validação para o módulo Pessoas.
Centraliza todas as funções de validação de documentos, tipos e dados.
"""
from typing import Optional, Tuple, Dict, Any
from ...core import (
    digits_only, is_valid_cpf, is_valid_cnpj,
    format_cpf, format_cnpj
)
from .models import DEFAULT_CLIENT_TYPE


def normalize_entity_type(value: Optional[str]) -> str:
    """
    Normaliza o tipo de entidade para valores válidos.
    
    Args:
        value: Valor a normalizar
        
    Returns:
        Tipo normalizado: 'PF', 'PJ' ou 'Órgão Público'
    """
    if not value:
        return 'PF'
    if isinstance(value, str) and value.upper() == 'ÓRGÃO PÚBLICO':
        return 'Órgão Público'
    return value


def extract_client_documents(client: Dict[str, Any]) -> Tuple[str, str]:
    """
    Extrai CPF e CNPJ de um cliente, tratando campos legados.
    
    Args:
        client: Dicionário com dados do cliente
        
    Returns:
        Tupla (cpf_digits, cnpj_digits) com apenas dígitos
    """
    cpf_digits = digits_only(client.get('cpf'))
    cnpj_digits = digits_only(client.get('cnpj'))
    raw_display = client.get('cpf_cnpj') or client.get('document', '')
    parts = [p.strip() for p in raw_display.split(' / ') if p.strip()]
    for part in parts:
        part_digits = digits_only(part)
        if len(part_digits) == 11 and not cpf_digits:
            cpf_digits = part_digits
        elif len(part_digits) == 14 and not cnpj_digits:
            cnpj_digits = part_digits
    return cpf_digits, cnpj_digits


def validate_client_documents(
    selected_type: Optional[str],
    cpf_value: Optional[str],
    cnpj_value: Optional[str]
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Valida documentos de cliente baseado no tipo selecionado.
    
    Args:
        selected_type: Tipo do cliente ('PF' ou 'PJ')
        cpf_value: Valor do CPF informado
        cnpj_value: Valor do CNPJ informado
        
    Returns:
        Tupla (client_type, cpf_digits, cnpj_digits, error_message)
        Se houver erro, retorna (None, None, None, mensagem)
    """
    client_type = selected_type or DEFAULT_CLIENT_TYPE
    cpf_digits = digits_only(cpf_value)
    cnpj_digits = digits_only(cnpj_value)
    
    if client_type == 'PF':
        if not cpf_digits or not is_valid_cpf(cpf_digits):
            return None, None, None, 'Informe um CPF válido.'
        return client_type, cpf_digits, '', None

    if client_type == 'PJ':
        if not cnpj_digits or not is_valid_cnpj(cnpj_digits):
            return None, None, None, 'Informe um CNPJ válido.'
        return client_type, '', cnpj_digits, None

    # Qualquer outro tipo é inválido após simplificação
    return None, None, None, 'Tipo de cliente inválido.'


def normalize_client_type_for_display(client: Dict[str, Any]) -> str:
    """
    Normaliza o tipo do cliente para exibição, tratando casos legados e ausentes.
    
    Args:
        client: Dicionário com dados do cliente
        
    Returns:
        Tipo normalizado: 'PF' ou 'PJ'
    """
    client_type = client.get('client_type')
    
    # Se já é PF ou PJ válido, retorna
    if client_type in ['PF', 'PJ']:
        return client_type
    
    # Se é tipo legado PF/PJ, tenta inferir pelo documento
    if client_type == 'PF/PJ':
        cpf_digits = digits_only(client.get('cpf') or client.get('cpf_cnpj') or client.get('document', ''))
        cnpj_digits = digits_only(client.get('cnpj') or client.get('cpf_cnpj') or client.get('document', ''))
        # Se tem CNPJ, prioriza PJ; senão PF
        if len(cnpj_digits) == 14:
            return 'PJ'
        elif len(cpf_digits) == 11:
            return 'PF'
        # Se não consegue inferir, assume PF por padrão
        return 'PF'
    
    # Se não tem tipo definido, tenta inferir pelos documentos
    cpf_digits = digits_only(client.get('cpf') or client.get('cpf_cnpj') or client.get('document', ''))
    cnpj_digits = digits_only(client.get('cnpj') or client.get('cpf_cnpj') or client.get('document', ''))
    
    if len(cnpj_digits) == 14:
        return 'PJ'
    elif len(cpf_digits) == 11:
        return 'PF'
    
    # Se não consegue inferir, assume PF por padrão
    return 'PF'


def validate_partner(partner_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Valida dados de um sócio.
    
    Args:
        partner_data: Dicionário com dados do sócio
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if not partner_data.get('full_name'):
        return False, 'Nome do sócio é obrigatório.'
    
    # Validação de participação (opcional, mas se informada deve ser numérica)
    share = partner_data.get('share', '').strip()
    if share:
        try:
            share_float = float(share)
            if share_float < 0 or share_float > 100:
                return False, 'Participação deve estar entre 0% e 100%.'
        except ValueError:
            return False, 'Participação deve ser um número válido.'
    
    return True, None


def validate_bond(bond_data: Dict[str, Any], client_name: str) -> Tuple[bool, Optional[str]]:
    """
    Valida dados de um vínculo.
    
    Args:
        bond_data: Dicionário com dados do vínculo
        client_name: Nome do cliente que está criando o vínculo
        
    Returns:
        Tupla (is_valid, error_message)
    """
    person_name = bond_data.get('person', '')
    bond_type = bond_data.get('type', '')
    
    if not person_name:
        return False, 'Pessoa é obrigatória.'
    
    if not bond_type:
        return False, 'Tipo de vínculo é obrigatório.'
    
    # Remove prefixos [C] ou [PC] para comparação
    clean_person_name = person_name
    if person_name.startswith('[C] '):
        clean_person_name = person_name[4:]
    elif person_name.startswith('[PC] '):
        clean_person_name = person_name[5:]
    
    if clean_person_name == client_name:
        return False, 'Não é possível vincular a si mesmo!'
    
    return True, None


def validate_email(email: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Valida formato de email (validação básica).
    
    Args:
        email: Email a validar
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if not email or not email.strip():
        return True, None  # Email é opcional
    
    email = email.strip()
    if '@' not in email or '.' not in email.split('@')[-1]:
        return False, 'Email inválido.'
    
    return True, None


def validate_phone(phone: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Valida formato de telefone (validação básica).
    
    Args:
        phone: Telefone a validar
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if not phone or not phone.strip():
        return True, None  # Telefone é opcional
    
    phone_digits = digits_only(phone)
    # Telefone deve ter pelo menos 10 dígitos (com DDD)
    if len(phone_digits) < 10:
        return False, 'Telefone deve ter pelo menos 10 dígitos.'
    
    return True, None


def format_client_document_for_display(client: Dict[str, Any]) -> str:
    """
    Formata documento do cliente para exibição.
    
    Args:
        client: Dicionário com dados do cliente
        
    Returns:
        String formatada com CPF/CNPJ
    """
    cpf_digits, cnpj_digits = extract_client_documents(client)
    
    parts = []
    if cpf_digits:
        parts.append(format_cpf(cpf_digits))
    if cnpj_digits:
        parts.append(format_cnpj(cnpj_digits))
    
    if parts:
        return ' / '.join(parts)
    
    # Fallback para campos legados
    return client.get('cpf_cnpj') or client.get('document', '')

