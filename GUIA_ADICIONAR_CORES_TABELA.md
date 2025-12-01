# Guia: Como Adicionar Novas Cores de Linha na Tabela de Processos

Este guia explica como adicionar um novo tipo de registro com cores próprias na tabela de processos.

---

## Passo a Passo

### 1. Definir Paleta de Cores

Escolha 3 cores para o novo tipo:

- **Barra Lateral**: Cor principal (ex: `#FF5733`)
- **Fundo da Linha**: Cor clara/pastel (ex: `#FFE5E0`)
- **Fundo Hover**: Cor um pouco mais escura (ex: `#FFD4CC`)

**Recomendações:**

- Use cores que contrastem bem com o texto
- Evite cores muito escuras no fundo (legibilidade)
- Mantenha consistência com a paleta existente

---

### 2. Adicionar CSS (`ui_components.py`)

Abra `mini_erp/pages/processos/ui_components.py` e localize a seção de CSS (linha ~86).

Adicione após os estilos de acompanhamentos de terceiros:

```css
/* LINHA [COR] PARA [NOVO TIPO] */
.q-table tbody tr[data-type="novo_tipo"],
.q-table tbody tr.novo-tipo-row {
  background-color: #COR_FUNDO !important;
  border-left: 4px solid #COR_BARRA !important;
}
.q-table tbody tr[data-type="novo_tipo"]:hover,
.q-table tbody tr.novo-tipo-row:hover {
  background-color: #COR_HOVER !important;
}
```

**Exemplo:**

```css
/* LINHA VERDE PARA PROCESSOS URGENTES */
.q-table tbody tr[data-type="urgente"],
.q-table tbody tr.urgente-row {
  background-color: #e8f5e9 !important;
  border-left: 4px solid #4caf50 !important;
}
.q-table tbody tr[data-type="urgente"]:hover,
.q-table tbody tr.urgente-row:hover {
  background-color: #c8e6c9 !important;
}
```

---

### 3. Adicionar Detecção no JavaScript (`processos_page.py`)

Abra `mini_erp/pages/processos/processos_page.py` e localize a função `apply_row_styles()` (linha ~610).

Adicione a detecção do novo tipo:

```javascript
// Dentro da função applyStyles(), após detectar processos futuros:

let isNovoTipo = false;

// Detecção do novo tipo
const novoTipoAttr = row.getAttribute("data-type");
if (novoTipoAttr === "novo_tipo") {
  isNovoTipo = true;
}

// Ou por atributo customizado:
const rowDataAttr = row.getAttribute("data-row-type");
if (rowDataAttr === "novo_tipo") {
  isNovoTipo = true;
}

// Aplica estilos
if (isNovoTipo) {
  row.setAttribute("data-type", "novo_tipo");
  row.classList.add("novo-tipo-row");
} else {
  row.removeAttribute("data-type");
  row.classList.remove("novo-tipo-row");
}
```

**Exemplo completo integrado:**

```javascript
let isUrgente = false;

// Detecta processos urgentes
const urgenteAttr = row.getAttribute("data-type");
if (urgenteAttr === "urgente") {
  isUrgente = true;
}

const rowDataAttr = row.getAttribute("data-row-type");
if (rowDataAttr === "urgente") {
  isUrgente = true;
}

// Aplica estilos para processos urgentes
if (isUrgente) {
  row.setAttribute("data-type", "urgente");
  row.classList.add("urgente-row");
} else {
  row.removeAttribute("data-type");
  row.classList.remove("urgente-row");
}
```

---

### 4. Marcar Rows com o Novo Tipo

Quando criar o `row_data` para o novo tipo, adicione um campo identificador:

**Opção A: Campo no row_data**

```python
row_data = {
    '_id': proc.get('_id'),
    'title': proc.get('title'),
    # ... outros campos ...
    'is_novo_tipo': True,  # ← Campo identificador
}
```

**Opção B: Adicionar atributo via JavaScript**

```python
# No JavaScript, após criar a row:
if (row_data.is_novo_tipo) {
    row.setAttribute('data-type', 'novo_tipo');
}
```

**Opção C: Slot Customizado (Vue)**

```python
# Adiciona atributo via slot na primeira célula
table.add_slot('body-cell-data_abertura', '''
    <q-td :props="props"
          :data-row-type="props.row.is_novo_tipo ? 'novo_tipo' : null"
          style="text-align: center;">
        <!-- conteúdo -->
    </q-td>
''')
```

---

### 5. Exemplo Completo: Processos Urgentes

#### CSS (`ui_components.py`)

```css
/* LINHA VERDE PARA PROCESSOS URGENTES */
.q-table tbody tr[data-type="urgente"],
.q-table tbody tr.urgente-row {
  background-color: #e8f5e9 !important;
  border-left: 4px solid #4caf50 !important;
}
.q-table tbody tr[data-type="urgente"]:hover,
.q-table tbody tr.urgente-row:hover {
  background-color: #c8e6c9 !important;
}
```

#### JavaScript (`processos_page.py`)

```javascript
let isUrgente = false;

// Detecta processos urgentes
if (
  row.getAttribute("data-type") === "urgente" ||
  row.getAttribute("data-row-type") === "urgente"
) {
  isUrgente = true;
}

if (isUrgente) {
  row.setAttribute("data-type", "urgente");
  row.classList.add("urgente-row");
}
```

#### Python (marcar rows)

```python
# Em fetch_processes() ou função similar
if proc.get('priority') == 'urgente':
    row_data['is_urgente'] = True
```

---

## Checklist de Implementação

- [ ] Escolhidas 3 cores (barra, fundo, hover)
- [ ] CSS adicionado em `ui_components.py`
- [ ] JavaScript atualizado em `processos_page.py`
- [ ] Campo identificador adicionado no `row_data`
- [ ] Testado visualmente
- [ ] Documentado no CHANGELOG

---

## Boas Práticas

### Nomenclatura

- **CSS Class:** Use formato `kebab-case` (ex: `novo-tipo-row`)
- **Data Attribute:** Use formato `snake_case` (ex: `novo_tipo`)
- **Campo Python:** Use formato `snake_case` com prefixo `is_` (ex: `is_novo_tipo`)

### Cores

- Mantenha contraste adequado para legibilidade
- Use cores que façam sentido semanticamente (verde = urgente, azul = monitoramento, etc.)
- Evite cores muito saturadas no fundo

### Performance

- CSS é mais performático que JavaScript inline
- Use classes CSS quando possível
- Evite aplicar estilos via JavaScript repetidamente

---

## Troubleshooting

### Cores não aparecem

**Verificar:**

1. CSS está correto (verificar console do navegador)
2. Atributo está sendo aplicado (inspecionar HTML)
3. JavaScript está executando (console do navegador)

**Solução:**

```javascript
// Adicionar debug temporário
console.log("Detectado novo tipo:", isNovoTipo);
console.log("Row:", row);
```

### Conflito com outros estilos

**Verificar:**

1. Especificidade do CSS (usar `!important` se necessário)
2. Ordem dos seletores CSS
3. Seletor CSS não está sendo sobrescrito

**Solução:**

```css
/* Aumentar especificidade */
.q-table tbody tr[data-type="novo_tipo"].novo-tipo-row {
  background-color: #COR !important;
}
```

### Estilos aplicados mas não visíveis

**Verificar:**

1. Cores não são muito claras/escuras
2. Barra lateral tem largura suficiente (4px mínimo)
3. Fundo não está sendo sobrescrito

---

## Paleta de Cores Sugeridas para Novos Tipos

| Tipo      | Barra Lateral        | Fundo     | Hover     | Uso                    |
| --------- | -------------------- | --------- | --------- | ---------------------- |
| Urgente   | `#4CAF50` (Verde)    | `#E8F5E9` | `#C8E6C9` | Processos prioritários |
| Suspenso  | `#FF9800` (Laranja)  | `#FFF3E0` | `#FFE0B2` | Processos pausados     |
| Arquivado | `#9E9E9E` (Cinza)    | `#F5F5F5` | `#EEEEEE` | Processos arquivados   |
| Crítico   | `#F44336` (Vermelho) | `#FFEBEE` | `#FFCDD2` | Processos críticos     |

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0


