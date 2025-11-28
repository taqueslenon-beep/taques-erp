"""
Módulo de renderizadores de tabelas para o módulo Pessoas.
Contém funções para criar e renderizar tabelas de clientes, outros envolvidos e vínculos.
"""
from typing import Callable, Dict, Any, List
from nicegui import ui
from ...core import get_full_name, get_display_name
from .database import get_clients_list, get_opposing_parties_list, invalidate_cache
from .business_logic import (
    group_clients_by_type, prepare_client_row_data, prepare_opposing_row_data
)
from .validators import normalize_client_type_for_display, normalize_entity_type
from .models import CLIENTS_TABLE_COLUMNS, OPPOSING_TABLE_COLUMNS, CLIENT_GROUP_CONFIG


def create_table_slots(table: ui.table) -> None:
    """
    Adiciona slots padrão para tabelas (CPF/CNPJ com copiar, ações edit/delete).
    
    Args:
        table: Tabela NiceGUI onde adicionar os slots
    """
    table.add_slot('body-cell-cpf_cnpj', '''
        <q-td :props="props">
            <span v-if="props.value" class="text-gray-600 text-sm">{{ props.value }}</span>
            <q-btn 
                v-if="props.value"
                flat dense round 
                icon="content_copy" 
                size="xs" 
                color="grey"
                class="ml-1"
                @click.stop="navigator.clipboard.writeText(props.value); $q.notify({message: 'Copiado!', color: 'positive', position: 'top', timeout: 1000})"
            />
            <span v-else class="text-gray-300">-</span>
        </q-td>
    ''')
    
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat dense icon="edit" color="grey" @click="$parent.$emit('edit', props.row)" size="sm"/>
            <q-btn flat dense icon="delete" color="red" @click="$parent.$emit('delete', props.row)" size="sm"/>
        </q-td>
    ''')


def render_clients_table(
    on_edit: Callable,
    on_delete: Callable
) -> None:
    """
    Renderiza tabela de clientes agrupada por tipo (PJ primeiro, depois PF).
    
    Args:
        on_edit: Função chamada ao editar cliente (recebe índice)
        on_delete: Função chamada ao deletar cliente (recebe cliente)
    """
    # Busca lista de clientes do Firebase
    clients_data: List[Dict] = get_clients_list()
    
    if not clients_data:
        ui.label('Nenhum cliente cadastrado.').classes('text-gray-400 italic py-4')
        return
    
    def create_table(rows: List[Dict], clients_snapshot: List[Dict]):
        """Cria tabela com snapshot dos dados para evitar problemas de referência."""
        table = ui.table(columns=CLIENTS_TABLE_COLUMNS, rows=rows, row_key='id').classes('w-full').props('flat dense')
        create_table_slots(table)
        
        def handle_edit(e):
            idx = e.args['id']
            if 0 <= idx < len(clients_snapshot):
                on_edit(clients_snapshot[idx])
        
        def handle_delete(e):
            idx = e.args['id']
            if 0 <= idx < len(clients_snapshot):
                on_delete(clients_snapshot[idx])
        
        table.on('edit', handle_edit)
        table.on('delete', handle_delete)
    
    # Agrupa clientes com títulos descritivos
    for group_info in CLIENT_GROUP_CONFIG:
        internal_type = group_info['type']
        group_title = group_info['title']
        
        # Coleta clientes do tipo (normalizando tipos antes de filtrar)
        group_clients = [
            (idx, c) for idx, c in enumerate(clients_data) 
            if normalize_client_type_for_display(c) == internal_type
        ]
        
        # Ordena alfabeticamente por nome completo
        group_clients.sort(key=lambda x: get_full_name(x[1]).upper())
        
        # Título do grupo (sempre exibe, mesmo se vazio)
        ui.label(group_title).classes('font-bold text-primary text-lg mt-4 mb-3')
        
        # Prepara rows ordenadas
        rows = []
        for original_idx, client in group_clients:
            rows.append(prepare_client_row_data(client, original_idx))
        
        # Cria tabela mesmo se vazia (mostra mensagem apropriada)
        if rows:
            create_table(rows, clients_data)
        else:
            tipo_nome = 'Pessoas Jurídicas' if internal_type == 'PJ' else 'Pessoas Físicas'
            ui.label(f'Nenhum cliente {tipo_nome.lower()} cadastrado.').classes('text-gray-400 italic py-2 mb-4')


def render_opposing_table(
    on_edit: Callable,
    on_delete: Callable
) -> None:
    """
    Renderiza tabela de outros envolvidos.
    
    Args:
        on_edit: Função chamada ao editar outro envolvido (recebe outro envolvido)
        on_delete: Função chamada ao deletar outro envolvido (recebe outro envolvido)
    """
    # Busca lista de outros envolvidos do Firebase
    opposing_data: List[Dict] = get_opposing_parties_list()
    
    if not opposing_data:
        ui.label('Nenhum outro envolvido cadastrado.').classes('text-gray-400 italic py-4')
        return
    
    rows = []
    for i, opposing in enumerate(opposing_data):
        rows.append(prepare_opposing_row_data(opposing, i))
    
    table = ui.table(columns=OPPOSING_TABLE_COLUMNS, rows=rows, row_key='id').classes('w-full').props('flat dense')
    create_table_slots(table)
    
    def handle_edit(e):
        idx = e.args['id']
        if 0 <= idx < len(opposing_data):
            on_edit(opposing_data[idx])
    
    def handle_delete(e):
        idx = e.args['id']
        if 0 <= idx < len(opposing_data):
            on_delete(opposing_data[idx])
    
    table.on('edit', handle_edit)
    table.on('delete', handle_delete)


def render_bonds_map(
    on_add_bond: Callable,
    on_remove_bond: Callable
) -> None:
    """
    Renderiza mapa de vínculos entre pessoas.
    
    Args:
        on_add_bond: Função chamada ao adicionar vínculo (recebe índice do cliente)
        on_remove_bond: Função chamada ao remover vínculo (recebe índice do cliente e índice do vínculo)
    """
    # Busca lista de clientes do Firebase
    clients_data: List[Dict] = get_clients_list()
    
    if not clients_data:
        ui.label('Nenhum cliente cadastrado.').classes('text-gray-400 italic py-4')
        return
    
    for idx, client in enumerate(clients_data):
        bonds = client.get('bonds', [])
        cpf_cnpj = client.get('cpf_cnpj') or client.get('document', '')
        
        with ui.row().classes('w-full items-start py-2 border-b border-gray-100'):
            # Info do cliente
            with ui.column().classes('gap-0 min-w-48'):
                ui.label(get_display_name(client)).classes('font-medium text-sm')
                if cpf_cnpj:
                    ui.label(cpf_cnpj).classes('text-xs text-gray-400')
            
            # Vínculos
            with ui.row().classes('flex-grow gap-1 flex-wrap items-center'):
                if bonds:
                    for bond_idx, bond in enumerate(bonds):
                        with ui.element('div').classes('flex items-center gap-1 bg-gray-100 rounded px-2 py-1'):
                            ui.label(f"{bond.get('type', '')}: {bond.get('person', '')}").classes('text-xs text-gray-600')
                            ui.button(
                                icon='close', 
                                on_click=lambda ci=idx, bi=bond_idx: on_remove_bond(ci, bi)
                            ).props('flat dense round size=xs color=grey')
                else:
                    ui.label('-').classes('text-xs text-gray-300')
            
            # Botão adicionar
            ui.button(icon='add', on_click=lambda i=idx: on_add_bond(i)).props('flat dense round size=sm color=grey')

