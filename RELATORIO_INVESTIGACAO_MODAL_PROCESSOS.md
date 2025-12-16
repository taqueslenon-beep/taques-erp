# RELATÓRIO DE INVESTIGAÇÃO: BUGS NO MODAL DE EDIÇÃO DE PROCESSOS

**Data**: 2024-12-19  
**Área**: Visão Geral do Escritório - Módulo de Processos  
**Rota Afetada**: `/visao-geral/processos`

---

## RESUMO EXECUTIVO

O modal de edição de processos na rota `/visao-geral/processos` apresenta problemas críticos onde os campos não são populados corretamente ao abrir um processo para edição. Após investigação detalhada, foram identificadas múltiplas causas raiz relacionadas ao fluxo de dados e ao timing de população dos campos.

---

## PROBLEMAS IDENTIFICADOS

### 1. TIMING DE POPULAÇÃO DOS CAMPOS

**Problema**: Os campos são populados em dois momentos diferentes, causando conflitos.

**Localização**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Detalhes**:

#### Primeira População (Durante Criação dos Componentes)
- **Linhas 286-322**: Os campos são criados com valores default usando `value=dados.get(...)`
  ```python
  title_input = ui.input(...)  # Sem value inicial
  number_input = ui.input(...)  # Sem value inicial
  type_select = ui.select(..., value=dados.get('tipo', 'Judicial'))  # Com value
  data_abertura_input = ui.input(..., value=dados.get('data_abertura', ''))  # Com value
  ```

#### Segunda População (Após Abertura do Modal)
- **Linhas 888-948**: Função `load_initial_data_after_open()` executa via `ui.timer(0.2, ...)`
  ```python
  def load_initial_data_after_open():
      if is_edicao:
          title_input.value = dados.get('titulo', '')
          number_input.value = dados.get('numero', '')
          # ...
  ```
- **Linha 970**: Timer configurado para executar 0.2 segundos após a criação do modal
  ```python
  ui.timer(0.2, load_initial_data_after_open, once=True)
  ```

**Problema Raiz**: 
- Se `dados` estiver vazio ou com estrutura incorreta quando os componentes são criados, os campos ficam em branco
- A segunda população via timer pode não executar se houver erros ou se o timing estiver incorreto
- Alguns campos (como `title_input` e `number_input`) não têm valor inicial na criação, dependendo apenas do timer

**Impacto**: Campos aparecem em branco mesmo quando os dados existem.

---

### 2. PROBLEMA DE ESTRUTURA DE DADOS NO FLUXO

**Problema**: Diferença entre como os dados são passados no modal original vs modal da Visão Geral.

**Localização**: 
- `mini_erp/pages/visao_geral/processos/main.py` (linhas 277-283)
- `mini_erp/pages/visao_geral/processos/processo_dialog.py` (linha 147)

**Detalhes**:

#### Modal Original (`/processos`)
- **Arquivo**: `mini_erp/pages/processos/modais/modal_processo.py`
- **Fluxo**: Recebe `process_idx` (índice inteiro)
- **Linha 1082**: Busca processo da lista: `p = processes[process_idx]`
- **Linhas 1115-1136**: Popula campos diretamente no `open_modal()`, ANTES de abrir o dialog
- **Vantagem**: Dados estão disponíveis e validados antes da renderização

#### Modal Visão Geral (`/visao-geral/processos`)
- **Arquivo**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`
- **Fluxo**: Recebe dicionário `processo` diretamente
- **Linha 147**: Cria cópia: `dados = processo.copy() if processo else criar_processo_vazio()`
- **Linha 278**: Abre dialog imediatamente: `dialog.open()`
- **Linha 970**: Timer tenta popular campos DEPOIS que o dialog já está aberto
- **Problema**: Timing incorreto - campos podem não estar prontos no DOM quando o timer executa

**Impacto**: Dados podem não estar disponíveis ou estruturados corretamente quando os campos são populados.

---

### 3. POSSÍVEL PROBLEMA DE CAMPOS VAZIOS OU NONE

**Problema**: Se `buscar_processo()` retornar dados com campos `None` ou vazios, o modal não os popula.

**Localização**: 
- `mini_erp/pages/visao_geral/processos/main.py` (linha 278)
- `mini_erp/pages/visao_geral/processos/database.py` (linhas 116-146)

**Detalhes**:

#### Função `buscar_processo()` 
- **Linha 135**: `processo = doc.to_dict()` - converte documento Firestore para dict
- **Linha 137**: `processo = _converter_timestamps(processo)` - converte timestamps
- **Retorno**: Pode conter campos `None` ou vazios se não existirem no Firestore

#### Função `abrir_dialog_processo()`
- **Linha 147**: `dados = processo.copy()` - cria cópia
- **Linhas 893-904**: Usa `dados.get('titulo', '')` - se `titulo` for `None`, retorna string vazia
- **Problema**: Não há validação se os campos existem ou se estão no formato esperado

**Possível Causa**: 
- Dados no Firestore podem ter estrutura diferente (ex: `title` vs `titulo`)
- Campos podem estar como `None` ao invés de strings vazias
- Conversão de timestamps pode estar corrompendo outros campos

**Impacto**: Campos ficam em branco mesmo que dados existam no Firestore.

---

### 4. PROBLEMA DE ORDEM DE EXECUÇÃO

**Problema**: O dialog é aberto ANTES de garantir que os dados foram carregados.

**Localização**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Detalhes**:

**Linha 972**: `dialog.open()` é chamado imediatamente  
**Linha 970**: Timer de 0.2s é configurado para popular campos

**Sequência Atual**:
1. `abrir_dialog_processo(processo=processo_completo)` é chamado
2. `dados = processo.copy()` cria cópia
3. Componentes UI são criados (linhas 173-887)
4. Timer é configurado (linha 970)
5. Dialog é aberto (linha 972) ← **PROBLEMA: Acontece antes do timer executar**
6. Timer executa após 0.2s (linha 970) ← **Tentativa de popular campos**

**Problema**: 
- NiceGUI pode não ter renderizado os componentes no DOM quando o timer executa
- 0.2 segundos pode não ser suficiente em alguns ambientes
- Se houver erro no timer, não há fallback

**Comparação com Modal Original**:
- No modal original, os campos são populados ANTES de `dialog.open()`
- Garante que os dados estão nos componentes antes da renderização

**Impacto**: Campos não são populados ou são populados parcialmente.

---

### 5. FALTA DE LOGS/DEBUG

**Problema**: Não há logs suficientes para diagnosticar o problema.

**Localização**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Detalhes**:
- **Linha 946-948**: Há apenas um try/except genérico que imprime erro, mas não logs detalhados
- Não há logs mostrando:
  - Se `processo` foi recebido corretamente
  - Se `dados` contém os campos esperados
  - Se o timer executou com sucesso
  - Quais campos foram populados e quais ficaram vazios

**Impacto**: Dificulta diagnóstico e correção.

---

### 6. INCONSISTÊNCIA NO MAPEAMENTO DE CAMPOS

**Problema**: Alguns campos podem ter nomes diferentes entre Firestore e o modal.

**Localização**: 
- `mini_erp/pages/visao_geral/processos/processo_dialog.py` (linhas 893-904)
- `mini_erp/pages/visao_geral/processos/models.py` (linha 119)

**Detalhes**:

#### Campos no Modal (Linha 893-904):
- `dados.get('titulo', '')`
- `dados.get('numero', '')`
- `dados.get('tipo', 'Judicial')`
- `dados.get('data_abertura', '')`
- `dados.get('sistema_processual', '')`
- `dados.get('area', '')`
- `dados.get('status', 'Ativo')`

#### Campos no Model (models.py, linha 119):
- `titulo: str` ✓
- `numero: str` ✓
- `tipo: str` ✓
- `data_abertura: str` ✓
- `sistema_processual: str` ✓
- `area: str` ✓
- `status: str` ✓

**Observação**: Os nomes parecem consistentes, mas não há garantia que o Firestore tenha esses campos populados.

---

## ARQUIVOS AFETADOS

1. **`mini_erp/pages/visao_geral/processos/main.py`**
   - Linhas 273-283: Handler de clique que chama `abrir_dialog_processo()`

2. **`mini_erp/pages/visao_geral/processos/processo_dialog.py`**
   - Linhas 137-147: Função `abrir_dialog_processo()` - recebe dados
   - Linhas 286-322: Criação de componentes com valores default
   - Linhas 888-948: Função `load_initial_data_after_open()` - população via timer
   - Linha 970: Timer que executa população
   - Linha 972: Abertura do dialog

3. **`mini_erp/pages/visao_geral/processos/database.py`**
   - Linhas 116-146: Função `buscar_processo()` - pode retornar dados incompletos

---

## EVIDÊNCIAS ENCONTRADAS

### Evidência 1: Timing de Execução
```python
# Linha 970: Timer configurado
ui.timer(0.2, load_initial_data_after_open, once=True)

# Linha 972: Dialog aberto imediatamente
dialog.open()
```
**Problema**: Dialog abre antes do timer executar, causando race condition.

### Evidência 2: Campos Sem Valor Inicial
```python
# Linhas 286-287: Campos sem value inicial
title_input = ui.input(make_required_label('Título do Processo')).classes('flex-grow').props('outlined dense')
number_input = ui.input(make_required_label('Número do Processo')).classes('w-48').props('outlined dense')
```
**Problema**: Dependem 100% do timer para serem populados.

### Evidência 3: Comparação com Modal Original
**Modal Original** (`modal_processo.py`, linha 1115):
```python
# Campos populados ANTES de dialog.open()
title_input.value = p.get('title', '') or ''
number_input.value = p.get('number', '') or ''
# ... outros campos ...
dialog.open()  # Só depois de popular todos os campos
```

**Modal Visão Geral** (`processo_dialog.py`, linha 972):
```python
# Dialog aberto primeiro
dialog.open()
# Timer tenta popular depois
ui.timer(0.2, load_initial_data_after_open, once=True)
```

---

## CAUSA RAIZ PRINCIPAL

**CAUSA RAIZ**: Ordem incorreta de execução onde o dialog é aberto ANTES dos campos serem populados, combinado com uso de timer que pode não executar a tempo ou pode encontrar componentes ainda não renderizados no DOM.

**FATORES CONTRIBUINTES**:
1. Falta de valor inicial nos campos críticos (`title_input`, `number_input`)
2. Timer de 0.2s pode ser insuficiente em alguns ambientes
3. Ausência de logs detalhados dificulta diagnóstico
4. Diferença arquitetural com modal original (índice vs dicionário direto)

---

## SUGESTÕES DE CORREÇÃO

### Correção 1: Popular Campos ANTES de Abrir Dialog (RECOMENDADO)
**Arquivo**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Mudança**: Mover lógica de `load_initial_data_after_open()` para ANTES de `dialog.open()`

**Localização**: 
- Remover timer (linha 970)
- Mover código de população para antes da linha 972
- Garantir que campos sejam populados antes de `dialog.open()`
- **IMPORTANTE**: Incluir TODOS os campos (básicos, jurídicos, relatório, estratégia, cenários, protocolos)

### Correção 2: Adicionar Valores Iniciais na Criação dos Componentes
**Arquivo**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Mudança**: Adicionar `value=dados.get(...)` na criação de TODOS os componentes

**Localização**: Linhas 286-322

### Correção 3: Adicionar Logs Detalhados
**Arquivo**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Mudança**: Adicionar logs antes e depois de popular cada campo

**Localização**: Início de `abrir_dialog_processo()` e em `load_initial_data_after_open()`

### Correção 4: Validar Dados Recebidos
**Arquivo**: `mini_erp/pages/visao_geral/processos/processo_dialog.py`

**Mudança**: Validar se `processo` contém campos esperados antes de usar

**Localização**: Linha 147, após `dados = processo.copy()`

### Correção 5: Alinhar com Modal Original (OPCIONAL - Refatoração Maior)
**Arquivo**: `mini_erp/pages/visao_geral/processos/main.py` e `processo_dialog.py`

**Mudança**: Mudar para usar índice ao invés de dicionário direto, alinhando com modal original

**Impacto**: Mudança arquitetural maior, mas garante consistência

---

## CAMPOS NÃO POPULADOS NO TIMER

A função `load_initial_data_after_open()` (linhas 890-948) **NÃO popula** os seguintes campos:

### Campos de Relatório (Aba 3):
- ❌ `relatory_facts_input` (linha 559)
- ❌ `relatory_timeline_input` (linha 565)
- ❌ `relatory_documents_input` (linha 571)

### Campos de Estratégia (Aba 4):
- ❌ `objectives_input` (linha 582)
- ❌ `thesis_input` (linha 588)
- ❌ `observations_input` (linha 594)

**Causa**: Esses campos dependem apenas do valor default na criação (`value=dados.get(...)`), mas se `dados` estiver vazio ou os campos não existirem, ficam em branco permanentemente.

**Solução**: Adicionar população desses campos na função `load_initial_data_after_open()` OU mover toda a população para antes de `dialog.open()`.

---

## PRÓXIMOS PASSOS RECOMENDADOS

1. **IMEDIATO**: Implementar Correção 1 (popular campos antes de abrir dialog) - **INCLUINDO campos de relatório e estratégia**
2. **SEGUNDO**: Adicionar logs detalhados (Correção 3) para validar se funciona
3. **TERCEIRO**: Testar com processo real do Firestore para garantir que dados são carregados
4. **OPCIONAL**: Considerar Correção 2 para redundância

---

## CONCLUSÃO

O problema principal é uma **race condition** onde o dialog é aberto antes dos campos serem populados. A solução mais direta é seguir o padrão do modal original: popular campos ANTES de abrir o dialog, eliminando a necessidade do timer e garantindo que os dados estejam disponíveis na renderização inicial.

