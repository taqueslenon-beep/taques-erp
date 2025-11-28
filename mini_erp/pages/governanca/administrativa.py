# Módulo Administrativa
# Gestão de processos administrativos e acordos

from nicegui import ui
from ...core import save_data, get_clients_list, get_agreements_list

# Status possíveis para acordos administrativos
AGREEMENT_STATUS = [
    'Mapeando oportunidade',
    'Negociação em curso',
    'Enviado ao órgão',
    'Assinado',
    'Cumprindo obrigações',
    'Encerrado'
]


def render_administrativa():
    """Renderiza a aba administrativa"""
    
    with ui.card().classes('w-full p-4 mb-4'):
        ui.label('Processos Administrativos').classes('font-bold text-xl mb-2')
        ui.label('Gestão de processos e penalidades administrativas').classes('text-gray-500 text-sm mb-4')
        
        # Estatísticas
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Processos Ativos').classes('text-sm text-gray-500')
                ui.label('5').classes('text-2xl font-bold text-gray-800')
            
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Multas Aplicadas').classes('text-sm text-gray-500')
                ui.label('R$ 250.000').classes('text-2xl font-bold text-red-600')
            
            with ui.card().classes('flex-1 min-w-48 p-4 text-center'):
                ui.label('Acordos Firmados').classes('text-sm text-gray-500')
                ui.label('2').classes('text-2xl font-bold text-green-600')
    
    # Tabela de acordos administrativos
    with ui.card().classes('w-full'):
        ui.label('Acordos Administrativos').classes('font-bold text-lg mb-3')
        
        def get_client_names():
            return [c.get('name', '') for c in get_clients_list() if c.get('name')]
        
        # Dialog para novo acordo
        with ui.dialog() as new_agreement_dialog, ui.card().classes('w-full max-w-lg p-6'):
            ui.label('Novo Acordo Administrativo').classes('text-lg font-bold mb-4')
            
            acordo_cliente = ui.select(
                options=get_client_names(),
                label='Cliente / Controlado',
                with_input=True
            ).classes('w-full mb-3').props('dense')
            
            acordo_orgao = ui.input(
                label='Órgão ou entidade'
            ).classes('w-full mb-3').props('dense')
            
            acordo_instrumento = ui.input(
                label='Instrumento (ex: TAC, TCA, Termo de Compromisso)'
            ).classes('w-full mb-3').props('dense')
            
            acordo_status = ui.select(
                options=AGREEMENT_STATUS,
                label='Status',
                value='Mapeando oportunidade'
            ).classes('w-full mb-3').props('dense')
            
            with ui.row().classes('w-full gap-3 flex-wrap'):
                acordo_valor = ui.input(
                    label='Valor estimado',
                    placeholder='Ex: 150000'
                ).classes('flex-1 min-w-48').props('dense prefix="R$" type=number step=0.01')
                
                acordo_prazo = ui.input(
                    label='Prazo limite (AAAA-MM-DD)'
                ).classes('flex-1 min-w-48').props('dense')
            
            acordo_obs = ui.textarea(
                label='Obrigações principais / observações'
            ).classes('w-full mt-3').props('dense rows=2')
            
            def save_agreement():
                if not acordo_cliente.value:
                    ui.notify('Escolha quem responde pelo acordo.', type='warning')
                    return
                if not acordo_orgao.value:
                    ui.notify('Informe o órgão ou entidade.', type='warning')
                    return
                if not acordo_instrumento.value:
                    ui.notify('Descreva o instrumento firmado.', type='warning')
                    return
                
                import uuid
                
                get_agreements_list().append({
                    'id': str(uuid.uuid4())[:8],
                    'cliente': acordo_cliente.value,
                    'orgao': acordo_orgao.value,
                    'instrumento': acordo_instrumento.value,
                    'status': acordo_status.value or 'Mapeando oportunidade',
                    'valor': acordo_valor.value or '',
                    'prazo': acordo_prazo.value or '',
                    'observacoes': acordo_obs.value or ''
                })
                save_data()
                render_agreements_table.refresh()
                
                # Limpa campos
                acordo_cliente.value = None
                acordo_orgao.value = ''
                acordo_instrumento.value = ''
                acordo_status.value = 'Mapeando oportunidade'
                acordo_valor.value = ''
                acordo_prazo.value = ''
                acordo_obs.value = ''
                
                new_agreement_dialog.close()
                ui.notify('Acordo registrado!', type='positive')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=new_agreement_dialog.close).props('flat dense')
                ui.button('Salvar', on_click=save_agreement).props('dense color=primary')
        
        # Botão para novo acordo
        with ui.row().classes('w-full justify-end mb-3'):
            ui.button('Novo Acordo Administrativo', icon='add', on_click=new_agreement_dialog.open).props('flat dense color=primary')
        
        @ui.refreshable
        def render_agreements_table():
            if not get_agreements_list():
                ui.label('Nenhum acordo cadastrado.').classes('text-gray-400 italic py-4')
                return
            
            columns = [
                {'name': 'cliente', 'label': 'Cliente', 'field': 'cliente', 'align': 'left'},
                {'name': 'orgao', 'label': 'Órgão', 'field': 'orgao', 'align': 'left'},
                {'name': 'instrumento', 'label': 'Instrumento', 'field': 'instrumento', 'align': 'left'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                {'name': 'valor', 'label': 'Valor', 'field': 'valor', 'align': 'right'},
                {'name': 'prazo', 'label': 'Prazo', 'field': 'prazo', 'align': 'center'},
                {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
            ]
            
            rows = []
            for agreement in get_agreements_list():
                valor_bruto = agreement.get('valor', '')
                valor_fmt = f'R$ {valor_bruto}' if valor_bruto not in (None, '') else '-'
                rows.append({
                    'id': agreement.get('id'),
                    'cliente': agreement.get('cliente', '-'),
                    'orgao': agreement.get('orgao', '-'),
                    'instrumento': agreement.get('instrumento', '-'),
                    'status': agreement.get('status', ''),
                    'valor': valor_fmt,
                    'prazo': agreement.get('prazo', '-'),
                })
            
            table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full').props('flat dense')
            
            table.add_slot('body-cell-status', '''
                <q-td :props="props">
                    <q-badge 
                        :color="props.value === 'Assinado' ? 'green' :
                                props.value === 'Cumprindo obrigações' ? 'teal' :
                                props.value === 'Enviado ao órgão' ? 'blue' :
                                props.value === 'Negociação em curso' ? 'orange' : 'grey'">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')
            
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat dense icon="delete" color="red" @click="$parent.$emit('delete', props.row)" size="sm"/>
                </q-td>
            ''')
            
            def remove_agreement(agreement_id):
                idx = next((i for i, item in enumerate(get_agreements_list()) if item.get('id') == agreement_id), None)
                if idx is not None:
                    get_agreements_list().pop(idx)
                    save_data()
                    render_agreements_table.refresh()
                    ui.notify('Acordo removido.', type='info')
            
            table.on('delete', lambda e: remove_agreement(e.args['id']))
        
        render_agreements_table()


