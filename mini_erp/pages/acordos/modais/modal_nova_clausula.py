"""
modal_nova_clausula.py - Modal para criar nova cláusula no acordo.
"""

from nicegui import ui
from typing import Optional, Callable, Dict


def validar_data_br(data_str: str) -> bool:
    """
    Valida formato de data brasileira DD/MM/AAAA.
    
    Args:
        data_str: String com data em formato DD/MM/AAAA
    
    Returns:
        True se válida, False caso contrário
    """
    import re
    
    # Verificar formato
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', data_str):
        return False
    
    try:
        dia, mes, ano = data_str.split('/')
        dia, mes, ano = int(dia), int(mes), int(ano)
        
        # Validar ranges
        if mes < 1 or mes > 12:
            return False
        
        # Dias por mês (simplificado)
        dias_mes = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        if dia < 1 or dia > dias_mes[mes - 1]:
            return False
        
        return True
    except Exception:
        return False


def render_clausula_dialog(on_save: Optional[Callable] = None, clausula_inicial: Optional[Dict] = None):
    """
    Renderiza dialog para criar/editar cláusula.
    
    Args:
        on_save: Callback executado ao salvar
        clausula_inicial: Dados da cláusula para edição (None para nova)
    
    Returns:
        tuple: (dialog, open_function)
    """
    
    is_editing = clausula_inicial is not None
    
    # Estado da cláusula
    clausula_state = {
        'titulo': clausula_inicial.get('titulo', '') if is_editing else '',
        'numero': clausula_inicial.get('numero', '') if is_editing else '',
        'descricao': clausula_inicial.get('descricao', '') if is_editing else '',
        'tipo': clausula_inicial.get('tipo', 'Geral') if is_editing else 'Geral',
        'status': clausula_inicial.get('status', 'Pendente') if is_editing else 'Pendente',
        'prazo_seguranca': clausula_inicial.get('prazo_seguranca', '') or '' if is_editing else '',
        'prazo_fatal': clausula_inicial.get('prazo_fatal', '') or '' if is_editing else '',
        'regular': clausula_inicial.get('regular', False) if is_editing else False,
    }
    
    # Dialog principal
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6 gap-4'):
        # Título do dialog
        titulo_dialog = 'EDITAR CLÁUSULA' if is_editing else 'NOVA CLÁUSULA'
        ui.label(titulo_dialog).classes('text-lg font-bold text-gray-800 mb-4')
        
        # Campos do formulário
        with ui.column().classes('w-full gap-4'):
            # Título da cláusula
            titulo_input = ui.input(
                label='Título da cláusula *',
                placeholder='Digite o título',
                value=clausula_state['titulo']
            ).classes('w-full').props('outlined dense')
            
            # Número da cláusula
            numero_input = ui.input(
                label='Número da cláusula',
                placeholder='Ex: 1.1, 2.3, etc',
                value=clausula_state['numero']
            ).classes('w-full').props('outlined dense')
            
            # Descrição da cláusula
            descricao_input = ui.textarea(
                label='Descrição da cláusula',
                placeholder='Digite a descrição detalhada da cláusula',
                value=clausula_state['descricao']
            ).classes('w-full').props('outlined dense')
            
            # Tipo da cláusula
            tipo_select = ui.select(
                ['Geral', 'Específica'],
                label='Tipo da cláusula',
                value=clausula_state['tipo']
            ).classes('w-full').props('outlined dense')
            
            # Status da cláusula
            status_select = ui.select(
                ['Cumprida', 'Pendente', 'Atrasada'],
                label='Status da cláusula',
                value=clausula_state['status']
            ).classes('w-full').props('outlined dense')
            
            # Prazos (opcionais)
            ui.label('Prazos (opcionais)').classes('text-sm font-semibold text-gray-600 mt-2')
            
            with ui.row().classes('w-full gap-4'):
                # Prazo de segurança
                prazo_seguranca_input = ui.input(
                    label='Prazo de segurança',
                    placeholder='DD/MM/AAAA',
                    value=clausula_state['prazo_seguranca']
                ).classes('flex-grow').props('outlined dense')
                
                # Prazo fatal
                prazo_fatal_input = ui.input(
                    label='Prazo fatal',
                    placeholder='DD/MM/AAAA',
                    value=clausula_state['prazo_fatal']
                ).classes('flex-grow').props('outlined dense')
            
            # Estado do checkbox "Regular"
            is_regular = {'value': clausula_state['regular']}
            
            # Checkbox Regular
            def toggle_regular():
                """Ativa/desativa modo regular."""
                is_regular['value'] = checkbox_regular.value
                
                if is_regular['value']:
                    # Desabilitar campos e limpar valores
                    prazo_seguranca_input.enabled = False
                    prazo_fatal_input.enabled = False
                    prazo_seguranca_input.value = ''
                    prazo_fatal_input.value = ''
                else:
                    # Habilitar campos
                    prazo_seguranca_input.enabled = True
                    prazo_fatal_input.enabled = True
            
            # Row com checkbox + texto
            with ui.row().classes('w-full items-center gap-2 mt-2'):
                checkbox_regular = ui.checkbox(
                    'Regular: deve ser cumprida durante todo o acordo',
                    value=clausula_state['regular'],
                    on_change=toggle_regular
                ).classes('text-sm')
            
            # Aplicar estado inicial do checkbox (se regular está ativo, desabilitar prazos)
            if clausula_state['regular']:
                prazo_seguranca_input.enabled = False
                prazo_fatal_input.enabled = False
        
        # Separador
        ui.separator().classes('my-4')
        
        # Botões
        with ui.row().classes('w-full gap-2 justify-end'):
            def on_cancel():
                """Fecha o dialog."""
                dialog.close()
            
            def on_save_clausula():
                """Salva a cláusula."""
                # Validar título obrigatório
                if not titulo_input.value:
                    ui.notify('Título da cláusula é obrigatório!', type='warning')
                    return
                
                # Validar prazos apenas se modo regular NÃO estiver ativo
                if not is_regular['value']:
                    prazo_seguranca = prazo_seguranca_input.value.strip()
                    prazo_fatal = prazo_fatal_input.value.strip()
                    
                    # Se fornecido, validar formato DD/MM/AAAA
                    if prazo_seguranca:
                        if not validar_data_br(prazo_seguranca):
                            ui.notify('Prazo de segurança: formato inválido (use DD/MM/AAAA)', type='warning')
                            return
                    
                    if prazo_fatal:
                        if not validar_data_br(prazo_fatal):
                            ui.notify('Prazo fatal: formato inválido (use DD/MM/AAAA)', type='warning')
                            return
                else:
                    # Se modo regular está ativo, prazos são None
                    prazo_seguranca = ''
                    prazo_fatal = ''
                
                # Preparar dados
                clausula_data = {
                    'titulo': titulo_input.value,
                    'numero': numero_input.value,
                    'descricao': descricao_input.value,
                    'tipo': tipo_select.value,
                    'status': status_select.value,
                    'prazo_seguranca': prazo_seguranca if prazo_seguranca else None,
                    'prazo_fatal': prazo_fatal if prazo_fatal else None,
                    'regular': is_regular['value'],  # Estado do botão Regular
                }
                
                # Chamar callback se fornecido
                if on_save:
                    on_save(clausula_data)
                
                # Fechar dialog
                dialog.close()
            
            ui.button('Cancelar', on_click=on_cancel).props('flat')
            ui.button('Salvar', on_click=on_save_clausula).props('color=primary').classes('font-bold')
    
    def open_dialog():
        """Abre o dialog."""
        dialog.open()
    
    return dialog, open_dialog

