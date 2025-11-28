"""
utils.py - Funções auxiliares e helpers para o módulo de Processos.

Este módulo contém:
- Funções de formatação de nomes (abreviações, siglas)
- Helpers para opções de seleção
- Funções de ícones e estilos para cenários
"""

from typing import List, Dict, Any, Tuple, Optional


def get_short_name(full_name: str, source_list: List[Dict[str, Any]]) -> str:
    """
    Retorna sigla/apelido ou primeiro nome de uma pessoa.
    
    Prioridade: nickname > alias > primeiro nome
    
    Args:
        full_name: Nome completo da pessoa
        source_list: Lista de pessoas (clientes ou partes contrárias)
    
    Returns:
        Nome abreviado ou sigla
    """
    for item in source_list:
        if item.get('name') == full_name:
            # Prioridade: nickname > alias > primeiro nome
            if item.get('nickname'):
                return item['nickname']
            if item.get('alias'):
                return item['alias']
            # Se não tem apelido, retorna primeiro nome
            return full_name.split()[0] if full_name else full_name
    # Se não encontrou na lista, retorna primeiro nome
    return full_name.split()[0] if full_name else full_name


def get_short_clients(clients: List[str], clients_list: List[Dict[str, Any]]) -> str:
    """
    Retorna lista de clientes abreviados.
    
    Args:
        clients: Lista de nomes completos de clientes
        clients_list: Lista completa de clientes (do core)
    
    Returns:
        String com nomes abreviados separados por vírgula
    """
    if not clients:
        return '-'
    short_names = [get_short_name(c, clients_list) for c in clients]
    return ', '.join(short_names)


def get_short_opposing(opposing: List[str], opposing_list: List[Dict[str, Any]]) -> str:
    """
    Retorna lista de partes contrárias abreviadas.
    
    Args:
        opposing: Lista de nomes completos de partes contrárias
        opposing_list: Lista completa de partes contrárias (do core)
    
    Returns:
        String com nomes abreviados separados por vírgula
    """
    if not opposing:
        return '-'
    short_names = [get_short_name(op, opposing_list) for op in opposing]
    return ', '.join(short_names)


def format_option_for_search(item: Dict[str, Any]) -> str:
    """
    Formata opção para busca: inclui nome e sigla/apelido.
    
    Args:
        item: Dicionário com dados da pessoa (name, nickname, etc)
    
    Returns:
        String formatada "Nome (Apelido)" ou apenas "Nome"
    """
    name = item.get('name', '')
    nickname = item.get('nickname', '')
    if nickname and nickname != name:
        return f"{name} ({nickname})"
    return name


def get_option_value(formatted_option: str, source_list: List[Dict[str, Any]]) -> str:
    """
    Extrai o nome completo de uma opção formatada.
    
    Remove a parte entre parênteses se existir.
    
    Args:
        formatted_option: Opção formatada como "Nome (Apelido)"
        source_list: Lista fonte (não usado diretamente, mantido para compatibilidade)
    
    Returns:
        Nome completo extraído
    """
    # Remove a parte entre parênteses se existir
    if '(' in formatted_option:
        return formatted_option.split(' (')[0]
    return formatted_option


# =============================================================================
# HELPERS PARA CENÁRIOS
# =============================================================================

def get_scenario_type_style(tipo: Optional[str]) -> Tuple[str, str]:
    """
    Retorna nome da cor e código hex baseado no tipo de cenário.
    
    Args:
        tipo: Tipo do cenário (Positivo, Neutro, Negativo)
    
    Returns:
        Tupla (nome_cor, codigo_hex)
    """
    if 'Positivo' in str(tipo):
        return 'green', '#22c55e'
    if 'Negativo' in str(tipo):
        return 'red', '#ef4444'
    return 'grey', '#9ca3af'


def get_scenario_status_icon(status: Optional[str]) -> str:
    """
    Retorna ícone Material para o status do cenário.
    
    Args:
        status: Status do cenário
    
    Returns:
        Nome do ícone Material
    """
    icons = {
        'Mapeado': 'explore',
        'Em análise': 'pending',
        'Próximo de ocorrer': 'schedule',
        'Ocorrido': 'check_circle',
        'Descartado': 'cancel'
    }
    return icons.get(status, 'help')


def get_scenario_chance_icon(chance: Optional[str]) -> str:
    """
    Retorna ícone Material para a chance do cenário.
    
    Args:
        chance: Nível de chance do cenário
    
    Returns:
        Nome do ícone Material
    """
    icons = {
        'Muito alta': 'keyboard_double_arrow_up',
        'Alta': 'keyboard_arrow_up',
        'Média': 'remove',
        'Baixa': 'keyboard_arrow_down',
        'Muito baixa': 'keyboard_double_arrow_down'
    }
    return icons.get(chance, 'remove')


def get_scenario_impact_icon(impact: Optional[str]) -> str:
    """
    Retorna ícone Material para o impacto do cenário.
    
    Args:
        impact: Nível de impacto do cenário
    
    Returns:
        Nome do ícone Material
    """
    icons = {
        'Muito bom': 'sentiment_very_satisfied',
        'Bom': 'sentiment_satisfied',
        'Moderado': 'sentiment_neutral',
        'Ruim': 'sentiment_dissatisfied',
        'Muito ruim': 'sentiment_very_dissatisfied'
    }
    return icons.get(impact, 'sentiment_neutral')


# =============================================================================
# HELPERS PARA CORES DE ACESSO
# =============================================================================

def get_access_color(requested: bool, granted: bool) -> str:
    """
    Retorna cor baseada no status de acesso.
    
    Args:
        requested: Se o acesso foi solicitado
        granted: Se o acesso foi concedido
    
    Returns:
        Código hex da cor
    """
    if granted:
        return '#22c55e'  # Verde - concedido
    elif requested:
        return '#3b82f6'  # Azul - em andamento
    else:
        return '#ef4444'  # Vermelho - parado


def get_area_badge_style(area: Optional[str]) -> str:
    """
    Retorna estilo CSS para badge de área.
    
    Args:
        area: Nome da área do processo
    
    Returns:
        String de estilo CSS
    """
    styles = {
        'Administrativo': 'background-color: #6b7280;',
        'Criminal': 'background-color: #dc2626;',
        'Cível': 'background-color: #2563eb;',
        'Tributário': 'background-color: #7c3aed;',
        'Técnico/projetos': 'background-color: #22c55e;',
    }
    return styles.get(area, 'background-color: #d1d5db; color: #374151;')


def get_status_badge_style(status: Optional[str]) -> str:
    """
    Retorna estilo CSS para badge de status.
    
    Args:
        status: Status do processo
    
    Returns:
        String de estilo CSS
    """
    styles = {
        'Em andamento': 'background-color: #eab308; color: #1f2937;',
        'Concluído': 'background-color: #166534; color: #ffffff;',
        'Concluído com pendências': 'background-color: #4d7c0f; color: #ffffff;',
        'Em monitoramento': 'background-color: #ea580c; color: #ffffff;',
    }
    return styles.get(status, 'background-color: #9ca3af; color: #1f2937;')


