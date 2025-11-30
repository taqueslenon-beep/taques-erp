"""
aba_identificacao.py - Aba de Identificação do Acordo.

Campos: Título e Data de Celebração.
"""

from nicegui import ui
from typing import Dict, Any, Tuple
from ...utils import make_required_label


def render_aba_identificacao(state: Dict[str, Any]) -> Tuple[ui.input, ui.input]:
    """
    Renderiza aba de identificação do acordo.
    
    Args:
        state: Dicionário de estado do formulário
    
    Returns:
        Tupla (titulo_input, data_celebracao_input)
    """
    with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
        ui.label('📋 Identificação do Acordo').classes('text-lg font-bold mb-3')
        with ui.column().classes('w-full gap-4'):
            titulo_input = ui.input(make_required_label('Título do Acordo')).classes('w-full').props('outlined dense')
            titulo_input.tooltip('Nome descritivo do acordo')
            
            data_celebracao_input = ui.input('Data de Celebração', placeholder='YYYY-MM-DD').classes('w-full').props('outlined dense type=date')
            data_celebracao_input.tooltip('Data em que o acordo foi celebrado')
    
    return titulo_input, data_celebracao_input

