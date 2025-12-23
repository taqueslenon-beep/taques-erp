"""
Funções auxiliares para o modal de processo (Visão Geral).
"""
from typing import List, Dict, Any, Optional, Tuple
from mini_erp.core import get_display_name


def make_required_label(text: str) -> str:
    """Adiciona asterisco ao final do label para campos obrigatórios."""
    return f'{text} *'


def get_short_name(full_name: str, source_list: List[Dict[str, Any]]) -> str:
    """
    Retorna nome curto para exibição em chips/badges.
    Busca o display_name da pessoa ou retorna o valor original.
    """
    if not full_name:
        return ''
    
    # Busca na lista fonte se disponível
    if source_list:
        for item in source_list:
            item_display = get_display_name(item)
            item_full = item.get('full_name', '') or item.get('name', '') or item.get('nome_completo', '')
            item_nome_exib = item.get('nome_exibicao', '')
            
            # Se encontrar correspondência, retorna o display_name
            if full_name in [item_display, item_full, item_nome_exib]:
                return item_display if item_display else full_name
    
    # Fallback: retorna o valor original (já é o display_name)
    return full_name


def format_option_for_search(item: Dict[str, Any]) -> str:
    """
    Formata opção para exibição no dropdown.
    Retorna apenas o nome de exibição (display_name) para manter a interface limpa.
    """
    # Obtém nome de exibição/apelido (prioridade do get_display_name)
    display_name = get_display_name(item)
    
    if display_name:
        return display_name
    
    # Fallback para outros campos
    return (item.get('nome_exibicao', '') or 
            item.get('nome_completo', '') or 
            item.get('full_name', '') or
            item.get('name', '') or 
            'Sem nome')


def get_option_value(formatted_option: str, source_list: List[Dict[str, Any]]) -> str:
    """Extrai o nome completo de uma opção formatada."""
    if '(' in formatted_option:
        return formatted_option.split(' (')[0]
    return formatted_option


def find_person_by_option(option_value: str, source_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Encontra uma pessoa na lista baseado no valor selecionado (display_name).
    
    Args:
        option_value: Valor selecionado no dropdown (display_name)
        source_list: Lista de pessoas para buscar
        
    Returns:
        Dicionário da pessoa encontrada ou None
    """
    if not option_value or not source_list:
        return None
    
    option_lower = option_value.strip().lower()
    
    for item in source_list:
        # Compara com display_name
        item_display = get_display_name(item).lower()
        if option_lower == item_display:
            return item
        
        # Compara com outros campos
        item_full = (item.get('full_name', '') or item.get('name', '') or '').lower()
        item_nome = (item.get('nome_exibicao', '') or item.get('nome_completo', '') or '').lower()
        
        if option_lower in [item_full, item_nome]:
            return item
    
    return None


def mapear_valores_para_opcoes(valores_salvos: List[str], source_list: List[Dict[str, Any]]) -> List[str]:
    """
    Mapeia valores salvos (formato antigo) para o formato das opções do dropdown.
    
    Isso é necessário porque:
    - Valores salvos podem ser "Paulo Silas Filho" (nome simples)
    - Opções do dropdown são formatadas como "Paulo Silas Filho (Paulo)" ou "Paulo Silas Filho"
    
    Args:
        valores_salvos: Lista de valores como estão salvos no banco
        source_list: Lista de pessoas/envolvidos para buscar
        
    Returns:
        Lista de valores no formato das opções do dropdown
    """
    if not valores_salvos or not source_list:
        return valores_salvos or []
    
    opcoes_mapeadas = []
    
    for valor in valores_salvos:
        if not valor or not valor.strip():
            continue
            
        valor = valor.strip()
        pessoa = find_person_by_option(valor, source_list)
        
        if pessoa:
            # Encontrou a pessoa, usa o formato da opção
            opcao_formatada = format_option_for_search(pessoa)
            opcoes_mapeadas.append(opcao_formatada)
        else:
            # Não encontrou, mantém o valor original (pode ser valor antigo/removido)
            opcoes_mapeadas.append(valor)
    
    return opcoes_mapeadas


def extrair_display_names(valores_opcoes: List[str], source_list: List[Dict[str, Any]]) -> List[str]:
    """
    Extrai os display_names a partir dos valores selecionados no dropdown.
    Usado para salvar no banco de dados de forma consistente.
    
    Args:
        valores_opcoes: Lista de valores selecionados no formato do dropdown
        source_list: Lista de pessoas/envolvidos
        
    Returns:
        Lista de display_names para salvar
    """
    if not valores_opcoes:
        return []
    
    display_names = []
    
    for valor in valores_opcoes:
        if not valor or not valor.strip():
            continue
            
        pessoa = find_person_by_option(valor, source_list)
        
        if pessoa:
            # Usa o display_name da pessoa
            display = get_display_name(pessoa)
            display_names.append(display if display else valor)
        else:
            # Fallback: extrai parte antes do parênteses ou usa valor completo
            nome = valor.split(' (')[0] if ' (' in valor else valor
            display_names.append(nome)
    
    return display_names


def get_scenario_type_style(tipo: Optional[str]) -> Tuple[str, str]:
    """Retorna cor baseada no tipo de cenário."""
    if 'Positivo' in str(tipo):
        return 'green', '#22c55e'
    if 'Negativo' in str(tipo):
        return 'red', '#ef4444'
    return 'grey', '#9ca3af'


def should_show_result_field(status: str) -> bool:
    """Verifica se deve mostrar campo de resultado baseado no status."""
    return status in ['Concluído', 'Concluído com pendências', 'Baixado', 'Encerrado']
