"""
lista_clausulas.py - Visualização de lista de cláusulas.
"""

from nicegui import ui
from typing import List, Dict, Any, Optional, Callable
from ..business_logic import formatar_data_para_exibicao


def lista_clausulas(
    clausulas: List[Dict[str, Any]],
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None
) -> Optional[ui.table]:
    """
    Renderiza lista de cláusulas em formato de tabela.
    
    Args:
        clausulas: Lista de dicionários com dados das cláusulas
        on_edit: Callback para editar (recebe index)
        on_delete: Callback para deletar (recebe index)
    
    Returns:
        Componente ui.table ou None se não houver cláusulas
    """
    if not clausulas:
        with ui.card().classes('w-full p-8 flex justify-center items-center'):
            ui.label('Nenhuma cláusula adicionada.').classes('text-gray-400 italic')
        return None
    
    # Função para ordenar cláusulas por número (se houver) ou mantém ordem original
    def sort_key(c):
        numero = c.get('numero', '')
        if numero:
            try:
                num_clean = numero.replace('.', '').strip()
                if num_clean.isdigit():
                    return (0, int(num_clean))
                parts = numero.split('.')
                if all(p.isdigit() for p in parts):
                    return (0, tuple(int(p) for p in parts))
            except:
                pass
            return (1, numero.lower())
        return (2, c.get('titulo', '').lower())
    
    # Define colunas da tabela
    columns = [
        {'name': 'numero_seq', 'label': '#', 'field': 'numero_seq', 'align': 'center', 'sortable': True, 'style': 'width: 50px;'},
        {'name': 'numero_clausula', 'label': 'Número', 'field': 'numero_clausula', 'align': 'left', 'sortable': True, 'style': 'width: 120px;'},
        {'name': 'titulo', 'label': 'Título da Cláusula', 'field': 'titulo', 'align': 'left', 'sortable': True},
        {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'center', 'sortable': True, 'style': 'width: 100px;'},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 120px;'},
        {'name': 'prazos', 'label': 'Prazos', 'field': 'prazos', 'align': 'left', 'sortable': False, 'style': 'width: 200px;'},
        {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 80px;'},
    ]
    
    # Prepara linhas - preserva índice original antes da ordenação
    clausulas_com_indice = [(idx, clausula) for idx, clausula in enumerate(clausulas)]
    
    def sort_key_with_index(item):
        idx, clausula = item
        return (sort_key(clausula), idx)
    
    clausulas_ordenadas_com_indice = sorted(clausulas_com_indice, key=sort_key_with_index)
    
    rows = []
    for seq_idx, (original_idx, clausula) in enumerate(clausulas_ordenadas_com_indice):
        numero = clausula.get('numero', '')
        titulo = clausula.get('titulo', 'Sem título')
        tipo = clausula.get('tipo_clausula', '')
        status = clausula.get('status', 'Pendente')
        
        # Formata prazos
        prazo_seg = formatar_data_para_exibicao(clausula.get('prazo_seguranca', ''))
        prazo_fatal = formatar_data_para_exibicao(clausula.get('prazo_fatal', ''))
        prazos_display = ''
        if prazo_seg and prazo_seg != '-' and prazo_fatal and prazo_fatal != '-':
            prazos_display = f'{prazo_seg} | {prazo_fatal}'
        elif prazo_seg and prazo_seg != '-':
            prazos_display = f'Seg: {prazo_seg}'
        elif prazo_fatal and prazo_fatal != '-':
            prazos_display = f'Fatal: {prazo_fatal}'
        else:
            prazos_display = '-'
        
        rows.append({
            'numero_seq': seq_idx + 1,
            'numero_clausula': numero if numero else '-',
            'titulo': titulo,
            'tipo': tipo if tipo else '-',
            'status': status,
            'prazos': prazos_display,
            'acoes': '',
            '_original_index': original_idx,
            '_clausula_data': clausula
        })
    
    # CSS para estilização da tabela de cláusulas
    clausulas_table_css = '''
        .clausulas-table .q-table__top {
            padding: 8px 12px;
        }
        .clausulas-table .q-table tbody tr:hover {
            background-color: #f9fafb !important;
        }
        .clausulas-table .q-table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }
        .clausulas-table .q-table tbody tr:nth-child(odd) {
            background-color: #ffffff;
        }
        .clausulas-table .q-table thead th {
            background-color: #f3f4f6;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }
    '''
    ui.add_head_html(f'<style>{clausulas_table_css}</style>')
    
    # Cria tabela
    table = ui.table(
        columns=columns,
        rows=rows,
        row_key='numero_seq',
        pagination={'rowsPerPage': 10}
    ).classes('w-full clausulas-table')
    
    # Slots da tabela (mesmo código do original)
    table.add_slot('body-cell-numero_seq', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <span class="text-sm text-gray-600 font-medium">{{ props.value }}</span>
        </q-td>
    ''')
    
    table.add_slot('body-cell-numero_clausula', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <span class="text-xs text-gray-700">{{ props.value || '-' }}</span>
        </q-td>
    ''')
    
    table.add_slot('body-cell-titulo', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <div class="text-sm font-medium text-gray-800" style="white-space: normal; word-wrap: break-word;">
                {{ props.value || 'Sem título' }}
            </div>
        </q-td>
    ''')
    
    table.add_slot('body-cell-tipo', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <q-badge 
                v-if="props.value && props.value !== '-'"
                :color="props.value.toLowerCase().includes('geral') ? 'blue' : 'purple'" 
                :label="props.value" 
                style="text-transform: capitalize;" />
            <span v-else class="text-gray-400 text-xs">—</span>
        </q-td>
    ''')
    
    table.add_slot('body-cell-status', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <q-badge 
                :color="!props.value || props.value.toLowerCase().includes('cumprida') ? 'green' : 
                        props.value.toLowerCase().includes('pendente') ? 'orange' : 
                        props.value.toLowerCase().includes('atrasada') ? 'red' : 'grey'" 
                :label="props.value || 'Pendente'" />
        </q-td>
    ''')
    
    table.add_slot('body-cell-prazos', '''
        <q-td :props="props" style="padding: 8px 12px; vertical-align: middle;">
            <span class="text-xs text-gray-700">{{ props.value || '-' }}</span>
        </q-td>
    ''')
    
    table.add_slot('body-cell-acoes', '''
        <q-td :props="props" style="text-align: center; padding: 8px 12px; vertical-align: middle;">
            <div style="display: flex; justify-content: center; gap: 4px;">
                <q-btn 
                    flat dense round 
                    icon="edit" 
                    size="sm" 
                    color="primary"
                    @click="$parent.$emit('editClausula', props.row._original_index)"
                />
                <q-btn 
                    flat dense round 
                    icon="delete" 
                    size="sm" 
                    color="red"
                    @click="$parent.$emit('deleteClausula', props.row._original_index)"
                />
            </div>
        </q-td>
    ''')
    
    # Handlers para ações
    if on_edit:
        def handle_edit(e):
            try:
                index = e.args
                if index is not None and isinstance(index, int):
                    if 0 <= index < len(clausulas):
                        on_edit(index)
                    else:
                        ui.notify('Índice de cláusula inválido!', type='warning')
                else:
                    ui.notify('Erro ao editar cláusula: índice inválido.', type='warning')
            except Exception as ex:
                ui.notify(f'Erro ao editar cláusula: {str(ex)}', type='negative')
        table.on('editClausula', handle_edit)
    
    if on_delete:
        def handle_delete(e):
            try:
                index = e.args
                if index is not None and isinstance(index, int):
                    if 0 <= index < len(clausulas):
                        on_delete(index)
                    else:
                        ui.notify('Índice de cláusula inválido!', type='warning')
                else:
                    ui.notify('Erro ao deletar cláusula: índice inválido.', type='warning')
            except Exception as ex:
                ui.notify(f'Erro ao deletar cláusula: {str(ex)}', type='negative')
        table.on('deleteClausula', handle_delete)
    
    return table

