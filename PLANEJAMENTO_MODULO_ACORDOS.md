# PLANEJAMENTO - MÓDULO DE ACORDOS

## 📋 VISÃO GERAL

Módulo completo para gerenciamento de **Acordos** com **Cláusulas** e **Prazos**, seguindo os padrões arquiteturais do projeto (casos, processos, pessoas).

---

## 🏗️ ESTRUTURA DE ARQUIVOS

```
mini_erp/pages/acordos/
├── __init__.py                    # Exporta módulo principal
├── acordos_page.py                # Página principal (rota /acordos)
├── models.py                      # Constantes, tipos, opções, schemas
├── database.py                    # Operações CRUD no Firestore
├── business_logic.py              # Lógica de negócio e regras
├── validators.py                  # Validações de campos obrigatórios
├── ui_components.py               # Componentes reutilizáveis de UI
├── ui_dialogs.py                  # Modais e diálogos
└── ui_tables.py                   # Tabelas e visualizações
```

**Total: 9 arquivos**

---

## 📊 ESTRUTURA DE DADOS

### Acordo (Agreement)

```python
{
    '_id': str,                    # ID único (gerado automaticamente)
    'title': str,                  # OBRIGATÓRIO - Título do acordo
    'celebration_date': str,       # OBRIGATÓRIO - Data de celebração (DD/MM/AAAA)
    'parties': List[str],          # OBRIGATÓRIO - Lista de IDs de clientes/partes (mínimo 1)
    'clauses': List[ClauseDict],   # Lista de cláusulas vinculadas
    'deadlines': List[DeadlineDict], # Lista de prazos vinculados (opcional)
    'status': str,                 # Status do acordo
    'observations': str,           # Observações gerais
    'created_at': str,             # Data de criação (ISO format)
    'updated_at': str,             # Data última atualização (ISO format)
    'created_by': str,             # ID do usuário criador
    'updated_by': str              # ID do usuário que atualizou
}
```

### Cláusula (Clause)

```python
{
    'id': str,                     # ID único (gerado automaticamente)
    'type': str,                   # OBRIGATÓRIO - Tipo da cláusula
    'title': str,                  # OBRIGATÓRIO - Título da cláusula
    'status': str,                 # OBRIGATÓRIO - Status da cláusula
    'content': str,                # Conteúdo/texto da cláusula
    'order': int,                  # Ordem de exibição
    'observations': str            # Observações específicas
}
```

### Prazo (Deadline)

```python
{
    'id': str,                     # ID único (gerado automaticamente)
    'security_deadline': str,      # OPCIONAL - Prazo de Segurança (DD/MM/AAAA)
    'fatal_deadline': str,         # OPCIONAL - Prazo Fatal (DD/MM/AAAA)
    'description': str,            # Descrição do prazo
    'status': str,                 # Status do prazo (pendente, cumprido, vencido)
    'observations': str            # Observações
}
```

---

## ✅ VALIDAÇÕES E REGRAS

### Acordo - Campos Obrigatórios

1. **Título** (`title`)
   - Não pode ser vazio
   - Mínimo 3 caracteres
   - Mensagem: "O título do acordo é obrigatório e deve ter pelo menos 3 caracteres."

2. **Data de Celebração** (`celebration_date`)
   - Formato: DD/MM/AAAA
   - Data válida (não pode ser futura se necessário)
   - Mensagem: "A data de celebração é obrigatória e deve estar no formato DD/MM/AAAA."

3. **Partes/Clientes** (`parties`)
   - Lista não pode estar vazia
   - Mínimo 1 parte/cliente
   - Mensagem: "O acordo deve ter pelo menos uma parte/cliente vinculado."

### Cláusula - Campos Obrigatórios

1. **Tipo** (`type`)
   - Deve ser uma das opções válidas
   - Mensagem: "O tipo da cláusula é obrigatório."

2. **Título** (`title`)
   - Não pode ser vazio
   - Mínimo 3 caracteres
   - Mensagem: "O título da cláusula é obrigatório e deve ter pelo menos 3 caracteres."

3. **Status** (`status`)
   - Deve ser uma das opções válidas
   - Mensagem: "O status da cláusula é obrigatório."

### Prazos - Validações Condicionais

1. **Prazo de Segurança** (`security_deadline`)
   - Se fornecido: formato DD/MM/AAAA válido
   - Deve ser anterior ao Prazo Fatal (se ambos existirem)
   - Mensagem: "O prazo de segurança deve estar no formato DD/MM/AAAA e ser anterior ao prazo fatal."

2. **Prazo Fatal** (`fatal_deadline`)
   - Se fornecido: formato DD/MM/AAAA válido
   - Deve ser posterior ao Prazo de Segurança (se ambos existirem)
   - Mensagem: "O prazo fatal deve estar no formato DD/MM/AAAA e ser posterior ao prazo de segurança."

---

## 📁 DETALHAMENTO DOS ARQUIVOS

### 1. `__init__.py`
```python
"""
Módulo de Acordos - Exportações principais
"""
from .acordos_page import acordos

__all__ = ['acordos']
```

### 2. `models.py`
**Conteúdo:**
- Constantes de status de acordo
- Opções de tipos de cláusula
- Opções de status de cláusula
- Opções de status de prazo
- TypedDict para Agreement, Clause, Deadline
- Configuração de colunas da tabela
- CSS customizado

**Constantes principais:**
```python
AGREEMENT_STATUS_OPTIONS = [
    'Em negociação',
    'Assinado',
    'Em cumprimento',
    'Cumprido',
    'Encerrado',
    'Cancelado'
]

CLAUSE_TYPE_OPTIONS = [
    'Obrigação',
    'Direito',
    'Condição',
    'Prazo',
    'Multa',
    'Rescisão',
    'Confidencialidade',
    'Outro'
]

CLAUSE_STATUS_OPTIONS = [
    'Pendente',
    'Em andamento',
    'Cumprida',
    'Não cumprida',
    'Suspensa'
]

DEADLINE_STATUS_OPTIONS = [
    'Pendente',
    'Cumprido',
    'Vencido',
    'Cancelado'
]
```

### 3. `validators.py`
**Funções:**
- `validate_agreement(data: Dict) -> Tuple[bool, Optional[str]]`
- `validate_clause(data: Dict) -> Tuple[bool, Optional[str]]`
- `validate_deadline(data: Dict) -> Tuple[bool, Optional[str]]`
- `validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]`
- `validate_date_range(security: str, fatal: str) -> Tuple[bool, Optional[str]]`
- `validate_parties_list(parties: List[str]) -> Tuple[bool, Optional[str]]`

### 4. `database.py`
**Funções:**
- `get_all_agreements() -> List[Dict]`
- `get_agreement_by_id(agreement_id: str) -> Optional[Dict]`
- `create_agreement(agreement_data: Dict) -> str`
- `update_agreement(agreement_id: str, agreement_data: Dict) -> bool`
- `delete_agreement(agreement_id: str) -> bool`
- `add_clause_to_agreement(agreement_id: str, clause_data: Dict) -> str`
- `update_clause(agreement_id: str, clause_id: str, clause_data: Dict) -> bool`
- `delete_clause(agreement_id: str, clause_id: str) -> bool`
- `add_deadline_to_agreement(agreement_id: str, deadline_data: Dict) -> str`
- `update_deadline(agreement_id: str, deadline_id: str, deadline_data: Dict) -> bool`
- `delete_deadline(agreement_id: str, deadline_id: str) -> bool`

### 5. `business_logic.py`
**Funções:**
- `format_agreement_display(agreement: Dict) -> Dict`
- `get_agreement_parties_names(agreement: Dict) -> List[str]`
- `count_clauses_by_status(agreement: Dict) -> Dict[str, int]`
- `get_upcoming_deadlines(agreement: Dict, days: int = 30) -> List[Dict]`
- `check_deadline_status(deadline: Dict) -> str`
- `calculate_agreement_progress(agreement: Dict) -> float`

### 6. `ui_components.py`
**Componentes:**
- `AgreementCard(agreement: Dict) -> ui.card`
- `ClauseItem(clause: Dict, on_edit, on_delete) -> ui.card`
- `DeadlineItem(deadline: Dict, on_edit, on_delete) -> ui.card`
- `PartiesSelector(selected: List[str], on_change) -> ui.select`
- `StatusBadge(status: str) -> ui.badge`

### 7. `ui_dialogs.py`
**Diálogos:**
- `AgreementDialog(mode: 'create' | 'edit', agreement_data: Optional[Dict])`
- `ClauseDialog(mode: 'create' | 'edit', clause_data: Optional[Dict])`
- `DeadlineDialog(mode: 'create' | 'edit', deadline_data: Optional[Dict])`
- `DeleteConfirmationDialog(item_type: str, item_name: str, on_confirm)`

### 8. `ui_tables.py`
**Tabelas:**
- `AgreementsTable(agreements: List[Dict], on_select, on_edit, on_delete)`
- `ClausesTable(clauses: List[Dict], on_edit, on_delete)`
- `DeadlinesTable(deadlines: List[Dict], on_edit, on_delete)`

### 9. `acordos_page.py`
**Estrutura:**
- Rota: `/acordos`
- Layout principal com sidebar
- Lista de acordos (tabela/cards)
- Modal de detalhes do acordo
- Abas: Informações, Cláusulas, Prazos
- Filtros: status, partes, data
- Busca por título

---

## 🔄 FLUXOS PRINCIPAIS

### 1. Criar Acordo
```
Usuário clica "Novo Acordo"
  → Abre AgreementDialog (mode='create')
  → Preenche: título, data, partes
  → Validação (validators.validate_agreement)
  → Se válido: database.create_agreement
  → Atualiza lista
  → Notificação de sucesso
```

### 2. Adicionar Cláusula
```
Usuário seleciona acordo
  → Aba "Cláusulas"
  → Clica "Adicionar Cláusula"
  → Abre ClauseDialog (mode='create')
  → Preenche: tipo, título, status
  → Validação (validators.validate_clause)
  → Se válido: database.add_clause_to_agreement
  → Atualiza lista de cláusulas
```

### 3. Adicionar Prazo
```
Usuário seleciona acordo
  → Aba "Prazos"
  → Clica "Adicionar Prazo"
  → Abre DeadlineDialog (mode='create')
  → Preenche: prazo segurança (opcional), prazo fatal (opcional)
  → Validação (validators.validate_deadline)
  → Se válido: database.add_deadline_to_agreement
  → Atualiza lista de prazos
```

### 4. Editar Acordo
```
Usuário clica "Editar" em um acordo
  → Abre AgreementDialog (mode='edit', agreement_data)
  → Carrega dados existentes
  → Usuário modifica
  → Validação
  → Se válido: database.update_agreement
  → Atualiza lista
```

### 5. Excluir Acordo
```
Usuário clica "Excluir"
  → Abre DeleteConfirmationDialog
  → Usuário confirma
  → database.delete_agreement
  → Remove da lista
  → Notificação
```

---

## 🔗 DEPENDÊNCIAS

### Módulos do Projeto
- `mini_erp.core` - Funções de acesso a dados (get_clients_list, etc.)
- `mini_erp.firebase_config` - Conexão Firestore
- `mini_erp.auth` - Autenticação (get_current_user)
- `mini_erp.pages.pessoas.models` - Tipos de pessoa (se necessário)

### Bibliotecas Externas
- `nicegui` - Framework UI
- `firebase_admin` - Firestore
- `datetime` - Manipulação de datas
- `uuid` - Geração de IDs
- `typing` - Type hints

---

## 📝 INTEGRAÇÃO COM O SISTEMA

### 1. Registro da Rota
**Arquivo:** `mini_erp/pages/__init__.py`
```python
from .acordos import acordos
```

**Arquivo:** `mini_erp/main.py` (ou onde as rotas são registradas)
```python
from .pages.acordos import acordos
# Rota já registrada automaticamente via @ui.page('/acordos')
```

### 2. Menu de Navegação
Adicionar item no menu principal:
```python
ui.menu_item('Acordos', icon='gavel', route='/acordos')
```

### 3. Coleção Firestore
- **Nome:** `agreements`
- **Estrutura:** Documentos com subcoleções ou arrays aninhados
- **Índices:** `title`, `celebration_date`, `status`, `parties[]`

---

## 🎨 INTERFACE (UI)

### Layout Principal
- **Header:** Título "Acordos" + botão "Novo Acordo"
- **Filtros:** Status, Partes, Período (data)
- **Busca:** Campo de pesquisa por título
- **Lista:** Tabela ou cards com acordos
- **Colunas da Tabela:**
  - Título
  - Data Celebração
  - Partes (lista)
  - Status (badge colorido)
  - Cláusulas (contador)
  - Prazos (contador)
  - Ações (editar, excluir)

### Modal de Detalhes
- **Aba Informações:**
  - Título, data, partes
  - Status, observações
  - Botões: Editar, Excluir
  
- **Aba Cláusulas:**
  - Lista de cláusulas
  - Botão "Adicionar Cláusula"
  - Para cada cláusula: tipo, título, status, ações
  
- **Aba Prazos:**
  - Lista de prazos
  - Botão "Adicionar Prazo"
  - Para cada prazo: descrição, prazos, status, ações

### Cores e Status
- **Status Acordo:**
  - Em negociação: laranja
  - Assinado: azul
  - Em cumprimento: verde claro
  - Cumprido: verde
  - Encerrado: cinza
  - Cancelado: vermelho

---

## 📊 RELATÓRIO FINAL

### Estrutura Completa em Árvore
```
mini_erp/pages/acordos/
├── __init__.py                    (16 linhas)
├── acordos_page.py                (450 linhas)
├── models.py                      (280 linhas)
├── database.py                    (320 linhas)
├── business_logic.py              (180 linhas)
├── validators.py                  (200 linhas)
├── ui_components.py               (250 linhas)
├── ui_dialogs.py                  (380 linhas)
└── ui_tables.py                   (220 linhas)
```

**Total de arquivos:** 9  
**Total de pastas:** 1 (acordos/)  
**Total estimado de linhas:** ~2.300 linhas

### Fluxos Principais Documentados
✅ Criar Acordo  
✅ Editar Acordo  
✅ Excluir Acordo  
✅ Adicionar Cláusula  
✅ Editar Cláusula  
✅ Excluir Cláusula  
✅ Adicionar Prazo  
✅ Editar Prazo  
✅ Excluir Prazo  
✅ Validações completas  
✅ Integração com Firestore  

### Dependências Mapeadas
✅ Módulos internos identificados  
✅ Bibliotecas externas listadas  
✅ Integração com core.py definida  
✅ Estrutura Firestore planejada  

### Pronto para Criação Passo a Passo
✅ Estrutura de arquivos definida  
✅ Modelos de dados especificados  
✅ Validações detalhadas  
✅ Funções de banco planejadas  
✅ Componentes UI descritos  
✅ Fluxos documentados  
✅ Padrões do projeto seguidos  

---

## 🚀 PRÓXIMOS PASSOS (ORDEM DE IMPLEMENTAÇÃO)

1. **Fase 1 - Base**
   - Criar estrutura de pastas
   - `models.py` com constantes e tipos
   - `validators.py` com todas as validações

2. **Fase 2 - Banco de Dados**
   - `database.py` com operações CRUD
   - Testes de conexão Firestore

3. **Fase 3 - Lógica de Negócio**
   - `business_logic.py` com funções auxiliares

4. **Fase 4 - Componentes UI**
   - `ui_components.py` com componentes básicos
   - `ui_tables.py` com tabelas

5. **Fase 5 - Diálogos**
   - `ui_dialogs.py` com modais completos

6. **Fase 6 - Página Principal**
   - `acordos_page.py` integrando tudo
   - Filtros e busca

7. **Fase 7 - Integração**
   - Registrar rota no sistema
   - Adicionar ao menu
   - Testes finais

---

## 📌 OBSERVAÇÕES IMPORTANTES

1. **Validações são obrigatórias** antes de salvar qualquer dado
2. **Mensagens de erro** devem ser claras e em português
3. **Datas** sempre no formato DD/MM/AAAA para exibição
4. **IDs** gerados automaticamente com UUID
5. **Soft delete** pode ser implementado (campo `isDeleted`)
6. **Auditoria** com `created_at`, `updated_at`, `created_by`, `updated_by`
7. **Performance** usar cache quando apropriado
8. **Responsividade** UI deve funcionar em diferentes tamanhos de tela

---

**Documento criado em:** 2025-01-XX  
**Status:** Planejamento completo - Pronto para implementação




