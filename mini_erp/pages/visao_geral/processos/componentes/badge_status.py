"""
Componente de badge de status para processos (Visão Geral).
"""
from nicegui import ui
from ..constants import STATUS_CORES


def render_badge_status(status: str):
    """
    Renderiza um badge colorido para o status do processo.
    
    Args:
        status: Status do processo
    """
    cores = STATUS_CORES.get(status, {'bg': '#6b7280', 'text': 'white'})
    with ui.badge(status).style(f'background-color: {cores["bg"]}; color: {cores["text"]};'):
        pass



