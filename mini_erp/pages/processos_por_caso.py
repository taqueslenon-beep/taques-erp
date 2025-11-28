"""
Visualização de Controle de Acesso aos Processos
Página dedicada para gerenciar permissões de acesso aos processos, organizados por caso.
"""
from nicegui import ui, run
from ..core import (
    layout, PRIMARY_COLOR, get_cases_list, get_processes_list, 
    save_process as save_process_core, get_db
)
from ..auth import is_authenticated
import asyncio
import traceback


# Cores dos status (mesmas usadas no módulo de processos)
STATUS_COLORS = {
    'Em andamento': '#eab308',
    'Concluído': '#166534',
    'Concluído com pendências': '#4d7c0f',
    'Em monitoramento': '#ea580c'
}

STATUS_TEXT_COLORS = {
    'Em andamento': '#1f2937',
    'Concluído': '#ffffff',
    'Concluído com pendências': '#ffffff',
    'Em monitoramento': '#ffffff'
}

# Cores das áreas do direito
PROCESS_AREA_COLORS = {
    'Administrativo': '#6b7280',
    'Criminal': '#dc2626',
    'Civil': '#2563eb',
    'Tributário': '#7c3aed',
    'Técnicos/projetos': '#22c55e'
}

# Sistemas processuais (mesmos do módulo de processos)
PROCESS_SYSTEMS = [
    'eproc - TJSC',
    'eproc - TRF-4',
    'Projudi - TJPR',
    'SGPE',
    'eProtocolo',
    'SEI - IBAMA'
]


@ui.page('/processos-por-caso')
def processos_por_caso():
    """Página de visualização de processos agrupados por caso."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Estado da página
    state = {
        'cases': [],
        'all_processes': [],
        'processes_without_case': [],
        'loading': True,
        'filter_system': None,
    }

    with layout('Processos por Caso', breadcrumbs=[('Processos', '/processos'), ('Por Caso', None)]):
        
        # Header
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label('Controle de Acesso aos Processos').classes('text-2xl font-bold text-gray-800')
            with ui.row().classes('gap-2'):
                ui.button('Voltar', icon='arrow_back', on_click=lambda: ui.navigate.to('/processos')).props('flat')
        
        ui.label('Gerencie as permissões de acesso aos processos. Os processos estão organizados por caso.').classes('text-gray-500 mb-4')
        
        # Filtro por sistema
        with ui.row().classes('w-full gap-3 mb-6 items-end'):
            system_filter = ui.select(
                options=PROCESS_SYSTEMS,
                label='Filtrar por sistema',
                with_input=True,
                multiple=True,
                clearable=True
            ).props('dense outlined use-chips').classes('w-96')
            
            def on_system_filter_change(e):
                state['filter_system'] = e.value if e.value else None
                render_cases_accordions.refresh()
            
            system_filter.on('update:model-value', on_system_filter_change)
            
            ui.button('Limpar filtro', icon='clear', on_click=lambda: (
                setattr(system_filter, 'value', None),
                state.update({'filter_system': None}),
                render_cases_accordions.refresh()
            )).props('flat')

        # Container principal
        main_container = ui.column().classes('w-full gap-4')
        loading_spinner = ui.spinner(size='xl', color='primary').classes('self-center my-8')

        @ui.refreshable
        def render_cases_accordions():
            main_container.clear()
            
            with main_container:
                if state['loading']:
                    ui.label('Carregando casos...').classes('text-gray-500')
                    return
                
                cases = state['cases']
                all_processes = state['all_processes']
                processes_without_case = state['processes_without_case']
                
                # Aplica filtro por sistema
                filter_system = state.get('filter_system')
                
                def matches_system_filter(process):
                    if not filter_system:
                        return True
                    process_system = process.get('system') or process.get('sistema_processual')
                    if isinstance(filter_system, list):
                        return process_system in filter_system
                    return process_system == filter_system
                
                # Filtra processos
                if filter_system:
                    filtered_cases = []
                    for case in cases:
                        filtered_procs = [p for p in case.get('processes', []) if matches_system_filter(p)]
                        if filtered_procs:
                            case_copy = case.copy()
                            case_copy['processes'] = filtered_procs
                            case_copy['process_count'] = len(filtered_procs)
                            filtered_cases.append(case_copy)
                    cases = filtered_cases
                    processes_without_case = [p for p in processes_without_case if matches_system_filter(p)]
                
                if not cases and not processes_without_case:
                    with ui.card().classes('w-full p-8 text-center'):
                        ui.icon('filter_alt_off', size='xl').classes('text-gray-400 mb-4')
                        ui.label('Nenhum processo encontrado com os filtros aplicados').classes('text-xl text-gray-600')
                    return
                
                # Estatísticas gerais
                total_cases = len(cases)
                cases_with_processes = sum(1 for c in cases if c.get('process_count', 0) > 0)
                total_processes = sum(c.get('process_count', 0) for c in cases) + len(processes_without_case)
                
                with ui.row().classes('w-full gap-4 mb-6 flex-wrap'):
                    with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                        ui.label('Total de Casos').classes('text-sm text-gray-500')
                        ui.label(str(total_cases)).classes('text-2xl font-bold text-gray-800')
                    with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                        ui.label('Casos com Processos').classes('text-sm text-gray-500')
                        ui.label(str(cases_with_processes)).classes('text-2xl font-bold text-gray-800')
                    with ui.card().classes('p-4 flex-1 min-w-[200px]'):
                        ui.label('Total de Processos').classes('text-sm text-gray-500')
                        ui.label(str(total_processes)).classes('text-2xl font-bold text-gray-800')
                
                # Ordenar casos: primeiro os com processos, depois alfabeticamente
                sorted_cases = sorted(cases, key=lambda c: (-c.get('process_count', 0), c.get('title', '').lower()))
                
                # Accordions por caso
                for case in sorted_cases:
                    case_title = case.get('title', 'Caso sem título')
                    case_slug = case.get('slug', '')
                    case_summary = case.get('summary') or case.get('description') or case.get('objectives') or ''
                    process_count = case.get('process_count', 0)
                    processes = case.get('processes', [])
                    
                    # Ícone baseado na quantidade de processos
                    icon = 'folder' if process_count == 0 else 'folder_open'
                    
                    # Header do accordion com contador
                    header_text = f"{case_title} ({process_count} {'processo' if process_count == 1 else 'processos'})"
                    
                    # Expande automaticamente se tiver processos
                    with ui.expansion(
                        header_text,
                        icon=icon,
                        value=(process_count > 0)
                    ).classes('w-full border rounded mb-2').props('dense'):
                        
                        with ui.column().classes('w-full gap-3 p-2'):
                            # Resumo do caso (se existir)
                            if case_summary:
                                summary_text = case_summary[:300] + '...' if len(case_summary) > 300 else case_summary
                                # Remove tags HTML se houver
                                import re
                                summary_text = re.sub(r'<[^>]+>', '', summary_text)
                                ui.label(summary_text).classes('text-sm text-gray-600 italic mb-2')
                            
                            # Link para o caso
                            with ui.row().classes('w-full justify-between items-center mb-3'):
                                ui.button(
                                    'Ver detalhes do caso',
                                    icon='open_in_new',
                                    on_click=lambda slug=case_slug: ui.navigate.to(f'/casos/{slug}')
                                ).props('flat dense').classes('text-primary')
                            
                            if process_count == 0:
                                ui.label('Nenhum processo vinculado a este caso.').classes('text-gray-500 text-sm py-4')
                            else:
                                # Função para salvar permissões
                                async def save_permission(process_id, field, value):
                                    try:
                                        def _update_process():
                                            db = get_db()
                                            doc_ref = db.collection('processes').document(process_id)
                                            doc_ref.update({field: value})
                                        
                                        await run.io_bound(_update_process)
                                        ui.notify('Permissões atualizadas', type='positive')
                                    except Exception as e:
                                        print(f'Erro ao salvar permissão: {e}')
                                        traceback.print_exc()
                                        ui.notify('Erro ao salvar permissões', type='negative')
                                
                                # Tabela de processos
                                table_columns = [
                                    {'name': 'area', 'label': 'Área', 'field': 'area_direito', 'align': 'center', 'style': 'width: 90px'},
                                    {'name': 'title', 'label': 'Título do Processo', 'field': 'title', 'align': 'left'},
                                    {'name': 'number', 'label': 'Número do processo', 'field': 'numero_processo', 'align': 'left', 'style': 'width: 150px'},
                                    {'name': 'advogado', 'label': 'Advogado tem acesso?', 'field': 'advogado_tem_acesso', 'align': 'center', 'style': 'width: 140px'},
                                    {'name': 'tecnicos', 'label': 'Técnicos têm acesso?', 'field': 'tecnicos_tem_acesso', 'align': 'center', 'style': 'width: 140px'},
                                    {'name': 'clientes', 'label': 'Clientes têm acesso?', 'field': 'clientes_tem_acesso', 'align': 'center', 'style': 'width: 140px'},
                                ]
                                
                                # Prepara dados da tabela
                                table_rows = []
                                for proc in processes:
                                    area = proc.get('area_direito') or proc.get('area', '')
                                    table_rows.append({
                                        '_id': proc.get('_id', ''),
                                        'title': proc.get('title') or proc.get('titulo', ''),
                                        'area_direito': area,
                                        'area_color': PROCESS_AREA_COLORS.get(area, '#6b7280'),
                                        'numero_processo': proc.get('numero_processo') or proc.get('number', ''),
                                        'link': proc.get('link_processo') or proc.get('link', ''),
                                        'advogado_tem_acesso': proc.get('advogado_tem_acesso', False),
                                        'tecnicos_tem_acesso': proc.get('tecnicos_tem_acesso', False),
                                        'clientes_tem_acesso': proc.get('clientes_tem_acesso', False),
                                    })
                                
                                processes_table = ui.table(
                                    columns=table_columns,
                                    rows=table_rows,
                                    row_key='_id'
                                ).classes('w-full').props('flat bordered dense')
                                
                                # Slot para área com chip colorido
                                processes_table.add_slot('body-cell-area', '''
                                    <q-td :props="props">
                                        <q-chip 
                                            :style="`background-color: ${props.row.area_color}; color: white;`"
                                            size="sm"
                                            dense
                                        >
                                            {{ props.value || 'N/A' }}
                                        </q-chip>
                                    </q-td>
                                ''')
                                
                                # Slot para número com link
                                processes_table.add_slot('body-cell-number', '''
                                    <q-td :props="props">
                                        <a v-if="props.row.link" 
                                            :href="props.row.link" 
                                            target="_blank" 
                                            class="text-primary hover:underline"
                                            style="text-decoration: none;"
                                        >
                                            {{ props.value || 'N/A' }}
                                        </a>
                                        <span v-else class="text-gray-600">
                                            {{ props.value || 'N/A' }}
                                        </span>
                                    </q-td>
                                ''')
                                
                                # Slot para checkbox advogado
                                processes_table.add_slot('body-cell-advogado', '''
                                    <q-td :props="props">
                                        <q-checkbox 
                                            :model-value="props.row.advogado_tem_acesso"
                                            @update:model-value="$parent.$emit('toggle-advogado', {id: props.row._id, value: $event})"
                                            dense
                                        />
                                    </q-td>
                                ''')
                                
                                # Slot para checkbox técnicos
                                processes_table.add_slot('body-cell-tecnicos', '''
                                    <q-td :props="props">
                                        <q-checkbox 
                                            :model-value="props.row.tecnicos_tem_acesso"
                                            @update:model-value="$parent.$emit('toggle-tecnicos', {id: props.row._id, value: $event})"
                                            dense
                                        />
                                    </q-td>
                                ''')
                                
                                # Slot para checkbox clientes
                                processes_table.add_slot('body-cell-clientes', '''
                                    <q-td :props="props">
                                        <q-checkbox 
                                            :model-value="props.row.clientes_tem_acesso"
                                            @update:model-value="$parent.$emit('toggle-clientes', {id: props.row._id, value: $event})"
                                            dense
                                        />
                                    </q-td>
                                ''')
                                
                                # Handlers para os checkboxes
                                async def handle_toggle_advogado(e):
                                    await save_permission(e.args['id'], 'advogado_tem_acesso', e.args['value'])
                                
                                async def handle_toggle_tecnicos(e):
                                    await save_permission(e.args['id'], 'tecnicos_tem_acesso', e.args['value'])
                                
                                async def handle_toggle_clientes(e):
                                    await save_permission(e.args['id'], 'clientes_tem_acesso', e.args['value'])
                                
                                processes_table.on('toggle-advogado', handle_toggle_advogado)
                                processes_table.on('toggle-tecnicos', handle_toggle_tecnicos)
                                processes_table.on('toggle-clientes', handle_toggle_clientes)
                                
                                # CSS para estilo da tabela
                                ui.add_head_html('''
                                <style>
                                .case-processes-table .q-table th {
                                    background-color: #f3f4f6 !important;
                                    font-weight: 600 !important;
                                    font-size: 11px;
                                    text-transform: uppercase;
                                }
                                .case-processes-table .q-table td {
                                    padding: 8px 12px !important;
                                    font-size: 14px;
                                }
                                </style>
                                ''')
                
                # Seção especial: Processos sem caso vinculado
                if processes_without_case:
                    with ui.expansion(
                        f"Processos sem caso vinculado ({len(processes_without_case)} {'processo' if len(processes_without_case) == 1 else 'processos'})",
                        icon='folder_off',
                        value=False
                    ).classes('w-full border rounded mb-2 bg-gray-50').props('dense'):
                        
                        with ui.column().classes('w-full gap-3 p-2'):
                            ui.label('Estes processos não estão vinculados a nenhum caso.').classes('text-sm text-gray-600 italic mb-2')
                            
                            # Função para salvar permissões
                            async def save_permission_no_case(process_id, field, value):
                                try:
                                    def _update_process():
                                        db = get_db()
                                        doc_ref = db.collection('processes').document(process_id)
                                        doc_ref.update({field: value})
                                    
                                    await run.io_bound(_update_process)
                                    ui.notify('Permissões atualizadas', type='positive')
                                except Exception as e:
                                    print(f'Erro ao salvar permissão: {e}')
                                    traceback.print_exc()
                                    ui.notify('Erro ao salvar permissões', type='negative')
                            
                            # Tabela de processos
                            table_columns = [
                                {'name': 'area', 'label': 'Área', 'field': 'area_direito', 'align': 'center', 'style': 'width: 90px'},
                                {'name': 'title', 'label': 'Título do Processo', 'field': 'title', 'align': 'left'},
                                {'name': 'number', 'label': 'Número do processo', 'field': 'numero_processo', 'align': 'left', 'style': 'width: 150px'},
                                {'name': 'advogado', 'label': 'Advogado tem acesso?', 'field': 'advogado_tem_acesso', 'align': 'center', 'style': 'width: 140px'},
                                {'name': 'tecnicos', 'label': 'Técnicos têm acesso?', 'field': 'tecnicos_tem_acesso', 'align': 'center', 'style': 'width: 140px'},
                                {'name': 'clientes', 'label': 'Clientes têm acesso?', 'field': 'clientes_tem_acesso', 'align': 'center', 'style': 'width: 140px'},
                            ]
                            
                            # Prepara dados da tabela
                            table_rows = []
                            for proc in processes_without_case:
                                area = proc.get('area_direito') or proc.get('area', '')
                                table_rows.append({
                                    '_id': proc.get('_id', ''),
                                    'title': proc.get('title') or proc.get('titulo', ''),
                                    'area_direito': area,
                                    'area_color': PROCESS_AREA_COLORS.get(area, '#6b7280'),
                                    'numero_processo': proc.get('numero_processo') or proc.get('number', ''),
                                    'link': proc.get('link_processo') or proc.get('link', ''),
                                    'advogado_tem_acesso': proc.get('advogado_tem_acesso', False),
                                    'tecnicos_tem_acesso': proc.get('tecnicos_tem_acesso', False),
                                    'clientes_tem_acesso': proc.get('clientes_tem_acesso', False),
                                })
                            
                            no_case_table = ui.table(
                                columns=table_columns,
                                rows=table_rows,
                                row_key='_id'
                            ).classes('w-full').props('flat bordered dense')
                            
                            # Slots para a tabela de processos sem caso
                            no_case_table.add_slot('body-cell-area', '''
                                <q-td :props="props">
                                    <q-chip 
                                        :style="`background-color: ${props.row.area_color}; color: white;`"
                                        size="sm"
                                        dense
                                    >
                                        {{ props.value || 'N/A' }}
                                    </q-chip>
                                </q-td>
                            ''')
                            
                            no_case_table.add_slot('body-cell-number', '''
                                <q-td :props="props">
                                    <a v-if="props.row.link" 
                                        :href="props.row.link" 
                                        target="_blank" 
                                        class="text-primary hover:underline"
                                        style="text-decoration: none;"
                                    >
                                        {{ props.value || 'N/A' }}
                                    </a>
                                    <span v-else class="text-gray-600">
                                        {{ props.value || 'N/A' }}
                                    </span>
                                </q-td>
                            ''')
                            
                            no_case_table.add_slot('body-cell-advogado', '''
                                <q-td :props="props">
                                    <q-checkbox 
                                        :model-value="props.row.advogado_tem_acesso"
                                        @update:model-value="$parent.$emit('toggle-advogado', {id: props.row._id, value: $event})"
                                        dense
                                    />
                                </q-td>
                            ''')
                            
                            no_case_table.add_slot('body-cell-tecnicos', '''
                                <q-td :props="props">
                                    <q-checkbox 
                                        :model-value="props.row.tecnicos_tem_acesso"
                                        @update:model-value="$parent.$emit('toggle-tecnicos', {id: props.row._id, value: $event})"
                                        dense
                                    />
                                </q-td>
                            ''')
                            
                            no_case_table.add_slot('body-cell-clientes', '''
                                <q-td :props="props">
                                    <q-checkbox 
                                        :model-value="props.row.clientes_tem_acesso"
                                        @update:model-value="$parent.$emit('toggle-clientes', {id: props.row._id, value: $event})"
                                        dense
                                    />
                                </q-td>
                            ''')
                            
                            # Handlers para os checkboxes
                            async def handle_toggle_advogado_no_case(e):
                                await save_permission_no_case(e.args['id'], 'advogado_tem_acesso', e.args['value'])
                            
                            async def handle_toggle_tecnicos_no_case(e):
                                await save_permission_no_case(e.args['id'], 'tecnicos_tem_acesso', e.args['value'])
                            
                            async def handle_toggle_clientes_no_case(e):
                                await save_permission_no_case(e.args['id'], 'clientes_tem_acesso', e.args['value'])
                            
                            no_case_table.on('toggle-advogado', handle_toggle_advogado_no_case)
                            no_case_table.on('toggle-tecnicos', handle_toggle_tecnicos_no_case)
                            no_case_table.on('toggle-clientes', handle_toggle_clientes_no_case)
        
        async def load_data():
            """Carrega TODOS os processos e agrupa por caso."""
            state['loading'] = True
            loading_spinner.visible = True
            render_cases_accordions.refresh()
            
            try:
                # Busca todos os casos e TODOS os processos
                cases = await run.io_bound(get_cases_list)
                all_processes = await run.io_bound(get_processes_list)
                
                # Cria dicionário para agrupar processos por caso
                processes_by_case = {}
                processes_without_case = []
                
                # Agrupa processos por caso
                for process in all_processes:
                    case_ids = process.get('case_ids', [])
                    
                    if case_ids:
                        # Processo tem casos vinculados
                        for case_id in case_ids:
                            if case_id not in processes_by_case:
                                processes_by_case[case_id] = []
                            processes_by_case[case_id].append(process)
                    else:
                        # Processo sem caso vinculado
                        processes_without_case.append(process)
                
                # Associa processos aos casos
                for case in cases:
                    case_slug = case.get('slug', '')
                    if case_slug in processes_by_case:
                        case['processes'] = processes_by_case[case_slug]
                        case['process_count'] = len(processes_by_case[case_slug])
                    else:
                        case['processes'] = []
                        case['process_count'] = 0
                
                state['cases'] = cases
                state['all_processes'] = all_processes
                state['processes_without_case'] = processes_without_case
                
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                traceback.print_exc()
                ui.notify('Erro ao carregar dados. Tente novamente.', type='negative')
                state['cases'] = []
                state['all_processes'] = []
                state['processes_without_case'] = []
            
            state['loading'] = False
            loading_spinner.visible = False
            render_cases_accordions.refresh()
        
        # Carrega dados ao iniciar
        ui.timer(0.1, load_data, once=True)

