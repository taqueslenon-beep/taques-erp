"""
tabela_prazos_flet.py - Tabela de prazos em Flet com abas e filtros.
"""

import flet as ft
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Callable
from .database import (
    listar_prazos,
    listar_prazos_por_status,
    excluir_prazo,
    atualizar_prazo,
    criar_proximo_prazo_recorrente,
    calcular_proximo_prazo_fatal,
    invalidar_cache_prazos,
)
from .ui_components import (
    formatar_data_prazo,
    calcular_prazo_seguranca,
    verificar_prazo_atrasado,
    formatar_lista_nomes,
    formatar_titulo_prazo,
    obter_semana_passada,
    obter_esta_semana,
    obter_proxima_semana,
    formatar_periodo_semana,
    filtrar_prazos_por_semana,
    criar_mensagem_vazia,
)
from .models import STATUS_LABELS


def criar_tabela_prazos_data(prazos_lista: List[Dict[str, Any]], usuarios_opcoes: Dict[str, str],
                              clientes_opcoes: Dict[str, str]) -> List[ft.DataRow]:
    """
    Cria linhas de DataTable a partir da lista de prazos.
    
    Args:
        prazos_lista: Lista de prazos
        usuarios_opcoes: Opções de usuários
        clientes_opcoes: Opções de clientes
    
    Returns:
        Lista de DataRow
    """
    rows = []
    
    for prazo in prazos_lista:
        prazo_id = prazo.get('_id')
        titulo = formatar_titulo_prazo(prazo)
        responsaveis_ids = prazo.get('responsaveis', [])
        responsaveis_texto = formatar_lista_nomes(responsaveis_ids, usuarios_opcoes)
        clientes_ids = prazo.get('clientes', [])
        clientes_texto = formatar_lista_nomes(clientes_ids, clientes_opcoes)
        prazo_fatal_ts = prazo.get('prazo_fatal')
        prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
        prazo_seguranca_texto = calcular_prazo_seguranca(prazo_fatal_ts)
        status = prazo.get('status', 'pendente')
        esta_concluido = status.lower() == 'concluido'
        esta_atrasado = verificar_prazo_atrasado(prazo_fatal_ts, status)
        recorrente = prazo.get('recorrente', False)
        recorrente_texto = 'Sim' if recorrente else 'Não'
        
        # Cor da linha baseada no status
        if esta_atrasado:
            cor_fundo = ft.colors.RED_50
        elif esta_concluido:
            cor_fundo = ft.colors.GREEN_50
        else:
            cor_fundo = None
        
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Checkbox(value=esta_concluido, data=prazo_id)),
                    ft.DataCell(ft.Text(titulo)),
                    ft.DataCell(ft.Text(responsaveis_texto)),
                    ft.DataCell(ft.Text(clientes_texto)),
                    ft.DataCell(ft.Text(prazo_seguranca_texto)),
                    ft.DataCell(ft.Text(prazo_fatal_texto)),
                    ft.DataCell(ft.Text(recorrente_texto)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.icons.EDIT, icon_color=ft.colors.BLUE, data=prazo_id),
                        ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED, data=prazo_id),
                    ])),
                ],
                color=cor_fundo,
                data=prazo,
            )
        )
    
    return rows


def criar_aba_pendentes(page: ft.Page, usuarios_opcoes: Dict[str, str], clientes_opcoes: Dict[str, str],
                        on_edit: Callable, on_delete: Callable, on_toggle: Callable,
                        on_refresh: Callable) -> ft.Container:
    """
    Cria aba de prazos pendentes.
    
    Returns:
        Container com tabela de pendentes
    """
    def carregar_pendentes():
        """Carrega prazos pendentes."""
        try:
            prazos_lista = listar_prazos_por_status('pendente')
            prazos_lista.sort(key=lambda p: p.get('prazo_fatal', 0))
            
            if not prazos_lista:
                return criar_mensagem_vazia(
                    ft.icons.CHECK_CIRCLE,
                    "Nenhum prazo pendente",
                    "Todos os prazos estão concluídos!"
                )
            
            # Criar tabela
            tabela = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("")),
                    ft.DataColumn(ft.Text("Título")),
                    ft.DataColumn(ft.Text("Responsáveis")),
                    ft.DataColumn(ft.Text("Clientes")),
                    ft.DataColumn(ft.Text("Prazo Segurança")),
                    ft.DataColumn(ft.Text("Prazo Fatal")),
                    ft.DataColumn(ft.Text("Recorrente")),
                    ft.DataColumn(ft.Text("Ações")),
                ],
                rows=criar_tabela_prazos_data(prazos_lista, usuarios_opcoes, clientes_opcoes),
            )
            
            # Adicionar handlers
            for row in tabela.rows:
                prazo_data = row.data
                prazo_id = prazo_data.get('_id')
                
                # Checkbox
                checkbox = row.cells[0].content
                if isinstance(checkbox, ft.Checkbox):
                    def make_toggle_handler(pid):
                        return lambda e: on_toggle(pid, e.control.value)
                    checkbox.on_change = make_toggle_handler(prazo_id)
                
                # Botões de ação
                acoes_row = row.cells[7].content
                if isinstance(acoes_row, ft.Row):
                    for btn in acoes_row.controls:
                        if isinstance(btn, ft.IconButton):
                            if btn.icon == ft.icons.EDIT:
                                def make_edit_handler(pid):
                                    return lambda e: on_edit(pid)
                                btn.on_click = make_edit_handler(prazo_id)
                            elif btn.icon == ft.icons.DELETE:
                                def make_delete_handler(pid):
                                    return lambda e: on_delete(pid)
                                btn.on_click = make_delete_handler(prazo_id)
            
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"{len(prazos_lista)} prazo(s) pendente(s)", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=tabela,
                        expand=True,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=8,
                    ),
                ], spacing=12),
                expand=True,
            )
        except Exception as e:
            print(f"[ERROR] Erro ao carregar prazos pendentes: {e}")
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"Erro ao carregar prazos: {str(e)}", color=ft.colors.RED),
                padding=16,
            )
    
    container = ft.Container(
        content=carregar_pendentes(),
        expand=True,
    )
    
    # Função para atualizar
    def refresh():
        container.content = carregar_pendentes()
        page.update()
    
    on_refresh['pendentes'] = refresh
    
    return container


def criar_aba_concluidos(page: ft.Page, usuarios_opcoes: Dict[str, str], clientes_opcoes: Dict[str, str],
                         on_edit: Callable, on_delete: Callable, on_toggle: Callable,
                         on_refresh: Callable) -> ft.Container:
    """
    Cria aba de prazos concluídos.
    
    Returns:
        Container com tabela de concluídos
    """
    def carregar_concluidos():
        """Carrega prazos concluídos."""
        try:
            prazos_lista = listar_prazos_por_status('concluido')
            prazos_lista.sort(key=lambda p: p.get('atualizado_em', 0), reverse=True)
            
            if not prazos_lista:
                return criar_mensagem_vazia(
                    ft.icons.PENDING_ACTIONS,
                    "Nenhum prazo concluído",
                    "Conclua alguns prazos para vê-los aqui"
                )
            
            # Criar tabela
            tabela = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("")),
                    ft.DataColumn(ft.Text("Título")),
                    ft.DataColumn(ft.Text("Responsáveis")),
                    ft.DataColumn(ft.Text("Clientes")),
                    ft.DataColumn(ft.Text("Prazo Segurança")),
                    ft.DataColumn(ft.Text("Prazo Fatal")),
                    ft.DataColumn(ft.Text("Recorrente")),
                    ft.DataColumn(ft.Text("Ações")),
                ],
                rows=criar_tabela_prazos_data(prazos_lista, usuarios_opcoes, clientes_opcoes),
            )
            
            # Adicionar handlers
            for row in tabela.rows:
                prazo_data = row.data
                prazo_id = prazo_data.get('_id')
                
                # Checkbox
                checkbox = row.cells[0].content
                if isinstance(checkbox, ft.Checkbox):
                    def make_toggle_handler(pid):
                        return lambda e: on_toggle(pid, e.control.value)
                    checkbox.on_change = make_toggle_handler(prazo_id)
                
                # Botões de ação
                acoes_row = row.cells[7].content
                if isinstance(acoes_row, ft.Row):
                    for btn in acoes_row.controls:
                        if isinstance(btn, ft.IconButton):
                            if btn.icon == ft.icons.EDIT:
                                def make_edit_handler(pid):
                                    return lambda e: on_edit(pid)
                                btn.on_click = make_edit_handler(prazo_id)
                            elif btn.icon == ft.icons.DELETE:
                                def make_delete_handler(pid):
                                    return lambda e: on_delete(pid)
                                btn.on_click = make_delete_handler(prazo_id)
            
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"{len(prazos_lista)} prazo(s) concluído(s)", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=tabela,
                        expand=True,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=8,
                    ),
                ], spacing=12),
                expand=True,
            )
        except Exception as e:
            print(f"[ERROR] Erro ao carregar prazos concluídos: {e}")
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"Erro ao carregar prazos: {str(e)}", color=ft.colors.RED),
                padding=16,
            )
    
    container = ft.Container(
        content=carregar_concluidos(),
        expand=True,
    )
    
    # Função para atualizar
    def refresh():
        container.content = carregar_concluidos()
        page.update()
    
    on_refresh['concluidos'] = refresh
    
    return container


def criar_aba_semana(page: ft.Page, usuarios_opcoes: Dict[str, str], clientes_opcoes: Dict[str, str],
                      on_edit: Callable, on_delete: Callable, on_toggle: Callable,
                      on_refresh: Callable) -> ft.Container:
    """
    Cria aba de prazos por semana com filtros.
    
    Returns:
        Container com tabela e filtros de semana
    """
    filtro_semana = {'tipo': 'esta_semana'}
    
    def obter_periodo_filtro():
        """Retorna início e fim baseado no filtro atual."""
        if filtro_semana['tipo'] == 'semana_passada':
            return obter_semana_passada()
        elif filtro_semana['tipo'] == 'proxima_semana':
            return obter_proxima_semana()
        else:  # esta_semana (padrão)
            return obter_esta_semana()
    
    def carregar_semana():
        """Carrega prazos da semana selecionada."""
        try:
            todos_prazos = listar_prazos()
            inicio, fim = obter_periodo_filtro()
            prazos_semana = filtrar_prazos_por_semana(todos_prazos, inicio, fim)
            prazos_semana.sort(key=lambda p: p.get('prazo_fatal', 0))
            
            if not prazos_semana:
                return criar_mensagem_vazia(
                    ft.icons.EVENT_BUSY,
                    "Nenhum prazo nesta semana",
                    "Selecione outra semana ou adicione novos prazos"
                )
            
            # Criar tabela com coluna de status
            tabela = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("")),
                    ft.DataColumn(ft.Text("Título")),
                    ft.DataColumn(ft.Text("Responsáveis")),
                    ft.DataColumn(ft.Text("Prazo Seg.")),
                    ft.DataColumn(ft.Text("Prazo Fatal")),
                    ft.DataColumn(ft.Text("Status")),
                    ft.DataColumn(ft.Text("Ações")),
                ],
                rows=[],
            )
            
            # Criar linhas
            for prazo in prazos_semana:
                prazo_id = prazo.get('_id')
                titulo = formatar_titulo_prazo(prazo)
                responsaveis_ids = prazo.get('responsaveis', [])
                responsaveis_texto = formatar_lista_nomes(responsaveis_ids, usuarios_opcoes)
                prazo_fatal_ts = prazo.get('prazo_fatal')
                prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
                prazo_seguranca_texto = calcular_prazo_seguranca(prazo_fatal_ts)
                status = prazo.get('status', 'pendente')
                esta_concluido = status.lower() == 'concluido'
                esta_atrasado = verificar_prazo_atrasado(prazo_fatal_ts, status)
                
                # Determinar status_label
                if esta_concluido:
                    status_label = 'Concluído'
                elif esta_atrasado:
                    status_label = 'Atrasado'
                else:
                    status_label = 'Pendente'
                
                # Cor da linha
                if esta_atrasado:
                    cor_fundo = ft.colors.RED_50
                elif esta_concluido:
                    cor_fundo = ft.colors.GREEN_50
                else:
                    cor_fundo = None
                
                # Badge de status
                if esta_concluido:
                    status_badge = ft.Container(
                        content=ft.Text(status_label, size=12, color=ft.colors.WHITE),
                        bgcolor=ft.colors.GREEN_400,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=8,
                    )
                elif esta_atrasado:
                    status_badge = ft.Container(
                        content=ft.Text(status_label, size=12, color=ft.colors.WHITE),
                        bgcolor=ft.colors.RED_400,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=8,
                    )
                else:
                    status_badge = ft.Container(
                        content=ft.Text(status_label, size=12, color=ft.colors.BLACK87),
                        bgcolor=ft.colors.YELLOW_400,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=8,
                    )
                
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Checkbox(value=esta_concluido, data=prazo_id)),
                        ft.DataCell(ft.Text(titulo)),
                        ft.DataCell(ft.Text(responsaveis_texto)),
                        ft.DataCell(ft.Text(prazo_seguranca_texto)),
                        ft.DataCell(ft.Text(prazo_fatal_texto)),
                        ft.DataCell(status_badge),
                        ft.DataCell(ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT, icon_color=ft.colors.BLUE, data=prazo_id),
                            ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED, data=prazo_id),
                        ])),
                    ],
                    color=cor_fundo,
                    data=prazo,
                )
                
                # Handlers
                checkbox = row.cells[0].content
                if isinstance(checkbox, ft.Checkbox):
                    def make_toggle_handler(pid):
                        return lambda e: on_toggle(pid, e.control.value)
                    checkbox.on_change = make_toggle_handler(prazo_id)
                
                acoes_row = row.cells[6].content
                if isinstance(acoes_row, ft.Row):
                    for btn in acoes_row.controls:
                        if isinstance(btn, ft.IconButton):
                            if btn.icon == ft.icons.EDIT:
                                def make_edit_handler(pid):
                                    return lambda e: on_edit(pid)
                                btn.on_click = make_edit_handler(prazo_id)
                            elif btn.icon == ft.icons.DELETE:
                                def make_delete_handler(pid):
                                    return lambda e: on_delete(pid)
                                btn.on_click = make_delete_handler(prazo_id)
                
                tabela.rows.append(row)
            
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"{len(prazos_semana)} prazo(s) nesta semana", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=tabela,
                        expand=True,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=8,
                    ),
                ], spacing=12),
                expand=True,
            )
        except Exception as e:
            print(f"[ERROR] Erro ao carregar prazos da semana: {e}")
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"Erro ao carregar prazos: {str(e)}", color=ft.colors.RED),
                padding=16,
            )
    
    def selecionar_filtro(tipo: str):
        """Seleciona um filtro de semana."""
        filtro_semana['tipo'] = tipo
        container.content = ft.Column([
            criar_filtros_semana(),
            carregar_semana(),
        ], spacing=12, expand=True)
        page.update()
    
    def criar_filtros_semana():
        """Cria botões de filtro de semana."""
        inicio, fim = obter_periodo_filtro()
        
        return ft.Row([
            ft.ElevatedButton(
                "Semana Passada",
                icon=ft.icons.CHEVRON_LEFT,
                on_click=lambda e: selecionar_filtro('semana_passada'),
                bgcolor=ft.colors.BLUE if filtro_semana['tipo'] == 'semana_passada' else None,
                color=ft.colors.WHITE if filtro_semana['tipo'] == 'semana_passada' else None,
            ),
            ft.ElevatedButton(
                "Esta Semana",
                icon=ft.icons.TODAY,
                on_click=lambda e: selecionar_filtro('esta_semana'),
                bgcolor=ft.colors.BLUE if filtro_semana['tipo'] == 'esta_semana' else None,
                color=ft.colors.WHITE if filtro_semana['tipo'] == 'esta_semana' else None,
            ),
            ft.ElevatedButton(
                "Próxima Semana",
                icon=ft.icons.CHEVRON_RIGHT,
                on_click=lambda e: selecionar_filtro('proxima_semana'),
                bgcolor=ft.colors.BLUE if filtro_semana['tipo'] == 'proxima_semana' else None,
                color=ft.colors.WHITE if filtro_semana['tipo'] == 'proxima_semana' else None,
            ),
            ft.Text(f"Período: {formatar_periodo_semana(inicio, fim)}", size=12, weight=ft.FontWeight.W_500),
        ], spacing=12, wrap=True)
    
    container = ft.Container(
        content=ft.Column([
            criar_filtros_semana(),
            carregar_semana(),
        ], spacing=12, expand=True),
        expand=True,
    )
    
    # Função para atualizar
    def refresh():
        container.content = ft.Column([
            criar_filtros_semana(),
            carregar_semana(),
        ], spacing=12, expand=True)
        page.update()
    
    on_refresh['semana'] = refresh
    
    return container

