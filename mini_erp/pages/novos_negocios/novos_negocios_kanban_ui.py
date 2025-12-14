"""
Componente de interface Kanban para Novos Negócios.
Visualização em colunas fixas para gestão de oportunidades de negócio.
"""
from typing import Callable, Optional, List, Dict
from datetime import datetime
from nicegui import ui
from .novos_negocios_services import (
    get_oportunidades,
    update_status_oportunidade
)
from mini_erp.models.prioridade import PRIORIDADE_PADRAO, get_cor_por_prioridade
from mini_erp.core import get_leads_list
from mini_erp.pages.visao_geral.casos.models import NUCLEO_OPTIONS, obter_cor_nucleo


# Constantes das colunas do Kanban
COLUNAS_NOVOS_NEGOCIOS = [
    {"id": "agir", "nome": "Agir", "cor": "#EF4444", "ordem": 1},
    {"id": "em_andamento", "nome": "Em Andamento", "cor": "#EAB308", "ordem": 2},
    {"id": "aguardando", "nome": "Aguardando", "cor": "#FDE047", "ordem": 3},
    {"id": "monitorando", "nome": "Monitorando", "cor": "#F97316", "ordem": 4},
    {"id": "concluido", "nome": "Concluído", "cor": "#22C55E", "ordem": 5},
]


# Estado global do drag & drop
drag_state = {
    'dragging_id': None,      # ID da oportunidade sendo arrastada
    'source_column': None,    # Coluna de origem
}


def formatar_valor(valor: Optional[float]) -> str:
    """Formata valor monetário."""
    if not valor:
        return ''
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def calcular_valor_total_coluna(oportunidades: List[Dict]) -> float:
    """
    Calcula a soma dos valores estimados das oportunidades.
    
    Args:
        oportunidades: Lista de dicionários com dados das oportunidades
    
    Returns:
        Soma total dos valores estimados
    """
    total = 0.0
    for op in oportunidades:
        valor = op.get('valor_estimado', 0) or 0
        if isinstance(valor, str):
            # Remove formatação se for string
            try:
                valor_limpo = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor = float(valor_limpo)
            except:
                valor = 0
        total += float(valor) if valor else 0
    return total


def formatar_valor_total(valor: float) -> str:
    """
    Formata valor total para exibição no cabeçalho (sem decimais).
    
    Args:
        valor: Valor numérico a formatar
    
    Returns:
        String formatada como "R$ X.XXX"
    """
    if not valor or valor == 0:
        return 'R$ 0'
    # Formata sem decimais, com separador de milhar
    return f'R$ {valor:,.0f}'.replace(',', '.')


def criar_badge_nucleo(nucleo: str):
    """
    Cria um badge visual para exibir o núcleo de uma oportunidade.
    
    Args:
        nucleo: Nome do núcleo (Ambiental, Cobranças, Generalista)
               Se None ou vazio, usa Generalista como padrão
    
    Returns:
        None (cria elemento UI diretamente)
    """
    # Normaliza núcleo (garante Generalista se inválido)
    if not nucleo or (isinstance(nucleo, str) and nucleo.strip() == ''):
        nucleo = 'Generalista'
    
    # Obtém a cor correspondente
    cor = obter_cor_nucleo(nucleo)
    
    # Cria badge compacto (mesmo estilo do módulo Casos)
    with ui.element('span').classes(
        'px-2 py-1 rounded text-xs font-semibold text-white uppercase inline-block'
    ).style(f'background-color: {cor}; font-size: 11px;'):
        ui.label(nucleo)


def criar_badge_prioridade(prioridade: str):
    """
    Cria um badge visual para exibir a prioridade de uma oportunidade.
    
    Args:
        prioridade: Código da prioridade (P1, P2, P3, P4)
                   Se None ou vazio, usa P4 como padrão
    
    Returns:
        None (cria elemento UI diretamente)
    """
    # Normaliza prioridade (garante P4 se inválida)
    if not prioridade or (isinstance(prioridade, str) and prioridade.strip() == ''):
        prioridade = PRIORIDADE_PADRAO
    
    # Obtém a cor correspondente
    try:
        cor = get_cor_por_prioridade(prioridade)
    except (ValueError, TypeError):
        # Fallback para P4 se código inválido
        cor = get_cor_por_prioridade(PRIORIDADE_PADRAO)
        prioridade = PRIORIDADE_PADRAO
    
    # Cria badge compacto
    with ui.element('span').classes(
        'px-2 py-1 rounded-full text-xs font-bold text-white inline-block'
    ).style(f'background-color: {cor}'):
        ui.label(prioridade)


def calcular_dias_desde(data_timestamp: Optional[float]) -> str:
    """Calcula quantos dias se passaram desde a data."""
    if not data_timestamp:
        return ''
    try:
        if isinstance(data_timestamp, (int, float)):
            data = datetime.fromtimestamp(data_timestamp)
        else:
            data = data_timestamp
        
        dias = (datetime.now() - data.replace(hour=0, minute=0, second=0, microsecond=0)).days
        if dias == 0:
            return 'Hoje'
        elif dias == 1:
            return 'há 1 dia'
        else:
            return f'há {dias} dias'
    except:
        return ''


def criar_card_oportunidade(
    oportunidade: dict, 
    coluna_atual: str, 
    on_refresh: Optional[Callable] = None,
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None
):
    """
    Cria componente visual de card para uma oportunidade.
    
    Args:
        oportunidade: Dicionário com dados da oportunidade
        coluna_atual: ID da coluna atual
        on_refresh: Função para atualizar o Kanban após mudanças
        on_edit: Função para abrir dialog de edição
        on_delete: Função para abrir dialog de exclusão
    """
    oportunidade_id = oportunidade.get('_id', '')
    nome = oportunidade.get('nome', 'Sem nome')
    nome_exibicao = oportunidade.get('nome_exibicao', '')
    valor_estimado = oportunidade.get('valor_estimado')
    origem = oportunidade.get('origem', '')
    data_criacao = oportunidade.get('data_criacao')
    responsavel = oportunidade.get('responsavel', '')
    lead_id = oportunidade.get('lead_id', '')
    prioridade = oportunidade.get('prioridade', PRIORIDADE_PADRAO)
    nucleo = oportunidade.get('nucleo', 'Generalista')  # Núcleo (padrão: Generalista)
    entrada_lead = oportunidade.get('entrada_lead', '')  # Formato: "MM/AAAA"
    resultado = oportunidade.get('resultado', '')  # 'ganho' ou 'perdido'
    status = oportunidade.get('status', '')
    
    # Busca nome do lead se houver lead_id
    lead_nome = ''
    if lead_id:
        # Tenta buscar o nome do lead salvo na oportunidade (cache)
        lead_nome_salvo = oportunidade.get('lead_nome', '')
        if lead_nome_salvo:
            lead_nome = lead_nome_salvo
        else:
            # Se não está salvo, busca na coleção de leads
            try:
                leads = get_leads_list()
                lead_encontrado = next((l for l in leads if l.get('_id') == lead_id), None)
                if lead_encontrado:
                    # Usa nome ou nome_exibicao do lead
                    lead_nome = lead_encontrado.get('nome_exibicao') or lead_encontrado.get('nome', '')
            except:
                pass
    
    # Define estilo de borda baseado no resultado
    borda_estilo = ''
    if status == 'concluido':
        if resultado == 'ganho':
            borda_estilo = 'border-left: 4px solid #22C55E;'
        elif resultado == 'perdido':
            borda_estilo = 'border-left: 4px solid #EF4444;'
    
    # Card draggable
    with ui.card().style(f'''
        background-color: white;
        border-radius: 8px;
        padding: 0;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: grab;
        user-select: none;
        transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
        {borda_estilo}
    ''').classes('draggable-card-oportunidade').props('draggable=true') as card:
        
        # Adiciona atributo data para drag & drop
        card.props(f'data-oportunidade-id="{oportunidade_id}"')
        
        # Evento de início do arrasto
        def on_dragstart(e, oid=oportunidade_id, col=coluna_atual):
            drag_state['dragging_id'] = oid
            drag_state['source_column'] = col
        
        card.on('dragstart', on_dragstart)
        
        # Container interno do card
        with ui.column().classes('w-full gap-2 p-3'):
            # LINHA 1: Header com Lead/Título + Menu de ações
            with ui.row().classes('w-full items-start justify-between gap-2'):
                # Container de título (lead + nome da oportunidade)
                with ui.column().classes('flex-1 gap-0'):
                    # Nome do Lead (destaque) OU Nome da Oportunidade se não tiver lead
                    if lead_nome:
                        ui.label(lead_nome).classes('text-sm font-bold text-gray-800').style('word-wrap: break-word;')
                        # Título da oportunidade (subtítulo, menor, cinza)
                        ui.label(nome).classes('text-xs text-gray-600 mt-0.5').style('word-wrap: break-word;')
                    else:
                        # Sem lead - mostrar só o título em destaque
                        ui.label(nome).classes('text-sm font-bold text-gray-800').style('word-wrap: break-word;')
                
                # Menu de ações (3 pontos)
                if on_edit or on_delete:
                    with ui.button(icon='more_vert').props('flat round dense').classes('flex-shrink-0'):
                        with ui.menu():
                            if on_edit:
                                ui.menu_item('Editar', on_click=lambda: on_edit(oportunidade_id))
                            if on_delete:
                                ui.menu_item('Excluir', on_click=lambda: on_delete(oportunidade))
            
            # LINHA 2: Resultado (se concluído)
            if status == 'concluido' and resultado:
                if resultado == 'ganho':
                    ui.label('✅ Negócio Ganho').classes('text-xs font-semibold').style('color: #22C55E;')
                elif resultado == 'perdido':
                    ui.label('❌ Negócio Perdido').classes('text-xs font-semibold').style('color: #EF4444;')
            
            # LINHA 4: Valor estimado (se existir)
            if valor_estimado:
                valor_texto = formatar_valor(valor_estimado)
                ui.label(valor_texto).classes('text-sm font-semibold').style('color: #22C55E;')
            
            # LINHA 5: Badges (Núcleo + Origem + Prioridade) e Responsável (canto inferior direito)
            with ui.row().classes('w-full items-center justify-between gap-2'):
                # Container de badges (Núcleo + Origem + Prioridade) - lado esquerdo
                with ui.row().classes('items-center gap-2'):
                    # Badge de Núcleo
                    criar_badge_nucleo(nucleo)
                    
                    # Badge de origem
                    if origem:
                        ui.label(origem).style('''
                            background-color: #E5E7EB;
                            color: #4B5563;
                            padding: 2px 8px;
                            border-radius: 4px;
                            font-size: 10px;
                            font-weight: 500;
                        ''')
                    
                    # Badge de prioridade
                    criar_badge_prioridade(prioridade)
                
                # Responsável (canto inferior direito)
                with ui.column().classes('items-end'):
                    # Processa lista de responsáveis
                    responsaveis_list = []
                    if responsavel:
                        if isinstance(responsavel, list):
                            responsaveis_list = responsavel
                        elif isinstance(responsavel, str):
                            responsaveis_list = [responsavel]
                    
                    # Cria label do responsável apenas se houver responsáveis
                    if responsaveis_list:
                        if len(responsaveis_list) == 1:
                            texto_resp = responsaveis_list[0]
                        else:
                            texto_resp = f"{responsaveis_list[0]} (+{len(responsaveis_list) - 1})"
                        ui.label(texto_resp).classes('text-xs text-gray-500')
    
    return card


def obter_ordem_prioridade(oportunidade: dict) -> int:
    """
    Retorna a ordem numérica de uma prioridade para ordenação.
    
    Args:
        oportunidade: Dicionário com dados da oportunidade
    
    Returns:
        Ordem numérica (1 para P1, 4 para P4)
    """
    prioridade = oportunidade.get('prioridade', PRIORIDADE_PADRAO)
    ordem_map = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
    return ordem_map.get(prioridade, 4)


def render_kanban_novos_negocios(
    on_refresh: Optional[Callable] = None,
    on_edit_oportunidade: Optional[Callable] = None,
    on_delete_oportunidade: Optional[Callable] = None,
    on_resultado_oportunidade: Optional[Callable] = None
):
    """
    Renderiza o componente Kanban com as colunas fixas e cards.
    
    Args:
        on_refresh: Função opcional para atualizar o Kanban
    """
    # Log para debug
    print(f"[KANBAN] Iniciando renderização...")
    
    # OTIMIZAÇÃO: Busca TODAS as oportunidades uma única vez (ao invés de 5 queries)
    todas_oportunidades = get_oportunidades()
    print(f"[KANBAN] Total de oportunidades no Firebase: {len(todas_oportunidades)}")
    
    # Agrupa oportunidades por status e ordena por prioridade (filtro local)
    oportunidades_por_status = {}
    for coluna in COLUNAS_NOVOS_NEGOCIOS:
        status = coluna['id']
        # Filtra localmente ao invés de fazer query separada
        oportunidades = [op for op in todas_oportunidades if op.get('status') == status]
        # Ordena por prioridade (P1 primeiro, P4 por último)
        oportunidades.sort(key=obter_ordem_prioridade)
        oportunidades_por_status[status] = oportunidades
        print(f"[KANBAN] Coluna '{status}': {len(oportunidades)} cards")
    
    # Função para processar drop
    def processar_drop(nova_coluna: str):
        """Processa quando um card é solto em uma nova coluna."""
        oportunidade_id = drag_state.get('dragging_id')
        coluna_origem = drag_state.get('source_column')
        
        # Limpa estado do drag
        drag_state['dragging_id'] = None
        drag_state['source_column'] = None
        
        # Verifica se tem dados válidos
        if not oportunidade_id:
            return
        
        # Se soltou na mesma coluna, não faz nada
        if coluna_origem == nova_coluna:
            return
        
        # Mapeamento de IDs para nomes de colunas
        colunas_map = {col['id']: col['nome'] for col in COLUNAS_NOVOS_NEGOCIOS}
        nome_coluna = colunas_map.get(nova_coluna, nova_coluna)
        
        # Se moveu para "Concluído", abre dialog de resultado
        if nova_coluna == 'concluido' and on_resultado_oportunidade:
            # Primeiro atualiza o status
            sucesso = update_status_oportunidade(oportunidade_id, nova_coluna)
            if sucesso:
                # Depois abre dialog para definir resultado
                on_resultado_oportunidade(oportunidade_id)
                # Não chama refresh aqui, o dialog vai chamar após salvar resultado
            else:
                ui.notify('Erro ao mover oportunidade', type='negative')
        else:
            # Atualiza status no Firebase normalmente
            sucesso = update_status_oportunidade(oportunidade_id, nova_coluna)
            if sucesso:
                ui.notify(f'Oportunidade movida para "{nome_coluna}"', type='positive')
                # Atualiza visual se função de refresh fornecida
                if on_refresh:
                    on_refresh()
            else:
                ui.notify('Erro ao mover oportunidade', type='negative')
    
    # CSS para drag & drop
    ui.add_head_html('''
        <style>
            .draggable-card-oportunidade {
                user-select: none;
                transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
            }
            .draggable-card-oportunidade:hover {
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            .draggable-card-oportunidade:active {
                opacity: 0.7;
                cursor: grabbing;
            }
            
            .drop-zone-oportunidade {
                min-height: 300px;
                transition: background-color 0.2s ease;
                border: 2px dashed transparent;
            }
            .drop-zone-oportunidade.drag-over {
                background-color: rgba(59, 130, 246, 0.15);
                border-color: rgba(59, 130, 246, 0.5);
            }
        </style>
    ''')
    
    # JavaScript para feedback visual durante arrasto
    ui.run_javascript('''
        (function() {
            function setupDropZones() {
                document.querySelectorAll('.drop-zone-oportunidade').forEach(zone => {
                    zone.addEventListener('dragenter', e => {
                        e.preventDefault();
                        zone.classList.add('drag-over');
                    });
                    zone.addEventListener('dragleave', e => {
                        e.preventDefault();
                        if (!zone.contains(e.relatedTarget)) {
                            zone.classList.remove('drag-over');
                        }
                    });
                    zone.addEventListener('dragover', e => {
                        e.preventDefault();
                    });
                    zone.addEventListener('drop', e => {
                        e.preventDefault();
                        zone.classList.remove('drag-over');
                    });
                });
            }
            
            function setupDraggableCards() {
                document.querySelectorAll('.draggable-card-oportunidade').forEach(card => {
                    card.addEventListener('dragstart', e => {
                        const oportunidadeId = card.getAttribute('data-oportunidade-id');
                        window._dragging_oportunidade_id = oportunidadeId;
                        card.style.opacity = '0.5';
                    });
                    card.addEventListener('dragend', e => {
                        window._dragging_oportunidade_id = null;
                        card.style.opacity = '1';
                        document.querySelectorAll('.drop-zone-oportunidade').forEach(z => {
                            z.classList.remove('drag-over');
                        });
                    });
                });
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    setupDropZones();
                    setupDraggableCards();
                });
            } else {
                setupDropZones();
                setupDraggableCards();
            }
            
            // Reconfigura após atualizações do DOM
            function setupKanbanObserver() {
                try {
                    const observer = new MutationObserver(function(mutations) {
                        setupDropZones();
                        setupDraggableCards();
                    });
                    
                    // Tripla verificação: existe, é Node, está no DOM
                    if (document.body && 
                        document.body instanceof Node && 
                        document.contains(document.body)) {
                        try {
                            observer.observe(document.body, { childList: true, subtree: true });
                        } catch (e) {
                            console.log('Observer error (kanban):', e.message);
                        }
                    }
                } catch (e) {
                    console.log('Observer setup skipped (kanban):', e.message);
                }
            }
            
            // Executar apenas quando DOM estiver pronto
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupKanbanObserver);
            } else {
                setupKanbanObserver();
            }
        })();
    ''')
    
    # Container principal do Kanban com scroll horizontal
    with ui.element('div').classes('w-full overflow-x-auto').style('padding-bottom: 16px;'):
        with ui.row().classes('w-full gap-4 items-start').style('min-width: fit-content;'):
            # Renderiza cada coluna
            for coluna in COLUNAS_NOVOS_NEGOCIOS:
                coluna_id = coluna['id']
                coluna_nome = coluna['nome']
                cor_fundo = coluna['cor']
                oportunidades_coluna = oportunidades_por_status.get(coluna_id, [])
                contador = len(oportunidades_coluna)
                
                # Container da coluna (largura fixa)
                with ui.column().classes('flex flex-col').style(f'min-width: 280px; max-width: 280px;'):
                    # Card completo da coluna (header + drop zone)
                    with ui.card().classes('w-full flex flex-col').style('padding: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'):
                        # Cabeçalho da coluna
                        with ui.element('div').classes('w-full p-3').style(f'background-color: {cor_fundo};'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(coluna_nome).classes('text-sm font-semibold').style('color: white;')
                                # Contador de cards e valor total
                                with ui.row().classes('items-center gap-2'):
                                    # Contador de cards
                                    ui.label(f'({contador})').classes('text-xs font-medium').style('color: rgba(255, 255, 255, 0.9);')
                                    # Valor total da coluna (discreto)
                                    valor_total_coluna = calcular_valor_total_coluna(oportunidades_coluna)
                                    if valor_total_coluna > 0:
                                        valor_formatado = formatar_valor_total(valor_total_coluna)
                                        ui.label(valor_formatado).classes('text-xs font-medium').style('color: rgba(255, 255, 255, 0.7);')
                        
                        # Área de drop zone para cards
                        with ui.element('div').classes('w-full flex-1 p-3 drop-zone-oportunidade').style(f'''
                            background-color: #F9FAFB;
                            border: 2px dashed #E5E7EB;
                            border-top: none;
                            min-height: 400px;
                        ''') as drop_zone:
                            # Adiciona identificador para drop zone
                            drop_zone.props(f'data-coluna-id="{coluna_id}" data-coluna-nome="{coluna_nome}"')
                            
                            # Handler de drop
                            def criar_handler_drop(destino):
                                """Cria handler de drop para a coluna."""
                                def on_drop(e):
                                    processar_drop(destino)
                                return on_drop
                            
                            # Registra eventos de drop
                            drop_zone.on('dragover.prevent', lambda e: None)
                            drop_zone.on('drop', criar_handler_drop(coluna_id))
                            
                            # Exibe cards ou mensagem de vazio
                            if oportunidades_coluna:
                                for oportunidade in oportunidades_coluna:
                                    criar_card_oportunidade(
                                        oportunidade, 
                                        coluna_id, 
                                        on_refresh,
                                        on_edit_oportunidade,
                                        on_delete_oportunidade
                                    )
                            else:
                                # Mensagem de vazio
                                with ui.column().classes('w-full items-center justify-center h-full py-8'):
                                    ui.icon('inbox').style('font-size: 32px;').classes('text-gray-300 mb-2')
                                    ui.label('Nenhuma oportunidade').classes('text-sm text-gray-400 text-center')
