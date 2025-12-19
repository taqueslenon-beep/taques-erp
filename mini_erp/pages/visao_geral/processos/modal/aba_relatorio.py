"""
Aba de Relatório do modal de processo (Visão Geral).
"""
from nicegui import ui
from typing import Dict, Any


def render_aba_relatorio(dados: Dict[str, Any], is_edicao: bool) -> Dict[str, Any]:
    """
    Renderiza a aba de Relatório do modal.
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
            ui.label('Resumo dos Fatos').classes('text-sm font-semibold text-gray-700')
            refs['relatory_facts_input'] = ui.editor(
                value=dados.get('relatory_facts', '') if is_edicao else '',
                placeholder='Descreva os principais fatos do processo...'
            ).classes('w-full').style('height: 200px')
            
            ui.label('Histórico / Linha do Tempo').classes('text-sm font-semibold text-gray-700')
            refs['relatory_timeline_input'] = ui.editor(
                value=dados.get('relatory_timeline', '') if is_edicao else '',
                placeholder='Descreva a sequência cronológica dos eventos...'
            ).classes('w-full').style('height: 200px')
            
            ui.label('Documentos Relevantes').classes('text-sm font-semibold text-gray-700')
            refs['relatory_documents_input'] = ui.editor(
                value=dados.get('relatory_documents', '') if is_edicao else '',
                placeholder='Liste os documentos importantes do processo...'
            ).classes('w-full').style('height: 200px')
    
    # Atrasa criação dos editores em 100ms para garantir DOM pronto
    ui.timer(0.1, create_editors, once=True)
    
    return refs

