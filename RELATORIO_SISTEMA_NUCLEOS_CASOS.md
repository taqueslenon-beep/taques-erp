# RELATÓRIO - SISTEMA DE NÚCLEOS NO MÓDULO CASOS

**Data:** 2024-12-12  
**Objetivo:** Documentar estrutura, visual e funcionamento do sistema de Núcleos para replicar no módulo Novos Negócios

---

## 1. ESTRUTURA DE DADOS

### Onde os núcleos estão definidos?

**Arquivo principal:** `mini_erp/pages/visao_geral/casos/models.py`

```22:32:mini_erp/pages/visao_geral/casos/models.py
# CONSTANTES - NÚCLEOS
# =============================================================================

NUCLEO_OPTIONS = ['Ambiental', 'Cobranças', 'Generalista']

NUCLEO_CORES = {
    'Ambiental': '#223631',      # Verde escuro
    'Cobranças': '#1e3a5f',      # Azul escuro
    'Generalista': '#5b9bd5',    # Azul claro
}
```

### Núcleos disponíveis

1. **Ambiental** - Cor: `#223631` (verde escuro)
2. **Cobranças** - Cor: `#1e3a5f` (azul escuro)
3. **Generalista** - Cor: `#5b9bd5` (azul claro) - **Este é o padrão**

### Como são salvos no Firebase?

- **Campo:** `nucleo` (string)
- **Coleção:** `vg_casos`
- **Tipo:** String simples (ex: `"Ambiental"`, `"Cobranças"`, `"Generalista"`)
- **Obrigatório:** Sim
- **Valor padrão:** `"Generalista"`

**Exemplo no Firebase:**
```json
{
  "_id": "abc123",
  "titulo": "Caso exemplo",
  "nucleo": "Ambiental",
  ...
}
```

### Os núcleos são fixos ou configuráveis?

**FIXOS** - Definição hardcoded no arquivo `models.py`. Não há interface para o usuário adicionar/editar núcleos.

---

## 2. VISUAL DOS NÚCLEOS

### Como são exibidos?

Os núcleos são exibidos como **badges** nos cards de casos usando `ui.label` com classes CSS customizadas.

### Cores por núcleo

| Núcleo | Cor Hexadecimal | Visual |
|--------|----------------|--------|
| Ambiental | `#223631` | Verde escuro |
| Cobranças | `#1e3a5f` | Azul escuro |
| Generalista | `#5b9bd5` | Azul claro |

### Componente NiceGUI usado

**`ui.label`** com classes CSS customizadas (`caso-badge`)

### Código que renderiza o núcleo

**No card do caso (main.py):**

```512:515:mini_erp/pages/visao_geral/casos/main.py
                # Badge do Núcleo
                ui.label(nucleo).classes('caso-badge').style(
                    f'background-color: {cor_nucleo}; color: white;'
                )
```

**Função auxiliar para obter cor:**

```110:112:mini_erp/pages/visao_geral/casos/models.py
def obter_cor_nucleo(nucleo: str) -> str:
    """Retorna a cor do badge do núcleo."""
    return NUCLEO_CORES.get(nucleo, '#6b7280')
```

**CSS do badge (definido em main.py):**

```134:142:mini_erp/pages/visao_geral/casos/main.py
.caso-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    width: fit-content;
}
```

---

## 3. DROPDOWN/FILTRO

### Dropdown no formulário

**Localização:** `mini_erp/pages/visao_geral/casos/caso_dialog.py`

```65:69:mini_erp/pages/visao_geral/casos/caso_dialog.py
                    nucleo_select = ui.select(
                        options=NUCLEO_OPTIONS,
                        value=dados.get('nucleo', 'Generalista'),
                        label='Núcleo *'
                    ).classes('flex-1').props('dense outlined')
```

**Propriedades:**
- **Obrigatório:** Sim (asterisco no label)
- **Valor padrão:** `'Generalista'`
- **Options:** `NUCLEO_OPTIONS` importado de `models.py`

### Filtro por núcleo na listagem

**Localização:** `mini_erp/pages/visao_geral/casos/main.py`

**Select do filtro:**

```302:307:mini_erp/pages/visao_geral/casos/main.py
                    # Filtro por núcleo
                    nucleo_select = ui.select(
                        options=['Todos'] + NUCLEO_OPTIONS,
                        value='Todos',
                        label='Núcleo'
                    ).classes('w-36').props('dense outlined')
```

**Lógica de filtro:**

```542:545:mini_erp/pages/visao_geral/casos/main.py
    # Filtro por núcleo
    nucleo_filtro = filtros.get('nucleo', 'Todos')
    if nucleo_filtro and nucleo_filtro != 'Todos':
        resultado = [c for c in resultado if c.get('nucleo') == nucleo_filtro]
```

---

## 4. FORMULÁRIO DE CASO

### Núcleo é obrigatório?

**SIM** - Campo obrigatório (asterisco `*` no label)

### Tem valor padrão?

**SIM** - `'Generalista'` é o valor padrão

**Código:**

```146:146:mini_erp/pages/visao_geral/casos/models.py
        'nucleo': 'Generalista',
```

### Posição no formulário

**Segunda linha** do formulário, junto com Status e Categoria:

```63:81:mini_erp/pages/visao_geral/casos/caso_dialog.py
                # Linha 2: Núcleo, Status, Categoria
                with ui.row().classes('w-full gap-4'):
                    nucleo_select = ui.select(
                        options=NUCLEO_OPTIONS,
                        value=dados.get('nucleo', 'Generalista'),
                        label='Núcleo *'
                    ).classes('flex-1').props('dense outlined')

                    status_select = ui.select(
                        options=STATUS_OPTIONS,
                        value=dados.get('status', 'Em andamento'),
                        label='Status'
                    ).classes('flex-1').props('dense outlined')

                    categoria_select = ui.select(
                        options=CATEGORIA_OPTIONS,
                        value=dados.get('categoria', 'Contencioso'),
                        label='Categoria'
                    ).classes('flex-1').props('dense outlined')
```

**Na aba de detalhes (dados básicos):**

```854:860:mini_erp/pages/visao_geral/casos/main.py
                ui.select(
                    options=NUCLEO_OPTIONS,
                    value=caso.get('nucleo', 'Generalista'),
                    label='Núcleo *',
                    on_change=on_nucleo_change
                ).classes('flex-1').props('dense outlined')
```

---

## 5. ARQUIVOS RELEVANTES

### Lista de arquivos que tratam núcleos

1. **`mini_erp/pages/visao_geral/casos/models.py`**
   - Define `NUCLEO_OPTIONS` e `NUCLEO_CORES`
   - Função `obter_cor_nucleo()`
   - Validação de núcleo em `validar_caso()`
   - Valor padrão em `criar_caso_vazio()`

2. **`mini_erp/pages/visao_geral/casos/caso_dialog.py`**
   - Select de núcleo no formulário de criação/edição
   - Validação e salvamento do núcleo

3. **`mini_erp/pages/visao_geral/casos/main.py`**
   - Filtro por núcleo na listagem
   - Renderização do badge do núcleo nos cards
   - Select de núcleo na aba de detalhes (com autosave)

4. **`mini_erp/pages/visao_geral/casos/database.py`**
   - Função `listar_casos_por_nucleo()` para consultas diretas no Firebase

5. **`mini_erp/pages/visao_geral/painel.py`**
   - Função `agrupar_casos_por_nucleo()` para gráficos
   - Uso de `obter_cor_nucleo()` para cores do gráfico

### Código das funções principais

**Função para obter cor do núcleo:**

```110:112:mini_erp/pages/visao_geral/casos/models.py
def obter_cor_nucleo(nucleo: str) -> str:
    """Retorna a cor do badge do núcleo."""
    return NUCLEO_CORES.get(nucleo, '#6b7280')
```

**Validação do núcleo:**

```195:198:mini_erp/pages/visao_geral/casos/models.py
    # Núcleo obrigatório
    nucleo = dados.get('nucleo', '')
    if nucleo not in NUCLEO_OPTIONS:
        return False, 'Núcleo inválido.'
```

**Consulta no Firebase:**

```234:263:mini_erp/pages/visao_geral/casos/database.py
def listar_casos_por_nucleo(nucleo: str) -> List[Dict[str, Any]]:
    """
    Lista casos filtrados por núcleo.

    Args:
        nucleo: Nome do núcleo (Ambiental, Cobranças, Generalista)

    Returns:
        Lista de casos do núcleo especificado
    """
    try:
        db = get_db()
        if not db:
            return []

        docs = db.collection(COLECAO_CASOS).where('nucleo', '==', nucleo).stream()
        casos = []

        for doc in docs:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            caso = _converter_timestamps(caso)
            casos.append(caso)

        casos.sort(key=lambda c: c.get('created_at', ''), reverse=True)
        return casos

    except Exception as e:
        print(f"Erro ao listar casos por núcleo: {e}")
        return []
```

### O que pode ser reutilizado vs criado novo

**✅ REUTILIZAR:**
- Constantes `NUCLEO_OPTIONS` e `NUCLEO_CORES` (se os núcleos forem os mesmos)
- Função `obter_cor_nucleo()` (se as cores forem as mesmas)
- Estrutura do código (padrão de implementação)

**🆕 CRIAR NOVO:**
- Arquivo `models.py` específico do módulo Novos Negócios (ou importar do módulo de casos)
- Funções de database específicas (ex: `listar_novos_negocios_por_nucleo()`)
- Componentes de UI do módulo (select, badge, filtro)

---

## 6. CÓDIGO PARA REPLICAR

### Imports necessários

```python
from .models import (
    NUCLEO_OPTIONS,
    NUCLEO_CORES,
    obter_cor_nucleo,
)
```

Ou se criar novo arquivo de models:

```python
# Constantes
NUCLEO_OPTIONS = ['Ambiental', 'Cobranças', 'Generalista']

NUCLEO_CORES = {
    'Ambiental': '#223631',      # Verde escuro
    'Cobranças': '#1e3a5f',      # Azul escuro
    'Generalista': '#5b9bd5',    # Azul claro
}

# Função auxiliar
def obter_cor_nucleo(nucleo: str) -> str:
    """Retorna a cor do badge do núcleo."""
    return NUCLEO_CORES.get(nucleo, '#6b7280')
```

### Constantes/definições

```python
# Em models.py
NUCLEO_OPTIONS = ['Ambiental', 'Cobranças', 'Generalista']

NUCLEO_CORES = {
    'Ambiental': '#223631',      # Verde escuro
    'Cobranças': '#1e3a5f',      # Azul escuro
    'Generalista': '#5b9bd5',    # Azul claro
}
```

### Função de criar badge

```python
# Função simples inline (como no código atual)
nucleo = caso.get('nucleo', 'Generalista')
cor_nucleo = obter_cor_nucleo(nucleo)

ui.label(nucleo).classes('caso-badge').style(
    f'background-color: {cor_nucleo}; color: white;'
)
```

**CSS necessário (adicionar no head ou arquivo CSS):**

```css
.caso-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    width: fit-content;
}
```

### Select para formulário

**Formulário simples:**

```python
nucleo_select = ui.select(
    options=NUCLEO_OPTIONS,
    value=dados.get('nucleo', 'Generalista'),
    label='Núcleo *'
).classes('flex-1').props('dense outlined')
```

**Com callback (autosave):**

```python
def on_nucleo_change(e):
    novo_negocio['nucleo'] = e.value or 'Generalista'
    _trigger_autosave(novo_negocio, novo_negocio_id)

ui.select(
    options=NUCLEO_OPTIONS,
    value=novo_negocio.get('nucleo', 'Generalista'),
    label='Núcleo *',
    on_change=on_nucleo_change
).classes('flex-1').props('dense outlined')
```

**Filtro na listagem:**

```python
nucleo_select = ui.select(
    options=['Todos'] + NUCLEO_OPTIONS,
    value='Todos',
    label='Núcleo'
).classes('w-36').props('dense outlined')

# Evento
nucleo_select.on('update:model-value', lambda: aplicar_filtros())

# Lógica de filtro
nucleo_filtro = filtros.get('nucleo', 'Todos')
if nucleo_filtro and nucleo_filtro != 'Todos':
    resultado = [n for n in resultado if n.get('nucleo') == nucleo_filtro]
```

---

## RESUMO EXECUTIVO

### Estrutura mínima necessária para replicar:

1. **Constantes** (em `models.py`):
   - `NUCLEO_OPTIONS = ['Ambiental', 'Cobranças', 'Generalista']`
   - `NUCLEO_CORES = {...}`
   - `obter_cor_nucleo(nucleo: str) -> str`

2. **Campo no Firebase:**
   - Campo `nucleo` (string, obrigatório, padrão: `'Generalista'`)

3. **Validação:**
   - Verificar se `nucleo in NUCLEO_OPTIONS`

4. **UI - Select no formulário:**
   - `ui.select(options=NUCLEO_OPTIONS, value='Generalista', label='Núcleo *')`

5. **UI - Badge visual:**
   - `ui.label(nucleo).classes('caso-badge').style(f'background-color: {cor}; color: white;')`

6. **UI - Filtro:**
   - Select com `['Todos'] + NUCLEO_OPTIONS`
   - Filtro: `if nucleo_filtro != 'Todos': resultado = [n for n in resultado if n.get('nucleo') == nucleo_filtro]`

7. **CSS:**
   - Classe `.caso-badge` com estilos definidos

---

## OBSERVAÇÕES IMPORTANTES

1. **Núcleos são FIXOS** - Não há interface para usuário criar novos núcleos
2. **Valor padrão sempre `'Generalista'`** - Usado em casos vazios e fallback
3. **Badge usa CSS inline** - Cor é aplicada via `.style()`, não classe CSS
4. **Validação obrigatória** - Núcleo deve estar em `NUCLEO_OPTIONS`
5. **Reutilização possível** - Se os núcleos forem os mesmos, pode importar de `casos.models`

















