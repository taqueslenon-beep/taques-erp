"""
Componentes reutilizáveis para o módulo de Casos.
Contém funções para criar elementos de UI comuns.
"""
from nicegui import ui
from .models import obter_cor_prioridade, PRIORIDADE_PADRAO


def criar_badge_prioridade(prioridade: str):
    """
    Cria um badge visual para exibir a prioridade de um caso.
    
    Args:
        prioridade: Código da prioridade (P1, P2, P3, P4)
                   Se None ou vazio, usa P4 como padrão
    
    Returns:
        None (cria elemento UI diretamente)
    """
    # Normaliza prioridade (garante P4 se inválida)
    if not prioridade or (isinstance(prioridade, str) and prioridade.strip() == ''):
        prioridade = PRIORIDADE_PADRAO
    
    # Obtém a cor correspondente
    cor = obter_cor_prioridade(prioridade)
    
    # Cria badge compacto
    with ui.element('span').classes(
        'px-2 py-1 rounded-full text-xs font-bold text-white inline-block'
    ).style(f'background-color: {cor}'):
        ui.label(prioridade)

