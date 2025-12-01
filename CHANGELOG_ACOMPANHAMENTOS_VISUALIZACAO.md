# CHANGELOG - Acompanhamentos de Terceiros na Visualização de Processos

## [1.0.0] - 2025-01-XX

### 🐛 Problema Identificado

**Sintoma:** Acompanhamentos de terceiros não apareciam na visualização geral de processos.

**Causa Raiz:** Função `fetch_processes()` buscava apenas da coleção `processes`, não incluía `third_party_monitoring`.

**Impacto:**

- ❌ Aba "Processos" (sem filtro) não mostrava acompanhamentos
- ❌ Aba "Processos" (filtro por casos) não mostrava acompanhamentos vinculados
- ✅ Card do Painel funcionava (usa função específica)

### ✨ Correção Implementada

#### 1. Modificação de `fetch_processes()`

**Antes:**

```python
def fetch_processes():
    raw = get_processes_list()  # Apenas processos normais
    # ...
```

**Depois:**

```python
def fetch_processes():
    # Buscar processos normais
    raw = get_processes_list()

    # Buscar acompanhamentos de terceiros e adicionar à lista
    from .database import obter_todos_acompanhamentos
    acompanhamentos = obter_todos_acompanhamentos()

    # Adicionar acompanhamentos à lista raw
    for acomp in acompanhamentos:
        acomp['_is_third_party_monitoring'] = True
        raw.append(acomp)
```

#### 2. Processamento Diferenciado de Acompanhamentos

**Implementação:**

- Detecta acompanhamentos pelo flag `_is_third_party_monitoring`
- Aplica regra "NA" para Clientes e Parte Contrária
- Processa casos vinculados corretamente
- Mantém compatibilidade com campos de data

**Código:**

```python
if is_third_party:
    # É um acompanhamento de terceiro
    clients_list = ['NA']  # REGRA: sempre "NA"
    opposing_list = ['NA']  # REGRA: sempre "NA"

    # Extrai casos vinculados
    cases_raw = proc.get('cases') or []
    if isinstance(cases_raw, list):
        cases_list = [str(c) for c in cases_raw if c]
    else:
        cases_list = [str(cases_raw)] if cases_raw else []

    # Título do acompanhamento
    display_title = proc.get('title') or proc.get('process_title') or proc.get('titulo')
else:
    # É um processo normal - processar normalmente
    # ...
```

#### 3. Filtro por Casos Inclui Acompanhamentos

**Comportamento:**

- Filtro por casos agora funciona para acompanhamentos
- Se acompanhamento está vinculado ao caso filtrado, aparece
- Se não está vinculado, não aparece

**Logs:**

```python
# Filtro de casos
if filter_case['value']:
    case_filter_value = filter_case['value']
    filtered = [r for r in filtered if case_filter_value in (r.get('cases_list') or [])]
    print(f"[FILTER_ROWS] Filtro por caso '{case_filter_value}': {len(filtered)} registros após filtro")
```

### 📝 Melhorias

#### Logs Detalhados

**Adicionados:**

- Log de quantos processos normais foram encontrados
- Log de quantos acompanhamentos foram encontrados
- Log do total combinado
- Log ao processar cada acompanhamento
- Log ao aplicar filtro por casos

**Exemplo de logs:**

```
[FETCH_PROCESSOS] Processos normais encontrados: 26
[FETCH_PROCESSOS] Acompanhamentos encontrados: 1
[FETCH_PROCESSOS] Total combinado (processos + acompanhamentos): 27
[FETCH_PROCESSOS] Processando acompanhamento: Acompanhamento de Jandir
[FETCH_PROCESSOS] Row de acompanhamento criada: título='Acompanhamento de Jandir', casos=['1.5 - Bituva / 2020']
[FILTER_ROWS] Filtro por caso '1.5 - Bituva / 2020': 2 registros após filtro
```

### 🔧 Mudanças Técnicas

#### Arquivo: `mini_erp/pages/processos/processos_page.py`

**Função `fetch_processes()`:**

- Importa `obter_todos_acompanhamentos` de `database.py`
- Busca acompanhamentos e adiciona à lista `raw`
- Marca acompanhamentos com `_is_third_party_monitoring = True`

**Loop de processamento:**

- Detecta acompanhamentos pelo flag
- Processa acompanhamentos com lógica específica
- Mantém processamento normal para processos

**Função `filter_rows()`:**

- Filtro por casos já funciona automaticamente (busca em `cases_list`)
- Logs adicionados para debug

### 📊 Comportamento Esperado

#### Visualização Geral (sem filtro)

- Mostra todos os processos normais
- Mostra todos os acompanhamentos
- Total: processos normais + acompanhamentos

#### Filtro por Casos

- Mostra processos vinculados ao caso
- Mostra acompanhamentos vinculados ao caso
- Se acompanhamento não tem caso vinculado, não aparece

#### Regra "NA"

- Acompanhamentos sempre mostram "NA" em Clientes
- Acompanhamentos sempre mostram "NA" em Parte Contrária
- Processos normais mostram lista normal

### 🎯 Campos Processados para Acompanhamentos

| Campo           | Origem                             | Processamento             |
| --------------- | ---------------------------------- | ------------------------- |
| Título          | `title`, `process_title`, `titulo` | Primeiro não vazio        |
| Número          | `number`, `process_number`         | Primeiro não vazio        |
| Link            | `link`, `link_do_processo`         | Primeiro não vazio        |
| Data            | `data_de_abertura`, `start_date`   | Mesma lógica de processos |
| Casos           | `cases`                            | Lista ou string           |
| Clientes        | -                                  | Sempre `['NA']`           |
| Parte Contrária | -                                  | Sempre `['NA']`           |
| Status          | `status`                           | Valor direto              |

### 🧪 Testes Realizados

#### Teste 1: Visualização Geral

1. Abrir aba "Processos" (sem filtro)
2. **Esperado:** ✅ Mostra 26 processos + 1 acompanhamento = 27 total
3. **Resultado:** ✅ Funcionando

#### Teste 2: Filtro por Casos

1. Filtrar por caso "1.5 - Bituva / 2020"
2. **Esperado:** ✅ Mostra processos e acompanhamentos vinculados
3. **Resultado:** ✅ Funcionando

#### Teste 3: Regra "NA"

1. Verificar colunas "Clientes" e "Parte Contrária" em acompanhamentos
2. **Esperado:** ✅ Mostram "NA" em itálico cinza
3. **Resultado:** ✅ Funcionando

### 📋 Checklist de Correção

- [x] Função `fetch_processes()` busca acompanhamentos
- [x] Acompanhamentos são marcados com flag `_is_third_party_monitoring`
- [x] Processamento diferenciado para acompanhamentos
- [x] Regra "NA" aplicada corretamente
- [x] Filtro por casos inclui acompanhamentos
- [x] Logs detalhados adicionados
- [x] Compatibilidade com campos de data mantida
- [x] Compatibilidade com múltiplos nomes de campos

### 🔍 Troubleshooting

#### Problema: Acompanhamentos ainda não aparecem

**Solução:**

1. Verificar logs: `[FETCH_PROCESSOS] Acompanhamentos encontrados: X`
2. Verificar se função `obter_todos_acompanhamentos()` retorna dados
3. Verificar se flag `_is_third_party_monitoring` está sendo setado

#### Problema: Filtro por casos não funciona para acompanhamentos

**Solução:**

1. Verificar se acompanhamento tem campo `cases` preenchido
2. Verificar logs: `[FILTER_ROWS] Filtro por caso`
3. Verificar se `cases_list` está sendo populado corretamente

### 📚 Arquivos Modificados

1. `mini_erp/pages/processos/processos_page.py`
   - `fetch_processes()` - Inclui acompanhamentos
   - Loop de processamento - Lógica diferenciada
   - `filter_rows()` - Logs adicionados

### 🎯 Benefícios

1. **Visualização Completa:**

   - Todos os processos e acompanhamentos em um só lugar
   - Fácil identificação visual (cores azuis)

2. **Filtros Funcionais:**

   - Filtro por casos funciona para ambos
   - Filtros mantêm comportamento esperado

3. **Consistência:**

   - Regra "NA" aplicada uniformemente
   - Processamento padronizado

4. **Debug:**
   - Logs detalhados facilitam diagnóstico
   - Rastreamento de cada etapa

---

**Versão:** 1.0.0  
**Data:** 2025-01-XX  
**Status:** ✅ CORRIGIDO


