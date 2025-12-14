"""
Página principal do módulo de Entregáveis com visualização Kanban.

Permite visualizar entregáveis por status ou categoria, com drag & drop.
"""

from datetime import datetime
from nicegui import ui
from ...core import layout, get_users_list
from ...auth import is_authenticated, get_current_user
from ...middlewares.verificar_workspace import verificar_e_definir_workspace_automatico
from ...models.entregavel import (
    STATUS_OPCOES,
    CATEGORIAS_OPCOES,
    get_cor_prioridade_entregavel,
    CORES_PRIORIDADE
)
from ...models.prioridade import CODIGOS_PRIORIDADE
from ...services.entregavel_service import (
    listar_entregaveis,
    criar_entregavel,
    atualizar_entregavel,
    atualizar_status,
    atualizar_categoria,
    excluir_entregavel,
    buscar_entregavel_por_id,
    invalidar_cache
)


@ui.page('/visao-geral/entregaveis')
def entregaveis():
    """Página principal de Entregáveis com visualização Kanban."""
    # Debug: verifica se a função está sendo chamada
    print("[ENTREGAVEIS] Função entregaveis() chamada")
    
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        # Verifica e define workspace automaticamente
        workspace_ok = verificar_e_definir_workspace_automatico()
        if not workspace_ok:
            # Se não tem permissão, a função já redirecionou
            print("[ENTREGAVEIS] Workspace não autorizado")
            return
        
        print("[ENTREGAVEIS] Iniciando renderização da página")
        
        # Estado da visualização (por status ou categoria)
        visualizacao = {'tipo': 'status'}  # 'status' ou 'categoria'
        
        # Estado dos entregáveis
        entregaveis_data = {'lista': []}
        
        def carregar_entregaveis():
            """Carrega entregáveis do Firestore."""
            entregaveis_data['lista'] = listar_entregaveis()
            kanban_area.refresh()
        
        def criar_card_entregavel(entregavel: dict):
            """Cria um card visual para um entregável."""
            entregavel_id = entregavel.get('_id', '')
            titulo = entregavel.get('titulo', 'Sem título')
            prioridade = entregavel.get('prioridade', 'P4')
            responsavel_nome = entregavel.get('responsavel_nome', 'Sem responsável')
            prazo = entregavel.get('prazo')
            
            # Cor da prioridade
            cor_prioridade = get_cor_prioridade_entregavel(prioridade)
            
            # Verifica se prazo está vencido ou próximo
            prazo_status = None
            prazo_texto = ''
            if prazo:
                try:
                    if isinstance(prazo, (int, float)):
                        prazo_dt = datetime.fromtimestamp(prazo)
                    else:
                        prazo_dt = prazo
                    
                    hoje = datetime.now()
                    dias_restantes = (prazo_dt - hoje).days
                    
                    if dias_restantes < 0:
                        prazo_status = 'vencido'
                        prazo_texto = f"Vencido há {abs(dias_restantes)} dias"
                    elif dias_restantes <= 3:
                        prazo_status = 'proximo'
                        prazo_texto = f"Vence em {dias_restantes} dias"
                    else:
                        prazo_status = 'ok'
                        prazo_texto = f"Vence em {dias_restantes} dias"
                except:
                    prazo_texto = 'Prazo inválido'
            
            with ui.card().classes('w-full p-3 cursor-move hover:shadow-md transition-shadow mb-2 draggable-card') as card:
                # Adiciona atributo data para drag & drop
                card.props(f'data-entregavel-id="{entregavel_id}"')
                
                # Badge de prioridade
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label(prioridade).classes('text-xs font-bold px-2 py-1 rounded').style(f'background-color: {cor_prioridade}; color: white;')
                    if prazo_status == 'vencido':
                        ui.icon('warning', size='sm').classes('text-red-500')
                    elif prazo_status == 'proximo':
                        ui.icon('schedule', size='sm').classes('text-orange-500')
                
                # Título
                ui.label(titulo).classes('text-sm font-semibold text-gray-800 mb-2')
                
                # Responsável
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    ui.icon('person', size='xs').classes('text-gray-500')
                    ui.label(responsavel_nome).classes('text-xs text-gray-600')
                
                # Prazo
                if prazo_texto:
                    cor_prazo = 'text-red-600' if prazo_status == 'vencido' else ('text-orange-600' if prazo_status == 'proximo' else 'text-gray-600')
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.icon('event', size='xs').classes('text-gray-500')
                        ui.label(prazo_texto).classes(f'text-xs {cor_prazo}')
                
                # Adiciona atributo para drag & drop
                card._entregavel_id = entregavel_id
                card._entregavel_data = entregavel
                
                # Clique no card abre modal de edição
                def abrir_edicao():
                    abrir_modal_edicao(entregavel_id)
                
                card.on('click', abrir_edicao)
            
            return card
        
        def abrir_modal_criacao():
            """Abre modal para criar novo entregável."""
            modal_entregavel.open()
            # Limpa campos
            titulo_input.value = ''
            responsavel_select.value = None
            categoria_select.value = 'Operacional'
            status_select.value = 'Pendente'
            prioridade_select.value = 'P4'
            prazo_input.value = None
            modal_entregavel._modo_edicao = False
            modal_entregavel._entregavel_id = None
        
        def abrir_modal_edicao(entregavel_id: str):
            """Abre modal para editar entregável existente."""
            entregavel = buscar_entregavel_por_id(entregavel_id)
            if not entregavel:
                ui.notify('Entregável não encontrado', type='negative')
                return
            
            modal_entregavel.open()
            modal_entregavel._modo_edicao = True
            modal_entregavel._entregavel_id = entregavel_id
            
            # Preenche campos
            titulo_input.value = entregavel.get('titulo', '')
            responsavel_select.value = entregavel.get('responsavel_id', '')
            categoria_select.value = entregavel.get('categoria', 'Operacional')
            status_select.value = entregavel.get('status', 'Pendente')
            prioridade_select.value = entregavel.get('prioridade', 'P4')
            
            # Prazo
            prazo_val = entregavel.get('prazo')
            if prazo_val:
                try:
                    if isinstance(prazo_val, (int, float)):
                        prazo_dt = datetime.fromtimestamp(prazo_val)
                    else:
                        prazo_dt = prazo_val
                    prazo_input.value = prazo_dt.strftime('%Y-%m-%d')
                except:
                    prazo_input.value = None
            else:
                prazo_input.value = None
        
        def salvar_entregavel():
            """Salva ou atualiza entregável."""
            # Validações
            if not titulo_input.value or not titulo_input.value.strip():
                ui.notify('Título é obrigatório', type='warning')
                return
            
            if not responsavel_select.value:
                ui.notify('Responsável é obrigatório', type='warning')
                return
            
            # Busca dados do responsável
            usuarios = get_users_list()
            responsavel_obj = next((u for u in usuarios if u.get('_id') == responsavel_select.value), None)
            if not responsavel_obj:
                ui.notify('Responsável não encontrado', type='negative')
                return
            
            responsavel_nome = responsavel_obj.get('name') or responsavel_obj.get('full_name') or responsavel_obj.get('email', 'Sem nome')
            
            # Prepara dados
            dados = {
                'titulo': titulo_input.value.strip(),
                'responsavel_id': responsavel_select.value,
                'responsavel_nome': responsavel_nome,
                'categoria': categoria_select.value,
                'status': status_select.value,
                'prioridade': prioridade_select.value,
            }
            
            # Prazo
            if prazo_input.value:
                try:
                    prazo_dt = datetime.strptime(prazo_input.value, '%Y-%m-%d')
                    dados['prazo'] = prazo_dt.timestamp()
                except:
                    pass
            
            try:
                if modal_entregavel._modo_edicao and modal_entregavel._entregavel_id:
                    # Atualizar
                    atualizar_entregavel(modal_entregavel._entregavel_id, dados)
                    ui.notify('Entregável atualizado com sucesso!', type='positive')
                else:
                    # Criar
                    user = get_current_user()
                    if user:
                        dados['criado_por'] = user.get('uid', '')
                    criar_entregavel(dados)
                    ui.notify('Entregável criado com sucesso!', type='positive')
                
                modal_entregavel.close()
                carregar_entregaveis()
            except Exception as e:
                ui.notify(f'Erro ao salvar entregável: {str(e)}', type='negative')
        
        def excluir_entregavel_confirmado():
            """Exclui entregável após confirmação."""
            if not modal_entregavel._modo_edicao or not modal_entregavel._entregavel_id:
                return
            
            entregavel_id = modal_entregavel._entregavel_id
            
            try:
                excluir_entregavel(entregavel_id)
                ui.notify('Entregável excluído com sucesso!', type='positive')
                modal_entregavel.close()
                carregar_entregaveis()
            except Exception as e:
                ui.notify(f'Erro ao excluir entregável: {str(e)}', type='negative')
        
        def confirmar_exclusao():
            """Confirma exclusão do entregável."""
            ui.dialog().props('persistent').open()
            with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md p-6'):
                ui.label('Confirmar exclusão').classes('text-xl font-bold mb-4 text-red-600')
                ui.label('Tem certeza que deseja excluir este entregável? Esta ação não pode ser desfeita.').classes('mb-4')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancelar', on_click=dialog_excluir.close).props('flat')
                    ui.button('Excluir', on_click=lambda: [dialog_excluir.close(), excluir_entregavel_confirmado()]).props('color=red')
        
        with layout('Entregáveis', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Entregáveis', None)]):
            # Header (título removido - já vem do layout())
            with ui.row().classes('w-full items-center justify-end mb-4'):
                ui.button('+ Novo Entregável', icon='add', on_click=abrir_modal_criacao).classes('bg-primary text-white')
            
            # Toggle de visualização
            with ui.row().classes('w-full items-center gap-4 mb-4'):
                ui.label('Visualização:').classes('text-sm font-medium text-gray-700')
                ui.button('Por Status', on_click=lambda: [visualizacao.update({'tipo': 'status'}), kanban_area.refresh()]).props(f"color={'primary' if visualizacao['tipo'] == 'status' else 'grey'}")
                ui.button('Por Categoria', on_click=lambda: [visualizacao.update({'tipo': 'categoria'}), kanban_area.refresh()]).props(f"color={'primary' if visualizacao['tipo'] == 'categoria' else 'grey'}")
            
            # Elemento oculto para comunicação JavaScript-Python
            drop_event_element = ui.label('').classes('hidden').props('id=drop-event-handler')
            
            def handle_drop(entregavel_id: str, nova_coluna: str):
                """Handle quando um card é solto em uma nova coluna."""
                tipo = visualizacao['tipo']
                
                try:
                    if tipo == 'status':
                        # Atualiza status
                        atualizar_status(entregavel_id, nova_coluna)
                        ui.notify(f'Status atualizado para "{nova_coluna}"', type='positive')
                    else:
                        # Atualiza categoria
                        atualizar_categoria(entregavel_id, nova_coluna)
                        ui.notify(f'Categoria atualizada para "{nova_coluna}"', type='positive')
                    
                    # Recarrega dados
                    carregar_entregaveis()
                except Exception as e:
                    ui.notify(f'Erro ao atualizar entregável: {str(e)}', type='negative')
            
            # Adiciona JavaScript para drag & drop
            ui.add_head_html('''
        <style>
            .draggable-card {
                user-select: none;
            }
            .draggable-card:active {
                opacity: 0.5;
            }
            .drop-zone {
                min-height: 200px;
                transition: background-color 0.2s;
            }
            .drop-zone.drag-over {
                background-color: rgba(59, 130, 246, 0.1);
            }
        </style>
            ''')
            
            # Área do Kanban
            @ui.refreshable
            def kanban_area():
                tipo = visualizacao['tipo']
                entregaveis_lista = entregaveis_data['lista']
                
                if tipo == 'status':
                    # Visualização por Status (4 colunas)
                    colunas = STATUS_OPCOES
                else:
                    # Visualização por Categoria (5 colunas)
                    colunas = CATEGORIAS_OPCOES
                
                with ui.row().classes('w-full gap-4 overflow-x-auto'):
                    for coluna_nome in colunas:
                        with ui.column().classes('flex flex-col gap-2 min-w-[280px]') as col:
                            # Header da coluna
                            with ui.card().classes('w-full p-3 bg-gray-100'):
                                ui.label(coluna_nome).classes('text-sm font-semibold text-gray-700')
                            
                            # Cards da coluna (drop zone)
                            cards_container_id = f'drop-zone-{coluna_nome.replace(" ", "-").lower()}'
                            with ui.column().classes('flex flex-col gap-2 min-h-[200px] drop-zone').props(f'id="{cards_container_id}" data-coluna-nome="{coluna_nome}"') as cards_container:
                                # Filtra entregáveis da coluna
                                if tipo == 'status':
                                    entregaveis_coluna = [e for e in entregaveis_lista if e.get('status') == coluna_nome]
                                else:
                                    entregaveis_coluna = [e for e in entregaveis_lista if e.get('categoria') == coluna_nome]
                                
                                # Renderiza cards
                                for entregavel in entregaveis_coluna:
                                    criar_card_entregavel(entregavel)
                                
                                # Se vazio, mostra mensagem
                                if not entregaveis_coluna:
                                    ui.label('Nenhum entregável').classes('text-xs text-gray-400 text-center py-8')
                
                # Configura drag & drop após renderizar
                ui.run_javascript('''
            (function() {
                setTimeout(function() {
                    // Configura cards arrastáveis
                    document.querySelectorAll('.draggable-card').forEach(function(card) {
                        card.draggable = true;
                        
                        card.addEventListener('dragstart', function(e) {
                            e.dataTransfer.effectAllowed = 'move';
                            const entregavelId = card.getAttribute('data-entregavel-id');
                            e.dataTransfer.setData('text/plain', entregavelId);
                            card.style.opacity = '0.5';
                        });
                        
                        card.addEventListener('dragend', function(e) {
                            card.style.opacity = '1';
                        });
                    });
                    
                    // Configura zonas de drop (colunas)
                    document.querySelectorAll('.drop-zone').forEach(function(zone) {
                        zone.addEventListener('dragover', function(e) {
                            e.preventDefault();
                            e.dataTransfer.dropEffect = 'move';
                            zone.classList.add('drag-over');
                        });
                        
                        zone.addEventListener('dragleave', function(e) {
                            zone.classList.remove('drag-over');
                        });
                        
                        zone.addEventListener('drop', function(e) {
                            e.preventDefault();
                            zone.classList.remove('drag-over');
                            
                            const entregavelId = e.dataTransfer.getData('text/plain');
                            const colunaNome = zone.getAttribute('data-coluna-nome');
                            
                            if (entregavelId && colunaNome) {
                                // Atualiza elemento oculto para trigger Python
                                const handler = document.getElementById('drop-event-handler');
                                if (handler) {
                                    handler.textContent = entregavelId + '|' + colunaNome;
                                    handler.dispatchEvent(new Event('change'));
                                }
                            }
                        });
                    });
                }, 100);
            })();
                ''')
            
            # Timer para verificar mudanças no elemento de drop
            def verificar_drop():
                """Verifica se houve um drop e processa."""
                texto = drop_event_element.text
                if texto and '|' in texto:
                    partes = texto.split('|')
                    if len(partes) == 2:
                        entregavel_id, coluna_nome = partes
                        drop_event_element.text = ''  # Limpa
                        handle_drop(entregavel_id, coluna_nome)
            
            ui.timer(0.5, verificar_drop)
            
            kanban_area()
            
            # Modal de criação/edição
            with ui.dialog() as modal_entregavel, ui.card().classes('w-full max-w-lg p-6'):
                ui.label('Novo Entregável').classes('text-xl font-bold mb-4 text-primary')
                
                # Campos do formulário
                titulo_input = ui.input('Título *', placeholder='Digite o título do entregável').classes('w-full mb-3')
                
                # Responsável
                usuarios = get_users_list()
                responsavel_options = {}
                for u in usuarios:
                    nome = u.get('name') or u.get('full_name') or u.get('email', 'Sem nome')
                    email = u.get('email', '')
                    u_id = u.get('_id', nome)
                    display = f"{nome} ({email})" if email else nome
                    responsavel_options[u_id] = display
                
                if not responsavel_options:
                    responsavel_options = {'-': 'Nenhum usuário cadastrado'}
                
                responsavel_select = ui.select(
                    options=responsavel_options,
                    label='Responsável *',
                    with_input=True
                ).classes('w-full mb-3')
                
                # Categoria
                categoria_select = ui.select(
                    options={c: c for c in CATEGORIAS_OPCOES},
                    label='Categoria',
                    value='Operacional'
                ).classes('w-full mb-3')
                
                # Status
                status_select = ui.select(
                    options={s: s for s in STATUS_OPCOES},
                    label='Status',
                    value='Pendente'
                ).classes('w-full mb-3')
                
                # Prioridade
                prioridade_options = {p: p for p in CODIGOS_PRIORIDADE}
                prioridade_select = ui.select(
                    options=prioridade_options,
                    label='Prioridade',
                    value='P4'
                ).classes('w-full mb-3')
                
                # Prazo
                prazo_input = ui.date('Prazo', value=None).classes('w-full mb-3')
                
                # Botões
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=modal_entregavel.close).props('flat')
                    
                    # Botão excluir (apenas na edição)
                    @ui.refreshable
                    def botoes_modal():
                        if hasattr(modal_entregavel, '_modo_edicao') and modal_entregavel._modo_edicao:
                            ui.button('Excluir', on_click=confirmar_exclusao).props('color=red flat')
                    
                    botoes_modal()
                    ui.button('Salvar', on_click=salvar_entregavel).props('color=primary')
            
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

