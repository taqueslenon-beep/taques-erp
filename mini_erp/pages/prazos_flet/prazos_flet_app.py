"""
prazos_flet_app.py - Aplicação Flet principal do módulo Prazos.
"""

import flet as ft
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from .database import (
    buscar_prazo_por_id,
    buscar_usuarios_para_select,
    buscar_clientes_para_select,
    buscar_casos_para_select,
    atualizar_prazo,
    excluir_prazo,
    criar_proximo_prazo_recorrente,
    calcular_proximo_prazo_fatal,
    invalidar_cache_prazos,
)
from .modal_prazo_flet import criar_modal_prazo
from .tabela_prazos_flet import (
    criar_aba_pendentes,
    criar_aba_concluidos,
    criar_aba_semana,
)
from ...auth import is_authenticated, get_current_user


def prazos_flet(page: ft.Page):
    """
    Função principal da aplicação Flet de Prazos.
    
    Args:
        page: Página Flet
    """
    # Verificar autenticação
    if not is_authenticated():
        page.route = "/login"
        page.update()
        return
    
    # Configurar página
    page.title = "Prazos - TAQUES ERP"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    
    # Carregar opções em paralelo
    opcoes = {'usuarios': {}, 'clientes': {}, 'casos': {}}
    
    def carregar_opcoes():
        """Carrega opções em paralelo."""
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(buscar_usuarios_para_select): 'usuarios',
                executor.submit(buscar_clientes_para_select): 'clientes',
                executor.submit(buscar_casos_para_select): 'casos',
            }
            
            for future in as_completed(futures):
                key = futures[future]
                try:
                    opcoes[key] = future.result()
                except Exception as e:
                    print(f"[PRAZOS-FLET] Erro ao carregar {key}: {e}")
                    opcoes[key] = {}
    
    carregar_opcoes()
    
    usuarios_opcoes = opcoes.get('usuarios', {})
    clientes_opcoes = opcoes.get('clientes', {})
    casos_opcoes = opcoes.get('casos', {})
    
    # Referências para funções de refresh
    refresh_funcs = {'pendentes': None, 'concluidos': None, 'semana': None}
    
    # Dialog de confirmação
    confirm_dialog = ft.Ref[ft.AlertDialog]()
    
    # Função para atualizar todas as abas
    def atualizar_todas_abas():
        """Atualiza todas as abas."""
        invalidar_cache_prazos()
        if refresh_funcs['pendentes']:
            refresh_funcs['pendentes']()
        if refresh_funcs['concluidos']:
            refresh_funcs['concluidos']()
        if refresh_funcs['semana']:
            refresh_funcs['semana']()
    
    # Callback após salvar prazo
    def on_prazo_salvo(prazo_data: Dict[str, Any]):
        """Callback executado após salvar prazo."""
        try:
            atualizar_todas_abas()
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Prazo salvo com sucesso!"),
                bgcolor=ft.colors.GREEN,
            )
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            print(f"[ERROR] Erro ao processar prazo salvo: {e}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Erro ao atualizar lista. Tente recarregar."),
                bgcolor=ft.colors.RED,
            )
            page.snack_bar.open = True
            page.update()
    
    # Função para abrir modal de edição
    def abrir_modal_edicao(prazo_id: str):
        """Abre modal de edição com dados do prazo."""
        try:
            prazo = buscar_prazo_por_id(prazo_id)
            if not prazo:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Prazo não encontrado!"),
                    bgcolor=ft.colors.RED,
                )
                page.snack_bar.open = True
                page.update()
                return
            
            # Criar dialog de edição
            dialog = criar_modal_prazo(
                page=page,
                on_success=on_prazo_salvo,
                prazo_inicial=prazo,
                usuarios_opcoes=usuarios_opcoes,
                clientes_opcoes=clientes_opcoes,
                casos_opcoes=casos_opcoes
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir modal de edição: {e}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Erro ao carregar dados do prazo. Tente novamente."),
                bgcolor=ft.colors.RED,
            )
            page.snack_bar.open = True
            page.update()
    
    # Função para excluir prazo
    def excluir_prazo_com_confirmacao(prazo_id: str, titulo: Optional[str] = None):
        """Exclui prazo com diálogo de confirmação."""
        if not titulo:
            prazo = buscar_prazo_por_id(prazo_id)
            titulo = prazo.get('titulo', 'este prazo') if prazo else 'este prazo'
        
        def on_confirm(e):
            try:
                sucesso = excluir_prazo(prazo_id)
                if sucesso:
                    atualizar_todas_abas()
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Prazo excluído com sucesso!"),
                        bgcolor=ft.colors.GREEN,
                    )
                    page.snack_bar.open = True
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Erro ao excluir prazo"),
                        bgcolor=ft.colors.RED,
                    )
                    page.snack_bar.open = True
            except Exception as ex:
                print(f"[ERROR] Erro ao excluir prazo: {ex}")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro ao excluir prazo: {str(ex)}"),
                    bgcolor=ft.colors.RED,
                )
                page.snack_bar.open = True
            
            confirm_dialog.current.open = False
            page.update()
        
        def on_cancel(e):
            confirm_dialog.current.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            ref=confirm_dialog,
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f'Tem certeza que deseja excluir o prazo "{titulo}"?'),
            actions=[
                ft.TextButton("Cancelar", on_click=on_cancel),
                ft.ElevatedButton("Excluir", on_click=on_confirm, bgcolor=ft.colors.RED, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Função para confirmar conclusão de prazo
    def confirmar_conclusao_prazo(prazo_id: str, titulo: str):
        """Mostra diálogo de confirmação para marcar prazo como concluído."""
        def on_confirm(e):
            try:
                prazo = buscar_prazo_por_id(prazo_id)
                if not prazo:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Prazo não encontrado!"),
                        bgcolor=ft.colors.RED,
                    )
                    page.snack_bar.open = True
                    page.update()
                    confirm_dialog.current.open = False
                    page.update()
                    return
                
                prazo['status'] = 'concluido'
                sucesso = atualizar_prazo(prazo_id, prazo)
                
                if sucesso:
                    # Se for recorrente, criar próximo prazo
                    if prazo.get('recorrente'):
                        novo_id = criar_proximo_prazo_recorrente(prazo)
                        if novo_id:
                            # Calcular nova data para exibir na notificação
                            nova_data = calcular_proximo_prazo_fatal(prazo)
                            if nova_data:
                                page.snack_bar = ft.SnackBar(
                                    content=ft.Text(f'Prazo concluído! Novo prazo criado para {nova_data.strftime("%d/%m/%Y")}'),
                                    bgcolor=ft.colors.GREEN,
                                )
                            else:
                                page.snack_bar = ft.SnackBar(
                                    content=ft.Text('Prazo concluído! Novo prazo criado.'),
                                    bgcolor=ft.colors.GREEN,
                                )
                        else:
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text('Prazo concluído! (Erro ao criar próximo prazo recorrente)'),
                                bgcolor=ft.colors.ORANGE,
                            )
                    else:
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text('Prazo concluído com sucesso!'),
                            bgcolor=ft.colors.GREEN,
                        )
                    
                    atualizar_todas_abas()
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text('Erro ao atualizar status'),
                        bgcolor=ft.colors.RED,
                    )
                    page.snack_bar.open = True
            except Exception as ex:
                print(f"[ERROR] Erro ao concluir prazo: {ex}")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f'Erro ao concluir prazo: {str(ex)}'),
                    bgcolor=ft.colors.RED,
                )
                page.snack_bar.open = True
            
            confirm_dialog.current.open = False
            page.update()
        
        def on_cancel(e):
            confirm_dialog.current.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            ref=confirm_dialog,
            modal=True,
            title=ft.Text("Confirmar Conclusão"),
            content=ft.Text(f'Deseja marcar o prazo "{titulo}" como concluído?'),
            actions=[
                ft.TextButton("Não", on_click=on_cancel),
                ft.ElevatedButton("Sim", on_click=on_confirm, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Função para confirmar reabertura de prazo
    def confirmar_reabertura_prazo(prazo_id: str, titulo: str):
        """Mostra diálogo de confirmação para reabrir prazo."""
        def on_confirm(e):
            try:
                prazo = buscar_prazo_por_id(prazo_id)
                if not prazo:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Prazo não encontrado!"),
                        bgcolor=ft.colors.RED,
                    )
                    page.snack_bar.open = True
                    page.update()
                    confirm_dialog.current.open = False
                    page.update()
                    return
                
                prazo['status'] = 'pendente'
                sucesso = atualizar_prazo(prazo_id, prazo)
                
                if sucesso:
                    atualizar_todas_abas()
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Prazo reaberto!"),
                        bgcolor=ft.colors.GREEN,
                    )
                    page.snack_bar.open = True
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text('Erro ao atualizar status'),
                        bgcolor=ft.colors.RED,
                    )
                    page.snack_bar.open = True
            except Exception as ex:
                print(f"[ERROR] Erro ao reabrir prazo: {ex}")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f'Erro ao reabrir prazo: {str(ex)}'),
                    bgcolor=ft.colors.RED,
                )
                page.snack_bar.open = True
            
            confirm_dialog.current.open = False
            page.update()
        
        def on_cancel(e):
            confirm_dialog.current.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            ref=confirm_dialog,
            modal=True,
            title=ft.Text("Reabrir Prazo"),
            content=ft.Text(f'Deseja reabrir o prazo "{titulo}"?'),
            actions=[
                ft.TextButton("Não", on_click=on_cancel),
                ft.ElevatedButton("Sim", on_click=on_confirm, bgcolor=ft.colors.ORANGE, color=ft.colors.WHITE),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Função para toggle de status
    def on_toggle_status(prazo_id: str, novo_valor: bool):
        """Handler para alterar status via checkbox."""
        try:
            prazo = buscar_prazo_por_id(prazo_id)
            if not prazo:
                return
            
            titulo = prazo.get('titulo', 'este prazo')
            
            if novo_valor:
                # Marcar como concluído - pedir confirmação
                confirmar_conclusao_prazo(prazo_id, titulo)
            else:
                # Reabrir prazo - pedir confirmação
                confirmar_reabertura_prazo(prazo_id, titulo)
        except Exception as e:
            print(f"[ERROR] Erro ao alternar status: {e}")
    
    # Função para abrir modal de novo prazo
    def abrir_modal_novo():
        """Abre modal para criar novo prazo."""
        dialog = criar_modal_prazo(
            page=page,
            on_success=on_prazo_salvo,
            prazo_inicial=None,
            usuarios_opcoes=usuarios_opcoes,
            clientes_opcoes=clientes_opcoes,
            casos_opcoes=casos_opcoes
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Função wrapper para excluir (busca título automaticamente)
    def excluir_prazo_wrapper(prazo_id: str):
        """Wrapper que busca título e chama exclusão."""
        excluir_prazo_com_confirmacao(prazo_id)
    
    # Criar abas
    tab_pendentes = criar_aba_pendentes(
        page=page,
        usuarios_opcoes=usuarios_opcoes,
        clientes_opcoes=clientes_opcoes,
        on_edit=abrir_modal_edicao,
        on_delete=excluir_prazo_wrapper,
        on_toggle=on_toggle_status,
        on_refresh=refresh_funcs,
    )
    
    tab_concluidos = criar_aba_concluidos(
        page=page,
        usuarios_opcoes=usuarios_opcoes,
        clientes_opcoes=clientes_opcoes,
        on_edit=abrir_modal_edicao,
        on_delete=excluir_prazo_wrapper,
        on_toggle=on_toggle_status,
        on_refresh=refresh_funcs,
    )
    
    tab_semana = criar_aba_semana(
        page=page,
        usuarios_opcoes=usuarios_opcoes,
        clientes_opcoes=clientes_opcoes,
        on_edit=abrir_modal_edicao,
        on_delete=excluir_prazo_wrapper,
        on_toggle=on_toggle_status,
        on_refresh=refresh_funcs,
    )
    
    # Criar tabs
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Pendentes", content=tab_pendentes),
            ft.Tab(text="Concluídos", content=tab_concluidos),
            ft.Tab(text="Por Semana", content=tab_semana),
        ],
        expand=1,
    )
    
    # Layout principal
    page.add(
        ft.Row([
            ft.Text("Prazos", size=24, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton(
                "Adicionar Prazo",
                icon=ft.icons.ADD,
                on_click=lambda e: abrir_modal_novo(),
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        tabs,
    )


# Função para rodar como aplicação web
def main(page: ft.Page):
    """Ponto de entrada para aplicação Flet standalone."""
    prazos_flet(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, port=8081)

