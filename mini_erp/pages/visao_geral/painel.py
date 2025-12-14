"""
Página principal do workspace "Visão geral do escritório".
Exibe o painel com visão consolidada de todos os casos e processos do escritório.
"""
from typing import Dict, List, Any
from collections import Counter
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from nicegui import ui, app
from mini_erp.core import layout, PRIMARY_COLOR
from mini_erp.auth import is_authenticated
from mini_erp.gerenciadores.gerenciador_workspace import definir_workspace
from mini_erp.models.prioridade import get_cor_por_prioridade
from .pessoas.database import (
    listar_pessoas, contar_pessoas,
    listar_envolvidos, contar_envolvidos,
    listar_parceiros, contar_parceiros
)
from .casos.database import contar_casos, listar_casos_por_status, listar_casos
from mini_erp.usuarios.database import listar_usuarios
from ..painel.chart_builders import build_bar_chart_config, build_pie_chart_config, build_line_chart_config, build_stacked_bar_chart_config
from ..painel.ui_components import create_empty_chart_state
from .casos.models import NUCLEO_CORES, STATUS_CORES, obter_cor_nucleo, obter_cor_status
from ...services.entregavel_service import listar_entregaveis as listar_entregaveis_service
from ..prazos.database import obter_estatisticas_prazos_mes
from ..novos_negocios.novos_negocios_services import get_oportunidades, obter_estatisticas_detalhadas


# =============================================================================
# FUNÇÕES DE AGRUPAMENTO PARA CASOS
# =============================================================================

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
    # Criar mapa de IDs para nomes (fallback caso responsaveis_dados não exista)
    usuarios_map = {}
    for usuario in usuarios:
        usuario_id = usuario.get('_id')
        nome = usuario.get('nome_completo') or usuario.get('nome') or usuario.get('display_name', 'Sem nome')
        if usuario_id:
            usuarios_map[usuario_id] = nome

    contador = Counter()
    for caso in casos:
        responsaveis_contados = False

        # PRIORIDADE 1: Usar responsaveis_dados (contém o nome diretamente)
        responsaveis_dados = caso.get('responsaveis_dados', [])
        if responsaveis_dados and isinstance(responsaveis_dados, list):
            for r in responsaveis_dados:
                if isinstance(r, dict):
                    nome = r.get('nome', '').strip()
                    if nome:
                        contador[nome] += 1
                        responsaveis_contados = True

        # PRIORIDADE 2: Fallback APENAS se não contou nenhum responsável acima
        if not responsaveis_contados:
            responsaveis = caso.get('responsaveis', [])
            if isinstance(responsaveis, list):
                for resp_id in responsaveis:
                    if resp_id in usuarios_map:
                        contador[usuarios_map[resp_id]] += 1
                    else:
                        contador[f'ID: {resp_id}'] += 1

    # Ordena do maior para o menor
    return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))


# =============================================================================
# FUNÇÕES DE AGRUPAMENTO PARA ENTREGÁVEIS
# =============================================================================

def agrupar_entregaveis_por_responsavel(entregaveis: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa entregáveis pendentes por responsável."""
    contador = Counter()
    for e in entregaveis:
        if e.get('status') != 'Concluído':
            responsavel = e.get('responsavel_nome', 'Sem responsável')
            contador[responsavel] += 1
    return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))


def agrupar_entregaveis_por_status(entregaveis: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa entregáveis por status."""
    contador = Counter()
    for e in entregaveis:
        status = e.get('status', 'Sem status')
        contador[status] += 1
    return dict(contador)


def agrupar_entregaveis_por_categoria(entregaveis: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa entregáveis pendentes por categoria."""
    contador = Counter()
    for e in entregaveis:
        if e.get('status') != 'Concluído':
            categoria = e.get('categoria', 'Sem categoria')
            contador[categoria] += 1
    return dict(contador)


def agrupar_entregaveis_por_prioridade(entregaveis: List[Dict[str, Any]]) -> Dict[str, int]:
    """Agrupa entregáveis pendentes por prioridade."""
    contador = Counter()
    for e in entregaveis:
        if e.get('status') != 'Concluído':
            prioridade = e.get('prioridade', 'P4')
            contador[prioridade] += 1
    return dict(contador)


def contar_entregaveis_concluidos_mes(entregaveis: List[Dict[str, Any]]) -> int:
    """Conta entregáveis concluídos no mês atual."""
    hoje = datetime.now()
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    concluidos_mes = 0
    for e in entregaveis:
        if e.get('status') == 'Concluído':
            atualizado = e.get('atualizado_em')
            if atualizado:
                try:
                    if hasattr(atualizado, 'timestamp'):
                        data_atualizacao = atualizado
                    elif isinstance(atualizado, (int, float)):
                        data_atualizacao = datetime.fromtimestamp(atualizado)
                    else:
                        continue

                    if data_atualizacao >= primeiro_dia_mes:
                        concluidos_mes += 1
                except:
                    pass

    return concluidos_mes


# =============================================================================
# PÁGINA PRINCIPAL DO PAINEL
# =============================================================================

@ui.page('/visao-geral/painel')
def painel():
    """Página principal do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace diretamente (sem middleware complexo)
    definir_workspace('visao_geral_escritorio')

    # Estado da visualização do painel
    visualizacao_painel = {'tipo': 'oportunidades'}  # 'oportunidades', 'casos', 'entregaveis', 'prazos', 'pessoas'

    # =========================================================================
    # CARREGAMENTO PARALELO DE DADOS - OTIMIZADO
    # =========================================================================
    _inicio_carregamento = time.time()
    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(obter_estatisticas_prazos_mes): 'stats_prazos',
                executor.submit(listar_casos): 'todos_casos',
                executor.submit(listar_usuarios): 'todos_usuarios',
                executor.submit(contar_pessoas): 'total_clientes',
                executor.submit(contar_envolvidos): 'total_envolvidos',
                executor.submit(contar_parceiros): 'total_parceiros',
                executor.submit(listar_pessoas): 'todas_pessoas',
                executor.submit(listar_envolvidos): 'todos_envolvidos',
                executor.submit(listar_parceiros): 'todos_parceiros',
                executor.submit(listar_entregaveis_service): 'todos_entregaveis',
                executor.submit(get_oportunidades): 'todas_oportunidades',
            }
            
            results = {}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    print(f"[PAINEL] Erro ao carregar {key}: {e}")
                    if key == 'stats_prazos':
                        results[key] = {'pendentes': 0, 'atrasados': 0, 'concluidos': 0, 'total_mes': 0, 'mes_nome': '', 'ano': 0}
                    elif key.startswith('total_'):
                        results[key] = 0
                    else:
                        results[key] = []
            
            # Extrair resultados
            stats_prazos = results.get('stats_prazos', {'pendentes': 0, 'atrasados': 0, 'concluidos': 0, 'total_mes': 0, 'mes_nome': '', 'ano': 0})
            todos_casos = results.get('todos_casos', [])
            todos_usuarios = results.get('todos_usuarios', [])
            total_clientes = results.get('total_clientes', 0)
            total_envolvidos = results.get('total_envolvidos', 0)
            total_parceiros = results.get('total_parceiros', 0)
            todas_pessoas = results.get('todas_pessoas', [])
            todos_envolvidos = results.get('todos_envolvidos', [])
            todos_parceiros = results.get('todos_parceiros', [])
            todos_entregaveis = results.get('todos_entregaveis', [])
            todas_oportunidades = results.get('todas_oportunidades', [])
            
            # Calcular estatísticas derivadas
            total_casos = len(todos_casos)
            casos_andamento = sum(1 for c in todos_casos if c.get('status') == 'Em andamento')
            casos_concluidos = sum(1 for c in todos_casos if c.get('status') == 'Concluído')
            total_pessoas = total_clientes + total_envolvidos + total_parceiros
            total_pf = sum(1 for p in todas_pessoas if p.get('tipo_pessoa') == 'PF')
            total_pj = sum(1 for p in todas_pessoas if p.get('tipo_pessoa') == 'PJ')
            entregaveis_pendentes = [e for e in todos_entregaveis if e.get('status') != 'Concluído']
            total_entregaveis_pendentes = len(entregaveis_pendentes)
            entregaveis_em_espera = sum(1 for e in entregaveis_pendentes if e.get('status') == 'Em espera')
            entregaveis_status_pendente = sum(1 for e in entregaveis_pendentes if e.get('status') == 'Pendente')
            entregaveis_em_andamento = sum(1 for e in entregaveis_pendentes if e.get('status') == 'Em andamento')
            
            # Calcular estatísticas de oportunidades ativas
            oportunidades_ativas = [op for op in todas_oportunidades if op.get('status') != 'concluido']
            total_oportunidades_ativas = len(oportunidades_ativas)
            oportunidades_agir = sum(1 for op in oportunidades_ativas if op.get('status') == 'agir')
            oportunidades_em_andamento = sum(1 for op in oportunidades_ativas if op.get('status') == 'em_andamento')
            oportunidades_aguardando = sum(1 for op in oportunidades_ativas if op.get('status') == 'aguardando')
            oportunidades_monitorando = sum(1 for op in oportunidades_ativas if op.get('status') == 'monitorando')
            
            tempo_carregamento = time.time() - _inicio_carregamento
            print(f"[PAINEL] ✅ Dados carregados em paralelo com sucesso. Tempo: {tempo_carregamento:.2f}s")

    except Exception as e:
        print(f"[PAINEL] ❌ Erro no carregamento paralelo: {e}")
        import traceback
        traceback.print_exc()
        # Fallback com valores padrão
        stats_prazos = {'pendentes': 0, 'atrasados': 0, 'concluidos': 0, 'total_mes': 0, 'mes_nome': '', 'ano': 0}
        todos_casos = []
        total_casos = 0
        casos_andamento = 0
        casos_concluidos = 0
        todos_usuarios = []
        total_clientes = 0
        total_envolvidos = 0
        total_parceiros = 0
        total_pessoas = 0
        total_pf = 0
        total_pj = 0
        todas_pessoas = []
        todos_envolvidos = []
        todos_parceiros = []
        todos_entregaveis = []
        total_entregaveis_pendentes = 0
        entregaveis_em_espera = 0
        entregaveis_status_pendente = 0
        entregaveis_em_andamento = 0
        todas_oportunidades = []
        total_oportunidades_ativas = 0
        oportunidades_agir = 0
        oportunidades_em_andamento = 0
        oportunidades_aguardando = 0
        oportunidades_monitorando = 0

    # =========================================================================
    # FUNÇÕES DE ALTERNÂNCIA DE VISUALIZAÇÃO
    # =========================================================================
    def selecionar_casos():
        visualizacao_painel['tipo'] = 'casos'
        area_cards.refresh()
        area_estatisticas.refresh()

    def selecionar_entregaveis():
        visualizacao_painel['tipo'] = 'entregaveis'
        area_cards.refresh()
        area_estatisticas.refresh()

    def selecionar_prazos():
        visualizacao_painel['tipo'] = 'prazos'
        area_cards.refresh()
        area_estatisticas.refresh()

    def selecionar_pessoas():
        visualizacao_painel['tipo'] = 'pessoas'
        area_cards.refresh()
        area_estatisticas.refresh()
    
    def selecionar_oportunidades():
        visualizacao_painel['tipo'] = 'oportunidades'
        area_cards.refresh()
        area_estatisticas.refresh()

    # =========================================================================
    # LAYOUT DA PÁGINA
    # =========================================================================
    with layout('Painel', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Painel', None)]):

        # =====================================================================
        # ÁREA DE CARDS DE RESUMO (refreshable para atualizar destaque)
        # =====================================================================
        @ui.refreshable
        def area_cards():
            with ui.row().classes('w-full gap-4 flex-nowrap overflow-x-auto mb-6'):
                # Card Oportunidades Ativas (clicável - alterna visualização)
                card_oportunidades_ativo = visualizacao_painel['tipo'] == 'oportunidades'
                classes_oportunidades = 'flex-1 min-w-0 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-all'
                if card_oportunidades_ativo:
                    classes_oportunidades += ' ring-2 ring-offset-2 shadow-lg'
                
                with ui.card().classes(classes_oportunidades).style(f'border-left-color: #10B981; {"ring-color: #10B981;" if card_oportunidades_ativo else ""}') as oportunidades_card:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('trending_up', size='24px').style('color: #10B981;')
                        ui.label('Oportunidades Ativas').classes('text-sm text-gray-500')
                    ui.label(str(total_oportunidades_ativas)).classes('text-3xl font-bold').style('color: #10B981;')
                    
                    # Breakdown por coluna (exceto "Concluído")
                    breakdown_parts = []
                    if oportunidades_agir > 0:
                        breakdown_parts.append(f'{oportunidades_agir} agir')
                    if oportunidades_em_andamento > 0:
                        breakdown_parts.append(f'{oportunidades_em_andamento} em andamento')
                    if oportunidades_aguardando > 0:
                        breakdown_parts.append(f'{oportunidades_aguardando} aguardando')
                    if oportunidades_monitorando > 0:
                        breakdown_parts.append(f'{oportunidades_monitorando} monitorando')
                    
                    if breakdown_parts:
                        ui.label(', '.join(breakdown_parts)).classes('text-xs text-gray-400 mt-1')
                    else:
                        ui.label('Nenhuma oportunidade ativa').classes('text-xs text-gray-400 mt-1')
                    
                    oportunidades_card.on('click', selecionar_oportunidades)
                
                # Card Casos (clicável - alterna visualização)
                card_casos_ativo = visualizacao_painel['tipo'] == 'casos'
                classes_casos = 'flex-1 min-w-0 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-all'
                if card_casos_ativo:
                    classes_casos += ' ring-2 ring-offset-2 shadow-lg'

                with ui.card().classes(classes_casos).style(f'border-left-color: {PRIMARY_COLOR}; {"ring-color: " + PRIMARY_COLOR + ";" if card_casos_ativo else ""}') as casos_card:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('folder', size='24px').classes('text-gray-400' if not card_casos_ativo else '').style(f'color: {PRIMARY_COLOR}' if card_casos_ativo else '')
                        ui.label('Casos').classes('text-sm text-gray-500')
                    ui.label(str(total_casos)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR}')
                    subtitulo = f'{casos_andamento} em andamento'
                    if casos_concluidos > 0:
                        subtitulo += f', {casos_concluidos} concluídos'
                    ui.label(subtitulo).classes('text-xs text-gray-400 mt-1')

                    casos_card.on('click', selecionar_casos)

                # Card Pessoas Cadastradas (clicável - alterna visualização)
                card_pessoas_ativo = visualizacao_painel['tipo'] == 'pessoas'
                classes_pessoas = 'flex-1 min-w-0 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-all'
                if card_pessoas_ativo:
                    classes_pessoas += ' ring-2 ring-offset-2 shadow-lg'

                with ui.card().classes(classes_pessoas).style(f'border-left-color: {PRIMARY_COLOR}; {"ring-color: " + PRIMARY_COLOR + ";" if card_pessoas_ativo else ""}') as pessoas_card:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('people', size='24px').classes('text-gray-400' if not card_pessoas_ativo else '').style(f'color: {PRIMARY_COLOR}' if card_pessoas_ativo else '')
                        ui.label('Pessoas Cadastradas').classes('text-sm text-gray-500')
                    ui.label(str(total_pessoas)).classes('text-3xl font-bold').style(f'color: {PRIMARY_COLOR}')
                    # Subtítulo mostra distribuição: clientes, envolvidos, parceiros
                    subtitulo_partes = []
                    if total_clientes > 0:
                        subtitulo_partes.append(f'{total_clientes} cliente{"s" if total_clientes != 1 else ""}')
                    if total_envolvidos > 0:
                        subtitulo_partes.append(f'{total_envolvidos} envolvido{"s" if total_envolvidos != 1 else ""}')
                    if total_parceiros > 0:
                        subtitulo_partes.append(f'{total_parceiros} parceiro{"s" if total_parceiros != 1 else ""}')
                    
                    if subtitulo_partes:
                        ui.label(', '.join(subtitulo_partes)).classes('text-xs text-gray-400 mt-1')
                    else:
                        ui.label('Nenhuma pessoa cadastrada').classes('text-xs text-gray-400 mt-1')

                    pessoas_card.on('click', selecionar_pessoas)

                # Card Processos Ativos (placeholder)
                with ui.card().classes('flex-1 min-w-0 p-4 border-l-4 border-gray-300'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('gavel', size='24px').classes('text-gray-300')
                        ui.label('Processos Ativos').classes('text-sm text-gray-500')
                    ui.label('-').classes('text-3xl font-bold text-gray-300')
                    ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')

                # Card Entregáveis Pendentes (clicável - alterna visualização)
                card_entregaveis_ativo = visualizacao_painel['tipo'] == 'entregaveis'
                classes_entregaveis = 'flex-1 min-w-0 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-all'
                if card_entregaveis_ativo:
                    classes_entregaveis += ' ring-2 ring-orange-500 ring-offset-2 shadow-lg'

                with ui.card().classes(classes_entregaveis).style('border-left-color: #F97316') as entregaveis_card:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('assignment_late', size='24px').classes('text-orange-400')
                        ui.label('Entregáveis Pendentes').classes('text-sm text-gray-500')
                    ui.label(str(total_entregaveis_pendentes)).classes('text-3xl font-bold text-orange-600')

                    # Breakdown por status
                    if total_entregaveis_pendentes > 0:
                        breakdown_parts = []
                        if entregaveis_em_espera > 0:
                            breakdown_parts.append(f'{entregaveis_em_espera} em espera')
                        if entregaveis_status_pendente > 0:
                            breakdown_parts.append(f'{entregaveis_status_pendente} pendentes')
                        if entregaveis_em_andamento > 0:
                            breakdown_parts.append(f'{entregaveis_em_andamento} em andamento')
                        subtitulo_entregaveis = ', '.join(breakdown_parts) if breakdown_parts else 'Nenhum pendente'
                    else:
                        subtitulo_entregaveis = 'Todos concluídos'
                    ui.label(subtitulo_entregaveis).classes('text-xs text-gray-400 mt-1')

                    entregaveis_card.on('click', selecionar_entregaveis)

                # Card Prazos do Mês (clicável - alterna visualização)
                card_prazos_ativo = visualizacao_painel['tipo'] == 'prazos'
                classes_prazos = 'flex-1 min-w-0 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-all'
                if card_prazos_ativo:
                    classes_prazos += ' ring-2 ring-amber-500 ring-offset-2 shadow-lg'

                with ui.card().classes(classes_prazos).style('border-left-color: #F59E0B') as prazos_card:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('calendar_month', size='24px').classes('text-amber-500')
                        ui.label('Prazos do Mês').classes('text-sm text-gray-500')

                    # Número principal: pendentes + atrasados (não concluídos)
                    total_pendentes_atrasados = stats_prazos['pendentes'] + stats_prazos['atrasados']
                    ui.label(str(total_pendentes_atrasados)).classes('text-3xl font-bold text-amber-600')

                    # Breakdown
                    if stats_prazos['total_mes'] > 0:
                        breakdown_prazos = []
                        if stats_prazos['atrasados'] > 0:
                            breakdown_prazos.append(f'{stats_prazos["atrasados"]} atrasados')
                        if stats_prazos['pendentes'] > 0:
                            breakdown_prazos.append(f'{stats_prazos["pendentes"]} pendentes')
                        if stats_prazos['concluidos'] > 0:
                            breakdown_prazos.append(f'{stats_prazos["concluidos"]} concluídos')
                        subtitulo_prazos = ', '.join(breakdown_prazos) if breakdown_prazos else 'Nenhum prazo'
                    else:
                        subtitulo_prazos = f'Nenhum prazo em {stats_prazos["mes_nome"]}'
                    ui.label(subtitulo_prazos).classes('text-xs text-gray-400 mt-1')

                    prazos_card.on('click', selecionar_prazos)

                # Card Acordos (placeholder)
                with ui.card().classes('flex-1 min-w-0 p-4 border-l-4 border-gray-300'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('handshake', size='24px').classes('text-gray-300')
                        ui.label('Acordos').classes('text-sm text-gray-500')
                    ui.label('-').classes('text-3xl font-bold text-gray-300')
                    ui.label('Funcionalidade em desenvolvimento').classes('text-xs text-gray-400 mt-1')

        area_cards()

        # =====================================================================
        # ÁREA DE ESTATÍSTICAS (refreshable para alternar entre todas as opções)
        # =====================================================================
        def renderizar_estatisticas_oportunidades():
            """Renderiza estatísticas de Oportunidades Ativas."""
            stats = obter_estatisticas_detalhadas()
            
            ui.label('Estatísticas de Oportunidades').classes('text-2xl font-bold text-gray-800 mt-8 mb-4')
            
            # Cores dos status do Kanban
            STATUS_CORES_OP = {
                'agir': '#EF4444',
                'em_andamento': '#EAB308',
                'aguardando': '#FDE047',
                'monitorando': '#F97316',
            }
            STATUS_NOMES_OP = {
                'agir': 'Agir',
                'em_andamento': 'Em Andamento',
                'aguardando': 'Aguardando',
                'monitorando': 'Monitorando',
            }
            
            # Grid de gráficos (responsivo) - Primeira linha
            with ui.row().classes('w-full gap-6 flex-wrap mb-6'):
                # 1. Gráfico de Oportunidades por Status (Pizza)
                with ui.card().classes('flex-1 min-w-96 p-6'):
                    ui.label('Oportunidades por Status').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                    if stats['total'] > 0:
                        pie_data = []
                        for status in ['agir', 'em_andamento', 'aguardando', 'monitorando']:
                            quantidade = stats['por_status'].get(status, 0)
                            if quantidade > 0:
                                pie_data.append({
                                    'value': quantidade,
                                    'name': STATUS_NOMES_OP[status],
                                    'itemStyle': {'color': STATUS_CORES_OP[status]}
                                })
                        
                        if pie_data:
                            config = build_pie_chart_config(
                                data=pie_data,
                                series_name='Oportunidades',
                                donut=True,
                                show_percentage=True
                            )
                            ui.echart(config).classes('w-full h-80')
                        else:
                            create_empty_chart_state('Nenhuma oportunidade ativa.')
                    else:
                        create_empty_chart_state('Nenhuma oportunidade ativa.')
                
                # 2. Gráfico de Oportunidades por Núcleo
                with ui.card().classes('flex-1 min-w-96 p-6'):
                    ui.label('Oportunidades por Núcleo').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                    if stats['por_nucleo']:
                        nucleos_ordenados = sorted(
                            stats['por_nucleo'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                        categories = [nucleo for nucleo, _ in nucleos_ordenados]
                        values = [qtd for _, qtd in nucleos_ordenados]
                        colors = [obter_cor_nucleo(nucleo) for nucleo in categories]
                        
                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Oportunidades',
                            horizontal=True,
                            show_percentage=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhuma oportunidade por núcleo.')
                
                # 3. Gráfico de Oportunidades por Origem
                with ui.card().classes('flex-1 min-w-96 p-6'):
                    ui.label('Oportunidades por Origem').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                    if stats['por_origem']:
                        origens_ordenadas = sorted(
                            stats['por_origem'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                        categories = [origem for origem, _ in origens_ordenadas]
                        values = [qtd for _, qtd in origens_ordenadas]
                        
                        # Cores alternadas para origem
                        cores_origem = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
                        colors = [cores_origem[i % len(cores_origem)] for i in range(len(categories))]
                        
                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Oportunidades',
                            horizontal=True,
                            show_percentage=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhuma oportunidade por origem.')
            
            # Segunda linha de gráficos
            with ui.row().classes('w-full gap-6 flex-wrap'):
                # 4. Gráfico de Evolução Mensal (Barras Horizontais Simples)
                with ui.card().classes('flex-1 min-w-96 p-6'):
                    ui.label('Evolução Mensal').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                    por_mes = stats.get('por_mes', {})
                    if por_mes:
                        # Ordena meses por data (mais antigo primeiro)
                        meses_ordenados = sorted(por_mes.items(), key=lambda x: (
                            int(x[0].split('/')[1]),  # Ano primeiro
                            int(x[0].split('/')[0])   # Mês depois
                        ))
                        
                        # Limita aos últimos 6 meses
                        if len(meses_ordenados) > 6:
                            meses_ordenados = meses_ordenados[-6:]
                        
                        # Formata meses para exibição (MM/AAAA -> "Jan/24")
                        meses_labels = []
                        valores = []
                        meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                       'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                        
                        for mes_ano, quantidade in meses_ordenados:
                            try:
                                mes, ano = mes_ano.split('/')
                                mes_int = int(mes)
                                if 1 <= mes_int <= 12:
                                    mes_nome = meses_nomes[mes_int - 1]
                                    meses_labels.append(f'{mes_nome}/{ano[-2:]}')
                                    valores.append(quantidade)
                            except:
                                # Se formato inválido, pula
                                continue
                        
                        if meses_labels and valores:
                            # Barras horizontais simples (uma cor azul)
                            config = build_bar_chart_config(
                                categories=meses_labels,
                                values=valores,
                                colors=['#3B82F6'],  # Cor azul única
                                series_name='Oportunidades',
                                horizontal=True,
                                show_percentage=True
                            )
                            ui.echart(config).classes('w-full h-80')
                        else:
                            create_empty_chart_state('Formato de datas inválido.')
                    else:
                        create_empty_chart_state('Nenhum dado mensal disponível.')
                
                # 5. Gráfico de Oportunidades por Responsável
                with ui.card().classes('flex-1 min-w-96 p-6'):
                    ui.label('Oportunidades por Responsável').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                    por_responsavel = stats.get('por_responsavel', {})
                    if por_responsavel:
                        # Ordena por quantidade (maior primeiro)
                        responsaveis_ordenados = sorted(
                            por_responsavel.items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                        
                        # Limita aos 10 primeiros para não ficar muito grande
                        responsaveis_limite = responsaveis_ordenados[:10]
                        
                        categories = [resp for resp, _ in responsaveis_limite]
                        values = [qtd for _, qtd in responsaveis_limite]
                        
                        # Cores alternadas
                        cores_responsavel = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
                        colors = [cores_responsavel[i % len(cores_responsavel)] for i in range(len(categories))]
                        
                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Oportunidades',
                            horizontal=True,
                            show_percentage=True
                        )
                        
                        # Ajusta altura do gráfico baseado no número de responsáveis
                        chart_height = max(300, len(categories) * 40)
                        ui.echart(config).classes('w-full').style(f'height: {chart_height}px;')
                    else:
                        create_empty_chart_state('Nenhuma oportunidade com responsável.')
                
                # 6. Gráfico de Valor por Etapa
                with ui.card().classes('flex-1 min-w-96 p-6'):
                    valores_por_status = stats.get('valores_por_status', {})
                    total_pipeline = sum(valores_por_status.values())
                    
                    # Título com total do pipeline
                    if total_pipeline > 0:
                        # Formata total do pipeline
                        total_formatado = f"R$ {total_pipeline:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.') if total_pipeline >= 1000 else f"R$ {total_pipeline:.0f}"
                        ui.label(f'Valor por Etapa (Total: {total_formatado})').classes('text-lg font-semibold text-gray-700 mb-4')
                    else:
                        ui.label('Valor por Etapa').classes('text-lg font-semibold text-gray-700 mb-4')
                    
                    if valores_por_status and total_pipeline > 0:
                        # Ordem das etapas (mesma ordem do Kanban)
                        etapas = [
                            ('agir', 'Agir', '#EF4444'),
                            ('em_andamento', 'Em Andamento', '#EAB308'),
                            ('aguardando', 'Aguardando', '#FDE047'),
                            ('monitorando', 'Monitorando', '#F97316')
                        ]
                        
                        categories = []
                        values = []
                        colors = []
                        
                        for status_id, nome, cor in etapas:
                            valor = valores_por_status.get(status_id, 0.0)
                            if valor > 0:
                                categories.append(nome)
                                values.append(valor)
                                colors.append(cor)
                        
                        if categories and values:
                            # Formata valores monetários para exibição
                            def formatar_reais(valor: float) -> str:
                                """Formata valor para moeda brasileira."""
                                if valor >= 1000:
                                    return f"R$ {valor:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                return f"R$ {valor:.0f}"
                            
                            # Prepara dados simples sem formatação complexa nos labels individuais
                            formatted_data = []
                            for valor, cor in zip(values, colors):
                                formatted_data.append({
                                    'value': valor,
                                    'itemStyle': {'color': cor}
                                })
                            
                            # Configuração customizada para valores monetários
                            config = {
                                'tooltip': {
                                    'trigger': 'axis',
                                    'axisPointer': {'type': 'shadow'}
                                },
                                'grid': {
                                    'left': '3%',
                                    'right': '15%',  # Mais espaço para labels monetários
                                    'bottom': '3%',
                                    'top': '3%',
                                    'containLabel': True
                                },
                                'xAxis': {
                                    'type': 'value'
                                    # Sem formatter customizado - valores numéricos simples
                                },
                                'yAxis': {
                                    'type': 'category',
                                    'data': list(reversed(categories)),
                                    'axisLabel': {'fontSize': 11}
                                },
                                'series': [{
                                    'name': 'Valor',
                                    'type': 'bar',
                                    'data': list(reversed(formatted_data)),
                                    'barWidth': '60%',
                                    'label': {
                                        'show': True,
                                        'position': 'right',
                                        'fontWeight': 'bold',
                                        'fontSize': 12,
                                        'formatter': 'R$ {c}'  # Template simples: R$ + valor numérico
                                    }
                                }]
                            }
                            
                            ui.echart(config).classes('w-full h-80')
                        else:
                            create_empty_chart_state('Nenhum valor encontrado.')
                    else:
                        create_empty_chart_state('Nenhum valor no pipeline.')
            
        @ui.refreshable
        def area_estatisticas():
            if visualizacao_painel['tipo'] == 'oportunidades':
                renderizar_estatisticas_oportunidades()
            elif visualizacao_painel['tipo'] == 'casos':
                renderizar_estatisticas_casos()
            elif visualizacao_painel['tipo'] == 'entregaveis':
                renderizar_estatisticas_entregaveis()
            elif visualizacao_painel['tipo'] == 'pessoas':
                renderizar_estatisticas_pessoas()
            else:
                renderizar_estatisticas_prazos()

        def renderizar_estatisticas_casos():
            """Renderiza estatísticas de Casos."""
            ui.label('Estatísticas de Casos').classes('text-2xl font-bold text-gray-800 mt-8 mb-4')

            # Grid de gráficos (responsivo)
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # 1. Gráfico de Casos por Núcleo
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Casos por Núcleo').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_nucleo = agrupar_casos_por_nucleo(todos_casos)
                    if dados_nucleo:
                        nucleos_ordenados = sorted(dados_nucleo.items(), key=lambda x: x[1], reverse=True)
                        categories = [nucleo for nucleo, _ in nucleos_ordenados]
                        values = [count for _, count in nucleos_ordenados]
                        colors = [obter_cor_nucleo(nucleo) for nucleo in categories]

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

                # 2. Gráfico de Casos por Status
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Casos por Status').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_status = agrupar_casos_por_status(todos_casos)
                    if dados_status:
                        status_ordem = ['Em andamento', 'Concluído', 'Concluído com pendências', 'Em monitoramento', 'Substabelecido']
                        status_ordenados = [s for s in status_ordem if s in dados_status]
                        status_ordenados.extend([s for s in dados_status.keys() if s not in status_ordem])

                        categories = status_ordenados
                        values = [dados_status[s] for s in categories]
                        colors = [obter_cor_status(s).get('bg', '#9E9E9E') for s in categories]

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

                # 3. Gráfico de Casos por Categoria
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Casos por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_categoria = agrupar_casos_por_categoria(todos_casos)
                    if dados_categoria:
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
                # 4. Gráfico de Casos por Prioridade
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Casos por Prioridade').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_prioridade = agrupar_casos_por_prioridade(todos_casos)
                    if dados_prioridade:
                        prioridades_ordem = ['P1', 'P2', 'P3', 'P4']
                        prioridades_ordenadas = [p for p in prioridades_ordem if p in dados_prioridade]

                        categories = prioridades_ordenadas
                        values = [dados_prioridade.get(p, 0) for p in categories]
                        colors = [get_cor_por_prioridade(p) for p in categories]

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

                # 5. Gráfico de Casos por Responsável
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Casos por Responsável').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_responsavel = agrupar_casos_por_responsavel(todos_casos, todos_usuarios)
                    if dados_responsavel:
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

        def renderizar_estatisticas_entregaveis():
            """Renderiza estatísticas de Entregáveis."""
            ui.label('Estatísticas de Entregáveis').classes('text-2xl font-bold text-gray-800 mt-8 mb-4')

            # Cores para status de entregáveis
            cores_status_entregaveis = {
                'Em espera': '#F97316',
                'Pendente': '#EF4444',
                'Em andamento': '#EAB308',
                'Concluído': '#22C55E',
            }

            # Cores para prioridades
            cores_prioridade = {
                'P1': '#DC2626',
                'P2': '#F59E0B',
                'P3': '#3B82F6',
                'P4': '#6B7280',
            }

            # Grid de gráficos
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # 1. Gráfico de Entregáveis por Responsável
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Entregáveis por Responsável').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_responsavel = agrupar_entregaveis_por_responsavel(todos_entregaveis)
                    if dados_responsavel:
                        responsaveis_limite = dict(list(dados_responsavel.items())[:10])
                        categories = list(responsaveis_limite.keys())
                        values = list(responsaveis_limite.values())

                        # Cores alternadas
                        cores_alternadas = ['#F97316', '#3B82F6', '#10B981', '#8B5CF6', '#EC4899', '#06B6D4']
                        colors = [cores_alternadas[i % len(cores_alternadas)] for i in range(len(categories))]

                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Entregáveis',
                            horizontal=True
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum entregável pendente.')

                # 2. Gráfico de Entregáveis por Status (Pizza)
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Entregáveis por Status').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_status = agrupar_entregaveis_por_status(todos_entregaveis)
                    if dados_status:
                        pie_data = [
                            {
                                'value': count,
                                'name': status,
                                'itemStyle': {'color': cores_status_entregaveis.get(status, '#6B7280')}
                            }
                            for status, count in dados_status.items()
                        ]
                        config = build_pie_chart_config(data=pie_data, series_name='Entregáveis', donut=True)
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum entregável cadastrado.')

                # 3. Gráfico de Entregáveis por Categoria
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Entregáveis por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_categoria = agrupar_entregaveis_por_categoria(todos_entregaveis)
                    if dados_categoria:
                        categories = list(dados_categoria.keys())
                        values = list(dados_categoria.values())

                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            series_name='Entregáveis',
                            horizontal=True
                        )
                        config['series'][0]['itemStyle'] = {'color': '#3B82F6'}
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum entregável pendente.')

            # Segunda linha de gráficos
            with ui.row().classes('w-full gap-4 flex-wrap mt-4'):
                # 4. Gráfico de Entregáveis por Prioridade
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Entregáveis por Prioridade').classes('text-lg font-semibold text-gray-700 mb-4')

                    dados_prioridade = agrupar_entregaveis_por_prioridade(todos_entregaveis)
                    if dados_prioridade:
                        # Ordena P1, P2, P3, P4
                        prioridades_ordem = ['P1', 'P2', 'P3', 'P4']
                        prioridades_ordenadas = [p for p in prioridades_ordem if p in dados_prioridade]

                        categories = prioridades_ordenadas
                        values = [dados_prioridade.get(p, 0) for p in categories]
                        colors = [cores_prioridade.get(p, '#6B7280') for p in categories]

                        config = build_bar_chart_config(
                            categories=categories,
                            values=values,
                            colors=colors,
                            series_name='Entregáveis',
                            horizontal=False
                        )
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state('Nenhum entregável pendente.')

                # 5. Card de Entregáveis Concluídos no Mês
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Concluídos no Mês').classes('text-lg font-semibold text-gray-700 mb-4')

                    concluidos_mes = contar_entregaveis_concluidos_mes(todos_entregaveis)
                    mes_atual = datetime.now().strftime('%B/%Y')

                    with ui.column().classes('w-full items-center justify-center py-8'):
                        ui.icon('task_alt', size='64px').classes('text-green-400 mb-4')
                        ui.label(str(concluidos_mes)).classes('text-6xl font-bold text-green-600')
                        ui.label(f'concluídos em {mes_atual}').classes('text-gray-500 mt-2')

        def renderizar_estatisticas_prazos():
            """Renderiza estatísticas de Prazos."""
            ui.label('Estatísticas de Prazos').classes('text-2xl font-bold text-gray-800 mt-8 mb-4')

            # Cores para status de prazos
            cores_prazos = {
                'Atrasados': '#EF5350',    # Vermelho
                'Pendentes': '#FFC107',    # Amarelo
                'Concluídos': '#4CAF50',   # Verde
            }

            # Grid de estatísticas
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # 1. Cards de resumo de prazos
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label(f'Prazos de {stats_prazos["mes_nome"]} {stats_prazos["ano"]}').classes('text-lg font-semibold text-gray-700 mb-4')

                    with ui.row().classes('w-full gap-4 flex-wrap'):
                        # Card Atrasados
                        with ui.card().classes('flex-1 min-w-32 p-4').style('background-color: #FFEBEE; border-left: 4px solid #EF5350;'):
                            ui.label('Atrasados').classes('text-sm text-gray-600')
                            ui.label(str(stats_prazos['atrasados'])).classes('text-4xl font-bold').style('color: #EF5350;')

                        # Card Pendentes
                        with ui.card().classes('flex-1 min-w-32 p-4').style('background-color: #FFF8E1; border-left: 4px solid #FFC107;'):
                            ui.label('Pendentes').classes('text-sm text-gray-600')
                            ui.label(str(stats_prazos['pendentes'])).classes('text-4xl font-bold').style('color: #FFA000;')

                        # Card Concluídos
                        with ui.card().classes('flex-1 min-w-32 p-4').style('background-color: #E8F5E9; border-left: 4px solid #4CAF50;'):
                            ui.label('Concluídos').classes('text-sm text-gray-600')
                            ui.label(str(stats_prazos['concluidos'])).classes('text-4xl font-bold').style('color: #4CAF50;')

                    # Total do mês
                    with ui.row().classes('w-full mt-4 items-center justify-center'):
                        ui.label(f'Total de prazos no mês: {stats_prazos["total_mes"]}').classes('text-gray-500')

                # 2. Gráfico de Pizza - Distribuição de Prazos
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Distribuição de Prazos').classes('text-lg font-semibold text-gray-700 mb-4')

                    # Montar dados para o gráfico de pizza
                    dados_grafico = []
                    if stats_prazos['atrasados'] > 0:
                        dados_grafico.append({
                            'value': stats_prazos['atrasados'],
                            'name': 'Atrasados',
                            'itemStyle': {'color': cores_prazos['Atrasados']}
                        })
                    if stats_prazos['pendentes'] > 0:
                        dados_grafico.append({
                            'value': stats_prazos['pendentes'],
                            'name': 'Pendentes',
                            'itemStyle': {'color': cores_prazos['Pendentes']}
                        })
                    if stats_prazos['concluidos'] > 0:
                        dados_grafico.append({
                            'value': stats_prazos['concluidos'],
                            'name': 'Concluídos',
                            'itemStyle': {'color': cores_prazos['Concluídos']}
                        })

                    if dados_grafico:
                        config = build_pie_chart_config(data=dados_grafico, series_name='Prazos', donut=True)
                        ui.echart(config).classes('w-full h-80')
                    else:
                        create_empty_chart_state(f'Nenhum prazo em {stats_prazos["mes_nome"]}')

                # 3. Card com link para página de Prazos
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Ações Rápidas').classes('text-lg font-semibold text-gray-700 mb-4')

                    with ui.column().classes('w-full items-center justify-center py-4 gap-4'):
                        ui.icon('calendar_month', size='64px').classes('text-amber-400 mb-2')

                        # Total não concluídos
                        total_nao_concluidos = stats_prazos['pendentes'] + stats_prazos['atrasados']
                        if total_nao_concluidos > 0:
                            ui.label(f'{total_nao_concluidos} prazos precisam de atenção').classes('text-gray-600')
                        else:
                            ui.label('Todos os prazos em dia!').classes('text-green-600 font-semibold')

                        ui.button(
                            'Ver todos os prazos',
                            icon='arrow_forward',
                            on_click=lambda: ui.navigate.to('/prazos')
                        ).classes('bg-amber-500 text-white')

        def renderizar_estatisticas_pessoas():
            """Renderiza estatísticas de Pessoas."""
            ui.label('Estatísticas de Pessoas').classes('text-2xl font-bold text-gray-800 mt-8 mb-4')

            # Grid de gráficos (responsivo)
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # 1. Gráfico de Distribuição por Categoria (Pizza/Donut)
                with ui.card().classes('flex-1 min-w-80 p-4'):
                    ui.label('Distribuição por Categoria').classes('text-lg font-semibold text-gray-700 mb-4')

                    if total_pessoas > 0:
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

                # 2. Gráfico de Clientes por Tipo (Barras Horizontal)
                with ui.card().classes('flex-1 min-w-80 p-4'):
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

            # Segunda linha de gráficos
            with ui.row().classes('w-full gap-4 flex-wrap mt-4'):
                # 3. Gráfico de Outros Envolvidos por Tipo (Barras Horizontal)
                with ui.card().classes('flex-1 min-w-80 p-4'):
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

                # 4. Gráfico de Parceiros por Tipo (Barras Horizontal)
                with ui.card().classes('flex-1 min-w-80 p-4'):
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

        area_estatisticas()

