"""
Implementações individuais de cada aba do Painel.
Cada função render_tab_* recebe o data_service e renderiza a visualização.
"""
import json
from nicegui import ui
from collections import Counter

from .models import (
    STATUS_COLORS, AREA_COLORS, PROBABILITY_COLORS, STATE_COLORS,
    CASE_TYPE_COLORS, CATEGORY_COLORS, TEMPORAL_COLORS, FINANCIAL_COLORS,
    HEATMAP_COLORS,
)
from .helpers import get_short_name, format_currency
from .chart_builders import (
    build_bar_chart_config, build_pie_chart_config, build_line_chart_config,
    build_heatmap_config, build_simple_pie_config,
)
from .ui_components import (
    create_stat_card, create_metric_row, create_empty_state,
    create_empty_chart_state, create_development_banner, create_under_construction,
)
from .data_service import PainelDataService


# =============================================================================
# ABA: TOTAIS
# =============================================================================
def render_tab_totais(ds: PainelDataService, primary_color: str) -> None:
    """Renderiza a aba de Totais gerais."""
    with ui.row().classes('gap-4 flex-wrap'):
        with ui.card().classes('w-64 p-4'):
            ui.label('Total de Casos').classes('text-gray-500 text-sm')
            ui.label(str(ds.total_casos)).classes('text-3xl font-bold').style(f'color: {primary_color};')
        with ui.card().classes('w-64 p-4'):
            ui.label('Total de Processos').classes('text-gray-500 text-sm')
            ui.label(str(ds.total_processos)).classes('text-3xl font-bold').style(f'color: {primary_color};')
        with ui.card().classes('w-64 p-4'):
            ui.label('Cenários Mapeados').classes('text-gray-500 text-sm')
            ui.label(str(ds.total_cenarios)).classes('text-3xl font-bold').style(f'color: {primary_color};')


# =============================================================================
# ABA: COMPARATIVO (Antigo/Novo/Futuro)
# =============================================================================
def render_tab_comparativo(ds: PainelDataService) -> None:
    """Renderiza a aba Comparativo de tipos de caso."""
    counts = ds.get_cases_type_counts()
    total_old = counts['Antigo']
    total_new = counts['Novo']
    total_future = counts['Futuro']
    
    # Cards com totais
    with ui.row().classes('gap-4 flex-wrap mb-4'):
        with ui.card().classes('w-64 p-4'):
            ui.label('Casos Antigos').classes('text-gray-500 text-sm')
            ui.label(str(total_old)).classes('text-3xl font-bold').style(f'color: {CASE_TYPE_COLORS["Antigo"]};')
        with ui.card().classes('w-64 p-4'):
            ui.label('Casos Novos').classes('text-gray-500 text-sm')
            ui.label(str(total_new)).classes('text-3xl font-bold').style(f'color: {CASE_TYPE_COLORS["Novo"]};')
        with ui.card().classes('w-64 p-4'):
            ui.label('Casos Futuros').classes('text-gray-500 text-sm')
            ui.label(str(total_future)).classes('text-3xl font-bold').style(f'color: {CASE_TYPE_COLORS["Futuro"]};')
    
    # Gráficos lado a lado
    with ui.row().classes('w-full gap-4 flex-wrap'):
        # Gráfico de Barras
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Comparativo de Casos').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if total_old > 0 or total_new > 0 or total_future > 0:
                categories = ['Casos Antigos', 'Casos Novos', 'Casos Futuros']
                values = [total_old, total_new, total_future]
                colors = [CASE_TYPE_COLORS['Antigo'], CASE_TYPE_COLORS['Novo'], CASE_TYPE_COLORS['Futuro']]
                
                config = build_bar_chart_config(
                    categories=categories,
                    values=values,
                    colors=colors,
                    bar_width='50%',
                    label_font_size=16,
                )
                ui.echart(config).classes('w-full h-80')
            else:
                create_empty_chart_state('Nenhum caso cadastrado ainda.')
        
        # Gráfico de Pizza
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Distribuição Percentual').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if total_old > 0 or total_new > 0 or total_future > 0:
                pie_data = [
                    {'value': total_old, 'name': 'Casos Antigos', 'itemStyle': {'color': CASE_TYPE_COLORS['Antigo']}},
                    {'value': total_new, 'name': 'Casos Novos', 'itemStyle': {'color': CASE_TYPE_COLORS['Novo']}},
                    {'value': total_future, 'name': 'Casos Futuros', 'itemStyle': {'color': CASE_TYPE_COLORS['Futuro']}},
                ]
                config = build_pie_chart_config(data=pie_data, series_name='Casos')
                ui.echart(config).classes('w-full h-80')
            else:
                create_empty_chart_state('Nenhum caso cadastrado ainda.')


# =============================================================================
# ABA: CATEGORIA (Contencioso/Consultivo)
# =============================================================================
def render_tab_categoria(ds: PainelDataService) -> None:
    """Renderiza a aba de Categorias."""
    counts = ds.get_cases_by_category()
    total_contencioso = counts['Contencioso']
    total_consultivo = counts['Consultivo']
    
    # Cards com totais
    with ui.row().classes('gap-4 flex-wrap mb-4'):
        with ui.card().classes('w-64 p-4 border-l-4').style(f'border-left-color: {CATEGORY_COLORS["Contencioso"]};'):
            ui.label('Contencioso').classes('text-gray-500 text-sm')
            ui.label(str(total_contencioso)).classes('text-3xl font-bold').style(f'color: {CATEGORY_COLORS["Contencioso"]};')
        with ui.card().classes('w-64 p-4 border-l-4').style(f'border-left-color: {CATEGORY_COLORS["Consultivo"]};'):
            ui.label('Consultivo').classes('text-gray-500 text-sm')
            ui.label(str(total_consultivo)).classes('text-3xl font-bold').style(f'color: {CATEGORY_COLORS["Consultivo"]};')
    
    # Gráficos lado a lado
    with ui.row().classes('w-full gap-4 flex-wrap'):
        # Gráfico de Barras
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Casos por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if total_contencioso > 0 or total_consultivo > 0:
                categories = ['Contencioso', 'Consultivo']
                values = [total_contencioso, total_consultivo]
                colors = [CATEGORY_COLORS['Contencioso'], CATEGORY_COLORS['Consultivo']]
                
                config = build_bar_chart_config(
                    categories=categories,
                    values=values,
                    colors=colors,
                    bar_width='50%',
                    label_font_size=18,
                )
                ui.echart(config).classes('w-full h-80')
            else:
                create_empty_chart_state('Nenhum caso cadastrado ainda.')
        
        # Gráfico de Pizza
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Distribuição Percentual').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if total_contencioso > 0 or total_consultivo > 0:
                pie_data = [
                    {'value': total_contencioso, 'name': 'Contencioso', 'itemStyle': {'color': CATEGORY_COLORS['Contencioso']}},
                    {'value': total_consultivo, 'name': 'Consultivo', 'itemStyle': {'color': CATEGORY_COLORS['Consultivo']}},
                ]
                config = build_pie_chart_config(data=pie_data, series_name='Casos', label_font_size=14)
                ui.echart(config).classes('w-full h-80')
            else:
                create_empty_chart_state('Nenhum caso cadastrado ainda.')


# =============================================================================
# ABA: TEMPORAL
# =============================================================================
def render_tab_temporal(ds: PainelDataService) -> None:
    """Renderiza a aba Temporal com filtros interativos."""
    # Estado dos filtros
    temporal_filters = {
        'show_cases': True,
        'show_processes': True,
        'year_start': '2008',
        'year_end': '2025'
    }
    
    @ui.refreshable
    def temporal_chart():
        """Renderiza o gráfico temporal de casos e processos."""
        # Coletar dados
        cases_by_year = ds.get_cases_by_year() if temporal_filters['show_cases'] else Counter()
        processes_by_year = ds.get_processes_by_year() if temporal_filters['show_processes'] else Counter()
        
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
        
        # Preparar dados para o gráfico
        cases_data = [cases_by_year.get(year, 0) for year in all_years]
        processes_data = [processes_by_year.get(year, 0) for year in all_years]
        
        # Preparar séries
        series_data = []
        if temporal_filters['show_cases']:
            series_data.append({
                'name': 'Casos',
                'data': cases_data,
                'color': TEMPORAL_COLORS['cases'],
            })
        
        if temporal_filters['show_processes']:
            series_data.append({
                'name': 'Processos',
                'data': processes_data,
                'color': TEMPORAL_COLORS['processes'],
            })
        
        with ui.card().classes('w-full p-6'):
            ui.label('Evolução Temporal de Casos e Processos').classes('text-xl font-semibold text-gray-800 mb-4')
            
            config = build_line_chart_config(years=all_years, series_data=series_data)
            ui.echart(config).classes('w-full h-96')
            
            # Estatísticas resumidas
            with ui.row().classes('w-full justify-center mt-6 gap-6 flex-wrap'):
                if temporal_filters['show_cases'] and cases_data:
                    total_cases = sum(cases_data)
                    max_cases = max(cases_data)
                    max_cases_year = all_years[cases_data.index(max_cases)]
                    
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('folder', size='sm').style(f'color: {TEMPORAL_COLORS["cases"]};')
                        ui.label(f'Casos: {total_cases} total | Pico: {max_cases_year} ({max_cases})').classes('text-sm font-medium text-gray-700')
                
                if temporal_filters['show_processes'] and processes_data:
                    total_processes = sum(processes_data)
                    max_processes = max(processes_data)
                    max_processes_year = all_years[processes_data.index(max_processes)]
                    
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('gavel', size='sm').style(f'color: {TEMPORAL_COLORS["processes"]};')
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


# =============================================================================
# ABA: STATUS
# =============================================================================
def render_tab_status(ds: PainelDataService) -> None:
    """Renderiza a aba de Status."""
    with ui.row().classes('w-full gap-4 flex-wrap'):
        # Gráfico de Casos por Status
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Casos por Status').classes('text-lg font-semibold text-gray-700 mb-4')
            
            sorted_cases_status = ds.get_cases_by_status()
            
            if sorted_cases_status:
                categories = [item[0] for item in sorted_cases_status]
                values = [item[1] for item in sorted_cases_status]
                colors = [STATUS_COLORS.get(cat, '#6b7280') for cat in categories]
                
                config = build_bar_chart_config(
                    categories=categories,
                    values=values,
                    colors=colors,
                    series_name='Casos',
                    rotate_labels=15,
                )
                ui.echart(config).classes('w-full h-80')
            else:
                create_empty_chart_state('Nenhum caso cadastrado ainda.')
        
        # Gráfico de Processos por Status
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Processos por Status').classes('text-lg font-semibold text-gray-700 mb-4')
            
            sorted_status = ds.get_processes_by_status()
            
            if sorted_status:
                categories = [item[0] for item in sorted_status]
                values = [item[1] for item in sorted_status]
                colors = [STATUS_COLORS.get(cat, '#6b7280') for cat in categories]
                
                config = build_bar_chart_config(
                    categories=categories,
                    values=values,
                    colors=colors,
                    series_name='Processos',
                    rotate_labels=15,
                )
                ui.echart(config).classes('w-full h-80')
            else:
                create_empty_chart_state('Nenhum processo cadastrado ainda.')


# =============================================================================
# ABA: RESULTADO
# =============================================================================
def render_tab_resultado() -> None:
    """Renderiza a aba de Resultado (em desenvolvimento)."""
    create_under_construction()


# =============================================================================
# ABA: CLIENTE
# =============================================================================
def render_tab_cliente(ds: PainelDataService, primary_color: str) -> None:
    """Renderiza a aba de Cliente."""
    # Gráfico de Casos por Cliente
    with ui.card().classes('w-full p-4 mb-4'):
        ui.label('Casos por Cliente').classes('text-lg font-semibold text-gray-700 mb-4')
        
        sorted_cases_clients = ds.get_cases_by_client()
        
        if sorted_cases_clients:
            client_names = [get_short_name(item[0], ds.clients) for item in sorted_cases_clients]
            client_values = [item[1] for item in sorted_cases_clients]
            
            chart_height = max(200, len(client_names) * 40)
            
            config = build_bar_chart_config(
                categories=client_names,
                values=client_values,
                series_name='Casos',
                horizontal=True,
            )
            # Override color
            config['series'][0]['itemStyle'] = {'color': '#0891b2'}
            
            ui.echart(config).classes('w-full').style(f'height: {chart_height}px;')
        else:
            create_empty_chart_state('Nenhum cliente vinculado a casos.')
    
    # Gráfico de Processos por Cliente
    with ui.card().classes('w-full p-4'):
        ui.label('Processos por Cliente').classes('text-lg font-semibold text-gray-700 mb-4')
        
        sorted_clients = ds.get_processes_by_client()
        
        if sorted_clients:
            client_names = [get_short_name(item[0], ds.clients) for item in sorted_clients]
            client_values = [item[1] for item in sorted_clients]
            
            chart_height = max(200, len(client_names) * 40)
            
            config = build_bar_chart_config(
                categories=client_names,
                values=client_values,
                series_name='Processos',
                horizontal=True,
            )
            config['series'][0]['itemStyle'] = {'color': primary_color}
            
            ui.echart(config).classes('w-full').style(f'height: {chart_height}px;')
        else:
            create_empty_chart_state('Nenhum cliente vinculado a processos.')


# =============================================================================
# ABA: PARTE CONTRÁRIA
# =============================================================================
def render_tab_parte(ds: PainelDataService) -> None:
    """Renderiza a aba de Parte Contrária."""
    with ui.card().classes('w-full p-4'):
        ui.label('Processos por Parte Contrária').classes('text-lg font-semibold text-gray-700 mb-4')
        
        sorted_opposing = ds.get_processes_by_opposing_party()
        
        if sorted_opposing:
            opposing_names = [get_short_name(item[0], ds.opposing_parties) for item in sorted_opposing]
            opposing_values = [item[1] for item in sorted_opposing]
            
            chart_height = max(200, len(opposing_names) * 40)
            
            config = build_bar_chart_config(
                categories=opposing_names,
                values=opposing_values,
                series_name='Processos',
                horizontal=True,
            )
            config['series'][0]['itemStyle'] = {'color': '#dc2626'}
            
            ui.echart(config).classes('w-full').style(f'height: {chart_height}px;')
        else:
            create_empty_chart_state('Nenhuma parte contrária vinculada a processos.')


# =============================================================================
# ABA: ÁREA
# =============================================================================
def render_tab_area(ds: PainelDataService) -> None:
    """Renderiza a aba de Área jurídica."""
    with ui.card().classes('w-full p-4'):
        ui.label('Processos por Área').classes('text-lg font-semibold text-gray-700 mb-4')
        
        sorted_areas = ds.get_processes_by_area()
        
        if sorted_areas:
            area_names = [item[0] for item in sorted_areas]
            area_values = [item[1] for item in sorted_areas]
            
            chart_height = max(200, len(area_names) * 40)
            
            # Preparar dados com cores específicas
            chart_data = [
                {
                    'value': value,
                    'itemStyle': {'color': AREA_COLORS.get(area_name, '#9ca3af')}
                }
                for area_name, value in zip(reversed(area_names), reversed(area_values))
            ]
            
            config = {
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
                    'axisLabel': {'fontSize': 12}
                },
                'series': [{
                    'name': 'Processos',
                    'type': 'bar',
                    'data': chart_data,
                    'barWidth': '60%',
                    'label': {
                        'show': True,
                        'position': 'right',
                        'fontWeight': 'bold',
                        'fontSize': 13
                    }
                }]
            }
            
            ui.echart(config).classes('w-full').style(f'height: {chart_height}px;')
        else:
            create_empty_chart_state('Nenhum processo com área cadastrada.')


# =============================================================================
# ABA: ÁREA (HA)
# =============================================================================
def render_tab_area_ha() -> None:
    """Renderiza a aba de Área em hectares (em desenvolvimento)."""
    with ui.card().classes('w-full p-4'):
        with ui.column().classes('items-center justify-center gap-4'):
            ui.icon('construction', size='64px').classes('text-gray-400')
            ui.label('Módulo em Construção').classes('text-2xl font-bold text-gray-600')
            ui.label('Visualizações por área (hectares) e afetação estarão disponíveis em breve.').classes('text-gray-500 text-center max-w-md')


# =============================================================================
# ABA: ESTADO
# =============================================================================
def render_tab_estado(ds: PainelDataService) -> None:
    """Renderiza a aba de Estado."""
    cases_by_state = ds.get_cases_by_state()
    processes_by_state = ds.get_processes_by_state()
    
    casos_parana = cases_by_state['Paraná']
    casos_sc = cases_by_state['Santa Catarina']
    processos_parana = processes_by_state['Paraná']
    processos_sc = processes_by_state['Santa Catarina']
    
    with ui.row().classes('w-full gap-4 flex-wrap'):
        # Gráfico de Casos por Estado
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Distribuição de Casos').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if casos_parana > 0 or casos_sc > 0:
                pie_data = [
                    {'value': casos_parana, 'name': 'Paraná', 'itemStyle': {'color': STATE_COLORS['Paraná']}},
                    {'value': casos_sc, 'name': 'Santa Catarina', 'itemStyle': {'color': STATE_COLORS['Santa Catarina']}},
                ]
                config = build_simple_pie_config(data=pie_data, series_name='Casos')
                ui.echart(config).classes('w-full h-64')
            else:
                create_empty_chart_state('Nenhum caso cadastrado com estado definido.')
        
        # Gráfico de Processos por Estado
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Distribuição de Processos').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if processos_parana > 0 or processos_sc > 0:
                pie_data = [
                    {'value': processos_parana, 'name': 'Paraná', 'itemStyle': {'color': STATE_COLORS['Paraná']}},
                    {'value': processos_sc, 'name': 'Santa Catarina', 'itemStyle': {'color': STATE_COLORS['Santa Catarina']}},
                ]
                config = build_simple_pie_config(data=pie_data, series_name='Processos')
                ui.echart(config).classes('w-full h-64')
            else:
                create_empty_chart_state('Nenhum processo vinculado a casos com estado definido.')


# =============================================================================
# ABA: HEATMAP
# =============================================================================
def render_tab_heatmap(ds: PainelDataService) -> None:
    """Renderiza a aba de Mapa de Calor."""
    heatmap_info = ds.build_heatmap_data()
    heatmap_data = heatmap_info['data']
    empresas_ordenadas = heatmap_info['empresas']
    areas_ordenadas = heatmap_info['areas']
    
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
        
        # Criar dados no formato do ECharts
        data_for_chart = []
        empresas_nomes_curtos = [get_short_name(emp, ds.clients) for emp in empresas_ordenadas]
        
        for i, empresa in enumerate(empresas_ordenadas):
            for j, area in enumerate(areas_ordenadas):
                value = heatmap_values[i][j]
                if value > 0:
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
            
            config = build_heatmap_config(
                data=data_for_chart,
                x_categories=areas_ordenadas,
                y_categories=empresas_nomes_curtos,
                max_value=max_value,
                tooltip_formatter=tooltip_formatter,
                colors=HEATMAP_COLORS,
            )
            
            ui.echart(config).classes('w-full').style(f'height: {max(500, len(empresas_ordenadas) * 50 + 150)}px;')
        
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
                    ui.label(get_short_name(empresa_max_problemas, ds.clients)).classes('text-lg font-bold').style('color: #dc2626;')
                    ui.label(f'{max_problemas_total} problema(s) total').classes('text-xs text-gray-400 mt-1')
            
            # Área com mais problemas
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
            create_empty_state(
                icon='info',
                title='Nenhum dado disponível',
                message='Cadastre processos com áreas e clientes para visualizar o mapa de calor.'
            )


# =============================================================================
# ABA: PROBABILIDADE
# =============================================================================
def render_tab_probabilidade(ds: PainelDataService) -> None:
    """Renderiza a aba de Probabilidades de êxito."""
    prob_data = ds.collect_probability_data()
    probabilidades_data = prob_data['counts']
    casos_com_probabilidade = prob_data['details']
    total_probabilidades = prob_data['total']
    
    create_development_banner(
        title='Módulo em Desenvolvimento',
        message='Esta visualização está sendo aprimorada. Os dados abaixo mostram as probabilidades de êxito das teses já cadastradas nos casos.',
        color='blue'
    )
    
    if total_probabilidades > 0:
        # Cards de resumo
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style(f'border-left-color: {PROBABILITY_COLORS["Alta"]};'):
                ui.label('Alta Probabilidade').classes('text-gray-500 text-sm mb-1')
                ui.label(str(probabilidades_data['Alta'])).classes('text-3xl font-bold').style(f'color: {PROBABILITY_COLORS["Alta"]};')
                ui.label('Teses com alta probabilidade de êxito').classes('text-xs text-gray-400 mt-1')
            
            with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style(f'border-left-color: {PROBABILITY_COLORS["Média"]};'):
                ui.label('Média Probabilidade').classes('text-gray-500 text-sm mb-1')
                ui.label(str(probabilidades_data['Média'])).classes('text-3xl font-bold').style(f'color: {PROBABILITY_COLORS["Média"]};')
                ui.label('Teses com média probabilidade de êxito').classes('text-xs text-gray-400 mt-1')
            
            with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style(f'border-left-color: {PROBABILITY_COLORS["Baixa"]};'):
                ui.label('Baixa Probabilidade').classes('text-gray-500 text-sm mb-1')
                ui.label(str(probabilidades_data['Baixa'])).classes('text-3xl font-bold').style(f'color: {PROBABILITY_COLORS["Baixa"]};')
                ui.label('Teses com baixa probabilidade de êxito').classes('text-xs text-gray-400 mt-1')
        
        # Gráficos
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Gráfico de pizza
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Distribuição de Probabilidades').classes('text-lg font-semibold text-gray-700 mb-4')
                
                pie_data = [
                    {'value': probabilidades_data['Alta'], 'name': 'Alta', 'itemStyle': {'color': PROBABILITY_COLORS['Alta']}},
                    {'value': probabilidades_data['Média'], 'name': 'Média', 'itemStyle': {'color': PROBABILITY_COLORS['Média']}},
                    {'value': probabilidades_data['Baixa'], 'name': 'Baixa', 'itemStyle': {'color': PROBABILITY_COLORS['Baixa']}},
                    {'value': probabilidades_data['Não informado'], 'name': 'Não informado', 'itemStyle': {'color': PROBABILITY_COLORS['Não informado']}},
                ]
                config = build_pie_chart_config(data=pie_data, series_name='Probabilidades')
                ui.echart(config).classes('w-full h-80')
            
            # Gráfico de barras
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Comparativo de Probabilidades').classes('text-lg font-semibold text-gray-700 mb-4')
                
                categories = ['Alta', 'Média', 'Baixa', 'Não informado']
                values = [probabilidades_data[c] for c in categories]
                colors = [PROBABILITY_COLORS[c] for c in categories]
                
                config = build_bar_chart_config(
                    categories=categories,
                    values=values,
                    colors=colors,
                    series_name='Teses',
                    bar_width='50%',
                )
                ui.echart(config).classes('w-full h-80')
        
        # Tabela detalhada
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
                create_empty_chart_state('Nenhuma tese cadastrada com probabilidade de êxito.')
    else:
        with ui.card().classes('w-full p-4'):
            create_empty_state(
                icon='trending_up',
                title='Nenhum dado disponível',
                message='Cadastre teses com probabilidades de êxito nos casos para visualizar os gráficos.'
            )


# =============================================================================
# ABA: FINANCEIRO
# =============================================================================
def render_tab_financeiro(ds: PainelDataService) -> None:
    """Renderiza a aba Financeiro."""
    dados_financeiros = ds.collect_financial_data()
    
    # Banner de desenvolvimento
    create_development_banner(
        title='Painel Financeiro em Desenvolvimento',
        message='Esta visualização está sendo aprimorada. Os gráficos abaixo mostram os dados financeiros já cadastrados.',
        color='yellow'
    )
    
    # Cards de totais
    with ui.row().classes('gap-4 flex-wrap mb-6'):
        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style(f'border-left-color: {FINANCIAL_COLORS["exposicao"]};'):
            ui.label('Exposição Financeira Total').classes('text-gray-500 text-sm mb-1')
            ui.label(format_currency(dados_financeiros["exposicao"])).classes('text-2xl font-bold').style(f'color: {FINANCIAL_COLORS["exposicao"]};')
            ui.label('Multas em aberto (Confirmadas + Em análise)').classes('text-xs text-gray-400 mt-1')
        
        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style(f'border-left-color: {FINANCIAL_COLORS["pago"]};'):
            ui.label('Multas Pagas/Recuperadas').classes('text-gray-500 text-sm mb-1')
            ui.label(format_currency(dados_financeiros["pago"])).classes('text-2xl font-bold').style(f'color: {FINANCIAL_COLORS["pago"]};')
            ui.label('Total já recuperado').classes('text-xs text-gray-400 mt-1')
        
        with ui.card().classes('flex-1 min-w-64 p-4 border-l-4').style(f'border-left-color: {FINANCIAL_COLORS["futuro"]};'):
            ui.label('Multas Futuras/Estimadas').classes('text-gray-500 text-sm mb-1')
            ui.label(format_currency(dados_financeiros["futuro"])).classes('text-2xl font-bold').style(f'color: {FINANCIAL_COLORS["futuro"]};')
            ui.label('Valores estimados futuros').classes('text-xs text-gray-400 mt-1')
    
    # Gráficos principais
    total_geral = dados_financeiros["exposicao"] + dados_financeiros["pago"] + dados_financeiros["futuro"]
    
    with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
        # Gráfico 1: Pizza
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Distribuição Financeira Geral').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if total_geral > 0:
                pie_data = [
                    {'value': dados_financeiros["exposicao"], 'name': 'Em Aberto', 'itemStyle': {'color': FINANCIAL_COLORS['exposicao']}},
                    {'value': dados_financeiros["pago"], 'name': 'Pagas/Recuperadas', 'itemStyle': {'color': FINANCIAL_COLORS['pago']}},
                    {'value': dados_financeiros["futuro"], 'name': 'Futuras/Estimadas', 'itemStyle': {'color': FINANCIAL_COLORS['futuro']}},
                ]
                config = build_pie_chart_config(data=pie_data, series_name='Valores')
                ui.echart(config).classes('w-full h-80')
            else:
                with ui.column().classes('items-center justify-center py-8'):
                    ui.icon('info', size='48px').classes('text-gray-400 mb-2')
                    ui.label('Nenhum dado financeiro cadastrado').classes('text-gray-400 italic')
                    ui.label('Cadastre cálculos financeiros nos casos para visualizar os gráficos.').classes('text-xs text-gray-400 mt-2')
        
        # Gráfico 2: Barras
        with ui.card().classes('flex-1 min-w-80 p-4'):
            ui.label('Comparativo de Valores').classes('text-lg font-semibold text-gray-700 mb-4')
            
            if total_geral > 0:
                categories = ['Em Aberto', 'Pagas/Recuperadas', 'Futuras/Estimadas']
                values = [
                    dados_financeiros["exposicao"],
                    dados_financeiros["pago"],
                    dados_financeiros["futuro"]
                ]
                colors = [FINANCIAL_COLORS['exposicao'], FINANCIAL_COLORS['pago'], FINANCIAL_COLORS['futuro']]
                
                chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
                
                config = {
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
                }
                ui.echart(config).classes('w-full h-80')
            else:
                with ui.column().classes('items-center justify-center py-8'):
                    ui.icon('info', size='48px').classes('text-gray-400 mb-2')
                    ui.label('Nenhum dado financeiro cadastrado').classes('text-gray-400 italic')
                    ui.label('Cadastre cálculos financeiros nos casos para visualizar os gráficos.').classes('text-xs text-gray-400 mt-2')
    
    # Gráfico 3: Detalhamento da exposição
    if dados_financeiros["exposicao"] > 0:
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Detalhamento da Exposição Financeira').classes('text-lg font-semibold text-gray-700 mb-4')
            
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # Gráfico de pizza do detalhamento
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Status das Multas em Aberto').classes('text-md font-semibold text-gray-700 mb-4')
                    
                    pie_data = [
                        {'value': dados_financeiros["confirmado"], 'name': 'Confirmado', 'itemStyle': {'color': FINANCIAL_COLORS['confirmado']}},
                        {'value': dados_financeiros["em_analise"], 'name': 'Em Análise', 'itemStyle': {'color': FINANCIAL_COLORS['em_analise']}},
                    ]
                    config = build_pie_chart_config(data=pie_data, series_name='Status')
                    ui.echart(config).classes('w-full h-64')
                
                # Cards de detalhamento
                with ui.column().classes('flex-1 min-w-80 gap-4'):
                    with ui.card().classes('p-4 border-l-4').style(f'border-left-color: {FINANCIAL_COLORS["confirmado"]};'):
                        ui.label('Confirmado').classes('text-gray-500 text-sm mb-1')
                        ui.label(format_currency(dados_financeiros["confirmado"])).classes('text-xl font-bold').style(f'color: {FINANCIAL_COLORS["confirmado"]};')
                        ui.label(f'{len([d for d in dados_financeiros["detalhes_aberto"] if d.get("status") == "Confirmado"])} item(ns)').classes('text-xs text-gray-400 mt-1')
                    
                    with ui.card().classes('p-4 border-l-4').style(f'border-left-color: {FINANCIAL_COLORS["em_analise"]};'):
                        ui.label('Em Análise').classes('text-gray-500 text-sm mb-1')
                        ui.label(format_currency(dados_financeiros["em_analise"])).classes('text-xl font-bold').style(f'color: {FINANCIAL_COLORS["em_analise"]};')
                        ui.label(f'{len([d for d in dados_financeiros["detalhes_aberto"] if d.get("status") == "Em análise"])} item(ns)').classes('text-xs text-gray-400 mt-1')


