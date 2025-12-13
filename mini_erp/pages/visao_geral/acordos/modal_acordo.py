"""
Modal/formulário para criar Acordo.
Workspace: Visão Geral do Escritório
"""
from nicegui import ui
from typing import Optional, Callable
from .models import NUCLEO_OPTIONS, AREA_OPTIONS, TIPO_ACORDO_OPTIONS


def abrir_dialog_acordo(on_save: Optional[Callable] = None):
    """
    Abre dialog para criar um novo acordo.

    Args:
        on_save: Callback executado após salvar com sucesso
    """
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        # Header
        with ui.row().classes('w-full items-center justify-between p-4'):
            ui.label('NOVO ACORDO').classes('text-xl font-bold text-gray-800')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round')

        ui.separator()

        # Container do formulário com scroll
        with ui.scroll_area().classes('w-full').style('max-height: 70vh'):
            with ui.column().classes('w-full gap-4 p-4'):
                # Título do Acordo (obrigatório)
                titulo_input = ui.input(
                    label='Título do Acordo *',
                    placeholder='Ex: Acordo de não persecução penal - Caso XYZ'
                ).classes('w-full').props('dense outlined')

                # Linha: Núcleo e Área do direito
                with ui.row().classes('w-full gap-4'):
                    nucleo_select = ui.select(
                        options=NUCLEO_OPTIONS,
                        value='Generalista',
                        label='Núcleo *'
                    ).classes('flex-1').props('dense outlined')

                    area_select = ui.select(
                        options=[''] + AREA_OPTIONS,
                        label='Área do direito'
                    ).classes('flex-1').props('dense outlined clearable')

                # Tipo de acordo (obrigatório)
                with ui.column().classes('w-full gap-2'):
                    ui.label('Tipo *').classes('text-sm font-medium text-gray-700')
                    tipo_radio = ui.radio(
                        options=TIPO_ACORDO_OPTIONS,
                        value='Judicial'
                    ).classes('w-full').props('inline')

                # Separador - Vínculos
                ui.separator().classes('my-2')
                ui.label('Vínculos').classes('text-sm font-bold text-gray-600')

                # Estado local para seleções múltiplas
                clientes_selecionados = []
                outros_selecionados = []

                # Cliente (placeholder - múltipla seleção com chips)
                with ui.row().classes('w-full gap-2 items-end'):
                    cliente_select = ui.select(
                        options={},
                        label='Cliente',
                        with_input=True
                    ).classes('flex-grow').props('dense outlined use-input input-debounce="300"')

                    def adicionar_cliente():
                        """Adiciona cliente selecionado (placeholder)."""
                        if cliente_select.value:
                            if cliente_select.value not in clientes_selecionados:
                                clientes_selecionados.append(cliente_select.value)
                                renderizar_chips_clientes.refresh()
                            else:
                                ui.notify('Cliente já adicionado!', type='warning')
                            cliente_select.value = None

                    ui.button(icon='add', text='Adicionar', on_click=adicionar_cliente).props(
                        'flat color=primary dense'
                    ).classes('mt-4')

                # Chips dos clientes selecionados
                @ui.refreshable
                def renderizar_chips_clientes():
                    if not clientes_selecionados:
                        ui.label('Nenhum cliente selecionado').classes(
                            'text-sm text-gray-400 italic py-2'
                        )
                        return

                    with ui.row().classes('w-full gap-2 flex-wrap py-2'):
                        for cliente_id in clientes_selecionados:
                            def remover_cliente(cid=cliente_id):
                                if cid in clientes_selecionados:
                                    clientes_selecionados.remove(cid)
                                    renderizar_chips_clientes.refresh()

                            with ui.element('div').classes(
                                'px-3 py-1 rounded-full flex items-center gap-1'
                            ).style('background-color: #e5e7eb;'):
                                ui.label(str(cliente_id)[:15]).classes('text-sm')
                                ui.button(
                                    icon='close',
                                    on_click=remover_cliente
                                ).props('flat dense round size=xs')

                renderizar_chips_clientes()

                # Outros envolvidos (placeholder - múltipla seleção com chips)
                with ui.row().classes('w-full gap-2 items-end mt-2'):
                    outros_select = ui.select(
                        options={},
                        label='Outros envolvidos',
                        with_input=True
                    ).classes('flex-grow').props('dense outlined use-input input-debounce="300"')

                    def adicionar_outro():
                        """Adiciona outro envolvido selecionado (placeholder)."""
                        if outros_select.value:
                            if outros_select.value not in outros_selecionados:
                                outros_selecionados.append(outros_select.value)
                                renderizar_chips_outros.refresh()
                            else:
                                ui.notify('Pessoa já adicionada!', type='warning')
                            outros_select.value = None

                    ui.button(icon='add', text='Adicionar', on_click=adicionar_outro).props(
                        'flat color=primary dense'
                    ).classes('mt-4')

                # Chips dos outros envolvidos selecionados
                @ui.refreshable
                def renderizar_chips_outros():
                    if not outros_selecionados:
                        ui.label('Nenhuma pessoa selecionada').classes(
                            'text-sm text-gray-400 italic py-2'
                        )
                        return

                    with ui.row().classes('w-full gap-2 flex-wrap py-2'):
                        for outro_id in outros_selecionados:
                            def remover_outro(oid=outro_id):
                                if oid in outros_selecionados:
                                    outros_selecionados.remove(oid)
                                    renderizar_chips_outros.refresh()

                            with ui.element('div').classes(
                                'px-3 py-1 rounded-full flex items-center gap-1'
                            ).style('background-color: #e5e7eb;'):
                                ui.label(str(outro_id)[:15]).classes('text-sm')
                                ui.button(
                                    icon='close',
                                    on_click=remover_outro
                                ).props('flat dense round size=xs')

                renderizar_chips_outros()

                # Caso vinculado (placeholder)
                caso_select = ui.select(
                    options={},
                    label='Caso vinculado',
                    with_input=True
                ).classes('w-full').props('dense outlined use-input input-debounce="300"')

                # Processo vinculado (placeholder)
                processo_select = ui.select(
                    options={},
                    label='Processo vinculado',
                    with_input=True
                ).classes('w-full').props('dense outlined use-input input-debounce="300"')

        # Botões
        ui.separator()
        with ui.row().classes('w-full justify-end gap-2 p-4'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            
            def salvar_acordo():
                """Salva o acordo (placeholder)."""
                titulo = titulo_input.value.strip()
                
                # Validação básica: título obrigatório
                if not titulo:
                    ui.notify('Título do acordo é obrigatório', type='negative')
                    return
                
                # Por enquanto, apenas notificação
                ui.notify('Acordo salvo com sucesso!', type='positive')
                dialog.close()
                
                if on_save:
                    on_save()
            
            ui.button('Salvar Acordo', on_click=salvar_acordo).props('color=primary')

    dialog.open()

