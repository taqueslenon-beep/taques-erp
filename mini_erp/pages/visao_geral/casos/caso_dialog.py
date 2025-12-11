"""
Dialogs para criação, edição e exclusão de casos.
Workspace: Visão geral do escritório

Formulário simplificado com campos:
- titulo, nucleo, status, categoria, estado, clientes, descricao
"""
from nicegui import ui
from typing import Optional, Callable
from .database import criar_caso, atualizar_caso
from .models import (
    NUCLEO_OPTIONS, STATUS_OPTIONS, CATEGORIA_OPTIONS, ESTADOS,
    criar_caso_vazio, validar_caso
)
# Usar coleção 'vg_pessoas' que tem 108 pessoas cadastradas
from ....firebase_config import get_db


def _carregar_pessoas_para_select():
    """Carrega pessoas da coleção 'vg_pessoas' para o select."""
    resultado = []
    try:
        db = get_db()
        if not db:
            print('[CASO_DIALOG] ❌ Conexão Firebase não disponível')
            return resultado

        for doc in db.collection('vg_pessoas').stream():
            dados = doc.to_dict()
            # Tentar diferentes campos de nome
            nome = dados.get('nome_exibicao') or dados.get('full_name') or dados.get('name') or ''
            if nome and doc.id:
                resultado.append({
                    '_id': doc.id,
                    'nome_exibicao': nome,
                    'full_name': nome
                })

        # Ordenar por nome
        resultado.sort(key=lambda p: p.get('nome_exibicao', '').lower())
        print(f'[CASO_DIALOG] ✅ {len(resultado)} pessoas carregadas da coleção vg_pessoas')
    except Exception as e:
        print(f'[CASO_DIALOG] ❌ Erro ao carregar pessoas: {e}')
        import traceback
        traceback.print_exc()
    return resultado


def abrir_dialog_caso(caso: Optional[dict] = None, on_save: Optional[Callable] = None):
    """
    Abre dialog para criar ou editar um caso.

    Args:
        caso: Dicionário com dados do caso (None para criar novo)
        on_save: Callback executado após salvar com sucesso
    """
    is_edicao = caso is not None
    dados = caso.copy() if caso else criar_caso_vazio()

    # Carregar clientes da coleção 'clients' (108+ pessoas)
    todas_pessoas = _carregar_pessoas_para_select()

    # Estado local para clientes selecionados
    clientes_selecionados = list(dados.get('clientes', []))
    todos_selecionados = {'value': False}

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
        # Header
        with ui.row().classes('w-full items-center justify-between p-4'):
            ui.label('Editar Caso' if is_edicao else 'Novo Caso').classes(
                'text-xl font-bold text-gray-800'
            )
            ui.button(icon='close', on_click=dialog.close).props('flat dense round')

        ui.separator()

        # Container do formulário com scroll
        with ui.scroll_area().classes('w-full').style('max-height: 70vh'):
            with ui.column().classes('w-full gap-4 p-4'):

                # Linha 1: Título (largura total)
                titulo_input = ui.input(
                    label='Título do Caso *',
                    value=dados.get('titulo', ''),
                    placeholder='Digite o título do caso...'
                ).classes('w-full').props('dense outlined')

                # Linha 2: Núcleo, Status, Categoria
                with ui.row().classes('w-full gap-4'):
                    nucleo_select = ui.select(
                        options=NUCLEO_OPTIONS,
                        value=dados.get('nucleo', 'Generalista'),
                        label='Núcleo *'
                    ).classes('flex-1').props('dense outlined')

                    status_select = ui.select(
                        options=STATUS_OPTIONS,
                        value=dados.get('status', 'Em andamento'),
                        label='Status'
                    ).classes('flex-1').props('dense outlined')

                    categoria_select = ui.select(
                        options=CATEGORIA_OPTIONS,
                        value=dados.get('categoria', 'Contencioso'),
                        label='Categoria'
                    ).classes('flex-1').props('dense outlined')

                # Linha 3: Estado
                estado_select = ui.select(
                    options=[''] + ESTADOS,
                    value=dados.get('estado', 'Santa Catarina'),
                    label='Estado'
                ).classes('w-full').props('dense outlined clearable')

                # Seção Clientes
                ui.separator().classes('my-2')
                ui.label('CLIENTES').classes('text-sm font-bold text-gray-600')

                # Dropdown para adicionar cliente + botão
                with ui.row().classes('w-full gap-2 items-end'):
                    # Preparar opções de clientes: dict {id: nome} para ui.select
                    opcoes_clientes = {
                        p['_id']: p.get('nome_exibicao', p.get('full_name', 'Sem nome'))
                        for p in todas_pessoas
                        if p.get('_id')
                    }
                    print(f'[CASO_DIALOG] Opções do select: {len(opcoes_clientes)} clientes')

                    cliente_select = ui.select(
                        options=opcoes_clientes,
                        label='Buscar pessoa...',
                        with_input=True
                    ).classes('flex-grow').props('dense outlined use-input input-debounce="300" clearable')

                    def adicionar_cliente():
                        if cliente_select.value:
                            if cliente_select.value not in clientes_selecionados:
                                clientes_selecionados.append(cliente_select.value)
                                todos_selecionados['value'] = False
                                todos_checkbox.value = False
                                renderizar_chips.refresh()
                            else:
                                ui.notify('Cliente já adicionado!', type='warning')
                            cliente_select.value = None

                    ui.button(icon='add', on_click=adicionar_cliente).props(
                        'flat color=primary dense'
                    ).classes('mt-4')

                # Checkbox "Todos"
                def toggle_todos(checked):
                    todos_selecionados['value'] = checked
                    if checked:
                        clientes_selecionados.clear()
                        clientes_selecionados.extend([p['_id'] for p in todas_pessoas])
                        ui.notify(f'Todos os {len(todas_pessoas)} clientes adicionados!', type='positive')
                    else:
                        clientes_selecionados.clear()
                    renderizar_chips.refresh()

                todos_checkbox = ui.checkbox(
                    text=f'Todos ({len(todas_pessoas)})',
                    value=todos_selecionados['value'],
                    on_change=lambda e: toggle_todos(e.value)
                ).classes('mt-2')

                # Chips dos clientes selecionados
                @ui.refreshable
                def renderizar_chips():
                    if not clientes_selecionados:
                        ui.label('Nenhum cliente selecionado').classes(
                            'text-sm text-gray-400 italic py-2'
                        )
                        return

                    with ui.row().classes('w-full gap-2 flex-wrap py-2'):
                        # Se todos selecionados, mostrar chip especial
                        if todos_selecionados['value'] and len(clientes_selecionados) == len(todas_pessoas):
                            with ui.element('div').classes(
                                'px-3 py-1 rounded-full flex items-center gap-2'
                            ).style('background-color: #3b82f6; color: white;'):
                                ui.icon('check_circle', size='16px')
                                ui.label(f'Todos os Clientes ({len(clientes_selecionados)})').classes('text-sm font-medium')
                        else:
                            # Mostrar chips individuais (limitado a 10 para performance)
                            exibir = clientes_selecionados[:10]
                            for cliente_id in exibir:
                                # Buscar nome do dicionário opcoes_clientes
                                nome = opcoes_clientes.get(cliente_id, cliente_id)
                                # Nome curto (primeiro nome ou sigla)
                                nome_curto = nome.split()[0] if ' ' in nome else nome
                                if len(nome_curto) > 15:
                                    nome_curto = nome_curto[:15] + '...'

                                def remover(cid=cliente_id):
                                    if cid in clientes_selecionados:
                                        clientes_selecionados.remove(cid)
                                        todos_selecionados['value'] = False
                                        todos_checkbox.value = False
                                        renderizar_chips.refresh()

                                with ui.element('div').classes(
                                    'px-3 py-1 rounded-full flex items-center gap-1'
                                ).style('background-color: #e5e7eb;'):
                                    ui.label(nome_curto).classes('text-sm').tooltip(nome)
                                    ui.button(
                                        icon='close',
                                        on_click=remover
                                    ).props('flat dense round size=xs')

                            # Indicador de mais clientes
                            if len(clientes_selecionados) > 10:
                                ui.label(f'+{len(clientes_selecionados) - 10} mais').classes(
                                    'text-sm text-gray-500 italic'
                                )

                renderizar_chips()

                # Descrição
                ui.separator().classes('my-2')
                descricao_input = ui.textarea(
                    label='Descrição',
                    value=dados.get('descricao', ''),
                    placeholder='Descrição do caso (opcional)...'
                ).classes('w-full').props('dense outlined rows=3')

        ui.separator()

        # Footer com botões
        with ui.row().classes('w-full justify-end gap-2 p-4'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def salvar():
                # Coleta dados do formulário (simplificado)
                # Usar dicionário opcoes_clientes para obter nomes
                nomes_clientes = [opcoes_clientes.get(cid, '') for cid in clientes_selecionados]

                novos_dados = {
                    'titulo': titulo_input.value.strip() if titulo_input.value else '',
                    'nucleo': nucleo_select.value or 'Generalista',
                    'status': status_select.value or 'Em andamento',
                    'categoria': categoria_select.value or 'Contencioso',
                    'estado': estado_select.value or '',
                    'clientes': clientes_selecionados.copy(),
                    'clientes_nomes': nomes_clientes,
                    'descricao': descricao_input.value.strip() if descricao_input.value else '',
                }

                # Validação
                valido, erro = validar_caso(novos_dados)
                if not valido:
                    ui.notify(erro, type='negative')
                    return

                # Salvar
                try:
                    if is_edicao:
                        sucesso = atualizar_caso(dados['_id'], novos_dados)
                        msg = 'Caso atualizado com sucesso!'
                    else:
                        caso_id = criar_caso(novos_dados)
                        sucesso = caso_id is not None
                        msg = 'Caso criado com sucesso!'

                    if sucesso:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        if on_save:
                            on_save()
                    else:
                        ui.notify('Erro ao salvar caso.', type='negative')
                except Exception as e:
                    print(f"Erro ao salvar caso: {e}")
                    ui.notify(f'Erro ao salvar: {str(e)}', type='negative')

            ui.button('Salvar', icon='save', on_click=salvar).props('color=primary')

    dialog.open()


def confirmar_exclusao(caso: dict, on_confirm: Optional[Callable] = None):
    """
    Dialog de confirmação de exclusão de caso.

    Args:
        caso: Dicionário com dados do caso a excluir
        on_confirm: Callback executado ao confirmar exclusão
    """
    titulo = caso.get('titulo', 'Caso')

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        # Header com ícone de alerta
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('warning', color='negative', size='32px')
            ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800')

        # Mensagem
        ui.label(f'Deseja realmente excluir o caso "{titulo}"?').classes(
            'text-gray-600 mb-2'
        )
        ui.label('Esta ação não pode ser desfeita.').classes(
            'text-sm text-red-500 mb-4'
        )

        # Botões
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def executar_exclusao():
                dialog.close()
                if on_confirm:
                    on_confirm()

            ui.button('Excluir', on_click=executar_exclusao).props('color=negative')

    dialog.open()
