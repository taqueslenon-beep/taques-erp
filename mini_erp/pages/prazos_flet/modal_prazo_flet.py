"""
modal_prazo_flet.py - Modal para criar/editar prazo em Flet.
"""

import flet as ft
import re
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from .database import (
    criar_prazo,
    atualizar_prazo,
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


def criar_modal_prazo(
    page: ft.Page,
    on_success: Optional[Callable] = None,
    prazo_inicial: Optional[Dict] = None,
    usuarios_opcoes: Optional[Dict[str, str]] = None,
    clientes_opcoes: Optional[Dict[str, str]] = None,
    casos_opcoes: Optional[Dict[str, str]] = None
) -> ft.AlertDialog:
    """
    Cria modal para criar ou editar prazo em Flet.

    Args:
        page: Página Flet
        on_success: Callback executado após salvar
        prazo_inicial: Dicionário com dados do prazo para edição (None para novo)
        usuarios_opcoes: Opções de usuários (se None, busca do banco)
        clientes_opcoes: Opções de clientes (se None, busca do banco)
        casos_opcoes: Opções de casos (se None, busca do banco)

    Returns:
        AlertDialog configurado
    """
    # Determinar se é edição ou criação
    is_edicao = prazo_inicial is not None
    prazo_id = prazo_inicial.get('_id') if is_edicao else None

    # Estado do formulário - preencher com dados iniciais se for edição
    config_recorrencia_inicial = prazo_inicial.get('config_recorrencia', {}) if is_edicao else {}
    dia_semana_inicial = config_recorrencia_inicial.get('dia_semana_especifico', {})

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

    # Campos do formulário
    titulo_field = ft.TextField(
        label="Título *",
        hint_text="Digite o título do prazo",
        value=prazo_inicial.get('titulo', '') if is_edicao else '',
        expand=True,
    )

    # Responsáveis (múltiplo) - usando lista de seleção
    responsaveis_selecionados = prazo_inicial.get('responsaveis', []) if is_edicao else []
    responsaveis_chips_ref = ft.Ref[ft.Wrap]()
    
    def atualizar_responsaveis_chips():
        """Atualiza chips de responsáveis."""
        if not responsaveis_chips_ref.current:
            return
        responsaveis_chips_ref.current.controls.clear()
        for resp_id in responsaveis_selecionados:
            if resp_id in usuarios_opcoes:
                chip = ft.Chip(
                    label=ft.Text(usuarios_opcoes[resp_id]),
                    on_delete=lambda e, rid=resp_id: remover_responsavel(rid),
                )
                responsaveis_chips_ref.current.controls.append(chip)
        page.update()
    
    def remover_responsavel(resp_id: str):
        """Remove responsável da lista."""
        if resp_id in responsaveis_selecionados:
            responsaveis_selecionados.remove(resp_id)
            atualizar_responsaveis_chips()
    
    def adicionar_responsavel(e):
        """Adiciona responsável da lista."""
        if responsaveis_dropdown.value and responsaveis_dropdown.value not in responsaveis_selecionados:
            responsaveis_selecionados.append(responsaveis_dropdown.value)
            responsaveis_dropdown.value = None
            atualizar_responsaveis_chips()
    
    responsaveis_dropdown = ft.Dropdown(
        label="Adicionar Responsável",
        hint_text="Selecione um responsável",
        options=[ft.dropdown.Option(key=k, text=v) for k, v in usuarios_opcoes.items()],
        expand=True,
    )
    responsaveis_dropdown.on_change = adicionar_responsavel
    
    # Clientes (múltiplo)
    clientes_selecionados = prazo_inicial.get('clientes', []) if is_edicao else []
    clientes_chips_ref = ft.Ref[ft.Wrap]()
    
    def atualizar_clientes_chips():
        """Atualiza chips de clientes."""
        if not clientes_chips_ref.current:
            return
        clientes_chips_ref.current.controls.clear()
        for cliente_id in clientes_selecionados:
            if cliente_id in clientes_opcoes:
                chip = ft.Chip(
                    label=ft.Text(clientes_opcoes[cliente_id]),
                    on_delete=lambda e, cid=cliente_id: remover_cliente(cid),
                )
                clientes_chips_ref.current.controls.append(chip)
        page.update()
    
    def remover_cliente(cliente_id: str):
        """Remove cliente da lista."""
        if cliente_id in clientes_selecionados:
            clientes_selecionados.remove(cliente_id)
            atualizar_clientes_chips()
    
    def adicionar_cliente(e):
        """Adiciona cliente da lista."""
        if clientes_dropdown.value and clientes_dropdown.value not in clientes_selecionados:
            clientes_selecionados.append(clientes_dropdown.value)
            clientes_dropdown.value = None
            atualizar_clientes_chips()
    
    clientes_dropdown = ft.Dropdown(
        label="Adicionar Cliente",
        hint_text="Selecione um cliente",
        options=[ft.dropdown.Option(key=k, text=v) for k, v in clientes_opcoes.items()],
        expand=True,
    )
    clientes_dropdown.on_change = adicionar_cliente
    
    # Casos (múltiplo)
    casos_selecionados = prazo_inicial.get('casos', []) if is_edicao else []
    casos_chips_ref = ft.Ref[ft.Wrap]()
    
    def atualizar_casos_chips():
        """Atualiza chips de casos."""
        if not casos_chips_ref.current:
            return
        casos_chips_ref.current.controls.clear()
        for caso_id in casos_selecionados:
            if caso_id in casos_opcoes:
                chip = ft.Chip(
                    label=ft.Text(casos_opcoes[caso_id]),
                    on_delete=lambda e, cid=caso_id: remover_caso(cid),
                )
                casos_chips_ref.current.controls.append(chip)
        page.update()
    
    def remover_caso(caso_id: str):
        """Remove caso da lista."""
        if caso_id in casos_selecionados:
            casos_selecionados.remove(caso_id)
            atualizar_casos_chips()
    
    def adicionar_caso(e):
        """Adiciona caso da lista."""
        if casos_dropdown.value and casos_dropdown.value not in casos_selecionados:
            casos_selecionados.append(casos_dropdown.value)
            casos_dropdown.value = None
            atualizar_casos_chips()
    
    casos_dropdown = ft.Dropdown(
        label="Adicionar Caso",
        hint_text="Selecione um caso",
        options=[ft.dropdown.Option(key=k, text=v) for k, v in casos_opcoes.items()],
        expand=True,
    )
    casos_dropdown.on_change = adicionar_caso
    
    # Inicializar chips se for edição
    if is_edicao:
        atualizar_responsaveis_chips()
        atualizar_clientes_chips()
        atualizar_casos_chips()

    # Prazo Fatal
    prazo_fatal_field = ft.TextField(
        label="Prazo Fatal *",
        hint_text="DD/MM/AAAA",
        value=converter_timestamp_para_data_br(
            prazo_inicial.get('prazo_fatal')
        ) if is_edicao else '',
        expand=True,
    )

    # Status
    status_dropdown = ft.Dropdown(
        label="Status",
        options=[ft.dropdown.Option(key=op, text=STATUS_LABELS.get(op, op)) for op in STATUS_OPCOES],
        value=prazo_inicial.get('status', 'pendente') if is_edicao else 'pendente',
        expand=True,
    )

    # Recorrente (switch)
    recorrente_switch = ft.Switch(
        label="Recorrente",
        value=prazo_inicial.get('recorrente', False) if is_edicao else False,
    )

    # Container para configuração de recorrência
    recorrencia_container = ft.Ref[ft.Column]()

    # Tipo de recorrência
    tipo_recorrencia_dropdown = ft.Dropdown(
        label="Tipo de Recorrência",
        options=[ft.dropdown.Option(key=op, text=TIPOS_RECORRENCIA_LABELS.get(op, op)) for op in TIPOS_RECORRENCIA],
        value=config_recorrencia_inicial.get('tipo', 'mensal') if is_edicao else 'mensal',
        expand=True,
    )

    # Dia específico
    dia_especifico_field = ft.TextField(
        label="Dia específico (1-31)",
        value=str(config_recorrencia_inicial.get('dia_especifico', '')) if config_recorrencia_inicial.get('dia_especifico') else '',
        expand=True,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    # Último dia do mês
    ultimo_dia_checkbox = ft.Checkbox(
        label="Último dia do mês",
        value=config_recorrencia_inicial.get('ultimo_dia_mes', False) if is_edicao else False,
    )

    # Semana específica
    semana_dropdown = ft.Dropdown(
        label="Qual semana",
        options=[ft.dropdown.Option(key=op, text=OPCOES_SEMANA_LABELS.get(op, op)) for op in OPCOES_SEMANA],
        value=dia_semana_inicial.get('semana', 'primeira') if is_edicao else 'primeira',
        expand=True,
    )

    # Dia da semana
    dia_semana_dropdown = ft.Dropdown(
        label="Qual dia da semana",
        options=[ft.dropdown.Option(key=op, text=OPCOES_DIA_SEMANA_LABELS.get(op, op)) for op in OPCOES_DIA_SEMANA],
        value=dia_semana_inicial.get('dia', 'segunda') if is_edicao else 'segunda',
        expand=True,
    )

    # Observações
    observacoes_field = ft.TextField(
        label="Observações",
        hint_text="Digite observações adicionais",
        value=prazo_inicial.get('observacoes', '') if is_edicao else '',
        multiline=True,
        min_lines=3,
        max_lines=5,
        expand=True,
    )

    # Função para renderizar seção de recorrência
    def render_recorrencia():
        """Renderiza seção de recorrência baseado no switch."""
        if not recorrencia_container.current:
            return
        
        recorrencia_container.current.controls.clear()
        
        if recorrente_switch.value:
            tipo = tipo_recorrencia_dropdown.value or 'mensal'
            
            recorrencia_container.current.controls.append(
                ft.Text("Configuração de Recorrência", size=14, weight=ft.FontWeight.BOLD)
            )
            recorrencia_container.current.controls.append(tipo_recorrencia_dropdown)
            
            if tipo in ['mensal', 'anual']:
                recorrencia_container.current.controls.append(
                    ft.Row([
                        dia_especifico_field,
                        ultimo_dia_checkbox,
                    ], expand=True)
                )
            elif tipo == 'semanal':
                recorrencia_container.current.controls.append(semana_dropdown)
                recorrencia_container.current.controls.append(dia_semana_dropdown)
        
        page.update()

    # Atualizar quando switch mudar
    def on_recorrente_changed(e):
        render_recorrencia()

    recorrente_switch.on_change = on_recorrente_changed

    # Atualizar quando tipo mudar
    def on_tipo_changed(e):
        render_recorrencia()

    tipo_recorrencia_dropdown.on_change = on_tipo_changed

    # Criar container de recorrência
    recorrencia_col = ft.Column(ref=recorrencia_container)
    render_recorrencia()

    # Função para salvar
    def on_save(e):
        """Salva o prazo."""
        # Validar título
        if not titulo_field.value or not titulo_field.value.strip():
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Título é obrigatório!"),
                bgcolor=ft.colors.ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return

        # Validar responsáveis
        if not responsaveis_selecionados:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Selecione pelo menos um responsável!"),
                bgcolor=ft.colors.ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return

        # Validar prazo fatal
        if not prazo_fatal_field.value or not validar_data_br(prazo_fatal_field.value):
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Prazo fatal inválido! Use o formato DD/MM/AAAA"),
                bgcolor=ft.colors.ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return

        # Converter data para timestamp
        prazo_fatal_ts = converter_data_br_para_timestamp(prazo_fatal_field.value)
        if not prazo_fatal_ts:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Erro ao converter data do prazo fatal"),
                bgcolor=ft.colors.RED,
            )
            page.snack_bar.open = True
            page.update()
            return

        # Preparar dados do prazo
        prazo_data = {
            'titulo': titulo_field.value.strip(),
            'responsaveis': responsaveis_selecionados.copy(),
            'clientes': clientes_selecionados.copy(),
            'casos': casos_selecionados.copy(),
            'prazo_fatal': prazo_fatal_ts,
            'status': status_dropdown.value or 'pendente',
            'recorrente': recorrente_switch.value or False,
            'observacoes': observacoes_field.value or '',
        }

        # Configuração de recorrência (se recorrente)
        if recorrente_switch.value:
            tipo = tipo_recorrencia_dropdown.value or 'mensal'
            config_recorrencia = {'tipo': tipo}

            if tipo in ['mensal', 'anual']:
                if dia_especifico_field.value:
                    try:
                        dia = int(dia_especifico_field.value)
                        if 1 <= dia <= 31:
                            config_recorrencia['dia_especifico'] = dia
                    except ValueError:
                        pass

                config_recorrencia['ultimo_dia_mes'] = ultimo_dia_checkbox.value

            elif tipo == 'semanal':
                config_recorrencia['dia_semana_especifico'] = {
                    'semana': semana_dropdown.value or 'primeira',
                    'dia': dia_semana_dropdown.value or 'segunda',
                }

            prazo_data['config_recorrencia'] = config_recorrencia

        # Adicionar criado_por se for novo
        if not is_edicao:
            usuario_atual = get_current_user()
            if usuario_atual:
                prazo_data['criado_por'] = usuario_atual.get('uid') or usuario_atual.get('email', '')

        try:
            # Salvar no banco
            if is_edicao and prazo_id:
                sucesso = atualizar_prazo(prazo_id, prazo_data)
                if not sucesso:
                    raise Exception('Erro ao atualizar prazo')
            else:
                prazo_id_novo = criar_prazo(prazo_data)
                prazo_data['_id'] = prazo_id_novo

            # Chamar callback se fornecido
            if on_success:
                on_success(prazo_data)

            page.snack_bar = ft.SnackBar(
                content=ft.Text('Prazo salvo com sucesso!' if is_edicao else 'Prazo criado com sucesso!'),
                bgcolor=ft.colors.GREEN,
            )
            page.snack_bar.open = True
            page.update()

            # Fechar dialog
            dialog.open = False
            page.update()

        except Exception as ex:
            print(f"Erro ao salvar prazo: {ex}")
            import traceback
            traceback.print_exc()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f'Erro ao salvar prazo: {str(ex)}'),
                bgcolor=ft.colors.RED,
            )
            page.snack_bar.open = True
            page.update()

    # Criar dialog
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text('Editar Prazo' if is_edicao else 'Novo Prazo'),
        content=ft.Container(
            content=ft.Column(
                [
                    titulo_field,
                    ft.Text("Responsável(is) *", size=12, weight=ft.FontWeight.W_500),
                    responsaveis_dropdown,
                    ft.Wrap(ref=responsaveis_chips_ref, spacing=8),
                    ft.Text("Clientes", size=12, weight=ft.FontWeight.W_500),
                    clientes_dropdown,
                    ft.Wrap(ref=clientes_chips_ref, spacing=8),
                    ft.Text("Casos", size=12, weight=ft.FontWeight.W_500),
                    casos_dropdown,
                    ft.Wrap(ref=casos_chips_ref, spacing=8),
                    prazo_fatal_field,
                    status_dropdown,
                    recorrente_switch,
                    recorrencia_col,
                    observacoes_field,
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                height=600,
            ),
            width=700,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            ft.ElevatedButton("Salvar", on_click=on_save, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return dialog

