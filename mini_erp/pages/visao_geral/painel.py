"""
Página principal do workspace "Visão geral do escritório".
Exibe o painel com visão consolidada de todos os casos e processos do escritório.
"""
from typing import Dict, List, Any
from collections import Counter
from nicegui import ui, app
from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace
from .pessoas.database import listar_pessoas
from .casos.database import contar_casos, listar_casos_por_status, listar_casos
from ...usuarios.database import listar_usuarios
from ..painel.chart_builders import build_bar_chart_config, build_pie_chart_config
from ..painel.ui_components import create_empty_chart_state


# Cores para os gráficos
CORES_NUCLEO = {
    'Ambiental': '#4CAF50',
    'Cobranças': '#FF9800',
    'Generalista': '#2196F3'
}

CORES_STATUS = {
    'Em andamento': '#2196F3',
    'Concluído': '#4CAF50',
    'Concluído com pendências': '#FFC107',
    'Em monitoramento': '#9C27B0',
    'Substabelecido': '#9E9E9E'
}

CORES_PRIORIDADE = {
    'P1': '#ef4444',
    'P2': '#f97316',
    'P3': '#eab308',
    'P4': '#22c55e'
}


def agrupar_casos_por_nucleo(casos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa casos por núcleo."""
    contador = Counter()
    for caso in casos:
        nucleo = caso.get('nucleo', 'Não informado')
        if nucleo:
            contador[nucleo] += 1
    return dict(contador)


def agrupar_casos_por_status(casos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa casos por status."""
    contador = Counter()
    for caso in casos:
        status = caso.get('status', 'Não informado')
        if status:
            contador[status] += 1
    return dict(contador)


def agrupar_casos_por_categoria(casos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa casos por categoria."""
    contador = Counter()
    for caso in casos:
        categoria = caso.get('categoria', 'Não informado')
        if categoria:
            contador[categoria] += 1
    return dict(contador)


def agrupar_casos_por_prioridade(casos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa casos por prioridade."""
    contador = Counter()
    for caso in casos:
        prioridade = caso.get('prioridade', 'P4')
        # Normaliza prioridade
        if prioridade and prioridade.startswith('P'):
            contador[prioridade] += 1
        else:
            contador['P4'] += 1
    return dict(contador)


def agrupar_casos_por_responsavel(casos: List[Dict[str, Any]], usuarios: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa casos por responsável, usando nomes dos usuários."""
    # Criar mapa de IDs para nomes
    usuarios_map = {}
    for usuario in usuarios:
        usuario_id = usuario.get('_id')
        nome = usuario.get('nome_completo') or usuario.get('nome') or usuario.get('display_name', 'Sem nome')
        if usuario_id:
            usuarios_map[usuario_id] = nome
    
    contador = Counter()
    for caso in casos:
        responsaveis = caso.get('responsaveis', [])
        if isinstance(responsaveis, list):
            for resp_id in responsaveis:
                if resp_id in usuarios_map:
                    contador[usuarios_map[resp_id]] += 1
                else:
                    contador[f'ID: {resp_id}'] += 1
    
    # Ordena do maior para o menor
    return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))


@ui.page('/visao-geral/painel')
def painel():
    """Página principal do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace diretamente (sem middleware complexo)
    definir_workspace('visao_geral_escritorio')

    # Carregar dados de casos (uma única consulta)
    try:
        todos_casos = listar_casos()
        total_casos = len(todos_casos)
        casos_andamento = sum(1 for c in todos_casos if c.get('status') == 'Em andamento')
        casos_concluidos = sum(1 for c in todos_casos if c.get('status') == 'Concluído')
    except Exception:
        todos_casos = []
        total_casos = 0
        casos_andamento = 0
        casos_concluidos = 0
    
    # Carregar usuários para gráfico de responsáveis
    try:
        todos_usuarios = listar_usuarios()
    except Exception:
        todos_usuarios = []

    # Carregar dados de pessoas do workspace
    try:
        todas_pessoas = listar_pessoas()
        total_pessoas = len(todas_pessoas) if todas_pessoas else 0
        
        # Separar por tipo
        total_pf = sum(1 for p in todas_pessoas if p.get('tipo_pessoa') == 'PF')
        total_pj = sum(1 for p in todas_pessoas if p.get('tipo_pessoa') == 'PJ')
    except Exception:
        # Em caso de erro, mostra zeros
        total_pessoas = 0
        total_pf = 0
        total_pj = 0

    with layout('Painel', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Painel', None)]):
        # Cards de resumo
        with ui.row().classes('w-full gap-4 flex-wrap mb-6'):
            # Card Casos (primeiro card)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-shadow').style(f'border-left-color: {PRIMARY_COLOR}') as casos_card:
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('folder', size='24px').classes('text-gray-400')
                    ui.label('Casos').classes('text-sm text-gray-500')
                ui.label(str(total_casos)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR}')
                subtitulo = f'{casos_andamento} em andamento'
                if casos_concluidos > 0:
                    subtitulo += f', {casos_concluidos} concluídos'
                ui.label(subtitulo).classes('text-xs text-gray-400 mt-1')
                
                def abrir_casos():
                    ui.navigate.to('/visao-geral/casos')
                
                casos_card.on('click', abrir_casos)
            
            # Card Pessoas Cadastradas (funcional)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: {PRIMARY_COLOR}'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('people', size='24px').classes('text-gray-400')
                    ui.label('Pessoas Cadastradas').classes('text-sm text-gray-500')
                ui.label(str(total_pessoas)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR}')
                ui.label(f'{total_pf} PF, {total_pj} PJ').classes('text-xs text-gray-400 mt-1')
            
            # Card Processos Ativos (placeholder)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 border-gray-300'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('gavel', size='24px').classes('text-gray-300')
                    ui.label('Processos Ativos').classes('text-sm text-gray-500')
                ui.label('-').classes('text-3xl font-bold text-gray-300')
                ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')
            
            # Card Casos Abertos (placeholder)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 border-gray-300'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('folder', size='24px').classes('text-gray-300')
                    ui.label('Casos Abertos').classes('text-sm text-gray-500')
                ui.label('-').classes('text-3xl font-bold text-gray-300')
                ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')
            
            # Card Acordos (placeholder)
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4 border-gray-300'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('handshake', size='24px').classes('text-gray-300')
                    ui.label('Acordos').classes('text-sm text-gray-500')
                ui.label('-').classes('text-3xl font-bold text-gray-300')
                ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')
        
        # Seção de Estatísticas de Casos
        ui.label('Estatísticas de Casos').classes('text-2xl font-bold text-gray-800 mt-8 mb-4')
        
        # Grid de gráficos (responsivo: 2-3 colunas em desktop, 1 em mobile)
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # 1. Gráfico de Casos por Núcleo (Pizza/Donut)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Casos por Núcleo').classes('text-lg font-semibold text-gray-700 mb-4')
                
                dados_nucleo = agrupar_casos_por_nucleo(todos_casos)
                if dados_nucleo:
                    pie_data = [
                        {
                            'value': count,
                            'name': nucleo,
                            'itemStyle': {'color': CORES_NUCLEO.get(nucleo, '#9E9E9E')}
                        }
                        for nucleo, count in dados_nucleo.items()
                    ]
                    config = build_pie_chart_config(data=pie_data, series_name='Casos', donut=True)
                    ui.echart(config).classes('w-full h-80')
                else:
                    create_empty_chart_state('Nenhum caso cadastrado ainda.')
            
            # 2. Gráfico de Casos por Status (Barras Horizontal)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Casos por Status').classes('text-lg font-semibold text-gray-700 mb-4')
                
                dados_status = agrupar_casos_por_status(todos_casos)
                if dados_status:
                    # Ordena status na ordem especificada
                    status_ordem = ['Em andamento', 'Concluído', 'Concluído com pendências', 'Em monitoramento', 'Substabelecido']
                    status_ordenados = [s for s in status_ordem if s in dados_status]
                    status_ordenados.extend([s for s in dados_status.keys() if s not in status_ordem])
                    
                    categories = status_ordenados
                    values = [dados_status[s] for s in categories]
                    colors = [CORES_STATUS.get(s, '#9E9E9E') for s in categories]
                    
                    config = build_bar_chart_config(
                        categories=categories,
                        values=values,
                        colors=colors,
                        series_name='Casos',
                        horizontal=True
                    )
                    ui.echart(config).classes('w-full h-80')
                else:
                    create_empty_chart_state('Nenhum caso cadastrado ainda.')
            
            # 3. Gráfico de Casos por Categoria (Pizza)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Casos por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')
                
                dados_categoria = agrupar_casos_por_categoria(todos_casos)
                if dados_categoria:
                    # Cores para categorias (usar cores padrão ou gerar)
                    cores_categoria = ['#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#be185d']
                    pie_data = [
                        {
                            'value': count,
                            'name': categoria,
                            'itemStyle': {'color': cores_categoria[i % len(cores_categoria)]}
                        }
                        for i, (categoria, count) in enumerate(dados_categoria.items())
                    ]
                    config = build_pie_chart_config(data=pie_data, series_name='Casos', donut=True)
                    ui.echart(config).classes('w-full h-80')
                else:
                    create_empty_chart_state('Nenhum caso cadastrado ainda.')
        
        # Segunda linha de gráficos
        with ui.row().classes('w-full gap-4 flex-wrap mt-4'):
            # 4. Gráfico de Casos por Prioridade (Barras Vertical)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Casos por Prioridade').classes('text-lg font-semibold text-gray-700 mb-4')
                
                dados_prioridade = agrupar_casos_por_prioridade(todos_casos)
                if dados_prioridade:
                    # Ordena por prioridade (P1, P2, P3, P4)
                    prioridades_ordem = ['P1', 'P2', 'P3', 'P4']
                    prioridades_ordenadas = [p for p in prioridades_ordem if p in dados_prioridade]
                    
                    categories = prioridades_ordenadas
                    values = [dados_prioridade.get(p, 0) for p in categories]
                    colors = [CORES_PRIORIDADE.get(p, '#9E9E9E') for p in categories]
                    
                    config = build_bar_chart_config(
                        categories=categories,
                        values=values,
                        colors=colors,
                        series_name='Casos',
                        horizontal=False
                    )
                    ui.echart(config).classes('w-full h-80')
                else:
                    create_empty_chart_state('Nenhum caso cadastrado ainda.')
            
            # 5. Gráfico de Casos por Responsável (Barras Horizontal)
            with ui.card().classes('flex-1 min-w-80 p-4'):
                ui.label('Casos por Responsável').classes('text-lg font-semibold text-gray-700 mb-4')
                
                dados_responsavel = agrupar_casos_por_responsavel(todos_casos, todos_usuarios)
                if dados_responsavel:
                    # Limita a 10 primeiros para não ficar muito grande
                    responsaveis_limite = dict(list(dados_responsavel.items())[:10])
                    
                    categories = list(responsaveis_limite.keys())
                    values = list(responsaveis_limite.values())
                    
                    chart_height = max(300, len(categories) * 40)
                    
                    config = build_bar_chart_config(
                        categories=categories,
                        values=values,
                        series_name='Casos',
                        horizontal=True
                    )
                    config['series'][0]['itemStyle'] = {'color': PRIMARY_COLOR}
                    ui.echart(config).classes('w-full').style(f'height: {chart_height}px;')
                else:
                    create_empty_chart_state('Nenhum caso com responsável cadastrado.')



