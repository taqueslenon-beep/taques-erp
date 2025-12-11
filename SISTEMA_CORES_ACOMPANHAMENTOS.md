# Sistema de Cores para Acompanhamentos de Terceiros

## Visão Geral

Sistema de coloração visual para diferenciar **Acompanhamentos de Terceiros** dos processos regulares na tabela, seguindo o mesmo padrão visual dos processos futuros.

---

## Paleta de Cores

### Acompanhamentos de Terceiros

| Elemento       | Cor              | Código Hex |
| -------------- | ---------------- | ---------- |
| Barra lateral  | Azul claro médio | `#4A90E2`  |
| Fundo da linha | Azul muito claro | `#E8F1FF`  |
| Fundo hover    | Azul claro       | `#D4E7FF`  |

### Processos Futuros (Referência)

| Elemento       | Cor             | Código Hex |
| -------------- | --------------- | ---------- |
| Barra lateral  | Roxo            | `#9B59B6`  |
| Fundo da linha | Roxo claro      | `#f3e8ff`  |
| Fundo hover    | Roxo mais claro | `#e9d5ff`  |

### Processos Normais

| Elemento      | Cor                                       |
| ------------- | ----------------------------------------- |
| Barra lateral | Nenhuma                                   |
| Fundo         | Branco/Cinza alternado (padrão da tabela) |

---

## Implementação Técnica

### 1. CSS (ui_components.py)

O CSS está definido em `mini_erp/pages/processos/ui_components.py` no bloco `TABELA_PROCESSOS_CSS`:

```css
/* LINHA AZUL CLARO PARA ACOMPANHAMENTOS DE TERCEIROS */
.q-table tbody tr[data-type="third_party_monitoring"],
.q-table tbody tr.third-party-monitoring-row {
  background-color: #e8f1ff !important;
  border-left: 4px solid #4a90e2 !important;
}
.q-table tbody tr[data-type="third_party_monitoring"]:hover,
.q-table tbody tr.third-party-monitoring-row:hover {
  background-color: #d4e7ff !important;
}
```

### 2. JavaScript (processos_page.py)

O JavaScript aplica automaticamente os estilos quando detecta:

- Atributo `data-type="third_party_monitoring"` na linha
- Classe `third-party-monitoring-row` na linha
- Atributo `data-row-type="third_party_monitoring"` na linha

A função `apply_row_styles()` é executada automaticamente:

- Imediatamente após renderizar a tabela (200ms delay)
- Observa mudanças na tabela (MutationObserver)
- Atualiza estilos dinamicamente quando a tabela muda

### 3. Identificação de Acompanhamentos

Para que uma linha seja identificada como acompanhamento de terceiro, é necessário:

**Opção A: Adicionar campo no row_data**

Ao criar o `row_data` para um acompanhamento, adicione:

```python
row_data = {
    '_id': acompanhamento.get('id'),
    'title': acompanhamento.get('process_title'),
    # ... outros campos ...
    'is_third_party_monitoring': True,  # ← Campo identificador
}
```

**Opção B: Adicionar atributo na linha (JavaScript)**

O JavaScript procura por atributos `data-row-type` ou `data-type` na linha:

```javascript
// Adiciona atributo diretamente na linha HTML
row.setAttribute("data-type", "third_party_monitoring");
```

---

## Como Integrar Acompanhamentos na Tabela

### Passo 1: Buscar Acompanhamentos

```python
from mini_erp.pages.processos.database import obter_todos_acompanhamentos

# Na função fetch_processes() ou similar
acompanhamentos = obter_todos_acompanhamentos()
```

### Passo 2: Transformar em Formato de Row

```python
def transformar_acompanhamento_para_row(acompanhamento):
    """Transforma acompanhamento em formato de row da tabela."""
    return {
        '_id': acompanhamento.get('id'),
        'title': acompanhamento.get('process_title', ''),
        'number': acompanhamento.get('process_number', ''),
        'data_abertura': acompanhamento.get('start_date', ''),
        'status': acompanhamento.get('status', 'ativo'),
        'clients_list': [acompanhamento.get('client_name', '')],
        # ... outros campos ...
        'is_third_party_monitoring': True,  # ← IMPORTANTE: Marca como acompanhamento
    }
```

### Passo 3: Adicionar às Rows da Tabela

```python
# Na função fetch_processes() ou render_table()
rows = []

# Adiciona processos normais
for proc in processos:
    rows.append(criar_row_processo(proc))

# Adiciona acompanhamentos (com marcação)
for acomp in acompanhamentos:
    row = transformar_acompanhamento_para_row(acomp)
    row['is_third_party_monitoring'] = True  # Marca como acompanhamento
    rows.append(row)
```

### Passo 4: Slot Customizado (Opcional)

Se quiser aplicar o atributo diretamente via Vue/NiceGUI, adicione um slot na primeira célula:

```python
# Adiciona atributo data-type baseado no campo is_third_party_monitoring
table.add_slot('body-cell-data_abertura', '''
    <q-td :props="props"
          :data-type="props.row.is_third_party_monitoring ? 'third_party_monitoring' : null"
          style="text-align: center; padding: 8px 12px; vertical-align: middle;">
        <span v-if="props.row.data_abertura" class="text-xs text-gray-700 font-medium">{{ props.row.data_abertura }}</span>
        <span v-else class="text-gray-400">—</span>
    </q-td>
''')
```

---

## Detecção Automática

O JavaScript detecta acompanhamentos de três formas:

1. **Por atributo `data-type`:**

   ```html
   <tr data-type="third_party_monitoring"></tr>
   ```

2. **Por classe CSS:**

   ```html
   <tr class="third-party-monitoring-row"></tr>
   ```

3. **Por atributo `data-row-type`:**
   ```html
   <tr data-row-type="third_party_monitoring"></tr>
   ```

A função `apply_row_styles()` verifica todas essas formas e aplica os estilos automaticamente.

---

## Exemplos de Uso

### Exemplo 1: Adicionar Campo Identificador no row_data

```python
# Em fetch_processes() ou função similar
row_data = {
    '_id': proc.get('_id'),
    'title': proc.get('title'),
    # ... outros campos ...
}

# Se for acompanhamento, marca
if proc.get('tipo') == 'acompanhamento_terceiro':
    row_data['is_third_party_monitoring'] = True

rows.append(row_data)
```

### Exemplo 2: Slot Customizado para Primeira Célula

```python
table.add_slot('body-cell-data_abertura', '''
    <q-td :props="props"
          :data-row-type="props.row.is_third_party_monitoring ? 'third_party_monitoring' : null"
          style="text-align: center; padding: 8px 12px; vertical-align: middle;">
        <span v-if="props.row.data_abertura">{{ props.row.data_abertura }}</span>
        <span v-else>—</span>
    </q-td>
''')
```

---

## Compatibilidade

### Responsividade

- **Desktop:** Barra lateral de 4px visível
- **Mobile:** Barra lateral mantida (pode ser ajustada se necessário)

### Filtros

As cores são mantidas mesmo quando:

- Filtros de área, casos, clientes estão ativos
- Busca por texto está ativa
- Ordenação está aplicada

### Performance

- CSS aplicado via classes (performance otimizada)
- JavaScript executa apenas quando necessário (MutationObserver)
- Cache de estilos automático

---

## Adicionar Novos Tipos de Registro

Para adicionar um novo tipo com cores próprias:

1. **Defina as cores no CSS:**

   ```css
   .q-table tbody tr[data-type="novo_tipo"] {
     background-color: #COR_FUNDO !important;
     border-left: 4px solid #COR_BARRA !important;
   }
   ```

2. **Adicione detecção no JavaScript:**

   ```javascript
   if (rowData === "novo_tipo") {
     row.setAttribute("data-type", "novo_tipo");
     row.classList.add("novo-tipo-row");
   }
   ```

3. **Marque as rows:**
   ```python
   row_data['is_novo_tipo'] = True
   ```

---

## Validação Visual

### Checklist

- [x] CSS definido com cores corretas
- [x] JavaScript detecta acompanhamentos automaticamente
- [x] Barra lateral de 4px aplicada
- [x] Fundo azul claro aplicado
- [x] Hover com cor mais escura
- [x] Compatível com processos futuros (roxo)
- [x] Não interfere com processos normais

### Como Testar

1. **Adicionar campo identificador:**

   ```python
   # Em fetch_processes(), adicione temporariamente:
   if row_data.get('title', '').startswith('TESTE'):
       row_data['is_third_party_monitoring'] = True
   ```

2. **Verificar visualmente:**

   - Linha deve ter barra azul à esquerda
   - Fundo deve ser azul muito claro
   - Hover deve escurecer ligeiramente

3. **Inspecionar HTML:**
   ```javascript
   // No console do navegador:
   document.querySelectorAll('tr[data-type="third_party_monitoring"]');
   // Deve retornar as linhas de acompanhamentos
   ```

---

## Troubleshooting

### Problema: Cores não aparecem

**Solução:**

1. Verificar se o campo `is_third_party_monitoring` está no `row_data`
2. Verificar se o JavaScript está executando (console do navegador)
3. Verificar se o CSS está carregado (inspecionar elementos)

### Problema: Barra lateral não aparece

**Solução:**

1. Verificar se o CSS tem `border-left: 4px solid #4A90E2 !important;`
2. Verificar se há conflito com outros estilos
3. Limpar cache do navegador

### Problema: Cores aparecem e somem

**Solução:**

1. Verificar se o MutationObserver está funcionando
2. Verificar se há JavaScript que remove os atributos
3. Aumentar o delay do setTimeout se necessário

---

## Arquivos Modificados

- `mini_erp/pages/processos/ui_components.py`: CSS adicionado
- `mini_erp/pages/processos/processos_page.py`: JavaScript atualizado

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0







