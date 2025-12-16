# RELATÓRIO DE INVESTIGAÇÃO - MÓDULO DE PROCESSOS

## SCHMIDMEIER E VISÃO GERAL DO ESCRITÓRIO

**Data:** 2024-12-XX  
**Objetivo:** Mapear estrutura completa do módulo de processos em ambos os workspaces

---

## 1. WORKSPACE "ÁREA DO CLIENTE: SCHMIDMEIER"

### 1.1 Arquivos do Módulo

**Estrutura Principal:**

```
mini_erp/pages/processos/
├── __init__.py                    # Exports principais
├── models.py                      # Modelos, constantes e TypeDicts
├── database.py                    # CRUD Firestore (1000+ linhas)
├── business_logic.py              # Lógica de negócio e validações
├── utils.py                       # Funções auxiliares
├── ui_components.py               # Componentes UI e templates
├── password_security.py           # Criptografia de senhas
├── auto_save.py                   # Auto-save para campos de texto longo
│
├── visualizacoes/                 # PÁGINAS/VISUALIZAÇÕES
│   ├── visualizacao_padrao.py    # Página principal /processos
│   └── visualizacao_acesso.py    # Página /processos/acesso
│
├── modais/                        # MODAIS
│   ├── modal_processo.py          # Modal principal (8 abas)
│   ├── modal_processo_futuro.py   # Modal processo futuro
│   ├── modal_protocolo.py         # Modal protocolo
│   ├── modal_acompanhamento_terceiros.py
│   ├── components/
│   │   └── passwords_tab.py       # Aba de senhas
│   └── abas/                      # (futuro: abas separadas)
│
├── filtros/                       # SISTEMA DE FILTROS
│   ├── filtros_manager.py         # Gerencia estado
│   ├── filtro_helper.py           # Helper genérico
│   ├── filtro_area.py
│   ├── filtro_casos.py
│   ├── filtro_clientes.py
│   ├── filtro_status.py
│   ├── filtro_pesquisa.py
│   ├── aplicar_filtros.py
│   └── obter_opcoes_filtros.py
│
└── botoes/                        # (futuro: botões extraídos)
```

**Arquivos Relacionados no Core:**

- `mini_erp/core.py` - Função `get_processes_list()`, `save_process()`, `sync_processes_cases()`
- `mini_erp/workspace_collections.py` - Define coleção `'processes'` para Schmidmeier

### 1.2 Nome da Coleção no Firestore

**Coleção:** `processes`

**Mapeamento em `workspace_collections.py`:**

```python
SCHMIDMEIER_COLLECTIONS = {
    'processos': 'processes',  # Nome da coleção no Firestore
}
```

### 1.3 Campos do Modelo de Processo

**Total: 45+ campos**

#### Campos Básicos (11 campos)

- `title` \* (obrigatório) - Título do Processo
- `number` - Número do Processo
- `link` - Link do Processo
- `process_type` \* (obrigatório) - Tipo: 'Existente' ou 'Futuro'
- `data_abertura` - Data de Abertura (aceita 3 formatos: AAAA, MM/AAAA, DD/MM/AAAA)
- `clients` - Clientes (List[str] - multi-select)
- `opposing_parties` - Parte Contrária (List[str] - multi-select)
- `other_parties` - Outros Envolvidos (List[str] - multi-select)
- `parent_ids` - Processos Pais (List[str] - multi-select, hierarquia)
- `cases` - Casos Vinculados (List[str] - multi-select)
- `case_ids` - IDs/Slugs dos casos (List[str] - usado para queries)

#### Campos Jurídicos (7 campos)

- `system` - Sistema Processual (ex: 'eproc - TJSC - 1ª instância', 'e-STF', etc.)
- `nucleo` - Núcleo (opções: 'Ambiental')
- `area` - Área (opções: 'Administrativo', 'Criminal', 'Cível', 'Tributário', 'Técnico/projetos', 'Outros')
- `status` \* (obrigatório) - Status (opções: 'Em andamento', 'Concluído', 'Concluído com pendências', 'Em monitoramento', 'Futuro/Previsto')
- `result` - Resultado do processo (condicional: 'Ganho', 'Perdido', 'Neutro')
- `envolve_dano_app` - Envolve Dano em APP? (bool - switch)
- `area_total_discutida` - Área Total Discutida (float - em hectares)

#### Campos de Relatório (3 campos - AUTO-SAVE)

- `relatory_facts` - Resumo dos Fatos (editor de texto longo)
- `relatory_timeline` - Histórico / Linha do Tempo (editor de texto longo)
- `relatory_documents` - Documentos Relevantes (editor de texto longo)

#### Campos de Estratégia (3 campos - AUTO-SAVE)

- `strategy_objectives` - Objetivos (editor de texto longo)
- `legal_thesis` - Teses a serem trabalhadas (editor de texto longo)
- `strategy_observations` - Observações (editor de texto longo)

#### Campos de Cenários (1 campo - lista)

- `scenarios` - Lista de cenários (List[ScenarioDict])
  - Cada cenário tem: `title`, `type`, `status`, `impact`, `chance`, `obs`

#### Campos de Protocolos (1 campo - lista)

- `protocols` - Lista de protocolos (List[ProtocolDict])
  - Cada protocolo tem: `title`, `date`, `number`, `system`, `link`, `observations`, `case_ids`, `process_ids`

#### Campos de Acesso (9 campos - compatibilidade/dummy)

- `access_lawyer_requested`, `access_lawyer_granted`, `access_lawyer_comment`
- `access_technicians_requested`, `access_technicians_granted`, `access_technicians_comment`
- `access_client_requested`, `access_client_granted`, `access_client_comment`

#### Campos de Hierarquia

- `parent_id` - ID do processo pai (DEPRECATED - usar parent_ids)
- `parent_ids` - Lista de IDs dos processos pais (List[str])
- `depth` - Nível hierárquico (int: 0=raiz, 1=filho, 2=neto, etc.)

#### Metadados (auto-gerados)

- `_id` - ID do documento no Firestore
- `created_at` - Data de criação (ISO format)
- `updated_at` - Data última atualização (ISO format)
- `created_by` - ID do usuário que criou
- `title_searchable` - Título em minúsculas para busca
- `state` - Estado interno
- `isDeleted` - Soft delete flag (bool)

#### Subcoleções

- `senhas_processo` - Subcoleção para senhas de acesso criptografadas
  - Campos: `titulo`, `usuario`, `senha` (criptografada), `link_acesso`, `observacoes`, `data_criacao`, `data_atualizacao`, `criado_por`

### 1.4 Funcionalidades Existentes

#### CRUD Completo

- ✅ **Criar** - Modal com 8 abas para cadastro completo
- ✅ **Ler** - Listagem em tabela com múltiplas visualizações
- ✅ **Atualizar** - Edição completa via modal
- ✅ **Deletar** - Soft delete (campo `isDeleted`)
- ✅ **Duplicar** - Função `duplicar_processo()` cria cópia com sufixo [CÓPIA]

#### Visualizações

- ✅ **Visualização Padrão** (`/processos`) - Tabela com todos os processos + acompanhamentos + desdobramentos hierárquicos
- ✅ **Visualização de Acesso** (`/processos/acesso`) - Filtra processos com acesso solicitado/concedido
- ✅ **Processos por Caso** (`/processos-por-caso`) - Visualização agrupada por casos

#### Filtros Implementados

1. **Filtro de Pesquisa** - Busca em título e número (texto livre)
2. **Filtro de Área** - Filtra por área (Administrativo, Criminal, Cível, etc.)
3. **Filtro de Casos** - Filtra processos vinculados a casos específicos
4. **Filtro de Clientes** - Filtra processos por clientes envolvidos
5. **Filtro de Status** - Filtra por status do processo
6. **Filtro de Parte Contrária** - Filtra por partes contrárias

#### Funcionalidades Avançadas

- ✅ **Hierarquia de Processos** - Suporte a processos pais/filhos/netos (campo `parent_ids`)
- ✅ **Desdobramentos** - Agrupamento hierárquico para exibição
- ✅ **Vinculação com Casos** - Campo `cases` e `case_ids` para relacionamento bidirecional
- ✅ **Sincronização** - Função `sync_processes_cases()` mantém sincronização bidirecional
- ✅ **Auto-Save** - Salva automaticamente campos de texto longo a cada 30 segundos
- ✅ **Senhas Criptografadas** - Subcoleção com senhas de acesso criptografadas
- ✅ **Acompanhamentos de Terceiros** - Módulo separado integrado na visualização
- ✅ **Protocolos** - Gestão de protocolos vinculados aos processos
- ✅ **Cenários** - Gestão de cenários (positivo, neutro, negativo) com impacto e chance

#### Relatórios/Exportação

- ❌ Não há relatórios implementados
- ❌ Não há exportação para CSV/Excel

### 1.5 Relação com Casos

**Campos de Vinculação:**

- `cases` - Lista de títulos dos casos (List[str]) - usado para exibição
- `case_ids` - Lista de slugs/IDs dos casos (List[str]) - usado para queries no Firestore

**Funcionalidades:**

- ✅ Multi-select de casos no modal de processo
- ✅ Visualização de casos vinculados na tabela
- ✅ Filtro por casos na visualização padrão
- ✅ Página dedicada `/processos-por-caso` agrupando por casos
- ✅ Sincronização bidirecional via `sync_processes_cases()` no core

**Como Funciona:**

1. No modal, usuário seleciona casos no campo `cases` (multi-select)
2. Sistema extrai slugs dos casos selecionados e popula `case_ids`
3. Query no Firestore usa `case_ids` para buscar processos: `where('case_ids', 'array_contains', case_slug)`
4. Casos também mantêm referência aos processos (via campo `process_ids` ou similar)

### 1.6 Status, Categorias e Tipos

#### Status Definidos

```python
STATUS_OPTIONS = [
    'Em andamento',
    'Concluído',
    'Concluído com pendências',
    'Em monitoramento',
    'Futuro/Previsto'
]
```

**Status que indicam finalização:**

```python
FINALIZED_STATUSES = {'Concluído', 'Concluído com pendências'}
```

#### Tipos de Processo

```python
PROCESS_TYPE_OPTIONS = ['Existente', 'Futuro']
```

#### Categorias/Áreas

```python
AREA_OPTIONS = [
    'Administrativo',
    'Criminal',
    'Cível',
    'Tributário',
    'Técnico/projetos',
    'Outros'
]
```

#### Núcleos

```python
NUCLEO_OPTIONS = ['Ambiental']
```

#### Sistemas Processuais (15+ opções)

- eproc (TJSC, TRF-4) - 1ª e 2ª instância
- e-STF, e-STJ
- eProtocolo, Projudi
- SEI - Ibama, SGPE, SinFAT
- SAT/PGE-Net
- Sistemas internos do MP (MPPR, MPSC)
- Processo físico

#### Resultado (quando aplicável)

```python
RESULT_OPTIONS = ['Ganho', 'Perdido', 'Neutro']
```

---

## 2. WORKSPACE "VISÃO GERAL DO ESCRITÓRIO"

### 2.1 Módulo de Processos Existe?

✅ **SIM** - Existe arquivo, mas é apenas **placeholder**.

**Arquivo:** `mini_erp/pages/visao_geral/processos.py`

### 2.2 Estrutura do Arquivo

```python
@ui.page('/visao-geral/processos')
def processos():
    """Página de Processos do workspace Visão geral do escritório."""
    # Verifica autenticação e workspace
    with layout('Processos', breadcrumbs=[...]):
        # Tela de "em desenvolvimento"
        ui.icon('construction', size='64px')
        ui.label('Módulo em desenvolvimento')
        ui.label('Este módulo estará disponível em breve.')
```

**Status:** ❌ Apenas placeholder - não funcional

### 2.3 Nome da Coleção no Firestore

**Coleção definida:** `visao_geral_escritorio_processos`

**Mapeamento em `workspace_collections.py`:**

```python
VISAO_GERAL_COLLECTIONS = {
    'processos': 'visao_geral_escritorio_processos',
}
```

**Status da Coleção:** ✅ Coleção existe no Firestore mas está **vazia (0 processos)**

### 2.4 Campos do Modelo

❌ **Não há modelo definido** - Módulo ainda não implementado.

**Expectativa:** Deve usar o mesmo modelo do Schmidmeier (`ProcessDict` do `models.py`)

### 2.5 Funcionalidades Existentes

❌ **Nenhuma funcionalidade implementada** - Apenas tela de "em desenvolvimento"

### 2.6 Status Funcional

❌ **Não funcional** - É apenas placeholder para desenvolvimento futuro

---

## 3. FUNCIONALIDADES DO SCHMIDMEIER A REPLICAR

### 3.1 Páginas/Rotas Existentes

1. **`/processos`** - Visualização padrão (principal)

   - Arquivo: `visualizacoes/visualizacao_padrao.py`
   - Exibe: Todos os processos + acompanhamentos + desdobramentos hierárquicos
   - Funcionalidades: CRUD, filtros, busca, ordenação, paginação

2. **`/processos/acesso`** - Visualização de acesso

   - Arquivo: `visualizacoes/visualizacao_acesso.py`
   - Exibe: Processos com solicitações/concessões de acesso
   - Funcionalidades: Filtro por tipo de acesso (advogado, técnicos, cliente)

3. **`/processos-por-caso`** - Processos agrupados por caso
   - Arquivo: `mini_erp/pages/processos_por_caso.py` (fora da pasta processos)
   - Exibe: Casos com processos vinculados agrupados

### 3.2 Filtros Implementados

1. **Filtro de Pesquisa** (`filtro_pesquisa.py`)

   - Busca texto livre em título e número do processo
   - Case-insensitive
   - Busca parcial (contém)

2. **Filtro de Área** (`filtro_area.py`)

   - Dropdown com opções: Administrativo, Criminal, Cível, Tributário, Técnico/projetos, Outros
   - Filtra exatamente pelo valor selecionado

3. **Filtro de Casos** (`filtro_casos.py`)

   - Dropdown com todos os casos únicos vinculados a processos
   - Filtra processos que têm o caso selecionado no campo `cases` ou `case_ids`

4. **Filtro de Clientes** (`filtro_clientes.py`)

   - Dropdown com todos os clientes únicos vinculados a processos
   - Filtra processos que têm o cliente no campo `clients`

5. **Filtro de Status** (`filtro_status.py`)

   - Dropdown com opções: Em andamento, Concluído, Concluído com pendências, Em monitoramento, Futuro/Previsto
   - Filtra exatamente pelo status

6. **Filtro de Parte Contrária** (implementado inline)
   - Dropdown com partes contrárias únicas
   - Filtra processos que têm a parte contrária no campo `opposing_parties`

**Gerenciamento:** `filtros_manager.py` centraliza estado de todos os filtros

### 3.3 Vinculação com Casos

**Como Funciona:**

1. **No Modal de Processo:**

   - Campo multi-select `cases` permite selecionar múltiplos casos
   - Sistema extrai slugs dos casos selecionados e popula `case_ids`

2. **No Firestore:**

   - Query usa `case_ids` para buscar: `where('case_ids', 'array_contains', case_slug)`
   - Campo `cases` armazena títulos para exibição

3. **Sincronização Bidirecional:**

   - Função `sync_processes_cases()` no core mantém sincronização
   - Quando processo é salvo, atualiza referências nos casos
   - Quando caso é atualizado, reflete nos processos vinculados

4. **Visualização:**
   - Tabela mostra casos vinculados na coluna "Casos Vinculados"
   - Página `/processos-por-caso` agrupa processos por casos

### 3.4 Integração com Outros Módulos

#### Prazos

- ❌ **Não há integração direta** com módulo de prazos
- Processos têm campo `data_abertura` mas não há vínculo direto com prazos

#### Entregáveis

- ❌ **Não há integração direta** com módulo de entregáveis
- Não há campo `entregaveis` ou similar nos processos

#### Casos

- ✅ **Integração completa** (ver seção 3.3)

#### Pessoas (Clientes e Partes Contrárias)

- ✅ **Integração completa**
- Campo `clients` vincula clientes
- Campo `opposing_parties` vincula partes contrárias
- Campo `other_parties` vincula outros envolvidos
- Busca por `nome_exibicao` para exibição padronizada

#### Protocolos

- ✅ **Integração interna** - Protocolos são gerenciados dentro do processo
- Campo `protocols` armazena lista de protocolos
- Modal dedicado `modal_protocolo.py` para gestão

#### Acompanhamentos de Terceiros

- ✅ **Integração** - Exibidos na mesma visualização de processos
- Coleção separada `third_party_monitoring` mas aparece na tabela de processos

### 3.5 Funcionalidades Especiais

1. **Hierarquia de Processos**

   - Suporte a processos pais/filhos/netos via `parent_ids`
   - Campo `depth` indica nível hierárquico
   - Visualização indentada de desdobramentos

2. **Auto-Save**

   - Campos de texto longo salvam automaticamente a cada 30 segundos
   - Indicador visual de status (Salvando... / Salvo às HH:MM / Erro)
   - Implementado em `auto_save.py`

3. **Senhas Criptografadas**

   - Subcoleção `senhas_processo` armazena senhas criptografadas
   - Criptografia via `password_security.py`
   - Aba dedicada no modal para gestão de senhas

4. **Processos Futuros**

   - Modal separado `modal_processo_futuro.py` para processos futuros/previstos
   - Tipo especial `process_type='Futuro'`

5. **Cenários**

   - Gestão de cenários com tipo (🟢 Positivo, ⚪ Neutro, 🔴 Negativo)
   - Campos: chance, impacto, status, observações

6. **Busca com Cache**
   - Sistema de cache no core com TTL de 5 minutos
   - Thread-safe com locks para evitar múltiplas queries simultâneas

---

## 4. VOLUME DE DADOS

### 4.1 Processos no Schmidmeier

**Total:** **107 processos** na coleção `processes`

**Fonte:** Query direta no Firestore executada em 2024-12-XX

**Observações:**

- Inclui processos normais
- Inclui acompanhamentos de terceiros (coleção separada)
- Exclui processos com `isDeleted=True` (soft delete)

### 4.2 Processos na Visão Geral

**Total:** **0 processos** na coleção `visao_geral_escritorio_processos`

**Status:** Coleção existe mas está vazia - módulo ainda não implementado

---

## RESUMO EXECUTIVO

### SCHMIDMEIER ✅

- **Status:** Completamente funcional
- **Arquivos:** ~20 arquivos organizados em estrutura modular
- **Funcionalidades:** CRUD completo, filtros, hierarquia, vinculação com casos, auto-save, senhas, protocolos, cenários
- **Dados:** 107 processos cadastrados
- **Coleção:** `processes`

### VISÃO GERAL ❌

- **Status:** Apenas placeholder
- **Arquivos:** 1 arquivo (`processos.py` com tela de "em desenvolvimento")
- **Funcionalidades:** Nenhuma implementada
- **Dados:** 0 processos (coleção existe mas vazia)
- **Coleção:** `visao_geral_escritorio_processos`

### PRÓXIMOS PASSOS SUGERIDOS

1. **Replicar estrutura do Schmidmeier** para Visão Geral
2. **Adaptar funções do core** para usar workspace-aware collections
3. **Migrar dados** se necessário (caso haja processos a migrar)
4. **Testar isolamento** de dados entre workspaces
5. **Implementar visualização** na Visão Geral

---

**Relatório gerado automaticamente pela investigação do código**



