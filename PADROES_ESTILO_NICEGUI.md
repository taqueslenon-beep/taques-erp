# Padrões de Estilo NiceGUI Mais Usados no Projeto TAQUES ERP

## 📊 Top 5 Padrões Mais Comuns

### 1. **Largura Total (`w-full`)**
**Ocorrências:** ~680 vezes

**Uso:** Define largura de 100% para componentes ocuparem todo o espaço disponível.

**Exemplos:**
```python
ui.input('Nome').classes('w-full mb-2')
ui.card().classes('w-full p-4 mb-4 bg-gray-50')
ui.row().classes('w-full gap-2 mb-2')
ui.dialog().classes('w-full max-w-lg p-6')
ui.tabs().classes('w-full bg-white')
```

**Variações comuns:**
- `w-full` - largura total
- `w-full max-w-lg` - largura total com máximo
- `w-full max-w-md` - largura total com máximo médio
- `w-full max-w-2xl` - largura total com máximo extra grande
- `w-full max-w-6xl` - largura total com máximo muito grande

---

### 2. **Cores de Fundo (`bg-*`)**
**Ocorrências:** ~136 vezes

**Uso:** Define cores de fundo para cards, botões e containers.

**Exemplos:**
```python
ui.button('Salvar').classes('bg-primary text-white')
ui.card().classes('w-full p-4 mb-4 bg-gray-50')
ui.card().classes('w-full p-8 bg-white rounded shadow-sm')
ui.card().classes('px-4 py-2 bg-yellow-100 border border-yellow-400')
ui.card().classes('w-full p-8 bg-red-50 border border-red-200')
ui.button('Excluir').classes('bg-red-600 text-white')
```

**Cores mais usadas:**
- `bg-primary` - cor primária do sistema (#223631)
- `bg-white` - branco
- `bg-gray-50` - cinza claro
- `bg-red-600` - vermelho para ações destrutivas
- `bg-red-50` - vermelho claro para alertas
- `bg-yellow-100` - amarelo claro para avisos

---

### 3. **Sombras (`shadow-*`)**
**Ocorrências:** ~28 vezes

**Uso:** Adiciona profundidade visual com sombras em cards e botões.

**Exemplos:**
```python
ui.button('Novo Caso').classes('bg-primary text-white shadow-md')
ui.card().classes('w-full p-6 bg-white rounded shadow-sm')
ui.card().classes('px-4 py-2 bg-yellow-100 rounded-lg shadow-lg')
```

**Níveis de sombra:**
- `shadow-sm` - sombra pequena (mais sutil)
- `shadow-md` - sombra média (padrão)
- `shadow-lg` - sombra grande (mais destacada)
- `shadow-xl` - sombra extra grande

---

### 4. **Espaçamento (`gap-*`)**
**Ocorrências:** ~273 vezes

**Uso:** Define espaçamento entre elementos em rows e grids.

**Exemplos:**
```python
ui.row().classes('w-full gap-2 mb-2')
ui.row().classes('w-full gap-4 items-end flex-wrap')
ui.row().classes('w-full justify-end gap-2')
ui.card().classes('px-4 py-2 flex items-center gap-2')
```

**Valores mais comuns:**
- `gap-2` - 0.5rem (8px) - espaçamento pequeno
- `gap-4` - 1rem (16px) - espaçamento médio
- `gap-6` - 1.5rem (24px) - espaçamento grande

---

### 5. **Padding e Margin (`p-*`, `mb-*`, `mt-*`)**
**Ocorrências:** ~1004 vezes

**Uso:** Controla espaçamento interno (padding) e externo (margin) dos componentes.

**Exemplos:**
```python
ui.card().classes('w-full p-4 mb-4 bg-gray-50')
ui.input('Nome').classes('w-full mb-2')
ui.label('Título').classes('text-xl font-bold mb-4')
ui.card().classes('px-4 py-2 flex items-center gap-2')
ui.card().classes('w-full p-6')
ui.card().classes('w-full p-8 flex justify-center')
```

**Padrões mais comuns:**

**Padding:**
- `p-2` - padding pequeno (8px)
- `p-4` - padding médio (16px)
- `p-6` - padding grande (24px)
- `p-8` - padding extra grande (32px)
- `px-4 py-2` - padding horizontal 16px, vertical 8px

**Margin:**
- `mb-2` - margin-bottom pequeno (8px)
- `mb-4` - margin-bottom médio (16px)
- `mb-6` - margin-bottom grande (24px)
- `mt-2` - margin-top pequeno
- `mt-4` - margin-top médio

---

## 🎨 Padrões Combinados Mais Frequentes

### Cards Padrão
```python
ui.card().classes('w-full p-4 mb-4 bg-gray-50')
ui.card().classes('w-full p-6 bg-white rounded shadow-sm')
```

### Botões Primários
```python
ui.button('Salvar').classes('bg-primary text-white')
ui.button('Novo Caso').classes('bg-primary text-white shadow-md')
```

### Botões Destrutivos
```python
ui.button('Excluir').classes('bg-red-600 text-white')
```

### Rows com Espaçamento
```python
ui.row().classes('w-full gap-2 mb-2')
ui.row().classes('w-full justify-end gap-2')
```

### Inputs Padrão
```python
ui.input('Campo').classes('w-full mb-2')
ui.select(options=[]).classes('w-full mb-2')
```

---

## 📝 Notas sobre Estilo

- **Tailwind CSS:** O projeto usa principalmente classes Tailwind via `.classes()`
- **Estilos inline:** Alguns casos usam `.style()` para estilos específicos não cobertos por Tailwind
- **Props do Quasar:** Alguns componentes usam `.props()` para propriedades do Quasar (framework base do NiceGUI)
- **Consistência:** O padrão `w-full mb-2` é muito comum em inputs e selects







