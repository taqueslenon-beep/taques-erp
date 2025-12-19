# RELATÓRIO DE DIAGNÓSTICO - LENTIDÃO NA TRANSIÇÃO ENTRE MÓDULOS

**Data:** 2025-01-27  
**Contexto:** Sistema lento ao navegar entre páginas/módulos, menos de 500 registros no total

---

## 1. VERIFICAÇÃO DE INVALIDAÇÃO DE CACHE

### Função `invalidate_cache()` em `mini_erp/core.py`

**Localização:** Linha 230-238

```python
def invalidate_cache(collection_name: str = None):
    """Invalida o cache de uma coleção ou de todas."""
    if collection_name:
        _cache.pop(collection_name, None)
        _cache_timestamp.pop(collection_name, None)
    else:
        _cache.clear()
        _cache_timestamp.clear()
```

### TODAS AS CHAMADAS DE `invalidate_cache()` ENCONTRADAS

| Arquivo                                                         | Linha     | Contexto                         | Problema                                            |
| --------------------------------------------------------------- | --------- | -------------------------------- | --------------------------------------------------- |
| `mini_erp/pages/pessoas/pessoas_page.py`                        | 35-36     | **NA ENTRADA DA PÁGINA**         | ⚠️ **CRÍTICO** - Invalida cache ao entrar na página |
| `mini_erp/pages/pessoas/pessoas_page.py`                        | 195       | Após deletar cliente             | OK                                                  |
| `mini_erp/pages/pessoas/pessoas_page.py`                        | 239       | Após deletar outro envolvido     | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 140       | Após salvar cliente              | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 320       | Após salvar cliente              | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 378       | Após salvar outro envolvido      | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 457       | Após salvar outro envolvido      | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 524       | Após salvar cliente              | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 547       | Após salvar cliente              | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 618       | Após salvar pessoa               | OK                                                  |
| `mini_erp/pages/pessoas/ui_dialogs.py`                          | 736       | Após salvar pessoa               | OK                                                  |
| `mini_erp/pages/processos/visualizacoes/visualizacao_padrao.py` | 574       | Após salvar processo             | OK                                                  |
| `mini_erp/pages/processos/visualizacoes/visualizacao_padrao.py` | 575       | Após salvar processo             | OK                                                  |
| `mini_erp/pages/processos/visualizacoes/visualizacao_padrao.py` | 589       | Após salvar protocolo            | OK                                                  |
| `mini_erp/pages/processos/visualizacoes/visualizacao_padrao.py` | 1491      | Após deletar processo            | OK                                                  |
| `mini_erp/pages/processos/database.py`                          | 454       | Após salvar processo             | OK                                                  |
| `mini_erp/pages/processos/database.py`                          | 498       | Após salvar processo             | OK                                                  |
| `mini_erp/pages/processos/database.py`                          | 890       | Após salvar acompanhamento       | OK                                                  |
| `mini_erp/pages/processos/database.py`                          | 1165      | Após salvar acompanhamento       | OK                                                  |
| `mini_erp/pages/processos/database.py`                          | 1191      | Após salvar acompanhamento       | OK                                                  |
| `mini_erp/pages/casos/database.py`                              | 145       | Após salvar caso                 | OK                                                  |
| `mini_erp/core.py`                                              | 1034      | Após salvar item                 | OK                                                  |
| `mini_erp/core.py`                                              | 1043      | Após deletar item                | OK                                                  |
| `mini_erp/core.py`                                              | 1311-1312 | Após sincronizar processos/casos | OK                                                  |
| `mini_erp/core.py`                                              | 1350      | Após atualizar caso              | OK                                                  |
| `mini_erp/core.py`                                              | 1900      | Após salvar protocolo            | OK                                                  |
| `mini_erp/core.py`                                              | 1911      | Após deletar protocolo           | OK                                                  |

### ⚠️ PROBLEMA IDENTIFICADO

**PÁGINA PESSOAS (`pessoas_page.py` linhas 35-36):**

```python
def _render_pessoas_content():
    """Conteúdo principal da página Pessoas."""
    # Invalida cache na entrada para garantir dados frescos do Firebase
    invalidate_cache('clients')
    invalidate_cache('opposing_parties')
```

**IMPACTO:** A cada navegação para `/pessoas`, o cache é invalidado, forçando recarregamento completo do Firestore mesmo que os dados estejam válidos (cache de 5 minutos).

---

## 2. VERIFICAÇÃO DE CARREGAMENTO SÍNCRONO NAS PÁGINAS

### 2.1 PÁGINA PAINEL (`mini_erp/pages/painel/painel_page.py`)

**Carregamento:**

- ✅ Usa `create_data_service()` que recebe funções `get_*_list()` como parâmetros
- ✅ Carregamento é feito dentro do `data_service`, não no início da página
- ❌ **NÃO há indicador de loading**
- ❌ **NÃO usa `ui.timer()` ou `async` para carregamento assíncrono**

**Chamadas `get_*_list()`:**

- `get_cases_list()` - chamado dentro do `data_service`
- `get_processes_list()` - chamado dentro do `data_service`
- `get_clients_list()` - chamado dentro do `data_service`
- `get_opposing_parties_list()` - chamado dentro do `data_service`

**Total:** 4 chamadas síncronas no carregamento inicial

---

### 2.2 PÁGINA PROCESSOS

**Arquivo:** Não encontrado `processos_page.py` diretamente. Módulo parece estar em:

- `mini_erp/pages/processos/visualizacoes/visualizacao_padrao.py`
- `mini_erp/pages/visao_geral/processos.py`

**Carregamento na visualização padrão:**

- `fetch_processes()` (linha 408) chama:
  - `get_processes_with_children()` - busca processos hierárquicos
  - `obter_todos_acompanhamentos()` - busca acompanhamentos
  - `get_clients_list()` (linha 447)
  - `get_opposing_parties_list()` (linha 448)

**Total:** Múltiplas chamadas síncronas, sem indicador de loading

---

### 2.3 PÁGINA CASOS (`mini_erp/pages/casos/casos_page.py`)

**Carregamento (linhas 86-91):**

```python
# OTIMIZAÇÃO: Carrega todos os dados UMA ÚNICA VEZ no início
_cases = deduplicate_cases_by_title(get_cases_list())
_clients = get_clients_list()
_opposing = get_opposing_parties_list()
```

**Características:**

- ❌ **Carregamento SÍNCRONO no início da função `casos()`**
- ❌ **NÃO há indicador de loading**
- ❌ **NÃO usa `ui.timer()` ou `async` para carregamento assíncrono**
- ✅ Usa `async/await` apenas para autosave e operações de edição (não para carregamento inicial)

**Total:** 3 chamadas síncronas bloqueantes no início

---

### 2.4 PÁGINA PESSOAS (`mini_erp/pages/pessoas/pessoas_page.py`)

**Carregamento:**

- ⚠️ **Invalida cache na entrada (linhas 35-36)** - FORÇA recarregamento
- Carregamento é feito dentro de `render_clients_table()` e `render_opposing_table()`
- ❌ **NÃO há indicador de loading**
- ❌ **NÃO usa `ui.timer()` ou `async` para carregamento assíncrono**
- ✅ Usa `ui.timer()` apenas para animação de sub-tabs (linha 152)

**Chamadas `get_*_list()`:**

- `get_clients_list()` - chamado dentro das tabelas
- `get_opposing_parties_list()` - chamado dentro das tabelas

**Total:** 2 chamadas síncronas + invalidação de cache

---

### 2.5 PÁGINA PRAZOS (`mini_erp/pages/prazos/prazos.py`)

**Carregamento (linhas 441-456):**

```python
# Carregar opções EM PARALELO para reduzir tempo de carregamento
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(buscar_usuarios_para_select): 'usuarios',
        executor.submit(buscar_clientes_para_select): 'clientes',
        executor.submit(buscar_casos_para_select): 'casos',
    }
```

**Características:**

- ✅ **USA ThreadPoolExecutor para carregamento paralelo** - BOA PRÁTICA
- ❌ **NÃO há indicador de loading**
- ❌ **NÃO usa `ui.timer()` ou `async` para carregamento assíncrono**

**Total:** 3 chamadas em paralelo (boa prática, mas ainda síncrono do ponto de vista do usuário)

---

## 3. VERIFICAÇÃO DE LAYOUT BASE

### Arquivo: `mini_erp/core.py` - Função `layout()` (linha 2153)

**JavaScript injetado em TODA navegação:**

1. **Meta tags anti-cache** (linhas 2161-2164)
2. **CSS customizado** (linhas 2166-2190) - ~25 linhas de CSS
3. **JavaScript de reconexão** (linhas 2191-2248) - ~58 linhas de JS
   - Inclui MutationObserver
   - Event listeners para DOMContentLoaded, online, load
   - Reconexão automática com limite de tentativas
   - Verificação a cada 3 segundos com `setInterval`
4. **JavaScript de workspace** (linhas 2238-2247) - ~10 linhas de JS

**Total de `ui.add_head_html()` no layout base:** 1 chamada com ~93 linhas de HTML/CSS/JS

**Problemas identificados:**

- ⚠️ **JavaScript pesado injetado em TODA navegação** - mesmo que já esteja no DOM
- ⚠️ **MutationObserver e setInterval criados a cada navegação** - pode causar memory leaks
- ⚠️ **Event listeners duplicados** - podem se acumular se não forem removidos

**Outras páginas com `ui.add_head_html()`:**

- `pessoas_page.py` - 1 chamada (CSS para tabs)
- `prazos.py` - 1 chamada (CSS e JS para tabela)
- `casos_page.py` - 2 chamadas (CSS para tabelas)
- `painel_page.py` - 1 chamada (CSS para tabs)
- Total adicional: ~5 chamadas por navegação

---

## 4. MEDIÇÃO DE TEMPO DE IMPORTS

**Script criado:** `scripts/medir_imports.py`

**Para executar:**

```bash
cd /Users/lenontaques/Documents/taques-erp
python3 scripts/medir_imports.py
```

**Módulos a medir:**

- `firebase_config`
- `core`
- `auth`
- `painel`
- `processos`
- `casos`
- `pessoas`
- `prazos`

---

## RESUMO DE PROBLEMAS IDENTIFICADOS

### 🔴 CRÍTICOS

1. **Invalidação de cache na entrada da página Pessoas**

   - Local: `pessoas_page.py:35-36`
   - Impacto: Força recarregamento do Firestore a cada navegação
   - Solução: Remover invalidação na entrada, manter apenas após operações de escrita

2. **Carregamento síncrono bloqueante em todas as páginas**

   - Páginas afetadas: Painel, Processos, Casos, Pessoas
   - Impacto: Interface congela durante carregamento
   - Solução: Implementar carregamento assíncrono com indicador de loading

3. **JavaScript pesado injetado a cada navegação**
   - Local: `core.py:layout()` linha 2160
   - Impacto: Reprocessamento desnecessário, possível memory leak
   - Solução: Verificar se já existe no DOM antes de injetar, ou usar `ui.add_head_html()` apenas uma vez

### 🟡 MODERADOS

4. **Falta de indicadores de loading**

   - Todas as páginas principais
   - Impacto: Usuário não sabe que está carregando
   - Solução: Adicionar spinners/indicadores durante carregamento

5. **Múltiplas chamadas `get_*_list()` síncronas**
   - Páginas fazem 2-4 chamadas sequenciais
   - Impacto: Tempo de carregamento acumulado
   - Solução: Carregar em paralelo (como Prazos já faz)

### 🟢 BONS EXEMPLOS

- **Prazos:** Usa `ThreadPoolExecutor` para carregamento paralelo
- **Cache:** Sistema de cache de 5 minutos implementado corretamente

---

## SUGESTÕES DE CORREÇÃO

### Prioridade 1: Remover invalidação de cache na entrada

**Arquivo:** `mini_erp/pages/pessoas/pessoas_page.py`

**Antes:**

```python
def _render_pessoas_content():
    invalidate_cache('clients')
    invalidate_cache('opposing_parties')
```

**Depois:**

```python
def _render_pessoas_content():
    # Cache será usado se válido (5 minutos)
    # Invalidação apenas após operações de escrita
```

---

### Prioridade 2: Implementar carregamento assíncrono

**Exemplo para página Casos:**

```python
@ui.page('/casos')
def casos():
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    with layout('Casos', breadcrumbs=[('Casos', None)]):
        # Mostrar loading
        loading = ui.spinner(size='lg')
        loading_label = ui.label('Carregando casos...')

        async def load_data():
            try:
                _cases = await run.io_bound(deduplicate_cases_by_title, get_cases_list())
                _clients = await run.io_bound(get_clients_list)
                _opposing = await run.io_bound(get_opposing_parties_list)

                # Esconder loading e renderizar conteúdo
                loading.set_visibility(False)
                loading_label.set_visibility(False)
                # ... resto do código
            except Exception as e:
                ui.notify(f'Erro ao carregar: {e}', type='negative')

        ui.timer(0.1, lambda: asyncio.create_task(load_data()), once=True)
```

---

### Prioridade 3: Otimizar JavaScript do layout

**Arquivo:** `mini_erp/core.py`

**Solução:** Verificar se script já foi injetado:

```python
ui.add_head_html('''
<script>
    if (!window.taques_erp_initialized) {
        window.taques_erp_initialized = true;
        // ... código JavaScript aqui
    }
</script>
''')
```

Ou mover para inicialização única do app (fora da função `layout()`).

---

### Prioridade 4: Carregamento paralelo

**Aplicar padrão de Prazos em outras páginas:**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(get_cases_list): 'cases',
        executor.submit(get_clients_list): 'clients',
        executor.submit(get_opposing_parties_list): 'opposing',
    }

    data = {}
    for future in as_completed(futures):
        key = futures[future]
        data[key] = future.result()
```

---

## PRÓXIMOS PASSOS

1. ✅ Executar `scripts/medir_imports.py` para medir tempo real de imports
2. ⏳ Remover invalidação de cache na entrada de Pessoas
3. ⏳ Implementar carregamento assíncrono nas páginas principais
4. ⏳ Adicionar indicadores de loading
5. ⏳ Otimizar JavaScript do layout base
6. ⏳ Aplicar carregamento paralelo onde possível

---

**FIM DO RELATÓRIO**








