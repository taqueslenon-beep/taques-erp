"""
Página de Estatísticas de Pessoas do workspace Visão Geral.
Exibe gráficos comparativos das pessoas cadastradas.
"""
from typing import Dict, List, Any
from collections import Counter
from nicegui import ui
from ....core import layout, PRIMARY_COLOR
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from .database import (
    listar_pessoas, contar_pessoas,
    listar_envolvidos, contar_envolvidos,
    listar_parceiros, contar_parceiros
)
from ...painel.chart_builders import build_bar_chart_config, build_pie_chart_config
from ...painel.ui_components import create_empty_chart_state


@ui.page('/visao-geral/pessoas/estatisticas')
def pessoas_estatisticas():
    """Página de Estatísticas de Pessoas do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace
    definir_workspace('visao_geral_escritorio')

    _renderizar_pagina_estatisticas()


def _renderizar_pagina_estatisticas():
    """Renderiza o conteúdo da página de estatísticas."""
    with layout('Estatísticas de Pessoas', breadcrumbs=[
        ('Visão geral do escritório', '/visao-geral/painel'),
        ('Pessoas', '/visao-geral/pessoas'),
        ('Estatísticas', None)
    ]):
        # =====================================================================
        # CARREGAR DADOS
        # =====================================================================
        try:
            # Contagem total por categoria
            total_clientes = contar_pessoas()
            total_envolvidos = contar_envolvidos()
            total_parceiros = contar_parceiros()
            total_geral = total_clientes + total_envolvidos + total_parceiros

            # Listas completas para análise
            todas_pessoas = listar_pessoas()
            todos_envolvidos = listar_envolvidos()
            todos_parceiros = listar_parceiros()
        except Exception as e:
            print(f"Erro ao carregar dados de pessoas: {e}")
            total_clientes = 0
            total_envolvidos = 0
            total_parceiros = 0
            total_geral = 0
            todas_pessoas = []
            todos_envolvidos = []
            todos_parceiros = []

        # =====================================================================
        # HEADER
        # =====================================================================
        with ui.column().classes('w-full mb-6'):
            ui.label('Estatísticas de Pessoas').classes('text-3xl font-bold text-gray-800')
            ui.label('Visão geral das pessoas cadastradas no sistema').classes('text-sm text-gray-500')

        # =====================================================================
        # CARDS DE RESUMO
        # =====================================================================
        with ui.row().classes('w-full gap-4 flex-wrap mb-8'):
            # Card Total Geral
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: {PRIMARY_COLOR}'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('people', size='24px').classes('text-gray-400')
                    ui.label('Total Geral').classes('text-sm text-gray-500')
                ui.label(str(total_geral)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR}')
                ui.label('Soma de todas as categorias').classes('text-xs text-gray-400 mt-1')

            # Card Clientes
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: #3b82f6'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('person', size='24px').classes('text-blue-400')
                    ui.label('Clientes').classes('text-sm text-gray-500')
                ui.label(str(total_clientes)).classes('text-3xl font-bold text-blue-600')
                ui.label('Pessoas cadastradas como clientes').classes('text-xs text-gray-400 mt-1')

            # Card Outros Envolvidos
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: #8b5cf6'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('groups', size='24px').classes('text-purple-400')
                    ui.label('Outros Envolvidos').classes('text-sm text-gray-500')
                ui.label(str(total_envolvidos)).classes('text-3xl font-bold text-purple-600')
                ui.label('Outros envolvidos nos processos').classes('text-xs text-gray-400 mt-1')

            # Card Parceiros
            with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: #10b981'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('handshake', size='24px').classes('text-green-400')
                    ui.label('Parceiros').classes('text-sm text-gray-500')
                ui.label(str(total_parceiros)).classes('text-3xl font-bold text-green-600')
                ui.label('Parceiros do escritório').classes('text-xs text-gray-400 mt-1')

        # =====================================================================
        # GRÁFICOS (Grid 2x2)
        # =====================================================================
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # GRÁFICO 1: Distribuição por Categoria (Pizza/Donut)
            with ui.card().classes('flex-1 min-w-96 p-4'):
                ui.label('Distribuição por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')

                if total_geral > 0:
                    # Prepara dados para gráfico de pizza
                    pie_data = []
                    if total_clientes > 0:
                        pie_data.append({
                            'value': total_clientes,
                            'name': 'Clientes',
                            'itemStyle': {'color': '#3b82f6'}
                        })
                    if total_envolvidos > 0:
                        pie_data.append({
                            'value': total_envolvidos,
                            'name': 'Outros Envolvidos',
                            'itemStyle': {'color': '#8b5cf6'}
                        })
                    if total_parceiros > 0:
                        pie_data.append({
                            'value': total_parceiros,
                            'name': 'Parceiros',
                            'itemStyle': {'color': '#10b981'}
                        })

                    if pie_data:
                        config = build_pie_chart_config(
                            data=pie_data,
                            series_name='Pessoas',
                            donut=True,
                            show_percentage=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhuma pessoa cadastrada.')
                else:
                    create_empty_chart_state('Nenhuma pessoa cadastrada.')

            # GRÁFICO 2: Clientes por Tipo (Barras Horizontal)
            with ui.card().classes('flex-1 min-w-96 p-4'):
                ui.label('Clientes por Tipo').classes('text-lg font-semibold text-gray-700 mb-4')

                if todas_pessoas:
                    # Agrupa por tipo_pessoa
                    contador_tipos = Counter()
                    for pessoa in todas_pessoas:
                        tipo = pessoa.get('tipo_pessoa', 'PF')
                        contador_tipos[tipo] += 1

                    if contador_tipos:
                        categories = ['PF', 'PJ']
                        values = [contador_tipos.get('PF', 0), contador_tipos.get('PJ', 0)]
                        colors = ['#3b82f6', '#f59e0b']  # Azul para PF, Amarelo para PJ

                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Clientes',
                            horizontal=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum cliente cadastrado.')
                else:
                    create_empty_chart_state('Nenhum cliente cadastrado.')

        with ui.row().classes('w-full gap-4 flex-wrap mt-4'):
            # GRÁFICO 3: Outros Envolvidos por Tipo (Barras Horizontal)
            with ui.card().classes('flex-1 min-w-96 p-4'):
                ui.label('Outros Envolvidos por Tipo').classes('text-lg font-semibold text-gray-700 mb-4')

                if todos_envolvidos:
                    # Agrupa por tipo_envolvido
                    contador_tipos = Counter()
                    for envolvido in todos_envolvidos:
                        tipo = envolvido.get('tipo_envolvido', 'PF')
                        contador_tipos[tipo] += 1

                    if contador_tipos:
                        # Ordem: PF, PJ, Ente Público
                        categories = ['PF', 'PJ', 'Ente Público']
                        values = [
                            contador_tipos.get('PF', 0),
                            contador_tipos.get('PJ', 0),
                            contador_tipos.get('Ente Público', 0)
                        ]
                        colors = ['#3b82f6', '#10b981', '#8b5cf6']  # Azul, Verde, Roxo

                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Envolvidos',
                            horizontal=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum envolvido cadastrado.')
                else:
                    create_empty_chart_state('Nenhum envolvido cadastrado.')

            # GRÁFICO 4: Parceiros por Tipo (Barras Horizontal)
            with ui.card().classes('flex-1 min-w-96 p-4'):
                ui.label('Parceiros por Tipo').classes('text-lg font-semibold text-gray-700 mb-4')

                if todos_parceiros:
                    # Agrupa por tipo_parceiro
                    contador_tipos = Counter()
                    for parceiro in todos_parceiros:
                        tipo = parceiro.get('tipo_parceiro', 'PF')
                        contador_tipos[tipo] += 1

                    if contador_tipos:
                        categories = ['PF', 'PJ']
                        values = [contador_tipos.get('PF', 0), contador_tipos.get('PJ', 0)]
                        colors = ['#3b82f6', '#10b981']  # Azul para PF, Verde para PJ

                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Parceiros',
                            horizontal=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum parceiro cadastrado.')
                else:
                    create_empty_chart_state('Nenhum parceiro cadastrado.')


