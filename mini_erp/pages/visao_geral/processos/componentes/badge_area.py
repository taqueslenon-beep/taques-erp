"""
Componente de badge de área para processos (Visão Geral).
"""
from nicegui import ui
from ..constants import AREA_CORES


def render_badge_area(area: str):
    """
    Renderiza um badge colorido para a área do processo.
    
    Args:
        area: Área do processo
    """
    cores = AREA_CORES.get(area, {'bg': '#f3f4f6', 'text': '#374151', 'border': '#d1d5db'})
    with ui.badge(area).style(f'background-color: {cores["bg"]}; color: {cores["text"]}; border: 1px solid {cores["border"]};'):
        pass











