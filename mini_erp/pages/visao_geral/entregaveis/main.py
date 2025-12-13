"""
Página principal do módulo de Entregáveis com visualização Kanban.

Permite visualizar entregáveis por status ou categoria, com drag & drop.
Workspace: Visão geral do escritório
"""

from datetime import datetime
from nicegui import ui
from ....core import layout
from ....auth import is_authenticated, get_current_user
from ....firebase_config import ensure_firebase_initialized, get_auth
from ....middlewares.verificar_workspace import verificar_e_definir_workspace_automatico
from ....models.entregavel import (
    STATUS_OPCOES,
    STATUS_PADRAO,
    CATEGORIAS_OPCOES,
    get_cor_prioridade_entregavel,
    CORES_PRIORIDADE,
    CORES_STATUS,
    normalizar_status,
)
from ....models.prioridade import CODIGOS_PRIORIDADE
from ....services.entregavel_service import (
    listar_entregaveis,
    criar_entregavel,
    atualizar_entregavel,
    atualizar_status,
    atualizar_categoria,
    excluir_entregavel,
    buscar_entregavel_por_id,
    invalidar_cache
)

# Dimensões fixas do Kanban (em pixels)
LARGURA_COLUNA = 260
LARGURA_CARD = 244  # LARGURA_COLUNA - 16 (padding)

# Ordem das prioridades (menor número = maior prioridade)
ORDEM_PRIORIDADE = {
    'P1': 1,
    'P2': 2,
    'P3': 3,
    'P4': 4,
}


def ordenar_por_prioridade(entregaveis: list) -> list:
    """
    Ordena lista de entregáveis por prioridade.
    P1 primeiro (topo), P4 por último (embaixo).
    """
    return sorted(
        entregaveis,
        key=lambda e: ORDEM_PRIORIDADE.get(e.get('prioridade', 'P4'), 99)
    )


# Estado global do drag & drop (compartilhado entre cards e colunas)
drag_state = {
    'dragging_id': None,      # ID do entregável sendo arrastado
    'source_column': None,    # Coluna de origem
}


@ui.page('/visao-geral/entregaveis')
def entregaveis_page():
    """Página principal de Entregáveis com visualização Kanban."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return

        # Verifica e define workspace automaticamente
        workspace_ok = verificar_e_definir_workspace_automatico()
        if not workspace_ok:
            # Se não tem permissão, a função já redirecionou
            return
        
        # Estado da visualização (por status ou categoria)
        visualizacao = {'tipo': 'status'}  # 'status' ou 'categoria'

        # Estado dos filtros
        filtros = {
            'prioridade': None,  # None = Todas, ou 'P1', 'P2', 'P3', 'P4'
            'responsavel_id': None,  # None = Todos, ou ID do responsável
            'categoria': None,  # None = Todas, ou nome da categoria (só ativo na visualização por status)
        }

        # Estado dos entregáveis
        entregaveis_data = {'lista': []}

        # Estado compartilhado para opções de responsável (preenchido ao criar modal)
        responsavel_options_state = {'opcoes': {}}

        # Estado para armazenar referências dos componentes do modal
        # (permite que a função abrir_modal_criacao acesse os componentes antes de serem criados)
        modal_state = {
            'modal': None,
            'titulo_modal': None,
            'titulo_input': None,
            'responsavel_select': None,
            'categoria_select': None,
            'status_select': None,
            'prioridade_select': None,
            'prazo_input': None,
            'slack_link_input': None,
        }

        def abrir_modal_criacao():
            """
            Abre modal para criar novo entregável (campos vazios).

            Diferente do modo edição:
            - _modo_edicao = False
            - _entregavel_id = None
            - Campos limpos
            - Botão EXCLUIR não aparece
            """
            if not modal_state['modal']:
                ui.notify('Modal ainda não inicializado', type='warning')
                return

            # Define modo de criação (não é edição)
            modal_state['modal']._modo_edicao = False
            modal_state['modal']._entregavel_id = None

            # Atualiza título do modal
            modal_state['titulo_modal'].text = 'Novo Entregável'
            modal_state['titulo_modal'].classes(replace='text-xl font-bold mb-4 text-primary')

            # Limpa todos os campos (diferente de edição que preenche com dados)
            modal_state['titulo_input'].value = ''
            modal_state['responsavel_select'].value = None
            modal_state['categoria_select'].value = 'Operacional'
            modal_state['status_select'].value = STATUS_PADRAO  # 'Em espera'
            modal_state['prioridade_select'].value = 'P4'
            modal_state['prazo_input'].value = ''
            modal_state['slack_link_input'].value = ''

            # Abre modal
            modal_state['modal'].open()

        def carregar_entregaveis():
            """Carrega entregáveis do Firestore."""
            entregaveis_data['lista'] = listar_entregaveis()
            kanban_area.refresh()
        
        def criar_card_entregavel(entregavel: dict, coluna_atual: str = None):
            """
            Cria um card visual para um entregável com título completo.

            Funcionalidades:
            - Clique no card abre modal de edição
            - Botão delete no canto superior direito (com confirmação)
            - Drag & drop entre colunas
            - Ícone do Slack (se houver link)
            """
            entregavel_id = entregavel.get('_id', '')
            titulo = entregavel.get('titulo', 'Sem título')
            prioridade = entregavel.get('prioridade', 'P4')
            responsavel_nome = entregavel.get('responsavel_nome', 'Sem responsável')
            prazo = entregavel.get('prazo')
            slack_link = entregavel.get('slack_link', '')

            # Cor da prioridade
            cor_prioridade = get_cor_prioridade_entregavel(prioridade)

            # Processa prazo
            prazo_texto = ''
            cor_prazo = '#6B7280'
            if prazo:
                try:
                    if isinstance(prazo, (int, float)):
                        prazo_dt = datetime.fromtimestamp(prazo)
                    else:
                        prazo_dt = prazo

                    hoje = datetime.now()
                    dias = (prazo_dt - hoje).days
                    prazo_texto = prazo_dt.strftime('%d/%m')

                    if dias < 0:
                        cor_prazo = '#DC2626'  # vermelho - vencido
                    elif dias <= 3:
                        cor_prazo = '#D97706'  # laranja - próximo
                except Exception:
                    pass

            # Primeiro nome do responsável
            primeiro_nome = responsavel_nome.split()[0] if responsavel_nome else '-'

            # Função para deletar entregável diretamente do card
            def confirmar_delete_card(e, eid=entregavel_id, titulo_ent=titulo):
                """Abre confirmação de exclusão diretamente do card."""
                # Impede propagação para não abrir modal de edição
                e.stop_propagation = True

                # Abre modal de confirmação
                with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md p-6'):
                    ui.label('Excluir Entregável').classes('text-xl font-bold mb-4 text-red-600')
                    ui.label('Tem certeza que deseja excluir:').classes('text-gray-700 mb-2')
                    ui.label(f'"{titulo_ent}"').classes('font-semibold text-gray-800 mb-4')
                    ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')

                    with ui.row().classes('w-full justify-end gap-2'):
                        ui.button('Cancelar', on_click=dialog_excluir.close).props('flat')

                        def executar_exclusao():
                            """Executa exclusão após confirmação."""
                            try:
                                sucesso = excluir_entregavel(eid)
                                if sucesso:
                                    ui.notify('Entregável excluído com sucesso!', type='positive')
                                    dialog_excluir.close()
                                    carregar_entregaveis()
                                else:
                                    ui.notify('Erro ao excluir entregável', type='negative')
                            except Exception as ex:
                                print(f"[ENTREGAVEIS] Erro ao excluir: {ex}")
                                ui.notify(f'Erro ao excluir: {str(ex)}', type='negative')

                        ui.button('Excluir', on_click=executar_exclusao, icon='delete').props('color=negative')

                dialog_excluir.open()

            # CARD - altura automática para acomodar título completo
            # cursor: pointer para indicar que é clicável
            with ui.card().style(f'''
                width: {LARGURA_CARD}px;
                max-width: {LARGURA_CARD}px;
                border-left: 4px solid {cor_prioridade};
                cursor: pointer;
                position: relative;
            ''').classes('bg-white rounded shadow-sm hover:shadow-md mb-2 p-0 draggable-card').props('draggable=true') as card:

                # Adiciona atributo data para drag & drop
                card.props(f'data-entregavel-id="{entregavel_id}"')

                # Evento de início do arrasto
                def on_dragstart(e, eid=entregavel_id, col=coluna_atual):
                    drag_state['dragging_id'] = eid
                    drag_state['source_column'] = col

                card.on('dragstart', on_dragstart)

                # Container interno
                with ui.column().style('width: 100%;').classes('gap-1 p-2'):

                    # LINHA 1: Badge + Título + Botão Delete
                    with ui.row().style('width: 100%;').classes('items-start gap-2'):
                        # Badge prioridade
                        ui.label(prioridade).style(f'''
                            background-color: {cor_prioridade};
                            color: white;
                            padding: 2px 8px;
                            border-radius: 4px;
                            font-size: 11px;
                            font-weight: bold;
                            flex-shrink: 0;
                            margin-top: 2px;
                        ''')

                        # Título COMPLETO (sem truncamento) - flex-grow para ocupar espaço
                        ui.label(titulo).style('''
                            font-size: 13px;
                            font-weight: 500;
                            color: #1f2937;
                            word-wrap: break-word;
                            overflow-wrap: break-word;
                            white-space: normal;
                            line-height: 1.4;
                            flex-grow: 1;
                        ''')

                        # BOTÃO DELETE - canto superior direito
                        delete_btn = ui.icon('delete', size='18px').style('''
                            color: #9CA3AF;
                            cursor: pointer;
                            flex-shrink: 0;
                            transition: color 0.2s;
                        ''').classes('hover-red').tooltip('Excluir entregável')
                        delete_btn.on('click', confirmar_delete_card)

                    # LINHA 2: Responsável + Slack + Prazo
                    with ui.row().style('width: 100%;').classes('items-center justify-between mt-1'):
                        # Responsável
                        with ui.row().classes('items-center gap-1'):
                            ui.icon('person', size='14px').style('color: #9ca3af;')
                            ui.label(primeiro_nome).style('font-size: 11px; color: #6b7280;')

                        # Ícones do lado direito (Slack + Prazo)
                        with ui.row().classes('items-center gap-2'):
                            # Ícone do Slack (se houver link)
                            if slack_link:
                                def abrir_slack(e, link=slack_link):
                                    """Abre link do Slack em nova aba."""
                                    e.stop_propagation = True  # Evita abrir modal de edição
                                    ui.run_javascript(f'window.open("{link}", "_blank")')

                                slack_btn = ui.icon('tag', size='16px').style('''
                                    color: #4A154B;
                                    cursor: pointer;
                                    transition: transform 0.2s;
                                ''').tooltip('Abrir no Slack')
                                slack_btn.on('click', abrir_slack)

                            # Prazo (se houver)
                            if prazo_texto:
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('event', size='14px').style(f'color: {cor_prazo};')
                                    ui.label(prazo_texto).style(f'font-size: 11px; font-weight: 500; color: {cor_prazo};')

                # Clique no card abre modal de edição
                card.on('click', lambda e, eid=entregavel_id: abrir_modal_edicao(eid))

            return card

        # Nota: abrir_modal_criacao foi movido para depois do modal ser criado
        # (ver abrir_modal_criacao_handler no final do layout)

        def abrir_modal_edicao(entregavel_id: str):
            """Abre modal para editar entregável existente."""
            entregavel = buscar_entregavel_por_id(entregavel_id)
            if not entregavel:
                ui.notify('Entregável não encontrado', type='negative')
                return
            
            # Define modo de edição
            modal_entregavel._modo_edicao = True
            modal_entregavel._entregavel_id = entregavel_id
            
            # Atualiza título do modal
            titulo_modal.text = 'Editar Entregável'
            titulo_modal.classes(replace='text-xl font-bold mb-4 text-primary')
            
            # Preenche campos
            titulo_input.value = entregavel.get('titulo', '')
            responsavel_select.value = entregavel.get('responsavel_id', '')
            categoria_select.value = entregavel.get('categoria', 'Operacional')
            status_select.value = normalizar_status(entregavel.get('status', STATUS_PADRAO))
            prioridade_select.value = entregavel.get('prioridade', 'P4')
            
            # Prazo (formato DD/MM/AAAA)
            prazo_val = entregavel.get('prazo')
            if prazo_val:
                try:
                    if isinstance(prazo_val, (int, float)):
                        prazo_dt = datetime.fromtimestamp(prazo_val)
                    else:
                        prazo_dt = prazo_val
                    prazo_input.value = prazo_dt.strftime('%d/%m/%Y')
                except:
                    prazo_input.value = ''
            else:
                prazo_input.value = ''

            # Link do Slack
            slack_link_input.value = entregavel.get('slack_link', '')
            
            # Abre modal
            modal_entregavel.open()
            
            # Atualiza botão excluir após abrir (deve estar visível)
            if 'atualizar_botao_excluir' in globals() or 'atualizar_botao_excluir' in locals():
                try:
                    atualizar_botao_excluir()
                except:
                    pass
        
        def salvar_entregavel():
            """Salva ou atualiza entregável."""
            # Validações
            if not titulo_input.value or not titulo_input.value.strip():
                ui.notify('Título é obrigatório', type='negative')
                return
            
            if not responsavel_select.value:
                ui.notify('Responsável é obrigatório', type='negative')
                return
            
            # Busca nome do responsável a partir das opções do select
            responsavel_id = responsavel_select.value
            responsavel_nome = responsavel_options_state['opcoes'].get(responsavel_id, 'Sem nome')
            # Remove o email entre parênteses para salvar só o nome
            if ' (' in responsavel_nome:
                responsavel_nome = responsavel_nome.split(' (')[0]
            
            # Prepara dados
            dados = {
                'titulo': titulo_input.value.strip(),
                'responsavel_id': responsavel_select.value,
                'responsavel_nome': responsavel_nome,
                'categoria': categoria_select.value,
                'status': status_select.value,
                'prioridade': prioridade_select.value,
                'slack_link': slack_link_input.value.strip() if slack_link_input.value else '',
            }

            # Prazo (formato DD/MM/AAAA)
            if prazo_input.value and prazo_input.value.strip():
                try:
                    prazo_dt = datetime.strptime(prazo_input.value, '%d/%m/%Y')
                    dados['prazo'] = prazo_dt.timestamp()
                except ValueError:
                    ui.notify('Formato de data inválido. Use DD/MM/AAAA', type='warning')
                    return
            
            try:
                if hasattr(modal_entregavel, '_modo_edicao') and modal_entregavel._modo_edicao and modal_entregavel._entregavel_id:
                    # Atualizar
                    sucesso = atualizar_entregavel(modal_entregavel._entregavel_id, dados)
                    if sucesso:
                        ui.notify('Entregável atualizado com sucesso!', type='positive')
                        modal_entregavel.close()
                        carregar_entregaveis()
                    else:
                        ui.notify('Erro ao atualizar entregável', type='negative')
                else:
                    # Criar
                    user = get_current_user()
                    if user:
                        dados['criado_por'] = user.get('uid', '')
                    entregavel_id = criar_entregavel(dados)
                    if entregavel_id:
                        ui.notify('Entregável criado com sucesso!', type='positive')
                        modal_entregavel.close()
                        carregar_entregaveis()
                    else:
                        ui.notify('Erro ao criar entregável', type='negative')
            except Exception as e:
                print(f"[ENTREGAVEIS] Erro ao salvar: {e}")
                import traceback
                traceback.print_exc()
                ui.notify(f'Erro ao salvar entregável: {str(e)}', type='negative')
        
        
        def confirmar_exclusao():
            """Confirma exclusão do entregável."""
            if not hasattr(modal_entregavel, '_modo_edicao') or not modal_entregavel._modo_edicao:
                ui.notify('Modo de edição não ativo', type='warning')
                return
            
            if not hasattr(modal_entregavel, '_entregavel_id') or not modal_entregavel._entregavel_id:
                ui.notify('ID do entregável não encontrado', type='negative')
                return
            
            entregavel_id = modal_entregavel._entregavel_id
            
            # Busca título do entregável para mostrar na confirmação
            entregavel = buscar_entregavel_por_id(entregavel_id)
            if not entregavel:
                ui.notify('Entregável não encontrado', type='negative')
                return
            
            titulo_entregavel = entregavel.get('titulo', 'este entregável')
            
            # Fecha modal de edição primeiro
            modal_entregavel.close()
            
            # Abre modal de confirmação
            with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md p-6'):
                ui.label('Excluir Entregável').classes('text-xl font-bold mb-4 text-red-600')
                ui.label('Tem certeza que deseja excluir:').classes('text-gray-700 mb-2')
                ui.label(f'"{titulo_entregavel}"').classes('font-semibold text-gray-800 mb-4')
                ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancelar', on_click=dialog_excluir.close).props('flat')
                    
                    def excluir_confirmado():
                        """Executa exclusão após confirmação."""
                        try:
                            sucesso = excluir_entregavel(entregavel_id)
                            if sucesso:
                                ui.notify('Entregável excluído com sucesso!', type='positive')
                                dialog_excluir.close()
                                carregar_entregaveis()
                            else:
                                ui.notify('Erro ao excluir entregável', type='negative')
                        except Exception as e:
                            print(f"[ENTREGAVEIS] Erro ao excluir: {e}")
                            ui.notify(f'Erro ao excluir entregável: {str(e)}', type='negative')
                    
                    ui.button('Excluir', on_click=excluir_confirmado, icon='delete').props('color=negative')
            
            dialog_excluir.open()
        
        with layout('Entregáveis', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Entregáveis', None)]):
            # Header - botão será conectado após modal ser criado
            with ui.row().classes('w-full items-center justify-end mb-4'):
                ui.button('+ Novo Entregável', icon='add', on_click=abrir_modal_criacao).classes('bg-primary text-white')
            
            # Toggle de visualização
            @ui.refreshable
            def toggle_visualizacao():
                """Renderiza os botões de toggle com visual dinâmico."""
                is_status = visualizacao['tipo'] == 'status'
                is_categoria = visualizacao['tipo'] == 'categoria'

                # Estilos para botão ativo e inativo
                estilo_ativo = 'background-color: #2D4A3E; color: white; border: none;'
                estilo_inativo = 'background-color: white; color: #4B5563; border: 1px solid #D1D5DB;'

                with ui.row().classes('items-center gap-0'):
                    # Botão "Por Status"
                    ui.button(
                        'Por Status',
                        on_click=lambda: [visualizacao.update({'tipo': 'status'}), toggle_visualizacao.refresh(), kanban_area.refresh()]
                    ).style(estilo_ativo if is_status else estilo_inativo).classes('rounded-l-lg rounded-r-none px-4 py-2 text-sm font-medium')

                    # Botão "Por Categoria"
                    ui.button(
                        'Por Categoria',
                        on_click=lambda: [visualizacao.update({'tipo': 'categoria'}), toggle_visualizacao.refresh(), kanban_area.refresh()]
                    ).style(estilo_ativo if is_categoria else estilo_inativo).classes('rounded-r-lg rounded-l-none px-4 py-2 text-sm font-medium')

            with ui.row().classes('w-full items-center gap-4 mb-2'):
                ui.label('Visualização:').classes('text-sm font-medium text-gray-700')
                toggle_visualizacao()

            # =================================================================
            # ÁREA DE FILTROS - Prioridade e Responsável
            # =================================================================

            def aplicar_filtro_prioridade(valor):
                """Aplica filtro de prioridade."""
                filtros['prioridade'] = valor if valor != 'todas' else None
                kanban_area.refresh()

            def aplicar_filtro_responsavel(valor):
                """Aplica filtro de responsável."""
                filtros['responsavel_id'] = valor if valor != 'todos' else None
                kanban_area.refresh()

            def aplicar_filtro_categoria(valor):
                """Aplica filtro de categoria (só funciona na visualização por status)."""
                filtros['categoria'] = valor if valor != 'todas' else None
                kanban_area.refresh()

            def limpar_filtros():
                """Limpa todos os filtros."""
                filtros['prioridade'] = None
                filtros['responsavel_id'] = None
                filtros['categoria'] = None
                filtro_prioridade_select.value = 'todas'
                filtro_responsavel_select.value = 'todos'
                # Atualiza filtro de categoria se existir e estiver visível
                if visualizacao['tipo'] == 'status':
                    filtro_categoria_select.value = 'todas'
                kanban_area.refresh()

            # Monta opções de responsáveis a partir dos entregáveis carregados
            def get_responsaveis_opcoes():
                """Retorna dict de responsáveis únicos dos entregáveis."""
                opcoes = {'todos': 'Todos'}
                for e in entregaveis_data['lista']:
                    resp_id = e.get('responsavel_id', '')
                    resp_nome = e.get('responsavel_nome', 'Sem nome')
                    if resp_id and resp_id not in opcoes:
                        opcoes[resp_id] = resp_nome
                return opcoes

            with ui.row().classes('w-full items-center gap-4 mb-4 flex-wrap'):
                ui.label('Filtros:').classes('text-sm font-medium text-gray-700')

                # Filtro de Prioridade (apenas códigos P1, P2, P3, P4)
                filtro_prioridade_select = ui.select(
                    options={
                        'todas': 'Todas',
                        'P1': 'P1',
                        'P2': 'P2',
                        'P3': 'P3',
                        'P4': 'P4',
                    },
                    label='Prioridade',
                    value='todas',
                    on_change=lambda e: aplicar_filtro_prioridade(e.value)
                ).classes('w-36').props('dense outlined')

                # Filtro de Responsável
                filtro_responsavel_select = ui.select(
                    options=get_responsaveis_opcoes(),
                    label='Responsável',
                    value='todos',
                    on_change=lambda e: aplicar_filtro_responsavel(e.value)
                ).classes('w-48').props('dense outlined')

                # Filtro de Categoria (só aparece na visualização por status)
                # Cria opções: "Todas" + categorias existentes
                categoria_opcoes = {'todas': 'Todas'}
                for cat in CATEGORIAS_OPCOES:
                    categoria_opcoes[cat] = cat

                filtro_categoria_select = ui.select(
                    options=categoria_opcoes,
                    label='Categoria',
                    value='todas',
                    on_change=lambda e: aplicar_filtro_categoria(e.value)
                ).classes('w-40').props('dense outlined')
                # Esconde filtro de categoria quando não estiver em visualização por status
                filtro_categoria_select.bind_visibility_from(
                    visualizacao,
                    'tipo',
                    backward=lambda t: t == 'status'
                )

                # Botão Limpar Filtros
                ui.button(icon='refresh', on_click=limpar_filtros).props('flat dense').tooltip('Limpar filtros').style('color: #6B7280;')
            
            def processar_drop(coluna_destino: str):
                """Processa o drop de um card em uma coluna."""
                entregavel_id = drag_state.get('dragging_id')
                coluna_origem = drag_state.get('source_column')
                tipo = visualizacao['tipo']

                # Limpa estado do drag
                drag_state['dragging_id'] = None
                drag_state['source_column'] = None

                # Verifica se tem dados válidos
                if not entregavel_id:
                    print("[DROP] Nenhum entregável sendo arrastado")
                    return

                # Verifica se mudou de coluna
                if coluna_origem == coluna_destino:
                    print(f"[DROP] Mesma coluna, ignorando: {coluna_destino}")
                    return

                print(f"[DROP] Movendo {entregavel_id} de '{coluna_origem}' para '{coluna_destino}'")

                try:
                    if tipo == 'status':
                        sucesso = atualizar_status(entregavel_id, coluna_destino)
                        if sucesso:
                            ui.notify(f'Movido para "{coluna_destino}"', type='positive')
                        else:
                            ui.notify('Erro ao atualizar status', type='negative')
                    else:
                        sucesso = atualizar_categoria(entregavel_id, coluna_destino)
                        if sucesso:
                            ui.notify(f'Categoria atualizada para "{coluna_destino}"', type='positive')
                        else:
                            ui.notify('Erro ao atualizar categoria', type='negative')

                    # Recarrega dados
                    carregar_entregaveis()

                except Exception as e:
                    print(f"[DROP] Erro: {e}")
                    ui.notify(f'Erro ao mover entregável: {str(e)}', type='negative')
            
            # Adiciona CSS customizado para drag & drop e botão delete
            ui.add_head_html('''
        <style>
            /* Cards arrastáveis - cursor pointer para clique */
            .draggable-card {
                user-select: none;
                transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
            }
            .draggable-card:hover {
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            .draggable-card:active {
                opacity: 0.7;
            }

            /* Drop zone visual */
            .drop-zone {
                min-height: 300px;
                transition: background-color 0.2s ease;
                border: 2px dashed transparent;
            }
            .drop-zone.drag-over {
                background-color: rgba(59, 130, 246, 0.15);
                border-color: rgba(59, 130, 246, 0.5);
            }

            /* Cards não expandem além da coluna */
            .nicegui-card {
                max-width: 100%;
                box-sizing: border-box;
            }

            /* Botão delete - hover vermelho */
            .hover-red:hover {
                color: #DC2626 !important;
            }

            /* Scroll horizontal */
            .overflow-x-auto::-webkit-scrollbar {
                height: 8px;
            }
            .overflow-x-auto::-webkit-scrollbar-track {
                background: #E5E7EB;
                border-radius: 4px;
            }
            .overflow-x-auto::-webkit-scrollbar-thumb {
                background: #9CA3AF;
                border-radius: 4px;
            }
            .overflow-x-auto::-webkit-scrollbar-thumb:hover {
                background: #6B7280;
            }
        </style>
            ''')
            
            # Área do Kanban
            @ui.refreshable
            def kanban_area():
                tipo = visualizacao['tipo']
                entregaveis_lista = entregaveis_data['lista']

                # =========================================================
                # APLICAR FILTROS (prioridade, responsável e categoria)
                # =========================================================
                lista_filtrada = entregaveis_lista

                # Filtro por prioridade
                if filtros['prioridade']:
                    lista_filtrada = [
                        e for e in lista_filtrada
                        if e.get('prioridade', 'P4') == filtros['prioridade']
                    ]

                # Filtro por responsável
                if filtros['responsavel_id']:
                    lista_filtrada = [
                        e for e in lista_filtrada
                        if e.get('responsavel_id', '') == filtros['responsavel_id']
                    ]

                # Filtro por categoria (só ativo na visualização por status)
                if tipo == 'status' and filtros['categoria']:
                    lista_filtrada = [
                        e for e in lista_filtrada
                        if e.get('categoria', 'Operacional') == filtros['categoria']
                    ]

                if tipo == 'status':
                    colunas = STATUS_OPCOES
                else:
                    colunas = CATEGORIAS_OPCOES

                with ui.row().classes('w-full gap-4 overflow-x-auto pb-4'):
                    for coluna_nome in colunas:
                        # Filtra entregáveis desta coluna (normaliza status antigos)
                        if tipo == 'status':
                            entregaveis_coluna = [
                                e for e in lista_filtrada
                                if normalizar_status(e.get('status', '')) == coluna_nome
                            ]
                        else:
                            entregaveis_coluna = [e for e in lista_filtrada if e.get('categoria') == coluna_nome]

                        # Ordenar por prioridade (P1 primeiro, P4 por último)
                        entregaveis_coluna = ordenar_por_prioridade(entregaveis_coluna)

                        qtd = len(entregaveis_coluna)

                        # Obtém cores da coluna (apenas para visualização por status)
                        if tipo == 'status' and coluna_nome in CORES_STATUS:
                            cores = CORES_STATUS[coluna_nome]
                            cor_fundo = cores['bg']
                            cor_header = cores['header']
                            cor_texto = cores['text']
                        else:
                            cor_fundo = '#F3F4F6'   # cinza padrão
                            cor_header = '#6B7280'  # cinza
                            cor_texto = '#374151'   # cinza escuro

                        # COLUNA COM COR
                        with ui.column().style(f'''
                            width: {LARGURA_COLUNA}px;
                            min-width: {LARGURA_COLUNA}px;
                            max-width: {LARGURA_COLUNA}px;
                            flex-shrink: 0;
                            background-color: {cor_fundo};
                            border-radius: 8px;
                            border-top: 3px solid {cor_header};
                        '''):

                            # HEADER DA COLUNA
                            with ui.row().style(f'''
                                width: 100%;
                                padding: 12px;
                                border-bottom: 1px solid rgba(0,0,0,0.05);
                            ''').classes('items-center justify-between'):
                                ui.label(coluna_nome).style(f'''
                                    font-size: 12px;
                                    font-weight: 700;
                                    color: {cor_texto};
                                    text-transform: uppercase;
                                    letter-spacing: 0.5px;
                                ''')
                                ui.badge(str(qtd)).style(f'''
                                    background-color: {cor_header} !important;
                                    color: white !important;
                                ''').props('rounded')

                            # CONTAINER DE CARDS (DROP ZONE)
                            with ui.column().style(f'''
                                width: 100%;
                                max-width: {LARGURA_COLUNA}px;
                                overflow: hidden;
                                min-height: 300px;
                                padding: 8px;
                            ''').classes('flex flex-col gap-2 drop-zone') as drop_zone:

                                # Eventos de drop na coluna
                                def criar_handler_drop(destino):
                                    """Cria handler de drop para a coluna."""
                                    def on_drop(e):
                                        processar_drop(destino)
                                    return on_drop

                                # Registra eventos de drag over e drop
                                drop_zone.on('dragover.prevent', lambda e: None)
                                drop_zone.on('drop', criar_handler_drop(coluna_nome))

                                # Renderiza cards
                                if entregaveis_coluna:
                                    for entregavel in entregaveis_coluna:
                                        criar_card_entregavel(entregavel, coluna_atual=coluna_nome)
                                else:
                                    with ui.column().classes('w-full items-center justify-center py-8'):
                                        ui.icon('inbox', size='32px').style(f'color: {cor_header}; opacity: 0.3;')
                                        ui.label('Nenhum entregável').style(f'font-size: 11px; color: {cor_texto}; opacity: 0.5; margin-top: 8px;')

                # JavaScript para feedback visual durante arrasto
                ui.run_javascript('''
                    document.querySelectorAll('.drop-zone').forEach(zone => {
                        zone.addEventListener('dragenter', e => {
                            e.preventDefault();
                            zone.classList.add('drag-over');
                        });
                        zone.addEventListener('dragleave', e => {
                            zone.classList.remove('drag-over');
                        });
                        zone.addEventListener('drop', e => {
                            zone.classList.remove('drag-over');
                        });
                    });
                ''')

            kanban_area()
            
            # Modal de criação/edição
            with ui.dialog() as modal_entregavel, ui.card().classes('w-full max-w-lg p-6'):
                # Salva referência do modal no estado compartilhado
                modal_state['modal'] = modal_entregavel

                # Título dinâmico do modal
                titulo_modal = ui.label('Novo Entregável').classes('text-xl font-bold mb-4 text-primary')
                modal_state['titulo_modal'] = titulo_modal

                # Campos do formulário
                titulo_input = ui.input('Título *', placeholder='Digite o título do entregável').classes('w-full mb-3')
                modal_state['titulo_input'] = titulo_input
                
                # Responsável - busca do Firebase Auth
                ensure_firebase_initialized()
                auth_instance = get_auth()
                usuarios = []

                try:
                    page = auth_instance.list_users()
                    while page:
                        for user in page.users:
                            usuarios.append({
                                '_id': user.uid,
                                'name': user.display_name or (user.email.split('@')[0] if user.email else 'Sem nome'),
                                'email': user.email or '',
                            })
                        try:
                            page = page.get_next_page()
                        except (StopIteration, Exception):
                            break
                except Exception as e:
                    print(f"[ENTREGAVEIS] Erro ao buscar usuários do Firebase Auth: {e}")
                    usuarios = []

                responsavel_options = {}
                for u in usuarios:
                    nome = u.get('name', 'Sem nome')
                    email = u.get('email', '')
                    u_id = u.get('_id', nome)
                    display = f"{nome} ({email})" if email else nome
                    responsavel_options[u_id] = display

                if not responsavel_options:
                    responsavel_options = {'-': 'Nenhum usuário cadastrado'}

                # Salva no estado compartilhado para uso em salvar_entregavel()
                responsavel_options_state['opcoes'] = responsavel_options

                responsavel_select = ui.select(
                    options=responsavel_options,
                    label='Responsável *',
                    with_input=True
                ).classes('w-full mb-3')
                modal_state['responsavel_select'] = responsavel_select

                # Categoria
                categoria_select = ui.select(
                    options={c: c for c in CATEGORIAS_OPCOES},
                    label='Categoria',
                    value='Operacional'
                ).classes('w-full mb-3')
                modal_state['categoria_select'] = categoria_select

                # Status
                status_select = ui.select(
                    options={s: s for s in STATUS_OPCOES},
                    label='Status',
                    value=STATUS_PADRAO  # 'Em espera'
                ).classes('w-full mb-3')
                modal_state['status_select'] = status_select

                # Prioridade
                prioridade_options = {p: p for p in CODIGOS_PRIORIDADE}
                prioridade_select = ui.select(
                    options=prioridade_options,
                    label='Prioridade',
                    value='P4'
                ).classes('w-full mb-3')
                modal_state['prioridade_select'] = prioridade_select

                # Prazo (formato DD/MM/AAAA)
                ui.label('Prazo').classes('text-sm font-medium text-gray-700')
                prazo_input = ui.input(
                    placeholder='DD/MM/AAAA'
                ).classes('w-full mb-3').props('mask="##/##/####"')
                modal_state['prazo_input'] = prazo_input

                # Link no Slack (opcional)
                with ui.row().classes('w-full items-center gap-2 mb-3'):
                    ui.icon('link').style('color: #4A154B;')  # Cor do Slack
                    slack_link_input = ui.input(
                        label='Link no Slack',
                        placeholder='Cole o link da mensagem do Slack'
                    ).props('clearable').classes('w-full flex-grow')
                    modal_state['slack_link_input'] = slack_link_input

                # Botões - container para permitir botão excluir à esquerda
                with ui.row().classes('w-full justify-between items-center mt-4'):
                    # Botão excluir (apenas na edição, à esquerda)
                    excluir_btn_container = ui.row().classes('gap-2')
                    
                    # Botões à direita (Cancelar e Salvar)
                    with ui.row().classes('gap-2'):
                        ui.button('Cancelar', on_click=modal_entregavel.close).props('flat')
                        ui.button('Salvar', on_click=salvar_entregavel).props('color=primary')
                
                # Função para atualizar botão excluir
                def atualizar_botao_excluir():
                    """Atualiza visibilidade do botão excluir."""
                    excluir_btn_container.clear()
                    if hasattr(modal_entregavel, '_modo_edicao') and modal_entregavel._modo_edicao:
                        ui.button('Excluir', on_click=confirmar_exclusao, icon='delete').props('color=negative flat')
                
                # Atualiza botão quando modal abrir
                def ao_abrir_modal():
                    atualizar_botao_excluir()
                
                modal_entregavel.on('open', ao_abrir_modal)

            # Carrega dados iniciais
            carregar_entregaveis()
            print("[ENTREGAVEIS] Página renderizada com sucesso")
        
    except Exception as e:
        import traceback
        error_msg = f"Erro ao carregar página de entregáveis: {e}"
        print(error_msg)
        traceback.print_exc()
        
        # Tenta mostrar erro na página mesmo sem layout completo
        try:
            with layout('Erro - Entregáveis', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Entregáveis', None)]):
                ui.label('Erro ao carregar página').classes('text-red-500 text-xl font-bold')
                ui.label(str(e)).classes('text-red-600 mt-2')
                ui.label('Verifique o console do servidor para mais detalhes.').classes('text-gray-500 mt-4')
                ui.button('Voltar', on_click=lambda: ui.navigate.to('/visao-geral/painel')).classes('mt-4')
        except:
            # Se até o layout falhar, mostra erro básico
            ui.label(f'Erro crítico: {str(e)}').classes('text-red-500 p-4')

