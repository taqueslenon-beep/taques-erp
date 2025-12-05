"""
Componentes de UI reutilizáveis para o módulo Painel.
Cards, seções, estados vazios e outros elementos visuais.
"""
from nicegui import ui
from typing import Optional, List, Tuple


def create_stat_card(
    label: str,
    value: str,
    color: str,
    subtitle: Optional[str] = None,
    border_color: Optional[str] = None,
    width: str = 'w-64',
) -> None:
    """
    Cria um card de estatística com valor destacado.
    
    Args:
        label: Título do card
        value: Valor principal a exibir
        color: Cor do valor
        subtitle: Texto adicional abaixo do valor
        border_color: Cor da borda esquerda (se None, não tem borda)
        width: Classe de largura do card
    """
    card_classes = f'{width} p-4'
    if border_color:
        card_classes += ' border-l-4'
    
    with ui.card().classes(card_classes) as card:
        if border_color:
            card.style(f'border-left-color: {border_color};')
        
        ui.label(label).classes('text-gray-500 text-sm')
        ui.label(value).classes('text-3xl font-bold').style(f'color: {color};')
        
        if subtitle:
            ui.label(subtitle).classes('text-xs text-gray-400 mt-1')


def create_metric_row(metrics: List[Tuple[str, str, str, Optional[str]]]) -> None:
    """
    Cria uma linha de cards de métricas.
    
    Args:
        metrics: Lista de tuplas (label, value, color, subtitle)
    """
    with ui.row().classes('gap-4 flex-wrap mb-4'):
        for metric in metrics:
            label, value, color = metric[:3]
            subtitle = metric[3] if len(metric) > 3 else None
            create_stat_card(label, value, color, subtitle, border_color=color)


def create_chart_card(title: str, min_width: str = 'min-w-80') -> ui.card:
    """
    Cria um card container para gráficos.
    
    Args:
        title: Título do card
        min_width: Largura mínima
    
    Returns:
        Contexto do card para adicionar conteúdo
    """
    card = ui.card().classes(f'flex-1 {min_width} p-4')
    with card:
        ui.label(title).classes('text-lg font-semibold text-gray-700 mb-4')
    return card


def create_empty_state(
    icon: str = 'info',
    title: str = 'Nenhum dado disponível',
    message: str = '',
    icon_size: str = '64px',
) -> None:
    """
    Cria um estado vazio com ícone e mensagem.
    
    Args:
        icon: Nome do ícone Material
        title: Título principal
        message: Mensagem secundária
        icon_size: Tamanho do ícone
    """
    with ui.column().classes('items-center justify-center gap-4 py-8'):
        ui.icon(icon, size=icon_size).classes('text-gray-400')
        ui.label(title).classes('text-xl font-bold text-gray-600')
        if message:
            ui.label(message).classes('text-gray-500 text-center max-w-md')


def create_empty_chart_state(message: str = 'Nenhum dado cadastrado ainda.') -> None:
    """Cria estado vazio simples para gráficos."""
    ui.label(message).classes('text-gray-400 italic text-center py-8')


def create_section_title(title: str, subtitle: Optional[str] = None) -> None:
    """
    Cria título de seção padronizado.
    
    Args:
        title: Título principal
        subtitle: Subtítulo opcional
    """
    ui.label(title).classes('text-lg font-semibold text-gray-700 mb-2')
    if subtitle:
        ui.label(subtitle).classes('text-sm text-gray-500 mb-4')


def create_development_banner(
    title: str = 'Módulo em Desenvolvimento',
    message: str = 'Esta visualização está sendo aprimorada.',
    color: str = 'yellow',
) -> None:
    """
    Cria banner de desenvolvimento/aviso.
    
    Args:
        title: Título do banner
        message: Mensagem do banner
        color: Cor base (yellow, blue, red, green)
    """
    color_map = {
        'yellow': ('#f59e0b', 'bg-yellow-50', 'text-yellow-600', 'text-yellow-800', 'text-yellow-700'),
        'blue': ('#2563eb', 'bg-blue-50', 'text-blue-600', 'text-blue-800', 'text-blue-700'),
        'red': ('#dc2626', 'bg-red-50', 'text-red-600', 'text-red-800', 'text-red-700'),
        'green': ('#16a34a', 'bg-green-50', 'text-green-600', 'text-green-800', 'text-green-700'),
    }
    
    border_color, bg_class, icon_class, title_class, msg_class = color_map.get(color, color_map['yellow'])
    
    with ui.card().classes(f'w-full p-4 mb-4 {bg_class} border-l-4').style(f'border-left-color: {border_color};'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('construction' if color == 'yellow' else 'info', size='md').classes(icon_class)
            with ui.column().classes('flex-grow'):
                ui.label(title).classes(f'text-sm font-semibold {title_class}')
                ui.label(message).classes(f'text-xs {msg_class}')


def create_under_construction() -> None:
    """Cria estado de 'em construção' para abas não implementadas."""
    with ui.card().classes('w-full p-4'):
        with ui.column().classes('items-center justify-center gap-4'):
            ui.icon('construction', size='64px').classes('text-gray-400')
            ui.label('Em Desenvolvimento').classes('text-2xl font-bold text-gray-600')
            ui.label('Esta visualização está sendo desenvolvida e estará disponível em breve.').classes('text-gray-500 text-center max-w-md')


def create_filter_card(title: str = 'Filtros') -> ui.card:
    """
    Cria card de filtros padronizado.
    
    Returns:
        Contexto do card para adicionar filtros
    """
    card = ui.card().classes('w-64 p-4 bg-gray-50')
    with card:
        ui.label(title).classes('text-base font-semibold text-gray-800 mb-4')
    return card


def create_stat_summary_row(items: List[Tuple[str, str, str, str]]) -> None:
    """
    Cria linha de resumo com ícone e texto.
    
    Args:
        items: Lista de tuplas (icon, color, label, value)
    """
    with ui.row().classes('w-full justify-center mt-6 gap-6 flex-wrap'):
        for icon, color, label, value in items:
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon, size='sm').style(f'color: {color};')
                ui.label(f'{label}: {value}').classes('text-sm font-medium text-gray-700')







