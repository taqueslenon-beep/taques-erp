"""
acordos_page.py - Página de Acordos.

Visualização simples em tabela dos acordos cadastrados.
"""

from datetime import datetime
from typing import List, Dict, Any
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated
from .modais import render_acordo_dialog
from .database import buscar_todos_os_acordos, invalidar_cache_acordos, salvar_acordo, buscar_acordo_por_id


def formatar_data(data: Any) -> str:
    """
    Formata data para exibição no padrão DD/MM/YYYY.
    
    Args:
        data: Pode ser string (YYYY-MM-DD), timestamp, ou objeto datetime
    
    Returns:
        String formatada ou '-' se inválida
    """
    if not data:
        return '-'
    
    try:
        # Se for string no formato YYYY-MM-DD
        if isinstance(data, str) and len(data) >= 10:
            if '-' in data:
                dt = datetime.strptime(data[:10], '%Y-%m-%d')
                return dt.strftime('%d/%m/%Y')
            # Se já estiver em formato brasileiro
            if '/' in data:
                return data
        
        # Se for timestamp (número)
        if isinstance(data, (int, float)):
            dt = datetime.fromtimestamp(data)
            return dt.strftime('%d/%m/%Y')
        
        # Se for objeto datetime
        if isinstance(data, datetime):
            return data.strftime('%d/%m/%Y')
        
        return str(data)
    except Exception:
        return '-'


def formatar_partes_envolvidas(acordo: Dict[str, Any]) -> str:
    """
    Formata lista de partes envolvidas para exibição.
    
    Args:
        acordo: Dicionário com dados do acordo
    
    Returns:
        String com partes separadas por vírgula ou '-'
    """
    partes = []
    
    # Tenta diferentes campos possíveis
    if acordo.get('partes_envolvidas'):
        if isinstance(acordo['partes_envolvidas'], list):
            partes.extend([str(p) for p in acordo['partes_envolvidas']])
        else:
            partes.append(str(acordo['partes_envolvidas']))
    
    if acordo.get('clientes'):
        if isinstance(acordo['clientes'], list):
            for cliente in acordo['clientes']:
                if isinstance(cliente, dict):
                    nome = cliente.get('title') or cliente.get('name') or cliente.get('display_name', '')
                    if nome:
                        partes.append(nome)
                else:
                    partes.append(str(cliente))
        else:
            partes.append(str(acordo['clientes']))
    
    if acordo.get('partes_contrarias'):
        if isinstance(acordo['partes_contrarias'], list):
            for parte in acordo['partes_contrarias']:
                if isinstance(parte, dict):
                    nome = parte.get('title') or parte.get('name') or parte.get('display_name', '')
                    if nome:
                        partes.append(nome)
                else:
                    partes.append(str(parte))
        else:
            partes.append(str(acordo['partes_contrarias']))
    
    # Remove duplicatas mantendo ordem
    partes_unicas = []
    for p in partes:
        if p and p not in partes_unicas:
            partes_unicas.append(p)
    
    if partes_unicas:
        # Limita a 2 partes para não ficar muito longo
        if len(partes_unicas) > 2:
            return f"{', '.join(partes_unicas[:2])}..."
        return ', '.join(partes_unicas)
    
    return '-'


def obter_cor_status(status: str) -> str:
    """
    Retorna cor do badge baseado no status.
    
    Args:
        status: Status do acordo
    
    Returns:
        Nome da cor para o badge
    """
    status_lower = (status or '').lower()
    
    if 'ativo' in status_lower or 'andamento' in status_lower or 'em andamento' in status_lower:
        return 'green'
    elif 'concluído' in status_lower or 'concluido' in status_lower or 'finalizado' in status_lower:
        return 'grey'
    elif 'rescindido' in status_lower or 'cancelado' in status_lower:
        return 'red'
    elif 'assinado' in status_lower:
        return 'teal'
    elif 'negociação' in status_lower or 'negociacao' in status_lower:
        return 'orange'
    else:
        return 'blue'


@ui.page('/acordos')
def acordos():
    """Página de Acordos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Criar dialog para novo acordo
    def on_acordo_salvo(acordo_data: Dict[str, Any]):
        """Callback executado após salvar acordo."""
        try:
            acordo_id = acordo_data.get('_id')
            salvar_acordo(acordo_data, acordo_id=acordo_id)
            invalidar_cache_acordos()
            render_tabela.refresh()
        except Exception as e:
            print(f"[ERROR] Erro ao salvar acordo: {e}")
            ui.notify('Erro ao salvar acordo no Firestore. Tente novamente.', type='negative')
    
    dialog_novo, open_dialog_novo = render_acordo_dialog(on_success=on_acordo_salvo)
    
    # Função para abrir modal de edição
    def abrir_modal_edicao(acordo_id: str):
        """Abre modal de edição com dados do acordo."""
        try:
            acordo = buscar_acordo_por_id(acordo_id)
            if not acordo:
                ui.notify('Acordo não encontrado!', type='negative')
                return
            
            # Criar dialog de edição
            dialog_edit, open_edit = render_acordo_dialog(
                on_success=on_acordo_salvo,
                acordo_inicial=acordo
            )
            open_edit()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir modal de edição: {e}")
            ui.notify('Erro ao carregar dados do acordo. Tente novamente.', type='negative')
    
    with layout('Acordos', breadcrumbs=[('Acordos', None)]):
        # Header com botão e busca
        with ui.row().classes('w-full gap-4 mb-6 items-center flex-wrap'):
            ui.button('+ NOVO ACORDO', on_click=open_dialog_novo).props(
                'color=primary'
            ).classes('font-bold')
            
            # Campo de busca
            busca_input = ui.input(
                label='Pesquisar acordos por título, número...',
                placeholder='Digite para buscar'
            ).classes('flex-grow min-w-64').props('outlined dense clearable')
        
        # Container para tabela
        tabela_container = ui.column().classes('w-full')
        
        @ui.refreshable
        def render_tabela():
            """Renderiza tabela de acordos."""
            tabela_container.clear()
            
            with tabela_container:
                try:
                    # Buscar acordos
                    acordos_lista = buscar_todos_os_acordos()
                    
                    if not acordos_lista:
                        # Mensagem quando não há acordos
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('handshake', size='48px').classes('text-gray-300 mb-4')
                            ui.label('Nenhum acordo cadastrado').classes(
                                'text-gray-500 text-lg font-medium mb-2'
                            )
                            ui.label('Clique em "+ NOVO ACORDO" para criar o primeiro').classes(
                                'text-sm text-gray-400 text-center'
                            )
                        return
                    
                    # Filtrar por busca se houver texto
                    texto_busca = (busca_input.value or '').lower().strip()
                    acordos_filtrados = acordos_lista
                    
                    if texto_busca:
                        acordos_filtrados = [
                            a for a in acordos_lista
                            if texto_busca in (a.get('titulo') or '').lower()
                            or texto_busca in (a.get('title') or '').lower()
                            or texto_busca in (a.get('numero') or '').lower()
                            or texto_busca in (a.get('number') or '').lower()
                            or texto_busca in str(a.get('_id', '')).lower()
                        ]
                    
                    if not acordos_filtrados:
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('search_off', size='48px').classes('text-gray-300 mb-4')
                            ui.label('Nenhum acordo encontrado').classes(
                                'text-gray-500 text-lg font-medium mb-2'
                            )
                            ui.label(f'Busca: "{texto_busca}"').classes(
                                'text-sm text-gray-400 text-center'
                            )
                        return
                    
                    # Definir colunas da tabela
                    columns = [
                        {'name': 'data', 'label': 'Data', 'field': 'data', 'align': 'center', 'style': 'width: 120px;'},
                        {'name': 'titulo', 'label': 'Título/Número', 'field': 'titulo', 'align': 'left'},
                        {'name': 'partes', 'label': 'Partes Envolvidas', 'field': 'partes', 'align': 'left'},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'style': 'width: 150px;'},
                        {'name': 'actions', 'label': 'Ações', 'field': 'actions', 'align': 'center', 'style': 'width: 120px;'},
                    ]
                    
                    # Preparar linhas
                    rows = []
                    for acordo in acordos_filtrados:
                        # Data de assinatura ou celebração
                        data = acordo.get('data_assinatura') or acordo.get('data_celebracao') or acordo.get('data')
                        data_formatada = formatar_data(data)
                        
                        # Título/Número
                        titulo = acordo.get('titulo') or acordo.get('title') or acordo.get('numero') or acordo.get('number') or '-'
                        
                        # Partes envolvidas
                        partes = formatar_partes_envolvidas(acordo)
                        
                        # Status
                        status = acordo.get('status') or 'Sem status'
                        
                        rows.append({
                            'id': acordo.get('_id'),
                            'data': data_formatada,
                            'titulo': titulo,
                            'partes': partes,
                            'status': status,
                        })
                    
                    # Criar tabela
                    table = ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='id'
                    ).classes('w-full').props('flat dense')
                    
                    # Slot para status com cores
                    table.add_slot('body-cell-status', '''
                        <q-td :props="props">
                            <q-badge 
                                :color="props.value && (
                                    props.value.toLowerCase().includes('ativo') || 
                                    props.value.toLowerCase().includes('andamento')
                                ) ? 'green' : 
                                (props.value && (
                                    props.value.toLowerCase().includes('concluído') || 
                                    props.value.toLowerCase().includes('concluido') || 
                                    props.value.toLowerCase().includes('finalizado')
                                )) ? 'grey' :
                                (props.value && (
                                    props.value.toLowerCase().includes('rescindido') || 
                                    props.value.toLowerCase().includes('cancelado')
                                )) ? 'red' :
                                (props.value && props.value.toLowerCase().includes('assinado')) ? 'teal' :
                                (props.value && (
                                    props.value.toLowerCase().includes('negociação') || 
                                    props.value.toLowerCase().includes('negociacao')
                                )) ? 'orange' : 'blue'"
                                :label="props.value"
                            />
                        </q-td>
                    ''')
                    
                    # Slot para ações (Editar, Deletar)
                    table.add_slot('body-cell-actions', '''
                        <q-td :props="props">
                            <q-btn 
                                flat 
                                dense 
                                icon="edit" 
                                color="primary" 
                                @click="$parent.$emit('edit', props.row)" 
                                size="sm"
                                title="Editar"
                            />
                            <q-btn 
                                flat 
                                dense 
                                icon="delete" 
                                color="red" 
                                @click="$parent.$emit('delete', props.row)" 
                                size="sm"
                                title="Deletar"
                            />
                        </q-td>
                    ''')
                    
                    # Handlers para ações
                    def on_edit(acordo_row):
                        """Handler para editar acordo."""
                        acordo_id = acordo_row.get('id')
                        if acordo_id:
                            abrir_modal_edicao(acordo_id)
                        else:
                            ui.notify('Erro: ID do acordo não encontrado', type='negative')
                    
                    def on_delete(acordo_row):
                        """Handler para deletar acordo."""
                        ui.notify('Deleção em desenvolvimento', type='info')
                    
                    table.on('edit', lambda e: on_edit(e.args))
                    table.on('delete', lambda e: on_delete(e.args))
                    
                except Exception as e:
                    # Tratamento de erro
                    print(f"[ERROR] Erro ao carregar acordos: {e}")
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('error', size='48px').classes('text-red-400 mb-4')
                        ui.label('Erro ao carregar acordos').classes(
                            'text-red-600 text-lg font-medium mb-2'
                        )
                        ui.label('Tente recarregar a página').classes(
                            'text-sm text-gray-500 text-center'
                        )
        
        # Renderizar tabela inicial
        render_tabela()
        
        # Atualizar tabela quando busca mudar
        busca_input.on('input', lambda: render_tabela.refresh())
