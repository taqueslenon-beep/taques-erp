"""
modal_prazo.py - Modal para criar/editar prazo.
"""

from nicegui import ui
from typing import Optional, Callable, Dict, Any
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import uuid
from ...core import PRIMARY_COLOR
from .database import (
    criar_prazo,
    atualizar_prazo,
    listar_prazos,
    buscar_usuarios_para_select,
    buscar_clientes_para_select,
    buscar_casos_para_select,
)
from .models import (
    STATUS_OPCOES,
    STATUS_LABELS,
    TIPOS_RECORRENCIA,
    TIPOS_RECORRENCIA_LABELS,
    OPCOES_SEMANA,
    OPCOES_SEMANA_LABELS,
    OPCOES_DIA_SEMANA,
    OPCOES_DIA_SEMANA_LABELS,
    ESTADO_ABERTURA_OPCOES,
    ESTADO_ABERTURA_LABELS,
    ESTADO_ABERTURA_PADRAO,
)
from ...auth import get_current_user


def validar_data_br(data_str: str) -> bool:
    """
    Valida formato de data brasileira DD/MM/AAAA.
    
    Args:
        data_str: String com data em formato DD/MM/AAAA
    
    Returns:
        True se válida, False caso contrário
    """
    import re
    
    if not data_str or not isinstance(data_str, str):
        return False
    
    # Verificar formato
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', data_str.strip()):
        return False
    
    try:
        dia, mes, ano = data_str.strip().split('/')
        dia, mes, ano = int(dia), int(mes), int(ano)
        
        # Validar ranges
        if mes < 1 or mes > 12:
            return False
        if ano < 1900 or ano > 2100:
            return False
        
        # Dias por mês (simplificado - não considera anos bissextos)
        dias_mes = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        if dia < 1 or dia > dias_mes[mes - 1]:
            return False
        
        return True
    except Exception:
        return False


def converter_data_br_para_timestamp(data_str: str) -> Optional[float]:
    """
    Converte data no formato DD/MM/AAAA para timestamp.
    
    Args:
        data_str: Data no formato DD/MM/AAAA
    
    Returns:
        Timestamp (float) ou None se inválida
    """
    if not validar_data_br(data_str):
        return None
    
    try:
        dia, mes, ano = data_str.strip().split('/')
        dt = datetime(int(ano), int(mes), int(dia))
        return dt.timestamp()
    except Exception:
        return None


def converter_timestamp_para_data_br(timestamp: Optional[float]) -> str:
    """
    Converte timestamp para data no formato DD/MM/AAAA.
    
    Args:
        timestamp: Timestamp (float) ou None
    
    Returns:
        Data formatada como DD/MM/AAAA ou string vazia
    """
    if not timestamp:
        return ''
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return ''


def _data_br_para_date(data_str: str) -> Optional[date]:
    """Converte DD/MM/AAAA em date."""
    if not validar_data_br(data_str):
        return None
    try:
        dia, mes, ano = data_str.strip().split('/')
        return date(int(ano), int(mes), int(dia))
    except Exception:
        return None


def _date_para_timestamp_inicio_dia(dt: date) -> float:
    """Converte date para timestamp (00:00) para padrão do módulo."""
    return datetime(dt.year, dt.month, dt.day).timestamp()


def _gerar_id_parcelamento() -> str:
    """Gera um ID único para agrupar parcelas no Firestore (sem backend)."""
    return f"parcelamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _calcular_datas_parcelas(
    data_base: date,
    total: int,
    intervalo: str,
    intervalo_dias_customizado: Optional[int] = None,
) -> list[date]:
    """
    Calcula datas de vencimento das parcelas.
    
    Regras:
    - Parcela 1: data_base
    - Semanal: +7 dias
    - Quinzenal: +15 dias
    - Mensal: +1 mês
    - Anual: +1 ano
    - Customizado: +N dias
    """
    if total < 2:
        raise ValueError('Não é possível gerar menos de 2 parcelas')

    datas = [data_base]
    atual = data_base

    for _ in range(2, total + 1):
        if intervalo == 'semanal':
            atual = atual + timedelta(days=7)
        elif intervalo == 'quinzenal':
            atual = atual + timedelta(days=15)
        elif intervalo == 'mensal':
            atual = atual + relativedelta(months=1)
        elif intervalo == 'anual':
            atual = atual + relativedelta(years=1)
        elif intervalo == 'customizado':
            dias = int(intervalo_dias_customizado or 0)
            if dias <= 0:
                raise ValueError('Intervalo em dias inválido')
            atual = atual + timedelta(days=dias)
        else:
            # Padrão: mensal
            atual = atual + relativedelta(months=1)

        datas.append(atual)

    return datas


def render_prazo_dialog(
    on_success: Optional[Callable] = None,
    prazo_inicial: Optional[Dict] = None,
    usuarios_opcoes: Optional[Dict[str, str]] = None,
    clientes_opcoes: Optional[Dict[str, str]] = None,
    casos_opcoes: Optional[Dict[str, str]] = None
):
    """
    Renderiza dialog para criar ou editar prazo.

    Args:
        on_success: Callback executado após salvar
        prazo_inicial: Dicionário com dados do prazo para edição (None para novo)
        usuarios_opcoes: Opções de usuários (se None, busca do banco)
        clientes_opcoes: Opções de clientes (se None, busca do banco)
        casos_opcoes: Opções de casos (se None, busca do banco)

    Returns:
        tuple: (dialog, open_function)
    """

    # Determinar se é edição ou criação
    # Validação defensiva: prazo_inicial deve ser dict não vazio
    is_edicao = prazo_inicial is not None and isinstance(prazo_inicial, dict) and len(prazo_inicial) > 0
    
    if prazo_inicial is not None and not is_edicao:
        print(f"[DEBUG] render_prazo_dialog: prazo_inicial inválido: {type(prazo_inicial)} - {prazo_inicial}")
    
    # Garantir que prazo_inicial é um dict para evitar erros de .get()
    prazo_inicial_safe = prazo_inicial if is_edicao else {}
    
    prazo_id = prazo_inicial_safe.get('_id') if is_edicao else None
    print(f"[DEBUG] render_prazo_dialog: is_edicao={is_edicao}, prazo_id={prazo_id}")

    # Estado do formulário - preencher com dados iniciais se for edição
    # Usar prazo_inicial_safe para evitar NoneType has no attribute 'get'
    config_recorrencia_inicial = prazo_inicial_safe.get('config_recorrencia') or {}
    dia_semana_inicial = config_recorrencia_inicial.get('dia_semana_especifico') or {}

    # Detecta se é uma parcela (prazo parcelado)
    parcelamento_id_inicial = prazo_inicial_safe.get('parcelamento_id') if is_edicao else None
    parcela_numero_inicial = prazo_inicial_safe.get('parcela_numero') if is_edicao else None
    parcela_total_inicial = prazo_inicial_safe.get('parcela_total') if is_edicao else None
    
    print(f"[DEBUG] render_prazo_dialog: parcelamento_id={parcelamento_id_inicial}, parcela={parcela_numero_inicial}/{parcela_total_inicial}")

    # Monta estado inicial do formulário usando prazo_inicial_safe (nunca None)
    state = {
        'titulo': prazo_inicial_safe.get('titulo', '') if is_edicao else '',
        'estado_abertura': prazo_inicial_safe.get('estado_abertura', ESTADO_ABERTURA_PADRAO) if is_edicao else ESTADO_ABERTURA_PADRAO,
        'responsaveis': prazo_inicial_safe.get('responsaveis') or [] if is_edicao else [],
        'clientes': prazo_inicial_safe.get('clientes') or [] if is_edicao else [],
        'casos': prazo_inicial_safe.get('casos') or [] if is_edicao else [],
        'prazo_fatal': converter_timestamp_para_data_br(
            prazo_inicial_safe.get('prazo_fatal')
        ) if is_edicao else '',
        'status': prazo_inicial_safe.get('status', 'pendente') if is_edicao else 'pendente',
        'recorrente': prazo_inicial_safe.get('recorrente', False) if is_edicao else False,
        'tipo_recorrencia': config_recorrencia_inicial.get('tipo', 'mensal') if is_edicao else 'mensal',
        'dia_especifico': config_recorrencia_inicial.get('dia_especifico') if is_edicao else None,
        'ultimo_dia_mes': config_recorrencia_inicial.get('ultimo_dia_mes', False) if is_edicao else False,
        'semana_especifica': dia_semana_inicial.get('semana', 'primeira') if is_edicao else 'primeira',
        'dia_semana': dia_semana_inicial.get('dia', 'segunda') if is_edicao else 'segunda',
        'observacoes': prazo_inicial_safe.get('observacoes', '') if is_edicao else '',

        # Tipo de prazo (novo controle: simples/recorrente/parcelado)
        'tipo_prazo': (
            'parcelado'
            if parcelamento_id_inicial
            else ('recorrente' if prazo_inicial_safe.get('recorrente', False) else 'simples')
        ),

        # Parcelamento (somente UI no modal; salvamento cria N documentos)
        'parcelamento_numero_parcelas': 2,
        'parcelamento_intervalo': 'mensal',
        'parcelamento_intervalo_dias': None,
        'parcelas_geradas': [],  # lista de dicts: {numero, total, vencimento_ts, vencimento_original_ts}
    }
    
    print(f"[DEBUG] render_prazo_dialog: state inicializado - titulo='{state.get('titulo', '')}', tipo_prazo='{state.get('tipo_prazo', 'simples')}'")

    # Usar opções passadas ou buscar do banco (com cache)
    if usuarios_opcoes is None:
        usuarios_opcoes = buscar_usuarios_para_select()
    if clientes_opcoes is None:
        clientes_opcoes = buscar_clientes_para_select()
    if casos_opcoes is None:
        casos_opcoes = buscar_casos_para_select()

    # Fallback se não houver usuários
    if not usuarios_opcoes:
        usuarios_opcoes = {'-': 'Nenhum usuário cadastrado'}

    # CSS local do modal (chips de tipo de prazo + rodapé fixo)
    ui.add_head_html('''
    <style>
      /* Botões compactos (estilo chip) para Tipo de Prazo */
      .tipo-prazo-btn {
        height: 38px !important;
        min-height: 38px !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        line-height: 1 !important;
      }
      /* Rodapé fixo do modal */
      .rodape-modal-prazo {
        position: sticky;
        bottom: 0;
        z-index: 5;
      }
    </style>
    ''')

    # =========================================================
    # Dialog auxiliar: ver todas as parcelas de um parcelamento
    # DEFINIDA ANTES DE SER USADA para evitar erro de referência
    # =========================================================
    def _abrir_dialog_parcelas(parcelamento_id: str):
        """Abre um dialog simples listando todas as parcelas do mesmo parcelamento."""
        if not parcelamento_id:
            ui.notify('ID do parcelamento não informado', type='warning')
            return
        
        try:
            todos = listar_prazos()
            parcelas = [p for p in (todos or []) if p.get('parcelamento_id') == parcelamento_id]
            parcelas.sort(key=lambda p: p.get('parcela_numero', 0))
        except Exception as e:
            print(f"[ERROR] Erro ao buscar parcelas: {e}")
            import traceback
            traceback.print_exc()
            parcelas = []
            ui.notify('Erro ao carregar parcelas', type='negative')

        try:
            with ui.dialog() as d, ui.card().classes('w-full max-w-2xl'):
                with ui.column().classes('w-full gap-3 p-4'):
                    ui.label('Parcelas deste parcelamento').classes('text-lg font-bold')
                    if not parcelas:
                        ui.label('Nenhuma parcela encontrada.').classes('text-gray-500')
                    else:
                        rows = []
                        for p in parcelas:
                            try:
                                rows.append({
                                    'parcela': f"{p.get('parcela_numero', '-')}/{p.get('parcela_total', '-')}",
                                    'vencimento': converter_timestamp_para_data_br(p.get('prazo_fatal')),
                                    'status': p.get('status', '-'),
                                })
                            except Exception as e:
                                print(f"[ERROR] Erro ao processar parcela: {e}")
                                continue
                        
                        if rows:
                            ui.table(
                                columns=[
                                    {'name': 'parcela', 'label': 'Parcela', 'field': 'parcela', 'align': 'left'},
                                    {'name': 'vencimento', 'label': 'Vencimento', 'field': 'vencimento', 'align': 'center'},
                                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                                ],
                                rows=rows,
                                row_key='parcela'
                            ).classes('w-full').props('flat dense')

                    with ui.row().classes('w-full justify-end'):
                        ui.button('Fechar', icon='close', on_click=d.close).props('flat')
            d.open()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir dialog de parcelas: {e}")
            import traceback
            traceback.print_exc()
            ui.notify('Erro ao abrir visualização de parcelas', type='negative')

    # Dialog principal
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl p-0 overflow-hidden'):
        with ui.column().classes('w-full gap-0'):
            # Cabeçalho
            titulo_dialog = ui.label(
                'Editar Prazo' if is_edicao else 'Novo Prazo'
            ).classes('text-xl font-bold p-4 bg-gray-50 border-b')
            
            # Conteúdo (scrollável)
            with ui.column().classes('w-full p-6 gap-4 overflow-auto').style('max-height: 70vh;'):

                # Informações extras quando é parcela (edição)
                if is_edicao and parcelamento_id_inicial and parcela_numero_inicial and parcela_total_inicial:
                    with ui.card().classes('w-full p-4 bg-blue-50 border border-blue-100'):
                        ui.label(f'Esta é a Parcela {parcela_numero_inicial} de {parcela_total_inicial}').classes('font-bold text-blue-800')
                        ui.label('Alterar esta parcela não afeta as demais.').classes('text-sm text-blue-700')
                        ui.button(
                            'Ver todas as parcelas deste parcelamento',
                            icon='view_list',
                            on_click=lambda pid=parcelamento_id_inicial: _abrir_dialog_parcelas(pid)
                        ).props('flat color=primary').classes('mt-2')
                
                # Título
                titulo_input = ui.input(
                    label='Título *',
                    placeholder='Digite o título do prazo',
                    value=state['titulo']
                ).classes('w-full').props('outlined dense')
                
                # Estado de Abertura
                estado_abertura_options = {
                    op: ESTADO_ABERTURA_LABELS.get(op, op)
                    for op in ESTADO_ABERTURA_OPCOES
                }
                estado_abertura_select = ui.select(
                    estado_abertura_options,
                    label='Estado de Abertura',
                    value=state['estado_abertura']
                ).classes('w-full').props('outlined dense')
                
                # Responsáveis (múltiplo) - usando mesma lógica de casos_page.py
                ui.label('Responsável(is) *').classes('text-sm font-medium text-gray-700')
                responsaveis_select = ui.select(
                    options=usuarios_opcoes,
                    label='Selecione o(s) responsável(eis)',
                    value=state['responsaveis'],
                    with_input=True,
                    multiple=True
                ).classes('w-full').props('use-chips clearable outlined dense')
                
                # Clientes (múltiplo)
                ui.label('Clientes').classes('text-sm font-medium text-gray-700 mt-2')
                clientes_select = ui.select(
                    options=clientes_opcoes,
                    label='Selecione os clientes',
                    value=state['clientes'],
                    with_input=True,
                    multiple=True
                ).classes('w-full').props('use-chips clearable outlined dense')

                # Casos (múltiplo)
                ui.label('Casos').classes('text-sm font-medium text-gray-700 mt-2')
                casos_select = ui.select(
                    options=casos_opcoes,
                    label='Selecione os casos',
                    value=state['casos'],
                    with_input=True,
                    multiple=True
                ).classes('w-full').props('use-chips clearable outlined dense')
                
                # Prazo Fatal
                prazo_fatal_input = ui.input(
                    label='Prazo Fatal *',
                    placeholder='DD/MM/AAAA',
                    value=state['prazo_fatal']
                ).classes('w-full').props('outlined dense')
                prazo_fatal_input.validation = {'Data inválida': validar_data_br}
                
                # Função para atualizar visibilidade do prazo fatal (deve vir depois da criação do campo)
                def atualizar_visibilidade_prazo_fatal():
                    """Atualiza a visibilidade/habilitado do campo prazo fatal baseado no estado de abertura."""
                    estado = estado_abertura_select.value or ESTADO_ABERTURA_PADRAO
                    state['estado_abertura'] = estado
                    
                    # Se for "aguardando_abertura", desabilita o campo prazo_fatal
                    if estado == 'aguardando_abertura':
                        prazo_fatal_input.props('disabled')
                        # Limpa o valor se estava preenchido
                        if prazo_fatal_input.value:
                            prazo_fatal_input.value = ''
                    else:
                        # Se for "aberto", habilita o campo
                        prazo_fatal_input.props(remove='disabled')
                
                # Atualizar inicialmente e quando o estado mudar
                atualizar_visibilidade_prazo_fatal()
                estado_abertura_select.on('update:model-value', lambda: atualizar_visibilidade_prazo_fatal())
                
                # Status
                status_options = {op: STATUS_LABELS.get(op, op) for op in STATUS_OPCOES}
                status_select = ui.select(
                    status_options,
                    label='Status',
                    value=state['status']
                ).classes('w-full').props('outlined dense')

                # =========================
                # Tipo de Prazo (exclusivo)
                # =========================
                ui.label('Tipo de Prazo').classes('text-sm font-medium text-gray-700 mt-2')
                tipo_prazo_row = ui.row().classes('w-full gap-2 items-center justify-start')

                refs_tipo = {'btn_simples': None, 'btn_recorrente': None, 'btn_parcelado': None}

                parcelamento_container = ui.column().classes('w-full gap-3')

                def atualizar_estilo_botoes_tipo():
                    """Atualiza o visual dos botões com base no tipo selecionado."""
                    tipo_atual = state.get('tipo_prazo', 'simples')
                    for key, tipo in [
                        ('btn_simples', 'simples'),
                        ('btn_recorrente', 'recorrente'),
                        ('btn_parcelado', 'parcelado'),
                    ]:
                        btn = refs_tipo.get(key)
                        if not btn:
                            continue
                        if tipo_atual == tipo:
                            btn.props('color=primary unelevated')
                        else:
                            btn.props('outline color=grey-6')

                def set_tipo_prazo(tipo: str):
                    """Define tipo de prazo, garantindo exclusividade e sincronizando o switch de recorrência."""
                    # Regras de edição:
                    # - Se estiver editando uma parcela, bloqueia alteração de tipo.
                    if is_edicao and parcelamento_id_inicial:
                        ui.notify('Este prazo é uma parcela. O tipo não pode ser alterado aqui.', type='warning')
                        state['tipo_prazo'] = 'parcelado'
                        atualizar_estilo_botoes_tipo()
                        return
                    # - Se estiver editando um prazo normal, bloqueia virar parcelado (para evitar duplicação).
                    if is_edicao and (not parcelamento_id_inicial) and tipo == 'parcelado':
                        ui.notify('Para criar um parcelamento, crie um NOVO prazo e selecione "Parcelado".', type='warning')
                        return

                    state['tipo_prazo'] = tipo

                    if tipo == 'recorrente':
                        recorrente_switch.value = True
                    else:
                        recorrente_switch.value = False

                    # Renderizações condicionais
                    render_secao_parcelamento()
                    render_secao_recorrencia()
                    atualizar_estilo_botoes_tipo()

                with tipo_prazo_row:
                    refs_tipo['btn_simples'] = ui.button(
                        'Simples',
                        on_click=lambda: set_tipo_prazo('simples')
                    ).props('size=sm').classes('tipo-prazo-btn w-32')

                    refs_tipo['btn_recorrente'] = ui.button(
                        'Recorrente',
                        on_click=lambda: set_tipo_prazo('recorrente')
                    ).props('size=sm').classes('tipo-prazo-btn w-32')

                    refs_tipo['btn_parcelado'] = ui.button(
                        'Parcelado',
                        on_click=lambda: set_tipo_prazo('parcelado')
                    ).props('size=sm').classes('tipo-prazo-btn w-32')

                # Dica
                ui.label('Dica: "Parcelado" cria vários itens (uma parcela por item).').classes('text-xs text-gray-500 -mt-1')
                
                # Recorrente (switch)
                recorrente_switch = ui.switch(
                    'Recorrente',
                    value=state['recorrente']
                ).classes('w-full')

                # =========================
                # Seção de Parcelamento
                # =========================
                refs_parcelamento = {
                    'numero_input': None,
                    'intervalo_select': None,
                    'dias_input': None,
                    'accordion_container': None,
                }

                def render_secao_parcelamento():
                    """
                    Renderiza seção de parcelamento apenas quando:
                    - tipo_prazo == 'parcelado'
                    - e NÃO é edição (parcelamento é criado no "Novo Prazo")
                    """
                    parcelamento_container.clear()
                    refs_parcelamento['numero_input'] = None
                    refs_parcelamento['intervalo_select'] = None
                    refs_parcelamento['dias_input'] = None
                    refs_parcelamento['accordion_container'] = None

                    if state.get('tipo_prazo') != 'parcelado':
                        return

                    if is_edicao:
                        # Não permite gerar novo parcelamento no modo edição (evita duplicação)
                        with parcelamento_container:
                            with ui.card().classes('w-full p-4 bg-yellow-50 border border-yellow-100'):
                                ui.label('Parcelamento').classes('font-bold text-yellow-800')
                                ui.label('Este é um prazo existente. Para criar um parcelamento, use "Novo Prazo".').classes('text-sm text-yellow-700')
                        return

                    with parcelamento_container:
                        ui.separator().classes('my-2')
                        ui.label('Configuração de Parcelamento').classes('text-sm font-bold text-gray-700')

                        with ui.row().classes('w-full gap-4 items-end'):
                            numero_parcelas_input = ui.number(
                                label='Número de Parcelas *',
                                value=state.get('parcelamento_numero_parcelas', 2),
                                min=2,
                                max=999,
                            ).classes('flex-1').props('outlined dense')
                            refs_parcelamento['numero_input'] = numero_parcelas_input

                            intervalo_options = {
                                'semanal': 'Semanal',
                                'quinzenal': 'Quinzenal',
                                'mensal': 'Mensal',
                                'anual': 'Anual',
                                'customizado': 'Customizado',
                            }
                            intervalo_select = ui.select(
                                intervalo_options,
                                label='Intervalo entre Parcelas',
                                value=state.get('parcelamento_intervalo', 'mensal'),
                            ).classes('flex-1').props('outlined dense')
                            refs_parcelamento['intervalo_select'] = intervalo_select

                        dias_custom_container = ui.column().classes('w-full')

                        def render_dias_customizados():
                            dias_custom_container.clear()
                            if refs_parcelamento['intervalo_select'] and refs_parcelamento['intervalo_select'].value == 'customizado':
                                with dias_custom_container:
                                    dias_input = ui.number(
                                        label='Intervalo em dias',
                                        value=state.get('parcelamento_intervalo_dias') or None,
                                        min=1,
                                        max=9999,
                                    ).classes('w-full').props('outlined dense')
                                    dias_input.tooltip('Usado apenas quando o intervalo está em "Customizado".')
                                    refs_parcelamento['dias_input'] = dias_input

                        render_dias_customizados()
                        intervalo_select.on('update:model-value', lambda: render_dias_customizados())

                        def gerar_parcelas_preview():
                            """Gera preview das parcelas e monta accordion editável."""
                            # Validação: parcelamento só é possível se o estado for "aberto"
                            estado_atual = estado_abertura_select.value or ESTADO_ABERTURA_PADRAO
                            if estado_atual == 'aguardando_abertura':
                                ui.notify('Não é possível criar parcelamento para prazos "Aguardando abertura". Mude o estado para "Aberto" primeiro.', type='warning')
                                return
                            
                            # Validações obrigatórias
                            if not prazo_fatal_input.value or not validar_data_br(prazo_fatal_input.value):
                                ui.notify('Por favor, preencha uma data válida em "Prazo Fatal".', type='warning')
                                return

                            n = int(refs_parcelamento['numero_input'].value or 0) if refs_parcelamento['numero_input'] else 0
                            if n < 2:
                                ui.notify('Não é possível gerar menos de 2 parcelas', type='warning')
                                return
                            if n > 999:
                                ui.notify('Número de parcelas máximo é 999', type='warning')
                                return

                            intervalo = refs_parcelamento['intervalo_select'].value if refs_parcelamento['intervalo_select'] else 'mensal'
                            dias_custom = None
                            if intervalo == 'customizado':
                                dias_custom = int(refs_parcelamento['dias_input'].value or 0) if refs_parcelamento['dias_input'] else 0
                                if not dias_custom or dias_custom <= 0:
                                    ui.notify('Por favor, preencha o "Intervalo em dias".', type='warning')
                                    return

                            data_base = _data_br_para_date(prazo_fatal_input.value)
                            if not data_base:
                                ui.notify('Data de vencimento inválida', type='warning')
                                return

                            try:
                                datas = _calcular_datas_parcelas(data_base, n, intervalo, dias_custom)
                            except Exception as e:
                                ui.notify(str(e), type='warning')
                                return

                            # Monta estado das parcelas
                            parcelas = []
                            for idx, dt_venc in enumerate(datas, start=1):
                                ts = _date_para_timestamp_inicio_dia(dt_venc)
                                parcelas.append({
                                    'numero': idx,
                                    'total': n,
                                    'vencimento_ts': ts,
                                    'vencimento_original_ts': ts,
                                })

                            state['parcelas_geradas'] = parcelas
                            ui.notify(f'Parcelas geradas: {n}', type='positive')
                            render_accordion_parcelas()

                        ui.button('Gerar Parcelas', icon='auto_awesome', on_click=gerar_parcelas_preview).props('color=primary')

                        # Accordion / preview (recolhível)
                        refs_parcelamento['accordion_container'] = ui.column().classes('w-full gap-2 mt-2')

                        def render_accordion_parcelas():
                            """
                            Renderiza um accordion de parcelas com edição de vencimento.
                            
                            Cada item permite:
                            - Editar data (DD/MM/AAAA)
                            - Redefinir para a data calculada automaticamente
                            """
                            container = refs_parcelamento['accordion_container']
                            if not container:
                                return
                            container.clear()

                            parcelas = state.get('parcelas_geradas') or []
                            if not parcelas:
                                return

                            with container:
                                ui.label(f'Parcelas Geradas ({len(parcelas)} total)').classes('text-sm font-bold text-gray-700')

                                for i, p in enumerate(parcelas):
                                    numero = p.get('numero', i + 1)
                                    total = p.get('total', len(parcelas))
                                    venc_ts = p.get('vencimento_ts')
                                    venc_br = converter_timestamp_para_data_br(venc_ts)

                                    exp = ui.expansion(f'Parcela {numero}/{total} - Vencimento: {venc_br}').classes('w-full')
                                    with exp:
                                        with ui.row().classes('w-full gap-3 items-end'):
                                            data_input = ui.input(
                                                label='Data de vencimento',
                                                placeholder='DD/MM/AAAA',
                                                value=venc_br,
                                            ).classes('flex-1').props('outlined dense')
                                            data_input.validation = {'Data inválida': validar_data_br}

                                            def _on_change_data(ev, idx=i):
                                                valor = ev.value
                                                if not valor:
                                                    return
                                                if not validar_data_br(valor):
                                                    ui.notify('Data de vencimento inválida', type='warning')
                                                    return
                                                ts_novo = converter_data_br_para_timestamp(valor)
                                                if not ts_novo:
                                                    ui.notify('Data de vencimento inválida', type='warning')
                                                    return
                                                state['parcelas_geradas'][idx]['vencimento_ts'] = ts_novo
                                                # Atualiza o título do item (re-render simples)
                                                render_accordion_parcelas()

                                            data_input.on('update:model-value', _on_change_data)

                                            def _redefinir(idx=i):
                                                state['parcelas_geradas'][idx]['vencimento_ts'] = state['parcelas_geradas'][idx]['vencimento_original_ts']
                                                render_accordion_parcelas()

                                            ui.button('Redefinir', icon='restart_alt', on_click=_redefinir).props('flat color=primary')

                # Render inicial da seção de parcelamento
                render_secao_parcelamento()
                
                # Seção de Recorrência (condicional)
                # Variáveis para armazenar referências dos campos de recorrência
                refs_recorrencia = {
                    'tipo_select': None,
                    'dia_especifico_input': None,
                    'ultimo_dia_checkbox': None,
                    'semana_select': None,
                    'dia_semana_select': None,
                }
                
                recorrencia_container = ui.column().classes('w-full gap-4')
                
                def render_secao_recorrencia():
                    """Renderiza seção de recorrência baseado no switch."""
                    recorrencia_container.clear()
                    # Limpar referências
                    for key in refs_recorrencia:
                        refs_recorrencia[key] = None
                    
                    if recorrente_switch.value:
                        with recorrencia_container:
                            ui.label('Configuração de Recorrência').classes(
                                'text-sm font-bold text-gray-700'
                            )
                            
                            # Tipo de recorrência
                            tipo_options = {
                                op: TIPOS_RECORRENCIA_LABELS.get(op, op)
                                for op in TIPOS_RECORRENCIA
                            }
                            tipo_recorrencia_select = ui.select(
                                tipo_options,
                                label='Tipo de Recorrência',
                                value=state['tipo_recorrencia']
                            ).classes('w-full').props('outlined dense')
                            refs_recorrencia['tipo_select'] = tipo_recorrencia_select
                            
                            # Container para opções específicas
                            opcoes_especificas_container = ui.column().classes('w-full gap-2')
                            
                            def render_opcoes_especificas():
                                """Renderiza opções específicas baseado no tipo."""
                                opcoes_especificas_container.clear()
                                tipo = tipo_recorrencia_select.value if tipo_recorrencia_select else state['tipo_recorrencia']
                                
                                if tipo in ['mensal', 'anual']:
                                    with opcoes_especificas_container:
                                        with ui.row().classes('w-full gap-4 items-center'):
                                            dia_especifico_input = ui.number(
                                                label='Dia específico (1-31)',
                                                value=state.get('dia_especifico'),
                                                min=1,
                                                max=31
                                            ).classes('flex-1').props('outlined dense')
                                            refs_recorrencia['dia_especifico_input'] = dia_especifico_input
                                            
                                            ultimo_dia_checkbox = ui.checkbox(
                                                'Último dia do mês',
                                                value=state.get('ultimo_dia_mes', False)
                                            ).classes('flex-1')
                                            refs_recorrencia['ultimo_dia_checkbox'] = ultimo_dia_checkbox
                                
                                elif tipo == 'semanal':
                                    with opcoes_especificas_container:
                                        semana_options = {
                                            op: OPCOES_SEMANA_LABELS.get(op, op)
                                            for op in OPCOES_SEMANA
                                        }
                                        semana_select = ui.select(
                                            semana_options,
                                            label='Qual semana',
                                            value=state.get('semana_especifica', 'primeira')
                                        ).classes('w-full').props('outlined dense')
                                        refs_recorrencia['semana_select'] = semana_select
                                        
                                        dia_semana_options = {
                                            op: OPCOES_DIA_SEMANA_LABELS.get(op, op)
                                            for op in OPCOES_DIA_SEMANA
                                        }
                                        dia_semana_select = ui.select(
                                            dia_semana_options,
                                            label='Qual dia da semana',
                                            value=state.get('dia_semana', 'segunda')
                                        ).classes('w-full').props('outlined dense')
                                        refs_recorrencia['dia_semana_select'] = dia_semana_select
                            
                            # Renderizar opções específicas inicialmente
                            render_opcoes_especificas()
                            
                            # Atualizar quando tipo mudar
                            tipo_recorrencia_select.on(
                                'update:model-value',
                                lambda: render_opcoes_especificas()
                            )
                
                # Renderizar seção de recorrência inicialmente
                render_secao_recorrencia()
                
                # Atualizar quando switch mudar
                def on_toggle_recorrente():
                    # Se ativar recorrente manualmente, desativa parcelado
                    if recorrente_switch.value:
                        state['tipo_prazo'] = 'recorrente'
                    else:
                        # Se estava recorrente e desligou, volta para simples (a menos que tenha parcelamento)
                        if state.get('tipo_prazo') == 'recorrente':
                            state['tipo_prazo'] = 'simples'
                    atualizar_estilo_botoes_tipo()
                    render_secao_parcelamento()
                    render_secao_recorrencia()

                recorrente_switch.on('update:model-value', lambda: on_toggle_recorrente())

                # Ajustar visual inicial dos botões
                atualizar_estilo_botoes_tipo()
                
                # Observações
                observacoes_input = ui.textarea(
                    label='Observações',
                    placeholder='Digite observações adicionais',
                    value=state['observacoes']
                ).classes('w-full').props('outlined dense rows=3')
            
            # Rodapé com botões
            with ui.row().classes('w-full gap-4 p-4 justify-between border-t bg-gray-50 rodape-modal-prazo'):
                def on_cancel():
                    """Cancela e fecha o dialog."""
                    dialog.close()
                
                def on_save():
                    """Salva o prazo."""
                    # Validar título
                    if not titulo_input.value or not titulo_input.value.strip():
                        ui.notify('Preencha o título do prazo', type='warning')
                        return
                    
                    # Validar responsáveis (pelo menos 1 obrigatório)
                    responsaveis_selecionados = responsaveis_select.value or []
                    if not responsaveis_selecionados or len(responsaveis_selecionados) == 0:
                        ui.notify('Selecione ao menos um responsável', type='warning')
                        return
                    
                    # Validar prazo fatal (somente se estado for "aberto")
                    estado_abertura_atual = estado_abertura_select.value or ESTADO_ABERTURA_PADRAO
                    if estado_abertura_atual == 'aberto':
                        if not prazo_fatal_input.value or not validar_data_br(prazo_fatal_input.value):
                            ui.notify('Preencha o prazo fatal (DD/MM/AAAA)', type='warning')
                            return
                    else:
                        # Se for "aguardando_abertura", não valida o prazo fatal
                        # Mas precisa garantir que não será salvo
                        if prazo_fatal_input.value:
                            prazo_fatal_input.value = ''
                    
                    # Converter data para timestamp (somente se estado for "aberto")
                    prazo_fatal_ts = None
                    if estado_abertura_atual == 'aberto':
                        prazo_fatal_ts = converter_data_br_para_timestamp(
                            prazo_fatal_input.value
                        )
                        if not prazo_fatal_ts:
                            ui.notify('Erro ao converter data do prazo fatal', type='negative')
                            return

                    tipo_prazo = state.get('tipo_prazo', 'simples')
                    
                    # Preparar dados do prazo
                    prazo_data = {
                        'titulo': titulo_input.value.strip(),
                        'estado_abertura': estado_abertura_atual,
                        'responsaveis': responsaveis_select.value or [],
                        'clientes': clientes_select.value or [],
                        'casos': casos_select.value or [],
                        'status': status_select.value or 'pendente',
                        'recorrente': recorrente_switch.value or False,
                        'observacoes': observacoes_input.value or '',
                    }
                    
                    # Adicionar prazo_fatal somente se estado for "aberto"
                    if estado_abertura_atual == 'aberto' and prazo_fatal_ts:
                        prazo_data['prazo_fatal'] = prazo_fatal_ts
                    
                    # Configuração de recorrência (se recorrente)
                    if recorrente_switch.value and tipo_prazo == 'recorrente':
                        tipo = refs_recorrencia['tipo_select'].value if refs_recorrencia['tipo_select'] else state['tipo_recorrencia']
                        config_recorrencia = {
                            'tipo': tipo,
                        }
                        
                        if tipo in ['mensal', 'anual']:
                            if refs_recorrencia['dia_especifico_input']:
                                dia = refs_recorrencia['dia_especifico_input'].value
                                if dia and 1 <= dia <= 31:
                                    config_recorrencia['dia_especifico'] = int(dia)
                            
                            if refs_recorrencia['ultimo_dia_checkbox']:
                                config_recorrencia['ultimo_dia_mes'] = refs_recorrencia['ultimo_dia_checkbox'].value
                        
                        elif tipo == 'semanal':
                            semana = refs_recorrencia['semana_select'].value if refs_recorrencia['semana_select'] else 'primeira'
                            dia_semana = refs_recorrencia['dia_semana_select'].value if refs_recorrencia['dia_semana_select'] else 'segunda'
                            
                            config_recorrencia['dia_semana_especifico'] = {
                                'semana': semana,
                                'dia': dia_semana,
                            }
                        
                        prazo_data['config_recorrencia'] = config_recorrencia
                    else:
                        # Garantia: prazo simples/parcelado não mantém config_recorrencia
                        prazo_data.pop('config_recorrencia', None)
                    
                    # Adicionar criado_por se for novo
                    if not is_edicao:
                        usuario_atual = get_current_user()
                        if usuario_atual:
                            prazo_data['criado_por'] = usuario_atual.get('uid') or usuario_atual.get('email', '')
                    
                    try:
                        # Salvar no banco
                        if tipo_prazo == 'parcelado' and not is_edicao:
                            # Parcelamento requer estado "aberto" e prazo_fatal
                            if estado_abertura_atual == 'aguardando_abertura':
                                ui.notify('Não é possível criar parcelamento para prazos "Aguardando abertura". Mude o estado para "Aberto" primeiro.', type='warning')
                                return
                            
                            parcelas = state.get('parcelas_geradas') or []
                            if not parcelas:
                                ui.notify('Configure o parcelamento antes de salvar', type='warning')
                                return

                            parcelamento_id = _gerar_id_parcelamento()
                            total = len(parcelas)
                            ids_criados = []
                            for p in parcelas:
                                numero = int(p.get('numero') or 0)
                                venc_ts = p.get('vencimento_ts')
                                if not venc_ts:
                                    ui.notify('Data de vencimento inválida', type='warning')
                                    return

                                prazo_parcela = dict(prazo_data)
                                prazo_parcela['prazo_fatal'] = float(venc_ts)
                                prazo_parcela['recorrente'] = False
                                prazo_parcela.pop('config_recorrencia', None)
                                prazo_parcela['parcelamento_id'] = parcelamento_id
                                prazo_parcela['parcela_numero'] = numero
                                prazo_parcela['parcela_total'] = total
                                prazo_parcela['titulo_original'] = prazo_data.get('titulo', '')

                                novo_id = criar_prazo(prazo_parcela)
                                ids_criados.append(novo_id)

                            # Callback (uma vez é suficiente para refresh)
                            if on_success and ids_criados:
                                on_success({**prazo_data, '_id': ids_criados[0], 'parcelamento_id': parcelamento_id})

                            ui.notify(f'Prazo parcelado criado com sucesso! ({total} parcelas)', type='positive')
                            dialog.close()
                            return

                        if is_edicao and prazo_id:
                            sucesso = atualizar_prazo(prazo_id, prazo_data)
                            if not sucesso:
                                raise Exception('Erro ao atualizar prazo')
                            # IMPORTANTE: garantir que _id está no prazo_data para o callback
                            prazo_data['_id'] = prazo_id
                        else:
                            prazo_id_novo = criar_prazo(prazo_data)
                            prazo_data['_id'] = prazo_id_novo
                        
                        # Chamar callback se fornecido
                        if on_success:
                            on_success(prazo_data)
                        
                        ui.notify('Prazo salvo com sucesso!' if is_edicao else 'Prazo criado com sucesso!', type='positive')
                        
                        # Fechar dialog
                        dialog.close()
                        
                    except Exception as e:
                        print(f"Erro ao salvar prazo: {e}")
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao salvar prazo: {str(e)}', type='negative')

                ui.button('Cancelar', icon='close', on_click=on_cancel).props('outline color=grey-7')
                ui.button('Salvar', icon='save', on_click=on_save).props('color=primary')
    
    def open_dialog():
        """Abre o dialog."""
        dialog.open()

    return dialog, open_dialog

