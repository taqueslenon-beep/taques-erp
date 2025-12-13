"""
prazos.py - Página principal do módulo Prazos.

Visualização em tabela dos prazos cadastrados com CRUD completo.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Tuple
from nicegui import ui
from ...core import layout, get_display_name
from ...auth import is_authenticated
from .database import (
    listar_prazos,
    listar_prazos_por_status,
    buscar_prazo_por_id,
    criar_prazo,
    atualizar_prazo,
    excluir_prazo,
    invalidar_cache_prazos,
    buscar_usuarios_para_select,
    buscar_clientes_para_select,
    buscar_casos_para_select,
)
from .modal_prazo import render_prazo_dialog
from .models import STATUS_LABELS


def formatar_data_prazo(timestamp: Any) -> str:
    """
    Formata timestamp para exibição no padrão DD/MM/AAAA.

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
            return dt.strftime('%d/%m/%Y')
        return str(timestamp)
    except Exception:
        return '-'


def calcular_prazo_seguranca(timestamp: Any) -> str:
    """
    Calcula o prazo de segurança (4 dias antes do prazo fatal).

    Args:
        timestamp: Timestamp do prazo fatal (float, int ou None)

    Returns:
        String com a data de segurança no formato DD/MM/AAAA ou '-' se inválida
    """
    if not timestamp:
        return '-'

    try:
        if isinstance(timestamp, (int, float)):
            data_fatal = datetime.fromtimestamp(timestamp)
            data_seguranca = data_fatal - timedelta(days=4)
            return data_seguranca.strftime('%d/%m/%Y')
        return '-'
    except Exception:
        return '-'


def verificar_prazo_atrasado(timestamp: Any, status: str) -> bool:
    """
    Verifica se um prazo está atrasado.

    Um prazo está atrasado quando:
    - O prazo fatal é anterior à data de hoje
    - E o status atual é 'pendente' (não concluído)

    Args:
        timestamp: Timestamp do prazo fatal (float, int ou None)
        status: Status atual do prazo ('pendente' ou 'concluido')

    Returns:
        True se o prazo está atrasado, False caso contrário
    """
    if not timestamp:
        return False

    # Só pode estar atrasado se estiver pendente
    if status.lower() != 'pendente':
        return False

    try:
        if isinstance(timestamp, (int, float)):
            data_fatal = datetime.fromtimestamp(timestamp)
            hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return data_fatal < hoje
        return False
    except Exception:
        return False


# =============================================================================
# FUNÇÕES DE CÁLCULO DE SEMANAS
# =============================================================================

def obter_inicio_fim_semana(data_ref: date) -> Tuple[date, date]:
    """
    Retorna o início (segunda) e fim (domingo) da semana de uma data.

    Args:
        data_ref: Data de referência

    Returns:
        Tupla (data_inicio, data_fim) da semana
    """
    # Segunda-feira da semana
    inicio = data_ref - timedelta(days=data_ref.weekday())
    # Domingo da semana
    fim = inicio + timedelta(days=6)
    return inicio, fim


def obter_semana_passada() -> Tuple[date, date]:
    """Retorna início e fim da semana passada."""
    hoje = date.today()
    inicio_esta_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana_passada = inicio_esta_semana - timedelta(days=7)
    fim_semana_passada = inicio_semana_passada + timedelta(days=6)
    return inicio_semana_passada, fim_semana_passada


def obter_esta_semana() -> Tuple[date, date]:
    """Retorna início e fim desta semana."""
    hoje = date.today()
    return obter_inicio_fim_semana(hoje)


def obter_proxima_semana() -> Tuple[date, date]:
    """Retorna início e fim da próxima semana."""
    hoje = date.today()
    inicio_esta_semana = hoje - timedelta(days=hoje.weekday())
    inicio_proxima_semana = inicio_esta_semana + timedelta(days=7)
    fim_proxima_semana = inicio_proxima_semana + timedelta(days=6)
    return inicio_proxima_semana, fim_proxima_semana


def obter_semana_do_ano(ano: int, numero_semana: int) -> Tuple[date, date]:
    """
    Retorna início e fim de uma semana específica do ano.

    Args:
        ano: Ano (ex: 2025)
        numero_semana: Número da semana (1-52)

    Returns:
        Tupla (data_inicio, data_fim)
    """
    # Usar isocalendar para encontrar a semana correta
    # Primeiro dia do ano
    primeiro_dia = date(ano, 1, 4)  # 4 de janeiro sempre está na semana 1
    inicio_semana_1 = primeiro_dia - timedelta(days=primeiro_dia.weekday())

    # Calcular início da semana desejada
    inicio = inicio_semana_1 + timedelta(weeks=numero_semana - 1)
    fim = inicio + timedelta(days=6)

    return inicio, fim


def formatar_periodo_semana(inicio: date, fim: date) -> str:
    """Formata o período da semana para exibição."""
    return f"{inicio.strftime('%d/%m')} - {fim.strftime('%d/%m/%Y')}"


def filtrar_prazos_por_semana(prazos: List[Dict[str, Any]], inicio_semana: date, fim_semana: date) -> List[Dict[str, Any]]:
    """
    Filtra prazos cujo PRAZO FATAL está dentro do período da semana.

    Args:
        prazos: Lista de prazos
        inicio_semana: Data de início da semana (segunda)
        fim_semana: Data de fim da semana (domingo)

    Returns:
        Lista de prazos filtrados
    """
    filtrados = []

    for prazo in prazos:
        prazo_fatal = prazo.get('prazo_fatal')

        if not prazo_fatal:
            continue

        try:
            # Converter para date
            if isinstance(prazo_fatal, (int, float)):
                data_fatal = datetime.fromtimestamp(prazo_fatal).date()
            else:
                continue

            # Verificar se está dentro da semana
            if inicio_semana <= data_fatal <= fim_semana:
                filtrados.append(prazo)

        except Exception as e:
            print(f"[PRAZOS] Erro ao filtrar prazo: {e}")
            continue

    return filtrados


def criar_opcoes_semanas(ano: int = None) -> Dict[str, str]:
    """
    Cria opções de semanas para o dropdown.

    Args:
        ano: Ano para gerar semanas (padrão: ano atual)

    Returns:
        Dicionário {valor: label} para o dropdown
    """
    if ano is None:
        ano = date.today().year

    opcoes = {}
    for semana in range(1, 53):
        try:
            inicio, fim = obter_semana_do_ano(ano, semana)
            label = f"Semana {semana}: {inicio.strftime('%d/%m')} - {fim.strftime('%d/%m')}"
            opcoes[f"{ano}-{semana}"] = label
        except Exception:
            continue

    return opcoes


def formatar_lista_nomes(ids: List[str], opcoes: Dict[str, str]) -> str:
    """
    Formata lista de IDs para exibição de nomes separados por vírgula.

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
            # Extrai apenas o nome (remove email entre parênteses se houver)
            nome_completo = opcoes[id_item]
            nome = nome_completo.split(' (')[0] if ' (' in nome_completo else nome_completo
            nomes.append(nome)
        else:
            nomes.append(f"({id_item[:8]}...)")

    if not nomes:
        return '-'

    # Limita a 2 nomes para não ficar muito longo
    if len(nomes) > 2:
        return f"{', '.join(nomes[:2])}..."

    return ', '.join(nomes)


def formatar_responsaveis(responsaveis_ids: List[str], usuarios_opcoes: Dict[str, str]) -> str:
    """
    Formata lista de responsáveis usando cache local - SEM consultas Firebase.

    Args:
        responsaveis_ids: Lista de UIDs dos usuários responsáveis
        usuarios_opcoes: Dicionário de usuários (uid -> "Nome (email)")

    Returns:
        String com nomes separados por vírgula ou '-'
    """
    if not responsaveis_ids:
        return '-'

    nomes = []
    for uid in responsaveis_ids:
        if uid in usuarios_opcoes:
            # Extrai apenas o nome (remove email entre parênteses)
            nome_completo = usuarios_opcoes[uid]
            nome = nome_completo.split(' (')[0] if ' (' in nome_completo else nome_completo
            nomes.append(nome)
        else:
            nomes.append(f"({uid[:8]}...)")

    if not nomes:
        return '-'

    # Limita a 2 nomes para não ficar muito longo
    if len(nomes) > 2:
        return f"{', '.join(nomes[:2])}..."

    return ', '.join(nomes)


def obter_cor_status(status: str) -> str:
    """
    Retorna estilo CSS para badge baseado no status.

    Args:
        status: Status do prazo ('pendente' ou 'concluido')

    Returns:
        String de estilo CSS para o badge
    """
    if not status:
        return 'background-color: #d1d5db; color: #000000;'

    status_lower = status.lower()

    if status_lower == 'pendente':
        return 'background-color: #fde047; color: #000000;'  # Amarelo
    elif status_lower == 'concluido' or status_lower == 'concluído':
        return 'background-color: #4ade80; color: #000000;'  # Verde
    else:
        return 'background-color: #d1d5db; color: #000000;'  # Cinza padrão


@ui.page('/prazos')
def prazos():
    """Página principal do módulo Prazos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    print("[PRAZOS] Iniciando carregamento da página...")

    # Carregar opções EM PARALELO para reduzir tempo de carregamento
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(buscar_usuarios_para_select): 'usuarios',
            executor.submit(buscar_clientes_para_select): 'clientes',
            executor.submit(buscar_casos_para_select): 'casos',
        }

        opcoes = {}
        for future in as_completed(futures):
            key = futures[future]
            try:
                opcoes[key] = future.result()
            except Exception as e:
                print(f"[PRAZOS] Erro ao carregar {key}: {e}")
                opcoes[key] = {}

    usuarios_opcoes = opcoes.get('usuarios', {})
    clientes_opcoes = opcoes.get('clientes', {})
    casos_opcoes = opcoes.get('casos', {})

    print(f"[PRAZOS] Opções carregadas: {len(usuarios_opcoes)} usuários, {len(clientes_opcoes)} clientes, {len(casos_opcoes)} casos")

    # Referências para as funções refreshable (serão definidas depois)
    refresh_funcs = {'pendentes': None, 'concluidos': None, 'semana': None}

    # Referências para as abas (serão definidas depois)
    tabs_refs = {'tab_pendentes': None, 'tab_concluidos': None, 'tab_semana': None}

    def atualizar_tabelas():
        """Atualiza todas as tabelas."""
        if refresh_funcs['pendentes']:
            refresh_funcs['pendentes'].refresh()
        if refresh_funcs['concluidos']:
            refresh_funcs['concluidos'].refresh()
        if refresh_funcs['semana']:
            refresh_funcs['semana'].refresh()

    # Função callback após salvar
    def on_prazo_salvo(prazo_data: Dict[str, Any]):
        """Callback executado após salvar prazo."""
        try:
            prazo_id = prazo_data.get('_id')
            if prazo_id:
                # Invalida cache e atualiza ambas as tabelas
                invalidar_cache_prazos()
                atualizar_tabelas()
            else:
                ui.notify('Erro: ID do prazo não retornado', type='negative')
        except Exception as e:
            print(f"[ERROR] Erro ao processar prazo salvo: {e}")
            ui.notify('Erro ao atualizar lista. Tente recarregar.', type='negative')

    # Dialog para novo prazo - passa opções para evitar recarregar
    dialog_novo, open_dialog_novo = render_prazo_dialog(
        on_success=on_prazo_salvo,
        usuarios_opcoes=usuarios_opcoes,
        clientes_opcoes=clientes_opcoes,
        casos_opcoes=casos_opcoes
    )

    # Função para abrir modal de edição
    def abrir_modal_edicao(prazo_id: str):
        """Abre modal de edição com dados do prazo."""
        try:
            prazo = buscar_prazo_por_id(prazo_id)
            if not prazo:
                ui.notify('Prazo não encontrado!', type='negative')
                return

            # Criar dialog de edição - passa opções para evitar recarregar
            dialog_edit, open_edit = render_prazo_dialog(
                on_success=on_prazo_salvo,
                prazo_inicial=prazo,
                usuarios_opcoes=usuarios_opcoes,
                clientes_opcoes=clientes_opcoes,
                casos_opcoes=casos_opcoes
            )
            open_edit()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir modal de edição: {e}")
            ui.notify('Erro ao carregar dados do prazo. Tente novamente.', type='negative')

    # Função para excluir prazo
    def excluir_prazo_com_confirmacao(prazo_id: str, titulo: str):
        """Exclui prazo com diálogo de confirmação."""
        with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Confirmar Exclusão').classes('text-lg font-bold')
                ui.label(f'Tem certeza que deseja excluir o prazo "{titulo}"?').classes('text-gray-700')

                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_excluir.close()

                    def on_confirm():
                        try:
                            sucesso = excluir_prazo(prazo_id)
                            if sucesso:
                                ui.notify('Prazo excluído com sucesso!', type='positive')
                                invalidar_cache_prazos()
                                atualizar_tabelas()
                            else:
                                ui.notify('Erro ao excluir prazo', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao excluir prazo: {e}")
                            ui.notify(f'Erro ao excluir prazo: {str(e)}', type='negative')

                        dialog_excluir.close()

                    ui.button('Cancelar', on_click=on_cancel).props('flat')
                    ui.button('Excluir', on_click=on_confirm).props('color=red')

        dialog_excluir.open()

    # Função para confirmar conclusão de prazo
    def confirmar_conclusao_prazo(prazo_id: str, titulo: str):
        """Mostra diálogo de confirmação para marcar prazo como concluído."""
        with ui.dialog() as dialog_confirmar, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Confirmar Conclusão').classes('text-lg font-bold')
                ui.label(f'Deseja marcar o prazo "{titulo}" como concluído?').classes('text-gray-700')

                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_confirmar.close()

                    def on_confirm():
                        try:
                            prazo = buscar_prazo_por_id(prazo_id)
                            if not prazo:
                                ui.notify('Prazo não encontrado!', type='negative')
                                dialog_confirmar.close()
                                return

                            prazo['status'] = 'concluido'
                            sucesso = atualizar_prazo(prazo_id, prazo)

                            if sucesso:
                                invalidar_cache_prazos()
                                atualizar_tabelas()
                                ui.notify('Prazo concluído com sucesso!', type='positive')
                            else:
                                ui.notify('Erro ao atualizar status', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao concluir prazo: {e}")
                            ui.notify(f'Erro ao concluir prazo: {str(e)}', type='negative')

                        dialog_confirmar.close()

                    ui.button('Não', on_click=on_cancel).props('flat')
                    ui.button('Sim', on_click=on_confirm).props('color=positive')

        dialog_confirmar.open()

    # Função para confirmar reabertura de prazo
    def confirmar_reabertura_prazo(prazo_id: str, titulo: str):
        """Mostra diálogo de confirmação para reabrir prazo."""
        with ui.dialog() as dialog_reabrir, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Reabrir Prazo').classes('text-lg font-bold')
                ui.label(f'Deseja reabrir o prazo "{titulo}"?').classes('text-gray-700')

                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_reabrir.close()

                    def on_confirm():
                        try:
                            prazo = buscar_prazo_por_id(prazo_id)
                            if not prazo:
                                ui.notify('Prazo não encontrado!', type='negative')
                                dialog_reabrir.close()
                                return

                            prazo['status'] = 'pendente'
                            sucesso = atualizar_prazo(prazo_id, prazo)

                            if sucesso:
                                invalidar_cache_prazos()
                                atualizar_tabelas()
                                ui.notify('Prazo reaberto!', type='positive')
                            else:
                                ui.notify('Erro ao atualizar status', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao reabrir prazo: {e}")
                            ui.notify(f'Erro ao reabrir prazo: {str(e)}', type='negative')

                        dialog_reabrir.close()

                    ui.button('Não', on_click=on_cancel).props('flat')
                    ui.button('Sim', on_click=on_confirm).props('color=warning')

        dialog_reabrir.open()

    with layout('Prazos', breadcrumbs=[('Prazos', None)]):
        # Header com botão
        with ui.row().classes('w-full gap-4 mb-6 items-center justify-between'):
            ui.label('Prazos').classes('text-2xl font-bold')
            ui.button('Adicionar Prazo', icon='add', on_click=open_dialog_novo).props(
                'color=primary'
            ).classes('font-bold')

        # Função para obter contadores - UMA consulta, dois resultados
        def obter_contadores():
            """Retorna contagem de prazos por status - UMA consulta."""
            try:
                todos = listar_prazos()  # Uma única consulta (usa cache)
                pendentes = sum(1 for p in todos if p.get('status', '').lower() == 'pendente')
                concluidos = sum(1 for p in todos if p.get('status', '').lower() == 'concluido')
                return pendentes, concluidos
            except Exception as e:
                print(f"[ERROR] Erro ao obter contadores: {e}")
                return 0, 0

        # Criar abas
        pendentes_count, concluidos_count = obter_contadores()
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_pendentes = ui.tab(f'Pendentes ({pendentes_count})')
            tab_concluidos = ui.tab(f'Concluídos ({concluidos_count})')
            tab_semana = ui.tab('Por Semana')

        # Salvar referências das abas
        tabs_refs['tab_pendentes'] = tab_pendentes
        tabs_refs['tab_concluidos'] = tab_concluidos
        tabs_refs['tab_semana'] = tab_semana

        # Função para criar tabela de prazos (sem coluna de status)
        def criar_tabela_prazos(prazos_lista: List[Dict[str, Any]], status_filtro: str):
            """Cria tabela de prazos com os dados fornecidos."""
            if not prazos_lista:
                # Mensagem quando não há prazos
                if status_filtro == 'pendente':
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('check_circle', size='48px').classes('text-green-300 mb-4')
                        ui.label('Nenhum prazo pendente').classes(
                            'text-gray-500 text-lg font-medium mb-2'
                        )
                        ui.label('Todos os prazos estão concluídos!').classes(
                            'text-sm text-gray-400 text-center'
                        )
                elif status_filtro == 'concluido':
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('pending_actions', size='48px').classes('text-yellow-300 mb-4')
                        ui.label('Nenhum prazo concluído').classes(
                            'text-gray-500 text-lg font-medium mb-2'
                        )
                        ui.label('Conclua alguns prazos para vê-los aqui').classes(
                            'text-sm text-gray-400 text-center'
                        )
                else:  # semana
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('event_busy', size='48px').classes('text-gray-300 mb-4')
                        ui.label('Nenhum prazo nesta semana').classes(
                            'text-gray-500 text-lg font-medium mb-2'
                        )
                        ui.label('Selecione outra semana ou adicione novos prazos').classes(
                            'text-sm text-gray-400 text-center'
                        )
                return

            # Definir colunas da tabela (sem coluna de status para abas Pendentes/Concluídos)
            columns = [
                {'name': 'concluido', 'label': '', 'field': 'concluido', 'align': 'center', 'style': 'width: 50px;'},
                {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left'},
                {'name': 'responsaveis', 'label': 'Responsáveis', 'field': 'responsaveis', 'align': 'left', 'style': 'width: 200px;'},
                {'name': 'clientes', 'label': 'Clientes', 'field': 'clientes', 'align': 'left', 'style': 'width: 200px;'},
                {'name': 'prazo_seguranca', 'label': 'Prazo de Segurança', 'field': 'prazo_seguranca', 'align': 'center', 'style': 'width: 140px;'},
                {'name': 'prazo_fatal', 'label': 'Prazo Fatal', 'field': 'prazo_fatal', 'align': 'center', 'style': 'width: 120px;'},
                {'name': 'recorrente', 'label': 'Recorrente', 'field': 'recorrente', 'align': 'center', 'style': 'width: 100px;'},
                {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 120px;'},
            ]

            # Preparar linhas
            rows = []
            for prazo in prazos_lista:
                # Formatações - usando cache local (sem consultas Firebase)
                titulo = prazo.get('titulo', '-')

                responsaveis_ids = prazo.get('responsaveis', [])
                responsaveis_texto = formatar_responsaveis(responsaveis_ids, usuarios_opcoes)

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

                rows.append({
                    'id': prazo.get('_id'),
                    'concluido': esta_concluido,
                    'atrasado': esta_atrasado,
                    'titulo': titulo,
                    'responsaveis': responsaveis_texto,
                    'clientes': clientes_texto,
                    'prazo_seguranca': prazo_seguranca_texto,
                    'prazo_fatal': prazo_fatal_texto,
                    'recorrente': recorrente_texto,
                    'acoes': prazo.get('_id'),
                })

            # Criar tabela
            table = ui.table(
                columns=columns,
                rows=rows,
                row_key='id'
            ).classes('w-full').props('flat dense')

            # Slot para checkbox de concluído
            table.add_slot('body-cell-concluido', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    <q-checkbox
                        :model-value="props.value"
                        @update:model-value="(val) => $parent.$emit('toggle-status', {row: props.row, value: val})"
                        color="green"
                        size="md"
                        round
                    >
                        <q-tooltip>{{ props.value ? "Reabrir prazo" : "Marcar como concluído" }}</q-tooltip>
                    </q-checkbox>
                </q-td>
            ''')

            # Slot para Título (com fundo vermelho se atrasado)
            table.add_slot('body-cell-titulo', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Responsáveis (com fundo vermelho se atrasado)
            table.add_slot('body-cell-responsaveis', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Clientes (com fundo vermelho se atrasado)
            table.add_slot('body-cell-clientes', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Prazo de Segurança (amarelo pastel, ou vermelho se atrasado)
            table.add_slot('body-cell-prazo_seguranca', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle; text-align: center;' : 'background-color: #FFF9C4; vertical-align: middle; text-align: center;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Prazo Fatal (vermelho pastel sempre, mais escuro se atrasado)
            table.add_slot('body-cell-prazo_fatal', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #EF9A9A; vertical-align: middle; text-align: center; font-weight: bold;' : 'background-color: #FFCDD2; vertical-align: middle; text-align: center;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Recorrente (com fundo vermelho se atrasado)
            table.add_slot('body-cell-recorrente', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle; text-align: center;' : 'vertical-align: middle; text-align: center;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para ações (editar e excluir)
            table.add_slot('body-cell-acoes', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
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

            # Handler para toggle de status COM CONFIRMAÇÃO
            def on_toggle_status(data):
                """Handler para alterar status via checkbox - abre diálogo de confirmação."""
                prazo_row = data.get('row')
                novo_valor = data.get('value')
                prazo_id = prazo_row.get('id')
                titulo = prazo_row.get('titulo', 'este prazo')

                if prazo_id:
                    if novo_valor:
                        # Marcar como concluído - pedir confirmação
                        confirmar_conclusao_prazo(prazo_id, titulo)
                    else:
                        # Reabrir prazo - pedir confirmação
                        confirmar_reabertura_prazo(prazo_id, titulo)

            # Handlers para ações
            def on_edit_tb(prazo_row):
                """Handler para editar prazo."""
                prazo_id = prazo_row.get('id')
                if prazo_id:
                    abrir_modal_edicao(prazo_id)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            def on_delete_tb(prazo_row):
                """Handler para excluir prazo."""
                prazo_id = prazo_row.get('id')
                titulo = prazo_row.get('titulo', 'este prazo')
                if prazo_id:
                    excluir_prazo_com_confirmacao(prazo_id, titulo)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            table.on('toggle-status', lambda e: on_toggle_status(e.args))
            table.on('edit', lambda e: on_edit_tb(e.args))
            table.on('delete', lambda e: on_delete_tb(e.args))

        # Função para criar tabela COM coluna de status (para aba Por Semana)
        def criar_tabela_prazos_com_status(prazos_lista: List[Dict[str, Any]]):
            """Cria tabela de prazos com coluna de status (para visualização Por Semana)."""
            if not prazos_lista:
                with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                    ui.icon('event_busy', size='48px').classes('text-gray-300 mb-4')
                    ui.label('Nenhum prazo nesta semana').classes(
                        'text-gray-500 text-lg font-medium mb-2'
                    )
                    ui.label('Selecione outra semana ou adicione novos prazos').classes(
                        'text-sm text-gray-400 text-center'
                    )
                return

            # Definir colunas da tabela COM coluna de status
            columns = [
                {'name': 'concluido', 'label': '', 'field': 'concluido', 'align': 'center', 'style': 'width: 50px;'},
                {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left'},
                {'name': 'responsaveis', 'label': 'Responsáveis', 'field': 'responsaveis', 'align': 'left', 'style': 'width: 180px;'},
                {'name': 'prazo_seguranca', 'label': 'Prazo Seg.', 'field': 'prazo_seguranca', 'align': 'center', 'style': 'width: 110px;'},
                {'name': 'prazo_fatal', 'label': 'Prazo Fatal', 'field': 'prazo_fatal', 'align': 'center', 'style': 'width: 110px;'},
                {'name': 'status', 'label': 'Status', 'field': 'status_label', 'align': 'center', 'style': 'width: 120px;'},
                {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 100px;'},
            ]

            # Preparar linhas
            rows = []
            for prazo in prazos_lista:
                titulo = prazo.get('titulo', '-')

                responsaveis_ids = prazo.get('responsaveis', [])
                responsaveis_texto = formatar_responsaveis(responsaveis_ids, usuarios_opcoes)

                prazo_fatal_ts = prazo.get('prazo_fatal')
                prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
                prazo_seguranca_texto = calcular_prazo_seguranca(prazo_fatal_ts)

                status = prazo.get('status', 'pendente')
                esta_concluido = status.lower() == 'concluido'
                esta_atrasado = verificar_prazo_atrasado(prazo_fatal_ts, status)

                # Determinar status_label para exibição
                if esta_concluido:
                    status_label = 'Concluído'
                    status_value = 'concluido'
                elif esta_atrasado:
                    status_label = 'Atrasado'
                    status_value = 'atrasado'
                else:
                    status_label = 'Pendente'
                    status_value = 'pendente'

                rows.append({
                    'id': prazo.get('_id'),
                    'concluido': esta_concluido,
                    'atrasado': esta_atrasado,
                    'titulo': titulo,
                    'responsaveis': responsaveis_texto,
                    'prazo_seguranca': prazo_seguranca_texto,
                    'prazo_fatal': prazo_fatal_texto,
                    'status_label': status_label,
                    'status_value': status_value,
                    'acoes': prazo.get('_id'),
                })

            # Criar tabela
            table = ui.table(
                columns=columns,
                rows=rows,
                row_key='id'
            ).classes('w-full').props('flat dense')

            # Slot para checkbox de concluído
            table.add_slot('body-cell-concluido', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    <q-checkbox
                        :model-value="props.value"
                        @update:model-value="(val) => $parent.$emit('toggle-status', {row: props.row, value: val})"
                        color="green"
                        size="md"
                        round
                    >
                        <q-tooltip>{{ props.value ? "Reabrir prazo" : "Marcar como concluído" }}</q-tooltip>
                    </q-checkbox>
                </q-td>
            ''')

            # Slot para Título
            table.add_slot('body-cell-titulo', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Responsáveis
            table.add_slot('body-cell-responsaveis', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Prazo de Segurança
            table.add_slot('body-cell-prazo_seguranca', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle; text-align: center;' : 'background-color: #FFF9C4; vertical-align: middle; text-align: center;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Prazo Fatal
            table.add_slot('body-cell-prazo_fatal', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #EF9A9A; vertical-align: middle; text-align: center; font-weight: bold;' : 'background-color: #FFCDD2; vertical-align: middle; text-align: center;'">
                    {{ props.value }}
                </q-td>
            ''')

            # Slot para Status com badge colorido
            table.add_slot('body-cell-status', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle; text-align: center;' : 'vertical-align: middle; text-align: center;'">
                    <q-badge
                        :style="props.row.status_value === 'atrasado' ? 'background-color: #EF5350; color: white;' :
                                props.row.status_value === 'concluido' ? 'background-color: #4CAF50; color: white;' :
                                'background-color: #FFC107; color: black;'"
                        class="px-3 py-1"
                    >
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')

            # Slot para ações
            table.add_slot('body-cell-acoes', '''
                <q-td :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2; vertical-align: middle;' : 'vertical-align: middle;'">
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

            # Handler para toggle de status
            def on_toggle_status(data):
                prazo_row = data.get('row')
                novo_valor = data.get('value')
                prazo_id = prazo_row.get('id')
                titulo = prazo_row.get('titulo', 'este prazo')

                if prazo_id:
                    if novo_valor:
                        confirmar_conclusao_prazo(prazo_id, titulo)
                    else:
                        confirmar_reabertura_prazo(prazo_id, titulo)

            def on_edit_tb(prazo_row):
                prazo_id = prazo_row.get('id')
                if prazo_id:
                    abrir_modal_edicao(prazo_id)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            def on_delete_tb(prazo_row):
                prazo_id = prazo_row.get('id')
                titulo = prazo_row.get('titulo', 'este prazo')
                if prazo_id:
                    excluir_prazo_com_confirmacao(prazo_id, titulo)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            table.on('toggle-status', lambda e: on_toggle_status(e.args))
            table.on('edit', lambda e: on_edit_tb(e.args))
            table.on('delete', lambda e: on_delete_tb(e.args))

        # Container para tabelas
        with ui.tab_panels(tabs, value=tab_pendentes).classes('w-full'):
            # =================================================================
            # ABA PENDENTES - Mostra TODOS os pendentes (visão geral)
            # =================================================================
            with ui.tab_panel(tab_pendentes):
                @ui.refreshable
                def render_tabela_pendentes():
                    """Renderiza tabela com TODOS os prazos pendentes."""
                    try:
                        print("[PRAZOS] Carregando todos os prazos pendentes...")

                        # Buscar TODOS os prazos pendentes (sem filtro de semana)
                        prazos_lista = listar_prazos_por_status('pendente')

                        # Ordenar por prazo_fatal (mais próximo primeiro)
                        prazos_lista.sort(key=lambda p: p.get('prazo_fatal', 0))

                        pendentes_count = len(prazos_lista)
                        print(f"[PRAZOS] {pendentes_count} prazos pendentes encontrados")

                        criar_tabela_prazos(prazos_lista, 'pendente')
                    except Exception as e:
                        print(f"[ERROR] Erro ao carregar prazos pendentes: {e}")
                        import traceback
                        traceback.print_exc()
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('error', size='48px').classes('text-red-400 mb-4')
                            ui.label('Erro ao carregar prazos').classes(
                                'text-red-600 text-lg font-medium mb-2'
                            )
                            ui.label(f'Detalhes: {str(e)}').classes(
                                'text-sm text-gray-500 text-center'
                            )

                # Salvar referência e renderizar
                refresh_funcs['pendentes'] = render_tabela_pendentes
                render_tabela_pendentes()

            # =================================================================
            # ABA CONCLUÍDOS - Mostra TODOS os concluídos
            # =================================================================
            with ui.tab_panel(tab_concluidos):
                @ui.refreshable
                def render_tabela_concluidos():
                    """Renderiza tabela com TODOS os prazos concluídos."""
                    try:
                        print("[PRAZOS] Carregando todos os prazos concluídos...")

                        # Buscar TODOS os prazos concluídos
                        prazos_lista = listar_prazos_por_status('concluido')

                        # Ordenar por atualizado_em (mais recente primeiro)
                        prazos_lista.sort(key=lambda p: p.get('atualizado_em', 0), reverse=True)

                        concluidos_count = len(prazos_lista)
                        print(f"[PRAZOS] {concluidos_count} prazos concluídos encontrados")

                        criar_tabela_prazos(prazos_lista, 'concluido')
                    except Exception as e:
                        print(f"[ERROR] Erro ao carregar prazos concluídos: {e}")
                        import traceback
                        traceback.print_exc()
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('error', size='48px').classes('text-red-400 mb-4')
                            ui.label('Erro ao carregar prazos').classes(
                                'text-red-600 text-lg font-medium mb-2'
                            )
                            ui.label(f'Detalhes: {str(e)}').classes(
                                'text-sm text-gray-500 text-center'
                            )

                # Salvar referência e renderizar
                refresh_funcs['concluidos'] = render_tabela_concluidos
                render_tabela_concluidos()

            # =================================================================
            # ABA POR SEMANA - Mostra TODOS os prazos da semana selecionada
            # =================================================================
            with ui.tab_panel(tab_semana):
                # Estado do filtro de semana
                filtro_semana = {'tipo': 'esta_semana', 'semana_especifica': None}

                def obter_periodo_filtro():
                    """Retorna início e fim baseado no filtro atual."""
                    if filtro_semana['tipo'] == 'semana_passada':
                        return obter_semana_passada()
                    elif filtro_semana['tipo'] == 'proxima_semana':
                        return obter_proxima_semana()
                    elif filtro_semana['tipo'] == 'selecionar' and filtro_semana['semana_especifica']:
                        ano, num_semana = filtro_semana['semana_especifica']
                        return obter_semana_do_ano(ano, num_semana)
                    else:  # esta_semana (padrão)
                        return obter_esta_semana()

                def selecionar_filtro(tipo: str):
                    """Seleciona um filtro de semana."""
                    filtro_semana['tipo'] = tipo
                    filtro_semana['semana_especifica'] = None
                    render_filtros_semana.refresh()
                    render_tabela_semana.refresh()

                def selecionar_semana_especifica(valor):
                    """Seleciona uma semana específica do dropdown."""
                    if valor:
                        try:
                            partes = valor.split('-')
                            ano = int(partes[0])
                            num_semana = int(partes[1])
                            filtro_semana['tipo'] = 'selecionar'
                            filtro_semana['semana_especifica'] = (ano, num_semana)
                            render_filtros_semana.refresh()
                            render_tabela_semana.refresh()
                        except Exception as e:
                            print(f"[ERROR] Erro ao selecionar semana: {e}")

                # Filtros de semana
                @ui.refreshable
                def render_filtros_semana():
                    """Renderiza os botões de filtro por semana."""
                    inicio, fim = obter_periodo_filtro()

                    with ui.row().classes('w-full gap-2 mb-4 items-center flex-wrap'):
                        # Botões de filtro rápido
                        btn_passada = ui.button(
                            'Semana Passada',
                            icon='chevron_left',
                            on_click=lambda: selecionar_filtro('semana_passada')
                        )
                        if filtro_semana['tipo'] == 'semana_passada':
                            btn_passada.props('color=primary unelevated')
                        else:
                            btn_passada.props('flat')

                        btn_esta = ui.button(
                            'Esta Semana',
                            icon='today',
                            on_click=lambda: selecionar_filtro('esta_semana')
                        )
                        if filtro_semana['tipo'] == 'esta_semana':
                            btn_esta.props('color=primary unelevated')
                        else:
                            btn_esta.props('flat')

                        btn_proxima = ui.button(
                            'Próxima Semana',
                            icon='chevron_right',
                            on_click=lambda: selecionar_filtro('proxima_semana')
                        )
                        if filtro_semana['tipo'] == 'proxima_semana':
                            btn_proxima.props('color=primary unelevated')
                        else:
                            btn_proxima.props('flat')

                        # Separador
                        ui.label('|').classes('text-gray-300 mx-2')

                        # Dropdown para selecionar semana específica
                        opcoes_semanas = criar_opcoes_semanas()
                        valor_atual = None
                        if filtro_semana['tipo'] == 'selecionar' and filtro_semana['semana_especifica']:
                            ano, num = filtro_semana['semana_especifica']
                            valor_atual = f"{ano}-{num}"

                        select_semana = ui.select(
                            options=opcoes_semanas,
                            value=valor_atual,
                            label='Selecionar Semana',
                            on_change=lambda e: selecionar_semana_especifica(e.value)
                        ).classes('w-64')

                        if filtro_semana['tipo'] == 'selecionar':
                            select_semana.props('outlined color=primary')
                        else:
                            select_semana.props('outlined')

                    # Label do período atual
                    with ui.row().classes('w-full mb-2'):
                        ui.icon('date_range', size='18px').classes('text-gray-500')
                        ui.label(f"Período: {formatar_periodo_semana(inicio, fim)}").classes(
                            'text-sm text-gray-600 font-medium'
                        )

                render_filtros_semana()

                @ui.refreshable
                def render_tabela_semana():
                    """Renderiza tabela com TODOS os prazos da semana (pendentes, atrasados e concluídos)."""
                    try:
                        print("[PRAZOS] Carregando prazos da semana...")

                        # Buscar TODOS os prazos (não filtrado por status)
                        todos_prazos = listar_prazos()

                        # Obter período do filtro
                        inicio, fim = obter_periodo_filtro()

                        # Filtrar prazos pela semana selecionada
                        prazos_semana = filtrar_prazos_por_semana(todos_prazos, inicio, fim)

                        # Ordenar por prazo_fatal (mais próximo primeiro)
                        prazos_semana.sort(key=lambda p: p.get('prazo_fatal', 0))

                        total_semana = len(prazos_semana)
                        print(f"[PRAZOS] {total_semana} prazos encontrados na semana")

                        # Mostrar contador
                        with ui.row().classes('w-full mb-2 items-center'):
                            ui.label(f'{total_semana} prazo(s) nesta semana').classes(
                                'text-sm text-gray-500'
                            )

                        criar_tabela_prazos_com_status(prazos_semana)
                    except Exception as e:
                        print(f"[ERROR] Erro ao carregar prazos da semana: {e}")
                        import traceback
                        traceback.print_exc()
                        with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                            ui.icon('error', size='48px').classes('text-red-400 mb-4')
                            ui.label('Erro ao carregar prazos').classes(
                                'text-red-600 text-lg font-medium mb-2'
                            )
                            ui.label(f'Detalhes: {str(e)}').classes(
                                'text-sm text-gray-500 text-center'
                            )

                # Salvar referência e renderizar
                refresh_funcs['semana'] = render_tabela_semana
                render_tabela_semana()

    print("[PRAZOS] Página carregada com sucesso!")
