"""
ui_components.py - Componentes de UI reutilizáveis para o módulo Prazos (Flet).

Funções de formatação e componentes visuais estilo Material Design.
"""

import flet as ft
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional


# =============================================================================
# FUNÇÕES DE FORMATAÇÃO
# =============================================================================

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


def formatar_titulo_prazo(prazo: Dict[str, Any]) -> str:
    """
    Formata o título do prazo, adicionando emoji 🔁 se for recorrente.
    
    Args:
        prazo: Dicionário com dados do prazo
    
    Returns:
        Título formatado com emoji se recorrente
    """
    titulo = prazo.get('titulo', 'Sem título')
    is_recorrente = prazo.get('recorrente', False)
    
    if is_recorrente:
        return f"🔁 {titulo}"
    return titulo


# =============================================================================
# FUNÇÕES DE SEMANA
# =============================================================================

def obter_inicio_fim_semana(data_ref: date) -> tuple[date, date]:
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


def obter_semana_passada() -> tuple[date, date]:
    """Retorna início e fim da semana passada."""
    hoje = date.today()
    inicio_esta_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana_passada = inicio_esta_semana - timedelta(days=7)
    fim_semana_passada = inicio_semana_passada + timedelta(days=6)
    return inicio_semana_passada, fim_semana_passada


def obter_esta_semana() -> tuple[date, date]:
    """Retorna início e fim desta semana."""
    hoje = date.today()
    return obter_inicio_fim_semana(hoje)


def obter_proxima_semana() -> tuple[date, date]:
    """Retorna início e fim da próxima semana."""
    hoje = date.today()
    inicio_esta_semana = hoje - timedelta(days=hoje.weekday())
    inicio_proxima_semana = inicio_esta_semana + timedelta(days=7)
    fim_proxima_semana = inicio_proxima_semana + timedelta(days=6)
    return inicio_proxima_semana, fim_proxima_semana


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
            print(f"[PRAZOS-FLET] Erro ao filtrar prazo: {e}")
            continue
    
    return filtrados


# =============================================================================
# COMPONENTES VISUAIS FLET
# =============================================================================

def criar_badge_status(status: str) -> ft.Container:
    """
    Cria um badge colorido para o status do prazo.
    
    Args:
        status: Status do prazo ('pendente', 'concluido', 'atrasado')
    
    Returns:
        Container com badge estilizado
    """
    status_lower = status.lower()
    
    if status_lower == 'concluido' or status_lower == 'concluído':
        cor_fundo = ft.colors.GREEN_400
        cor_texto = ft.colors.WHITE
        texto = 'Concluído'
    elif status_lower == 'atrasado':
        cor_fundo = ft.colors.RED_400
        cor_texto = ft.colors.WHITE
        texto = 'Atrasado'
    else:  # pendente
        cor_fundo = ft.colors.YELLOW_400
        cor_texto = ft.colors.BLACK87
        texto = 'Pendente'
    
    return ft.Container(
        content=ft.Text(
            texto,
            size=12,
            weight=ft.FontWeight.W_500,
            color=cor_texto,
        ),
        bgcolor=cor_fundo,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=12,
    )


def criar_card_prazo(prazo: Dict[str, Any], usuarios_opcoes: Dict[str, str], 
                     clientes_opcoes: Dict[str, str], on_edit, on_delete, on_toggle) -> ft.Card:
    """
    Cria um card visual para um prazo (alternativa à tabela).
    
    Args:
        prazo: Dicionário com dados do prazo
        usuarios_opcoes: Opções de usuários
        clientes_opcoes: Opções de clientes
        on_edit: Callback para editar
        on_delete: Callback para excluir
        on_toggle: Callback para alternar status
    
    Returns:
        Card Flet estilizado
    """
    prazo_id = prazo.get('_id')
    titulo = formatar_titulo_prazo(prazo)
    status = prazo.get('status', 'pendente')
    prazo_fatal_ts = prazo.get('prazo_fatal')
    prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
    esta_atrasado = verificar_prazo_atrasado(prazo_fatal_ts, status)
    esta_concluido = status.lower() == 'concluido'
    
    # Cor de fundo baseada no status
    if esta_atrasado:
        cor_fundo = ft.colors.RED_50
    elif esta_concluido:
        cor_fundo = ft.colors.GREEN_50
    else:
        cor_fundo = ft.colors.WHITE
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Checkbox(
                                value=esta_concluido,
                                on_change=lambda e: on_toggle(prazo_id, e.control.value),
                            ),
                            ft.Text(
                                titulo,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                            criar_badge_status(status),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.CALENDAR_TODAY, size=16, color=ft.colors.GREY_600),
                            ft.Text(f"Prazo Fatal: {prazo_fatal_texto}", size=12),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.PERSON, size=16, color=ft.colors.GREY_600),
                            ft.Text(
                                formatar_lista_nomes(prazo.get('responsaveis', []), usuarios_opcoes),
                                size=12,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                icon_color=ft.colors.BLUE,
                                tooltip="Editar",
                                on_click=lambda _: on_edit(prazo_id),
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_color=ft.colors.RED,
                                tooltip="Excluir",
                                on_click=lambda _: on_delete(prazo_id),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            bgcolor=cor_fundo,
            border_radius=8,
        ),
        elevation=2,
    )


def criar_mensagem_vazia(icone: str, titulo: str, subtitulo: str) -> ft.Container:
    """
    Cria uma mensagem de estado vazio.
    
    Args:
        icone: Nome do ícone Material
        titulo: Título da mensagem
        subtitulo: Subtítulo da mensagem
    
    Returns:
        Container com mensagem estilizada
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icone, size=64, color=ft.colors.GREY_400),
                ft.Text(titulo, size=18, weight=ft.FontWeight.W_500, color=ft.colors.GREY_600),
                ft.Text(subtitulo, size=14, color=ft.colors.GREY_500),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
        ),
        padding=48,
        alignment=ft.alignment.center,
    )


