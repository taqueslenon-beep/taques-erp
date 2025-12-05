# Documentação Técnica: Clique em Título para Editar Acompanhamento

## Visão Geral

Sistema permite que usuário clique no título de um acompanhamento de terceiro na tabela de processos para abrir modal de edição preenchido com todos os dados.

---

## Arquitetura

### Componentes Envolvidos

1. **Tabela de Processos** (`processos_page.py`)

   - Renderiza lista de processos e acompanhamentos
   - Detecta clique no título
   - Identifica tipo de registro

2. **Handler de Clique** (`handle_title_click`)

   - Captura evento de clique
   - Verifica tipo de registro
   - Decide qual modal abrir

3. **Banco de Dados** (`database.py`)

   - Função `obter_acompanhamento_por_id()`
   - Busca dados do Firestore

4. **Modal de Acompanhamento** (`third_party_monitoring_dialog.py`)
   - Função `open_modal(monitoring_id=...)`
   - Carrega e exibe dados
   - Permite edição

---

## Fluxo de Dados

### 1. Evento de Clique

```
Usuário clica no título
    ↓
NiceGUI dispara evento 'titleClick'
    ↓
handle_title_click(e) é chamado
    ↓
Extrai dados da linha clicada
```

### 2. Detecção de Tipo

```python
# Verifica campo is_third_party_monitoring
is_third_party = clicked_row.get('is_third_party_monitoring', False)

if is_third_party:
    # É acompanhamento → buscar e abrir modal de acompanhamento
else:
    # É processo → abrir modal de processo
```

### 3. Busca de Dados

```python
# Busca no Firestore
acompanhamento = obter_acompanhamento_por_id(row_id)

# Validação
if not acompanhamento:
    # Mostra erro: não encontrado
    return
```

### 4. Abertura do Modal

```python
# Abre modal em modo edição
open_third_party_modal(monitoring_id=row_id)

# Internamente:
# - Busca dados do acompanhamento
# - Pré-preenche campos
# - Abre modal
```

### 5. Carregamento de Dados

```python
# Para cada campo:
title_input.value = p.get('process_title') or p.get('title', '')
number_input.value = p.get('process_number') or p.get('number', '')
# ... todos os outros campos
```

---

## Estrutura de Dados

### Row Data na Tabela

```python
row_data = {
    '_id': 'id_do_acompanhamento',
    'title': 'Acompanhamento de Terceiro',
    'is_third_party_monitoring': True,  # ← Marca como acompanhamento
    # ... outros campos
}
```

### Dados do Acompanhamento no Firestore

```python
acompanhamento = {
    '_id': 'id_do_documento',
    'process_title': 'Título do acompanhamento',
    'process_number': '1234567-89.2023.4.01.0001',
    'status': 'ativo',
    'tipo_de_acompanhamento': 'Acompanhamento de Sócio',
    'pessoa_ou_entidade_acompanhada': 'Jandir José Leismann',
    # ... todos os outros campos
}
```

---

## Funções Principais

### 1. `handle_title_click(e)` - `processos_page.py`

**Responsabilidade:** Captura clique e decide qual modal abrir.

**Entrada:**

- `e`: Evento do NiceGUI com `e.args` contendo dados da linha

**Processamento:**

1. Extrai `_id` da linha
2. Verifica `is_third_party_monitoring`
3. Se True → busca e abre modal de acompanhamento
4. Se False → abre modal de processo

**Saída:**

- Abre modal apropriado
- Mostra notificação em caso de erro

### 2. `obter_acompanhamento_por_id(doc_id)` - `database.py`

**Responsabilidade:** Busca acompanhamento no Firestore.

**Entrada:**

- `doc_id`: ID do documento no Firestore

**Processamento:**

1. Conecta ao Firestore
2. Busca na coleção `third_party_monitoring`
3. Retorna dados do documento

**Saída:**

- Dicionário com dados do acompanhamento ou `None`

### 3. `open_modal(monitoring_id=None)` - `third_party_monitoring_dialog.py`

**Responsabilidade:** Abre modal em modo criar ou editar.

**Entrada:**

- `monitoring_id`: ID do acompanhamento (opcional)

**Processamento:**

1. Se `monitoring_id` fornecido:
   - Busca dados no Firestore
   - Pré-preenche campos
   - Abre em modo edição
2. Se `None`:
   - Limpa formulário
   - Abre em modo criar

**Saída:**

- Modal aberto e pronto para uso

---

## Mapeamento de Campos

### Campos Básicos

| Campo no Firestore                   | Campo no Modal              | Notas                    |
| ------------------------------------ | --------------------------- | ------------------------ |
| `process_title` ou `title`           | `title_input.value`         | Título do acompanhamento |
| `process_number` ou `number`         | `number_input.value`        | Número do processo       |
| `link_do_processo` ou `link`         | `link_input.value`          | Link externo             |
| `tipo_de_processo` ou `process_type` | `type_select.value`         | Tipo (Existente/Futuro)  |
| `data_de_abertura` ou `start_date`   | `data_abertura_input.value` | Data de abertura         |

### Partes Envolvidas

| Campo no Firestore                     | Campo no Modal               | Notas             |
| -------------------------------------- | ---------------------------- | ----------------- |
| `clients` ou `parte_ativa`             | `state['selected_clients']`  | Parte ativa       |
| `opposing_parties` ou `parte_passiva`  | `state['selected_opposing']` | Parte passiva     |
| `other_parties` ou `outros_envolvidos` | `state['selected_others']`   | Outros envolvidos |
| `cases`                                | `state['selected_cases']`    | Casos vinculados  |

### Campos Específicos de Acompanhamento

| Campo no Firestore               | Campo no Modal                      | Status   |
| -------------------------------- | ----------------------------------- | -------- |
| `tipo_de_acompanhamento`         | `tipo_acompanhamento_select.value`  | Opcional |
| `pessoa_ou_entidade_acompanhada` | `third_party_name_input.value`      | Opcional |
| `nivel_de_envolvimento`          | `involvement_level_select.value`    | Opcional |
| `intensidade_de_monitoramento`   | `monitoring_intensity_select.value` | Opcional |
| `frequencia_de_check_in`         | `checkin_frequency_select.value`    | Opcional |

**Nota:** Campos específicos são opcionais e podem não existir no modal ainda. O código verifica antes de usar.

---

## Tratamento de Erros

### Erro 1: Acompanhamento Não Encontrado

**Causa:** Documento foi deletado ou ID incorreto.

**Tratamento:**

```python
if not acompanhamento:
    ui.notify('Acompanhamento não encontrado. Pode ter sido deletado.', type='negative')
    return
```

### Erro 2: Erro ao Buscar no Firestore

**Causa:** Problema de conexão ou permissões.

**Tratamento:**

```python
try:
    acompanhamento = obter_acompanhamento_por_id(row_id)
except Exception as ex:
    ui.notify(f'Erro ao abrir acompanhamento: {str(ex)}', type='negative')
    traceback.print_exc()
```

### Erro 3: Campos Específicos Não Existem

**Causa:** Campos podem não estar implementados ainda.

**Tratamento:**

```python
try:
    if 'tipo_acompanhamento_select' in locals():
        tipo_acompanhamento_select.value = ...
except Exception as e:
    # Continua sem esses campos
    print(f"Campos específicos não encontrados: {e}")
```

---

## Logs de Debug

### Logs Implementados

```
[TITLE_CLICK] Abrindo modal de edição para acompanhamento ID: {id}
[TITLE_CLICK] ✓ Modal de acompanhamento aberto com sucesso
[TITLE_CLICK] ❌ Acompanhamento não encontrado: {id}

[OPEN_MODAL] Carregando acompanhamento ID: {id}
[OPEN_MODAL] Erro ao carregar acompanhamento: {erro}
```

### Como Usar

1. Abrir console do navegador (F12)
2. Verificar logs ao clicar no título
3. Identificar problemas de busca ou carregamento

---

## Testes

### Teste 1: Clique Funcional

1. Abrir página de processos
2. Filtrar por acompanhamentos (clicar no card do painel)
3. Clicar no título de um acompanhamento
4. **Esperado:** Modal abre com dados preenchidos

### Teste 2: Edição Funcional

1. Clicar no título de um acompanhamento
2. Modal abre preenchido
3. Modificar algum campo
4. Clicar em "SALVAR"
5. **Esperado:** Dados são atualizados e tabela recarrega

### Teste 3: Erro de Acompanhamento Não Encontrado

1. Deletar um acompanhamento
2. Tentar clicar no título (se ainda aparecer)
3. **Esperado:** Mensagem de erro clara

### Teste 4: Detecção de Tipo

1. Tabela com processos e acompanhamentos misturados
2. Clicar no título de processo normal
3. **Esperado:** Abre modal de processo
4. Clicar no título de acompanhamento
5. **Esperado:** Abre modal de acompanhamento

---

## Compatibilidade

### Schemas de Dados

O sistema suporta múltiplos nomes de campos para compatibilidade:

**Título:**

- `process_title` (novo)
- `title` (compatibilidade)

**Número:**

- `process_number` (novo)
- `number` (compatibilidade)

**Partes:**

- `parte_ativa` / `clients` (ambos suportados)
- `parte_passiva` / `opposing_parties` (ambos suportados)

---

## Performance

### Otimizações

1. **Busca Direta:** Usa ID direto, não busca toda a lista
2. **Carregamento Lazy:** Campos são carregados apenas quando necessário
3. **Cache:** Firestore usa cache automático

### Métricas Esperadas

- Tempo de clique → modal aberto: < 500ms
- Tempo de busca no Firestore: < 200ms
- Tempo de preenchimento de campos: < 100ms

---

## Manutenção

### Adicionar Novo Campo

1. Adicionar campo no formulário do modal
2. Adicionar mapeamento em `open_modal()`:
   ```python
   novo_campo.value = p.get('novo_campo', '')
   ```
3. Adicionar em `clear_form()`:
   ```python
   novo_campo.value = ''
   ```

### Modificar Validação

1. Editar função `validate_third_party_monitoring()`
2. Adicionar regras necessárias
3. Testar com dados válidos e inválidos

---

## Troubleshooting

### Problema: Modal não abre

**Solução:**

1. Verificar logs: `[TITLE_CLICK]`
2. Verificar se `is_third_party_monitoring` está marcado na row
3. Verificar se ID está correto

### Problema: Campos não são preenchidos

**Solução:**

1. Verificar logs: `[OPEN_MODAL]`
2. Verificar se dados foram buscados corretamente
3. Verificar nomes dos campos no Firestore

### Problema: Erro ao salvar

**Solução:**

1. Verificar validações
2. Verificar permissões do Firestore
3. Verificar logs do servidor

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0




