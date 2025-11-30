"""
acordo_dialog.py - Dialog/Modal para criar e editar acordos.

Seguindo o padrão do formulário de processos com sidebar e abas.
"""

from nicegui import ui
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

from ....core import (
    PRIMARY_COLOR, get_cases_list, get_processes_list, 
    get_clients_list, get_opposing_parties_list, get_users_list,
    get_display_name
)
from ..database import (
    create_acordo, listar_casos, listar_processos, 
    listar_pessoas_como_clientes, listar_todas_pessoas
)
from ..business_logic import validate_acordo, generate_acordo_id
from ..clausulas.modais.modal_nova_clausula import criar_dialog_nova_clausula
from ..clausulas.visualizacoes.lista_clausulas import lista_clausulas
from ..utils import make_required_label, format_option_for_search, format_option_for_pessoa, format_option_for_search_pessoa
from .abas.aba_identificacao import render_aba_identificacao
from .abas.aba_vinculacoes import render_aba_vinculacoes
from .abas.aba_partes import render_aba_partes

# CSS para sidebar tabs (mesmo padrão de processos)
ACORDO_SIDEBAR_TABS_CSS = '''
    .acordo-sidebar-tabs .q-tab {
        justify-content: flex-start !important;
        flex-direction: row !important;
        padding: 6px 12px !important;
        min-height: 32px !important;
        height: 32px !important;
        font-size: 11px !important;
        color: white !important;
        border-radius: 0 !important;
        text-transform: none !important;
        text-align: left !important;
        align-items: center !important;
    }
    .acordo-sidebar-tabs .q-tab:hover {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
    }
    .acordo-sidebar-tabs .q-tab--active {
        background: rgba(255,255,255,0.12) !important;
        color: white !important;
        border-left: 2px solid rgba(255,255,255,0.8) !important;
    }
    .acordo-sidebar-tabs .q-tab__content {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        width: 100% !important;
    }
    .acordo-sidebar-tabs .q-tab__icon {
        font-size: 16px !important;
        margin: 0 !important;
        color: white !important;
        align-self: center !important;
        flex-shrink: 0 !important;
    }
    .acordo-sidebar-tabs .q-tab__label {
        font-weight: 400 !important;
        letter-spacing: 0.2px !important;
        color: white !important;
        text-align: left !important;
        align-self: center !important;
    }
    .acordo-sidebar-tabs .q-tabs__content {
        overflow: visible !important;
    }
    .acordo-sidebar-tabs .q-tab__indicator {
        display: none !important;
    }
'''


def render_acordo_dialog(on_success: Optional[Callable] = None):
    """
    Factory function para criar o Dialog de Acordo com sidebar e abas.
    
    Args:
        on_success: Callback executado após salvar com sucesso
    
    Returns:
        tuple: (dialog_component, open_function)
    """
    
    # Estado do formulário
    state = {
        'selected_casos': [],  # Lista de IDs dos casos
        'selected_processos': [],  # Lista de IDs dos processos
        'selected_clientes': [],  # Lista de IDs dos clientes (múltiplos)
        'parte_contraria_id': None,  # ID da parte contrária (singular)
        'selected_outros_envolvidos': [],  # Lista de IDs de outros envolvidos (múltiplos)
        'clausulas': [],  # Lista de cláusulas do acordo
    }
    
    # Inject CSS styles for sidebar menu
    ui.add_head_html(f'<style>{ACORDO_SIDEBAR_TABS_CSS}</style>')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden relative').style('height: 80vh; max-height: 80vh;'):
        with ui.row().classes('w-full h-full gap-0'):
            # Sidebar
            with ui.column().classes('h-full shrink-0 justify-between').style(f'width: 170px; background: {PRIMARY_COLOR};'):
                with ui.column().classes('w-full gap-0'):
                    dialog_title = ui.label('NOVO ACORDO').classes('text-xs font-medium px-3 py-2 text-white/80 uppercase tracking-wide')
                    
                    with ui.tabs().props('vertical dense no-caps inline-label').classes('w-full acordo-sidebar-tabs') as tabs:
                        tab_dados = ui.tab('Dados básicos', icon='description')
                        tab_clausulas = ui.tab('Cláusulas', icon='article')
            
            # Content
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_dados).classes('w-full h-full p-4 bg-transparent'):
                    
                    # --- TAB 1: DADOS BÁSICOS ---
                    with ui.tab_panel(tab_dados):
                        with ui.column().classes('w-full gap-4'):
                            
                            # SEÇÃO 1 - Identificação do Acordo
                            titulo_input, data_celebracao_input = render_aba_identificacao(state)
                            
                            # SEÇÃO 2 - Vinculações
                            casos_sel, casos_chips, processos_sel, processos_chips, refresh_casos_chips, refresh_processos_chips = render_aba_vinculacoes(state)
                            
                            # SEÇÃO 3 - Partes do Acordo
                            clientes_sel, clientes_chips, parte_contraria_sel, parte_contraria_chips, outros_sel, outros_chips, refresh_clientes_chips, refresh_parte_contraria_chip, refresh_outros_chips = render_aba_partes(state)
                    
                    # --- TAB 2: CLÁUSULAS ---
                    with ui.tab_panel(tab_clausulas):
                        with ui.column().classes('w-full gap-4'):
                            # Título da seção
                            ui.label('📜 Cláusulas do Acordo').classes('text-lg font-bold mb-2')
                            
                            # Botão Nova Cláusula
                            with ui.row().classes('w-full justify-end mb-4'):
                                def on_nova_clausula():
                                    """Abre dialog para nova cláusula."""
                                    clausula_dialog, open_clausula_dialog = criar_dialog_nova_clausula(
                                        on_save_callback=lambda clausula_data, edit_idx=None: on_save_clausula(clausula_data, edit_idx)
                                    )
                                    open_clausula_dialog()
                                
                                ui.button('+ NOVA CLÁUSULA', icon='add', on_click=on_nova_clausula).props('color=primary')
                            
                            # Container para lista de cláusulas (refreshable)
                            clausulas_container = ui.column().classes('w-full')
                            
                            def refresh_clausulas_list():
                                """Atualiza lista de cláusulas com validação de DOM."""
                                try:
                                    if not clausulas_container:
                                        return
                                    clausulas_container.clear()
                                    with clausulas_container:
                                        # Renderiza lista de cláusulas
                                        result = lista_clausulas(
                                            state['clausulas'],
                                            on_edit=on_edit_clausula,
                                            on_delete=on_delete_clausula
                                        )
                                        # Se não há cláusulas, mostra mensagem
                                        if not state['clausulas']:
                                            with ui.card().classes('w-full p-8 flex justify-center items-center'):
                                                ui.label('Nenhuma cláusula adicionada.').classes('text-gray-400 italic')
                                except Exception as e:
                                    import traceback
                                    error_trace = traceback.format_exc()
                                    print(f"ERRO em refresh_clausulas_list: {error_trace}")  # Log para debug
                                    # Tenta renderizar mensagem de erro
                                    try:
                                        clausulas_container.clear()
                                        with clausulas_container:
                                            ui.label('Erro ao carregar cláusulas.').classes('text-red-500')
                                    except:
                                        pass
                            
                            def on_save_clausula(clausula_data: Dict[str, Any], edit_index: Optional[int] = None):
                                """Callback ao salvar cláusula."""
                                import uuid
                                from datetime import datetime
                                
                                try:
                                    # Adiciona metadados necessários
                                    now = datetime.now().isoformat()
                                    
                                    if edit_index is not None and isinstance(edit_index, int):
                                        # Editar cláusula existente
                                        if 0 <= edit_index < len(state['clausulas']):
                                            clausula_existente = state['clausulas'][edit_index]
                                            # Preserva ID e data de criação
                                            clausula_data['_id'] = clausula_existente.get('_id') or str(uuid.uuid4())
                                            clausula_data['data_criacao'] = clausula_existente.get('data_criacao', now)
                                            clausula_data['data_atualizacao'] = now
                                            # Preserva ordem se existir, senão usa índice
                                            clausula_data['ordem'] = clausula_existente.get('ordem', edit_index)
                                            state['clausulas'][edit_index] = clausula_data
                                        else:
                                            ui.notify(f'Erro: índice de cláusula inválido ({edit_index})!', type='negative')
                                            return
                                    else:
                                        # Adicionar nova cláusula
                                        # Gera ID único se não existir
                                        if '_id' not in clausula_data or not clausula_data.get('_id'):
                                            clausula_data['_id'] = str(uuid.uuid4())
                                        # Adiciona timestamps
                                        if 'data_criacao' not in clausula_data or not clausula_data.get('data_criacao'):
                                            clausula_data['data_criacao'] = now
                                        clausula_data['data_atualizacao'] = now
                                        # Adiciona ordem (baseada na posição na lista)
                                        clausula_data['ordem'] = len(state['clausulas'])
                                        state['clausulas'].append(clausula_data)
                                    
                                    # Atualiza lista de cláusulas na interface
                                    refresh_clausulas_list()
                                    
                                except Exception as e:
                                    import traceback
                                    error_trace = traceback.format_exc()
                                    print(f"ERRO em on_save_clausula: {error_trace}")  # Log para debug
                                    ui.notify(f'Erro ao salvar cláusula: {str(e)}', type='negative')
                            
                            def on_edit_clausula(index: int):
                                """Abre dialog para editar cláusula."""
                                if 0 <= index < len(state['clausulas']):
                                    clausula = state['clausulas'][index]
                                    # Cria callback que preserva o índice correto
                                    def save_callback(clausula_data, edit_idx):
                                        # Usa o índice passado como parâmetro, não o edit_idx do dialog
                                        on_save_clausula(clausula_data, index)
                                    
                                    clausula_dialog, open_clausula_dialog = criar_dialog_nova_clausula(
                                        on_save_callback=save_callback,
                                        clausula_edit=clausula,
                                        edit_index=index
                                    )
                                    open_clausula_dialog()
                            
                            def on_delete_clausula(index: int):
                                """Remove cláusula da lista."""
                                if 0 <= index < len(state['clausulas']):
                                    clausula = state['clausulas'][index]
                                    titulo = clausula.get('titulo', 'cláusula')
                                    
                                    def confirm_delete():
                                        state['clausulas'].pop(index)
                                        refresh_clausulas_list()
                                        ui.notify(f'Cláusula "{titulo}" removida!', type='positive')
                                    
                                    # Dialog de confirmação
                                    with ui.dialog() as confirm_dialog, ui.card().classes('p-6'):
                                        ui.label(f'Tem certeza que deseja remover a cláusula "{titulo}"?').classes('text-base mb-4')
                                        with ui.row().classes('w-full justify-end gap-2'):
                                            ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                                            ui.button('Remover', on_click=lambda: [confirm_delete(), confirm_dialog.close()]).props('color=red')
                                    
                                    confirm_dialog.open()
                            
                            # Renderizar lista inicial
                            refresh_clausulas_list()
            
            # Footer Actions
            with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10').style('background: rgba(249, 250, 251, 0.95); border-radius: 8px 0 0 0;'):
                def do_save():
                    # Coletar dados do formulário
                    acordo_data = {
                        'titulo': titulo_input.value.strip() if titulo_input.value else '',
                        'casos_vinculados': state['selected_casos'],
                        'processos_vinculados': state['selected_processos'],
                        'data_celebracao': data_celebracao_input.value if data_celebracao_input.value else None,
                        'status': 'Rascunho',
                    }
                    
                    # Clientes (múltiplos)
                    acordo_data['clientes_ids'] = state['selected_clientes']
                    
                    # Parte Contrária (usa state['parte_contraria_id'])
                    if state.get('parte_contraria_id'):
                        acordo_data['parte_contraria'] = state['parte_contraria_id']
                    else:
                        acordo_data['parte_contraria'] = None
                    
                    # Outros Envolvidos
                    acordo_data['outros_envolvidos'] = state['selected_outros_envolvidos']
                    
                    # Cláusulas
                    acordo_data['clausulas'] = state['clausulas']
                    
                    # Validação
                    is_valid, error_msg = validate_acordo(acordo_data)
                    if not is_valid:
                        ui.notify(error_msg, type='warning')
                        return
                    
                    # Validar todas as cláusulas
                    from ..business_logic import validar_clausula
                    for idx, clausula in enumerate(state['clausulas']):
                        is_valid_clausula, error_msg_clausula = validar_clausula(clausula)
                        if not is_valid_clausula:
                            ui.notify(f'Erro na cláusula {idx + 1}: {error_msg_clausula}', type='warning')
                            return
                    
                    # Salvar
                    try:
                        acordo_id = create_acordo(acordo_data)
                        ui.notify('Acordo criado com sucesso!', type='positive')
                        dialog.close()
                        if on_success:
                            on_success()
                    except Exception as e:
                        ui.notify(f'Erro ao salvar acordo: {str(e)}', type='negative')
                
                ui.button('CANCELAR', icon='cancel', on_click=dialog.close).props('flat').classes('font-bold')
                ui.button('SALVAR', icon='save', on_click=do_save).props('color=primary').classes('font-bold shadow-lg')
    
    def open_dialog():
        """Abre o dialog para criar novo acordo."""
        # Limpar formulário
        titulo_input.value = ''
        data_celebracao_input.value = ''
        parte_contraria_sel.value = None
        state['selected_casos'] = []
        state['selected_processos'] = []
        state['selected_clientes'] = []
        state['parte_contraria_id'] = None
        state['selected_outros_envolvidos'] = []
        state['clausulas'] = []
        
        # Atualizar opções de casos
        casos_list = listar_casos()
        casos_options = [format_option_for_search(c) for c in casos_list]
        casos_sel.options = casos_options or ['-']
        
        # Atualizar opções de processos
        processos_list = listar_processos()
        processos_options = []
        for proc in processos_list:
            title = proc.get('title', 'Sem título')
            number = proc.get('number', '')
            if number:
                processos_options.append(f"{title} | {proc.get('_id', '')}")
            else:
                processos_options.append(f"{title} | {proc.get('_id', '')}")
        processos_sel.options = processos_options or ['-']
        
        # Atualizar opções de clientes
        clientes_list = listar_pessoas_como_clientes()
        clientes_options = [format_option_for_pessoa(c) for c in clientes_list]
        clientes_sel.options = clientes_options or ['-']
        
        # Atualizar opções de pessoas (parte contrária e outros envolvidos)
        todas_pessoas = listar_todas_pessoas()
        pessoas_options = [format_option_for_pessoa(p) for p in todas_pessoas]
        parte_contraria_sel.options = pessoas_options or ['-']
        outros_sel.options = pessoas_options or ['-']
        
        # Limpar chips
        refresh_casos_chips(casos_chips)
        refresh_processos_chips(processos_chips)
        refresh_clientes_chips(clientes_chips)
        refresh_parte_contraria_chip(parte_contraria_chips)
        refresh_outros_chips(outros_chips)
        
        # Limpar lista de cláusulas
        refresh_clausulas_list()
        
        dialog.open()
    
    return dialog, open_dialog
