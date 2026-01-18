"""
Página principal do módulo Audiências.

Visualização em tabela das audiências cadastradas com CRUD completo.
"""

from datetime import datetime
from typing import List, Dict, Any
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated
from ...componentes.breadcrumb_helper import gerar_breadcrumbs
from .database import (
    listar_audiencias,
    buscar_audiencia_por_id,
    excluir_audiencia,
    atualizar_audiencia,
    buscar_clientes_para_select,
    buscar_usuarios_para_select,
)
from .modal_audiencia import render_modal_audiencia
from .models import MODALIDADES_AUDIENCIA, STATUS_AUDIENCIA


def formatar_data(timestamp: Any) -> str:
    """
    Formata timestamp para exibição no padrão "DD de mês por extenso de AAAA" 
    com dia da semana em linha separada.
    Exemplo: "18 de janeiro de 2026<br>Domingo"
    
    Args:
        timestamp: Timestamp (float ou int) ou None
    
    Returns:
        String formatada com HTML ou '-' se inválida
    """
    if not timestamp:
        return '-'
    
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            
            # Meses por extenso em português
            meses = {
                1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
                5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
                9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
            }
            
            # Dias da semana por extenso em português
            dias_semana = {
                0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
                3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
            }
            
            dia = dt.day
            mes = meses[dt.month]
            ano = dt.year
            dia_semana = dias_semana[dt.weekday()]
            
            return f"{dia} de {mes} de {ano}<br>{dia_semana}"
        return str(timestamp)
    except Exception:
        return '-'


def formatar_hora(timestamp: Any) -> str:
    """
    Formata timestamp para exibição no padrão HH:MM.
    
    Args:
        timestamp: Timestamp (float ou int) ou None
    
    Returns:
        String formatada ou '-' se inválida
    """
    if not timestamp:
        return '-'
    
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%H:%M')
        return str(timestamp)
    except Exception:
        return '-'


def formatar_lista_clientes(ids: List[str], opcoes: Dict[str, str]) -> str:
    """
    Formata lista de IDs de clientes para exibição de nomes separados por vírgula.
    
    Args:
        ids: Lista de IDs
        opcoes: Dicionário mapeando ID -> Nome
    
    Returns:
        String com nomes separados por vírgula ou '-'
    """
    if not ids:
        return '-'
    
    nomes = []
    for id_item in ids:
        if id_item in opcoes:
            nomes.append(opcoes[id_item])
    
    if not nomes:
        return '-'
    
    return ', '.join(nomes)


@ui.page('/audiencias')
def audiencias():
    """Página principal do módulo Audiências."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # CSS: tabela responsiva com linhas zebradas, checkbox arredondado e linhas mais altas
    ui.add_head_html('''
    <style>
        /* Linhas zebradas sutis para manter legibilidade */
        .tabela-audiencias tbody tr:nth-child(even) {
            background-color: #ffffff !important;
        }
        .tabela-audiencias tbody tr:nth-child(odd) {
            background-color: #fafafa !important;
        }
        
        /* Aumentar altura das linhas */
        .tabela-audiencias tbody tr {
            height: auto !important;
            min-height: 60px !important;
        }
        
        .tabela-audiencias tbody td {
            padding-top: 16px !important;
            padding-bottom: 16px !important;
            vertical-align: top !important;
            word-wrap: break-word !important;
            white-space: normal !important;
        }
        
        /* Checkbox arredondado */
        .tabela-audiencias .q-checkbox__bg {
            border-radius: 999px !important;
        }
        
        /* Tornar tabela responsiva */
        .tabela-audiencias {
            width: 100% !important;
            table-layout: auto !important;
        }
        
        /* Permitir quebra de linha em todas as células */
        .tabela-audiencias td,
        .tabela-audiencias th {
            overflow-wrap: break-word !important;
            word-break: break-word !important;
        }
    </style>
    ''')
    
    # Carregar opções para formatação
    clientes_opcoes = buscar_clientes_para_select()
    usuarios_opcoes = buscar_usuarios_para_select()
    
    # Garantir que há opções de usuários (fallback)
    if not usuarios_opcoes:
        print("[WARNING] Nenhum usuário encontrado na página. Usando opções padrão.")
        usuarios_opcoes = {
            'lenon_taques': 'Lenon Taques',
            'gilberto_taques': 'Gilberto Taques'
        }
    else:
        print(f"[DEBUG] Usuários carregados na página: {usuarios_opcoes}")
    
    # Estado do filtro (padrão: em_aberto)
    filtro_status = {'value': 'em_aberto'}
    
    # Estado do filtro por mês (None = todos os meses, ou dict com 'ano' e 'mes')
    from datetime import date
    hoje = date.today()
    filtro_mes = {'ano': None, 'mes': None}  # Padrão: Todos os meses
    
    # Função callback após salvar
    def on_audiencia_salva(audiencia_data: Dict[str, Any]):
        """Callback executado após salvar audiência."""
        try:
            render_tabela.refresh()
        except Exception as e:
            print(f"[ERROR] Erro ao processar audiência salva: {e}")
            ui.notify('Erro ao atualizar lista. Tente recarregar.', type='negative')
    
    # Dialog para nova audiência
    dialog_novo, open_dialog_novo = render_modal_audiencia(on_success=on_audiencia_salva)
    
    # Função para abrir modal de edição
    def abrir_modal_edicao(audiencia_id: str):
        """Abre modal de edição com dados da audiência."""
        try:
            audiencia = buscar_audiencia_por_id(audiencia_id)
            if not audiencia:
                ui.notify('Audiência não encontrada!', type='negative')
                return
            
            # Criar dialog de edição
            dialog_edit, open_edit = render_modal_audiencia(
                on_success=on_audiencia_salva,
                audiencia_inicial=audiencia
            )
            open_edit()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir modal de edição: {e}")
            ui.notify('Erro ao carregar dados da audiência. Tente novamente.', type='negative')
    
    # Função para excluir audiência
    def excluir_audiencia_com_confirmacao(audiencia_id: str, titulo: str):
        """Exclui audiência com diálogo de confirmação."""
        with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Confirmar Exclusão').classes('text-lg font-bold')
                ui.label(f'Tem certeza que deseja excluir a audiência "{titulo}"?').classes('text-gray-700')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_excluir.close()
                    
                    def on_confirm():
                        try:
                            sucesso = excluir_audiencia(audiencia_id)
                            if sucesso:
                                ui.notify('Audiência excluída com sucesso!', type='positive')
                                render_tabela.refresh()
                            else:
                                ui.notify('Erro ao excluir audiência', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao excluir audiência: {e}")
                            ui.notify(f'Erro ao excluir audiência: {str(e)}', type='negative')
                        
                        dialog_excluir.close()
                    
                    ui.button('Cancelar', on_click=on_cancel).props('flat')
                    ui.button('Excluir', on_click=on_confirm).props('color=red')
        
        dialog_excluir.open()
    
    # Gera breadcrumb padronizado com workspace
    breadcrumbs = gerar_breadcrumbs('Audiências', url_modulo='/audiencias')
    
    with layout('Audiências', breadcrumbs=breadcrumbs):
        # Filtros de status
        with ui.row().classes('w-full gap-3 mb-4 items-center'):
            ui.label('Filtrar por:').classes('text-sm font-medium text-gray-600')
            
            def filtrar_em_aberto():
                filtro_status['value'] = 'em_aberto'
                atualizar_estilo_botoes()
                render_tabela.refresh()
            
            def filtrar_concluidas():
                filtro_status['value'] = 'concluido'
                atualizar_estilo_botoes()
                render_tabela.refresh()
            
            def filtrar_todas():
                filtro_status['value'] = None
                atualizar_estilo_botoes()
                render_tabela.refresh()
            
            btn_em_aberto = ui.button('Em Aberto', on_click=filtrar_em_aberto).props('size=sm')
            btn_concluidas = ui.button('Concluídas', on_click=filtrar_concluidas).props('size=sm outline')
            btn_todas = ui.button('Todas', on_click=filtrar_todas).props('size=sm outline')
            
            def atualizar_estilo_botoes():
                """Atualiza o estilo dos botões de filtro baseado no filtro ativo."""
                if filtro_status['value'] == 'em_aberto':
                    btn_em_aberto.props('color=primary')
                    btn_em_aberto.props(remove='outline')
                    btn_concluidas.props('outline color=grey-6')
                    btn_todas.props('outline color=grey-6')
                elif filtro_status['value'] == 'concluido':
                    btn_concluidas.props('color=primary')
                    btn_concluidas.props(remove='outline')
                    btn_em_aberto.props('outline color=grey-6')
                    btn_todas.props('outline color=grey-6')
                else:
                    btn_todas.props('color=primary')
                    btn_todas.props(remove='outline')
                    btn_em_aberto.props('outline color=grey-6')
                    btn_concluidas.props('outline color=grey-6')
        
        # Filtro por mês
        with ui.row().classes('w-full gap-3 mb-4 items-center flex-wrap'):
            ui.label('Filtrar por mês:').classes('text-sm font-medium text-gray-600')
            
            # Nomes dos meses em português
            meses_nomes = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            
            # Função para atualizar o label do mês
            def atualizar_label_mes():
                if filtro_mes['ano'] is None or filtro_mes['mes'] is None:
                    label_mes.set_text('Todos os meses')
                    btn_mes_atual.set_visibility(False)
                else:
                    label_mes.set_text(f"{meses_nomes[filtro_mes['mes']]} de {filtro_mes['ano']}")
                    # Mostra botão "Mês Atual" se não estiver no mês atual
                    if filtro_mes['ano'] != hoje.year or filtro_mes['mes'] != hoje.month:
                        btn_mes_atual.set_visibility(True)
                    else:
                        btn_mes_atual.set_visibility(False)
            
            # Função para navegar mês anterior
            def mes_anterior():
                # Se está em "Todos os meses", vai para o mês atual primeiro
                if filtro_mes['ano'] is None or filtro_mes['mes'] is None:
                    filtro_mes['ano'] = hoje.year
                    filtro_mes['mes'] = hoje.month
                
                if filtro_mes['mes'] == 1:
                    filtro_mes['mes'] = 12
                    filtro_mes['ano'] -= 1
                else:
                    filtro_mes['mes'] -= 1
                
                atualizar_label_mes()
                render_tabela.refresh()
            
            # Função para navegar próximo mês
            def proximo_mes():
                # Se está em "Todos os meses", vai para o mês atual primeiro
                if filtro_mes['ano'] is None or filtro_mes['mes'] is None:
                    filtro_mes['ano'] = hoje.year
                    filtro_mes['mes'] = hoje.month
                
                if filtro_mes['mes'] == 12:
                    filtro_mes['mes'] = 1
                    filtro_mes['ano'] += 1
                else:
                    filtro_mes['mes'] += 1
                
                atualizar_label_mes()
                render_tabela.refresh()
            
            # Função para ver todos os meses
            def todos_os_meses():
                filtro_mes['ano'] = None
                filtro_mes['mes'] = None
                atualizar_label_mes()
                render_tabela.refresh()
            
            # Função para voltar ao mês atual
            def voltar_mes_atual():
                filtro_mes['ano'] = hoje.year
                filtro_mes['mes'] = hoje.month
                atualizar_label_mes()
                render_tabela.refresh()
            
            # Botão mês anterior
            ui.button(icon='chevron_left', on_click=mes_anterior).props('flat dense round').classes('text-gray-600').tooltip('Mês anterior')
            
            # Label do mês atual
            label_mes = ui.label('Todos os meses').classes('text-sm font-medium min-w-[180px] text-center')
            
            # Botão próximo mês
            ui.button(icon='chevron_right', on_click=proximo_mes).props('flat dense round').classes('text-gray-600').tooltip('Próximo mês')
            
            # Separador visual
            ui.label('|').classes('text-gray-300 mx-1')
            
            # Botão "Mês Atual" (aparece quando não está no mês atual)
            btn_mes_atual = ui.button('Mês Atual', on_click=voltar_mes_atual).props('size=sm outline color=primary').tooltip('Voltar para o mês atual')
            btn_mes_atual.set_visibility(False)
            
            # Botão "Todos"
            ui.button('Todos', on_click=todos_os_meses).props('size=sm outline color=grey-6').tooltip('Ver todas as audiências')
        
        # Header com botão
        with ui.row().classes('w-full gap-4 mb-6 items-center justify-end'):
            ui.button('Adicionar Audiência', icon='add', on_click=open_dialog_novo).props(
                'color=primary'
            ).classes('font-bold')
        
        # Container para tabela
        tabela_container = ui.column().classes('w-full')
        
        @ui.refreshable
        def render_tabela():
            """Renderiza tabela de audiências."""
            tabela_container.clear()
            
            with tabela_container:
                try:
                    # Buscar audiências
                    audiencias_lista = listar_audiencias()
                    
                    # Aplicar filtro de status
                    if filtro_status['value'] == 'em_aberto':
                        audiencias_lista = [a for a in audiencias_lista if a.get('status', 'em_aberto') == 'em_aberto']
                    elif filtro_status['value'] == 'concluido':
                        audiencias_lista = [a for a in audiencias_lista if a.get('status', 'em_aberto') == 'concluido']
                    
                    # Aplicar filtro de mês
                    if filtro_mes['ano'] is not None and filtro_mes['mes'] is not None:
                        audiencias_filtradas = []
                        for audiencia in audiencias_lista:
                            data_hora_inicio = audiencia.get('data_hora_inicio')
                            if data_hora_inicio:
                                dt = datetime.fromtimestamp(data_hora_inicio)
                                if dt.year == filtro_mes['ano'] and dt.month == filtro_mes['mes']:
                                    audiencias_filtradas.append(audiencia)
                        audiencias_lista = audiencias_filtradas
                    
                    if not audiencias_lista:
                        # Mensagem quando não há audiências
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('event', size='48px').classes('text-gray-300 mb-4')
                            ui.label('Nenhuma audiência cadastrada').classes(
                                'text-gray-500 text-lg font-medium mb-2'
                            )
                            ui.label('Clique em "Adicionar Audiência" para criar a primeira').classes(
                                'text-sm text-gray-400 text-center'
                            )
                        return
                    
                    # Definir colunas da tabela (título como coluna principal flexível)
                    columns = [
                        {
                            'name': 'concluido',
                            'label': '',
                            'field': 'concluido',
                            'align': 'center',
                            'style': 'width: 50px; min-width: 50px;',
                        },
                        {
                            'name': 'titulo',
                            'label': 'Título',
                            'field': 'titulo',
                            'align': 'left',
                            'style': 'min-width: 250px;',  # Coluna principal - flexível
                        },
                        {
                            'name': 'data',
                            'label': 'Data',
                            'field': 'data',
                            'align': 'center',
                            'style': 'width: 200px; min-width: 200px;',
                        },
                        {
                            'name': 'hora_inicio',
                            'label': 'Início',
                            'field': 'hora_inicio',
                            'align': 'center',
                            'style': 'width: 70px; min-width: 70px;',
                        },
                        {
                            'name': 'hora_fim',
                            'label': 'Fim',
                            'field': 'hora_fim',
                            'align': 'center',
                            'style': 'width: 70px; min-width: 70px;',
                        },
                        {
                            'name': 'modalidade',
                            'label': 'Modalidade',
                            'field': 'modalidade',
                            'align': 'center',
                            'style': 'width: 110px; min-width: 110px;',
                        },
                        {
                            'name': 'responsavel',
                            'label': 'Responsável',
                            'field': 'responsavel',
                            'align': 'left',
                            'style': 'width: 140px; min-width: 140px;',
                        },
                        {
                            'name': 'clientes',
                            'label': 'Clientes',
                            'field': 'clientes',
                            'align': 'left',
                            'style': 'width: 180px; min-width: 180px;',
                        },
                        {
                            'name': 'status',
                            'label': 'Status',
                            'field': 'status',
                            'align': 'center',
                            'style': 'width: 110px; min-width: 110px;',
                        },
                        {
                            'name': 'acoes',
                            'label': 'Ações',
                            'field': 'acoes',
                            'align': 'center',
                            'style': 'width: 100px; min-width: 100px;',
                        },
                    ]
                    
                    # Preparar linhas
                    rows = []
                    for audiencia in audiencias_lista:
                        titulo = audiencia.get('titulo', '-')
                        
                        data_hora_inicio_ts = audiencia.get('data_hora_inicio')
                        data_texto = formatar_data(data_hora_inicio_ts)
                        hora_inicio_texto = formatar_hora(data_hora_inicio_ts)
                        
                        data_hora_fim_ts = audiencia.get('data_hora_fim')
                        hora_fim_texto = formatar_hora(data_hora_fim_ts)
                        
                        modalidade = audiencia.get('modalidade', 'presencial')
                        modalidade_label = MODALIDADES_AUDIENCIA.get(modalidade, modalidade)
                        
                        responsavel_id = audiencia.get('responsavel_id')
                        responsavel_nome = usuarios_opcoes.get(responsavel_id, '-') if responsavel_id else '-'
                        
                        # Suporte para múltiplos clientes (clientes_ids) ou único cliente (cliente_id - retrocompatibilidade)
                        clientes_ids = audiencia.get('clientes_ids', [])
                        if not clientes_ids and audiencia.get('cliente_id'):
                            clientes_ids = [audiencia.get('cliente_id')]
                        clientes_nomes = formatar_lista_clientes(clientes_ids, clientes_opcoes)
                        
                        status = audiencia.get('status', 'em_aberto')
                        status_label = STATUS_AUDIENCIA.get(status, status)
                        
                        # Determina se está concluído para o checkbox
                        is_concluido = status == 'concluido'

                        rows.append({
                            'id': str(audiencia.get('_id')),
                            'concluido': is_concluido,
                            'titulo': titulo,
                            'data': data_texto,
                            'hora_inicio': hora_inicio_texto,
                            'hora_fim': hora_fim_texto,
                            'modalidade': modalidade_label,
                            'responsavel': responsavel_nome,
                            'clientes': clientes_nomes,
                            'status': status_label,
                            'status_value': status,
                            'acoes': str(audiencia.get('_id')),
                        })
                    
                    # Criar tabela responsiva
                    table = ui.table(
                        columns=columns,
                        rows=rows,
                        row_key='id'
                    ).classes('w-full tabela-audiencias').props('flat dense wrap-cells')
                    
                    # Slot para checkbox arredondado (marcar como concluído)
                    table.add_slot('body-cell-concluido', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <q-checkbox
                                :model-value="props.row.concluido"
                                @update:model-value="(val) => $parent.$emit('toggle-status', {...props.row, novo_status: val})"
                                color="positive"
                                size="md"
                            >
                                <q-tooltip>{{ props.row.concluido ? 'Marcar como Em Aberto' : 'Marcar como Concluído' }}</q-tooltip>
                            </q-checkbox>
                        </q-td>
                    ''')
                    
                    # Slot para data com dia da semana (permite HTML)
                    table.add_slot('body-cell-data', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <div v-html="props.value"></div>
                        </q-td>
                    ''')
                    
                    # Slot para status com badge colorido
                    table.add_slot('body-cell-status', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <q-badge 
                                :style="props.row.status_value === 'em_aberto' ? 'background-color: #FEF3C7; color: #92400E;' : 
                                        props.row.status_value === 'concluido' ? 'background-color: #10B981; color: #ffffff;' : 
                                        'background-color: #d1d5db; color: #000000;'"
                                class="px-3 py-1"
                                style="border: 1px solid rgba(0,0,0,0.1);"
                            >
                                {{ props.value }}
                            </q-badge>
                        </q-td>
                    ''')
                    
                    # Slot para ações (editar e excluir)
                    table.add_slot('body-cell-acoes', '''
                        <q-td :props="props" style="vertical-align: middle;">
                            <q-btn 
                                flat 
                                round 
                                dense 
                                icon="edit" 
                                color="primary" 
                                size="sm"
                                @click="$parent.$emit('edit', props.row)"
                            >
                                <q-tooltip>Editar</q-tooltip>
                            </q-btn>
                            <q-btn 
                                flat 
                                round 
                                dense 
                                icon="delete" 
                                color="negative" 
                                size="sm"
                                @click="$parent.$emit('delete', props.row)"
                            >
                                <q-tooltip>Excluir</q-tooltip>
                            </q-btn>
                        </q-td>
                    ''')
                    
                    # Handlers para ações
                    def on_edit(audiencia_row):
                        """Handler para editar audiência."""
                        audiencia_id = audiencia_row.get('id')
                        if audiencia_id:
                            abrir_modal_edicao(audiencia_id)
                        else:
                            ui.notify('Erro: ID da audiência não encontrado', type='negative')
                    
                    def on_delete(audiencia_row):
                        """Handler para excluir audiência."""
                        audiencia_id = audiencia_row.get('id')
                        titulo = audiencia_row.get('titulo', 'esta audiência')
                        if audiencia_id:
                            excluir_audiencia_com_confirmacao(audiencia_id, titulo)
                        else:
                            ui.notify('Erro: ID da audiência não encontrado', type='negative')
                    
                    def on_toggle_status(audiencia_row):
                        """Handler para alternar status da audiência com confirmação."""
                        audiencia_id = audiencia_row.get('id')
                        titulo = audiencia_row.get('titulo', 'esta audiência')
                        status_atual = audiencia_row.get('status_value', 'em_aberto')
                        novo_status_bool = audiencia_row.get('novo_status', False)
                        
                        # Define o novo status baseado no checkbox
                        novo_status = 'concluido' if novo_status_bool else 'em_aberto'
                        
                        if not audiencia_id:
                            ui.notify('Erro: ID da audiência não encontrado', type='negative')
                            return
                        
                        # Mensagens de confirmação
                        if novo_status == 'concluido':
                            mensagem = f'Deseja marcar a audiência "{titulo}" como CONCLUÍDA?'
                            cor_botao = 'positive'
                            texto_botao = 'Sim, Concluir'
                        else:
                            mensagem = f'Deseja retornar a audiência "{titulo}" para EM ABERTO?'
                            cor_botao = 'primary'
                            texto_botao = 'Sim, Reabrir'
                        
                        # Diálogo de confirmação
                        with ui.dialog() as dialog_confirmar, ui.card().classes('w-full max-w-md'):
                            with ui.column().classes('w-full gap-4 p-4'):
                                ui.label('Confirmar Alteração de Status').classes('text-lg font-bold')
                                ui.label(mensagem).classes('text-gray-700')
                                
                                with ui.row().classes('w-full justify-end gap-2'):
                                    def on_cancel():
                                        dialog_confirmar.close()
                                        # Força refresh para reverter visualmente o checkbox
                                        render_tabela.refresh()
                                    
                                    def on_confirm():
                                        try:
                                            sucesso = atualizar_audiencia(audiencia_id, {'status': novo_status})
                                            if sucesso:
                                                if novo_status == 'concluido':
                                                    ui.notify('Audiência marcada como concluída!', type='positive')
                                                else:
                                                    ui.notify('Audiência reaberta!', type='info')
                                                render_tabela.refresh()
                                            else:
                                                ui.notify('Erro ao atualizar status', type='negative')
                                                render_tabela.refresh()
                                        except Exception as e:
                                            print(f"[ERROR] Erro ao atualizar status: {e}")
                                            ui.notify('Erro ao atualizar status', type='negative')
                                            render_tabela.refresh()
                                        
                                        dialog_confirmar.close()
                                    
                                    ui.button('Cancelar', on_click=on_cancel).props('flat')
                                    ui.button(texto_botao, on_click=on_confirm).props(f'color={cor_botao}')
                        
                        dialog_confirmar.open()

                    table.on('edit', lambda e: on_edit(e.args))
                    table.on('delete', lambda e: on_delete(e.args))
                    table.on('toggle-status', lambda e: on_toggle_status(e.args))
                    
                except Exception as e:
                    # Tratamento de erro
                    print(f"[ERROR] Erro ao carregar audiências: {e}")
                    import traceback
                    traceback.print_exc()
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('error', size='48px').classes('text-red-400 mb-4')
                        ui.label('Erro ao carregar audiências').classes(
                            'text-red-600 text-lg font-medium mb-2'
                        )
                        ui.label('Tente recarregar a página').classes(
                            'text-sm text-gray-500 text-center'
                        )
        
        # Renderizar tabela inicial
        render_tabela()
