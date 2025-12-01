# Paleta de Cores - Tabela de Processos

## Visão Geral

Este documento define a paleta de cores padrão para diferenciação visual de tipos de documentos na tabela de processos.

---

## Cores por Tipo de Documento

### 1. Processos Normais
**Características:**
- Fundo branco padrão
- Sem barra lateral especial
- Cores alternadas (par/ímpar) mantidas pelo CSS padrão

**Códigos de Cor:**
- Fundo: `#FFFFFF` (branco)
- Fundo par: `#FAFAFA` (cinza muito claro)
- Fundo ímpar: `#FFFFFF` (branco)
- Barra lateral: nenhuma

**Aplicação:**
- Processos cadastrados normais
- Não são processos futuros
- Não são acompanhamentos de terceiros

---

### 2. Processos Futuros/Previstos
**Características:**
- Fundo roxo/lilás claro
- Barra lateral roxa de 4px
- Ícone de estrela no badge de status

**Códigos de Cor:**
- Barra lateral: `#9B59B6` (roxo)
- Fundo: `#F3E5F5` (roxo muito claro/lilás)
- Hover: `#E1BEE7` (roxo claro)

**Aplicação:**
- Processos com `status === 'Futuro/Previsto'`
- Processos com `process_type === 'Futuro'`

**Identificação CSS:**
```css
.q-table tbody tr[data-status="Futuro/Previsto"],
.q-table tbody tr.future-process-row {
    background-color: #F3E5F5 !important;
    border-left: 4px solid #9B59B6 !important;
}
```

---

### 3. Acompanhamentos de Terceiros
**Características:**
- Fundo azul muito claro
- Barra lateral azul de 4px
- Estilo idêntico ao de processos futuros (barra lateral + fundo tintado)

**Códigos de Cor:**
- Barra lateral: `#4A90E2` (azul médio)
- Fundo: `#E8F1FF` (azul muito claro)
- Hover: `#D4E7FF` (azul claro)

**Aplicação:**
- Processos com `is_third_party_monitoring === True`
- `tipo_documento === 'acompanhamento_terceiros'`

**Identificação CSS:**
```css
.q-table tbody tr[data-type="third_party_monitoring"],
.q-table tbody tr.third-party-monitoring-row {
    background-color: #E8F1FF !important;
    border-left: 4px solid #4A90E2 !important;
}
```

---

## Tabela Resumo

| Tipo | Barra Lateral | Fundo | Código Barra | Código Fundo | Prioridade |
|------|---------------|-------|--------------|--------------|------------|
| Processo Normal | nenhuma | branco | - | #FFFFFF | 3 (padrão) |
| Processo Futuro | roxo | roxo claro | #9B59B6 | #F3E5F5 | 2 |
| Acompanhamento de Terceiros | azul claro | azul muito claro | #4A90E2 | #E8F1FF | 1 (máxima) |

---

## Regras de Prioridade

Quando um processo pode ser classificado em múltiplas categorias:

1. **Acompanhamentos de Terceiros** têm prioridade máxima
   - Sempre aplicam estilo azul, mesmo se também forem futuros

2. **Processos Futuros** têm prioridade média
   - Aplicam estilo roxo apenas se não forem acompanhamentos

3. **Processos Normais** são o padrão
   - Aplicam estilo branco quando não se enquadram em outras categorias

---

## Implementação Técnica

### Identificação no Código

**Python (row_data):**
```python
row_data = {
    '_id': '...',
    'status': 'Futuro/Previsto',  # Para processos futuros
    'is_third_party_monitoring': True,  # Para acompanhamentos
    ...
}
```

**JavaScript (atributos data-*):**
```html
<td data-is-third-party="true" data-status="..." data-row-id="...">
```

**CSS (seletores):**
```css
/* Acompanhamentos */
tr[data-type="third_party_monitoring"]
tr.third-party-monitoring-row

/* Processos Futuros */
tr[data-status="Futuro/Previsto"]
tr.future-process-row
```

---

## Compatibilidade

### Navegadores
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari

### Dispositivos
- ✅ Desktop
- ✅ Tablet
- ✅ Mobile (cores mantidas, barra lateral ajustada)

---

## Manutenção

### Para Adicionar Novo Tipo
1. Adicionar cores na tabela acima
2. Adicionar CSS em `ui_components.py`
3. Atualizar JavaScript em `processos_page.py`
4. Atualizar esta documentação

### Para Alterar Cores
1. Atualizar códigos hex em `ui_components.py`
2. Atualizar tabela nesta documentação
3. Testar em diferentes navegadores

---

## Referências

- **Arquivo CSS**: `mini_erp/pages/processos/ui_components.py` (TABELA_PROCESSOS_CSS)
- **Aplicação JavaScript**: `mini_erp/pages/processos/processos_page.py` (apply_row_styles)
- **CHANGELOG**: `CHANGELOG_COLORACAO_ACOMPANHAMENTOS.md`



