"""
modal_visualizar_clausulas.py - Modal para visualizar cláusulas de um acordo em formato de tabela.
"""

from nicegui import ui
from typing import List, Dict, Any


def render_visualizar_clausulas_dialog(clausulas: List[Dict[str, Any]], titulo_acordo: str = ''):
    """
    Renderiza dialog para visualizar cláusulas de um acordo em formato de tabela.
    
    Args:
        clausulas: Lista de dicionários com dados das cláusulas
        titulo_acordo: Título do acordo (opcional, para exibição no cabeçalho)
    
    Returns:
        tuple: (dialog, open_function)
    """
    
    # CSS para melhorar a aparência da tabela
    TABLE_CSS = '''
        .clausulas-table .q-table__top {
            padding: 12px 16px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }
        .clausulas-table .q-table thead tr th {
            background: #f3f4f6;
            font-weight: 600;
            font-size: 13px;
            color: #374151;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 12px 8px;
        }
        .clausulas-table .q-table tbody tr {
            border-bottom: 1px solid #e5e7eb;
        }
        .clausulas-table .q-table tbody tr:hover {
            background: #f9fafb;
        }
        .clausulas-table .q-table tbody tr:nth-child(even) {
            background: #fafafa;
        }
        .clausulas-table .q-table tbody tr:nth-child(even):hover {
            background: #f3f4f6;
        }
        .clausulas-table .q-table tbody td {
            padding: 12px 8px;
            font-size: 13px;
        }
    '''
    
    ui.add_head_html(f'<style>{TABLE_CSS}</style>')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-7xl p-0 overflow-hidden').style('max-height: 90vh;'):
        
        # Cabeçalho do modal
        with ui.row().classes('w-full p-5 items-center justify-between').style('border-bottom: 2px solid #e5e7eb; background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);'):
            with ui.column().classes('gap-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('table_chart', size='28px').classes('text-primary')
                    ui.label('Cláusulas do Acordo').classes('text-xl font-bold text-gray-800')
                if titulo_acordo:
                    ui.label(titulo_acordo).classes('text-sm text-gray-600 ml-10')
            
            ui.button(icon='close', on_click=dialog.close).props('flat dense round').classes('text-gray-500 hover:bg-gray-200')
        
        # Conteúdo com scroll
        with ui.column().classes('w-full overflow-y-auto bg-white').style('max-height: calc(90vh - 140px);'):
            
            if not clausulas:
                # Mensagem quando não há cláusulas
                with ui.card().classes('w-full p-16 flex flex-col items-center justify-center m-4').style('border: 2px dashed #e5e7eb; background: #fafafa;'):
                    ui.icon('note_add', size='80px').classes('text-gray-300 mb-4')
                    ui.label('Nenhuma cláusula cadastrada').classes(
                        'text-gray-600 text-xl font-semibold mb-2'
                    )
                    ui.label('Este acordo ainda não possui cláusulas cadastradas.').classes(
                        'text-sm text-gray-500 text-center'
                    )
            else:
                # Estatísticas rápidas
                total = len(clausulas)
                cumpridas = sum(1 for c in clausulas if c.get('status') == 'Cumprida')
                pendentes = sum(1 for c in clausulas if c.get('status') == 'Pendente')
                atrasadas = sum(1 for c in clausulas if c.get('status') == 'Atrasada')
                
                with ui.row().classes('w-full p-4 gap-3 bg-gray-50').style('border-bottom: 1px solid #e5e7eb;'):
                    with ui.card().classes('flex-1 p-3').style('border: 1px solid #e0e0e0; background: white;'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('list', size='20px').classes('text-blue-500')
                            ui.label('Total').classes('text-xs text-gray-500')
                        ui.label(str(total)).classes('text-2xl font-bold text-gray-800 mt-1')
                    
                    with ui.card().classes('flex-1 p-3').style('border: 1px solid #e0e0e0; background: white;'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('check_circle', size='20px').classes('text-green-500')
                            ui.label('Cumpridas').classes('text-xs text-gray-500')
                        ui.label(str(cumpridas)).classes('text-2xl font-bold text-green-600 mt-1')
                    
                    with ui.card().classes('flex-1 p-3').style('border: 1px solid #e0e0e0; background: white;'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('schedule', size='20px').classes('text-orange-500')
                            ui.label('Pendentes').classes('text-xs text-gray-500')
                        ui.label(str(pendentes)).classes('text-2xl font-bold text-orange-600 mt-1')
                    
                    with ui.card().classes('flex-1 p-3').style('border: 1px solid #e0e0e0; background: white;'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('warning', size='20px').classes('text-red-500')
                            ui.label('Atrasadas').classes('text-xs text-gray-500')
                        ui.label(str(atrasadas)).classes('text-2xl font-bold text-red-600 mt-1')
                
                # Tabela de cláusulas
                columns = [
                    {'name': 'numero', 'label': 'Nº', 'field': 'numero', 'align': 'center', 'style': 'width: 70px; font-weight: 600;'},
                    {'name': 'titulo', 'label': 'Título da Cláusula', 'field': 'titulo', 'align': 'left', 'style': 'min-width: 300px;'},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'center', 'style': 'width: 140px;'},
                    {'name': 'prazo_seguranca', 'label': 'Prazo Segurança', 'field': 'prazo_seguranca', 'align': 'center', 'style': 'width: 150px;'},
                    {'name': 'prazo_fatal', 'label': 'Prazo Fatal', 'field': 'prazo_fatal', 'align': 'center', 'style': 'width: 150px;'},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'style': 'width: 130px;'},
                ]
                
                # Preparar linhas
                rows = []
                for idx, clausula in enumerate(clausulas):
                    # Prazos
                    if clausula.get('regular'):
                        prazo_seg = 'Regular'
                        prazo_fat = '-'
                    else:
                        prazo_seg = clausula.get('prazo_seguranca', '-') or '-'
                        prazo_fat = clausula.get('prazo_fatal', '-') or '-'
                    
                    rows.append({
                        'id': idx + 1,
                        'numero': clausula.get('numero', f'#{idx + 1}'),
                        'titulo': clausula.get('titulo', 'Sem título'),
                        'tipo': clausula.get('tipo', '-'),
                        'prazo_seguranca': prazo_seg,
                        'prazo_fatal': prazo_fat,
                        'status': clausula.get('status', '-'),
                        'regular': clausula.get('regular', False),
                    })
                
                # Criar tabela
                table = ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='id'
                ).classes('w-full clausulas-table').props('flat bordered')
                
                # Slot para número (com badge)
                table.add_slot('body-cell-numero', '''
                    <q-td :props="props" style="vertical-align: middle;">
                        <q-badge 
                            color="primary" 
                            :label="props.value"
                            class="px-2 py-1"
                            style="font-weight: 600;"
                        />
                    </q-td>
                ''')
                
                # Slot para título (com quebra de linha se necessário)
                table.add_slot('body-cell-titulo', '''
                    <q-td :props="props" style="vertical-align: middle;">
                        <div style="max-width: 400px; word-wrap: break-word; line-height: 1.4;">
                            {{ props.value }}
                        </div>
                    </q-td>
                ''')
                
                # Slot para tipo
                table.add_slot('body-cell-tipo', '''
                    <q-td :props="props" style="vertical-align: middle;">
                        <span style="font-size: 12px; color: #6b7280;">{{ props.value || '-' }}</span>
                    </q-td>
                ''')
                
                # Slot para prazo segurança (com destaque para "Regular")
                table.add_slot('body-cell-prazo_seguranca', '''
                    <q-td :props="props" style="vertical-align: middle;">
                        <div v-if="props.row.regular" style="display: flex; align-items: center; justify-content: center;">
                            <q-badge 
                                color="positive" 
                                label="Regular"
                                class="px-3 py-1"
                                style="font-weight: 600;"
                            />
                        </div>
                        <span v-else style="font-size: 12px; color: #374151;">{{ props.value || '-' }}</span>
                    </q-td>
                ''')
                
                # Slot para prazo fatal
                table.add_slot('body-cell-prazo_fatal', '''
                    <q-td :props="props" style="vertical-align: middle;">
                        <span style="font-size: 12px; color: #374151;">{{ props.value || '-' }}</span>
                    </q-td>
                ''')
                
                # Slot para status com cores
                table.add_slot('body-cell-status', '''
                    <q-td :props="props" style="vertical-align: middle;">
                        <q-badge 
                            :color="props.value === 'Cumprida' ? 'positive' : 
                                    props.value === 'Pendente' ? 'warning' : 
                                    props.value === 'Atrasada' ? 'negative' : 'grey'"
                            :label="props.value || '-'"
                            class="px-3 py-1"
                            style="font-weight: 500; font-size: 12px;"
                        />
                    </q-td>
                ''')
        
        # Rodapé com informações e botão de fechar
        with ui.row().classes('w-full p-4 justify-between items-center').style('border-top: 2px solid #e5e7eb; background: #f9fafb;'):
            if clausulas:
                ui.label(f'Total de {len(clausulas)} cláusula(s) cadastrada(s)').classes('text-sm text-gray-600 font-medium')
            else:
                ui.label('').classes('text-sm')
            
            ui.button('Fechar', icon='close', on_click=dialog.close).props('flat color=primary').classes('font-medium')
    
    def open_dialog():
        """Abre o dialog."""
        dialog.open()
    
    return dialog, open_dialog

