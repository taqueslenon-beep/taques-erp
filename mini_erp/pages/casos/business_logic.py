"""
Módulo de lógica de negócio para o módulo de Casos.

Contém funções de cálculo, validação e processamento de casos
sem dependência de UI (lógica pura).
"""

from google.cloud.firestore import SERVER_TIMESTAMP

from ...core import (
    get_cases_list,
    get_clients_list,
    slugify
)

from .models import (
    CASE_TYPE_OPTIONS,
    CASE_TYPE_PREFIX,
    filter_state
)


def get_case_type(case: dict) -> str:
    """
    Retorna o tipo do caso baseado no campo case_type ou is_new_case (compatibilidade).
    
    Args:
        case: Dicionário com dados do caso
        
    Returns:
        Tipo do caso: 'Antigo', 'Novo' ou 'Futuro'
    """
    ct = case.get('case_type')
    if ct in CASE_TYPE_OPTIONS:
        return ct
    # Compatibilidade com dados antigos que usam is_new_case
    if case.get('is_new_case', False):
        return 'Novo'
    return 'Antigo'


def get_case_sort_key(case: dict) -> tuple:
    """
    Retorna a chave de ordenação para um caso (ano, mês, nome).
    
    Args:
        case: Dicionário com dados do caso
        
    Returns:
        Tupla (ano, mês, nome) para ordenação
    """
    year = case.get('year', '9999')
    if isinstance(year, str):
        year = int(year) if year.isdigit() else 9999
    month = case.get('month', 12)
    if month is None:
        month = 12
    name = case.get('name', '').lower()
    return (year, month, name)


def get_cases_by_type(case_type: str) -> list:
    """
    Retorna todos os casos de um tipo específico, ordenados por data.
    
    Args:
        case_type: Tipo do caso ('Antigo', 'Novo' ou 'Futuro')
        
    Returns:
        Lista de casos filtrados e ordenados
    """
    cases_of_type = [c for c in get_cases_list() if get_case_type(c) == case_type]
    return sorted(cases_of_type, key=get_case_sort_key)


def calculate_case_number(case_type: str, year: int, month: int, name: str) -> int:
    """
    Calcula o número sequencial de um caso baseado na sua posição cronológica.
    
    Args:
        case_type: Tipo do caso
        year: Ano do caso
        month: Mês do caso
        name: Nome do caso
        
    Returns:
        Número sequencial que o caso deve ter dentro do seu tipo
    """
    # Pegar todos os casos do mesmo tipo ordenados
    existing_cases = get_cases_by_type(case_type)
    
    # Criar chave de ordenação para o novo caso
    new_case_key = (year, month, name.lower())
    
    # Encontrar a posição onde o novo caso se encaixa
    position = 1
    for existing_case in existing_cases:
        existing_key = get_case_sort_key(existing_case)
        if new_case_key > existing_key:
            position += 1
        else:
            break
    
    return position


def generate_case_title(case_type: str, sequence: int, name: str, year: int) -> str:
    """
    Gera o título formatado do caso: X.Y - Nome / Ano
    
    Args:
        case_type: Tipo do caso
        sequence: Número sequencial do caso
        name: Nome do caso
        year: Ano do caso
        
    Returns:
        Título formatado do caso
    """
    prefix = CASE_TYPE_PREFIX.get(case_type, 1)
    return f"{prefix}.{sequence} - {name} / {year}"


def deduplicate_cases_by_title(cases: list) -> list:
    """
    Remove casos duplicados baseado em título + ano.
    
    Mantém apenas o primeiro caso encontrado para cada combinação única
    de título e ano.
    
    Args:
        cases: Lista de casos
        
    Returns:
        Lista de casos únicos (sem duplicatas)
    """
    seen = {}
    unique_cases = []
    
    for case in cases:
        title = case.get('title', '')
        year = case.get('year', '')
        key = f"{title}|{year}"
        
        if key not in seen:
            seen[key] = True
            unique_cases.append(case)
    
    return unique_cases


def get_filtered_cases() -> list:
    """
    Retorna casos filtrados com base nos filtros ativos, sem duplicatas.
    
    Returns:
        Lista de casos filtrados
    """
    raw_cases = get_cases_list().copy()
    
    # DEDUPLICAÇÃO: Remove duplicatas por título+ano primeiro
    # raw_cases = deduplicate_cases_by_title(raw_cases)
    
    # DEDUPLICAÇÃO: Remove duplicatas por slug (identificador único)
    # Mantém apenas o primeiro caso encontrado para cada slug
    seen_slugs = set()
    filtered = []
    for c in raw_cases:
        slug = c.get('slug') or c.get('_id', '')
        if slug and slug not in seen_slugs:
            seen_slugs.add(slug)
            filtered.append(c)
        elif not slug:
            # Caso sem slug (legado), adiciona mesmo assim
            filtered.append(c)
    
    # Filtro de busca livre
    if filter_state['search']:
        search_term = filter_state['search'].lower()
        clients_list = get_clients_list()
        filtered = [c for c in filtered if 
            search_term in c.get('title', '').lower() or
            search_term in c.get('name', '').lower() or
            search_term in ' '.join(c.get('clients', [])).lower() or
            # Buscar também por sigla/apelido dos clientes
            any(search_term in (cl.get('nickname', '') or '').lower() or 
                search_term in (cl.get('alias', '') or '').lower()
                for cl_name in c.get('clients', [])
                for cl in clients_list if cl.get('name') == cl_name)
        ]
    
    # Filtro por status
    if filter_state['status']:
        filtered = [c for c in filtered if c.get('status') == filter_state['status']]
    
    # Filtro por cliente
    if filter_state['client']:
        filtered = [c for c in filtered if filter_state['client'] in c.get('clients', [])]
    
    # Filtro por estado (UF)
    if filter_state['state']:
        filtered = [c for c in filtered if c.get('state') == filter_state['state']]
    
    # Filtro por categoria (Contencioso ou Consultivo)
    if filter_state['category']:
        filtered = [c for c in filtered if c.get('category', 'Contencioso') == filter_state['category']]

    # Filtro por tipo de caso (antigo, novo ou futuro)
    view_type = filter_state.get('case_type')
    if view_type == 'new':
        filtered = [c for c in filtered if get_case_type(c) == 'Novo']
    elif view_type == 'old':
        filtered = [c for c in filtered if get_case_type(c) == 'Antigo']
    elif view_type == 'future':
        filtered = [c for c in filtered if get_case_type(c) == 'Futuro']
    
    # Ordenar por data (ano, mês, nome)
    filtered = sorted(filtered, key=get_case_sort_key)
    
    return filtered


def create_new_case_dict(
    case_name: str,
    year: int,
    month: int,
    case_type: str,
    category: str,
    status: str,
    state: str,
    parte_contraria: str,
    parte_contraria_options: dict,
    selected_clients: list,
    selected_responsaveis: list = None
) -> dict:
    """
    Cria um dicionário para um novo caso com todos os campos necessários.
    
    Args:
        case_name: Nome do caso
        year: Ano do caso
        month: Mês do caso
        case_type: Tipo do caso ('Antigo', 'Novo', 'Futuro')
        category: Categoria ('Contencioso', 'Consultivo')
        status: Status do caso
        state: Estado (UF)
        parte_contraria: Código da parte contrária
        parte_contraria_options: Dicionário com opções de parte contrária
        selected_clients: Lista de clientes selecionados
        selected_responsaveis: Lista de responsáveis selecionados (opcional)
        
    Returns:
        Dicionário com dados do novo caso
    """
    # Calcular número sequencial baseado na posição cronológica
    case_num = calculate_case_number(case_type, year, month, case_name)
    prefix = CASE_TYPE_PREFIX.get(case_type, 1)
    
    year_str = str(year)
    
    # Gerar título no formato X.Y - Nome / Ano
    formatted_title = f"{prefix}.{case_num} - {case_name} / {year_str}"
    # Inclui prefixo e número no slug para garantir unicidade
    slug = slugify(f"{prefix}-{case_num} {case_name} {year_str}")
    
    # Processar responsáveis com timestamp
    responsaveis_data = []
    if selected_responsaveis:
        for resp in selected_responsaveis:
            responsaveis_data.append({
                'usuario_id': resp.get('usuario_id', ''),
                'nome': resp.get('nome', ''),
                'email': resp.get('email', ''),
                'data_atribuicao': SERVER_TIMESTAMP
            })
    
    return {
        'title': formatted_title,
        'name': case_name,
        'year': year_str,
        'month': month,
        'number': case_num,
        'slug': slug,
        'status': status,
        'state': state,
        'parte_contraria': parte_contraria or '-',
        'parte_contraria_nome': parte_contraria_options.get(parte_contraria or '-', ''),
        'clients': selected_clients.copy(),
        'responsaveis': responsaveis_data,
        # Tipo de caso: Antigo, Novo ou Futuro
        'case_type': case_type,
        # Categoria: Contencioso ou Consultivo
        'category': category,
        # Manter is_new_case para compatibilidade retroativa
        'is_new_case': case_type == 'Novo',
        'processes': [],
        'links': [],
        'objectives': '',
        'legal_considerations': '',
        'technical_considerations': '',
        'theses': [],
        'swot_s': [''] * 10,
        'swot_w': [''] * 10,
        'swot_o': [''] * 10,
        'swot_t': [''] * 10,
        'strategy_observations': '',
        'next_actions': '',
        'maps': [],
        'map_notes': ''
    }

