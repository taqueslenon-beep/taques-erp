"""
Dashboard de Oportunidades Ativas.
Análise detalhada do funil de vendas com gráficos e estatísticas.
"""
from datetime import datetime, timedelta
from collections import OrderedDict
from nicegui import ui
from mini_erp.core import layout, PRIMARY_COLOR
from mini_erp.auth import is_authenticated
from mini_erp.gerenciadores.gerenciador_workspace import definir_workspace
from ..novos_negocios.novos_negocios_services import obter_estatisticas_detalhadas
from ..painel.chart_builders import build_pie_chart_config, build_bar_chart_config, build_line_chart_config
from ..painel.ui_components import create_empty_chart_state
from .casos.models import obter_cor_nucleo


# Cores dos status do Kanban (consistentes com o módulo)
STATUS_CORES = {
    'agir': '#EF4444',           # Vermelho
    'em_andamento': '#EAB308',    # Amarelo
    'aguardando': '#FDE047',      # Amarelo claro
    'monitorando': '#F97316',     # Laranja
}

# Nomes de exibição dos status
STATUS_NOMES = {
    'agir': 'Agir',
    'em_andamento': 'Em Andamento',
    'aguardando': 'Aguardando',
    'monitorando': 'Monitorando',
}


@ui.page('/visao-geral/dashboard-oportunidades')
def dashboard_oportunidades():
    """Página de dashboard de oportunidades ativas."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Define o workspace
    definir_workspace('visao_geral_escritorio')
    
    # Busca estatísticas
    stats = obter_estatisticas_detalhadas()
    
    with layout('Dashboard de Oportunidades', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Dashboard de Oportunidades', None)]):
        # Header com botão voltar
        with ui.row().classes('w-full justify-between items-center mb-6'):
            with ui.column().classes('gap-0'):
                ui.label('Dashboard de Oportunidades').classes('text-2xl font-bold text-gray-800')
                ui.label('Análise detalhada do funil de vendas').classes('text-sm text-gray-500')
            
            ui.button('Voltar', icon='arrow_back', on_click=lambda: ui.navigate.to('/visao-geral/painel')).props('flat')
        
        # Grid de gráficos
        # Linha 1: Por Status (pizza) e Evolução Mensal (linha)
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            # Gráfico 1: Oportunidades por Status (Pizza/Donut)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Oportunidades por Status').classes('text-lg font-semibold text-gray-700 mb-4')
                
                if stats['total'] > 0:
                    # Prepara dados para gráfico de pizza
                    pie_data = []
                    for status in ['agir', 'em_andamento', 'aguardando', 'monitorando']:
                        quantidade = stats['por_status'].get(status, 0)
                        if quantidade > 0:
                            pie_data.append({
                                'value': quantidade,
                                'name': STATUS_NOMES[status],
                                'itemStyle': {'color': STATUS_CORES[status]}
                            })
                    
                    if pie_data:
                        config = build_pie_chart_config(
                            data=pie_data,
                            series_name='Oportunidades',
                            donut=True,
                            show_percentage=True
                        )
                        ui.echart(config).classes('w-full h-80')
                        
                        # Total abaixo do gráfico
                        with ui.row().classes('w-full justify-center mt-2'):
                            ui.label(f'Total: {stats["total"]} oportunidades ativas').classes('text-sm font-semibold text-gray-600')
                    else:
                        create_empty_chart_state('Nenhuma oportunidade ativa.')
                else:
                    create_empty_chart_state('Nenhuma oportunidade ativa.')
            
            # Gráfico 2: Evolução Mensal (Linha)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Evolução Mensal').classes('text-lg font-semibold text-gray-700 mb-4')
                
                if stats['por_mes']:
                    # Ordena meses por data (mais antigo primeiro)
                    meses_ordenados = sorted(stats['por_mes'].items(), key=lambda x: (
                        int(x[0].split('/')[1]),  # Ano
                        int(x[0].split('/')[0])   # Mês
                    ))
                    
                    # Limita aos últimos 6 meses
                    if len(meses_ordenados) > 6:
                        meses_ordenados = meses_ordenados[-6:]
                    
                    # Formata meses para exibição (Mês/Ano -> Abr/2024)
                    meses_labels = []
                    valores = []
                    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    
                    for mes_ano, quantidade in meses_ordenados:
                        mes, ano = mes_ano.split('/')
                        mes_nome = meses_nomes[int(mes) - 1]
                        meses_labels.append(f'{mes_nome}/{ano[-2:]}')
                        valores.append(quantidade)
                    
                    # Configuração do gráfico de linha
                    config = build_line_chart_config(
                        years=meses_labels,
                        series_data=[{
                            'name': 'Oportunidades Criadas',
                            'data': valores,
                            'color': PRIMARY_COLOR
                        }],
                        show_area=True
                    )
                    ui.echart(config).classes('w-full h-80')
                else:
                    create_empty_chart_state('Nenhum dado mensal disponível.')
        
        # Linha 2: Por Núcleo (barras)
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            # Gráfico 3: Por Núcleo (Barras)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Oportunidades por Núcleo').classes('text-lg font-semibold text-gray-700 mb-4')
                
                if stats['por_nucleo']:
                    # Ordena por quantidade (maior primeiro)
                    nucleos_ordenados = sorted(
                        stats['por_nucleo'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    categories = [nucleo for nucleo, _ in nucleos_ordenados]
                    values = [qtd for _, qtd in nucleos_ordenados]
                    
                    # Cores baseadas no núcleo
                    colors = [obter_cor_nucleo(nucleo) for nucleo in categories]
                    
                    config = build_bar_chart_config(
                        categories=categories,
                        values=values,
                        colors=colors,
                        series_name='Oportunidades',
                        horizontal=False
                    )
                    ui.echart(config).classes('w-full h-80')
                else:
                    create_empty_chart_state('Nenhuma oportunidade por núcleo.')
        
        # Placeholder para gráficos futuros (Parte 2)
        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Por Origem').classes('text-lg font-semibold text-gray-700 mb-4')
                ui.label('Em desenvolvimento (Parte 2)').classes('text-gray-400 italic')
            
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Por Responsável').classes('text-lg font-semibold text-gray-700 mb-4')
                ui.label('Em desenvolvimento (Parte 2)').classes('text-gray-400 italic')

