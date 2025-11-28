from nicegui import ui
from ..core import layout, get_cases_list, get_processes_list, get_clients_list, get_opposing_parties_list, PRIMARY_COLOR
from ..auth import is_authenticated
from collections import Counter
import json

def get_short_name(full_name: str, source_list: list) -> str:
    """Retorna sigla/apelido ou primeiro nome"""
    for item in source_list:
        if item.get('name') == full_name:
            # Prioridade: nickname > alias > primeiro nome
            if item.get('nickname'):
                return item['nickname']
            if item.get('alias'):
                return item['alias']
            # Se não tem apelido, retorna primeiro nome
            return full_name.split()[0] if full_name else full_name
    # Se não encontrou na lista, retorna primeiro nome
    return full_name.split()[0] if full_name else full_name

@ui.page('/')
def painel():
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # ==========================================================================
    # OTIMIZAÇÃO: Carrega todos os dados UMA ÚNICA VEZ no início
    # Evita múltiplas chamadas ao Firestore durante a renderização
    # ==========================================================================
    _cases = get_cases_list()
    _processes = get_processes_list()
    _clients = get_clients_list()
    _opposing = get_opposing_parties_list()
    
    # Pré-calcula totais e contagens (usando dados locais)
    total_casos = len(_cases)
    total_processos = len(_processes)
    total_cenarios = sum(len(proc.get('scenarios', [])) for proc in _processes)
    
    # Mapa de casos por título para lookups rápidos
    _cases_by_title = {c.get('title'): c for c in _cases if c.get('title')}
    
    with layout('Painel', breadcrumbs=[('Painel', None)]):
        ui.label('Visão consolidada dos dados do sistema. Informações atualizadas em tempo real.').classes('text-gray-500 text-sm mb-4 -mt-4')
        
        # Estilo para abas minimalistas
        ui.add_head_html('''
            <style>
                .q-tab__icon { font-size: 16px !important; }
                .q-tab { min-height: 36px !important; padding: 4px 8px !important; }
            </style>
        ''')
        
        # Contar casos por estado (usando dados locais)
        casos_parana = len([c for c in _cases if c.get('state') == 'Paraná'])
        casos_sc = len([c for c in _cases if c.get('state') == 'Santa Catarina'])
        
        # Contar processos por estado (usando mapa de casos local)
        processos_parana = 0
        processos_sc = 0
        for proc in _processes:
            proc_cases = proc.get('cases', [])
            for case_title in proc_cases:
                case = _cases_by_title.get(case_title)
                if case:
                    if case.get('state') == 'Paraná':
                        processos_parana += 1
                        break
                    elif case.get('state') == 'Santa Catarina':
                        processos_sc += 1
                        break

        # Estado para controlar a aba ativa
        active_tab = {'value': 'totais'}
        
        # Layout vertical: menu lateral esquerdo + conteúdo à direita
        with ui.row().classes('w-full gap-4 items-start'):
            # Menu vertical à esquerda
            with ui.column().classes('w-64 min-w-64 bg-white rounded shadow-sm p-2 sticky top-4'):
                ui.label('Visualizações').classes('text-sm font-semibold text-gray-700 mb-2 px-2')
                
                def set_active_tab(tab_name: str):
                    active_tab['value'] = tab_name
                    menu_buttons.refresh()
                    content_area.refresh()
                
                @ui.refreshable
                def menu_buttons():
                    tabs_config = [
                        ('totais', 'Totais', 'dashboard'),
                        ('comparativo', 'Comparativo', 'bar_chart'),
                        ('categoria', 'Categoria', 'category'),
                        ('temporal', 'Temporal', 'timeline'),
                        ('status', 'Status', 'insights'),
                        ('resultado', 'Resultado', 'assessment'),
                        ('cliente', 'Cliente', 'person'),
                        ('parte', 'Parte Contrária', 'gavel'),
                        ('area', 'Área', 'domain'),
                        ('area_ha', 'Área (HA)', 'landscape'),
                        ('estado', 'Estado', 'map'),
                        ('heatmap', 'Mapa de Calor', 'whatshot'),
                        ('probabilidade', 'Probabilidades', 'trending_up'),
                        ('financeiro', 'Financeiro', 'attach_money'),
                    ]
                    
                    for tab_id, tab_label, tab_icon in tabs_config:
                        is_active = active_tab['value'] == tab_id
                        def make_click_handler(tid):
                            return lambda: set_active_tab(tid)
                        btn = ui.button(tab_label, icon=tab_icon, on_click=make_click_handler(tab_id))
                        props_str = ('unelevated' if is_active else 'flat') + ' ' + ('color=primary' if is_active else 'color=grey-7') + ' align=left'
                        btn.props(props_str)
                        btn.classes('w-full justify-start text-left px-3 py-2 mb-1')
                        if is_active:
                            btn.style('background-color: #e3f2fd; font-weight: 600;')
                
                menu_buttons()
            
            # Área de conteúdo à direita
            with ui.column().classes('flex-1 min-w-0'):
                @ui.refreshable
                def content_area():
                    current_tab = active_tab['value']
                    
                    if current_tab == 'totais':
                        # Aba Totais
                        # Cards de totais gerais
                        with ui.row().classes('gap-4 flex-wrap'):
                            with ui.card().classes('w-64 p-4'):
                                ui.label('Total de Casos').classes('text-gray-500 text-sm')
                                ui.label(str(total_casos)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR};')
                            with ui.card().classes('w-64 p-4'):
                                ui.label('Total de Processos').classes('text-gray-500 text-sm')
                                ui.label(str(total_processos)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR};')
                            with ui.card().classes('w-64 p-4'):
                                ui.label('Cenários Mapeados').classes('text-gray-500 text-sm')
                                ui.label(str(total_cenarios)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR};')
                    
                    elif current_tab == 'comparativo':
                        # Aba Comparativo - Casos Antigos vs Novos vs Futuros

                        def get_case_type(case: dict) -> str:
                            ct = case.get('case_type')
                            if ct in ['Antigo', 'Novo', 'Futuro']:
                                return ct
                            # Compatibilidade com dados antigos
                            if case.get('is_new_case', False):
                                return 'Novo'
                            return 'Antigo'
                        
                        # Classificar casos baseado no campo case_type (usa _cases local)
                        future_cases = [c for c in _cases if get_case_type(c) == 'Futuro']
                        new_cases = [c for c in _cases if get_case_type(c) == 'Novo']
                        old_cases = [c for c in _cases if get_case_type(c) == 'Antigo']
                        
                        # Totais
                        total_old = len(old_cases)
                        total_new = len(new_cases)
                        total_future = len(future_cases)
                        
                        # Cards com totais
                        with ui.row().classes('gap-4 flex-wrap mb-4'):
                            with ui.card().classes('w-64 p-4'):
                                ui.label('Casos Antigos').classes('text-gray-500 text-sm')
                                ui.label(str(total_old)).classes('text-3xl font-bold').style('color: #0891b2;')  # cyan-600
                            with ui.card().classes('w-64 p-4'):
                                ui.label('Casos Novos').classes('text-gray-500 text-sm')
                                ui.label(str(total_new)).classes('text-3xl font-bold').style('color: #16a34a;')  # green-600
                            with ui.card().classes('w-64 p-4'):
                                ui.label('Casos Futuros').classes('text-gray-500 text-sm')
                                ui.label(str(total_future)).classes('text-3xl font-bold').style('color: #9333ea;')  # purple-600
                        
                        # Gráficos lado a lado
                        with ui.row().classes('w-full gap-4 flex-wrap'):
                            # Gráfico de Barras Comparativo
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Comparativo de Casos').classes('text-lg font-semibold text-gray-700 mb-4')
                                
                                if total_old > 0 or total_new > 0 or total_future > 0:
                                    categories = ['Casos Antigos', 'Casos Novos', 'Casos Futuros']
                                    values = [total_old, total_new, total_future]
                                    colors = ['#0891b2', '#16a34a', '#9333ea']  # cyan, green, purple
                                    
                                    chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
                                    
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'axis',
                                            'axisPointer': {'type': 'shadow'}
                                        },
                                        'grid': {
                                            'left': '3%',
                                            'right': '4%',
                                            'bottom': '3%',
                                            'containLabel': True
                                        },
                                        'xAxis': {
                                            'type': 'category',
                                            'data': categories,
                                            'axisLabel': {
                                                'interval': 0,
                                                'fontSize': 12,
                                                'fontWeight': 'bold'
                                            }
                                        },
                                        'yAxis': {
                                            'type': 'value',
                                            'minInterval': 1
                                        },
                                        'series': [{
                                            'name': 'Quantidade',
                                            'type': 'bar',
                                            'data': chart_data,
                                            'barWidth': '50%',
                                            'label': {
                                                'show': True,
                                                'position': 'top',
                                                'fontWeight': 'bold',
                                                'fontSize': 16
                                            }
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    ui.label('Nenhum caso cadastrado ainda.').classes('text-gray-400 italic text-center py-8')
                        
                            # Gráfico de Pizza
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Distribuição Percentual').classes('text-lg font-semibold text-gray-700 mb-4')
                                
                                if total_old > 0 or total_new > 0 or total_future > 0:
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'item',
                                            'formatter': '{b}: {c} ({d}%)'
                                        },
                                        'legend': {
                                            'orient': 'vertical',
                                            'left': 'left',
                                            'top': 'center',
                                            'fontSize': 13
                                        },
                                        'series': [{
                                            'name': 'Casos',
                                            'type': 'pie',
                                            'radius': ['40%', '70%'],
                                            'center': ['65%', '50%'],
                                    'avoidLabelOverlap': False,
                                    'itemStyle': {
                                        'borderRadius': 10,
                                        'borderColor': '#fff',
                                        'borderWidth': 2
                                    },
                                    'label': {
                                        'show': True,
                                        'position': 'outside',
                                        'fontSize': 13,
                                        'fontWeight': 'bold',
                                        'formatter': '{b}\n{c} ({d}%)'
                                    },
                                    'labelLine': {'show': True},
                                    'data': [
                                        {'value': total_old, 'name': 'Casos Antigos', 'itemStyle': {'color': '#0891b2'}},
                                        {'value': total_new, 'name': 'Casos Novos', 'itemStyle': {'color': '#16a34a'}},
                                        {'value': total_future, 'name': 'Casos Futuros', 'itemStyle': {'color': '#9333ea'}}
                                    ]
                                }]
                            }).classes('w-full h-80')
                                else:
                                    ui.label('Nenhum caso cadastrado ainda.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'categoria':
                                # Aba Categoria - Contencioso vs Consultivo
                        # Contar casos por categoria
                        total_contencioso = len([c for c in _cases if c.get('category', 'Contencioso') == 'Contencioso'])
                        total_consultivo = len([c for c in _cases if c.get('category') == 'Consultivo'])
                
                        # Cards com totais
                        with ui.row().classes('gap-4 flex-wrap mb-4'):
                            with ui.card().classes('w-64 p-4 border-l-4').style('border-left-color: #dc2626;'):
                                ui.label('Contencioso').classes('text-gray-500 text-sm')
                                ui.label(str(total_contencioso)).classes('text-3xl font-bold').style('color: #dc2626;')
                            with ui.card().classes('w-64 p-4 border-l-4').style('border-left-color: #16a34a;'):
                                ui.label('Consultivo').classes('text-gray-500 text-sm')
                                ui.label(str(total_consultivo)).classes('text-3xl font-bold').style('color: #16a34a;')
                
                        # Gráficos lado a lado
                        with ui.row().classes('w-full gap-4 flex-wrap'):
                            # Gráfico de Barras
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Casos por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                if total_contencioso > 0 or total_consultivo > 0:
                                    categories = ['Contencioso', 'Consultivo']
                                    values = [total_contencioso, total_consultivo]
                                    colors = ['#dc2626', '#16a34a']  # vermelho, verde
                            
                                    chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
                            
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'axis',
                                            'axisPointer': {'type': 'shadow'}
                                        },
                                        'grid': {
                                            'left': '3%',
                                            'right': '4%',
                                            'bottom': '3%',
                                            'containLabel': True
                                        },
                                        'xAxis': {
                                            'type': 'category',
                                            'data': categories,
                                            'axisLabel': {
                                                'interval': 0,
                                                'fontSize': 14,
                                                'fontWeight': 'bold'
                                            }
                                        },
                                        'yAxis': {
                                            'type': 'value',
                                            'minInterval': 1
                                        },
                                        'series': [{
                                            'name': 'Quantidade',
                                            'type': 'bar',
                                            'data': chart_data,
                                            'barWidth': '50%',
                                            'label': {
                                                'show': True,
                                                'position': 'top',
                                                'fontWeight': 'bold',
                                                'fontSize': 18
                                            }
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    ui.label('Nenhum caso cadastrado ainda.').classes('text-gray-400 italic text-center py-8')
                    
                            # Gráfico de Pizza
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Distribuição Percentual').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                if total_contencioso > 0 or total_consultivo > 0:
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'item',
                                            'formatter': '{b}: {c} ({d}%)'
                                        },
                                        'legend': {
                                            'orient': 'vertical',
                                            'left': 'left',
                                            'top': 'center',
                                            'fontSize': 14
                                        },
                                        'series': [{
                                            'name': 'Casos',
                                            'type': 'pie',
                                            'radius': ['40%', '70%'],
                                            'center': ['65%', '50%'],
                                            'avoidLabelOverlap': False,
                                            'itemStyle': {
                                                'borderRadius': 10,
                                                'borderColor': '#fff',
                                                'borderWidth': 2
                                            },
                                            'label': {
                                                'show': True,
                                                'position': 'outside',
                                                'fontSize': 14,
                                                'fontWeight': 'bold',
                                                'formatter': '{b}\n{c} ({d}%)'
                                            },
                                            'labelLine': {'show': True},
                                            'data': [
                                                {'value': total_contencioso, 'name': 'Contencioso', 'itemStyle': {'color': '#dc2626'}},
                                                {'value': total_consultivo, 'name': 'Consultivo', 'itemStyle': {'color': '#16a34a'}}
                                            ]
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    ui.label('Nenhum caso cadastrado ainda.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'temporal':
                        # Aba Temporal - Evolução de Casos e Processos por Ano (DESIGN PROFISSIONAL)
                        
                        # Estado dos filtros
                        temporal_filters = {
                            'show_cases': True,
                            'show_processes': True,
                            'year_start': '2008',
                            'year_end': '2025'
                        }
                        
                        @ui.refreshable
                        def temporal_chart():
                            """Renderiza o gráfico temporal de casos e processos"""
                            from collections import Counter
                            
                            # Coletar dados de casos por ano
                            cases_by_year = Counter()
                            if temporal_filters['show_cases']:
                                for case in _cases:
                                    year = case.get('year')
                                    if year:
                                        year_str = str(year)
                                        cases_by_year[year_str] += 1
                            
                            # Coletar dados de processos por ano
                            processes_by_year = Counter()
                            if temporal_filters['show_processes']:
                                for process in _processes:
                                    year = process.get('year')
                                    if year:
                                        year_str = str(year)
                                        processes_by_year[year_str] += 1
                            
                            # Obter todos os anos únicos e ordenar
                            all_years = sorted(set(list(cases_by_year.keys()) + list(processes_by_year.keys())))
                            
                            # Filtrar por período
                            try:
                                year_start = int(temporal_filters['year_start'])
                                year_end = int(temporal_filters['year_end'])
                                all_years = [y for y in all_years if year_start <= int(y) <= year_end]
                            except:
                                pass
                            
                            if not all_years:
                                with ui.card().classes('w-full p-8 flex justify-center items-center bg-gray-50'):
                                    ui.label('Nenhum dado encontrado para o período selecionado.').classes('text-gray-400 italic')
                                return
                            
                            # Preparar dados para o gráfico de linhas
                            cases_data = [cases_by_year.get(year, 0) for year in all_years]
                            processes_data = [processes_by_year.get(year, 0) for year in all_years]
                            
                            # CORES PROFISSIONAIS (neutras)
                            COLOR_CASES = '#455A64'        # Cinza azulado
                            COLOR_PROCESSES = '#2d4a3f'    # Verde escuro (cor do sistema)
                            
                            # Preparar séries
                            series_data = []
                            if temporal_filters['show_cases']:
                                series_data.append({
                                    'name': 'Casos',
                                    'type': 'line',
                                    'data': cases_data,
                                    'smooth': True,
                                    'lineStyle': {'color': COLOR_CASES, 'width': 3},
                                    'itemStyle': {'color': COLOR_CASES},
                                    'areaStyle': {
                                        'color': {
                                            'type': 'linear',
                                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                            'colorStops': [
                                                {'offset': 0, 'color': COLOR_CASES + '40'},
                                                {'offset': 1, 'color': COLOR_CASES + '10'}
                                            ]
                                        }
                                    },
                                    'emphasis': {'focus': 'series'}
                                })
                            
                            if temporal_filters['show_processes']:
                                series_data.append({
                                    'name': 'Processos',
                                    'type': 'line',
                                    'data': processes_data,
                                    'smooth': True,
                                    'lineStyle': {'color': COLOR_PROCESSES, 'width': 3},
                                    'itemStyle': {'color': COLOR_PROCESSES},
                                    'areaStyle': {
                                        'color': {
                                            'type': 'linear',
                                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                            'colorStops': [
                                                {'offset': 0, 'color': COLOR_PROCESSES + '40'},
                                                {'offset': 1, 'color': COLOR_PROCESSES + '10'}
                                            ]
                                        }
                                    },
                                    'emphasis': {'focus': 'series'}
                                })
                            
                            with ui.card().classes('w-full p-6'):
                                ui.label('Evolução Temporal de Casos e Processos').classes('text-xl font-semibold text-gray-800 mb-4')
                                
                                ui.echart({
                                    'tooltip': {
                                        'trigger': 'axis',
                                        'backgroundColor': 'rgba(255, 255, 255, 0.95)',
                                        'borderColor': '#ddd',
                                        'borderWidth': 1,
                                        'textStyle': {'color': '#333'},
                                        'axisPointer': {
                                            'type': 'cross',
                                            'lineStyle': {'color': '#999', 'type': 'dashed'}
                                        }
                                    },
                                    'legend': {
                                        'data': [s['name'] for s in series_data],
                                        'top': '3%',
                                        'left': 'center',
                                        'textStyle': {'fontSize': 14, 'color': '#333'}
                                    },
                                    'grid': {
                                        'left': '3%',
                                        'right': '4%',
                                        'bottom': '10%',
                                        'top': '15%',
                                        'containLabel': True,
                                        'backgroundColor': '#f8f9fa'
                                    },
                                    'xAxis': {
                                        'type': 'category',
                                        'data': all_years,
                                        'boundaryGap': False,
                                        'axisLine': {'lineStyle': {'color': '#e0e0e0'}},
                                        'axisLabel': {
                                            'fontSize': 12,
                                            'color': '#333',
                                            'fontWeight': '500'
                                        },
                                        'name': 'Ano',
                                        'nameLocation': 'middle',
                                        'nameGap': 35,
                                        'nameTextStyle': {
                                            'fontSize': 13,
                                            'fontWeight': 'bold',
                                            'color': '#555'
                                        }
                                    },
                                    'yAxis': {
                                        'type': 'value',
                                        'minInterval': 1,
                                        'axisLine': {'lineStyle': {'color': '#e0e0e0'}},
                                        'splitLine': {'lineStyle': {'color': '#e0e0e0', 'type': 'dashed'}},
                                        'axisLabel': {
                                            'fontSize': 12,
                                            'color': '#333'
                                        },
                                        'name': 'Quantidade',
                                        'nameLocation': 'middle',
                                        'nameGap': 50,
                                        'nameTextStyle': {
                                            'fontSize': 13,
                                            'fontWeight': 'bold',
                                            'color': '#555'
                                        }
                                    },
                                    'series': series_data
                                }).classes('w-full h-96')
                                
                                # Estatísticas resumidas
                                with ui.row().classes('w-full justify-center mt-6 gap-6 flex-wrap'):
                                    if temporal_filters['show_cases'] and cases_data:
                                        total_cases = sum(cases_data)
                                        max_cases = max(cases_data)
                                        max_cases_year = all_years[cases_data.index(max_cases)]
                                        
                                        with ui.row().classes('items-center gap-2'):
                                            ui.icon('folder', size='sm').style(f'color: {COLOR_CASES};')
                                            ui.label(f'Casos: {total_cases} total | Pico: {max_cases_year} ({max_cases})').classes('text-sm font-medium text-gray-700')
                                    
                                    if temporal_filters['show_processes'] and processes_data:
                                        total_processes = sum(processes_data)
                                        max_processes = max(processes_data)
                                        max_processes_year = all_years[processes_data.index(max_processes)]
                                        
                                        with ui.row().classes('items-center gap-2'):
                                            ui.icon('gavel', size='sm').style(f'color: {COLOR_PROCESSES};')
                                            ui.label(f'Processos: {total_processes} total | Pico: {max_processes_year} ({max_processes})').classes('text-sm font-medium text-gray-700')
                        
                        # Filtros
                        with ui.row().classes('w-full gap-6 mb-4'):
                            # Coluna de filtros à esquerda
                            with ui.card().classes('w-64 p-4 bg-gray-50'):
                                ui.label('Filtros').classes('text-base font-semibold text-gray-800 mb-4')
                                
                                ui.label('Tipo de Dados').classes('text-sm font-medium text-gray-700 mb-2')
                                
                                def toggle_cases():
                                    temporal_filters['show_cases'] = not temporal_filters['show_cases']
                                    filter_checkboxes.refresh()
                                    temporal_chart.refresh()
                                
                                def toggle_processes():
                                    temporal_filters['show_processes'] = not temporal_filters['show_processes']
                                    filter_checkboxes.refresh()
                                    temporal_chart.refresh()
                                
                                @ui.refreshable
                                def filter_checkboxes():
                                    with ui.column().classes('gap-2 mb-4'):
                                        cb_cases = ui.checkbox('📁 Casos', value=temporal_filters['show_cases'])
                                        cb_cases.on('update:model-value', lambda: toggle_cases())
                                        
                                        cb_processes = ui.checkbox('⚖️ Processos', value=temporal_filters['show_processes'])
                                        cb_processes.on('update:model-value', lambda: toggle_processes())
                                
                                filter_checkboxes()
                                
                                ui.separator().classes('my-3')
                                
                                ui.label('Período').classes('text-sm font-medium text-gray-700 mb-2')
                                
                                year_start_input = ui.input('Ano Inicial', value=temporal_filters['year_start']).classes('w-full mb-2').props('dense outlined')
                                year_end_input = ui.input('Ano Final', value=temporal_filters['year_end']).classes('w-full mb-3').props('dense outlined')
                                
                                def update_period():
                                    temporal_filters['year_start'] = year_start_input.value
                                    temporal_filters['year_end'] = year_end_input.value
                                    temporal_chart.refresh()
                                    ui.notify('Período atualizado!', type='positive')
                                
                                ui.button('🔄 Atualizar', on_click=update_period).props('color=primary').classes('w-full')
                            
                            # Gráfico à direita
                            with ui.column().classes('flex-1'):
                                temporal_chart()
                    
                    elif current_tab == 'status':
                                # Aba Status
                        # Gráficos lado a lado
                        with ui.row().classes('w-full gap-4 flex-wrap'):
                            # Gráfico de Casos por Status
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Casos por Status').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                # Contar casos por status
                                cases_status_counter = Counter(case.get('status', 'Sem status') for case in _cases)
                        
                                # Ordenar do maior para o menor
                                sorted_cases_status = sorted(cases_status_counter.items(), key=lambda x: x[1], reverse=True)
                        
                                if sorted_cases_status:
                                    cases_categories = [item[0] for item in sorted_cases_status]
                                    cases_values = [item[1] for item in sorted_cases_status]
                            
                                    # Cores para cada status (atualizadas)
                                    # Em andamento: amarelo queimado | Concluído: verde escuro
                                    # Concluído com pendências: verde militar | Em monitoramento: laranja
                                    status_colors = {
                                        'Em andamento': '#b45309',              # amarelo queimado
                                        'Concluído': '#166534',                 # verde escuro
                                        'Concluído com pendências': '#4d7c0f',  # verde militar
                                        'Em monitoramento': '#ea580c',          # laranja
                                        'Sem status': '#6b7280'                 # gray
                                    }
                            
                                    cases_colors = [status_colors.get(cat, '#6b7280') for cat in cases_categories]
                            
                                    # Dados para o gráfico de barras
                                    cases_chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(cases_values, cases_colors)]
                            
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'axis',
                                            'axisPointer': {'type': 'shadow'}
                                        },
                                        'grid': {
                                            'left': '3%',
                                            'right': '4%',
                                            'bottom': '3%',
                                            'containLabel': True
                                        },
                                        'xAxis': {
                                            'type': 'category',
                                            'data': cases_categories,
                                            'axisLabel': {
                                                'interval': 0,
                                                'rotate': 15,
                                                'fontSize': 11
                                            }
                                        },
                                        'yAxis': {
                                            'type': 'value',
                                            'minInterval': 1
                                        },
                                        'series': [{
                                            'name': 'Casos',
                                            'type': 'bar',
                                            'data': cases_chart_data,
                                            'barWidth': '60%',
                                            'label': {
                                                'show': True,
                                                'position': 'top',
                                                'fontWeight': 'bold',
                                                'fontSize': 14
                                            }
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    ui.label('Nenhum caso cadastrado ainda.').classes('text-gray-400 italic text-center py-8')
                    
                            # Gráfico de Processos por Status
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Processos por Status').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                # Contar processos por status
                                status_counter = Counter(proc.get('status', 'Sem status') for proc in _processes)
                        
                                # Ordenar do maior para o menor
                                sorted_status = sorted(status_counter.items(), key=lambda x: x[1], reverse=True)
                        
                                if sorted_status:
                                    categories = [item[0] for item in sorted_status]
                                    values = [item[1] for item in sorted_status]
                            
                                    # Cores para cada status (atualizadas)
                                    # Em andamento: amarelo queimado | Concluído: verde escuro
                                    # Concluído com pendências: verde militar | Em monitoramento: laranja
                                    status_colors = {
                                        'Em andamento': '#b45309',              # amarelo queimado
                                        'Concluído': '#166534',                 # verde escuro
                                        'Concluído com pendências': '#4d7c0f',  # verde militar
                                        'Em monitoramento': '#ea580c',          # laranja
                                        'Sem status': '#6b7280'                 # gray
                                    }
                            
                                    colors = [status_colors.get(cat, '#6b7280') for cat in categories]
                            
                                    # Dados para o gráfico de barras
                                    chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
                            
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'axis',
                                            'axisPointer': {'type': 'shadow'}
                                        },
                                        'grid': {
                                            'left': '3%',
                                            'right': '4%',
                                            'bottom': '3%',
                                            'containLabel': True
                                        },
                                        'xAxis': {
                                            'type': 'category',
                                            'data': categories,
                                            'axisLabel': {
                                                'interval': 0,
                                                'rotate': 15,
                                                'fontSize': 11
                                            }
                                        },
                                        'yAxis': {
                                            'type': 'value',
                                            'minInterval': 1
                                        },
                                        'series': [{
                                            'name': 'Processos',
                                            'type': 'bar',
                                            'data': chart_data,
                                            'barWidth': '60%',
                                            'label': {
                                                'show': True,
                                                'position': 'top',
                                                'fontWeight': 'bold',
                                                'fontSize': 14
                                            }
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    ui.label('Nenhum processo cadastrado ainda.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'resultado':
                                # Aba Resultado
                        with ui.card().classes('w-full p-4'):
                            with ui.column().classes('items-center justify-center gap-4'):
                                ui.icon('construction', size='64px').classes('text-gray-400')
                                ui.label('Em Desenvolvimento').classes('text-2xl font-bold text-gray-600')
                                ui.label('Esta visualização está sendo desenvolvida e estará disponível em breve.').classes('text-gray-500 text-center max-w-md')
                    
                    elif current_tab == 'cliente':
                                # Aba Cliente
                        # Gráfico de Casos por Cliente
                        with ui.card().classes('w-full p-4 mb-4'):
                            ui.label('Casos por Cliente').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                            # Contar casos por cliente
                            cases_client_counter = Counter()
                            for caso in _cases:
                                for client in caso.get('clients', []):
                                    cases_client_counter[client] += 1
                    
                            # Ordenar do maior para o menor
                            sorted_cases_clients = sorted(cases_client_counter.items(), key=lambda x: x[1], reverse=True)
                    
                            if sorted_cases_clients:
                                # Usar nomes curtos (sigla/apelido ou primeiro nome)
                                cases_client_names = [get_short_name(item[0], _clients) for item in sorted_cases_clients]
                                cases_client_values = [item[1] for item in sorted_cases_clients]
                        
                                # Altura dinâmica baseada na quantidade de clientes
                                cases_chart_height = max(200, len(cases_client_names) * 40)
                        
                                ui.echart({
                                    'tooltip': {
                                        'trigger': 'axis',
                                        'axisPointer': {'type': 'shadow'}
                                    },
                                    'grid': {
                                        'left': '3%',
                                        'right': '10%',
                                        'bottom': '3%',
                                        'top': '3%',
                                        'containLabel': True
                                    },
                                    'xAxis': {
                                        'type': 'value',
                                        'minInterval': 1
                                    },
                                    'yAxis': {
                                        'type': 'category',
                                        'data': list(reversed(cases_client_names)),
                                        'axisLabel': {
                                            'fontSize': 11
                                        }
                                    },
                                    'series': [{
                                        'name': 'Casos',
                                        'type': 'bar',
                                        'data': list(reversed(cases_client_values)),
                                        'barWidth': '60%',
                                        'itemStyle': {'color': '#0891b2'},  # cyan-600
                                        'label': {
                                            'show': True,
                                            'position': 'right',
                                            'fontWeight': 'bold',
                                            'fontSize': 13
                                        }
                                    }]
                                }).classes('w-full').style(f'height: {cases_chart_height}px;')
                            else:
                                ui.label('Nenhum cliente vinculado a casos.').classes('text-gray-400 italic text-center py-8')
                
                        # Gráfico de Processos por Cliente
                        with ui.card().classes('w-full p-4'):
                            ui.label('Processos por Cliente').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                            # Contar processos por cliente
                            client_counter = Counter()
                            for proc in _processes:
                                for client in proc.get('clients', []):
                                    client_counter[client] += 1
                    
                            # Ordenar do maior para o menor
                            sorted_clients = sorted(client_counter.items(), key=lambda x: x[1], reverse=True)
                    
                            if sorted_clients:
                                # Usar nomes curtos (sigla/apelido ou primeiro nome)
                                client_names = [get_short_name(item[0], _clients) for item in sorted_clients]
                                client_values = [item[1] for item in sorted_clients]
                        
                                # Altura dinâmica baseada na quantidade de clientes
                                chart_height = max(200, len(client_names) * 40)
                        
                                ui.echart({
                                    'tooltip': {
                                        'trigger': 'axis',
                                        'axisPointer': {'type': 'shadow'}
                                    },
                                    'grid': {
                                        'left': '3%',
                                        'right': '10%',
                                        'bottom': '3%',
                                        'top': '3%',
                                        'containLabel': True
                                    },
                                    'xAxis': {
                                        'type': 'value',
                                        'minInterval': 1
                                    },
                                    'yAxis': {
                                        'type': 'category',
                                        'data': list(reversed(client_names)),
                                        'axisLabel': {
                                            'fontSize': 11
                                        }
                                    },
                                    'series': [{
                                        'name': 'Processos',
                                        'type': 'bar',
                                        'data': list(reversed(client_values)),
                                        'barWidth': '60%',
                                        'itemStyle': {'color': PRIMARY_COLOR},
                                        'label': {
                                            'show': True,
                                            'position': 'right',
                                            'fontWeight': 'bold',
                                            'fontSize': 13
                                        }
                                    }]
                                }).classes('w-full').style(f'height: {chart_height}px;')
                            else:
                                ui.label('Nenhum cliente vinculado a processos.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'parte':
                                # Aba Parte Contrária
                        with ui.card().classes('w-full p-4'):
                            ui.label('Processos por Parte Contrária').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                            # Contar processos por parte contrária
                            opposing_counter = Counter()
                            for proc in _processes:
                                for opposing in proc.get('opposing_parties', []):
                                    opposing_counter[opposing] += 1
                    
                            # Ordenar do maior para o menor
                            sorted_opposing = sorted(opposing_counter.items(), key=lambda x: x[1], reverse=True)
                    
                            if sorted_opposing:
                                # Usar nomes curtos (sigla/apelido ou primeiro nome)
                                opposing_names = [get_short_name(item[0], _opposing) for item in sorted_opposing]
                                opposing_values = [item[1] for item in sorted_opposing]
                        
                                # Altura dinâmica baseada na quantidade de partes
                                chart_height = max(200, len(opposing_names) * 40)
                        
                                ui.echart({
                                    'tooltip': {
                                        'trigger': 'axis',
                                        'axisPointer': {'type': 'shadow'}
                                    },
                                    'grid': {
                                        'left': '3%',
                                        'right': '10%',
                                        'bottom': '3%',
                                        'top': '3%',
                                        'containLabel': True
                                    },
                                    'xAxis': {
                                        'type': 'value',
                                        'minInterval': 1
                                    },
                                    'yAxis': {
                                        'type': 'category',
                                        'data': list(reversed(opposing_names)),
                                        'axisLabel': {
                                            'fontSize': 11
                                        }
                                    },
                                    'series': [{
                                        'name': 'Processos',
                                        'type': 'bar',
                                        'data': list(reversed(opposing_values)),
                                        'barWidth': '60%',
                                        'itemStyle': {'color': '#dc2626'},
                                        'label': {
                                            'show': True,
                                            'position': 'right',
                                            'fontWeight': 'bold',
                                            'fontSize': 13
                                        }
                                    }]
                                }).classes('w-full').style(f'height: {chart_height}px;')
                            else:
                                ui.label('Nenhuma parte contrária vinculada a processos.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'area':
                                # Aba Área
                        with ui.card().classes('w-full p-4'):
                            ui.label('Processos por Área').classes('text-lg font-semibold text-gray-700 mb-4')

                            area_counter = Counter()
                            for proc in _processes:
                                area = proc.get('area') or 'Não informado'
                                area_counter[area] += 1

                            sorted_areas = sorted(area_counter.items(), key=lambda x: x[1], reverse=True)

                            if sorted_areas:
                                area_names = [item[0] for item in sorted_areas]
                                area_values = [item[1] for item in sorted_areas]

                                chart_height = max(200, len(area_names) * 40)

                                # Cores correspondentes ao módulo de Processos
                                area_colors = {
                                    'Administrativo': '#6b7280',      # cinza
                                    'Criminal': '#dc2626',             # vermelho
                                    'Cível': '#2563eb',                # azul
                                    'Tributário': '#7c3aed',           # roxo
                                    'Técnico/projetos': '#22c55e',     # verde
                                    'Outros': '#d1d5db',               # cinza claro
                                    'Não informado': '#9ca3af'         # cinza médio
                                }
                        
                                area_chart_data = [
                                    {
                                        'value': value, 
                                        'itemStyle': {
                                            'color': area_colors.get(area_name, '#9ca3af')
                                        }
                                    }
                                    for area_name, value in zip(reversed(area_names), reversed(area_values))
                                ]

                                ui.echart({
                                    'tooltip': {
                                        'trigger': 'axis',
                                        'axisPointer': {'type': 'shadow'}
                                    },
                                    'grid': {
                                        'left': '3%',
                                        'right': '10%',
                                        'bottom': '3%',
                                        'top': '3%',
                                        'containLabel': True
                                    },
                                    'xAxis': {
                                        'type': 'value',
                                        'minInterval': 1
                                    },
                                    'yAxis': {
                                        'type': 'category',
                                        'data': list(reversed(area_names)),
                                        'axisLabel': {
                                            'fontSize': 12
                                        }
                                    },
                                    'series': [{
                                        'name': 'Processos',
                                        'type': 'bar',
                                        'data': area_chart_data,
                                        'barWidth': '60%',
                                        'label': {
                                            'show': True,
                                            'position': 'right',
                                            'fontWeight': 'bold',
                                            'fontSize': 13
                                        }
                                    }]
                                }).classes('w-full').style(f'height: {chart_height}px;')
                            else:
                                ui.label('Nenhum processo com área cadastrada.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'area_ha':
                                # Aba Área (HA)
                        with ui.card().classes('w-full p-4'):
                            with ui.column().classes('items-center justify-center gap-4'):
                                ui.icon('construction', size='64px').classes('text-gray-400')
                                ui.label('Módulo em Construção').classes('text-2xl font-bold text-gray-600')
                                ui.label('Visualizações por área (hectares) e afetação estarão disponíveis em breve.').classes('text-gray-500 text-center max-w-md')
                    
                    elif current_tab == 'financeiro':
                                # Aba Financeiro
                        # Coletar todos os dados financeiros dos casos
                        def coletar_dados_financeiros():
                            """Coleta todos os valores financeiros dos cálculos dos casos"""
                            total_exposicao = 0.0  # Multas em aberto
                            total_pago = 0.0  # Multas pagas/recuperadas
                            total_futuro = 0.0  # Multas futuras/estimadas
                            total_em_analise = 0.0  # Em análise
                            total_confirmado = 0.0  # Confirmado
                    
                            detalhes_aberto = []  # Detalhes das multas em aberto
                            detalhes_pago = []  # Detalhes das multas pagas
                            detalhes_futuro = []  # Detalhes das multas futuras
                    
                            for case in _cases:
                                calculations = case.get('calculations', [])
                                case_title = case.get('title', 'Sem título')
                        
                                for calc in calculations:
                                    if calc.get('type') == 'Financeiro':
                                        finance_rows = calc.get('finance_rows', [])
                                
                                        for row in finance_rows:
                                            value = float(row.get('value', 0.0) or 0.0)
                                            status = row.get('status', 'Em análise')
                                            description = row.get('description', 'Sem descrição')
                                    
                                            if status == 'Recuperado':
                                                total_pago += value
                                                detalhes_pago.append({
                                                    'case': case_title,
                                                    'description': description,
                                                    'value': value
                                                })
                                            elif status == 'Estimado':
                                                total_futuro += value
                                                detalhes_futuro.append({
                                                    'case': case_title,
                                                    'description': description,
                                                    'value': value
                                                })
                                            elif status == 'Em análise':
                                                total_em_analise += value
                                                total_exposicao += value
                                                detalhes_aberto.append({
                                                    'case': case_title,
                                                    'description': description,
                                                    'value': value,
                                                    'status': status
                                                })
                                            elif status == 'Confirmado':
                                                total_confirmado += value
                                                total_exposicao += value
                                                detalhes_aberto.append({
                                                    'case': case_title,
                                                    'description': description,
                                                    'value': value,
                                                    'status': status
                                                })
                    
                            return {
                                'exposicao': total_exposicao,
                                'pago': total_pago,
                                'futuro': total_futuro,
                                'em_analise': total_em_analise,
                                'confirmado': total_confirmado,
                                'detalhes_aberto': detalhes_aberto,
                                'detalhes_pago': detalhes_pago,
                                'detalhes_futuro': detalhes_futuro
                            }
                
                        dados_financeiros = coletar_dados_financeiros()
                
                        # Banner de desenvolvimento
                        with ui.card().classes('w-full p-4 mb-4 bg-yellow-50 border-l-4').style('border-left-color: #f59e0b;'):
                            with ui.row().classes('items-center gap-3'):
                                ui.icon('construction', size='md').classes('text-yellow-600')
                                with ui.column().classes('flex-grow'):
                                    ui.label('Painel Financeiro em Desenvolvimento').classes('text-sm font-semibold text-yellow-800')
                                    ui.label('Esta visualização está sendo aprimorada. Os gráficos abaixo mostram os dados financeiros já cadastrados.').classes('text-xs text-yellow-700')
                
                        # Cards de totais
                        with ui.row().classes('gap-4 flex-wrap mb-6'):
                            with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #dc2626;'):
                                ui.label('Exposição Financeira Total').classes('text-gray-500 text-sm mb-1')
                                ui.label(f'R$ {dados_financeiros["exposicao"]:,.2f}').classes('text-2xl font-bold').style('color: #dc2626;')
                                ui.label('Multas em aberto (Confirmadas + Em análise)').classes('text-xs text-gray-400 mt-1')
                    
                            with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #16a34a;'):
                                ui.label('Multas Pagas/Recuperadas').classes('text-gray-500 text-sm mb-1')
                                ui.label(f'R$ {dados_financeiros["pago"]:,.2f}').classes('text-2xl font-bold').style('color: #16a34a;')
                                ui.label('Total já recuperado').classes('text-xs text-gray-400 mt-1')
                    
                            with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #9333ea;'):
                                ui.label('Multas Futuras/Estimadas').classes('text-gray-500 text-sm mb-1')
                                ui.label(f'R$ {dados_financeiros["futuro"]:,.2f}').classes('text-2xl font-bold').style('color: #9333ea;')
                                ui.label('Valores estimados futuros').classes('text-xs text-gray-400 mt-1')
                
                        # Gráficos principais
                        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                            # Gráfico 1: Exposição Financeira Total (pizza)
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Distribuição Financeira Geral').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                total_geral = dados_financeiros["exposicao"] + dados_financeiros["pago"] + dados_financeiros["futuro"]
                        
                                if total_geral > 0:
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'item',
                                            'formatter': '{b}: R$ {c}<br/>({d}%)'
                                        },
                                        'legend': {
                                            'orient': 'vertical',
                                            'left': 'left',
                                            'top': 'center',
                                            'fontSize': 13
                                        },
                                        'series': [{
                                            'name': 'Valores',
                                            'type': 'pie',
                                            'radius': ['40%', '70%'],
                                            'center': ['65%', '50%'],
                                            'avoidLabelOverlap': False,
                                            'itemStyle': {
                                                'borderRadius': 10,
                                                'borderColor': '#fff',
                                                'borderWidth': 2
                                            },
                                            'label': {
                                                'show': True,
                                                'position': 'outside',
                                                'fontSize': 13,
                                                'fontWeight': 'bold'
                                            },
                                            'labelLine': {'show': True},
                                            'data': [
                                                {
                                                    'value': dados_financeiros["exposicao"],
                                                    'name': 'Em Aberto',
                                                    'itemStyle': {'color': '#dc2626'}
                                                },
                                                {
                                                    'value': dados_financeiros["pago"],
                                                    'name': 'Pagas/Recuperadas',
                                                    'itemStyle': {'color': '#16a34a'}
                                                },
                                                {
                                                    'value': dados_financeiros["futuro"],
                                                    'name': 'Futuras/Estimadas',
                                                    'itemStyle': {'color': '#9333ea'}
                                                }
                                            ]
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    with ui.column().classes('items-center justify-center py-8'):
                                        ui.icon('info', size='48px').classes('text-gray-400 mb-2')
                                        ui.label('Nenhum dado financeiro cadastrado').classes('text-gray-400 italic')
                                        ui.label('Cadastre cálculos financeiros nos casos para visualizar os gráficos.').classes('text-xs text-gray-400 mt-2')
                    
                            # Gráfico 2: Barras comparativas
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Comparativo de Valores').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                if total_geral > 0:
                                    categories = ['Em Aberto', 'Pagas/Recuperadas', 'Futuras/Estimadas']
                                    values = [
                                        dados_financeiros["exposicao"],
                                        dados_financeiros["pago"],
                                        dados_financeiros["futuro"]
                                    ]
                                    colors = ['#dc2626', '#16a34a', '#9333ea']
                            
                                    chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
                            
                                    ui.echart({
                                        'tooltip': {
                                            'trigger': 'axis',
                                            'axisPointer': {'type': 'shadow'},
                                            'formatter': '{b}<br/>{a}: R$ {c}'
                                        },
                                        'grid': {
                                            'left': '3%',
                                            'right': '4%',
                                            'bottom': '3%',
                                            'containLabel': True
                                        },
                                        'xAxis': {
                                            'type': 'category',
                                            'data': categories,
                                            'axisLabel': {
                                                'interval': 0,
                                                'fontSize': 12,
                                                'fontWeight': 'bold'
                                            }
                                        },
                                        'yAxis': {
                                            'type': 'value',
                                            'axisLabel': {
                                                'formatter': 'R$ {value}'
                                            }
                                        },
                                        'series': [{
                                            'name': 'Valor (R$)',
                                            'type': 'bar',
                                            'data': chart_data,
                                            'barWidth': '50%',
                                            'label': {
                                                'show': True,
                                                'position': 'top',
                                                'fontWeight': 'bold',
                                                'fontSize': 12,
                                                'formatter': 'R$ {c}'
                                            }
                                        }]
                                    }).classes('w-full h-80')
                                else:
                                    with ui.column().classes('items-center justify-center py-8'):
                                        ui.icon('info', size='48px').classes('text-gray-400 mb-2')
                                        ui.label('Nenhum dado financeiro cadastrado').classes('text-gray-400 italic')
                                        ui.label('Cadastre cálculos financeiros nos casos para visualizar os gráficos.').classes('text-xs text-gray-400 mt-2')
                
                        # Gráfico 3: Detalhamento da exposição (Confirmado vs Em análise)
                        if dados_financeiros["exposicao"] > 0:
                            with ui.card().classes('w-full p-4 mb-4'):
                                ui.label('Detalhamento da Exposição Financeira').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                with ui.row().classes('w-full gap-4 flex-wrap'):
                                    # Gráfico de pizza do detalhamento
                                    with ui.card().classes('flex-1 min-w-80 p-4'):
                                        ui.label('Status das Multas em Aberto').classes('text-md font-semibold text-gray-700 mb-4')
                                
                                        ui.echart({
                                            'tooltip': {
                                                'trigger': 'item',
                                                'formatter': '{b}: R$ {c}<br/>({d}%)'
                                            },
                                            'legend': {
                                                'orient': 'vertical',
                                                'left': 'left',
                                                'top': 'center',
                                                'fontSize': 13
                                            },
                                            'series': [{
                                                'name': 'Status',
                                                'type': 'pie',
                                                'radius': ['40%', '70%'],
                                                'center': ['65%', '50%'],
                                                'avoidLabelOverlap': False,
                                                'itemStyle': {
                                                    'borderRadius': 10,
                                                    'borderColor': '#fff',
                                                    'borderWidth': 2
                                                },
                                                'label': {
                                                    'show': True,
                                                    'position': 'outside',
                                                    'fontSize': 13,
                                                    'fontWeight': 'bold'
                                                },
                                                'labelLine': {'show': True},
                                                'data': [
                                                    {
                                                        'value': dados_financeiros["confirmado"],
                                                        'name': 'Confirmado',
                                                        'itemStyle': {'color': '#b45309'}
                                                    },
                                                    {
                                                        'value': dados_financeiros["em_analise"],
                                                        'name': 'Em Análise',
                                                        'itemStyle': {'color': '#0891b2'}
                                                    }
                                                ]
                                            }]
                                        }).classes('w-full h-64')
                            
                                    # Cards de detalhamento
                                    with ui.column().classes('flex-1 min-w-80 gap-4'):
                                        with ui.card().classes('p-4 border-l-4').style('border-left-color: #b45309;'):
                                            ui.label('Confirmado').classes('text-gray-500 text-sm mb-1')
                                            ui.label(f'R$ {dados_financeiros["confirmado"]:,.2f}').classes('text-xl font-bold').style('color: #b45309;')
                                            ui.label(f'{len([d for d in dados_financeiros["detalhes_aberto"] if d.get("status") == "Confirmado"])} item(ns)').classes('text-xs text-gray-400 mt-1')
                                
                                        with ui.card().classes('p-4 border-l-4').style('border-left-color: #0891b2;'):
                                            ui.label('Em Análise').classes('text-gray-500 text-sm mb-1')
                                            ui.label(f'R$ {dados_financeiros["em_analise"]:,.2f}').classes('text-xl font-bold').style('color: #0891b2;')
                                            ui.label(f'{len([d for d in dados_financeiros["detalhes_aberto"] if d.get("status") == "Em análise"])} item(ns)').classes('text-xs text-gray-400 mt-1')
                    
                    elif current_tab == 'estado':
                                # Aba Estado
                        # Gráficos de distribuição
                        with ui.row().classes('w-full gap-4 flex-wrap'):
                            # Gráfico de Casos por Estado
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Distribuição de Casos').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                if casos_parana > 0 or casos_sc > 0:
                                    ui.echart({
                                        'tooltip': {'trigger': 'item'},
                                        'series': [{
                                            'name': 'Casos',
                                            'type': 'pie',
                                            'radius': ['40%', '70%'],
                                            'center': ['50%', '50%'],
                                            'avoidLabelOverlap': False,
                                            'itemStyle': {
                                                'borderRadius': 10,
                                                'borderColor': '#fff',
                                                'borderWidth': 2
                                            },
                                            'label': {
                                                'show': True,
                                                'position': 'outside',
                                                'fontSize': 14,
                                                'fontWeight': 'bold',
                                                'formatter': '{b}: {c}'
                                            },
                                            'labelLine': {'show': True},
                                            'data': [
                                                {'value': casos_parana, 'name': 'Paraná', 'itemStyle': {'color': '#007934'}},
                                                {'value': casos_sc, 'name': 'Santa Catarina', 'itemStyle': {'color': '#d52b1e'}}
                                            ]
                                        }]
                                    }).classes('w-full h-64')
                                else:
                                    ui.label('Nenhum caso cadastrado com estado definido.').classes('text-gray-400 italic text-center py-8')
                    
                            # Gráfico de Processos por Estado  
                            with ui.card().classes('flex-1 min-w-80 p-4'):
                                ui.label('Distribuição de Processos').classes('text-lg font-semibold text-gray-700 mb-4')
                        
                                if processos_parana > 0 or processos_sc > 0:
                                    ui.echart({
                                        'tooltip': {'trigger': 'item'},
                                        'series': [{
                                            'name': 'Processos',
                                            'type': 'pie',
                                            'radius': ['40%', '70%'],
                                            'center': ['50%', '50%'],
                                            'avoidLabelOverlap': False,
                                            'itemStyle': {
                                                'borderRadius': 10,
                                                'borderColor': '#fff',
                                                'borderWidth': 2
                                            },
                                            'label': {
                                                'show': True,
                                                'position': 'outside',
                                                'fontSize': 14,
                                                'fontWeight': 'bold',
                                                'formatter': '{b}: {c}'
                                            },
                                            'labelLine': {'show': True},
                                            'data': [
                                                {'value': processos_parana, 'name': 'Paraná', 'itemStyle': {'color': '#007934'}},
                                                {'value': processos_sc, 'name': 'Santa Catarina', 'itemStyle': {'color': '#d52b1e'}}
                                            ]
                                        }]
                                    }).classes('w-full h-64')
                                else:
                                    ui.label('Nenhum processo vinculado a casos com estado definido.').classes('text-gray-400 italic text-center py-8')
                    
                    elif current_tab == 'heatmap':
                                # Aba Mapa de Calor
                        # Preparar dados: empresas (clientes) x áreas
                        # Contar problemas (casos + processos) por empresa e área
                        heatmap_data = {}  # {empresa: {área: quantidade}}
                        empresas_set = set()
                        areas_set = set()
                
                        # Coletar dados dos casos
                        for case in _cases:
                            clients = case.get('clients', [])
                            # Buscar processos relacionados para pegar a área
                            case_processes = case.get('processes', [])
                            for proc_title in case_processes:
                                for proc in _processes:
                                    if proc.get('title') == proc_title:
                                        area = proc.get('area') or 'Não informado'
                                        areas_set.add(area)
                                        for client in clients:
                                            empresas_set.add(client)
                                            if client not in heatmap_data:
                                                heatmap_data[client] = {}
                                            if area not in heatmap_data[client]:
                                                heatmap_data[client][area] = 0
                                            heatmap_data[client][area] += 1
                                        break
                
                        # Coletar dados dos processos diretamente
                        for proc in _processes:
                            area = proc.get('area') or 'Não informado'
                            areas_set.add(area)
                            clients = proc.get('clients', [])
                            for client in clients:
                                empresas_set.add(client)
                                if client not in heatmap_data:
                                    heatmap_data[client] = {}
                                if area not in heatmap_data[client]:
                                    heatmap_data[client][area] = 0
                                heatmap_data[client][area] += 1
                
                        # Ordenar empresas e áreas
                        empresas_ordenadas = sorted(empresas_set)
                        areas_ordenadas = sorted(areas_set)
                
                        if heatmap_data and empresas_ordenadas and areas_ordenadas:
                            # Preparar dados para o heatmap
                            heatmap_values = []
                            max_value = 0
                    
                            for empresa in empresas_ordenadas:
                                row = []
                                for area in areas_ordenadas:
                                    value = heatmap_data.get(empresa, {}).get(area, 0)
                                    row.append(value)
                                    max_value = max(max_value, value)
                                heatmap_values.append(row)
                    
                            # Criar dados no formato do ECharts (com nomes incluídos)
                            data_for_chart = []
                            empresas_nomes_curtos = [get_short_name(emp, _clients) for emp in empresas_ordenadas]
                    
                            for i, empresa in enumerate(empresas_ordenadas):
                                for j, area in enumerate(areas_ordenadas):
                                    value = heatmap_values[i][j]
                                    if value > 0:  # Só adicionar se houver valor
                                        # Formato: [x, y, value, area_nome, empresa_nome]
                                        data_for_chart.append([j, i, value, area, empresas_nomes_curtos[i]])
                    
                            with ui.card().classes('w-full p-4'):
                                ui.label('Mapa de Calor: Empresas x Áreas').classes('text-lg font-semibold text-gray-700 mb-4')
                                ui.label('Intensidade de problemas (casos + processos) por empresa do setor da família e área jurídica').classes('text-sm text-gray-500 mb-4')
                        
                                # Preparar tooltip com dados
                                areas_json = json.dumps(areas_ordenadas, ensure_ascii=False)
                                empresas_json = json.dumps(empresas_nomes_curtos, ensure_ascii=False)
                                tooltip_formatter = f'''function(params) {{
                                    var data = params.data;
                                    var areas = {areas_json};
                                    var empresas = {empresas_json};
                                    return areas[data[0]] + "<br/>" + empresas[data[1]] + ": <strong>" + data[2] + "</strong> problema(s)";
                                }}'''
                        
                                ui.echart({
                                    'tooltip': {
                                        'position': 'top',
                                        'formatter': tooltip_formatter
                                    },
                                    'grid': {
                                        'height': f'{max(400, len(empresas_ordenadas) * 40)}px',
                                        'top': '10%',
                                        'left': '15%',
                                        'right': '10%'
                                    },
                                    'xAxis': {
                                        'type': 'category',
                                        'data': areas_ordenadas,
                                        'splitArea': {'show': True},
                                        'axisLabel': {
                                            'rotate': 45,
                                            'fontSize': 11
                                        }
                                    },
                                    'yAxis': {
                                        'type': 'category',
                                        'data': empresas_nomes_curtos,
                                        'splitArea': {'show': True},
                                        'axisLabel': {
                                            'fontSize': 11
                                        }
                                    },
                                    'visualMap': {
                                        'min': 0,
                                        'max': max_value,
                                        'calculable': True,
                                        'orient': 'horizontal',
                                        'left': 'center',
                                        'bottom': '5%',
                                        'inRange': {
                                            'color': ['#e0f2fe', '#0ea5e9', '#0284c7', '#0369a1', '#075985', '#0c4a6e']
                                        },
                                        'text': ['Alto', 'Baixo'],
                                        'textStyle': {'color': '#000'}
                                    },
                                    'series': [{
                                        'name': 'Problemas',
                                        'type': 'heatmap',
                                        'data': data_for_chart,
                                        'label': {
                                            'show': True,
                                            'fontSize': 11,
                                            'fontWeight': 'bold',
                                            'color': '#000'
                                        },
                                        'emphasis': {
                                            'itemStyle': {
                                                'shadowBlur': 10,
                                                'shadowColor': 'rgba(0, 0, 0, 0.5)'
                                            }
                                        }
                                    }]
                                }).classes('w-full').style(f'height: {max(500, len(empresas_ordenadas) * 50 + 150)}px;')
                    
                            # Estatísticas resumidas
                            with ui.row().classes('w-full gap-4 flex-wrap mt-4'):
                                # Empresa com mais problemas
                                empresa_max_problemas = None
                                max_problemas_total = 0
                                for empresa, areas_dict in heatmap_data.items():
                                    total = sum(areas_dict.values())
                                    if total > max_problemas_total:
                                        max_problemas_total = total
                                        empresa_max_problemas = empresa
                        
                                if empresa_max_problemas:
                                    with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #dc2626;'):
                                        ui.label('Empresa com Mais Problemas').classes('text-gray-500 text-sm mb-1')
                                        ui.label(get_short_name(empresa_max_problemas, _clients)).classes('text-lg font-bold').style('color: #dc2626;')
                                        ui.label(f'{max_problemas_total} problema(s) total').classes('text-xs text-gray-400 mt-1')
                        
                                # Área com mais problemas
                                area_max_problemas = None
                                max_problemas_area = 0
                                area_counter_total = {}
                                for empresa, areas_dict in heatmap_data.items():
                                    for area, count in areas_dict.items():
                                        if area not in area_counter_total:
                                            area_counter_total[area] = 0
                                        area_counter_total[area] += count
                        
                                if area_counter_total:
                                    area_max_problemas = max(area_counter_total.items(), key=lambda x: x[1])
                                    max_problemas_area = area_max_problemas[1]
                                    area_max_problemas = area_max_problemas[0]
                            
                                    with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #0891b2;'):
                                        ui.label('Área com Mais Problemas').classes('text-gray-500 text-sm mb-1')
                                        ui.label(area_max_problemas).classes('text-lg font-bold').style('color: #0891b2;')
                                        ui.label(f'{max_problemas_area} problema(s) total').classes('text-xs text-gray-400 mt-1')
                        else:
                            with ui.card().classes('w-full p-4'):
                                with ui.column().classes('items-center justify-center gap-4'):
                                    ui.icon('info', size='64px').classes('text-gray-400')
                                    ui.label('Nenhum dado disponível').classes('text-xl font-bold text-gray-600')
                                    ui.label('Cadastre processos com áreas e clientes para visualizar o mapa de calor.').classes('text-gray-500 text-center max-w-md')
                    
                    elif current_tab == 'probabilidade':
                                # Aba Probabilidades de Êxito
                                # Coletar dados de probabilidades das teses dos casos
                                probabilidades_data = {
                                    'Alta': 0,
                                    'Média': 0,
                                    'Baixa': 0,
                                    'Não informado': 0
                                }
                        
                                casos_com_probabilidade = []
                                for idx, case in enumerate(_cases):
                                    theses = case.get('theses', [])
                                    for thesis_idx, thesis in enumerate(theses):
                                        prob = thesis.get('probability', 'Não informado')
                                        if prob in probabilidades_data:
                                            probabilidades_data[prob] += 1
                                        else:
                                            probabilidades_data['Não informado'] += 1
                                
                                        casos_com_probabilidade.append({
                                            'id': f"{idx}_{thesis_idx}",
                                            'case': case.get('title', 'Sem título'),
                                            'thesis': thesis.get('name', 'Sem nome'),
                                            'probability': prob,
                                            'status': thesis.get('status', 'Não informado')
                                        })
                        
                                total_probabilidades = sum(probabilidades_data.values())
                        
                                with ui.card().classes('w-full p-4 mb-4 bg-blue-50 border-l-4').style('border-left-color: #2563eb;'):
                                    with ui.row().classes('items-center gap-3'):
                                        ui.icon('info', size='md').classes('text-blue-600')
                                        with ui.column().classes('flex-grow'):
                                            ui.label('Módulo em Desenvolvimento').classes('text-sm font-semibold text-blue-800')
                                            ui.label('Esta visualização está sendo aprimorada. Os dados abaixo mostram as probabilidades de êxito das teses já cadastradas nos casos.').classes('text-xs text-blue-700')
                        
                                if total_probabilidades > 0:
                                    # Cards de resumo
                                    with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                                        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #16a34a;'):
                                            ui.label('Alta Probabilidade').classes('text-gray-500 text-sm mb-1')
                                            ui.label(str(probabilidades_data['Alta'])).classes('text-3xl font-bold').style('color: #16a34a;')
                                            ui.label('Teses com alta probabilidade de êxito').classes('text-xs text-gray-400 mt-1')
                                
                                        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #f59e0b;'):
                                            ui.label('Média Probabilidade').classes('text-gray-500 text-sm mb-1')
                                            ui.label(str(probabilidades_data['Média'])).classes('text-3xl font-bold').style('color: #f59e0b;')
                                            ui.label('Teses com média probabilidade de êxito').classes('text-xs text-gray-400 mt-1')
                                
                                        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style('border-left-color: #dc2626;'):
                                            ui.label('Baixa Probabilidade').classes('text-gray-500 text-sm mb-1')
                                            ui.label(str(probabilidades_data['Baixa'])).classes('text-3xl font-bold').style('color: #dc2626;')
                                            ui.label('Teses com baixa probabilidade de êxito').classes('text-xs text-gray-400 mt-1')
                            
                                    # Gráficos
                                    with ui.row().classes('w-full gap-4 flex-wrap'):
                                        # Gráfico de pizza
                                        with ui.card().classes('flex-1 min-w-80 p-4'):
                                            ui.label('Distribuição de Probabilidades').classes('text-lg font-semibold text-gray-700 mb-4')
                                    
                                            ui.echart({
                                        'tooltip': {
                                            'trigger': 'item',
                                            'formatter': '{b}: {c} ({d}%)'
                                        },
                                        'legend': {
                                            'orient': 'vertical',
                                            'left': 'left',
                                            'top': 'center',
                                            'fontSize': 13
                                        },
                                        'series': [{
                                            'name': 'Probabilidades',
                                            'type': 'pie',
                                            'radius': ['40%', '70%'],
                                            'center': ['65%', '50%'],
                                            'avoidLabelOverlap': False,
                                            'itemStyle': {
                                                'borderRadius': 10,
                                                'borderColor': '#fff',
                                                'borderWidth': 2
                                            },
                                            'label': {
                                                'show': True,
                                                'position': 'outside',
                                                'fontSize': 13,
                                                'fontWeight': 'bold',
                                                'formatter': '{b}\n{c} ({d}%)'
                                            },
                                            'labelLine': {'show': True},
                                            'data': [
                                                {'value': probabilidades_data['Alta'], 'name': 'Alta', 'itemStyle': {'color': '#16a34a'}},
                                                {'value': probabilidades_data['Média'], 'name': 'Média', 'itemStyle': {'color': '#f59e0b'}},
                                                {'value': probabilidades_data['Baixa'], 'name': 'Baixa', 'itemStyle': {'color': '#dc2626'}},
                                                {'value': probabilidades_data['Não informado'], 'name': 'Não informado', 'itemStyle': {'color': '#6b7280'}}
                                            ]
                                        }]
                                            }).classes('w-full h-80')
                                
                                        # Gráfico de barras
                                        with ui.card().classes('flex-1 min-w-80 p-4'):
                                            ui.label('Comparativo de Probabilidades').classes('text-lg font-semibold text-gray-700 mb-4')
                                    
                                            categories = ['Alta', 'Média', 'Baixa', 'Não informado']
                                            values = [
                                                probabilidades_data['Alta'],
                                                probabilidades_data['Média'],
                                                probabilidades_data['Baixa'],
                                                probabilidades_data['Não informado']
                                            ]
                                            colors = ['#16a34a', '#f59e0b', '#dc2626', '#6b7280']
                                    
                                            chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
                                    
                                            ui.echart({
                                        'tooltip': {
                                            'trigger': 'axis',
                                            'axisPointer': {'type': 'shadow'}
                                        },
                                        'grid': {
                                            'left': '3%',
                                            'right': '4%',
                                            'bottom': '3%',
                                            'containLabel': True
                                        },
                                        'xAxis': {
                                            'type': 'category',
                                            'data': categories,
                                            'axisLabel': {
                                                'interval': 0,
                                                'fontSize': 12,
                                                'fontWeight': 'bold'
                                            }
                                        },
                                        'yAxis': {
                                            'type': 'value',
                                            'minInterval': 1
                                        },
                                        'series': [{
                                            'name': 'Teses',
                                            'type': 'bar',
                                            'data': chart_data,
                                            'barWidth': '50%',
                                            'label': {
                                                'show': True,
                                                'position': 'top',
                                                'fontWeight': 'bold',
                                                'fontSize': 14
                                            }
                                        }]
                                            }).classes('w-full h-80')
                            
                                    # Tabela detalhada (opcional, para futuro)
                                    with ui.card().classes('w-full p-4 mt-4'):
                                        ui.label('Detalhamento das Teses').classes('text-lg font-semibold text-gray-700 mb-4')
                                        ui.label('Esta tabela será expandida no futuro com mais análises e métricas.').classes('text-sm text-gray-500 mb-4')
                                
                                        if casos_com_probabilidade:
                                            columns_table = [
                                                {'name': 'case', 'label': 'Caso', 'field': 'case', 'align': 'left'},
                                                {'name': 'thesis', 'label': 'Tese', 'field': 'thesis', 'align': 'left'},
                                                {'name': 'probability', 'label': 'Probabilidade', 'field': 'probability', 'align': 'center'},
                                                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'}
                                            ]
                                            ui.table(columns=columns_table, rows=casos_com_probabilidade[:20], row_key='id').classes('w-full').props('flat bordered')
                                        else:
                                            ui.label('Nenhuma tese cadastrada com probabilidade de êxito.').classes('text-gray-400 italic text-center py-8')
                                else:
                                    with ui.card().classes('w-full p-4'):
                                        with ui.column().classes('items-center justify-center gap-4'):
                                            ui.icon('trending_up', size='64px').classes('text-gray-400')
                                            ui.label('Nenhum dado disponível').classes('text-xl font-bold text-gray-600')
                                            ui.label('Cadastre teses com probabilidades de êxito nos casos para visualizar os gráficos.').classes('text-gray-500 text-center max-w-md')
                
                content_area()
