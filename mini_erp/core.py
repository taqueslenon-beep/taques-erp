import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
from nicegui import ui, run, app
import re
import unicodedata

# Importa configuração do Firebase
from .firebase_config import get_db
from firebase_admin import auth as admin_auth
from .auth import get_current_user

# Cor primária do sistema (verde escuro)
PRIMARY_COLOR = '#223631'

# Cache local para reduzir consultas ao Firestore
_cache = {}
_cache_timestamp = {}
_cache_lock = threading.Lock()  # Lock para evitar chamadas concorrentes
# Cache de 15 minutos - otimizado para poucos registros
# Invalidação manual ocorre após operações de escrita (salvar/deletar)
CACHE_DURATION = 900  # 15 minutos em segundos


def digits_only(value: Optional[str]) -> str:
    """Remove caracteres não numéricos."""
    if not value:
        return ''
    return re.sub(r'\D', '', str(value))


def format_cpf(value: Optional[str]) -> str:
    """Formata CPF no padrão 000.000.000-00."""
    digits = digits_only(value)
    if len(digits) != 11:
        return digits
    return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'


def format_cnpj(value: Optional[str]) -> str:
    """Formata CNPJ no padrão 00.000.000/0000-00."""
    digits = digits_only(value)
    if len(digits) != 14:
        return digits
    return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'


def is_valid_cpf(value: Optional[str]) -> bool:
    """Valida CPF pelos dígitos verificadores."""
    digits = digits_only(value)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    sum_1 = sum(int(digits[i]) * (10 - i) for i in range(9))
    remainder_1 = sum_1 % 11
    check_1 = 0 if remainder_1 < 2 else 11 - remainder_1
    if check_1 != int(digits[9]):
        return False
    sum_2 = sum(int(digits[i]) * (11 - i) for i in range(10))
    remainder_2 = sum_2 % 11
    check_2 = 0 if remainder_2 < 2 else 11 - remainder_2
    return check_2 == int(digits[10])


def is_valid_cnpj(value: Optional[str]) -> bool:
    """Valida CNPJ pelos dígitos verificadores."""
    digits = digits_only(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    multipliers_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(int(digits[i]) * multipliers_1[i] for i in range(12))
    remainder_1 = sum_1 % 11
    check_1 = 0 if remainder_1 < 2 else 11 - remainder_1
    if check_1 != int(digits[12]):
        return False
    multipliers_2 = [6] + multipliers_1
    sum_2 = sum(int(digits[i]) * multipliers_2[i] for i in range(13))
    remainder_2 = sum_2 % 11
    check_2 = 0 if remainder_2 < 2 else 11 - remainder_2
    return check_2 == int(digits[13])


def _format_document_display(cpf: Optional[str], cnpj: Optional[str]) -> str:
    """Monta string amigável para CPF/CNPJ."""
    parts = []
    if cpf:
        parts.append(format_cpf(cpf))
    if cnpj:
        parts.append(format_cnpj(cnpj))
    return ' / '.join(filter(None, parts))


def normalize_client_documents(client: Dict[str, Any]) -> Dict[str, Any]:
    """Garante campos consistentes para documentos de clientes."""
    cpf_digits = digits_only(client.get('cpf'))
    cnpj_digits = digits_only(client.get('cnpj'))
    legacy_doc = client.get('cpf_cnpj') or client.get('document', '')
    legacy_digits = digits_only(legacy_doc)

    if not cpf_digits and len(legacy_digits) == 11:
        cpf_digits = legacy_digits
    if not cnpj_digits and len(legacy_digits) == 14:
        cnpj_digits = legacy_digits

    client['cpf'] = cpf_digits or ''
    client['cnpj'] = cnpj_digits or ''

    allowed_types = {'PF', 'PJ', 'PF/PJ'}
    client_type = client.get('client_type')
    if client_type not in allowed_types:
        if cpf_digits and cnpj_digits:
            client_type = 'PF/PJ'
        elif cnpj_digits:
            client_type = 'PJ'
        else:
            client_type = 'PF'
    client['client_type'] = client_type

    document_display = _format_document_display(cpf_digits, cnpj_digits)
    if not document_display:
        document_display = legacy_doc or ''
    client['cpf_cnpj'] = document_display
    client['document'] = document_display
    return client


def normalize_entity_type_value(value: Optional[str]) -> str:
    """Padroniza rótulo de tipo de entidade."""
    if not value:
        return 'PF'
    if isinstance(value, str) and value.upper() == 'ÓRGÃO PÚBLICO':
        return 'Órgão Público'
    allowed = {'PF', 'PJ', 'Órgão Público'}
    if value in allowed:
        return value
    return 'PF'


def _get_collection(collection_name: str) -> List[Dict[str, Any]]:
    """
    Obtém dados de uma coleção do Firestore com cache thread-safe.
    
    Para a coleção 'processes', filtra automaticamente processos deletados
    (isDeleted=True) para não exibi-los no frontend.
    """
    import time
    
    now = time.time()
    
    # Verifica cache sem lock (leitura rápida)
    if collection_name in _cache and collection_name in _cache_timestamp:
        if now - _cache_timestamp[collection_name] < CACHE_DURATION:
            return _cache[collection_name]
    
    # Usa lock para evitar múltiplas consultas simultâneas ao Firestore
    with _cache_lock:
        # Verifica novamente dentro do lock (outro thread pode ter atualizado)
        if collection_name in _cache and collection_name in _cache_timestamp:
            if now - _cache_timestamp[collection_name] < CACHE_DURATION:
                return _cache[collection_name]
        
        # Só consulta Firestore se cache expirou ou não existe
        try:
            db = get_db()
            docs = db.collection(collection_name).stream()
            items = []
            for doc in docs:
                item = doc.to_dict()
                item['_id'] = doc.id  # Guarda o ID do documento
                
                # Filtra processos deletados (soft delete)
                # Apenas para coleção 'processes'
                if collection_name == 'processes':
                    # Ignora processos marcados como deletados
                    if item.get('isDeleted') is True:
                        continue
                
                items.append(item)
            
            # Atualiza cache
            _cache[collection_name] = items
            _cache_timestamp[collection_name] = time.time()
            
            return items
        except Exception as e:
            print(f"Erro ao buscar {collection_name}: {e}")
            # Retorna cache antigo se houver erro
            return _cache.get(collection_name, [])


def _save_to_collection(collection_name: str, item: Dict[str, Any], doc_id: str = None):
    """Salva um item em uma coleção do Firestore."""
    db = get_db()
    
    # Remove _id do item antes de salvar (é metadado interno)
    item_to_save = {k: v for k, v in item.items() if k != '_id'}
    
    if doc_id:
        doc_id = doc_id.replace('/', '-').replace(' ', '-').lower()[:100]
        db.collection(collection_name).document(doc_id).set(item_to_save)
    else:
        db.collection(collection_name).add(item_to_save)
    
    # Invalida cache
    _cache.pop(collection_name, None)


def _delete_from_collection(collection_name: str, doc_id: str):
    """Remove um item de uma coleção do Firestore."""
    db = get_db()
    db.collection(collection_name).document(doc_id).delete()
    
    # Invalida cache
    _cache.pop(collection_name, None)


def _update_in_collection(collection_name: str, doc_id: str, updates: Dict[str, Any]):
    """Atualiza campos específicos de um documento."""
    db = get_db()
    
    # Remove _id dos updates
    updates_clean = {k: v for k, v in updates.items() if k != '_id'}
    
    db.collection(collection_name).document(doc_id).update(updates_clean)
    
    # Invalida cache
    _cache.pop(collection_name, None)


def invalidate_cache(collection_name: str = None):
    """Invalida o cache de uma coleção ou de todas."""
    if collection_name:
        _cache.pop(collection_name, None)
        _cache_timestamp.pop(collection_name, None)  # Também limpa o timestamp!
    else:
        _cache.clear()
        _cache_timestamp.clear()


# Funções de acesso às listas (compatibilidade com código existente)
def get_cases_list() -> List[Dict[str, Any]]:
    return _get_collection('cases')


def get_processes_list() -> List[Dict[str, Any]]:
    return _get_collection('processes')


def get_child_processes(parent_id: str) -> List[Dict[str, Any]]:
    """
    Busca todos os processos filhos diretos de um processo pai.
    
    Args:
        parent_id: ID do processo pai
        
    Returns:
        Lista de processos que têm este parent_id
    """
    if not parent_id:
        return []
    try:
        db = get_db()
        query = db.collection('processes').where('parent_id', '==', parent_id)
        docs = query.stream()
        children = []
        for doc in docs:
            process = doc.to_dict()
            process['_id'] = doc.id
            
            # Filtra processos deletados (soft delete)
            if process.get('isDeleted') is True:
                continue
            
            children.append(process)
        return children
    except Exception as e:
        print(f"[ERROR] Erro ao buscar filhos do processo {parent_id}: {e}")
        return []


def get_root_processes() -> List[Dict[str, Any]]:
    """
    Busca todos os processos raiz (sem pai).
    
    Returns:
        Lista de processos onde parent_id é None ou não existe
    """
    try:
        all_processes = get_processes_list()
        # Filtra apenas processos sem pai
        roots = [p for p in all_processes if not p.get('parent_id')]
        return roots
    except Exception as e:
        print(f"[ERROR] Erro ao buscar processos raiz: {e}")
        return []


def build_process_tree(processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Organiza uma lista de processos em estrutura hierárquica para exibição.
    Retorna lista ordenada com processos pai seguidos de seus filhos (indentados).
    
    Args:
        processes: Lista de todos os processos
        
    Returns:
        Lista ordenada: pai1, filho1.1, neto1.1.1, filho1.2, pai2, filho2.1...
        Cada processo recebe '_display_depth' indicando nível de indentação.
    """
    if not processes:
        return []
    
    # Criar índice por ID para busca rápida
    by_id = {p.get('_id'): p for p in processes if p.get('_id')}
    
    # Mapear filhos por parent_id
    children_map = {}  # parent_id -> [children]
    roots = []
    orphans = []  # Filhos cujo pai não está na lista (foi filtrado)
    
    for p in processes:
        parent_id = p.get('parent_id')
        if not parent_id:
            # Processo raiz
            p['_display_depth'] = 0
            roots.append(p)
        elif parent_id in by_id:
            # Filho com pai presente na lista
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(p)
        else:
            # Órfão: pai foi filtrado, mostrar como raiz
            p['_display_depth'] = 0
            p['_is_orphan'] = True  # Marcar para possível indicação visual
            orphans.append(p)
    
    # Função para ordenar por data (mais recentes primeiro)
    def sort_key(x):
        # Tenta usar data_abertura, senão usa título
        date = x.get('data_abertura') or ''
        title = x.get('title') or ''
        # Inverter para ordem decrescente
        return (date, title)
    
    # Ordenar raízes por data (mais recentes primeiro)
    roots.sort(key=sort_key, reverse=True)
    orphans.sort(key=sort_key, reverse=True)
    
    # Função recursiva para adicionar filhos
    def add_with_children(process: Dict, depth: int, result: List[Dict]):
        process['_display_depth'] = depth
        result.append(process)
        
        # Buscar e ordenar filhos
        proc_id = process.get('_id')
        children = children_map.get(proc_id, [])
        children.sort(key=sort_key, reverse=True)
        
        # Adicionar cada filho recursivamente
        for child in children:
            add_with_children(child, depth + 1, result)
    
    # Construir lista final
    result = []
    
    # Primeiro: raízes com seus filhos
    for root in roots:
        add_with_children(root, 0, result)
    
    # Depois: órfãos (filhos cujo pai não está na lista)
    for orphan in orphans:
        add_with_children(orphan, 0, result)
    
    return result


def get_clients_list() -> List[Dict[str, Any]]:
    """
    Obtém lista de clientes do Firestore.
    
    Retorna apenas clientes da coleção 'clients' para evitar duplicatas.
    """
    return _get_collection('clients')


def get_opposing_parties_list() -> List[Dict[str, Any]]:
    return _get_collection('opposing_parties')


def get_all_people_for_opposing_parties() -> List[Dict[str, Any]]:
    """
    Obtém todas as pessoas cadastradas (Clientes + Outros Envolvidos) 
    para usar como opções de Parte Contrária.
    
    Retorna lista com:
    - _id: UID da pessoa
    - display_name: nome para exibição
    - full_name: nome completo
    - type: 'Cliente - PF', 'Cliente - PJ' ou 'Órgão Público', 'PF', 'PJ'
    """
    people = []
    
    # Adiciona Clientes
    for client in get_clients_list():
        client_type = client.get('client_type', 'PF')
        people.append({
            '_id': client.get('_id'),
            'display_name': get_display_name(client),
            'full_name': get_full_name(client),
            'type': f'Cliente - {client_type}',
            'source': 'client'
        })
    
    # Adiciona Outros Envolvidos
    for opposing in get_opposing_parties_list():
        entity_type = opposing.get('entity_type', 'PF')
        people.append({
            '_id': opposing.get('_id'),
            'display_name': get_display_name(opposing),
            'full_name': get_full_name(opposing),
            'type': entity_type,
            'source': 'opposing_party'
        })
    
    # Ordena por display_name
    people.sort(key=lambda x: x.get('display_name', '').lower())
    
    return people


# Cache para nomes de exibição (thread-safe)
_display_name_cache = {}
_display_name_cache_timestamp = {}
# Cache de 15 minutos - otimizado para poucos registros
# Invalidação manual ocorre após operações de escrita (salvar/deletar)
DISPLAY_NAME_CACHE_DURATION = 900  # 15 minutos em segundos

def get_display_name_by_id(person_id: str, person_type: str = None) -> str:
    """
    Função centralizada para obter nome de exibição por ID da pessoa.
    
    Esta é a função principal que deve ser usada em todos os módulos.
    Implementa cache thread-safe para otimizar performance.
    
    Args:
        person_id: ID da pessoa (campo _id no Firestore)
        person_type: Tipo da pessoa ('client', 'opposing_party') - opcional para otimização
    
    Returns:
        Nome de exibição da pessoa ou "Sem identificação" se não encontrada
    
    Prioridade de exibição:
        1. nickname (se existir e não vazio)
        2. display_name (se existir e não vazio) 
        3. full_name (fallback)
        4. name (compatibilidade com dados antigos)
        5. "Sem identificação" (se pessoa não encontrada)
    """
    import time
    
    if not person_id:
        return "Sem identificação"
    
    # Verifica cache
    cache_key = f"{person_id}_{person_type or 'any'}"
    now = time.time()
    
    if cache_key in _display_name_cache and cache_key in _display_name_cache_timestamp:
        if now - _display_name_cache_timestamp[cache_key] < DISPLAY_NAME_CACHE_DURATION:
            return _display_name_cache[cache_key]
    
    # Busca pessoa no Firestore
    with _cache_lock:
        # Verifica cache novamente dentro do lock
        if cache_key in _display_name_cache and cache_key in _display_name_cache_timestamp:
            if now - _display_name_cache_timestamp[cache_key] < DISPLAY_NAME_CACHE_DURATION:
                return _display_name_cache[cache_key]
        
        try:
            person = None
            
            # Otimização: se tipo especificado, busca apenas na coleção específica
            if person_type == 'client':
                clients = get_clients_list()
                person = next((c for c in clients if c.get('_id') == person_id), None)
            elif person_type == 'opposing_party':
                opposing = get_opposing_parties_list()
                person = next((o for o in opposing if o.get('_id') == person_id), None)
            else:
                # Busca em ambas as coleções
                clients = get_clients_list()
                person = next((c for c in clients if c.get('_id') == person_id), None)
                
                if not person:
                    opposing = get_opposing_parties_list()
                    person = next((o for o in opposing if o.get('_id') == person_id), None)
            
            if person:
                display_name = get_display_name(person)
                # Atualiza cache
                _display_name_cache[cache_key] = display_name
                _display_name_cache_timestamp[cache_key] = time.time()
                return display_name
            else:
                # Pessoa não encontrada - cache resultado negativo por menos tempo
                not_found = "Sem identificação"
                _display_name_cache[cache_key] = not_found
                _display_name_cache_timestamp[cache_key] = time.time() - DISPLAY_NAME_CACHE_DURATION + 60  # Cache por apenas 1 minuto
                return not_found
                
        except Exception as e:
            print(f"Erro ao buscar nome de exibição para {person_id}: {e}")
            return "Sem identificação"


def get_display_name(item: Dict[str, Any]) -> str:
    """
    Retorna o nome para exibição de um item (dicionário de pessoa).
    
    Esta função trabalha com o objeto pessoa já carregado.
    Para buscar por ID, use get_display_name_by_id().
    
    Prioridade de exibição:
        1. nickname (se existir e não vazio)
        2. nome_exibicao (campo padronizado, se existir e não vazio)
        3. display_name (compatibilidade, se existir e não vazio)
        4. full_name (fallback)
        5. name (compatibilidade com dados antigos)
        6. string vazia (se nenhum campo disponível)
    
    Args:
        item: Dicionário com dados da pessoa
    
    Returns:
        Nome de exibição da pessoa
    """
    if not item:
        return ""
    
    # Prioridade 1: nickname
    nickname = item.get('nickname', '').strip()
    if nickname:
        return nickname
    
    # Prioridade 2: nome_exibicao (campo padronizado)
    nome_exibicao = item.get('nome_exibicao', '').strip()
    if nome_exibicao:
        return nome_exibicao
    
    # Prioridade 3: display_name (compatibilidade)
    display_name = item.get('display_name', '').strip()
    if display_name:
        return display_name
    
    # Prioridade 4: full_name
    full_name = item.get('full_name', '').strip()
    if full_name:
        return full_name
    
    # Prioridade 5: name (compatibilidade)
    name = item.get('name', '').strip()
    if name:
        return name
    
    return ""


def invalidate_display_name_cache(person_id: str = None):
    """
    Invalida o cache de nomes de exibição.
    
    Args:
        person_id: ID específico para invalidar. Se None, limpa todo o cache.
    """
    if person_id:
        # Remove entradas específicas da pessoa
        keys_to_remove = [k for k in _display_name_cache.keys() if k.startswith(f"{person_id}_")]
        for key in keys_to_remove:
            _display_name_cache.pop(key, None)
            _display_name_cache_timestamp.pop(key, None)
    else:
        # Limpa todo o cache
        _display_name_cache.clear()
        _display_name_cache_timestamp.clear()


def get_full_name(item: Dict[str, Any]) -> str:
    """
    Retorna o nome completo do item.
    Suporta tanto novo schema (full_name) quanto legado (name).
    """
    return item.get('full_name') or item.get('name', '')


def format_client_option_for_select(item: dict) -> str:
    """
    Formata opção de cliente para exibição em dropdowns.
    Retorna string no formato "Nome Completo (Apelido/Display)" ou apenas "Nome Completo".
    Usado consistentemente em New Case e New Process modals.
    
    Prioridade de exibição no parênteses: nickname > display_name
    """
    full_name = get_full_name(item)
    display = get_display_name(item)
    
    # Se display é diferente do nome completo, mostra entre parênteses
    if display and display != full_name:
        return f"{full_name} ({display})"
    return full_name


def get_client_options_for_select() -> List[str]:
    """
    Retorna lista de opções de clientes formatadas para uso em dropdowns.
    Inclui tanto Clientes quanto Outros Envolvidos.
    Usa o mesmo formato do New Case modal para consistência.
    """
    options = []
    # Adiciona Clientes
    for c in get_clients_list():
        formatted = format_client_option_for_select(c)
        if formatted:
            options.append(formatted)
    # Adiciona Outros Envolvidos
    for op in get_opposing_parties_list():
        formatted = format_client_option_for_select(op)
        if formatted:
            options.append(formatted)
    # Remove duplicatas e ordena
    options = sorted(list(set(options)), key=str.lower)
    return options


def get_client_id_by_name(client_name: str) -> Optional[str]:
    """
    Retorna o ID do cliente (ou outro envolvido) dado o nome completo.
    Primeiro busca em Clientes, depois em Outros Envolvidos.
    Retorna None se não encontrar.
    """
    # Busca em Clientes
    for c in get_clients_list():
        if c.get('name', '') == client_name:
            return c.get('_id') or client_name
    
    # Busca em Outros Envolvidos
    for op in get_opposing_parties_list():
        if op.get('name', '') == client_name:
            return op.get('_id') or client_name
    
    return None


def get_case_title_by_slug(case_slug: str) -> Optional[str]:
    """
    Retorna o título do caso dado o slug.
    """
    if not case_slug:
        return None
    
    try:
        db = get_db()
        case_doc = db.collection('cases').document(case_slug).get()
        if case_doc.exists:
            case_data = case_doc.to_dict()
            return case_data.get('title', '')
    except Exception as e:
        print(f"Erro ao buscar título do caso {case_slug}: {e}")

def get_case_by_slug(case_slug: str) -> Optional[Dict[str, Any]]:
    """
    Retorna os dados completos do caso dado o slug.
    """
    if not case_slug:
        return None
    
    try:
        db = get_db()
        case_doc = db.collection('cases').document(case_slug).get()
        if case_doc.exists:
            return case_doc.to_dict()
    except Exception as e:
        print(f"Erro ao buscar caso {case_slug}: {e}")
    return None
    
    return None


def get_client_name_by_id(client_id: str) -> Optional[str]:
    """
    Retorna o nome completo do cliente (ou outro envolvido) dado o ID.
    Primeiro busca em Clientes, depois em Outros Envolvidos.
    Retorna None se não encontrar.
    """
    # Busca em Clientes
    for c in get_clients_list():
        c_id = c.get('_id') or c.get('name', '')
        if c_id == client_id:
            return c.get('name', '')
    
    # Busca em Outros Envolvidos
    for op in get_opposing_parties_list():
        op_id = op.get('_id') or op.get('name', '')
        if op_id == client_id:
            return op.get('name', '')
    
    return None


def extract_client_name_from_formatted_option(formatted_option: str) -> str:
    """
    Extrai o nome completo de uma opção formatada.
    Remove a parte entre parênteses se existir.
    Exemplo: "Carlos Schmidmeier (Carlos)" -> "Carlos Schmidmeier"
    """
    if '(' in formatted_option:
        return formatted_option.split(' (')[0]
    return formatted_option


def get_users_list() -> List[Dict[str, Any]]:
    return _get_collection('users')


def get_benefits_list() -> List[Dict[str, Any]]:
    return _get_collection('benefits')


def get_agreements_list() -> List[Dict[str, Any]]:
    return _get_collection('agreements')


def get_convictions_list() -> List[Dict[str, Any]]:
    return _get_collection('convictions')


def get_protocols_list() -> List[Dict[str, Any]]:
    """Obtém lista de protocolos independentes do Firestore."""
    return _get_collection('protocols')


def validate_case_process_integrity() -> Dict[str, Any]:
    """
    Valida integridade das referências entre casos e processos.
    
    Returns:
        Dicionário com estatísticas de validação e problemas encontrados
    """
    try:
        db = get_db()
        cases = get_cases_list()
        processes = get_processes_list()
        
        cases_by_slug = {case.get('slug'): case for case in cases if case.get('slug')}
        processes_by_id = {p.get('_id'): p for p in processes if p.get('_id')}
        
        issues = {
            'orphan_process_references': [],  # Processos referenciando casos inexistentes
            'orphan_case_references': [],    # Casos referenciando processos inexistentes
            'missing_case_ids': [],          # Processos sem campo case_ids
        }
        
        # Valida processos
        for process in processes:
            process_id = process.get('_id')
            process_title = process.get('title', 'Sem título')
            case_ids = process.get('case_ids', [])
            
            if not case_ids:
                if process.get('cases'):  # Tem casos antigos mas não tem case_ids
                    issues['missing_case_ids'].append({
                        'process_id': process_id,
                        'process_title': process_title
                    })
            
            # Verifica se case_ids referenciam casos existentes
            for case_slug in case_ids:
                if case_slug not in cases_by_slug:
                    issues['orphan_process_references'].append({
                        'process_id': process_id,
                        'process_title': process_title,
                        'case_slug': case_slug
                    })
        
        # Valida casos
        for case in cases:
            case_slug = case.get('slug')
            case_title = case.get('title', 'Sem título')
            process_ids = case.get('process_ids', [])
            
            for process_id in process_ids:
                if process_id not in processes_by_id:
                    issues['orphan_case_references'].append({
                        'case_slug': case_slug,
                        'case_title': case_title,
                        'process_id': process_id
                    })
        
        stats = {
            'total_cases': len(cases),
            'total_processes': len(processes),
            'issues_found': sum(len(v) for v in issues.values()),
            'issues': issues
        }
        
        if stats['issues_found'] > 0:
            print(f"⚠️  Validação encontrou {stats['issues_found']} problema(s):")
            if issues['orphan_process_references']:
                print(f"  - {len(issues['orphan_process_references'])} referências a casos inexistentes")
            if issues['orphan_case_references']:
                print(f"  - {len(issues['orphan_case_references'])} referências a processos inexistentes")
            if issues['missing_case_ids']:
                print(f"  - {len(issues['missing_case_ids'])} processos sem campo case_ids")
        else:
            print("✅ Validação de integridade: sem problemas encontrados")
        
        return stats
        
    except Exception as e:
        print(f"❌ Erro ao validar integridade: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def get_processes_paged(
    page_size: int = 10,
    last_doc: Any = None,
    search_term: Optional[str] = None,
    status: Optional[str] = None,
    client: Optional[str] = None,
    case: Optional[str] = None,
    area: Optional[str] = None
) -> (List[Dict[str, Any]], Any):
    """
    Obtém uma página de processos do Firestore com filtros e paginação.
    
    ESTRUTURA: Suporta filtro por case (slug ou título para compatibilidade).
    """
    db = get_db()
    query = db.collection('processes')

    # Filtra processos deletados (soft delete)
    # Firestore não suporta != diretamente, então filtramos depois
    # Mas podemos usar where('isDeleted', '==', False) ou None
    # Para evitar problemas, vamos filtrar depois da query
    
    # Aplica filtros
    if search_term:
        # Este é um filtro simples de "começa com".
        # Para buscas mais complexas, seria necessário um serviço de busca como o Algolia ou ElasticSearch.
        query = query.where('title_searchable', '>=', search_term.lower()).where('title_searchable', '<=', search_term.lower() + '\uf8ff')
    if status:
        query = query.where('status', '==', status)
    if client:
        query = query.where('client', '==', client)
    if case:
        # Tenta primeiro por case_ids (slug), depois por cases (título) para compatibilidade
        try:
            query = query.where('case_ids', 'array_contains', case)
        except:
            query = query.where('cases', 'array_contains', case)
    if area:
        query = query.where('area_direito', '==', area)
    
    # Ordena para garantir paginação consistente
    query = query.order_by('title_searchable')

    # Paginação
    if last_doc:
        query = query.start_after(last_doc)
    
    query = query.limit(page_size)

    try:
        docs = list(query.stream())
        processes = []
        
        # Mapeamento de cores por área
        PROCESS_AREA_COLORS = {
            'Administrativo': '#6b7280',      # gray
            'Criminal': '#dc2626',            # red
            'Civil': '#2563eb',               # blue
            'Tributário': '#7c3aed',          # purple
            'Técnicos/projetos': '#22c55e'    # light green
        }
        
        for doc in docs:
            process = doc.to_dict()
            process['_id'] = doc.id
            
            # Filtra processos deletados (soft delete)
            if process.get('isDeleted') is True:
                continue
            
            # Adiciona cor da área
            area = process.get('area_direito') or process.get('area', '')
            process['area_direito'] = area
            process['area_color'] = PROCESS_AREA_COLORS.get(area, '#6b7280')
            
            # Enriquece com nome do cliente (se tiver client_id)
            client_id = process.get('cliente_id') or process.get('client_id')
            if client_id and not process.get('client'):
                client_name = get_client_name_by_id(client_id)
                if client_name:
                    process['client'] = client_name
            
            # Enriquece com títulos dos casos vinculados
            case_ids = process.get('case_ids', []) or []
            case_titles = []
            if case_ids:
                for slug in case_ids:
                    title = get_case_title_by_slug(slug)
                    if title:
                        case_titles.append(title)
            else:
                # Fallback para campo antigo 'cases'
                legacy_cases = process.get('cases', []) or []
                case_titles.extend(legacy_cases)
                # tenta mapear para slugs se possível
                if legacy_cases and not process.get('case_ids'):
                    from .core import get_cases_list  # avoid circular import? (can't)
            
            # Mantém compatibilidade com campos antigos
            process['case_titles'] = case_titles
            process['case_slugs'] = case_ids  # Adiciona slugs para navegação
            if not process.get('case_title'):
                process['case_title'] = case_titles[0] if case_titles else ''
            
            # Enriquece com parte contrária (herda do caso se não tiver)
            if not process.get('parte_contraria') or process.get('parte_contraria') == '-':
                if case_ids:
                    # Busca parte contrária do primeiro caso vinculado
                    first_case_slug = case_ids[0]
                    case_data = get_case_by_slug(first_case_slug)
                    if case_data:
                        process['parte_contraria'] = case_data.get('parte_contraria', '-')
            
            processes.append(process)
        
        # O último documento da página atual para usar como cursor na próxima
        new_last_doc = docs[-1] if docs else None
        
        return processes, new_last_doc

    except Exception as e:
        print(f"Erro ao buscar processos paginados: {e}")
        return [], None


def get_processes_by_case(case_slug: str = None, case_title: str = None) -> List[Dict[str, Any]]:
    """
    Busca todos os processos vinculados a um caso específico diretamente do Firestore.
    Esta função ignora o cache para garantir dados sempre atualizados.
    
    ESTRUTURA: Usa 'case_ids' (array de slugs) como fonte da verdade.
    
    Args:
        case_slug: Slug do caso (preferencial, mais confiável)
        case_title: Título do caso (para compatibilidade, se slug não fornecido)
        
    Returns:
        Lista de processos vinculados ao caso
    """
    if not case_slug and not case_title:
        return []
    
    try:
        db = get_db()
        
        # Se slug fornecido, usa case_ids (fonte da verdade)
        if case_slug:
            query = db.collection('processes').where('case_ids', 'array_contains', case_slug)
        else:
            # Fallback: usa campo 'cases' (títulos) para compatibilidade
            query = db.collection('processes').where('cases', 'array_contains', case_title)
        
        docs = query.stream()
        
        processes = []
        for doc in docs:
            process = doc.to_dict()
            process['_id'] = doc.id
            processes.append(process)
        
        return processes
    except Exception as e:
        print(f"Erro ao buscar processos do caso (slug: {case_slug}, título: {case_title}): {e}")
        import traceback
        traceback.print_exc()
        return []



# Variáveis de compatibilidade (para código que ainda usa as listas diretamente)
# NOTA: Estas são funções que retornam as listas dinamicamente
def cases_list():
    return get_cases_list()


def processes_list():
    return get_processes_list()


def clients_list():
    return get_clients_list()


# Classe para listas mutáveis que sincronizam com Firestore
class _FirestoreList:
    """Lista mutável que sincroniza automaticamente com Firestore."""
    def __init__(self, collection_name: str, get_func, save_func=None):
        self._collection_name = collection_name
        self._get_func = get_func
        self._save_func = save_func
        self._items = None
        self._dirty = False
    
    def _load(self):
        """Carrega itens do Firestore."""
        if self._items is None or self._dirty:
            self._items = self._get_func()
            self._dirty = False
        return self._items
    
    def _save_item(self, item: Dict[str, Any]):
        """Salva um item individual no Firestore."""
        if self._save_func:
            self._save_func(item)
        else:
            # Salva genérico
            doc_id = item.get('slug') or item.get('title') or item.get('name') or item.get('email') or item.get('id')
            if doc_id:
                doc_id = str(doc_id).replace('/', '-').replace(' ', '-').replace('@', '-').replace('.', '-').lower()[:100]
                _save_to_collection(self._collection_name, item, doc_id)
        invalidate_cache(self._collection_name)
        self._dirty = True
    
    def _delete_item(self, item: Dict[str, Any]):
        """Remove um item do Firestore."""
        doc_id = item.get('_id') or item.get('slug') or item.get('title') or item.get('name') or item.get('email') or item.get('id')
        if doc_id:
            doc_id = str(doc_id).replace('/', '-').replace(' ', '-').replace('@', '-').replace('.', '-').lower()[:100]
            _delete_from_collection(self._collection_name, doc_id)
        invalidate_cache(self._collection_name)
        self._dirty = True
    
    def __iter__(self):
        return iter(self._load())
    
    def __len__(self):
        return len(self._load())
    
    def __getitem__(self, key):
        return self._load()[key]
    
    def __setitem__(self, key, value):
        items = self._load()
        items[key] = value
        self._save_item(value)
    
    def __delitem__(self, key):
        items = self._load()
        item = items[key]
        del items[key]
        self._delete_item(item)
    
    def append(self, item):
        items = self._load()
        items.append(item)
        self._save_item(item)
    
    def remove(self, item):
        items = self._load()
        items.remove(item)
        self._delete_item(item)
    
    def pop(self, index=-1):
        items = self._load()
        item = items.pop(index)
        self._delete_item(item)
        return item
    
    def extend(self, iterable):
        items = self._load()
        items.extend(iterable)
        for item in iterable:
            self._save_item(item)
    
    def insert(self, index, item):
        items = self._load()
        items.insert(index, item)
        self._save_item(item)
    
    def clear(self):
        items = self._load()
        for item in items:
            self._delete_item(item)
        items.clear()
    
    def copy(self):
        return self._load().copy()
    
    def index(self, item):
        return self._load().index(item)
    
    def count(self, item):
        return self._load().count(item)


# Wrapper para compatibilidade: permite usar listas sem parênteses
class _ListWrapper:
    """Wrapper que permite acessar listas como propriedades."""
    def __getattr__(self, name):
        if name == 'cases_list':
            return _FirestoreList('cases', get_cases_list, save_case)
        elif name == 'processes_list':
            return _FirestoreList('processes', get_processes_list, save_process)
        elif name == 'clients_list':
            return _FirestoreList('clients', get_clients_list, save_client)
        elif name == 'opposing_parties_list':
            return _FirestoreList('opposing_parties', get_opposing_parties_list)
        elif name == 'users_list':
            return _FirestoreList('users', get_users_list, save_user)
        elif name == 'benefits_list':
            return _FirestoreList('benefits', get_benefits_list)
        elif name == 'agreements_list':
            return _FirestoreList('agreements', get_agreements_list)
        elif name == 'convictions_list':
            return _FirestoreList('convictions', get_convictions_list)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# Instância global para compatibilidade
_wrapper = _ListWrapper()


# Objeto data para compatibilidade (comporta-se como dicionário)
class _DataDict:
    """Dicionário compatível que retorna listas dinamicamente."""
    def __getitem__(self, key):
        if key == 'cases':
            return get_cases_list()
        elif key == 'processes':
            return get_processes_list()
        elif key == 'clients':
            return get_clients_list()
        elif key == 'opposing_parties':
            return get_opposing_parties_list()
        elif key == 'users':
            return get_users_list()
        elif key == 'benefits':
            return get_benefits_list()
        elif key == 'agreements':
            return get_agreements_list()
        elif key == 'convictions':
            return get_convictions_list()
        raise KeyError(key)
    
    def __setitem__(self, key, value):
        # Para compatibilidade, permite definir mas não persiste (já está no Firestore)
        pass
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


# Instância global de data
data = _DataDict()


def __getattr__(name):
    """Permite acessar listas como variáveis do módulo."""
    valid_names = ['cases_list', 'processes_list', 'clients_list', 'opposing_parties_list', 
                   'users_list', 'benefits_list', 'agreements_list', 'convictions_list']
    if name in valid_names:
        return getattr(_wrapper, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# ============================================================================
# ESTRUTURA DE DADOS PADRONIZADA - CASO ↔ PROCESSOS
# ============================================================================
# 
# FONTE DA VERDADE: Processos
# - Campo 'case_ids': array de slugs dos casos vinculados (obrigatório)
# - Campo 'cases': array de títulos dos casos (derivado, para compatibilidade)
#
# DERIVADO: Casos
# - Campo 'process_ids': array de _id dos processos vinculados (sincronizado)
# - Campo 'processes': array de títulos dos processos (derivado, para compatibilidade)
#
# REGRAS:
# 1. Processos são a fonte da verdade - case_ids define os vínculos
# 2. Casos têm process_ids derivados (sincronizados automaticamente)
# 3. Títulos são mantidos para compatibilidade e buscas
# 4. Validações garantem que IDs referenciem documentos existentes
# ============================================================================

def sync_processes_cases():
    """
    Sincroniza bidirecionalmente processos e casos no Firestore usando IDs.
    
    ESTRUTURA:
    - Processos têm 'case_ids' (array de slugs) - FONTE DA VERDADE
    - Casos têm 'process_ids' (array de _id) - DERIVADO
    
    Garante:
    - Cada caso tenha 'process_ids' atualizado baseado nos processos que o referenciam
    - Cada processo tenha 'cases' (títulos) atualizado baseado em 'case_ids'
    - Referências órfãs são limpas automaticamente
    """
    try:
        db = get_db()
        cases = get_cases_list()
        processes = get_processes_list()
        
        # Cria mapa de casos por slug para validação rápida
        cases_by_slug = {case.get('slug'): case for case in cases if case.get('slug')}
        cases_by_title = {case.get('title'): case for case in cases if case.get('title')}
        
        # Cria mapa de processos por _id para validação rápida
        processes_by_id = {p.get('_id'): p for p in processes if p.get('_id')}
        
        # Passo 1: Limpa e reconstrói process_ids em cada caso
        for case in cases:
            case_slug = case.get('slug')
            case_title = case.get('title')
            
            if not case_slug:
                continue
            
            # Limpa referências antigas (em memória apenas)
            new_process_ids = []
            new_processes = []  # Títulos para compatibilidade
            
            # Reconstrói baseado nos processos
            for process in processes:
                process_id = process.get('_id')
                process_title = process.get('title')
                
                if not process_id or not process_title:
                    continue
                
                # Verifica se processo referencia este caso
                process_case_ids = process.get('case_ids', [])
                
                # Compatibilidade: também verifica campo 'cases' (títulos) antigo
                process_cases_old = process.get('cases', [])
                
                # Se caso está referenciado (por ID ou título antigo)
                if case_slug in process_case_ids or case_title in process_cases_old:
                    # Adiciona ID do processo ao caso
                    if process_id not in new_process_ids:
                        new_process_ids.append(process_id)
                    
                    # Adiciona título para compatibilidade
                    if process_title not in new_processes:
                        new_processes.append(process_title)
            
            # CRÍTICO: Só salva se houve mudança real (evita salvamentos desnecessários)
            current_process_ids = set(case.get('process_ids', []))
            new_process_ids_set = set(new_process_ids)
            current_processes = set(case.get('processes', []))
            new_processes_set = set(new_processes)
            
            if current_process_ids != new_process_ids_set or current_processes != new_processes_set:
                case['process_ids'] = new_process_ids
                case['processes'] = new_processes
                # Salva caso atualizado apenas se houve mudança
                save_case(case)
        
        # Passo 2: Atualiza 'cases' (títulos) em cada processo baseado em 'case_ids'
        for process in processes:
            process_id = process.get('_id')
            process_case_ids = process.get('case_ids', [])
            
            if not process_id:
                continue
            
            # Reconstrói array de títulos baseado em case_ids
            process_cases_titles = []
            valid_case_ids = []
            
            for case_slug in process_case_ids:
                case = cases_by_slug.get(case_slug)
                if case:
                    case_title = case.get('title')
                    if case_title and case_title not in process_cases_titles:
                        process_cases_titles.append(case_title)
                    valid_case_ids.append(case_slug)
                else:
                    # Caso não existe mais - remove referência órfã
                    print(f"⚠️  Processo '{process.get('title', process_id)}' referencia caso inexistente: {case_slug}")
            
            # Atualiza processo apenas se houver mudanças
            needs_update = False
            if set(process.get('cases', [])) != set(process_cases_titles):
                process['cases'] = process_cases_titles
                needs_update = True
            
            if set(process.get('case_ids', [])) != set(valid_case_ids):
                process['case_ids'] = valid_case_ids
                needs_update = True
            
            if needs_update:
                save_process(process, doc_id=process_id)
        
        # Invalida cache
        invalidate_cache('cases')
        invalidate_cache('processes')
        
        print("✅ Sincronização processos ↔ casos concluída")
        
    except Exception as e:
        print(f"❌ Erro ao sincronizar processos e casos: {e}")
        import traceback
        traceback.print_exc()


# Funções de salvamento
def save_case(case: Dict[str, Any]):
    """Salva um caso no Firestore."""
    doc_id = case.get('slug') or slugify(case.get('title', ''))
    _save_to_collection('cases', case, doc_id)


def update_case(case_id: str, data: Dict[str, Any]):
    """
    Atualiza um caso existente no Firestore.
    
    Esta função complementa save_case() que é usada para novos casos.
    
    Args:
        case_id: ID do documento do caso no Firebase (geralmente o slug)
        data: Dicionário com os dados atualizados do caso
    
    Exemplo:
        update_case('caso-123', {'title': 'Novo Título', 'status': 'Concluído'})
    """
    # Remove _id dos dados para evitar conflitos
    data_clean = {k: v for k, v in data.items() if k != '_id'}
    
    # Atualiza o documento no Firestore usando merge=True para preservar campos não mencionados
    db = get_db()
    db.collection('cases').document(case_id).set(data_clean, merge=True)
    
    # Invalida cache para forçar reload
    invalidate_cache('cases')



def get_case_state_by_slug(case_slug: str) -> Optional[str]:
    """
    Retorna o estado (UF) de um caso dado seu slug.
    Útil para herança de estado em processos.
    
    Args:
        case_slug: Slug do caso
    
    Returns:
        Estado do caso ou None se não encontrado/não definido
    """
    try:
        db = get_db()
        case_doc = db.collection('cases').document(case_slug).get()
        if case_doc.exists:
            case_data = case_doc.to_dict()
            return case_data.get('state')
        return None
    except Exception as e:
        print(f"⚠️  Erro ao obter estado do caso {case_slug}: {e}")
        return None


def save_process(process: Dict[str, Any], doc_id: str = None, sync: bool = False):
    """
    Salva um processo no Firestore.
    
    ESTRUTURA:
    - Garante que 'case_ids' (array de slugs) seja mantido
    - Atualiza 'cases' (títulos) baseado em 'case_ids' para compatibilidade
    - Herda automaticamente o 'state' do primeiro caso vinculado
    
    Args:
        process: Dicionário com os dados do processo
        doc_id: ID do documento (opcional). Se não fornecido, será gerado a partir do título
        sync: Se True, sincroniza referências casos-processos após salvar (default: False para performance)
    
    NOTA: A sincronização foi removida por padrão para melhorar performance.
    Chame sync_processes_cases() manualmente se precisar atualizar referências bidirecionais.
    """
    if not doc_id:
        doc_id = process.get('title', '').replace('/', '-').replace(' ', '-').lower()[:100]
    
    # Adiciona campo de busca em minúsculas
    if 'title' in process:
        process['title_searchable'] = process['title'].lower()
    
    # Se case_ids não existe mas cases (títulos) existe, converte títulos para slugs
    db = get_db()
    if 'case_ids' not in process or not process.get('case_ids'):
        if process.get('cases'):
            # Converte títulos para slugs
            case_ids = []
            for case_title in process['cases']:
                # Busca caso pelo título
                cases_query = db.collection('cases').where('title', '==', case_title).limit(1).stream()
                for doc in cases_query:
                    case_ids.append(doc.id)
                    break
            process['case_ids'] = case_ids
        else:
            process['case_ids'] = []
    
    # Valida e atualiza 'cases' (títulos) baseado em 'case_ids'
    # Também herda o estado do primeiro caso vinculado
    if process.get('case_ids'):
        cases_by_slug = {}
        inherited_state = None
        
        for idx, case_slug in enumerate(process['case_ids']):
            try:
                case_doc = db.collection('cases').document(case_slug).get()
                if case_doc.exists:
                    case_data = case_doc.to_dict()
                    cases_by_slug[case_slug] = case_data.get('title')
                    
                    # Herda estado do primeiro caso vinculado
                    if idx == 0 and case_data.get('state'):
                        inherited_state = case_data.get('state')
            except Exception as e:
                print(f"⚠️  Erro ao validar caso {case_slug}: {e}")
        
        # Atualiza array de títulos
        process['cases'] = [cases_by_slug[slug] for slug in process['case_ids'] if cases_by_slug.get(slug)]
        
        # Herda estado do caso (apenas se caso tiver estado definido)
        if inherited_state:
            process['state'] = inherited_state
        elif 'state' not in process:
            # Se não herdar estado e processo não tiver, define como None
            process['state'] = None
    else:
        process['cases'] = []
        # Se não há casos vinculados, não herda estado
        if 'state' not in process:
            process['state'] = None
    
    # Hierarquia de processos - Suporte para múltiplos processos pai
    # Migração: parent_id (antigo) → parent_ids (novo)
    parent_ids = process.get('parent_ids', [])
    
    # Compatibilidade: se tem parent_id antigo mas não tem parent_ids, migra
    old_parent_id = process.get('parent_id')
    if old_parent_id and not parent_ids:
        parent_ids = [old_parent_id]
        process['parent_ids'] = parent_ids
    
    # Garantir que parent_ids é uma lista
    if not isinstance(parent_ids, list):
        parent_ids = [parent_ids] if parent_ids else []
        process['parent_ids'] = parent_ids
    
    # Remover valores None ou vazios
    parent_ids = [pid for pid in parent_ids if pid]
    process['parent_ids'] = parent_ids
    
    # Calcular depth baseado no maior depth dos processos pai
    if not parent_ids:
        # Processo raiz
        process['depth'] = 0
        # Mantém compatibilidade com campo antigo
        process['parent_id'] = None
    else:
        # Processo com pais - calcula depth baseado no maior depth dos pais
        max_parent_depth = -1
        for parent_id in parent_ids:
            try:
                parent_doc = db.collection('processes').document(parent_id).get()
                if parent_doc.exists:
                    parent_data = parent_doc.to_dict()
                    parent_depth = parent_data.get('depth', 0) or 0
                    max_parent_depth = max(max_parent_depth, parent_depth)
                else:
                    print(f"[WARN] Processo pai {parent_id} não encontrado")
            except Exception as e:
                print(f"[WARN] Erro ao buscar processo pai {parent_id}: {e}")
        
        # Depth = maior depth dos pais + 1
        process['depth'] = max_parent_depth + 1 if max_parent_depth >= 0 else 1
        
        # Compatibilidade: mantém parent_id com o primeiro pai (para funções legadas)
        process['parent_id'] = parent_ids[0] if parent_ids else None
    
    # Salva processo
    _save_to_collection('processes', process, doc_id)
    
    # Sincroniza referências nos casos apenas se solicitado
    if sync:
        sync_processes_cases()


def save_client(
    client: Dict[str, Any] = None,
    *,
    full_name: str = None,
    cpf_cnpj: str = None,
    display_name: str = None,
    nickname: str = None,
    client_type: str = None,
    cpf: str = None,
    cnpj: str = None,
):
    """
    Salva um cliente no Firestore.
    
    Pode ser chamada de duas formas:
    1. save_client(dict_cliente) - compatibilidade com código existente
    2. save_client(full_name="...", cpf_cnpj="...", ...) - nova API
    
    Schema:
    - full_name: string (obrigatório)
    - display_name: string (opcional)
    - nickname: string (opcional)
    - client_type: "PF", "PJ" ou "PF/PJ"
    - cpf/cnpj: armazenados separados e exibidos em cpf_cnpj para compatibilidade
    - created_at: SERVER_TIMESTAMP
    - updated_at: SERVER_TIMESTAMP
    
    Compatibilidade: campos antigos (name, document) são migrados automaticamente.
    """
    from google.cloud.firestore import SERVER_TIMESTAMP
    
    # Suporte para nova API com parâmetros nomeados
    if client is None:
        if not full_name:
            raise ValueError("full_name é obrigatório")
        if not any([cpf, cnpj, cpf_cnpj]):
            raise ValueError("Informe ao menos um documento (cpf ou cnpj)")
        client = {
            'full_name': full_name,
            'display_name': display_name or '',
            'nickname': nickname or '',
        }
        if cpf_cnpj:
            client['cpf_cnpj'] = cpf_cnpj
        if cpf:
            client['cpf'] = cpf
        if cnpj:
            client['cnpj'] = cnpj
        if client_type:
            client['client_type'] = client_type
    
    # Migração de campos antigos para novo schema
    if 'name' in client and 'full_name' not in client:
        client['full_name'] = client.get('name', '')
    if 'document' in client and 'cpf_cnpj' not in client:
        client['cpf_cnpj'] = client.get('document', '')
    
    client = normalize_client_documents(client)
    
    # Garante que nome_exibicao seja preenchido (obrigatório)
    if not client.get('nome_exibicao', '').strip():
        # Se nome_exibicao vazio, usa display_name ou full_name como fallback
        client['nome_exibicao'] = (
            client.get('display_name', '').strip() or 
            client.get('full_name', '').strip() or 
            client.get('name', '').strip() or 
            'Sem nome'
        )
    
    # Mantém display_name sincronizado para compatibilidade
    if not client.get('display_name', '').strip():
        client['display_name'] = client['nome_exibicao']
    
    # Mantém campos antigos para compatibilidade (podem ser removidos futuramente)
    if 'full_name' in client:
        client['name'] = client['full_name']
    if 'cpf_cnpj' in client:
        client['document'] = client['cpf_cnpj']
    
    # Timestamps usando SERVER_TIMESTAMP do Firestore
    if 'created_at' not in client or client.get('created_at') is None:
        client['created_at'] = SERVER_TIMESTAMP
    client['updated_at'] = SERVER_TIMESTAMP
    
    # Usa _id se existir, senão gera do nome
    doc_id = client.get('_id') or client.get('full_name', client.get('name', '')).replace('/', '-').replace(' ', '-').lower()[:100]
    _save_to_collection('clients', client, doc_id)
    
    # Invalida cache de nome de exibição
    invalidate_display_name_cache(doc_id)


def delete_client(client: Dict[str, Any]):
    """Remove um cliente do Firestore."""
    doc_id = client.get('_id') or client.get('name', '').replace('/', '-').replace(' ', '-').lower()[:100]
    _delete_from_collection('clients', doc_id)
    
    # Invalida cache de nome de exibição
    invalidate_display_name_cache(doc_id)


def save_opposing_party(opposing: Dict[str, Any] = None, *, full_name: str = None, cpf_cnpj: str = None,
                        entity_type: str = None, display_name: str = None, nickname: str = None):
    """
    Salva um outro envolvido no Firestore.
    
    Pode ser chamada de duas formas:
    1. save_opposing_party(dict_opposing) - compatibilidade com código existente
    2. save_opposing_party(full_name="...", cpf_cnpj="...", entity_type="PF", ...) - nova API
    
    Schema:
    - full_name: string (obrigatório)
    - display_name: string (opcional)
    - nickname: string (opcional)
    - cpf_cnpj: string (obrigatório)
    - entity_type: string (obrigatório, um de: "PF", "PJ", "Órgão Público")
    - created_at: SERVER_TIMESTAMP
    - updated_at: SERVER_TIMESTAMP
    
    Compatibilidade: campos antigos (name, document) são migrados automaticamente.
    """
    from google.cloud.firestore import SERVER_TIMESTAMP
    
    # Suporte para nova API com parâmetros nomeados
    if opposing is None:
        if not full_name or not cpf_cnpj:
            raise ValueError("full_name e cpf_cnpj são obrigatórios")
        opposing = {
            'full_name': full_name,
            'cpf_cnpj': cpf_cnpj,
            'entity_type': entity_type or 'PF',
            'display_name': display_name or '',
            'nickname': nickname or '',
        }
    
    # Migração de campos antigos para novo schema
    if 'name' in opposing and 'full_name' not in opposing:
        opposing['full_name'] = opposing.get('name', '')
    if 'document' in opposing and 'cpf_cnpj' not in opposing:
        opposing['cpf_cnpj'] = opposing.get('document', '')
    
    # Mantém campos antigos para compatibilidade
    if 'full_name' in opposing:
        opposing['name'] = opposing['full_name']
    if 'cpf_cnpj' in opposing:
        opposing['document'] = opposing['cpf_cnpj']
    
    # Entity type default se não informado
    if 'entity_type' not in opposing:
        opposing['entity_type'] = 'PF'
    
    opposing['entity_type'] = normalize_entity_type_value(opposing.get('entity_type'))
    
    # Garante que nome_exibicao seja preenchido (obrigatório)
    if not opposing.get('nome_exibicao', '').strip():
        # Se nome_exibicao vazio, usa display_name ou full_name como fallback
        opposing['nome_exibicao'] = (
            opposing.get('display_name', '').strip() or 
            opposing.get('full_name', '').strip() or 
            opposing.get('name', '').strip() or 
            'Sem nome'
        )
    
    # Mantém display_name sincronizado para compatibilidade
    if not opposing.get('display_name', '').strip():
        opposing['display_name'] = opposing['nome_exibicao']
    
    # Timestamps usando SERVER_TIMESTAMP do Firestore
    if 'created_at' not in opposing or opposing.get('created_at') is None:
        opposing['created_at'] = SERVER_TIMESTAMP
    opposing['updated_at'] = SERVER_TIMESTAMP
    
    # Usa _id se existir, senão gera do nome
    doc_id = opposing.get('_id') or opposing.get('full_name', opposing.get('name', '')).replace('/', '-').replace(' ', '-').lower()[:100]
    _save_to_collection('opposing_parties', opposing, doc_id)
    
    # Invalida cache de nome de exibição
    invalidate_display_name_cache(doc_id)


def delete_opposing_party(opposing: Dict[str, Any]):
    """Remove um outro envolvido do Firestore."""
    doc_id = opposing.get('_id') or opposing.get('name', '').replace('/', '-').replace(' ', '-').lower()[:100]
    _delete_from_collection('opposing_parties', doc_id)
    
    # Invalida cache de nome de exibição
    invalidate_display_name_cache(doc_id)


# =============================================================================
# FUNÇÕES DE LEADS
# =============================================================================

def get_leads_list() -> List[Dict[str, Any]]:
    """
    Obtém lista de leads do Firestore.
    Filtra pela coleção 'pessoas' onde tipo_pessoa == 'lead'.
    Usa cache para otimizar performance.
    """
    import time
    
    cache_key = 'pessoas_leads'
    now = time.time()
    
    # Verifica cache sem lock (leitura rápida)
    if cache_key in _cache and cache_key in _cache_timestamp:
        if now - _cache_timestamp[cache_key] < CACHE_DURATION:
            return _cache[cache_key]
    
    # Usa lock para evitar múltiplas consultas simultâneas ao Firestore
    with _cache_lock:
        # Verifica novamente dentro do lock
        if cache_key in _cache and cache_key in _cache_timestamp:
            if now - _cache_timestamp[cache_key] < CACHE_DURATION:
                return _cache[cache_key]
        
        try:
            db = get_db()
            query = db.collection('pessoas').where('tipo_pessoa', '==', 'lead')
            docs = query.stream()
            leads = []
            for doc in docs:
                lead = doc.to_dict()
                lead['_id'] = doc.id
                leads.append(lead)
            
            # Atualiza cache
            _cache[cache_key] = leads
            _cache_timestamp[cache_key] = time.time()
            
            return leads
        except Exception as e:
            print(f"Erro ao buscar leads: {e}")
            # Retorna cache antigo se houver erro
            return _cache.get(cache_key, [])


def save_lead(lead: Dict[str, Any] = None, *, full_name: str = None, email: str = None,
              telefone: str = None, endereco: str = None, cidade: str = None,
              estado: str = None, cep: str = None, cpf_cnpj: str = None,
              observacoes: str = None, origem: str = None):
    """
    Salva um lead no Firestore na coleção 'pessoas'.
    
    Pode ser chamada de duas formas:
    1. save_lead(dict_lead) - compatibilidade com código existente
    2. save_lead(full_name="...", email="...", ...) - nova API
    
    Schema:
    - full_name: string (obrigatório)
    - email: string (opcional)
    - telefone: string (opcional)
    - endereco: string (opcional)
    - cidade: string (opcional)
    - estado: string (opcional)
    - cep: string (opcional)
    - cpf_cnpj: string (opcional)
    - observacoes: string (opcional)
    - origem: string (opcional) - "Indicação", "Site", "Telefone", "Evento", "Redes Sociais", "Outro"
    - tipo_pessoa: string (fixo "lead")
    - status_lead: string (fixo "lead")
    - data_cadastro: SERVER_TIMESTAMP
    - created_at: SERVER_TIMESTAMP
    - updated_at: SERVER_TIMESTAMP
    """
    from google.cloud.firestore import SERVER_TIMESTAMP
    
    # Suporte para nova API com parâmetros nomeados (mantido para compatibilidade)
    if lead is None:
        if not full_name:
            raise ValueError("full_name é obrigatório")
        lead = {
            'nome': full_name,  # Usa 'nome' como campo principal
            'full_name': full_name,  # Mantém 'full_name' para compatibilidade
            'email': email or '',
            'telefone': telefone or '',
            'endereco': endereco or '',
            'cidade': cidade or '',
            'estado': estado or '',
            'cep': cep or '',
            'cpf_cnpj': cpf_cnpj or '',
            'observacoes': observacoes or '',
            'origem': origem or '',
        }
    
    # Normaliza campos de nome (suporta tanto 'nome' quanto 'full_name' para compatibilidade)
    if 'nome' in lead and not lead.get('full_name'):
        lead['full_name'] = lead['nome']
    elif 'full_name' in lead and not lead.get('nome'):
        lead['nome'] = lead['full_name']
    
    # Garante campos obrigatórios
    if not lead.get('nome') and not lead.get('full_name'):
        raise ValueError("nome é obrigatório")
    
    # Garante que ambos os campos estejam preenchidos
    if not lead.get('nome'):
        lead['nome'] = lead.get('full_name', '')
    if not lead.get('full_name'):
        lead['full_name'] = lead.get('nome', '')
    
    # Garante nome_exibicao (usa nome de exibição se fornecido, senão usa nome)
    if not lead.get('nome_exibicao', '').strip():
        lead['nome_exibicao'] = lead.get('nome', lead.get('full_name', '')).strip() or 'Sem nome'
    if not lead.get('display_name', '').strip():
        lead['display_name'] = lead['nome_exibicao']
    
    # Define campos fixos para leads
    lead['tipo_pessoa'] = 'lead'
    lead['status_lead'] = 'lead'
    
    # Timestamps usando SERVER_TIMESTAMP do Firestore
    if 'data_cadastro' not in lead or lead.get('data_cadastro') is None:
        lead['data_cadastro'] = SERVER_TIMESTAMP
    if 'created_at' not in lead or lead.get('created_at') is None:
        lead['created_at'] = SERVER_TIMESTAMP
    lead['updated_at'] = SERVER_TIMESTAMP
    
    # Usa _id se existir, senão gera do nome
    doc_id = lead.get('_id') or lead.get('nome', lead.get('full_name', '')).replace('/', '-').replace(' ', '-').lower()[:100]
    _save_to_collection('pessoas', lead, doc_id)
    
    # Invalida cache de leads
    _cache.pop('pessoas_leads', None)
    _cache_timestamp.pop('pessoas_leads', None)
    
    # Invalida cache de nome de exibição
    invalidate_display_name_cache(doc_id)


def delete_lead(lead: Dict[str, Any]):
    """Remove um lead do Firestore."""
    doc_id = lead.get('_id') or lead.get('full_name', '').replace('/', '-').replace(' ', '-').lower()[:100]
    _delete_from_collection('pessoas', doc_id)
    
    # Invalida cache de leads
    _cache.pop('pessoas_leads', None)
    _cache_timestamp.pop('pessoas_leads', None)
    
    # Invalida cache de nome de exibição
    invalidate_display_name_cache(doc_id)


# =============================================================================
# FUNÇÕES DE PROTOCOLOS INDEPENDENTES
# =============================================================================

def save_protocol(protocol: Dict[str, Any], doc_id: str = None):
    """
    Salva um protocolo independente no Firestore.
    
    Protocolos podem ser vinculados a múltiplos casos e processos.
    
    Schema:
    - title: string (título/descrição do protocolo)
    - date: string (data do protocolo)
    - number: string (número do protocolo)
    - system: string (sistema onde foi protocolado)
    - link: string (link/URL externo do protocolo)
    - observations: string (observações)
    - case_ids: array de slugs de casos vinculados
    - process_ids: array de _ids de processos vinculados
    - created_at: timestamp
    - updated_at: timestamp
    
    Args:
        protocol: Dicionário com dados do protocolo
        doc_id: ID do documento (opcional, será gerado se não fornecido)
    """
    from google.cloud.firestore import SERVER_TIMESTAMP
    
    # Garante arrays vazios se não existirem
    if 'case_ids' not in protocol:
        protocol['case_ids'] = []
    if 'process_ids' not in protocol:
        protocol['process_ids'] = []
    
    # Timestamps
    if 'created_at' not in protocol or protocol.get('created_at') is None:
        protocol['created_at'] = SERVER_TIMESTAMP
    protocol['updated_at'] = SERVER_TIMESTAMP
    
    # Gera doc_id se não fornecido
    if not doc_id:
        doc_id = protocol.get('_id')
    if not doc_id:
        # Gera ID único baseado em timestamp e título
        import time
        timestamp = int(time.time() * 1000)
        title_slug = (protocol.get('title', '') or 'protocolo').replace('/', '-').replace(' ', '-').lower()[:50]
        doc_id = f"{title_slug}-{timestamp}"
    
    _save_to_collection('protocols', protocol, doc_id)
    
    # Invalida cache
    invalidate_cache('protocols')


def delete_protocol(doc_id: str):
    """
    Remove um protocolo do Firestore.
    
    Args:
        doc_id: ID do documento do protocolo
    """
    _delete_from_collection('protocols', doc_id)
    invalidate_cache('protocols')


def get_protocols_by_process(process_id: str) -> List[Dict[str, Any]]:
    """
    Busca todos os protocolos vinculados a um processo específico.
    
    Args:
        process_id: _id do processo no Firestore
    
    Returns:
        Lista de protocolos vinculados ao processo
    """
    if not process_id:
        return []
    
    try:
        db = get_db()
        query = db.collection('protocols').where('process_ids', 'array_contains', process_id)
        docs = query.stream()
        
        protocols = []
        for doc in docs:
            protocol = doc.to_dict()
            protocol['_id'] = doc.id
            protocols.append(protocol)
        
        return protocols
    except Exception as e:
        print(f"Erro ao buscar protocolos do processo {process_id}: {e}")
        return []


def get_protocols_by_case(case_slug: str) -> List[Dict[str, Any]]:
    """
    Busca todos os protocolos vinculados a um caso específico.
    
    Args:
        case_slug: Slug do caso
    
    Returns:
        Lista de protocolos vinculados ao caso
    """
    if not case_slug:
        return []
    
    try:
        db = get_db()
        query = db.collection('protocols').where('case_ids', 'array_contains', case_slug)
        docs = query.stream()
        
        protocols = []
        for doc in docs:
            protocol = doc.to_dict()
            protocol['_id'] = doc.id
            protocols.append(protocol)
        
        return protocols
    except Exception as e:
        print(f"Erro ao buscar protocolos do caso {case_slug}: {e}")
        return []


def save_user(user: Dict[str, Any]):
    """Salva um usuário no Firestore."""
    doc_id = user.get('email', '').replace('@', '-').replace('.', '-').lower()[:100]
    _save_to_collection('users', user, doc_id)


def delete_case(slug: str, sync: bool = False):
    """
    Remove um caso do Firestore e limpa referências nos processos.
    
    ESTRUTURA:
    - Remove caso do Firestore
    - Remove slug do caso de todos os processos que o referenciam (case_ids)
    
    Args:
        slug: Slug do caso a ser removido
        sync: Se True, sincroniza referências casos-processos após deletar (default: False)
    """
    # Remove referências do caso em todos os processos
    try:
        db = get_db()
        processes = db.collection('processes').where('case_ids', 'array_contains', slug).stream()
        
        for process_doc in processes:
            process_data = process_doc.to_dict()
            case_ids = process_data.get('case_ids', [])
            
            if slug in case_ids:
                case_ids.remove(slug)
                # Remove também do array de títulos
                cases_titles = process_data.get('cases', [])
                db.collection('processes').document(process_doc.id).update({
                    'case_ids': case_ids,
                    'cases': [t for t in cases_titles if t]  # limpa títulos órfãos
                })
        
        # Remove caso
        _delete_from_collection('cases', slug)
        
        # Sincroniza apenas se solicitado
        if sync:
            sync_processes_cases()
    except Exception as e:
        print(f"⚠️  Erro ao remover referências do caso {slug}: {e}")
        # Remove caso mesmo se houver erro na limpeza
        _delete_from_collection('cases', slug)


def delete_process(doc_id: str, sync: bool = False):
    """
    Remove um processo do Firestore.
    
    ESTRUTURA:
    - Remove processo do Firestore
    
    Args:
        doc_id: ID do documento do processo (pode ser o título ou o _id do documento)
        sync: Se True, sincroniza referências casos-processos após deletar (default: False)
    
    NOTA: A sincronização foi removida por padrão para melhorar performance.
    """
    # Se for um título (não contém caracteres especiais de ID), converte para doc_id
    if '/' in doc_id or ' ' in doc_id or doc_id != doc_id.lower():
        doc_id = doc_id.replace('/', '-').replace(' ', '-').lower()[:100]
    
    _delete_from_collection('processes', doc_id)
    
    # Sincroniza apenas se solicitado
    if sync:
        sync_processes_cases()


# Função save_data para compatibilidade (agora não faz nada, pois salvamos direto no Firestore)
def save_data():
    """Função de compatibilidade - dados já são salvos automaticamente no Firestore."""
    # Esta função é mantida para compatibilidade com código antigo.
    # A persistência agora é gerenciada pelas chamadas diretas de save/delete.
    pass


def slugify(text: str) -> str:
    """Converte texto para slug (URL-friendly)."""
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def format_date_br(date_str: Optional[str] = None) -> str:
    """Formata datas para padrão brasileiro (dd/mm/aaaa)."""
    if not date_str:
        return '-'
    if re.match(r'^\d{2}/\d{2}/\d{4}$', str(date_str)):
        return str(date_str)
    value = str(date_str)
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%d/%m/%Y')
    except Exception:
        pass
    try:
        dt = datetime.strptime(value, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return value


def preload_data():
    """Pré-carrega dados em background para melhorar performance."""
    def _load():
        try:
            get_cases_list()
            get_processes_list()
            get_clients_list()
        except Exception:
            # Em caso de falha, apenas ignore para não bloquear a inicialização
            pass
    
    thread = threading.Thread(target=_load, daemon=True)
    thread.start()


def get_route_for_workspace(base_route: str) -> str:
    """
    Retorna a rota correta baseada no workspace atual.

    Args:
        base_route: Rota base (ex: '/', '/casos', '/processos')

    Returns:
        Rota ajustada para o workspace atual
    """
    from .gerenciadores.gerenciador_workspace import obter_workspace_atual, obter_info_workspace

    workspace_id = obter_workspace_atual()
    workspace_info = obter_info_workspace(workspace_id)

    if not workspace_info:
        return base_route

    # Se for workspace do cliente (area_cliente_schmidmeier), usa rotas normais
    # NOTA: Workspace padrão agora é 'visao_geral_escritorio', mas esta verificação
    # ainda é necessária para manter compatibilidade com workspace do cliente
    if workspace_id == 'area_cliente_schmidmeier':
        return base_route

    # Se for novo workspace (visao_geral_escritorio), adiciona prefixo /visao-geral/
    if workspace_id == 'visao_geral_escritorio':
        # Trata rota raiz especial
        if base_route == '/':
            return '/visao-geral/painel'
        # Remove barra inicial se existir e adiciona prefixo
        route = base_route.lstrip('/')
        return f'/visao-geral/{route}' if route else '/visao-geral/painel'

    return base_route


def menu_item(label: str, icon: str, target: str):
    """Cria item do menu de navegação."""
    # Ajusta rota baseado no workspace atual
    adjusted_target = get_route_for_workspace(target)
    with ui.link(target=adjusted_target).classes('w-full flex flex-row flex-nowrap items-center gap-3 hover:bg-white/10 rounded transition-colors no-underline cursor-pointer').style('padding: 8px 8px 8px 12px; margin-left: 0;'):
        ui.icon(icon, size='sm').classes('text-white/80 flex-shrink-0')
        ui.label(label).classes('text-sm font-medium text-white/90 whitespace-nowrap')


def capitalize_first(text: str) -> str:
    """Garante que a primeira letra seja maiúscula."""
    if not text:
        return text
    return text[0].upper() + text[1:]


@contextmanager
def layout(page_title: str, breadcrumbs: list = None):
    """Layout comum para todas as páginas."""
    # Garante que o título sempre comece com maiúscula
    page_title = capitalize_first(page_title)
    
    ui.colors(primary=PRIMARY_COLOR)
    
    ui.add_head_html('''
        <!-- Meta tags anti-cache para corrigir hot reload -->
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
        
        <style>
            a.no-underline { text-decoration: none !important; color: inherit !important; }
            a.no-underline:hover { text-decoration: none !important; }
            /* Otimização para Vivaldi e outros navegadores */
            * {
                -webkit-tap-highlight-color: transparent;
            }
            .q-page, .q-header {
                transition: none !important;
            }
            /* Drawer mantém transição própria definida em sidebar_base.py */
            .q-tab__indicator {
                transition: none !important;
            }
            .q-ripple {
                display: none !important;
            }
            /* Desabilitar animações pesadas */
            @media (prefers-reduced-motion: reduce) {
                * {
                    animation: none !important;
                    transition: none !important;
                }
            }
        </style>
        <script>
            // Evita re-execução em navegações SPA (Single Page Application)
            // O JavaScript de reconexão deve executar apenas UMA VEZ para evitar:
            // - MutationObserver e setInterval duplicados
            // - Event listeners acumulados (memory leak)
            // - Reprocessamento desnecessário
            if (window._taques_erp_layout_initialized) {
                // Layout já inicializado, pula re-inicialização
            } else {
                window._taques_erp_layout_initialized = true;
                
                // Reconexão otimizada - mais conservador para evitar loops
                document.addEventListener('DOMContentLoaded', function() {
                    let reconnectAttempts = 0;
                    const MAX_RECONNECT_ATTEMPTS = 3;
                    const RECONNECT_DELAY = 5000; // 5 segundos
                    
                    function hideConnectionDialog() {
                        try {
                            const dialogs = document.querySelectorAll('.q-dialog, .q-banner');
                            dialogs.forEach(function(dialog) {
                                if (dialog && dialog.textContent) {
                                    if (dialog.textContent.includes('Connection lost') || dialog.textContent.includes('Trying to reconnect')) {
                                        dialog.style.display = 'none';
                                        
                                        // Só tenta reconectar se não excedeu o limite
                                        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                                            reconnectAttempts++;
                                            console.log('Tentativa de reconexão ' + reconnectAttempts + '/' + MAX_RECONNECT_ATTEMPTS);
                                            setTimeout(function() { 
                                                window.location.reload(); 
                                            }, RECONNECT_DELAY);
                                        } else {
                                            console.log('Limite de reconexões atingido. Recarregue manualmente.');
                                        }
                                    }
                                }
                            });
                        } catch (e) {
                            console.log('Reconnect check error:', e);
                        }
                    }
                    
                    // Verificação menos frequente (a cada 3 segundos)
                    setInterval(hideConnectionDialog, 3000);
                    
                    // Reconexão ao voltar online (reseta contador)
                    window.addEventListener('online', function() {
                        reconnectAttempts = 0;
                        window.location.reload();
                    });
                    
                    // Reseta contador quando página carrega com sucesso
                    window.addEventListener('load', function() {
                        reconnectAttempts = 0;
                    });
                    
                    // Carrega workspace do localStorage ao carregar página (se não estiver na sessão)
                    try {
                        const savedWorkspace = localStorage.getItem('taques_erp_workspace');
                        if (savedWorkspace) {
                            // Sincroniza com sessão NiceGUI se necessário
                            // A sessão será atualizada pelo Python quando necessário
                        }
                    } catch (e) {
                        console.log('Erro ao carregar workspace do localStorage:', e);
                    }
                });
            }
        </script>
    ''')
    
    # Header
    with ui.header().style(f'background-color: {PRIMARY_COLOR}; height: 60px; padding: 0 16px;'):
        with ui.row().style('width: 100%; align-items: center; height: 100%;'):
            # ESQUERDA - Logo/Título
            ui.label('TAQUES ERP').style('font-size: 18px; font-weight: bold; color: white;')
            
            # CENTRO - Espaço flexível
            ui.space()
            
            # DIREITA - Elementos alinhados
            with ui.row().style('align-items: center; gap: 16px; color: white;'):
                # Botão /dev - Apenas para desenvolvedores
                # Verificação direta do email do usuário logado
                user_data = app.storage.user.get('user', {})
                user_email = user_data.get('email', '').lower() if user_data else ''
                if user_email == 'taqueslenon@gmail.com':
                    ui.button(icon='code', on_click=lambda: ui.navigate.to('/dev')) \
                        .props('flat dense') \
                        .tooltip('Painel do Desenvolvedor') \
                        .style('color: white; opacity: 0.8; margin-right: 8px;')
                
                # Workspace - Dropdown de seleção
                from .componentes.dropdown_workspace import render_workspace_dropdown
                render_workspace_dropdown()
                
                # Separador
                ui.element('div').style('width: 1px; height: 20px; background-color: rgba(255,255,255,0.2);')
                
                ui.icon('notifications').style('font-size: 20px; cursor: pointer;')
                
                # Verificar cache do avatar ANTES de renderizar (evita piscar)
                from .auth import get_current_user
                avatar_cache = app.storage.user.get('avatar_cache', {})
                current_user_for_avatar = get_current_user()
                cached_url = None
                user_initials = 'U'
                
                if current_user_for_avatar:
                    uid_for_avatar = current_user_for_avatar.get('uid')
                    email_for_avatar = current_user_for_avatar.get('email', '')
                    
                    # Calcula iniciais
                    user_initials = email_for_avatar[:2].upper() if email_for_avatar else 'U'
                    
                    # Verifica se tem cache válido
                    if avatar_cache.get('uid') == uid_for_avatar and avatar_cache.get('url'):
                        cached_url = avatar_cache.get('url')
                
                with ui.button().props('flat dense').classes('p-0'):
                    with ui.avatar(color='white', text_color='primary').style('width: 40px; height: 40px;').classes('cursor-pointer font-semibold') as avatar_comp:
                        # Se tem cache válido, renderiza imagem direto (SEM PISCAR)
                        if cached_url:
                            ui.image(cached_url).classes('w-full h-full object-cover rounded-full')
                            avatar_label = None  # Não precisa de label
                        else:
                            # Sem cache - mostra iniciais e carrega depois
                            avatar_label = ui.label(user_initials).classes('text-sm font-bold')
                    
                    with ui.menu():
                        with ui.menu_item(on_click=lambda: ui.navigate.to('/configuracoes')):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('person', size='xs')
                                ui.label('Meu Perfil')
                        ui.separator()
                        with ui.menu_item(on_click=lambda: ui.navigate.to('/logout')):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('logout', size='xs')
                                ui.label('Sair')

                    # Estado para evitar múltiplas carregamentos simultâneos
                    avatar_navbar_loading = {'status': False}
                    
                    async def load_user_avatar():
                        """Carrega o avatar do usuário na navbar com cache"""
                        try:
                            if avatar_navbar_loading['status']:
                                return  # Evita múltiplas chamadas simultâneas
                            
                            # Importa get_current_user no início da função para evitar UnboundLocalError
                            from .auth import get_current_user
                            from .storage import obter_url_avatar
                            
                            # Se já tem imagem do cache aplicada na renderização inicial, não precisa fazer nada
                            avatar_cache = app.storage.user.get('avatar_cache', {})
                            user = get_current_user()
                            if user:
                                uid = user.get('uid')
                                if avatar_cache.get('uid') == uid and avatar_cache.get('url'):
                                    print("[AVATAR HEADER] Cache já aplicado na renderização inicial")
                                    return
                            
                            avatar_navbar_loading['status'] = True
                            
                            user = get_current_user()
                            if not user:
                                print("[AVATAR HEADER] Usuário não encontrado")
                                return
                                
                            # Define iniciais (usa display_name se disponível)
                            email = user.get('email', '')
                            uid = user.get('uid')
                            
                            # Atualiza iniciais se avatar_label existir (não existe se cache foi usado)
                            if avatar_label is not None:
                                # Tenta obter display_name
                                display_name = None
                                if uid:
                                    try:
                                        from .storage import obter_display_name
                                        display_name = await run.io_bound(obter_display_name, uid)
                                        # Se retornou "Usuário" (fallback), trata como None
                                        if display_name == "Usuário":
                                            display_name = None
                                    except:
                                        pass
                                
                                # Usa display_name para iniciais, senão usa email
                                if display_name and len(display_name) >= 2:
                                    # Pega primeiras 2 letras do nome
                                    initials = display_name[:2].upper()
                                    # Tooltip com nome completo
                                    avatar_label.tooltip = display_name
                                else:
                                    # Fallback: usa email
                                    initials = email[:2].upper() if email else 'U'
                                    avatar_label.tooltip = email
                                
                                avatar_label.text = initials
                            
                            # Carrega avatar do Storage
                            print(f"[AVATAR HEADER] Carregando do Storage para UID: {uid}")
                            
                            if uid:
                                url = await run.io_bound(obter_url_avatar, uid)
                                print(f"[AVATAR HEADER] URL obtida: {url}")
                                
                                if url:
                                    # Salva no cache para próximas navegações
                                    app.storage.user['avatar_cache'] = {'url': url, 'uid': uid}
                                    
                                    # Limpa o avatar e adiciona a imagem
                                    avatar_comp.clear()
                                    with avatar_comp:
                                        # Adiciona a imagem com estilo circular
                                        ui.image(url).classes('w-full h-full object-cover rounded-full')
                                    print(f"[AVATAR HEADER] Imagem aplicada e cache atualizado!")
                                else:
                                    print(f"[AVATAR HEADER] Nenhuma URL retornada, mantendo iniciais")
                        except Exception as e:
                            print(f"[AVATAR HEADER] Erro ao carregar avatar: {e}")
                            import traceback
                            traceback.print_exc()
                        finally:
                            avatar_navbar_loading['status'] = False

                    ui.timer(0.1, load_user_avatar, once=True)
                    
                    # Escuta evento customizado para atualizar display name quando alterado
                    ui.run_javascript("""
                        window.addEventListener('display-name-updated', function(event) {
                            // Força reload da página para atualizar iniciais no header
                            // (alternativa: poderia fazer uma chamada AJAX, mas reload é mais simples)
                            setTimeout(function() {
                                window.location.reload();
                            }, 500);
                        });
                    """)
                    
                    # Listener JavaScript para evento avatar-updated
                    # Quando avatar é atualizado, limpa cache e recarrega
                    ui.run_javascript("""
                        window.addEventListener('avatar-updated', function(event) {
                            console.log('[AVATAR HEADER] Evento avatar-updated recebido', event.detail);
                            // Limpa cache e força recarregamento do avatar após 500ms
                            setTimeout(function() {
                                window.location.reload();
                            }, 500);
                        });
                    """)

    # Sidebar - Renderiza baseado no workspace ativo
    from .componentes.sidebar_base import render_sidebar, obter_itens_menu_por_workspace
    from .gerenciadores.gerenciador_workspace import obter_workspace_atual

    # Obtém workspace atual e itens de menu correspondentes
    workspace_atual = obter_workspace_atual()
    itens_menu = obter_itens_menu_por_workspace(workspace_atual)

    # Obtém rota atual para destacar item ativo
    # app já está importado no topo do arquivo
    rota_atual = None
    try:
        # Tenta obter a rota atual da requisição
        rota_atual = app.storage.user.get('_current_route', None)
    except Exception:
        pass

    # Renderiza sidebar com itens do workspace
    render_sidebar(itens_menu, rota_atual=rota_atual)

    # CORREÇÃO: Container de conteúdo - NiceGUI behavior=push já empurra o conteúdo
    # Padding apenas top/right/bottom (pl-0 para evitar duplicação com CSS)
    with ui.column().classes('w-full min-h-screen pt-4 pr-4 pb-4 pl-0 bg-gray-50 taques-content-container'):
        if breadcrumbs:
            with ui.row().classes('items-center gap-2 mb-4'):
                for i, crumb in enumerate(breadcrumbs):
                    # Suporta breadcrumb como tupla (label, url) ou string simples
                    if isinstance(crumb, tuple) and len(crumb) >= 2:
                        crumb_label, crumb_url = crumb[0], crumb[1]
                    elif isinstance(crumb, tuple) and len(crumb) == 1:
                        crumb_label, crumb_url = crumb[0], None
                    elif isinstance(crumb, str):
                        crumb_label, crumb_url = crumb, None
                    else:
                        crumb_label, crumb_url = str(crumb), None
                    # Garante que breadcrumbs também comecem com maiúscula
                    crumb_label = capitalize_first(crumb_label) if crumb_label else crumb_label
                    if crumb_url:
                        ui.link(crumb_label, crumb_url).classes('text-sm text-gray-500 hover:text-primary')
                    else:
                        ui.label(crumb_label).classes('text-sm text-gray-700 font-medium')
                    if i < len(breadcrumbs) - 1:
                        ui.icon('chevron_right', size='xs').classes('text-gray-400')
        
        ui.label(page_title).classes('text-2xl font-bold text-gray-800 mb-6')
        
        yield


# Pré-carrega dados ao iniciar
preload_data()
