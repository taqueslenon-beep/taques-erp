"""
prazos_page.py - Página principal do módulo Prazos.

Visualização em tabela dos prazos cadastrados com CRUD completo.
"""

from datetime import datetime
from typing import List, Dict, Any
from nicegui import ui
from ...core import layout, get_display_name
from ...auth import is_authenticated
from .database import (
    listar_prazos,
    buscar_prazo_por_id,
    criar_prazo,
    atualizar_prazo,
    excluir_prazo,
    buscar_usuarios_para_select,
    buscar_clientes_para_select,
    buscar_casos_para_select,
)
from .modal_prazo import render_prazo_dialog
from .models import STATUS_LABELS


def formatar_data_prazo(timestamp: Any) -> str:
    """
    Formata timestamp para exibição no padrão DD/MM/AAAA.
    
    Args:
        timestamp: Timestamp (float ou int) ou None
    
    Returns:
        String formatada ou '-' se inválida
    """
    if not timestamp:
        return '-'
    
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%d/%m/%Y')
        return str(timestamp)
    except Exception:
        return '-'


def formatar_lista_nomes(ids: List[str], opcoes: Dict[str, str]) -> str:
    """
    Formata lista de IDs para exibição de nomes separados por vírgula.
    
    Args:
        ids: Lista de IDs
        opcoes: Dicionário mapeando ID -> Nome
    
    Returns:
        String com nomes separados por vírgula ou '-'
    """
    if not ids:
        return '-'
    
    nomes = []
    for id_item in ids:
        if id_item in opcoes:
            nomes.append(opcoes[id_item])
    
    if not nomes:
        return '-'
    
    # Limita a 2 nomes para não ficar muito longo
    if len(nomes) > 2:
        return f"{', '.join(nomes[:2])}..."
    
    return ', '.join(nomes)


def obter_cor_status(status: str) -> str:
    """
    Retorna estilo CSS para badge baseado no status.
    
    Args:
        status: Status do prazo ('pendente' ou 'concluido')
    
    Returns:
        String de estilo CSS para o badge
    """
    if not status:
        return 'background-color: #d1d5db; color: #000000;'
    
    status_lower = status.lower()
    
    if status_lower == 'pendente':
        return 'background-color: #fde047; color: #000000;'  # Amarelo
    elif status_lower == 'concluido' or status_lower == 'concluído':
        return 'background-color: #4ade80; color: #000000;'  # Verde
    else:
        return 'background-color: #d1d5db; color: #000000;'  # Cinza padrão


@ui.page('/prazos')
def prazos():
    """Página principal do módulo Prazos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Carregar opções para formatação
    usuarios_opcoes = buscar_usuarios_para_select()
    clientes_opcoes = buscar_clientes_para_select()
    casos_opcoes = buscar_casos_para_select()
    
    # Função callback após salvar
    def on_prazo_salvo(prazo_data: Dict[str, Any]):
        """Callback executado após salvar prazo."""
        try:
            prazo_id = prazo_data.get('_id')
            if prazo_id:
                # Já foi salvo no modal, só atualizar tabela
                render_tabela.refresh()
            else:
                ui.notify('Erro: ID do prazo não retornado', type='negative')
        except Exception as e:
            print(f"[ERROR] Erro ao processar prazo salvo: {e}")
            ui.notify('Erro ao atualizar lista. Tente recarregar.', type='negative')
    
    # Dialog para novo prazo
    dialog_novo, open_dialog_novo = render_prazo_dialog(on_success=on_prazo_salvo)
    
    # Função para abrir modal de edição
    def abrir_modal_edicao(prazo_id: str):
        """Abre modal de edição com dados do prazo."""
        try:
            prazo = buscar_prazo_por_id(prazo_id)
            if not prazo:
                ui.notify('Prazo não encontrado!', type='negative')
                return
            
            # Criar dialog de edição
            dialog_edit, open_edit = render_prazo_dialog(
                on_success=on_prazo_salvo,
                prazo_inicial=prazo
            )
            open_edit()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir modal de edição: {e}")
            ui.notify('Erro ao carregar dados do prazo. Tente novamente.', type='negative')
    
    # Função para excluir prazo
    def excluir_prazo_com_confirmacao(prazo_id: str, titulo: str):
        """Exclui prazo com diálogo de confirmação."""
        with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Confirmar Exclusão').classes('text-lg font-bold')
                ui.label(f'Tem certeza que deseja excluir o prazo "{titulo}"?').classes('text-gray-700')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_excluir.close()
                    
                    def on_confirm():
                        try:
                            sucesso = excluir_prazo(prazo_id)
                            if sucesso:
                                ui.notify('Prazo excluído com sucesso!', type='positive')
                                render_tabela.refresh()
                            else:
                                ui.notify('Erro ao excluir prazo', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao excluir prazo: {e}")
                            ui.notify(f'Erro ao excluir prazo: {str(e)}', type='negative')
                        
                        dialog_excluir.close()
                    
                    ui.button('Cancelar', on_click=on_cancel).props('flat')
                    ui.button('Excluir', on_click=on_confirm).props('color=red')
        
        dialog_excluir.open()
    
    with layout('Prazos', breadcrumbs=[('Prazos', None)]):
        # Header com botão (título removido - já vem do layout())
        with ui.row().classes('w-full gap-4 mb-6 items-center justify-end'):
            ui.button('Adicionar Prazo', icon='add', on_click=open_dialog_novo).props(
                'color=primary'
            ).classes('font-bold')
        
        # Container para tabela
        tabela_container = ui.column().classes('w-full')
        
        @ui.refreshable
        def render_tabela():
            """Renderiza tabela de prazos."""
            tabela_container.clear()
            
            with tabela_container:
                try:
                    # Buscar prazos (já ordenados por prazo_fatal)
                    prazos_lista = listar_prazos()
                    
                    if not prazos_lista:
                        # Mensagem quando não há prazos
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('calendar_month', size='48px').classes('text-gray-300 mb-4')
                            ui.label('Nenhum prazo cadastrado').classes(
                                'text-gray-500 text-lg font-medium mb-2'
                            )
                            ui.label('Clique em "Adicionar Prazo" para criar o primeiro').classes(
                                'text-sm text-gray-400 text-center'
                            )
                        return
                    
                    # Definir colunas da tabela
                    columns = [
                        {'name': 'concluido', 'label': '', 'field': 'concluido', 'align': 'center', 'style': 'width: 50px;'},
                        {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left'},
                        {'name': 'responsaveis', 'label': 'Responsáveis', 'field': 'responsaveis', 'align': 'left', 'style': 'width: 200px;'},
                        {'name': 'clientes', 'label': 'Clientes', 'field': 'clientes', 'align': 'left', 'style': 'width: 200px;'},
                        {'name': 'prazo_fatal', 'label': 'Prazo Fatal', 'field': 'prazo_fatal', 'align': 'center', 'style': 'width: 120px;'},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'style': 'width: 120px;'},
                        {'name': 'recorrente', 'label': 'Recorrente', 'field': 'recorrente', 'align': 'center', 'style': 'width: 100px;'},
                        {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 120px;'},
                    ]
                    
                    # Preparar linhas
                    rows = []
                    for prazo in prazos_lista:
                        # Formatações
                        titulo = prazo.get('titulo', '-')
                        
                        responsaveis_ids = prazo.get('responsaveis', [])
                        responsaveis_texto = formatar_lista_nomes(
                            responsaveis_ids,
                            usuarios_opcoes
                        )
                        
                        clientes_ids = prazo.get('clientes', [])
                        clientes_texto = formatar_lista_nomes(
                            clientes_ids,
                            clientes_opcoes
                        )
                        
                        prazo_fatal_ts = prazo.get('prazo_fatal')
                        prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
                        
                        status = prazo.get('status', 'pendente')
                        status_label = STATUS_LABELS.get(status, status)
                        
                        recorrente = prazo.get('recorrente', False)
                        recorrente_texto = 'Sim' if recorrente else 'Não'
                        
                        # Determina se está concluído
                        is_concluido = status.lower() in ['concluido', 'concluído']

                        rows.append({
                            'id': prazo.get('_id'),
                            'concluido': is_concluido,
                            'titulo': titulo,
                            'responsaveis': responsaveis_texto,
                            'clientes': clientes_texto,
                            'prazo_fatal': prazo_fatal_texto,
                            'status': status_label,
                            'status_value': status,
                            'recorrente': recorrente_texto,
                            'acoes': prazo.get('_id'),
                        })
                    
                    # Criar tabela
                    table = ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='id'
                    ).classes('w-full').props('flat dense')

                    # Slot para checkbox arredondado (marcar como concluído)
                    table.add_slot('body-cell-concluido', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <q-checkbox
                                :model-value="props.row.concluido"
                                @update:model-value="(val) => $parent.$emit('toggle-status', {...props.row, novo_status: val})"
                                color="positive"
                                round
                                size="md"
                            >
                                <q-tooltip>{{ props.row.concluido ? 'Marcar como Pendente' : 'Marcar como Concluído' }}</q-tooltip>
                            </q-checkbox>
                        </q-td>
                    ''')

                    # Slot para status com badge colorido
                    table.add_slot('body-cell-status', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <q-badge 
                                :style="props.row.status_value === 'pendente' ? 'background-color: #fde047; color: #000000;' : 
                                        (props.row.status_value === 'concluido' || props.row.status_value === 'concluído') ? 'background-color: #4ade80; color: #000000;' : 
                                        'background-color: #d1d5db; color: #000000;'"
                                class="px-3 py-1"
                                style="border: 1px solid rgba(0,0,0,0.1);"
                            >
                                {{ props.value }}
                            </q-badge>
                        </q-td>
                    ''')
                    
                    # Slot para ações (editar e excluir)
                    table.add_slot('body-cell-acoes', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <q-btn 
                                flat 
                                round 
                                dense 
                                icon="edit" 
                                color="primary" 
                                size="sm"
                                @click="$parent.$emit('edit', props.row)"
                            >
                                <q-tooltip>Editar</q-tooltip>
                            </q-btn>
                            <q-btn 
                                flat 
                                round 
                                dense 
                                icon="delete" 
                                color="negative" 
                                size="sm"
                                @click="$parent.$emit('delete', props.row)"
                            >
                                <q-tooltip>Excluir</q-tooltip>
                            </q-btn>
                        </q-td>
                    ''')
                    
                    # Handlers para ações
                    def on_edit(prazo_row):
                        """Handler para editar prazo."""
                        prazo_id = prazo_row.get('id')
                        if prazo_id:
                            abrir_modal_edicao(prazo_id)
                        else:
                            ui.notify('Erro: ID do prazo não encontrado', type='negative')
                    
                    def on_delete(prazo_row):
                        """Handler para excluir prazo."""
                        prazo_id = prazo_row.get('id')
                        titulo = prazo_row.get('titulo', 'este prazo')
                        if prazo_id:
                            excluir_prazo_com_confirmacao(prazo_id, titulo)
                        else:
                            ui.notify('Erro: ID do prazo não encontrado', type='negative')

                    def on_toggle_status(prazo_row):
                        """Handler para alternar status do prazo (checkbox)."""
                        prazo_id = prazo_row.get('id')
                        novo_status_bool = prazo_row.get('novo_status', False)
                        novo_status = 'concluido' if novo_status_bool else 'pendente'

                        if prazo_id:
                            try:
                                sucesso = atualizar_prazo(prazo_id, {'status': novo_status})
                                if sucesso:
                                    msg = 'Prazo concluído!' if novo_status_bool else 'Prazo reaberto!'
                                    ui.notify(msg, type='positive')
                                    render_tabela.refresh()
                                else:
                                    ui.notify('Erro ao atualizar status', type='negative')
                            except Exception as e:
                                print(f"[ERROR] Erro ao atualizar status: {e}")
                                ui.notify('Erro ao atualizar status', type='negative')
                        else:
                            ui.notify('Erro: ID do prazo não encontrado', type='negative')

                    table.on('edit', lambda e: on_edit(e.args))
                    table.on('delete', lambda e: on_delete(e.args))
                    table.on('toggle-status', lambda e: on_toggle_status(e.args))
                    
                except Exception as e:
                    # Tratamento de erro
                    print(f"[ERROR] Erro ao carregar prazos: {e}")
                    import traceback
                    traceback.print_exc()
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('error', size='48px').classes('text-red-400 mb-4')
                        ui.label('Erro ao carregar prazos').classes(
                            'text-red-600 text-lg font-medium mb-2'
                        )
                        ui.label('Tente recarregar a página').classes(
                            'text-sm text-gray-500 text-center'
                        )
        
        # Renderizar tabela inicial
        render_tabela()

