# CHANGELOG - Coloração Azul Claro para Acompanhamentos de Terceiros

## Data: 2025-01-XX

### Resumo
Implementação de coloração visual diferenciada para acompanhamentos de terceiros na tabela de processos, aplicando azul claro (similar ao estilo de processos futuros).

---

## Mudanças Implementadas

### 1. CSS - Estilos de Coloração (`ui_components.py`)
- **Arquivo**: `mini_erp/pages/processos/ui_components.py`
- **Alteração**: Adicionados estilos CSS para acompanhamentos de terceiros e ajustada cor de processos futuros

**Cores aplicadas:**
- **Acompanhamentos de Terceiros**:
  - Barra lateral: `#4A90E2` (azul médio)
  - Fundo: `#E8F1FF` (azul muito claro)
  - Hover: `#D4E7FF` (azul claro)

- **Processos Futuros** (ajustado):
  - Barra lateral: `#9B59B6` (roxo)
  - Fundo: `#F3E5F5` (roxo muito claro)
  - Hover: `#E1BEE7` (roxo claro)

- **Processos Normais**:
  - Fundo: `#FFFFFF` (branco)
  - Sem barra lateral

### 2. Identificação de Acompanhamentos (`processos_page.py`)
- **Arquivo**: `mini_erp/pages/processos/processos_page.py`
- **Alteração**: Modificado slot de célula `body-cell-data_abertura` para incluir atributos `data-*` que identificam o tipo de documento

**Atributos adicionados:**
- `data-row-id`: ID do processo
- `data-is-third-party`: Indica se é acompanhamento (`true`/`false`)
- `data-status`: Status do processo

### 3. JavaScript - Aplicação de Estilos (`processos_page.py`)
- **Arquivo**: `mini_erp/pages/processos/processos_page.py`
- **Alteração**: Implementada função `apply_row_styles()` que:
  1. Lê atributos `data-*` da primeira célula (data_abertura)
  2. Aplica classes CSS e atributos na row (`<tr>`) correspondente
  3. Prioriza acompanhamentos sobre processos futuros (se ambos aplicáveis)
  4. Mantém fallback para detectar processos futuros pelo badge de status

**Classes CSS aplicadas:**
- `third-party-monitoring-row`: Para acompanhamentos de terceiros
- `future-process-row`: Para processos futuros
- Atributos `data-type="third_party_monitoring"` e `data-status="Futuro/Previsto"`

---

## Paleta de Cores Padrão

| Tipo | Barra Lateral | Fundo | Código Barra | Código Fundo |
|------|---------------|-------|--------------|--------------|
| Processo Normal | nenhuma | branco | - | #FFFFFF |
| Processo Futuro | roxo | roxo claro | #9B59B6 | #F3E5F5 |
| Acompanhamento de Terceiros | azul claro | azul muito claro | #4A90E2 | #E8F1FF |

---

## Comportamento

### Visualização
- **Acompanhamentos de Terceiros**: Linhas com fundo azul claro (`#E8F1FF`) e barra lateral azul (`#4A90E2`)
- **Processos Futuros**: Linhas com fundo roxo claro (`#F3E5F5`) e barra lateral roxa (`#9B59B6`)
- **Processos Normais**: Linhas com fundo branco, sem barra lateral

### Prioridade de Estilos
1. **Acompanhamentos de Terceiros** (prioridade máxima)
2. **Processos Futuros**
3. **Processos Normais** (padrão)

### Cenários de Teste
- ✅ Tabela sem filtros: mostra todos os tipos com cores corretas
- ✅ Filtro por caso: acompanhamentos vinculados aparecem em azul
- ✅ Filtro por status "Futuro": processos futuros aparecem em roxo
- ✅ Clique em linha colorida: abre modal corretamente sem perder estilo

---

## Arquivos Modificados

1. `mini_erp/pages/processos/ui_components.py`
   - Ajuste de cores CSS para processos futuros
   - CSS para acompanhamentos de terceiros (já existia, confirmado)

2. `mini_erp/pages/processos/processos_page.py`
   - Slot `body-cell-data_abertura` com atributos `data-*`
   - Função `apply_row_styles()` simplificada e otimizada

---

## Compatibilidade

- **NiceGUI**: Compatível com versões que suportam slots customizados e Vue.js
- **Navegadores**: Chrome, Firefox, Edge (suportam MutationObserver)
- **Responsivo**: Funciona em diferentes tamanhos de tela

---

## Observações Técnicas

### Identificação de Acompanhamentos
Os acompanhamentos são identificados através do campo `is_third_party_monitoring` na row_data:
```python
row_data = {
    ...
    'is_third_party_monitoring': True,  # Para acompanhamentos
    ...
}
```

### Aplicação de Estilos
O JavaScript:
1. Lê atributos `data-is-third-party` e `data-status` da primeira célula
2. Sobe até a row pai (`<tr>`) e aplica classes/atributos
3. Usa MutationObserver para reagir a mudanças (pagination, filtros)

### Performance
- Estilos aplicados apenas após renderização inicial
- MutationObserver observa apenas mudanças relevantes
- Timeout de 400ms garante que DOM está pronto

---

## Próximos Passos (Opcional)

- [ ] Adicionar testes automatizados de coloração
- [ ] Documentar paleta de cores em arquivo centralizado
- [ ] Considerar tooltip explicativo ao passar mouse sobre linhas coloridas

---

## Autor
Implementação realizada conforme especificação do usuário para diferenciação visual de tipos de documentos na tabela de processos.








