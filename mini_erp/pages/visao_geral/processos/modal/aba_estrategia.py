"""
Aba de Estratégia do modal de processo (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any


def render_aba_estrategia(dados: Dict[str, Any], is_edicao: bool) -> Dict[str, Any]:
    """
    Renderiza a aba de Estratégia do modal.
    Usa delay na inicialização dos editores Quill para evitar erros MutationObserver.
    
    Args:
        dados: Dados do processo (se edição)
        is_edicao: Se está editando
        
    Returns:
        Dicionário com referências aos campos criados
    """
    container = ui.column().classes('w-full gap-5')
    refs = {'container': container}
    
    def create_editors():
        """Cria os editores com delay para garantir DOM pronto."""
        container.clear()
        with container:
            ui.label('Objetivos').classes('text-sm font-semibold text-gray-700')
            refs['objectives_input'] = ui.editor(
                value=dados.get('strategy_objectives', '') if is_edicao else '',
                placeholder='Descreva os objetivos...'
            ).classes('w-full').style('height: 200px')
            
            ui.label('Teses a serem trabalhadas').classes('text-sm font-semibold text-gray-700')
            refs['thesis_input'] = ui.editor(
                value=dados.get('legal_thesis', '') if is_edicao else '',
                placeholder='Descreva as teses...'
            ).classes('w-full').style('height: 200px')
            
            ui.label('Observações').classes('text-sm font-semibold text-gray-700')
            refs['observations_input'] = ui.editor(
                value=(dados.get('strategy_observations', '') or dados.get('observacoes', '')) if is_edicao else '',
                placeholder='Observações...'
            ).classes('w-full').style('height: 200px')
    
    # Atrasa criação dos editores em 100ms para garantir DOM pronto
    ui.timer(0.1, create_editors, once=True)
    
    return refs

