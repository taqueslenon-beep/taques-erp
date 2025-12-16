# CORREÇÃO: MODAL DE EDIÇÃO DE PROCESSOS - VISÃO GERAL DO ESCRITÓRIO

**Data**: 2024-12-19  
**Arquivo**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`  
**Problema**: Race condition causando campos em branco ao editar processos

---

## PROBLEMA IDENTIFICADO

O modal de edição apresentava campos em branco devido a uma **race condition**:
- Dialog era aberto ANTES dos campos serem populados
- Timer de 0.2s tentava popular campos DEPOIS do dialog estar aberto
- Campos de Relatório e Estratégia NÃO eram populados pelo timer
- Campos críticos não tinham valor inicial na criação

---

## CORREÇÕES IMPLEMENTADAS

### 1. Removido Timer e População Assíncrona

**Antes**:
```python
# Executa após dialog ser aberto usando timer
ui.timer(0.2, load_initial_data_after_open, once=True)
dialog.open()
```

**Depois**:
```python
# Popular campos ANTES de abrir o dialog (corrige race condition)
populate_all_fields()
dialog.open()
```

### 2. Criada Função `populate_all_fields()`

Nova função que popula TODOS os campos de forma síncrona antes de abrir o dialog.

**Campos Populados**:

#### Campos Básicos (Aba 1):
- ✅ `title_input` - com fallback 'titulo'/'title'
- ✅ `number_input` - com fallback 'numero'/'number'
- ✅ `link_input`
- ✅ `type_select`
- ✅ `data_abertura_input`
- ✅ Chips de clientes, parte contrária, outros, casos

#### Campos Jurídicos (Aba 2):
- ✅ `system_select`
- ✅ `area_select`
- ✅ `estado_select`
- ✅ `comarca_input`
- ✅ `vara_input`
- ✅ `status_select`
- ✅ `result_select` (com toggle de visibilidade)

#### Campos Relatório (Aba 3) - **CORRIGIDO**:
- ✅ `relatory_facts_input` - **agora é populado**
- ✅ `relatory_timeline_input` - **agora é populado**
- ✅ `relatory_documents_input` - **agora é populado**

#### Campos Estratégia (Aba 4) - **CORRIGIDO**:
- ✅ `objectives_input` - **agora é populado**
- ✅ `thesis_input` - **agora é populado**
- ✅ `observations_input` - **agora é populado** (com fallback 'strategy_observations'/'observacoes')

#### Cenários (Aba 5):
- ✅ Carregamento de lista de cenários
- ✅ Migração de campos antigos (cenario_melhor, cenario_intermediario, cenario_pior)

#### Protocolos (Aba 6):
- ✅ Carregamento de lista de protocolos

### 3. Função `safe_get()` para Compatibilidade

Criada função auxiliar para:
- Converter `None` para string vazia
- Fazer fallback entre variações de nomes de campos
- Garantir que valores sejam strings

```python
def safe_get(key, default='', fallback_key=None):
    """Retorna valor do campo ou default, convertendo None para string vazia."""
    value = dados.get(key)
    if value is None and fallback_key:
        value = dados.get(fallback_key)
    if value is None or value == '':
        return default
    return str(value) if value else default
```

### 4. Logs Detalhados Adicionados

Logs foram adicionados para facilitar debug:
- Log no início da população
- Log após popular cada grupo de campos
- Log de erros específicos
- Formato: `[TIMESTAMP] [MODAL_VG] [POPULAR] mensagem`

### 5. Tratamento de Erros Melhorado

- Try/except específico para população de campos
- Notificação ao usuário se houver erro
- Logs detalhados de exceções

---

## ORDEM DE EXECUÇÃO CORRIGIDA

**ANTES (Incorreto)**:
1. Componentes UI criados
2. Timer configurado
3. Dialog aberto ← **Race condition aqui**
4. Timer executa (0.2s depois) ← **Tentativa tardia de popular**

**DEPOIS (Correto)**:
1. Componentes UI criados
2. **População de TODOS os campos** ← **ANTES de abrir**
3. Dialog aberto ← **Dados já estão nos campos**

---

## COMPATIBILIDADE

### Fallbacks de Nomes de Campos

A função `safe_get()` suporta fallbacks para garantir compatibilidade:
- `titulo` → fallback para `title`
- `numero` → fallback para `number`

### Tratamento de None

Todos os campos tratam `None` como string vazia:
```python
value = dados.get('campo')
if value is None or value == '':
    return default
```

### Listas e Arrays

Listas são validadas antes de usar:
```python
if dados.get('scenarios') and isinstance(dados.get('scenarios'), list):
    state['scenarios'] = dados.get('scenarios')
```

---

## TESTES RECOMENDADOS

1. ✅ Abrir processo existente para edição
2. ✅ Verificar se campos básicos são populados
3. ✅ Verificar se campos jurídicos são populados
4. ✅ Verificar se campos de relatório são populados
5. ✅ Verificar se campos de estratégia são populados
6. ✅ Verificar se cenários são carregados
7. ✅ Verificar se protocolos são carregados
8. ✅ Verificar se chips (clientes, casos, etc) são renderizados
9. ✅ Testar criação de novo processo (deve estar vazio)
10. ✅ Testar salvamento após edição

---

## ARQUIVOS MODIFICADOS

- `mini_erp/pages/visao_geral/processos/processo_dialog.py`
  - Linhas 887-1067: Função `populate_all_fields()` substituindo `load_initial_data_after_open()`
  - Linha 1069: Removido timer, chamada direta de `populate_all_fields()`
  - Linha 1071: Dialog abre APÓS população dos campos

---

## RESULTADO ESPERADO

Após esta correção:
- ✅ Todos os campos devem aparecer populados ao editar processo
- ✅ Abas de Relatório e Estratégia não devem mais aparecer em branco
- ✅ Sem race conditions
- ✅ Logs facilitam diagnóstico de problemas
- ✅ Compatibilidade com diferentes estruturas de dados

---

## OBSERVAÇÕES

- A correção segue o padrão do modal original (`modal_processo.py`)
- Função `populate_all_fields()` é executada de forma síncrona
- Todos os campos críticos agora são populados
- Logs detalhados permitem rastreamento de problemas

