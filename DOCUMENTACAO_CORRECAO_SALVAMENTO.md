# Documentação Técnica: Correção do Bug de Salvamento de Acompanhamentos

## Causa Raiz do Problema

### Problema Identificado

**Sintoma:** Acompanhamentos de terceiros eram salvos no Firestore, mas o título não aparecia na tabela de processos.

**Causa Raiz:** A função `build_third_party_monitoring_data()` recebia o parâmetro `title` mas **não incluía esse campo no dicionário retornado**.

### Análise do Código Original

```python
# CÓDIGO ORIGINAL (BUGADO)
def build_third_party_monitoring_data(title: str, ...):
    data = {
        'link_do_processo': ...,
        'tipo_de_processo': ...,
        # ❌ Campo 'title' NÃO estava sendo incluído!
    }
    return data
```

**Resultado:**
- Dados eram salvos no Firestore
- Campo `title` não existia no documento
- Tabela buscava `title` e não encontrava
- Título aparecia vazio ou com valor padrão

---

## Solução Implementada

### 1. Correção na Função `build_third_party_monitoring_data()`

**Arquivo:** `mini_erp/pages/processos/third_party_monitoring_dialog.py`

```python
# CÓDIGO CORRIGIDO
def build_third_party_monitoring_data(title: str, ...):
    data = {
        # ✅ TÍTULO - CRÍTICO: Agora está incluído
        'title': title or '',  # Campo principal
        'process_title': title or '',  # Compatibilidade
        'titulo': title or '',  # Compatibilidade adicional
        
        'link_do_processo': ...,
        'tipo_de_processo': ...,
        # ... outros campos
    }
    return data
```

**Benefícios:**
- Título é sempre salvo
- Múltiplos campos para compatibilidade
- Funciona com dados antigos e novos

### 2. Melhorias nas Funções de Salvamento

#### `atualizar_acompanhamento()`

**Melhorias:**
- Validação de título antes de atualizar
- Verificação se documento existe
- Logs detalhados de cada etapa
- Verificação pós-salvamento

**Código:**
```python
def atualizar_acompanhamento(doc_id: str, updates: Dict[str, Any]) -> bool:
    # Validação
    title_value = updates.get('title') or updates.get('process_title')
    if not title_value or not str(title_value).strip():
        print(f"⚠️  AVISO: Título está vazio!")
    
    # Verifica se documento existe
    doc = doc_ref.get()
    if not doc.exists:
        return False
    
    # Atualiza
    doc_ref.update(updates)
    
    # Verifica se foi salvo
    doc_after = doc_ref.get()
    title_after = doc_after.to_dict().get('title')
    print(f"Verificação: Título após salvar: '{title_after}'")
    
    return True
```

#### `criar_acompanhamento()`

**Melhorias:**
- Validação obrigatória de título
- Garantia de múltiplos campos
- Logs detalhados
- Verificação pós-salvamento

**Código:**
```python
def criar_acompanhamento(acompanhamento_data: Dict[str, Any]) -> str:
    # Validação obrigatória
    title_value = acompanhamento_data.get('title')
    if not title_value or not str(title_value).strip():
        raise ValueError("Título do acompanhamento é obrigatório")
    
    # Garante múltiplos campos
    doc_data['title'] = title_value
    doc_data['process_title'] = title_value
    
    # Salva
    doc_ref.set(doc_data)
    
    # Verifica
    doc_after = doc_ref.get()
    # ... logs de verificação
    
    return doc_id
```

### 3. Melhorias no Modal

#### Função `do_save()`

**Melhorias:**
- Logs detalhados antes de salvar
- Remoção de campos que não devem ser atualizados
- Mensagens de sucesso/erro melhoradas
- Timeout aumentado para mensagens

**Código:**
```python
def do_save():
    # Logs
    print(f"[SALVAR ACOMPANHAMENTO] Título: {title_input.value}")
    print(f"[SALVAR ACOMPANHAMENTO] Modo: {'EDITAR' if editing else 'CRIAR'}")
    
    # Constrói dados
    monitoring_data = build_third_party_monitoring_data(...)
    
    # Remove campos que não devem ser atualizados
    monitoring_data.pop('id', None)
    monitoring_data.pop('_id', None)
    
    # Salva
    if editing:
        sucesso = atualizar_acompanhamento(id, monitoring_data)
        if sucesso:
            ui.notify('✅ Acompanhamento atualizado com sucesso!', timeout=3000)
    else:
        doc_id = criar_acompanhamento(monitoring_data)
        ui.notify('✅ Acompanhamento criado com sucesso!', timeout=3000)
```

### 4. Melhorias na Busca de Título

#### Função `fetch_acompanhamentos_terceiros()`

**Melhorias:**
- Busca título em múltiplos campos
- Logs para debug
- Fallback para valor padrão

**Código:**
```python
# Busca título em múltiplos campos
title = (
    acomp.get('title') or 
    acomp.get('process_title') or 
    acomp.get('titulo') or 
    'Acompanhamento de Terceiro'  # Fallback
)

print(f"[FETCH_ACOMPANHAMENTOS] Título: '{title}'")
```

---

## Fluxo Completo Corrigido

### Criar Novo Acompanhamento

```
1. Usuário preenche formulário
   └─ Título: "Acompanhamento de Jandir"
   
2. Clica "SALVAR"
   └─ do_save() é chamado
   
3. Validação
   └─ validate_third_party_monitoring() verifica campos obrigatórios
   
4. Construção de dados
   └─ build_third_party_monitoring_data() inclui 'title'
   └─ Dados: {'title': 'Acompanhamento de Jandir', ...}
   
5. Salvamento
   └─ criar_acompanhamento() valida título
   └─ Salva no Firestore com campo 'title'
   └─ Verifica se foi salvo corretamente
   
6. Feedback
   └─ ui.notify('✅ Acompanhamento criado!')
   └─ Cache invalidado
   └─ Tabela recarregada
   
7. Exibição
   └─ fetch_acompanhamentos_terceiros() busca título
   └─ Título aparece na tabela: "Acompanhamento de Jandir"
```

### Editar Acompanhamento Existente

```
1. Usuário clica no título
   └─ Modal abre com dados pré-preenchidos
   
2. Usuário modifica título
   └─ Título: "Acompanhamento de Jandir - Atualizado"
   
3. Clica "SALVAR"
   └─ do_save() detecta modo edição
   
4. Construção de dados
   └─ build_third_party_monitoring_data() inclui novo título
   
5. Atualização
   └─ atualizar_acompanhamento() verifica se documento existe
   └─ Atualiza campo 'title' no Firestore
   └─ Verifica se foi atualizado
   
6. Feedback
   └─ ui.notify('✅ Acompanhamento atualizado!')
   └─ Cache invalidado
   └─ Tabela recarregada
   
7. Exibição
   └─ Título atualizado aparece na tabela
```

---

## Validações Implementadas

### Validação de Título

**Antes de Criar:**
```python
if not title_value or not str(title_value).strip():
    raise ValueError("Título do acompanhamento é obrigatório")
```

**Antes de Atualizar:**
```python
title_value = updates.get('title')
if not title_value or not str(title_value).strip():
    print(f"⚠️  AVISO: Título está vazio!")
    # Não bloqueia, mas avisa
```

### Validação de Documento

**Antes de Atualizar:**
```python
doc = doc_ref.get()
if not doc.exists:
    print(f"❌ Documento não existe")
    return False
```

---

## Logs de Debug

### Logs de Salvamento

```
[SALVAR ACOMPANHAMENTO] Iniciando salvamento...
[SALVAR ACOMPANHAMENTO] Modo: EDITAR
[SALVAR ACOMPANHAMENTO] Título: "Acompanhamento de Jandir"
[SALVAR ACOMPANHAMENTO] ID: abc123
[SALVAR ACOMPANHAMENTO] Dados construídos: ['title', 'process_title', ...]
[SALVAR ACOMPANHAMENTO] Título nos dados: "Acompanhamento de Jandir"
```

### Logs de Atualização

```
[ATUALIZAR_ACOMPANHAMENTO] Iniciando atualização do documento abc123
[ATUALIZAR_ACOMPANHAMENTO] Campos a atualizar: ['title', 'status', ...]
[ATUALIZAR_ACOMPANHAMENTO] Título nos dados: "Acompanhamento de Jandir"
[ATUALIZAR_ACOMPANHAMENTO] Documento encontrado. Atualizando...
[ATUALIZAR_ACOMPANHAMENTO] ✓ Documento atualizado com sucesso
[ATUALIZAR_ACOMPANHAMENTO] Verificação: Título após salvar: "Acompanhamento de Jandir"
```

### Logs de Criação

```
[CRIAR_ACOMPANHAMENTO] Iniciando criação de novo acompanhamento
[CRIAR_ACOMPANHAMENTO] Título: "Novo Acompanhamento"
[CRIAR_ACOMPANHAMENTO] ID gerado: xyz789
[CRIAR_ACOMPANHAMENTO] ✓ Documento salvo no Firestore
[CRIAR_ACOMPANHAMENTO] Verificação: Título após salvar: "Novo Acompanhamento"
[CRIAR_ACOMPANHAMENTO] ✓ Acompanhamento criado com sucesso. ID: xyz789
```

---

## Como Verificar se Está Funcionando

### 1. Verificar Logs do Servidor

Ao salvar um acompanhamento, verificar logs:
- `[SALVAR ACOMPANHAMENTO]` - Deve mostrar título
- `[ATUALIZAR_ACOMPANHAMENTO]` ou `[CRIAR_ACOMPANHAMENTO]` - Deve mostrar sucesso
- Verificação pós-salvamento - Deve confirmar título salvo

### 2. Verificar Firebase Console

1. Ir para Firebase Console > Firestore
2. Coleção: `third_party_monitoring`
3. Abrir documento do acompanhamento
4. Verificar se campo `title` existe e tem valor

### 3. Verificar Tabela

1. Abrir página de processos
2. Filtrar por acompanhamentos (clicar no card)
3. Verificar se título aparece na coluna "Título"
4. Não deve aparecer vazio ou "Acompanhamento de Terceiro" (padrão)

---

## Troubleshooting

### Problema: Título ainda não aparece

**Solução:**
1. Verificar logs: `[FETCH_ACOMPANHAMENTOS]` deve mostrar título
2. Verificar Firebase Console: campo `title` deve existir
3. Limpar cache: recarregar página (F5)

### Problema: Erro ao salvar

**Solução:**
1. Verificar logs: `[SALVAR ACOMPANHAMENTO]` para ver erro específico
2. Verificar validações: título não pode estar vazio
3. Verificar Firestore Rules: permissões de escrita

### Problema: Dados não persistem

**Solução:**
1. Verificar logs de verificação pós-salvamento
2. Verificar se documento existe no Firestore
3. Verificar se cache foi invalidado

---

## Testes Recomendados

### Teste 1: Criar e Verificar
1. Criar novo acompanhamento com título "Teste 1"
2. Salvar
3. Verificar Firebase Console: campo `title` = "Teste 1"
4. Verificar tabela: título aparece como "Teste 1"

### Teste 2: Editar e Verificar
1. Editar acompanhamento existente
2. Mudar título para "Teste 2"
3. Salvar
4. Verificar Firebase Console: campo `title` = "Teste 2"
5. Verificar tabela: título atualizado

### Teste 3: Reabrir e Verificar
1. Editar e salvar acompanhamento
2. Fechar modal
3. Clicar novamente no título
4. Modal deve abrir com título atualizado

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0  
**Status:** ✅ CORRIGIDO


