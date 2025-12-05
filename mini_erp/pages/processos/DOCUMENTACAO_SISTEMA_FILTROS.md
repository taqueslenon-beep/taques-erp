# Documentação Técnica: Sistema de Filtros - Aba de Processos

**Versão:** 1.0  
**Data:** 2024-12-XX  
**Módulo:** `mini_erp/pages/processos/`  
**Stack:** Python + NiceGUI + Firebase Firestore

---

## 1. Resumo Executivo

### 1.1. Overview do Sistema

O sistema de filtros da aba de Processos permite filtrar processos cadastrados no Firestore através de múltiplos critérios simultâneos. Os filtros operam em memória após o carregamento completo dos dados, garantindo performance e flexibilidade.

**Características principais:**

- 7 filtros disponíveis (Pesquisa, Área, Casos, Clientes, Parte, Parte Contrária, Status)
- Filtros combinados com operador lógico **AND** (interseção)
- Busca por texto em tempo real
- Limpeza individual ou completa de filtros
- Suporte a processos normais e acompanhamentos de terceiros
- Filtros via URL (para integração com painel)

### 1.2. Lista de Filtros Identificados

| #   | Nome Técnico      | Label Visual    | Tipo        | Localização      |
| --- | ----------------- | --------------- | ----------- | ---------------- |
| 1   | `search_term`     | Campo de busca  | `ui.input`  | Linha superior   |
| 2   | `filter_area`     | Área            | `ui.select` | Linha de filtros |
| 3   | `filter_case`     | Casos           | `ui.select` | Linha de filtros |
| 4   | `filter_client`   | Clientes        | `ui.select` | Linha de filtros |
| 5   | `filter_parte`    | Parte           | `ui.select` | Linha de filtros |
| 6   | `filter_opposing` | Parte Contrária | `ui.select` | Linha de filtros |
| 7   | `filter_status`   | Status          | `ui.select` | Linha de filtros |

---

## 2. Detalhamento por Filtro

### 2.1. Filtro de Pesquisa (search_term)

**Nome técnico:** `search_term`  
**Label visual:** Campo de busca com placeholder "Pesquisar processos por título, número..."  
**Tipo de componente:** `ui.input` com ícone de lupa  
**Localização:** Linha superior, antes dos botões de ação

#### Estrutura Técnica

```python
# Estado
search_term = {'value': ''}

# Componente
search_input = ui.input(
    placeholder='Pesquisar processos por título, número...'
).props('outlined dense clearable')
```

#### Fonte de Dados

- **Campo buscado:** `title_raw` (título original sem indentação hierárquica)
- **Fallback:** `title` (se `title_raw` não existir)
- **Busca:** Case-insensitive, substring matching

#### Validações

- Nenhuma validação específica
- Aceita qualquer string (incluindo vazia)
- Espaços são preservados

#### Dependências

- Nenhuma dependência de outros filtros
- Funciona independentemente

#### Comportamento ao Aplicar

```python
# Linha 728-730: processos_page.py
if search_term['value']:
    term = search_term['value'].lower()
    filtered = [r for r in filtered if term in (r.get('title_raw') or r.get('title') or '').lower()]
```

**Lógica:**

- Converte termo de busca para minúsculas
- Busca substring no título (case-insensitive)
- Retorna processos que contêm o termo no título

#### Event Handler

```python
# Linha 607-611: processos_page.py
def on_search_change():
    search_term['value'] = search_input.value if search_input.value else ''
    refresh_table()

search_input.on('update:model-value', on_search_change)
```

**Trigger:** Mudança em tempo real no campo de input

---

### 2.2. Filtro de Área (filter_area)

**Nome técnico:** `filter_area`  
**Label visual:** "Área"  
**Tipo de componente:** `ui.select` (dropdown)  
**Localização:** Primeiro filtro na linha de filtros

#### Estrutura Técnica

```python
# Estado
filter_area = {'value': ''}

# Opções (geradas dinamicamente)
filter_options['area'] = [''] + sorted(set([r.get('area', '') for r in all_rows if r.get('area')]))

# Componente
filter_selects['area'] = create_filter_dropdown(
    'Área',
    filter_options['area'],
    filter_area,
    'w-full sm:w-auto min-w-[100px] sm:min-w-[120px]'
)
```

#### Fonte de Dados

- **Origem:** Extraído dinamicamente de todos os processos carregados
- **Função:** `get_filter_options()` (linha 568-577)
- **Processamento:**
  - Extrai valores únicos do campo `area` de todos os processos
  - Remove valores vazios
  - Ordena alfabeticamente
  - Adiciona opção vazia no início (para "sem filtro")

#### Validações

```python
# Linha 733-738: processos_page.py
if filter_area['value']:
    area_filter_value = filter_area['value'].strip()
    filtered = [
        r for r in filtered
        if (r.get('area') or '').strip() == area_filter_value
    ]
```

**Validações aplicadas:**

- Normalização de espaços (`.strip()`)
- Comparação exata (case-sensitive)
- Tratamento de valores vazios/None

#### Dependências

- Nenhuma dependência de outros filtros
- Opções dependem dos dados carregados (atualizadas a cada `fetch_processes()`)

#### Comportamento ao Aplicar

- Filtra processos que têm exatamente o valor selecionado no campo `area`
- Comparação exata (não substring)
- Processos sem área não aparecem quando filtro está ativo

#### Valores Possíveis

- Valores dinâmicos baseados nos processos cadastrados
- Exemplos comuns: "Administrativo", "Criminal", "Cível", "Tributário", "Técnico/projetos"

---

### 2.3. Filtro de Casos (filter_case)

**Nome técnico:** `filter_case`  
**Label visual:** "Casos"  
**Tipo de componente:** `ui.select` (dropdown)  
**Localização:** Segundo filtro na linha de filtros

#### Estrutura Técnica

```python
# Estado
filter_case = {'value': ''}

# Opções (geradas dinamicamente)
filter_options['cases'] = [''] + sorted(set([c for r in all_rows for c in r.get('cases_list', []) if c]))
```

#### Fonte de Dados

- **Origem:** Extraído do campo `cases_list` de todos os processos
- **Processamento:**
  - Extrai todos os casos de todos os processos
  - Remove duplicatas
  - Ordena alfabeticamente
  - Adiciona opção vazia no início

#### Validações

```python
# Linha 741-771: processos_page.py
if filter_case['value']:
    case_filter_value = filter_case['value'].strip()
    filtered_new = []
    for r in filtered:
        cases_list = r.get('cases_list') or []
        matches = any(
            str(c).strip().lower() == case_filter_value.lower() or
            case_filter_value.lower() in str(c).strip().lower()
            for c in cases_list if c
        )
        if matches:
            filtered_new.append(r)
    filtered = filtered_new
```

**Validações aplicadas:**

- Normalização de espaços (`.strip()`)
- Comparação case-insensitive
- Dupla verificação: igualdade exata OU substring (compatibilidade)
- Suporta múltiplos casos por processo (verifica se algum caso corresponde)

#### Dependências

- **Dados:** Depende de `fetch_processes()` para construir `cases_list`
- **Extração:** Processa campos `cases` e `case_ids` (linha 247-280)
- **Conversão:** IDs de casos são convertidos para títulos usando `get_cases_list()`

#### Comportamento ao Aplicar

- Filtra processos que têm o caso selecionado na lista `cases_list`
- Processos podem ter múltiplos casos (filtro retorna se algum caso corresponder)
- Acompanhamentos de terceiros também são filtrados por caso

#### Tratamento Especial

- **Acompanhamentos de terceiros:** Suportados (linha 765-771)
- **Debug:** Logs detalhados para rastreamento (linha 762-771)

---

### 2.4. Filtro de Clientes (filter_client)

**Nome técnico:** `filter_client`  
**Label visual:** "Clientes"  
**Tipo de componente:** `ui.select` (dropdown)  
**Localização:** Terceiro filtro na linha de filtros

#### Estrutura Técnica

```python
# Estado
filter_client = {'value': ''}

# Opções (geradas dinamicamente)
filter_options['clients'] = [''] + sorted(set([c for r in all_rows for c in r.get('clients_list', []) if c]))
```

#### Fonte de Dados

- **Origem:** Extraído do campo `clients_list` de todos os processos
- **Processamento:**
  - Extrai todos os clientes de todos os processos
  - Remove duplicatas
  - Ordena alfabeticamente
  - Adiciona opção vazia no início

#### Validações

```python
# Linha 774-779: processos_page.py
if filter_client['value']:
    client_filter_value = filter_client['value'].strip()
    filtered = [
        r for r in filtered
        if any(str(c).strip().lower() == client_filter_value.lower() for c in (r.get('clients_list') or []))
    ]
```

**Validações aplicadas:**

- Normalização de espaços (`.strip()`)
- Comparação case-insensitive
- Comparação exata (não substring)
- Suporta múltiplos clientes por processo (verifica se algum cliente corresponde)

#### Dependências

- **Dados:** Depende de `fetch_processes()` para construir `clients_list`
- **Formatação:** Clientes são formatados usando `_format_names_list()` (linha 63-76)
- **Display Names:** Usa `get_display_name()` para obter nomes de exibição (linha 17-60)

#### Comportamento ao Aplicar

- Filtra processos que têm o cliente selecionado na lista `clients_list`
- Processos podem ter múltiplos clientes (filtro retorna se algum cliente corresponder)
- Acompanhamentos de terceiros mostram "NA" e não aparecem neste filtro

#### Tratamento Especial

- **Acompanhamentos de terceiros:** Mostram "NA" em `clients_list` (linha 212, 396)
- **Normalização:** Nomes são normalizados para busca (maiúsculas, remoção de parênteses)

---

### 2.5. Filtro de Parte (filter_parte)

**Nome técnico:** `filter_parte`  
**Label visual:** "Parte"  
**Tipo de componente:** `ui.select` (dropdown)  
**Localização:** Quarto filtro na linha de filtros

#### Estrutura Técnica

```python
# Estado
filter_parte = {'value': ''}

# Opções (geradas dinamicamente)
filter_options['parte'] = [''] + sorted(set([c for r in all_rows for c in r.get('clients_list', []) if c]))
```

**Nota:** Este filtro usa a mesma fonte de dados que o filtro de Clientes (`clients_list`)

#### Fonte de Dados

- **Origem:** Mesma do filtro de Clientes (`clients_list`)
- **Processamento:** Idêntico ao filtro de Clientes

#### Validações

```python
# Linha 782-787: processos_page.py
if filter_parte['value']:
    parte_filter_value = filter_parte['value'].strip()
    filtered = [
        r for r in filtered
        if any(str(c).strip().lower() == parte_filter_value.lower() for c in (r.get('clients_list') or []))
    ]
```

**Validações aplicadas:**

- Idênticas ao filtro de Clientes
- Comparação case-insensitive
- Comparação exata

#### Dependências

- Mesmas do filtro de Clientes

#### Comportamento ao Aplicar

- **Idêntico ao filtro de Clientes**
- Filtra processos que têm a parte selecionada na lista `clients_list`
- Funcionalmente equivalente ao filtro de Clientes (pode ser redundante)

#### Observação

Este filtro parece ser uma duplicata funcional do filtro de Clientes. Pode ser mantido para compatibilidade ou removido em refatoração futura.

---

### 2.6. Filtro de Parte Contrária (filter_opposing)

**Nome técnico:** `filter_opposing`  
**Label visual:** "Parte Contrária"  
**Tipo de componente:** `ui.select` (dropdown)  
**Localização:** Quinto filtro na linha de filtros

#### Estrutura Técnica

```python
# Estado
filter_opposing = {'value': ''}

# Opções (geradas dinamicamente)
filter_options['opposing'] = [''] + sorted(set([c for r in all_rows for c in r.get('opposing_list', []) if c]))
```

#### Fonte de Dados

- **Origem:** Extraído do campo `opposing_list` de todos os processos
- **Processamento:**
  - Extrai todas as partes contrárias de todos os processos
  - Remove duplicatas
  - Ordena alfabeticamente
  - Adiciona opção vazia no início

#### Validações

```python
# Linha 790-795: processos_page.py
if filter_opposing['value']:
    opposing_filter_value = filter_opposing['value'].strip()
    filtered = [
        r for r in filtered
        if any(str(c).strip().lower() == opposing_filter_value.lower() for c in (r.get('opposing_list') or []))
    ]
```

**Validações aplicadas:**

- Normalização de espaços (`.strip()`)
- Comparação case-insensitive
- Comparação exata (não substring)
- Suporta múltiplas partes contrárias por processo

#### Dependências

- **Dados:** Depende de `fetch_processes()` para construir `opposing_list`
- **Formatação:** Partes contrárias são formatadas usando `_format_names_list()` (linha 242-243)
- **Display Names:** Usa `get_display_name()` para obter nomes de exibição

#### Comportamento ao Aplicar

- Filtra processos que têm a parte contrária selecionada na lista `opposing_list`
- Processos podem ter múltiplas partes contrárias (filtro retorna se alguma corresponder)
- Acompanhamentos de terceiros mostram "NA" e não aparecem neste filtro

#### Tratamento Especial

- **Acompanhamentos de terceiros:** Mostram "NA" em `opposing_list` (linha 213, 397)

---

### 2.7. Filtro de Status (filter_status)

**Nome técnico:** `filter_status`  
**Label visual:** "Status"  
**Tipo de componente:** `ui.select` (dropdown)  
**Localização:** Sexto filtro na linha de filtros

#### Estrutura Técnica

```python
# Estado
filter_status = {'value': initial_status_filter}  # Pode vir da URL

# Opções (geradas dinamicamente)
filter_options['status'] = [''] + sorted(set([r.get('status', '') for r in all_rows if r.get('status')]))
```

#### Fonte de Dados

- **Origem:** Extraído do campo `status` de todos os processos
- **Processamento:**
  - Extrai todos os status únicos
  - Remove valores vazios/None
  - Ordena alfabeticamente
  - Adiciona opção vazia no início

#### Validações

```python
# Linha 799-801: processos_page.py
if filter_status['value'] and filter_status['value'].strip():
    status_filter = filter_status['value'].strip()
    filtered = [r for r in filtered if (r.get('status') or '').strip() == status_filter]
```

**Validações aplicadas:**

- Verifica se valor não é vazio
- Normalização de espaços (`.strip()`)
- Comparação exata (case-sensitive)
- Tratamento de valores None/vazios

#### Dependências

- **URL:** Pode receber valor inicial via query parameter `filter=futuro_previsto` (linha 534-548)
- **Painel:** Integração com painel para filtrar processos futuros

#### Comportamento ao Aplicar

- Filtra processos que têm exatamente o status selecionado
- Comparação exata (não substring)
- Processos sem status não aparecem quando filtro está ativo

#### Valores Possíveis

- Valores dinâmicos baseados nos processos cadastrados
- Exemplos comuns: "Em andamento", "Concluído", "Concluído com pendências", "Em monitoramento", "Futuro/Previsto"

#### Tratamento Especial

- **Processos Futuros:** Se `process_type == 'Futuro'` e status vazio, define como "Futuro/Previsto" (linha 374-375)
- **URL Integration:** Suporta filtro inicial via URL (linha 534-548, 641-671)

---

## 3. Fluxo de Dados

### 3.1. Diagrama Textual do Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CARREGAMENTO INICIAL                                         │
│    fetch_processes() → Busca TODOS os processos do Firestore   │
│    - Processos normais via get_processes_list()                │
│    - Acompanhamentos via obter_todos_acompanhamentos()          │
│    - Formatação de dados (clientes, casos, status)              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CONSTRUÇÃO DE OPÇÕES DE FILTROS                              │
│    get_filter_options() → Extrai valores únicos                 │
│    - Área: set([r.get('area') for r in all_rows])               │
│    - Casos: set([c for r in all_rows for c in r.cases_list])    │
│    - Clientes: set([c for r in all_rows for c in r.clients_list])│
│    - Status: set([r.get('status') for r in all_rows])           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. INTERAÇÃO DO USUÁRIO                                          │
│    Usuário seleciona valores nos dropdowns ou digita busca     │
│    - Event: 'update:model-value' em cada filtro                 │
│    - Callback: on_filter_change() → atualiza state_dict         │
│    - Trigger: refresh_table()                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. APLICAÇÃO DE FILTROS                                          │
│    filter_rows(rows) → Aplica filtros sequencialmente           │
│    - Filtro de pesquisa (substring no título)                   │
│    - Filtro de área (igualdade exata)                           │
│    - Filtro de casos (igualdade exata ou substring)            │
│    - Filtro de clientes (igualdade exata)                      │
│    - Filtro de parte (igualdade exata)                         │
│    - Filtro de parte contrária (igualdade exata)               │
│    - Filtro de status (igualdade exata)                        │
│    - Operador lógico: AND (interseção)                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. RENDERIZAÇÃO DA TABELA                                        │
│    render_table() → Cria ui.table com dados filtrados           │
│    - Colunas: COLUMNS (definidas em processos_page.py)          │
│    - Rows: filtered (resultado de filter_rows())               │
│    - Slots customizados para formatação visual                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2. Points de Transformação de Dados

#### Point 1: Extração de Dados do Firestore

**Localização:** `fetch_processes()` (linha 84-438)

**Transformações:**

- Processos normais: Extrai `clients`, `opposing_parties`, `cases`, `case_ids`
- Acompanhamentos: Extrai `cases`, marca como `_is_third_party_monitoring`
- Formatação de nomes: Aplica `_format_names_list()` para obter display names
- Conversão de IDs: `case_ids` → títulos de casos via `get_cases_list()`
- Normalização de status: Processos futuros sem status → "Futuro/Previsto"

#### Point 2: Construção de Opções de Filtros

**Localização:** `get_filter_options()` (linha 568-577)

**Transformações:**

- Extrai valores únicos de cada campo
- Remove valores vazios/None
- Ordena alfabeticamente
- Adiciona opção vazia no início (para "sem filtro")

#### Point 3: Aplicação de Filtros

**Localização:** `filter_rows()` (linha 695-819)

**Transformações:**

- Normalização: `.strip()`, `.lower()` para comparações
- Filtragem sequencial: Cada filtro reduz o conjunto de resultados
- Operador lógico: AND (todos os filtros devem corresponder)

### 3.3. Cache Utilizado

**Cache de Dados:**

- **Função:** `get_processes_list()`, `get_cases_list()`, `get_clients_list()`
- **Localização:** `mini_erp/core.py`
- **Invalidação:** `invalidate_cache('processes')` após salvar/editar processo
- **Estratégia:** Cache em memória com invalidação manual

**Cache de Opções de Filtros:**

- **Não há cache:** Opções são recalculadas a cada `get_filter_options()`
- **Impacto:** Performance pode ser afetada com muitos processos
- **Oportunidade de otimização:** Cachear opções e atualizar apenas quando necessário

---

## 4. Estrutura Técnica

### 4.1. Arquivos Envolvidos

| Arquivo             | Linhas Relevantes | Responsabilidade                                    |
| ------------------- | ----------------- | --------------------------------------------------- |
| `processos_page.py` | 84-438            | `fetch_processes()` - Carregamento de dados         |
| `processos_page.py` | 568-577           | `get_filter_options()` - Construção de opções       |
| `processos_page.py` | 584-597           | `create_filter_dropdown()` - Criação de componentes |
| `processos_page.py` | 695-819           | `filter_rows()` - Lógica de filtragem               |
| `processos_page.py` | 674-692           | `clear_filters()` - Limpeza de filtros              |
| `utils.py`          | 16-27             | `normalize_name_for_display()` - Normalização       |
| `utils.py`          | 30-54             | `get_short_name()` - Formatação de nomes            |
| `database.py`       | 33-40             | `get_all_processes()` - Acesso a dados              |
| `business_logic.py` | 210-286           | `filter_processes()` - Filtragem alternativa        |

### 4.2. Funções-Chave

#### `fetch_processes()`

**Assinatura:**

```python
def fetch_processes() -> List[Dict[str, Any]]
```

**Responsabilidade:**

- Busca todos os processos do Firestore
- Busca acompanhamentos de terceiros
- Formata dados para exibição na tabela
- Constrói `clients_list`, `opposing_list`, `cases_list`

**Retorna:** Lista de dicionários com dados formatados para a tabela

---

#### `get_filter_options()`

**Assinatura:**

```python
def get_filter_options() -> Dict[str, List[str]]
```

**Responsabilidade:**

- Extrai valores únicos de cada campo filtrado
- Ordena opções alfabeticamente
- Adiciona opção vazia no início

**Retorna:** Dicionário com listas de opções para cada filtro

---

#### `create_filter_dropdown()`

**Assinatura:**

```python
def create_filter_dropdown(
    label: str,
    options: List[str],
    state_dict: Dict[str, str],
    width_class: str = 'min-w-[140px]',
    initial_value: str = ''
) -> ui.select
```

**Responsabilidade:**

- Cria componente `ui.select` para filtro
- Configura estilo e propriedades
- Registra callback de mudança
- Atualiza estado e recarrega tabela

**Retorna:** Componente NiceGUI `ui.select`

---

#### `filter_rows()`

**Assinatura:**

```python
def filter_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

**Responsabilidade:**

- Aplica todos os filtros ativos sequencialmente
- Normaliza valores para comparação
- Retorna lista filtrada

**Parâmetros:**

- `rows`: Lista de processos a filtrar

**Retorna:** Lista filtrada de processos

**Lógica:**

1. Inicia com todos os processos
2. Aplica filtro de pesquisa (se ativo)
3. Aplica filtro de área (se ativo)
4. Aplica filtro de casos (se ativo)
5. Aplica filtro de clientes (se ativo)
6. Aplica filtro de parte (se ativo)
7. Aplica filtro de parte contrária (se ativo)
8. Aplica filtro de status (se ativo)
9. Retorna resultado final

---

#### `clear_filters()`

**Assinatura:**

```python
def clear_filters() -> None
```

**Responsabilidade:**

- Limpa todos os filtros (estado e UI)
- Reseta campo de busca
- Recarrega tabela

**Efeitos:**

- Define todos os `state_dict['value']` como `''`
- Define todos os `select.value` como `''`
- Define `search_input.value` como `''`
- Chama `refresh_table()`

---

### 4.3. Variáveis de Estado Importantes

| Variável          | Tipo                   | Inicialização                      | Uso                                  |
| ----------------- | ---------------------- | ---------------------------------- | ------------------------------------ |
| `search_term`     | `Dict[str, str]`       | `{'value': ''}`                    | Armazena termo de busca              |
| `filter_area`     | `Dict[str, str]`       | `{'value': ''}`                    | Armazena área selecionada            |
| `filter_case`     | `Dict[str, str]`       | `{'value': ''}`                    | Armazena caso selecionado            |
| `filter_client`   | `Dict[str, str]`       | `{'value': ''}`                    | Armazena cliente selecionado         |
| `filter_parte`    | `Dict[str, str]`       | `{'value': ''}`                    | Armazena parte selecionada           |
| `filter_opposing` | `Dict[str, str]`       | `{'value': ''}`                    | Armazena parte contrária selecionada |
| `filter_status`   | `Dict[str, str]`       | `{'value': initial_status_filter}` | Armazena status selecionado          |
| `filter_options`  | `Dict[str, List[str]]` | `get_filter_options()`             | Opções disponíveis para cada filtro  |
| `filter_selects`  | `Dict[str, ui.select]` | `{}`                               | Referências aos componentes UI       |

**Nota:** Uso de dicionários `{'value': ''}` permite mutabilidade em callbacks Python.

---

### 4.4. Event Handlers

#### `on_search_change()`

**Trigger:** `search_input.on('update:model-value', on_search_change)`  
**Ação:** Atualiza `search_term['value']` e chama `refresh_table()`

#### `on_filter_change()`

**Trigger:** `select.on('update:model-value', on_filter_change)`  
**Ação:** Atualiza `state_dict['value']` e chama `refresh_table()`

**Nota:** Cada filtro tem seu próprio `on_filter_change()` closure que captura o `state_dict` específico.

---

## 5. Padrões Identificados

### 5.1. Padrões de Codificação

#### Padrão 1: Estado Mutável via Dicionários

```python
filter_area = {'value': ''}  # Permite mutação em callbacks
```

**Motivo:** NiceGUI callbacks precisam de referências mutáveis para atualizar estado.

#### Padrão 2: Filtragem Sequencial

```python
filtered = rows  # Inicia com todos
if filter_area['value']:
    filtered = [r for r in filtered if ...]  # Reduz conjunto
if filter_case['value']:
    filtered = [r for r in filtered if ...]  # Reduz mais
```

**Motivo:** Aplicação incremental de filtros com operador AND.

#### Padrão 3: Normalização Consistente

```python
filter_value = filter_area['value'].strip()  # Sempre normaliza
if (r.get('area') or '').strip() == filter_value:  # Compara normalizado
```

**Motivo:** Garante comparações corretas independente de espaços extras.

#### Padrão 4: Opções Dinâmicas

```python
filter_options = get_filter_options()  # Recalcula a cada renderização
```

**Motivo:** Opções refletem dados atuais (incluindo novos processos).

### 5.2. Convenções de Nomenclatura

- **Filtros:** `filter_<campo>` (ex: `filter_area`, `filter_case`)
- **Estado:** Dicionários com chave `'value'` (ex: `filter_area['value']`)
- **Opções:** `filter_options['<campo>']` (ex: `filter_options['area']`)
- **Componentes:** `filter_selects['<campo>']` (ex: `filter_selects['area']`)
- **Funções:** `get_<recurso>_options()` (ex: `get_filter_options()`)

### 5.3. Estruturas de Dados Padrão

#### Row Data (Processo Formatado)

```python
{
    '_id': str,                    # ID do documento Firestore
    'data_abertura': str,          # Data formatada (DD/MM/AAAA)
    'data_abertura_sort': str,     # Data para ordenação (AAAA/MM/DD)
    'title': str,                  # Título para exibição
    'title_raw': str,              # Título original (para busca)
    'number': str,                 # Número do processo
    'clients_list': List[str],     # Lista de clientes formatados
    'opposing_list': List[str],    # Lista de partes contrárias formatadas
    'cases_list': List[str],       # Lista de casos vinculados
    'system': str,                 # Sistema do processo
    'status': str,                 # Status do processo
    'area': str,                   # Área do direito
    'link': str,                   # Link do processo
    'is_third_party_monitoring': bool  # Flag de acompanhamento
}
```

---

## 6. Integração com Banco de Dados

### 6.1. Queries Firestore

**Importante:** O sistema de filtros **NÃO** usa queries Firestore diretamente. Todos os dados são carregados uma vez e filtrados em memória.

#### Carregamento Inicial

```python
# processos_page.py, linha 98
raw = get_processes_list()  # Busca TODOS os processos

# processos_page.py, linha 104
acompanhamentos = obter_todos_acompanhamentos()  # Busca TODOS os acompanhamentos
```

**Query equivalente:**

```javascript
// Firestore (conceitual)
db.collection("processes").get(); // Todos os processos
db.collection("third_party_monitoring").get(); // Todos os acompanhamentos
```

**Estratégia:** Load-all-then-filter (carrega tudo, depois filtra)

### 6.2. Índices Utilizados

**Nenhum índice específico necessário** porque:

- Todas as queries são `get()` sem filtros
- Filtragem é feita em memória após carregamento

**Possíveis otimizações futuras:**

- Índices compostos para queries filtradas no Firestore
- Queries com `where()` para reduzir dados carregados

### 6.3. Otimizações de Performance

#### Otimização 1: Cache de Dados

- **Localização:** `mini_erp/core.py`
- **Estratégia:** Cache em memória com invalidação manual
- **Benefício:** Reduz chamadas ao Firestore

#### Otimização 2: Carregamento Único

- **Estratégia:** Carrega todos os dados uma vez
- **Benefício:** Evita múltiplas queries ao aplicar filtros
- **Trade-off:** Maior uso de memória, mas filtros mais rápidos

#### Otimização 3: Conversão de IDs em Lote

```python
# processos_page.py, linha 262-276
all_cases = get_cases_list()  # Busca uma vez
case_titles_by_id = {}  # Cria mapeamento
for case in all_cases:
    case_titles_by_id[str(case_id)] = str(case_title)
```

**Benefício:** Evita múltiplas buscas ao converter `case_ids` para títulos.

### 6.4. Possíveis Gargalos

#### Gargalo 1: Carregamento Inicial

- **Problema:** Carrega TODOS os processos mesmo se não forem exibidos
- **Impacto:** Lento com muitos processos (>1000)
- **Solução possível:** Paginação ou queries filtradas no Firestore

#### Gargalo 2: Reconstrução de Opções

- **Problema:** `get_filter_options()` recalcula opções a cada renderização
- **Impacto:** Lento com muitos processos
- **Solução possível:** Cachear opções e atualizar apenas quando necessário

#### Gargalo 3: Filtragem Sequencial

- **Problema:** Múltiplas iterações sobre a lista
- **Impacto:** Lento com muitos processos
- **Solução possível:** Otimizar com list comprehensions ou generators

---

## 7. Tratamento de Erros

### 7.1. Mensagens de Erro Possíveis

**Nenhuma mensagem de erro específica** é exibida ao usuário. O sistema trata erros silenciosamente:

#### Erro 1: Dados Inválidos no Firestore

```python
# processos_page.py, linha 436-438
except Exception as e:
    print(f"Erro ao buscar processos: {e}")
    return []  # Retorna lista vazia
```

**Comportamento:** Retorna lista vazia, tabela mostra "Nenhum processo encontrado"

#### Erro 2: Erro ao Buscar Acompanhamentos

```python
# processos_page.py, linha 122-125
except Exception as e:
    print(f"[FETCH_PROCESSOS] Erro ao buscar acompanhamentos: {e}")
    # Continua sem acompanhamentos
```

**Comportamento:** Continua sem acompanhamentos, não interrompe carregamento

### 7.2. Comportamento com Dados Inválidos

#### Caso 1: Campo Vazio/None

```python
# Normalização automática
proc_status = proc.get('status') or ''  # Converte None para ''
```

**Comportamento:** Trata valores None como vazios, não causa erro

#### Caso 2: Lista Vazia/None

```python
# Tratamento defensivo
cases_list = r.get('cases_list') or []  # Garante lista vazia se None
```

**Comportamento:** Usa lista vazia como fallback, não causa erro

#### Caso 3: Tipo de Dado Inesperado

```python
# Conversão defensiva
if isinstance(cases_raw, list):
    cases_list.extend([str(c).strip() for c in cases_raw if c])
else:
    cases_list.append(str(cases_raw).strip())
```

**Comportamento:** Converte para string, não causa erro

### 7.3. Cenários Edge Case

#### Edge Case 1: Processo sem Status

- **Comportamento:** Normalizado para string vazia `''`
- **Filtro:** Processos sem status não aparecem quando filtro de status está ativo
- **Tratamento:** Linha 367-378 em `processos_page.py`

#### Edge Case 2: Processo Futuro sem Status

- **Comportamento:** Define automaticamente como "Futuro/Previsto"
- **Tratamento:** Linha 374-375 em `processos_page.py`

#### Edge Case 3: Acompanhamento sem Casos

- **Comportamento:** `cases_list` fica vazia `[]`
- **Filtro:** Não aparece quando filtro de casos está ativo
- **Tratamento:** Linha 220-227 em `processos_page.py`

#### Edge Case 4: Múltiplos Formatos de Data

- **Comportamento:** Suporta AAAA, MM/AAAA, DD/MM/AAAA
- **Tratamento:** Linha 293-359 em `processos_page.py`

### 7.4. Recuperação de Erros

**Estratégia:** Fail-safe (retorna estado seguro)

- **Erro ao buscar processos:** Retorna `[]` (lista vazia)
- **Erro ao buscar acompanhamentos:** Continua sem acompanhamentos
- **Erro ao aplicar filtro:** Log no console, continua com dados não filtrados

**Logs de Debug:**

- Todos os erros são logados no console com `print()`
- Facilita diagnóstico sem interromper usuário

---

## 8. Limpeza e Reset

### 8.1. Limpeza Individual

**Mecanismo:** Cada filtro tem botão "clear" (propriedade `clearable` do `ui.select`)

```python
# processos_page.py, linha 585
select = ui.select(...).props('clearable dense outlined')
```

**Comportamento:**

- Usuário clica no "X" no dropdown
- Valor é limpo (`select.value = ''`)
- Callback `on_filter_change()` é disparado
- Estado é atualizado (`state_dict['value'] = ''`)
- Tabela é recarregada

### 8.2. Botão "Limpar"

**Localização:** Linha 692 em `processos_page.py`

```python
ui.button('Limpar', icon='clear_all', on_click=clear_filters)
```

**Função:** `clear_filters()` (linha 674-692)

**Ações:**

1. Limpa todos os estados: `filter_area['value'] = ''`, etc.
2. Limpa todos os componentes: `filter_selects['area'].value = ''`, etc.
3. Limpa campo de busca: `search_input.value = ''`
4. Recarrega tabela: `refresh_table()`

**Resultado:** Todos os filtros são resetados, tabela mostra todos os processos

### 8.3. Estado Após Reset

**Estado dos Filtros:**

- Todos os `state_dict['value']` = `''`
- Todos os `select.value` = `''`
- `search_input.value` = `''`

**Estado da Tabela:**

- Mostra TODOS os processos (sem filtros aplicados)
- Ordenação: Por título (alfabética)

### 8.4. Persistência

**Não há persistência:**

- Filtros não são salvos entre sessões
- Ao recarregar página, todos os filtros são resetados
- Filtros via URL são aplicados apenas na carga inicial

**Exceção:** Filtro via URL

- Query parameter `filter=futuro_previsto` é lido na carga inicial
- Aplica filtro de status automaticamente
- Não persiste após limpeza manual

---

## 9. Responsividade e UX

### 9.1. Comportamento em Diferentes Tamanhos de Tela

#### Layout Responsivo

```python
# processos_page.py, linha 600
with ui.row().classes('w-full items-center gap-2 sm:gap-4 mb-4 flex-wrap'):
```

**Breakpoints:**

- **Mobile:** `w-full` (largura total)
- **Desktop:** `sm:w-auto` (largura automática)

#### Filtros Responsivos

```python
# processos_page.py, linha 634
filter_selects['area'] = create_filter_dropdown(
    'Área',
    filter_options['area'],
    filter_area,
    'w-full sm:w-auto min-w-[100px] sm:min-w-[120px]'
)
```

**Comportamento:**

- **Mobile:** Filtros ocupam largura total, empilham verticalmente
- **Desktop:** Filtros ficam em linha horizontal, largura mínima definida

### 9.2. Acessibilidade dos Filtros

#### Labels Visuais

- Todos os filtros têm labels claros ("Área", "Casos", etc.)
- Placeholder no campo de busca indica o que pode ser pesquisado

#### Navegação por Teclado

- **Tab:** Navega entre filtros sequencialmente
- **Enter:** Seleciona opção no dropdown (comportamento padrão do NiceGUI)
- **Escape:** Fecha dropdown (comportamento padrão do NiceGUI)

#### Indicadores Visuais

- **Ícone de busca:** Indica campo de pesquisa
- **Botão "Limpar":** Ícone `clear_all` indica função de limpeza
- **Estilo discreto:** Filtros não competem visualmente com conteúdo principal

### 9.3. Interações por Teclado/Mouse

#### Mouse

- **Clique no dropdown:** Abre lista de opções
- **Clique na opção:** Seleciona e fecha dropdown
- **Clique no "X":** Limpa filtro individual
- **Clique em "Limpar":** Limpa todos os filtros

#### Teclado

- **Tab:** Navega entre campos
- **Enter:** Seleciona opção no dropdown
- **Escape:** Fecha dropdown
- **Digitação no campo de busca:** Filtra em tempo real

### 9.4. Feedback Visual ao Usuário

#### Feedback Imediato

- **Mudança de filtro:** Tabela atualiza instantaneamente
- **Sem delay perceptível:** Filtros são aplicados em memória (rápido)

#### Indicadores de Estado

- **Filtro ativo:** Dropdown mostra valor selecionado
- **Filtro vazio:** Dropdown mostra placeholder
- **Busca ativa:** Campo mostra texto digitado

#### Falta de Indicadores

- **Não há indicador visual** de quantos filtros estão ativos
- **Não há contador** de resultados filtrados
- **Oportunidade de melhoria:** Adicionar badge com contagem de filtros ativos

---

## 10. Possíveis Melhorias

### 10.1. Gaps na Funcionalidade

#### Gap 1: Filtro por Data de Abertura

- **Status:** Não implementado
- **Impacto:** Usuários não podem filtrar por período
- **Solução:** Adicionar filtro de data (range ou seleção de ano/mês)

#### Gap 2: Filtro por Sistema

- **Status:** Não implementado na interface principal
- **Impacto:** Usuários não podem filtrar por sistema (PJe, e-SAJ, etc.)
- **Solução:** Adicionar dropdown de sistemas

#### Gap 3: Filtro por Número do Processo

- **Status:** Não implementado (apenas busca por texto)
- **Impacto:** Busca por número é genérica (substring)
- **Solução:** Adicionar filtro específico para número

#### Gap 4: Filtro Duplicado (Parte vs Clientes)

- **Status:** `filter_parte` é funcionalmente idêntico a `filter_client`
- **Impacto:** Confusão do usuário, redundância
- **Solução:** Remover `filter_parte` ou diferenciar funcionalmente

### 10.2. Otimizações de Performance

#### Otimização 1: Cache de Opções de Filtros

```python
# Atual: Recalcula a cada renderização
filter_options = get_filter_options()

# Sugestão: Cachear e invalidar apenas quando necessário
_filter_options_cache = None
def get_filter_options_cached():
    global _filter_options_cache
    if _filter_options_cache is None:
        _filter_options_cache = get_filter_options()
    return _filter_options_cache
```

**Benefício:** Reduz tempo de renderização com muitos processos

#### Otimização 2: Debounce na Busca

```python
# Atual: Atualiza a cada tecla digitada
search_input.on('update:model-value', on_search_change)

# Sugestão: Debounce de 300ms
from nicegui import ui
search_input.on('update:model-value', lambda: ui.timer(0.3, on_search_change, once=True))
```

**Benefício:** Reduz recarregamentos desnecessários durante digitação

#### Otimização 3: Queries Filtradas no Firestore

```python
# Atual: Carrega tudo, filtra em memória
raw = get_processes_list()

# Sugestão: Query filtrada quando possível
if filter_status['value']:
    raw = db.collection('processes').where('status', '==', filter_status['value']).get()
```

**Benefício:** Reduz dados carregados e tempo de resposta

### 10.3. Melhorias de UX

#### Melhoria 1: Indicador de Filtros Ativos

```python
# Adicionar badge com contagem
active_filters_count = sum(1 for f in [filter_area, filter_case, ...] if f['value'])
if active_filters_count > 0:
    ui.badge(f'{active_filters_count} filtros ativos', color='primary')
```

**Benefício:** Usuário sabe quantos filtros estão aplicados

#### Melhoria 2: Contador de Resultados

```python
# Mostrar "X processos encontrados"
ui.label(f'{len(filtered)} processos encontrados').classes('text-sm text-gray-600')
```

**Benefício:** Feedback claro sobre quantidade de resultados

#### Melhoria 3: Salvar Filtros Favoritos

```python
# Permitir salvar combinações de filtros
def save_filter_preset(name: str):
    preset = {
        'area': filter_area['value'],
        'status': filter_status['value'],
        # ...
    }
    # Salvar no localStorage ou Firestore
```

**Benefício:** Usuários podem reutilizar filtros comuns

#### Melhoria 4: Filtros Avançados (Modal)

```python
# Botão "Filtros Avançados" abre modal com mais opções
ui.button('Filtros Avançados', on_click=open_advanced_filters_modal)
```

**Benefício:** Interface mais limpa, opções avançadas disponíveis

### 10.4. Refatorações Recomendadas

#### Refatoração 1: Extrair Lógica de Filtros

```python
# Criar classe FilterManager
class FilterManager:
    def __init__(self):
        self.filters = {}
        self.options = {}

    def add_filter(self, name: str, options: List[str]):
        self.filters[name] = {'value': ''}
        self.options[name] = options

    def apply_filters(self, rows: List[Dict]) -> List[Dict]:
        # Lógica centralizada de filtragem
        pass
```

**Benefício:** Código mais organizado, fácil de testar

#### Refatoração 2: Separar Filtros de UI

```python
# Separar lógica de negócio da UI
# business_logic.py
def apply_all_filters(rows, filters_config) -> List[Dict]:
    # Lógica pura de filtragem
    pass

# processos_page.py
filtered = apply_all_filters(rows, {
    'area': filter_area['value'],
    'status': filter_status['value'],
    # ...
})
```

**Benefício:** Testabilidade, reutilização

#### Refatoração 3: Unificar Filtros Duplicados

```python
# Remover filter_parte ou diferenciar
# Se "Parte" deve ser diferente de "Clientes", implementar lógica específica
# Caso contrário, remover e usar apenas filter_client
```

**Benefício:** Código mais limpo, menos confusão

---

## 11. Integração com Resto do Sistema

### 11.1. Dependências de Módulos Externos

#### `mini_erp/core.py`

- **Funções usadas:**
  - `get_processes_list()`: Busca processos do Firestore
  - `get_clients_list()`: Busca clientes
  - `get_opposing_parties_list()`: Busca partes contrárias
  - `get_cases_list()`: Busca casos
  - `get_display_name()`: Obtém nome de exibição de pessoas
  - `invalidate_cache()`: Invalida cache após mudanças

#### `mini_erp/pages/processos/database.py`

- **Funções usadas:**
  - `obter_todos_acompanhamentos()`: Busca acompanhamentos de terceiros

#### `mini_erp/pages/processos/utils.py`

- **Funções usadas:**
  - `normalize_name_for_display()`: Normaliza nomes para comparação
  - `get_short_name()`: Obtém nome abreviado

### 11.2. Integração com Painel

**Filtro via URL:**

```python
# processos_page.py, linha 534-548
if query_params.get('filter') and 'futuro_previsto' in query_params.get('filter', [])[0]:
    initial_status_filter = 'Futuro/Previsto'
```

**Uso:** Painel pode navegar para `/processos?filter=futuro_previsto` para mostrar apenas processos futuros

### 11.3. Integração com Acompanhamentos de Terceiros

**Suporte integrado:**

- Acompanhamentos são incluídos em `fetch_processes()`
- Marcados com `is_third_party_monitoring: True`
- Filtrados pelos mesmos critérios (exceto Clientes/Parte Contrária que mostram "NA")
- Suportam filtro por casos

### 11.4. Callbacks de Atualização

**Callback após salvar processo:**

```python
# processos_page.py, linha 489-508
def on_process_saved():
    invalidate_cache('processes')
    invalidate_cache('clients')
    refresh_table()
```

**Integração:** Modal de processo chama este callback após salvar, garantindo tabela atualizada

---

## 12. Rastreabilidade

### 12.1. Histórico de Mudanças

#### Versão 1.0 (2024-12-XX)

- Documentação inicial completa
- Mapeamento de todos os 7 filtros
- Análise de estrutura técnica
- Identificação de padrões e melhorias

#### Correções Anteriores (documentadas em `CORRECAO_FILTROS.md`)

- Correção de extração de casos (suporte a `case_ids`)
- Correção de lógica de comparação (igualdade exata)
- Normalização consistente de dados

### 12.2. Versão do Sistema

**Versão atual:** 1.0 (documentação)  
**Versão do código:** Baseada em commits do repositório  
**Stack:** Python + NiceGUI + Firebase Firestore

### 12.3. Datas Relevantes

- **Criação do módulo:** Data do primeiro commit (consultar git log)
- **Última correção de filtros:** Documentada em `CORRECAO_FILTROS.md`
- **Documentação criada:** 2024-12-XX

---

## 13. Acessibilidade para Usuários Sem Experiência Técnica

### 13.1. Glossário de Termos

| Termo               | Definição Simples                                                             |
| ------------------- | ----------------------------------------------------------------------------- |
| **Filtro**          | Ferramenta para mostrar apenas processos que atendem a um critério específico |
| **Dropdown**        | Lista suspensa que aparece ao clicar em um campo                              |
| **Busca**           | Campo de texto onde você digita palavras para encontrar processos             |
| **Limpar**          | Botão que remove todos os filtros aplicados                                   |
| **Área**            | Tipo de direito do processo (ex: Cível, Criminal, Tributário)                 |
| **Status**          | Situação atual do processo (ex: Em andamento, Concluído)                      |
| **Caso**            | Processo maior ao qual este processo está vinculado                           |
| **Cliente**         | Pessoa ou empresa que contratou os serviços                                   |
| **Parte Contrária** | Pessoa ou empresa contra quem o processo está sendo movido                    |

### 13.2. Guia Rápido de Uso

#### Como Filtrar por Área

1. Localize o dropdown "Área" na linha de filtros
2. Clique no dropdown
3. Selecione a área desejada (ex: "Cível")
4. A tabela atualiza automaticamente mostrando apenas processos daquela área

#### Como Buscar por Título

1. Localize o campo de busca (com ícone de lupa) no topo
2. Digite parte do título do processo
3. A tabela atualiza automaticamente enquanto você digita

#### Como Limpar Todos os Filtros

1. Localize o botão "Limpar" (com ícone de limpeza) na linha de filtros
2. Clique no botão
3. Todos os filtros são removidos e a tabela mostra todos os processos

#### Como Combinar Múltiplos Filtros

1. Selecione um filtro (ex: Área = "Cível")
2. Selecione outro filtro (ex: Status = "Em andamento")
3. A tabela mostra apenas processos que atendem AMBOS os critérios

### 13.3. Problemas Comuns e Soluções

#### Problema: "Não encontro nenhum processo"

**Possíveis causas:**

- Filtros muito restritivos aplicados
- Busca por texto que não existe em nenhum título

**Solução:**

- Clique em "Limpar" para remover todos os filtros
- Verifique se o texto da busca está correto

#### Problema: "Filtro não aparece na lista"

**Possíveis causas:**

- Nenhum processo tem aquele valor
- Dados ainda não foram carregados

**Solução:**

- Aguarde alguns segundos para carregamento
- Se persistir, o valor pode não existir nos dados

#### Problema: "Tabela não atualiza após mudar filtro"

**Possíveis causas:**

- Erro no carregamento de dados
- Problema de conexão

**Solução:**

- Recarregue a página (F5)
- Verifique sua conexão com a internet

---

## 14. Conclusão

### 14.1. Resumo da Análise

O sistema de filtros da aba de Processos é robusto e funcional, com 7 filtros disponíveis que operam em memória após carregamento completo dos dados. A arquitetura é simples e direta, facilitando manutenção e extensão.

**Pontos fortes:**

- Filtros funcionam corretamente
- Interface responsiva
- Suporte a múltiplos critérios simultâneos
- Tratamento adequado de edge cases

**Pontos de melhoria:**

- Performance com muitos processos (>1000)
- Falta de indicadores visuais de filtros ativos
- Filtro duplicado (Parte vs Clientes)
- Ausência de filtros por data e sistema

### 14.2. Recomendações Prioritárias

1. **Alta prioridade:** Adicionar indicador visual de filtros ativos e contador de resultados
2. **Média prioridade:** Otimizar performance com cache de opções e debounce na busca
3. **Baixa prioridade:** Remover ou diferenciar filtro "Parte" duplicado
4. **Futuro:** Implementar filtros por data e sistema

### 14.3. Próximos Passos

1. Revisar esta documentação com o time de desenvolvimento
2. Priorizar melhorias identificadas
3. Implementar otimizações de performance
4. Adicionar testes automatizados para filtros
5. Coletar feedback de usuários sobre UX

---

**Fim da Documentação**



