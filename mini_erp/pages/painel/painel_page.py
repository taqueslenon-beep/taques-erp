"""
Página principal do Painel - Orquestrador.
Gerencia o layout, navegação entre abas e carregamento de dados.
"""
from nicegui import ui

from ...core import layout, get_cases_list, get_processes_list, get_clients_list, get_opposing_parties_list, PRIMARY_COLOR
from ...auth import is_authenticated

from .models import TAB_CONFIG, TAB_STYLES
from .data_service import create_data_service
from .tab_visualizations import (
    render_tab_totais,
    render_tab_comparativo,
    render_tab_categoria,
    render_tab_temporal,
    render_tab_status,
    render_tab_resultado,
    render_tab_cliente,
    render_tab_parte,
    render_tab_area,
    render_tab_area_ha,
    render_tab_estado,
    render_tab_heatmap,
    render_tab_probabilidade,
    render_tab_financeiro,
)


@ui.page('/')
def painel():
    """
    Rota inicial do sistema - redireciona para o Painel (Visão Geral do Escritório).
    
    ALTERAÇÃO: Anteriormente direcionava para 'Área do Cliente', agora redireciona
    para '/visao-geral/painel' que é o Painel do escritório.
    """
    # Redireciona diretamente para o Painel (Visão Geral do Escritório)
    ui.navigate.to('/visao-geral/painel')
    return


