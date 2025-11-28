# Módulo de Condenações Criminais
# Gestão de condenações e penas criminais

from nicegui import ui
from ....core import (
    save_data, get_clients_list, get_processes_list, get_convictions_list,
    format_date_br,
)


def render_condenacoes_criminais():
    """Renderiza a aba de condenações criminais"""
    
    # Dialog para nova condenação criminal
    with ui.dialog() as new_criminal_conviction_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Nova Condenação Criminal').classes('text-lg font-bold mb-4')
        
        crim_condenado = ui.select(
            options=[c.get('name', '') for c in get_clients_list() if c.get('name')],
            label='Condenado',
            with_input=True
        ).classes('w-full mb-3').props('dense')
        
        crim_crime = ui.input(
            label='Crime',
            placeholder='Ex: Crime ambiental, Corrupção'
        ).classes('w-full mb-3').props('dense')
        
        crim_pena = ui.textarea(
            label='Pena Aplicada',
            placeholder='Descreva a pena aplicada...'
        ).classes('w-full mb-3').props('dense rows=2')
        
        crim_status = ui.select(
            options=['Em cumprimento', 'Cumprida', 'Pendente recurso', 'Suspensa', 'Extinta'],
            label='Status',
            value='Em cumprimento'
        ).classes('w-full mb-3').props('dense')
        
        crim_data_sentenca = ui.input(
            label='Data da Sentença'
        ).classes('w-full mb-3').props('dense')
        
        crim_processo = ui.select(
            options=[p.get('number', '') for p in get_processes_list() if p.get('number')],
            label='Processo Vinculado',
            with_input=True
        ).classes('w-full mb-3').props('dense')
        
        crim_obs = ui.textarea(
            label='Observações',
            placeholder='Informações adicionais...'
        ).classes('w-full').props('dense rows=2')
        
        def save_criminal_conviction():
            if not crim_condenado.value:
                ui.notify('Selecione o condenado!', type='warning')
                return
            if not crim_crime.value:
                ui.notify('Informe o crime!', type='warning')
                return
            
            import uuid
            from datetime import datetime
            
            get_convictions_list().append({
                'id': str(uuid.uuid4())[:8],
                'condenado': crim_condenado.value,
                'tipo': 'Criminal',
                'crime': crim_crime.value,
                'pena': crim_pena.value or '',
                'status': crim_status.value or 'Em cumprimento',
                'data_sentenca': crim_data_sentenca.value or '',
                'processo': crim_processo.value or '',
                'observacoes': crim_obs.value or '',
                'created_at': datetime.now().isoformat()
            })
            save_data()
            render_criminal_convictions_table.refresh()
            new_criminal_conviction_dialog.close()
            
            # Limpa os campos
            crim_condenado.value = None
            crim_crime.value = ''
            crim_pena.value = ''
            crim_status.value = 'Em cumprimento'
            crim_data_sentenca.value = ''
            crim_processo.value = None
            crim_obs.value = ''
            
            ui.notify('Condenação criminal cadastrada com sucesso!')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=new_criminal_conviction_dialog.close).props('flat dense')
            ui.button('Salvar', on_click=save_criminal_conviction).props('dense color=primary')
    
    # Botão para adicionar nova condenação criminal
    with ui.row().classes('w-full justify-end mb-3'):
        ui.button('Nova Condenação Criminal', icon='add', on_click=new_criminal_conviction_dialog.open).props('flat dense color=primary')
    
    # Tabela de condenações criminais
    with ui.card().classes('w-full'):
        ui.label('Condenações Criminais').classes('font-bold text-lg mb-3')
        
        @ui.refreshable
        def render_criminal_convictions_table():
            # Filtra apenas condenações criminais
            criminal_convictions = [c for c in get_convictions_list() if c.get('tipo') == 'Criminal']
            
            if not criminal_convictions:
                ui.label('Nenhuma condenação criminal cadastrada.').classes('text-gray-400 italic py-4')
                return
            
            columns = [
                {'name': 'condenado', 'label': 'Condenado', 'field': 'condenado', 'align': 'left'},
                {'name': 'crime', 'label': 'Crime', 'field': 'crime', 'align': 'left'},
                {'name': 'pena', 'label': 'Pena', 'field': 'pena', 'align': 'left'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                {'name': 'data', 'label': 'Data Sentença', 'field': 'data', 'align': 'center'},
                {'name': 'processo', 'label': 'Processo', 'field': 'processo', 'align': 'left'},
                {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
            ]
            
            rows = []
            for conviction in criminal_convictions:
                pena = conviction.get('pena', '')
                pena_truncated = (pena[:50] + '...') if len(pena) > 50 else pena
                
                rows.append({
                    'id': conviction.get('id'),
                    'condenado': conviction.get('condenado', ''),
                    'crime': conviction.get('crime', ''),
                    'pena': pena_truncated,
                    'status': conviction.get('status', ''),
                    'data': format_date_br(conviction.get('data_sentenca')),
                    'processo': conviction.get('processo', '-'),
                })
            
            table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full').props('flat dense')
            
            table.add_slot('body-cell-status', '''
                <q-td :props="props">
                    <q-badge 
                        :color="props.value === 'Cumprida' || props.value === 'Extinta' ? 'green' : 
                                props.value === 'Em cumprimento' ? 'orange' :
                                props.value === 'Suspensa' ? 'blue' : 
                                props.value === 'Pendente recurso' ? 'purple' : 'grey'">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')
            
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat dense icon="delete" color="red" @click="$parent.$emit('delete', props.row)" size="sm"/>
                </q-td>
            ''')
            
            def remove_criminal_conviction(conviction_id):
                idx = next((i for i, c in enumerate(get_convictions_list()) if c.get('id') == conviction_id), None)
                if idx is not None:
                    get_convictions_list().pop(idx)
                    save_data()
                    render_criminal_convictions_table.refresh()
                    ui.notify('Condenação removida!')
            
            table.on('delete', lambda e: remove_criminal_conviction(e.args['id']))
        
        render_criminal_convictions_table()

