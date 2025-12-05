# CHANGELOG - Clique em Título para Editar Acompanhamento

## [1.0.0] - 2025-01-XX

### ✨ Funcionalidades Adicionadas

#### Clique no Título para Abrir Modal de Edição

- **Funcionalidade:** Ao clicar no título de um acompanhamento na tabela, abre modal de edição
- **Comportamento:** Idêntico ao clique em processo normal
- **Arquivo:** `mini_erp/pages/processos/processos_page.py`

#### Modal de Acompanhamento Aceita ID Direto

- **Funcionalidade:** Modal pode ser aberto diretamente com `monitoring_id` do Firestore
- **Parâmetro:** `open_modal(monitoring_id=...)` além de `process_idx`
- **Arquivo:** `mini_erp/pages/processos/third_party_monitoring_dialog.py`

#### Detecção Automática de Tipo

- **Funcionalidade:** Handler detecta automaticamente se é processo ou acompanhamento
- **Campo:** Verifica `is_third_party_monitoring` na row
- **Ação:** Abre modal correto baseado no tipo

### 🔧 Mudanças Técnicas

#### `mini_erp/pages/processos/processos_page.py`

**Função `handle_title_click()` atualizada:**

```python
def handle_title_click(e):
    clicked_row = e.args
    row_id = clicked_row['_id']

    # Verifica se é acompanhamento
    is_third_party = clicked_row.get('is_third_party_monitoring', False)

    if is_third_party:
        # Busca e abre modal de acompanhamento
        acompanhamento = obter_acompanhamento_por_id(row_id)
        open_third_party_modal(monitoring_id=row_id)
    else:
        # Abre modal de processo normal
        open_process_modal(idx)
```

**Melhorias:**

- Detecção automática de tipo de registro
- Tratamento de erros com mensagens claras
- Logs de debug para facilitar diagnóstico

#### `mini_erp/pages/processos/third_party_monitoring_dialog.py`

**Função `open_modal()` atualizada:**

```python
def open_modal(process_idx=None, monitoring_id=None):
    """
    Abre modal em modo criar ou editar.

    Args:
        process_idx: Índice na lista (compatibilidade)
        monitoring_id: ID do acompanhamento no Firestore (prioridade)
    """
    if monitoring_id:
        # Busca dados diretamente do Firestore
        acompanhamento = obter_acompanhamento_por_id(monitoring_id)
        # Carrega todos os campos
        # Abre modal em modo edição
```

**Melhorias:**

- Aceita `monitoring_id` como parâmetro
- Busca dados diretamente do Firestore
- Pré-preenche todos os campos do formulário
- Adapta nomes de campos (compatibilidade com diferentes schemas)
- Tratamento de erros robusto

### 📝 Validações e Tratamento de Erros

#### Validações Implementadas

- Verifica se acompanhamento existe antes de abrir modal
- Verifica se dados foram carregados corretamente
- Mensagens de erro claras em português

#### Tratamento de Erros

```python
try:
    acompanhamento = obter_acompanhamento_por_id(row_id)
    if acompanhamento:
        open_third_party_modal(monitoring_id=row_id)
    else:
        ui.notify('Acompanhamento não encontrado. Pode ter sido deletado.', type='negative')
except Exception as ex:
    ui.notify(f'Erro ao abrir acompanhamento: {str(ex)}', type='negative')
```

### 🎯 Fluxo Completo

1. **Usuário clica no título:**

   - Título na tabela é clicável
   - Handler captura evento

2. **Sistema detecta tipo:**

   - Verifica campo `is_third_party_monitoring`
   - Se True → é acompanhamento
   - Se False → é processo normal

3. **Sistema busca dados:**

   - Busca acompanhamento no Firestore
   - Usa função `obter_acompanhamento_por_id()`

4. **Sistema abre modal:**

   - Modal abre em modo edição
   - Título muda para "EDITAR ACOMPANHAMENTO DE TERCEIRO"
   - Botão "SALVAR" em vez de "CRIAR"

5. **Modal pré-preenchido:**

   - Todos os campos são preenchidos
   - Dados são exibidos nas abas corretas
   - Usuário pode editar qualquer campo

6. **Usuário salva:**
   - Clica em "SALVAR"
   - Validações são executadas
   - Dados são atualizados no Firestore
   - Tabela é recarregada

### 📋 Campos Carregados

#### Dados Básicos

- Título do processo
- Número do processo
- Link do processo
- Tipo de processo
- Data de abertura
- Tipo de acompanhamento (se existir)
- Pessoa/Entidade acompanhada (se existir)
- Nível de envolvimento (se existir)
- Intensidade de monitoramento (se existir)
- Frequência de check-in (se existir)

#### Partes Envolvidas

- Parte Ativa (clientes)
- Parte Passiva (parte contrária)
- Outros Envolvidos

#### Dados Jurídicos

- Sistema processual
- Núcleo
- Área
- Status
- Resultado (se aplicável)

#### Relatório

- Fatos do processo
- Linha do tempo
- Documentos relevantes

#### Estratégia

- Objetivos
- Teses jurídicas
- Observações

#### Cenários e Protocolos

- Lista de cenários
- Lista de protocolos

#### Acesso

- Acesso do advogado (solicitado/concedido)
- Acesso dos técnicos (solicitado/concedido)
- Acesso do cliente (solicitado/concedido)
- Comentários de cada acesso

### 🔄 Compatibilidade

#### Campos com Nomes Diferentes

O sistema adapta automaticamente campos com nomes diferentes:

- `process_title` ou `title` → título
- `process_number` ou `number` → número
- `link_do_processo` ou `link` → link
- `data_de_abertura` ou `start_date` → data
- `clients` ou `parte_ativa` → parte ativa
- `opposing_parties` ou `parte_passiva` → parte passiva

### 📊 Logs de Debug

Logs adicionados para facilitar diagnóstico:

- `[TITLE_CLICK]` - Ao clicar no título
- `[OPEN_MODAL]` - Ao abrir modal
- Logs de sucesso e erro em cada etapa

### 🎨 Interface

#### Feedback Visual

- Título é clicável (cursor pointer)
- Notificações claras em caso de erro
- Modal abre suavemente

#### Responsividade

- Funciona em desktop e mobile
- Modal adaptável ao tamanho da tela

### 📚 Arquivos Modificados

1. `mini_erp/pages/processos/processos_page.py`

   - Função `handle_title_click()` adaptada
   - Detecção de tipo de registro
   - Integração com modal de acompanhamentos

2. `mini_erp/pages/processos/third_party_monitoring_dialog.py`
   - Função `open_modal()` atualizada
   - Suporte a `monitoring_id`
   - Carregamento de dados do Firestore
   - Pré-preenchimento de campos

### ✅ Checklist de Funcionalidades

- [x] Clique no título detecta tipo de registro
- [x] Busca dados do acompanhamento por ID
- [x] Abre modal em modo edição
- [x] Pré-preenche todos os campos
- [x] Título do modal muda para "EDITAR"
- [x] Botão "SALVAR" aparece (não "CRIAR")
- [x] Tratamento de erros robusto
- [x] Mensagens em português
- [x] Logs de debug
- [x] Compatibilidade com diferentes schemas

### 🔮 Próximos Passos (Opcional)

- [ ] Adicionar validação se modal já está aberto
- [ ] Adicionar confirmação antes de fechar sem salvar
- [ ] Melhorar feedback visual ao carregar dados

---

**Versão:** 1.0.0  
**Data:** 2025-01-XX  
**Autor:** Sistema ERP




