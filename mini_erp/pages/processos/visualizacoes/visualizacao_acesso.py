"""
visualizacao_acesso.py - Página de visualização "Acesso aos Processos".

Esta página replica a visualização de processos com sincronização em tempo real.
Qualquer modificação feita aqui ou na página principal é refletida em ambas.
"""

from nicegui import ui
from datetime import datetime
from ....core import layout, get_processes_list, get_clients_list, get_opposing_parties_list, get_cases_list, invalidate_cache, save_process
from ....auth import is_authenticated
from ..modais.modal_processo import render_process_dialog
from ..ui_components import TABELA_PROCESSOS_CSS
from ..utils import normalize_name_for_display
from ..database import obter_todos_acompanhamentos, atualizar_acompanhamento
from ..modais.modal_acompanhamento_terceiros import render_third_party_monitoring_dialog


def _get_priority_name(name: str, people_list: list) -> str:
    """
    Busca pessoa na lista e retorna nome de exibição usando regra centralizada.
    
    CORREÇÃO: Garante que SEMPRE retorna nome_exibicao (não nome_completo).
    Faz busca bidirecional (nome completo → display_name e display_name → nome completo).
    Sempre em MAIÚSCULAS.
    
    IMPORTANTE: Se a pessoa não for encontrada, tenta buscar por nome_completo também
    para garantir que encontre mesmo quando o processo tem nome_completo salvo.
    """
    from ....core import get_display_name
    
    if not name:
        return ''
    
    normalized_input = normalize_name_for_display(name)
    
    # Busca pessoa na lista pelo nome, ID ou nome de exibição
    person = None
    for p in people_list:
        full_name = p.get('full_name') or p.get('name', '')
        # CORREÇÃO: Também verifica nome_completo se existir
        nome_completo = p.get('nome_completo', '')
        display_name = get_display_name(p)
        normalized_full = normalize_name_for_display(full_name)
        normalized_completo = normalize_name_for_display(nome_completo) if nome_completo else ''
        normalized_display = normalize_name_for_display(display_name)
        
        # Busca por nome completo, ID, nome_completo ou nome de exibição (com fallback normalizado)
        if (
            full_name == name or 
            nome_completo == name or
            p.get('_id') == name or 
            display_name == name or
            display_name.upper() == name.upper() or
            (normalized_input and (
                normalized_full == normalized_input or
                normalized_completo == normalized_input or
                normalized_display == normalized_input
            ))
        ):
            person = p
            break
    
    if person:
        # CORREÇÃO: SEMPRE usa get_display_name que prioriza nome_exibicao
        # Nunca retorna nome_completo diretamente
        display_name = get_display_name(person)
        if display_name:
            return display_name.upper()
        # Se get_display_name retornou vazio, tenta nome_exibicao diretamente
        nome_exibicao = person.get('nome_exibicao', '').strip()
        if nome_exibicao:
            return nome_exibicao.upper()
        # Último fallback: usa full_name apenas se não houver nome_exibicao
        fallback_name = person.get('full_name') or person.get('name', '')
        return fallback_name.upper() if fallback_name else name.upper()
    
    # Se não encontrou, retorna o nome original em maiúsculas
    # (mas idealmente isso não deveria acontecer se os dados estiverem corretos)
    return name.upper() if name else ''


def _format_names_list(names_raw, people_list: list) -> list:
    """
    Formata lista de nomes aplicando prioridade e MAIÚSCULAS.
    Retorna lista para exibição vertical.
    """
    if not names_raw:
        return []
    
    if isinstance(names_raw, list):
        formatted = [_get_priority_name(str(n), people_list) for n in names_raw if n]
        return formatted
    else:
        name = _get_priority_name(str(names_raw), people_list)
        return [name] if name else []


def format_third_party_row(acompanhamento: dict) -> dict:
    """
    Formata um acompanhamento de terceiros no mesmo formato de um processo normal.
    
    Args:
        acompanhamento: Dicionário com dados do acompanhamento
    
    Returns:
        Dicionário formatado no mesmo padrão de processos
    """
    # Extrai casos vinculados - retorna lista
    cases_raw = acompanhamento.get('cases') or acompanhamento.get('cases_list') or []
    if isinstance(cases_raw, list):
        cases_list = [str(c) for c in cases_raw if c]
    else:
        cases_list = [str(cases_raw)] if cases_raw else []
    
    # Processamento de data de abertura (mesmo formato que processos)
    data_abertura_raw = acompanhamento.get('data_abertura') or ''
    data_abertura_display = ''
    data_abertura_sort = ''
    
    if data_abertura_raw:
        try:
            data_abertura_raw = str(data_abertura_raw).strip()
            
            # Formato: AAAA (apenas ano) - 4 dígitos
            if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                data_abertura_display = data_abertura_raw
                data_abertura_sort = f"{data_abertura_raw}/00/00"
            
            # Formato: MM/AAAA (mês e ano) - 7 caracteres
            elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                partes = data_abertura_raw.split('/')
                if len(partes) == 2:
                    data_abertura_display = data_abertura_raw
                    data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
            
            # Formato: DD/MM/AAAA (completa) - 10 caracteres
            elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                partes = data_abertura_raw.split('/')
                if len(partes) == 3:
                    data_abertura_display = data_abertura_raw
                    data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
            
            # Formato legado: YYYY-MM-DD
            elif '-' in data_abertura_raw:
                partes = data_abertura_raw.split('-')
                if len(partes) == 3:
                    data_abertura_display = f"{partes[2]}/{partes[1]}/{partes[0]}"
                    data_abertura_sort = f"{partes[0]}/{partes[1]}/{partes[2]}"
                else:
                    data_abertura_display = data_abertura_raw
            
            else:
                # Fallback - mantém valor original
                data_abertura_display = data_abertura_raw
                
        except Exception:
            data_abertura_display = data_abertura_raw
    
    return {
        '_id': acompanhamento.get('_id', ''),
        'tipo_processo': 'acompanhamento',  # Marcador de tipo
        'data_abertura': data_abertura_display,
        'data_abertura_sort': data_abertura_sort,
        'title': acompanhamento.get('titulo') or acompanhamento.get('title') or '(sem título)',
        'number': acompanhamento.get('numero') or acompanhamento.get('number') or '',
        'clients_list': ['NA'],  # Acompanhamentos não têm clientes na estrutura padrão
        'opposing_list': ['NA'],  # Acompanhamentos não têm partes contrárias na estrutura padrão
        'cases_list': cases_list,
        'system': acompanhamento.get('system') or acompanhamento.get('sistema') or '',
        'status': acompanhamento.get('status', ''),
        'area': acompanhamento.get('area') or acompanhamento.get('area_direito') or '',
        'link': acompanhamento.get('link') or acompanhamento.get('link_do_processo') or '',
        # Campos de acesso (mapeamento dos campos do acompanhamento)
        'access_requested': acompanhamento.get('access_lawyer_requested', False),
        'access_granted': acompanhamento.get('access_lawyer_granted', False) or acompanhamento.get('access_lawyer', False),
        'access_technicians': acompanhamento.get('access_technicians_granted', False) or acompanhamento.get('access_technicians', False),
    }


def fetch_processes():
    """
    Busca processos do Firestore e acompanhamentos de terceiros, formatando para exibição.
    
    Returns:
        Lista de dicionários prontos para a tabela (processos normais + acompanhamentos).
    """
    try:
        # 1. Carregar processos normais
        raw_processes = get_processes_list()
        
        # Carrega listas de pessoas para buscar siglas/display_names
        clients_list = get_clients_list()
        opposing_list = get_opposing_parties_list()
        all_people = clients_list + opposing_list
        
        process_rows = []
        for proc in raw_processes:
            # Extrai e formata clientes (prioridade + MAIÚSCULAS) - retorna lista
            clients_raw = proc.get('clients') or proc.get('client') or []
            clients_list_formatted = _format_names_list(clients_raw, all_people)

            # Extrai e formata partes contrárias (prioridade + MAIÚSCULAS) - retorna lista
            opposing_raw = proc.get('opposing_parties') or []
            opposing_list_formatted = _format_names_list(opposing_raw, all_people)

            # Extrai casos vinculados - retorna lista
            cases_raw = proc.get('cases') or []
            if isinstance(cases_raw, list):
                cases_list = [str(c) for c in cases_raw if c]
            else:
                cases_list = [str(cases_raw)] if cases_raw else []

            # =====================================================
            # PROCESSAMENTO DE DATA DE ABERTURA (APROXIMADA)
            # =====================================================
            # Suporta 3 formatos:
            # - AAAA (apenas ano): 2008 → ordena como 2008/00/00
            # - MM/AAAA (mês/ano): 09/2008 → ordena como 2008/09/00
            # - DD/MM/AAAA (completa): 05/09/2008 → ordena como 2008/09/05
            # =====================================================
            data_abertura_raw = proc.get('data_abertura') or ''
            data_abertura_display = ''
            data_abertura_sort = ''  # Formato AAAA/MM/DD para ordenação correta
            
            if data_abertura_raw:
                try:
                    data_abertura_raw = data_abertura_raw.strip()
                    
                    # Formato: AAAA (apenas ano) - 4 dígitos
                    if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                        data_abertura_display = data_abertura_raw
                        data_abertura_sort = f"{data_abertura_raw}/00/00"
                    
                    # Formato: MM/AAAA (mês e ano) - 7 caracteres
                    elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                        partes = data_abertura_raw.split('/')
                        if len(partes) == 2:
                            data_abertura_display = data_abertura_raw
                            data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
                    
                    # Formato: DD/MM/AAAA (completa) - 10 caracteres
                    elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                        partes = data_abertura_raw.split('/')
                        if len(partes) == 3:
                            data_abertura_display = data_abertura_raw
                            data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
                    
                    # Formato legado: YYYY-MM-DD
                    elif '-' in data_abertura_raw:
                        partes = data_abertura_raw.split('-')
                        if len(partes) == 3:
                            data_abertura_display = f"{partes[2]}/{partes[1]}/{partes[0]}"
                            data_abertura_sort = f"{partes[0]}/{partes[1]}/{partes[2]}"
                        else:
                            data_abertura_display = data_abertura_raw
                    
                    else:
                        # Fallback - mantém valor original
                        data_abertura_display = data_abertura_raw
                        
                except Exception:
                    data_abertura_display = data_abertura_raw
            
            process_rows.append({
                '_id': proc.get('_id', ''),
                'tipo_processo': 'normal',  # Marcador de tipo
                'data_abertura': data_abertura_display,
                'data_abertura_sort': data_abertura_sort,  # Formato AAAA/MM/DD para ordenação
                'title': proc.get('title') or proc.get('searchable_title') or '(sem título)',
                'number': proc.get('number') or '',
                'clients_list': clients_list_formatted,
                'opposing_list': opposing_list_formatted,
                'cases_list': cases_list,
                'system': proc.get('system') or '',
                'status': proc.get('status') or '',
                'area': proc.get('area') or proc.get('area_direito') or '',
                'link': proc.get('link') or '',
                # Campos de acesso
                'access_requested': proc.get('access_lawyer_requested', False),
                'access_granted': proc.get('access_lawyer_granted', False),
                'access_technicians': proc.get('access_technicians', False) or proc.get('access_technicians_granted', False),
            })
        
        # 2. Carregar acompanhamentos de terceiros
        raw_acompanhamentos = obter_todos_acompanhamentos()
        acompanhamento_rows = []
        for acomp in raw_acompanhamentos:
            acompanhamento_rows.append(format_third_party_row(acomp))
        
        # 3. Consolidar ambos os tipos
        all_rows = process_rows + acompanhamento_rows
        
        # 4. Ordenar por data de abertura (decrescente) e depois por título
        all_rows.sort(key=lambda r: (
            r.get('data_abertura_sort', '') or '0000/00/00',
            (r.get('title') or '').lower()
        ), reverse=True)
        
        return all_rows
    except Exception as e:
        print(f"Erro ao buscar processos e acompanhamentos: {e}")
        import traceback
        traceback.print_exc()
        return []


# Colunas da tabela reorganizadas conforme especificação
# REGRA: Coluna "Data" (data de abertura) sempre como primeira coluna nas visualizações de processos
# Usa campo data_abertura_sort (AAAA/MM/DD) para ordenação cronológica correta
COLUMNS = [
    {'name': 'data_abertura', 'label': 'Data', 'field': 'data_abertura_sort', 'align': 'center', 'sortable': True, 'style': 'width: 90px; min-width: 90px; font-size: 11px;'},
    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True, 'style': 'width: 200px; max-width: 200px; font-size: 11px;'},
    {'name': 'cases', 'label': 'Casos', 'field': 'cases', 'align': 'left', 'style': 'width: 120px; min-width: 120px; font-size: 11px;'},
    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 120px; font-size: 11px;'},
    {'name': 'clients', 'label': 'Clientes', 'field': 'clients', 'align': 'left', 'style': 'width: 100px; max-width: 100px; font-size: 11px;'},
    {'name': 'opposing', 'label': 'Parte Contrária', 'field': 'opposing', 'align': 'left', 'style': 'width: 100px; max-width: 100px; font-size: 11px;'},
    {'name': 'system', 'label': 'Sistema', 'field': 'system', 'align': 'left', 'sortable': True, 'style': 'width: 120px; font-size: 11px;'},
    {'name': 'access_requested', 'label': 'Acesso Solicitado?', 'field': 'access_requested', 'align': 'center', 'style': 'width: 90px; font-size: 11px;'},
    {'name': 'access_granted', 'label': 'Acesso Concedido?', 'field': 'access_granted', 'align': 'center', 'style': 'width: 90px; font-size: 11px;'},
    {'name': 'access_technicians', 'label': 'Processo Disponibilizado para Técnicos?', 'field': 'access_technicians', 'align': 'center', 'style': 'width: 120px; font-size: 11px;'},
]


@ui.page('/processos/acesso')
def acesso_processos():
    """Página de visualização 'Acesso aos Processos'."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    with layout('Acesso aos Processos', breadcrumbs=[('Processos', '/processos'), ('Acesso aos Processos', None)]):
        # Aplicar CSS padrão de cores alternadas para tabelas de processos
        ui.add_head_html(TABELA_PROCESSOS_CSS)
        
        # Função de callback para atualizar após salvar processo
        def on_process_saved():
            invalidate_cache('processes')
            refresh_table()
        
        # Função de callback para atualizar após salvar acompanhamento
        def on_acompanhamento_saved():
            invalidate_cache('third_party_monitoring')
            refresh_table()
        
        # Criar modal completo com barra lateral (uma vez para toda a página)
        process_dialog, open_process_modal = render_process_dialog(
            on_success=on_process_saved
        )
        
        # Criar modal de acompanhamento de terceiros
        third_party_dialog, open_third_party_modal = render_third_party_monitoring_dialog(
            on_success=on_acompanhamento_saved
        )
        
        # Função para atualizar campo de acesso no banco de dados
        def update_access_field(item_id: str, tipo_processo: str, field_name: str, value: bool):
            """
            Atualiza um campo de acesso específico no processo ou acompanhamento.
            
            Args:
                item_id: ID do processo ou acompanhamento
                tipo_processo: 'normal' ou 'acompanhamento'
                field_name: Nome do campo ('access_requested', 'access_granted', 'access_technicians')
                value: Novo valor booleano
            """
            try:
                if tipo_processo == 'normal':
                    # Processo normal - salvar em 'processes'
                    all_processes = get_processes_list()
                    process = None
                    for p in all_processes:
                        if p.get('_id') == item_id:
                            process = p.copy()
                            break
                    
                    if not process:
                        print(f"Processo não encontrado: {item_id}")
                        ui.notify(f"Processo não encontrado", type='negative')
                        return
                    
                    # Mapeia campos da tabela para campos do banco
                    field_mapping = {
                        'access_requested': 'access_lawyer_requested',
                        'access_granted': 'access_lawyer_granted',
                        'access_technicians': 'access_technicians_granted'
                    }
                    
                    db_field = field_mapping.get(field_name, field_name)
                    process[db_field] = value
                    
                    # Se concedido, automaticamente marca como solicitado
                    if db_field == 'access_lawyer_granted' and value:
                        process['access_lawyer_requested'] = True
                    
                    # Para técnicos, mantém consistência entre access_technicians e access_technicians_granted
                    if db_field == 'access_technicians_granted':
                        process['access_technicians'] = value
                    
                    # Adiciona timestamp de atualização
                    process['data_atualizacao'] = datetime.now().isoformat()
                    
                    # Salva no Firestore
                    save_process(process, doc_id=item_id, sync=False)
                    
                    # Invalida cache e atualiza tabela
                    invalidate_cache('processes')
                    refresh_table()
                    ui.notify('Permissões atualizadas com sucesso', type='positive')
                    
                elif tipo_processo == 'acompanhamento':
                    # Acompanhamento - salvar em 'third_party_monitoring'
                    # Mapeia campos da tabela para campos do banco de acompanhamentos
                    field_mapping = {
                        'access_requested': 'access_lawyer_requested',
                        'access_granted': 'access_lawyer_granted',
                        'access_technicians': 'access_technicians_granted'
                    }
                    
                    db_field = field_mapping.get(field_name, field_name)
                    
                    # Prepara atualização
                    updates = {
                        db_field: value,
                        'data_atualizacao': datetime.now().isoformat()
                    }
                    
                    # Se concedido, automaticamente marca como solicitado
                    if db_field == 'access_lawyer_granted' and value:
                        updates['access_lawyer_requested'] = True
                    
                    # Para técnicos, mantém consistência
                    if db_field == 'access_technicians_granted':
                        updates['access_technicians'] = value
                    
                    # Atualiza no Firestore
                    sucesso = atualizar_acompanhamento(item_id, updates)
                    
                    if sucesso:
                        # Invalida cache e atualiza tabela
                        invalidate_cache('third_party_monitoring')
                        refresh_table()
                        ui.notify('Permissões atualizadas com sucesso', type='positive')
                    else:
                        ui.notify('Erro ao atualizar permissões do acompanhamento', type='negative')
                else:
                    print(f"Tipo de processo inválido: {tipo_processo}")
                    ui.notify(f"Tipo inválido: {tipo_processo}", type='negative')
                
            except Exception as e:
                print(f"Erro ao atualizar acesso: {e}")
                import traceback
                traceback.print_exc()
                ui.notify(f"Erro ao salvar: {e}", type='negative')
        
        # Estado dos filtros (usando variáveis Python simples)
        search_term = {'value': ''}
        filter_area = {'value': ''}
        filter_case = {'value': ''}
        filter_client = {'value': ''}
        filter_parte = {'value': ''}
        filter_opposing = {'value': ''}
        filter_status = {'value': ''}
        filter_priority = {'value': ''}  # Filtro de prioridade (P1, P2, P3, P4)
        
        # Referência para render_table (será definida depois)
        render_table_ref = {'func': None}
        
        # Função para atualizar tabela
        def refresh_table():
            if render_table_ref['func']:
                render_table_ref['func'].refresh()
        
        # Função para extrair opções únicas dos dados
        def get_filter_options():
            all_rows = fetch_processes()
            return {
                'area': [''] + sorted(set([r.get('area', '') for r in all_rows if r.get('area')])),
                'cases': [''] + sorted(set([c for r in all_rows for c in r.get('cases_list', []) if c])),
                'clients': [''] + sorted(set([c for r in all_rows for c in r.get('clients_list', []) if c])),
                'parte': [''] + sorted(set([c for r in all_rows for c in r.get('clients_list', []) if c])),
                'opposing': [''] + sorted(set([c for r in all_rows for c in r.get('opposing_list', []) if c])),
                'status': [''] + sorted(set([r.get('status', '') for r in all_rows if r.get('status')])),
                'priority': ['', 'P1', 'P2', 'P3', 'P4']  # Opções fixas de prioridade
            }
        
        # Filtros discretos em uma linha
        filter_options = get_filter_options()
        filter_selects = {}
        
        # Função auxiliar para criar filtros discretos
        def create_filter_dropdown(label, options, state_dict, width_class='min-w-[140px]'):
            select = ui.select(options, label=label, value='').props('clearable dense outlined').classes(width_class)
            # Estilo discreto e minimalista
            select.style('font-size: 12px; border-color: #d1d5db;')
            select.classes('filter-select')
            
            # Callback para atualizar filtro quando valor mudar
            def on_filter_change():
                state_dict['value'] = select.value if select.value else ''
                refresh_table()
            
            # Registrar callback
            select.on('update:model-value', on_filter_change)
            return select
        
        # Barra de pesquisa
        with ui.row().classes('w-full items-center gap-4 mb-4'):
            # Campo de busca com ícone de lupa
            with ui.input(placeholder='Pesquisar processos por título, número...').props('outlined dense clearable').classes('flex-grow max-w-xl') as search_input:
                with search_input.add_slot('prepend'):
                    ui.icon('search').classes('text-gray-400')
            
            # Callback para atualizar pesquisa quando valor mudar
            def on_search_change():
                search_term['value'] = search_input.value if search_input.value else ''
                refresh_table()
            
            search_input.on('update:model-value', on_search_change)
            
            # Botão para voltar à página principal de processos
            ui.button('← Voltar para Processos', on_click=lambda: ui.navigate.to('/processos')).props('flat').classes('whitespace-nowrap')
        
        # Linha de filtros
        with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
            ui.label('Filtros:').classes('text-gray-600 font-medium text-sm')
            # Criar filtros com rótulos limpos (sem ícones em inglês)
            filter_selects['area'] = create_filter_dropdown('Área', filter_options['area'], filter_area, 'min-w-[120px]')
            filter_selects['case'] = create_filter_dropdown('Casos', filter_options['cases'], filter_case, 'min-w-[140px]')
            filter_selects['client'] = create_filter_dropdown('Clientes', filter_options['clients'], filter_client, 'min-w-[140px]')
            filter_selects['parte'] = create_filter_dropdown('Parte', filter_options['parte'], filter_parte, 'min-w-[140px]')
            filter_selects['opposing'] = create_filter_dropdown('Parte Contrária', filter_options['opposing'], filter_opposing, 'min-w-[170px]')
            filter_selects['status'] = create_filter_dropdown('Status', filter_options['status'], filter_status, 'min-w-[140px]')
            filter_selects['priority'] = create_filter_dropdown('Prioridade', filter_options['priority'], filter_priority, 'min-w-[100px]')
            
            # Botão limpar filtros
            def clear_filters():
                filter_area['value'] = ''
                filter_case['value'] = ''
                filter_client['value'] = ''
                filter_parte['value'] = ''
                filter_opposing['value'] = ''
                filter_status['value'] = ''
                filter_priority['value'] = ''  # Limpa filtro de prioridade
                search_term['value'] = ''
                # Limpar valores dos selects
                filter_selects['area'].value = ''
                filter_selects['case'].value = ''
                filter_selects['client'].value = ''
                filter_selects['parte'].value = ''
                filter_selects['opposing'].value = ''
                filter_selects['status'].value = ''
                filter_selects['priority'].value = ''  # Limpa select de prioridade
                search_input.value = ''
                refresh_table()
            
            ui.button('Limpar', icon='clear_all', on_click=clear_filters).props('flat dense').classes('text-xs text-gray-600')
        
        # Função de filtragem
        def filter_rows(rows):
            filtered = rows
            
            # Filtro de pesquisa (título)
            if search_term['value']:
                term = search_term['value'].lower()
                filtered = [r for r in filtered if term in (r.get('title') or '').lower()]
            
            # Filtro de área
            if filter_area['value']:
                filtered = [r for r in filtered if r.get('area') == filter_area['value']]
            
            # Filtro de casos
            if filter_case['value']:
                filtered = [r for r in filtered if filter_case['value'] in (r.get('cases_list') or [])]
            
            # Filtro de clientes (apenas processos normais - acompanhamentos têm 'NA')
            if filter_client['value']:
                filtered = [r for r in filtered 
                           if r.get('tipo_processo') == 'acompanhamento' or 
                              filter_client['value'] in (r.get('clients_list') or [])]
            
            # Filtro de parte (apenas processos normais - acompanhamentos têm 'NA')
            if filter_parte['value']:
                filtered = [r for r in filtered 
                           if r.get('tipo_processo') == 'acompanhamento' or 
                              filter_parte['value'] in (r.get('clients_list') or [])]
            
            # Filtro de parte contrária (apenas processos normais - acompanhamentos têm 'NA')
            if filter_opposing['value']:
                filtered = [r for r in filtered 
                           if r.get('tipo_processo') == 'acompanhamento' or 
                              filter_opposing['value'] in (r.get('opposing_list') or [])]
            
            # Filtro de status
            if filter_status['value']:
                filtered = [r for r in filtered if r.get('status') == filter_status['value']]
            
            # Filtro de prioridade (P1, P2, P3, P4)
            if filter_priority['value']:
                filtered = [r for r in filtered if r.get('prioridade') == filter_priority['value']]
            
            return filtered

        @ui.refreshable
        def render_table():
            rows = fetch_processes()
            
            # Aplicar filtros
            rows = filter_rows(rows)
            
            if not rows:
                with ui.card().classes('w-full p-8 flex justify-center items-center'):
                    ui.label('Nenhum processo encontrado.').classes('text-gray-400 italic')
                return

            # Slots customizados
            table = ui.table(columns=COLUMNS, rows=rows, row_key='_id', pagination={'rowsPerPage': 20}).classes('w-full')
            # Estilo compacto para acomodar todas as colunas
            table.style('font-size: 11px;')
            
            # Handler para clique no título (abre modal de edição)
            def handle_title_click(e):
                clicked_row = e.args
                if clicked_row and '_id' in clicked_row:
                    item_id = clicked_row['_id']
                    tipo_processo = clicked_row.get('tipo_processo', 'normal')
                    
                    if tipo_processo == 'acompanhamento':
                        # Abre modal de acompanhamento
                        open_third_party_modal(monitoring_id=item_id)
                    else:
                        # Abre modal de processo normal
                        all_processes = get_processes_list()
                        for idx, proc in enumerate(all_processes):
                            if proc.get('_id') == item_id:
                                open_process_modal(idx)
                                break
            
            table.on('titleClick', handle_title_click)
            
            # Handler para atualizar checkboxes de acesso
            def handle_access_change(e):
                data = e.args
                item_id = data.get('process_id') or data.get('item_id')
                tipo_processo = data.get('tipo_processo', 'normal')
                field_name = data.get('field')
                value = data.get('value')
                if item_id and field_name:
                    update_access_field(item_id, tipo_processo, field_name, value)
            
            table.on('accessChange', handle_access_change)
            
            # Slot customizado para header da última coluna (com quebra de linha)
            table.add_slot('header-cell-access_technicians', '''
                <q-th :props="props" style="text-align: center; padding: 8px 10px; background-color: #f5f5f5; border-bottom: 2px solid #d0d0d0; border-right: 1px solid #e0e0e0; vertical-align: middle;">
                    <div style="font-size: 11px; font-weight: 600; line-height: 1.3;">
                        Processo Disponibilizado<br>para Técnicos?
                    </div>
                </q-th>
            ''')
            
            # Slot para data de abertura - exibe DD/MM/AAAA (usa props.row.data_abertura para exibição)
            table.add_slot('body-cell-data_abertura', '''
                <q-td :props="props" style="text-align: center; padding: 6px 10px; font-size: 11px; vertical-align: middle;">
                    <span v-if="props.row.data_abertura" class="text-gray-700" style="font-size: 11px; font-weight: 500;">{{ props.row.data_abertura }}</span>
                    <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
                </q-td>
            ''')
            
            # Slot para título - clicável para abrir modal de edição, com ícone de interrogação se solicitado
            # Diferenciação visual: acompanhamentos mostram ícone de link
            table.add_slot('body-cell-title', '''
                <q-td :props="props" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 200px; padding: 6px 10px; font-size: 11px; vertical-align: middle;">
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <q-icon v-if="props.row.tipo_processo === 'acompanhamento'" 
                                name="link" 
                                size="xs" 
                                color="info" 
                                style="flex-shrink: 0;"
                                title="Acompanhamento de Terceiros">
                        </q-icon>
                        <span class="cursor-pointer font-medium" 
                              style="line-height: 1.4; color: #223631; font-size: 11px;"
                              @click="$parent.$emit('titleClick', props.row)">
                            {{ props.value }}
                        </span>
                        <q-icon v-if="props.row.access_requested && !props.row.access_granted" 
                                name="help" 
                                size="xs" 
                                color="orange" 
                                style="cursor: pointer; flex-shrink: 0;"
                                title="Acesso solicitado pendente">
                        </q-icon>
                    </div>
                </q-td>
            ''')
            
            # Slot para sistema processual
            table.add_slot('body-cell-system', '''
                <q-td :props="props" style="padding: 6px 10px; font-size: 11px; vertical-align: middle;">
                    <span v-if="props.value" class="text-gray-700" style="font-size: 11px;">{{ props.value }}</span>
                    <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
                </q-td>
            ''')
            
            # Slot para clientes - exibe múltiplos verticalmente em espaço compacto
            # Acompanhamentos mostram 'NA' em cinza
            table.add_slot('body-cell-clients', '''
                <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 6px 10px; font-size: 11px;">
                    <div v-if="props.row.clients_list && props.row.clients_list.length > 0 && props.row.clients_list[0] !== 'NA'" style="display: flex; flex-direction: column; gap: 2px;">
                        <div v-for="(client, index) in props.row.clients_list" :key="index" class="text-gray-700" style="word-wrap: break-word; overflow-wrap: break-word; font-size: 11px; line-height: 1.3;">
                            {{ client }}
                        </div>
                    </div>
                    <span v-else class="text-gray-400" style="font-size: 11px;">{{ props.row.tipo_processo === 'acompanhamento' ? 'NA' : '—' }}</span>
                </q-td>
            ''')
            
            # Slot para parte contrária - exibe múltiplos verticalmente em espaço compacto
            # Acompanhamentos mostram 'NA' em cinza
            table.add_slot('body-cell-opposing', '''
                <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 6px 10px; font-size: 11px;">
                    <div v-if="props.row.opposing_list && props.row.opposing_list.length > 0 && props.row.opposing_list[0] !== 'NA'" style="display: flex; flex-direction: column; gap: 2px;">
                        <div v-for="(opposing, index) in props.row.opposing_list" :key="index" class="text-gray-700" style="word-wrap: break-word; overflow-wrap: break-word; font-size: 11px; line-height: 1.3;">
                            {{ opposing }}
                        </div>
                    </div>
                    <span v-else class="text-gray-400" style="font-size: 11px;">{{ props.row.tipo_processo === 'acompanhamento' ? 'NA' : '—' }}</span>
                </q-td>
            ''')
            
            # Slot para casos - exibe em linha única com ajuste automático
            table.add_slot('body-cell-cases', '''
                <q-td :props="props" style="vertical-align: middle; padding: 6px 10px; font-size: 11px;">
                    <div v-if="props.row.cases_list && props.row.cases_list.length > 0" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.4;">
                        <span v-for="(caso, index) in props.row.cases_list" :key="index" class="text-gray-700" style="font-size: 11px;">
                            {{ caso }}<span v-if="index < props.row.cases_list.length - 1">, </span>
                        </span>
                    </div>
                    <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
                </q-td>
            ''')
            
            # Slot para número - hyperlink clicável com ícone de copiar
            # PADRONIZADO: Números com e sem link têm exatamente a mesma aparência visual
            table.add_slot('body-cell-number', '''
                <q-td :props="props" style="padding: 6px 10px; font-size: 11px; vertical-align: middle;">
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <a v-if="props.row.link && props.value" 
                           :href="props.row.link" 
                           target="_blank" 
                           class="process-number-link"
                           style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; text-decoration: none; font-family: inherit;">
                            {{ props.value }}
                        </a>
                        <span v-else-if="props.value" 
                              class="process-number-text"
                              style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; font-family: inherit;">
                            {{ props.value }}
                        </span>
                        <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
                        <q-btn 
                            v-if="props.value"
                            flat dense round 
                            icon="content_copy" 
                            size="xs" 
                            color="grey"
                            class="ml-1"
                            @click.stop="$parent.$emit('copyNumber', props.value)"
                        >
                            <q-tooltip>Copiar número</q-tooltip>
                        </q-btn>
                    </div>
                </q-td>
            ''')
            
            # Handler para copiar número do processo para área de transferência
            def handle_copy_number(e):
                """
                Copia o número do processo para a área de transferência usando JavaScript.
                Compatível com Chrome, Firefox e Edge.
                """
                numero = e.args
                if numero:
                    # Escapa aspas simples no número para evitar erro de JS
                    numero_escaped = str(numero).replace("'", "\\'")
                    ui.run_javascript(f'''
                        navigator.clipboard.writeText('{numero_escaped}').then(() => {{
                            // Sucesso - notificação já exibida pelo NiceGUI
                        }}).catch(err => {{
                            console.error('Erro ao copiar:', err);
                        }});
                    ''')
                    ui.notify("Número copiado!", type="positive", position="top", timeout=1500)
            
            table.on('copyNumber', handle_copy_number)
            
            # Slot para acesso solicitado - checkbox ou N.A para processos futuros
            table.add_slot('body-cell-access_requested', '''
                <q-td :props="props" style="text-align: center; padding: 6px 10px; vertical-align: middle;">
                    <div style="display: flex; justify-content: center; align-items: center;">
                        <span v-if="props.row.status === 'Futuro/Previsto'" 
                              title="Processos futuros não possuem acesso ativo"
                              class="text-gray-400 text-sm italic" 
                              style="color: #999; font-style: italic; pointer-events: auto; user-select: none; cursor: help;">
                            N.A
                        </span>
                        <q-checkbox 
                            v-else
                            :model-value="props.row.access_requested"
                            @update:model-value="(val) => $parent.$emit('accessChange', {item_id: props.row._id, tipo_processo: props.row.tipo_processo || 'normal', field: 'access_requested', value: val})"
                            size="sm"
                            color="primary"
                            dense
                        />
                    </div>
                </q-td>
            ''')
            
            # Slot para acesso concedido - checkbox ou N.A para processos futuros
            table.add_slot('body-cell-access_granted', '''
                <q-td :props="props" style="text-align: center; padding: 6px 10px; vertical-align: middle;">
                    <div style="display: flex; justify-content: center; align-items: center;">
                        <span v-if="props.row.status === 'Futuro/Previsto'" 
                              title="Processos futuros não possuem acesso ativo"
                              class="text-gray-400 text-sm italic" 
                              style="color: #999; font-style: italic; pointer-events: auto; user-select: none; cursor: help;">
                            N.A
                        </span>
                        <q-checkbox 
                            v-else
                            :model-value="props.row.access_granted"
                            @update:model-value="(val) => $parent.$emit('accessChange', {item_id: props.row._id, tipo_processo: props.row.tipo_processo || 'normal', field: 'access_granted', value: val})"
                            size="sm"
                            color="primary"
                            dense
                        />
                    </div>
                </q-td>
            ''')
            
            # Slot para processo disponibilizado para técnicos - checkbox ou N.A para processos futuros
            table.add_slot('body-cell-access_technicians', '''
                <q-td :props="props" style="text-align: center; padding: 6px 10px; vertical-align: middle;">
                    <div style="display: flex; justify-content: center; align-items: center;">
                        <span v-if="props.row.status === 'Futuro/Previsto'" 
                              title="Processos futuros não possuem acesso ativo"
                              class="text-gray-400 text-sm italic" 
                              style="color: #999; font-style: italic; pointer-events: auto; user-select: none; cursor: help;">
                            N.A
                        </span>
                        <q-checkbox 
                            v-else
                            :model-value="props.row.access_technicians"
                            @update:model-value="(val) => $parent.$emit('accessChange', {item_id: props.row._id, tipo_processo: props.row.tipo_processo || 'normal', field: 'access_technicians', value: val})"
                            size="sm"
                            color="primary"
                            dense
                        />
                    </div>
                </q-td>
            ''')
        
        render_table_ref['func'] = render_table
        render_table()
