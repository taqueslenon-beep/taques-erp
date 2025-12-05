# Funções Principais de Manipulação de Dados - TAQUES ERP

## 📋 Índice
- [Casos (Cases)](#casos-cases)
- [Pessoas (Clients & Opposing Parties)](#pessoas-clients--opposing-parties)
- [Processos](#processos)

---

## 🗂️ Casos (Cases)

### **CRUD - Operações Básicas**

#### **CREATE (Criar)**
```python
# database.py
save_case(case: dict, skip_duplicate_check: bool = False) -> None
```
- Salva um caso no Firestore usando slug como ID único
- Args: `case` - dicionário com dados do caso

```python
# business_logic.py
create_new_case_dict(
    case_name: str,
    year: int,
    month: int,
    case_type: str,
    category: str,
    status: str,
    state: str,
    parte_contraria: str,
    parte_contraria_options: dict,
    selected_clients: list
) -> dict
```
- Cria estrutura completa de um novo caso com todos os campos necessários
- Retorna dicionário pronto para salvar

#### **READ (Ler)**
```python
# core.py (via database.py)
get_cases_list() -> List[Dict[str, Any]]
```
- Retorna lista completa de todos os casos do Firestore

```python
# business_logic.py
get_filtered_cases() -> list
```
- Retorna casos filtrados por busca, status, cliente, estado, categoria
- Remove duplicatas automaticamente

```python
# business_logic.py
get_cases_by_type(case_type: str) -> list
```
- Retorna casos de um tipo específico ('Antigo', 'Novo', 'Futuro')
- Ordenados por data (ano, mês, nome)

```python
# core.py
get_case_by_slug(case_slug: str) -> Optional[Dict[str, Any]]
```
- Retorna dados completos de um caso pelo slug

```python
# core.py
get_case_title_by_slug(case_slug: str) -> Optional[str]
```
- Retorna apenas o título do caso pelo slug

#### **UPDATE (Atualizar)**
```python
# database.py
save_case(case: dict, skip_duplicate_check: bool = False) -> None
```
- Atualiza caso existente (mesma função de criar, usa slug como chave)

```python
# database.py
renumber_cases_of_type(case_type: str, force: bool = False) -> None
```
- Renumera todos os casos de um tipo baseado na ordem cronológica
- Atualiza título e slug automaticamente

```python
# database.py
renumber_all_cases() -> None
```
- Renumera todos os casos de todos os tipos

#### **DELETE (Deletar)**
```python
# database.py
remove_case(case_to_remove: dict) -> bool
```
- Remove caso da lista e limpa referências em processos
- Args: `case_to_remove` - dicionário do caso
- Returns: True se removido com sucesso

```python
# database.py
delete_case(slug: str) -> None
```
- Wrapper para deletar caso pelo slug

---

### **Lógica de Negócio - Casos**

```python
# business_logic.py
get_case_type(case: dict) -> str
```
- Retorna tipo do caso ('Antigo', 'Novo', 'Futuro')

```python
# business_logic.py
get_case_sort_key(case: dict) -> tuple
```
- Retorna chave de ordenação (ano, mês, nome)

```python
# business_logic.py
calculate_case_number(case_type: str, year: int, month: int, name: str) -> int
```
- Calcula número sequencial baseado na posição cronológica

```python
# business_logic.py
generate_case_title(case_type: str, sequence: int, name: str, year: int) -> str
```
- Gera título formatado: "X.Y - Nome / Ano"

```python
# business_logic.py
deduplicate_cases_by_title(cases: list) -> list
```
- Remove duplicatas baseado em título + ano

---

## 👥 Pessoas (Clients & Opposing Parties)

### **CRUD - Clientes (Clients)**

#### **CREATE (Criar)**
```python
# database.py
save_client(client: Dict[str, Any]) -> None
```
- Salva um cliente no Firestore
- Args: `client` - dicionário com dados do cliente

```python
# core.py (API alternativa)
save_client(
    client: Dict[str, Any] = None,
    *,
    full_name: str = None,
    cpf_cnpj: str = None,
    display_name: str = None,
    nickname: str = None,
    client_type: str = None,
    cpf: str = None,
    cnpj: str = None,
) -> None
```
- Pode ser chamada com dicionário ou parâmetros nomeados

#### **READ (Ler)**
```python
# database.py
get_clients_list() -> List[Dict[str, Any]]
```
- Retorna lista completa de clientes

```python
# database.py
get_client_by_index(index: int) -> Optional[Dict[str, Any]]
```
- Retorna cliente pelo índice na lista

```python
# database.py
get_client_by_name(full_name: str) -> Optional[Dict[str, Any]]
```
- Busca cliente pelo nome completo

#### **UPDATE (Atualizar)**
```python
# database.py
save_client(client: Dict[str, Any]) -> None
```
- Mesma função de criar (usa _id ou nome como chave)

#### **DELETE (Deletar)**
```python
# database.py
delete_client(client: Dict[str, Any]) -> None
```
- Remove cliente do Firestore
- Args: `client` - dicionário do cliente a remover

---

### **CRUD - Outros Envolvidos (Opposing Parties)**

#### **CREATE (Criar)**
```python
# database.py
save_opposing_party(opposing: Dict[str, Any]) -> None
```
- Salva um outro envolvido no Firestore

```python
# core.py (API alternativa)
save_opposing_party(
    opposing: Dict[str, Any] = None,
    *,
    full_name: str = None,
    cpf_cnpj: str = None,
    entity_type: str = None,
    display_name: str = None,
    nickname: str = None
) -> None
```

#### **READ (Ler)**
```python
# database.py
get_opposing_parties_list() -> List[Dict[str, Any]]
```
- Retorna lista completa de outros envolvidos

```python
# database.py
get_opposing_party_by_index(index: int) -> Optional[Dict[str, Any]]
```
- Retorna outro envolvido pelo índice

```python
# database.py
get_opposing_party_by_name(full_name: str) -> Optional[Dict[str, Any]]
```
- Busca outro envolvido pelo nome completo

#### **UPDATE (Atualizar)**
```python
# database.py
save_opposing_party(opposing: Dict[str, Any]) -> None
```
- Mesma função de criar

#### **DELETE (Deletar)**
```python
# database.py
delete_opposing_party(opposing: Dict[str, Any]) -> None
```
- Remove outro envolvido do Firestore

---

### **Lógica de Negócio - Pessoas**

```python
# business_logic.py
get_people_options_for_partners() -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]
```
- Retorna opções de pessoas (Clientes + Outros Envolvidos) para dropdown de sócios
- Returns: (options_dict, data_dict)

```python
# business_logic.py
group_clients_by_type() -> List[Tuple[str, List[Tuple[int, Dict[str, Any]]]]]
```
- Agrupa clientes por tipo (PJ primeiro, depois PF)
- Ordena alfabeticamente

```python
# business_logic.py
process_partners_from_rows(partners_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```
- Processa linhas de sócios do formulário

```python
# business_logic.py
create_bond_data(person_label: str, bond_type: str) -> Dict[str, Any]
```
- Cria estrutura de dados de vínculo entre pessoas

```python
# business_logic.py
check_bond_exists(client: Dict[str, Any], person_name: str) -> bool
```
- Verifica se vínculo já existe

```python
# business_logic.py
validate_bond_not_self(person_label: str, client_name: str) -> bool
```
- Valida que vínculo não é auto-referência

---

## ⚖️ Processos

### **CRUD - Operações Básicas**

#### **CREATE (Criar)**
```python
# database.py
save_process(process_data: Dict[str, Any], edit_index: Optional[int] = None) -> str
```
- Salva ou atualiza processo
- Args: `process_data` - dados do processo, `edit_index` - None para novo
- Returns: Mensagem de sucesso

```python
# business_logic.py
build_process_data(
    title: str,
    number: str,
    system: Optional[str],
    link: str,
    nucleo: Optional[str],
    area: Optional[str],
    status: Optional[str],
    result: Optional[str],
    process_type: str,
    clients: List[str],
    opposing_parties: List[str],
    other_parties: List[str],
    cases: List[str],
    strategy_objectives: str,
    legal_thesis: str,
    strategy_observations: str,
    scenarios: List[Dict[str, Any]],
    protocols: List[Dict[str, Any]],
    access_lawyer: bool,
    access_technicians: bool,
    access_client: bool,
    access_lawyer_comment: str,
    access_technicians_comment: str,
    access_client_comment: str,
) -> Dict[str, Any]
```
- Constrói dicionário completo de processo para salvar

#### **READ (Ler)**
```python
# database.py
get_all_processes() -> List[Dict[str, Any]]
```
- Retorna lista completa de processos

```python
# database.py
get_process_by_index(idx: int) -> Optional[Dict[str, Any]]
```
- Retorna processo pelo índice

```python
# core.py
get_processes_by_case(case_slug: str = None, case_title: str = None) -> List[Dict[str, Any]]
```
- Busca processos vinculados a um caso específico

```python
# core.py
get_processes_paged(
    page_size: int = 10,
    last_doc: Any = None,
    search_term: Optional[str] = None,
    status: Optional[str] = None,
    client: Optional[str] = None,
    case: Optional[str] = None,
    area: Optional[str] = None
) -> (List[Dict[str, Any]], Any)
```
- Retorna página de processos com filtros e paginação

#### **UPDATE (Atualizar)**
```python
# database.py
save_process(process_data: Dict[str, Any], edit_index: Optional[int] = None) -> str
```
- Mesma função de criar (usa edit_index para atualizar)

```python
# database.py
update_process_field(idx: int, field: str, value: Any) -> bool
```
- Atualiza campo específico de um processo

```python
# database.py
update_process_access(idx: int, access_type: str, field: str, value: bool) -> bool
```
- Atualiza campo de acesso (lawyer, technicians, client)

```python
# database.py
update_process_access_comment(idx: int, access_type: str, comment: str) -> bool
```
- Atualiza comentário de acesso

#### **DELETE (Deletar)**
```python
# database.py
delete_process(idx: int) -> Optional[str]
```
- Exclui processo pelo índice
- Returns: Título do processo excluído ou None

---

### **Lógica de Negócio - Processos**

```python
# business_logic.py
validate_process(
    title: str,
    selected_cases: List[str],
    selected_clients: Optional[List[str]] = None
) -> Tuple[bool, str]
```
- Valida dados antes de salvar
- Returns: (is_valid, error_message)

```python
# business_logic.py
filter_processes(
    processes: List[Tuple[int, Dict[str, Any]]],
    process_type: str,
    search_query: str = '',
    filter_nucleo: Optional[str] = None,
    filter_area: Optional[str] = None,
    filter_system: Optional[str] = None,
    filter_client: Optional[str] = None,
    filter_opposing: Optional[str] = None,
    filter_case: Optional[str] = None,
    filter_status: Optional[str] = None,
) -> List[Tuple[int, Dict[str, Any]]]
```
- Aplica múltiplos filtros a lista de processos

```python
# business_logic.py
group_processes_by_case(
    processes: List[Tuple[int, Dict[str, Any]]]
) -> Tuple[Dict[str, List[Tuple[int, Dict[str, Any]]]], List[Tuple[int, Dict[str, Any]]]]
```
- Agrupa processos por caso vinculado
- Returns: (dict por caso, lista sem caso)

```python
# business_logic.py
build_table_row(
    idx: int,
    process: Dict[str, Any],
    clients_list: List[Dict[str, Any]],
    opposing_list: List[Dict[str, Any]]
) -> Dict[str, Any]
```
- Constrói linha formatada para tabela

```python
# business_logic.py
is_finalized_status(status: Optional[str]) -> bool
```
- Verifica se status indica processo finalizado

---

## 🔄 Funções de Cache e Sincronização

```python
# database.py (pessoas) / core.py
invalidate_cache(collection_name: Optional[str] = None) -> None
```
- Invalida cache de uma coleção ou todas

```python
# core.py
sync_processes_cases() -> None
```
- Sincroniza referências bidirecionais entre processos e casos

```python
# database.py (processos)
sync_all() -> None
```
- Wrapper para sincronização

```python
# database.py (processos)
save_all() -> None
```
- Salva todos os dados

---

## 📝 Notas Importantes

1. **Firestore como Banco**: Todas as operações CRUD usam Firebase Firestore via `core.py`
2. **Cache**: Sistema usa cache em memória (5 minutos TTL) para melhor performance
3. **Slugs como IDs**: Casos usam `slug` como identificador único
4. **Sincronização**: Processos são fonte da verdade para vínculos com casos (`case_ids`)
5. **Validação**: Funções de validação estão em `business_logic.py`
6. **Deduplicação**: Sistema remove duplicatas automaticamente em várias operações







