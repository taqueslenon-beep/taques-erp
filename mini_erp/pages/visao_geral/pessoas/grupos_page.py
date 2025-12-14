"""
Página de Grupos de Relacionamento.
Renderiza lista de grupos em formato de cards.
"""
from nicegui import ui
from .database_grupo import (
    listar_grupos,
    excluir_grupo,
    inicializar_grupo_schmidmeier,
)
from .database import listar_pessoas
from .grupo_dialog import abrir_dialog_grupo
from .models_grupo import GrupoRelacionamento


def confirmar_exclusao_grupo(grupo: GrupoRelacionamento, on_confirm: callable):
    """
    Exibe dialog de confirmação antes de excluir grupo.

    Args:
        grupo: Instância de GrupoRelacionamento a ser excluída
        on_confirm: Callback chamado quando usuário confirma exclusão
    """
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
        ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800 mb-4')
        
        ui.label(
            f'Tem certeza que deseja excluir o grupo "{grupo.nome}"?'
        ).classes('text-gray-600 mb-2')
        
        ui.label(
            'Esta ação marcará o grupo como inativo. '
            'Pessoas vinculadas não serão afetadas.'
        ).classes('text-sm text-gray-500 mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', icon='close', on_click=dialog.close).props('flat')
            ui.button(
                'Excluir',
                icon='delete',
                on_click=lambda: (on_confirm(), dialog.close())
            ).props('color=negative')
        
    dialog.open()


def renderizar_pagina_grupos():
    """
    Renderiza a página de grupos de relacionamento.
    """
    # Inicializa grupo Schmidmeier se não existir
    try:
        inicializar_grupo_schmidmeier()
    except Exception as e:
        print(f"Erro ao inicializar grupo Schmidmeier: {e}")
    
    # Container principal
    with ui.card().classes('w-full'):
        # Header com botão novo grupo
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label('Grupos de Relacionamento').classes('text-xl font-bold text-gray-800')
            ui.button(
                'Novo Grupo',
                icon='add',
                on_click=lambda: abrir_dialog_grupo(on_save=lambda: refresh_grupos.refresh())
            ).props('color=primary')
    
    # Container para cards de grupos
    @ui.refreshable
    def refresh_grupos():
        try:
            grupos = listar_grupos(apenas_ativos=True)
            pessoas = listar_pessoas()
            
            # Conta pessoas por grupo
            pessoas_por_grupo = {}
            for pessoa in pessoas:
                grupo_id = pessoa.get('grupo_id', '')
                if grupo_id:
                    pessoas_por_grupo[grupo_id] = pessoas_por_grupo.get(grupo_id, 0) + 1
        except Exception as e:
            print(f"Erro ao carregar grupos: {e}")
            with ui.card().classes('w-full'):
                ui.icon('error', size='48px', color='negative')
                ui.label('Erro ao carregar grupos').classes('text-lg text-gray-600 mt-2')
                ui.label('Tente recarregar a página.').classes('text-sm text-gray-400')
            return
        
        # Estado vazio
        if not grupos:
            with ui.card().classes('w-full'):
                with ui.column().classes('w-full items-center py-12'):
                    ui.icon('group', size='64px').classes('text-gray-300')
                    ui.label('Nenhum grupo cadastrado').classes('text-lg text-gray-500 mt-4')
                    ui.label('Clique em "Novo Grupo" para começar.').classes('text-sm text-gray-400')
            return
        
        # Grid de cards
        with ui.grid(columns=3).classes('w-full gap-4'):
            for grupo in grupos:
                qtd_pessoas = pessoas_por_grupo.get(grupo._id, 0)
                
                with ui.card().classes('w-full hover:shadow-lg transition-shadow'):
                    # Header do card com cor de fundo
                    with ui.row().classes('w-full items-center gap-3 p-4').style(
                        f'background-color: {grupo.cor}20; border-left: 4px solid {grupo.cor};'
                    ):
                        # Ícone
                        ui.label(grupo.icone or '📁').classes('text-3xl')
                        
                        # Nome e descrição
                        with ui.column().classes('flex-1 gap-1'):
                            ui.label(grupo.nome).classes('text-lg font-bold text-gray-800')
                            if grupo.descricao:
                                ui.label(grupo.descricao).classes('text-sm text-gray-600 line-clamp-2')
                    
                    # Conteúdo do card
                    with ui.column().classes('w-full p-4 gap-3'):
                        # Estatísticas
                        with ui.row().classes('w-full items-center gap-2'):
                            ui.icon('people', size='sm').classes('text-gray-500')
                            ui.label(f'{qtd_pessoas} pessoa(s) vinculada(s)').classes('text-sm text-gray-600')
                        
                        # Botões de ação
                        with ui.row().classes('w-full justify-end gap-2 mt-2'):
                            ui.button(
                                icon='edit',
                                on_click=lambda g=grupo: abrir_dialog_grupo(
                                    grupo=g,
                                    on_save=lambda: refresh_grupos.refresh()
                                )
                            ).props('flat dense color=primary').tooltip('Editar')
                            
                            def excluir(g=grupo):
                                """Exclui o grupo."""
                                def executar_exclusao():
                                    if excluir_grupo(g._id):
                                        ui.notify(f'Grupo "{g.nome}" excluído com sucesso!', type='positive')
                                        refresh_grupos.refresh()
                                    else:
                                        ui.notify('Erro ao excluir grupo. Tente novamente.', type='negative')
                                
                                confirmar_exclusao_grupo(g, executar_exclusao)
                            
                            ui.button(
                                icon='delete',
                                on_click=excluir
                            ).props('flat dense color=negative').tooltip('Excluir')
    
    refresh_grupos()

