# REGISTRO DE MUDANÇAS - TAQUES ERP

## 2025-12-19 - Ajustes Visuais no Módulo de Prazos

### Alterações Realizadas

**Arquivos:**
- `mini_erp/pages/prazos/prazos.py`
- `mini_erp/pages/prazos/prazos_page.py` (legado, mantido consistente)

**Descrição (somente visual):**
- Linhas zebradas na tabela de Prazos (cores sutis para legibilidade).
- Checkbox de conclusão com visual arredondado.
- Remoção da coluna **"Recorrente"** da tabela (o dado continua no backend).

**Detalhes técnicos (UI/CSS):**
- Zebra: alternância entre `#ffffff` e `#fafafa`.
- Checkbox: CSS para forçar borda arredondada no componente Quasar.

**Backup gerado antes da alteração:**
- `backups/ui_prazos_20251219_101732/`

### Screenshots

- Antes:
  - `docs/screenshots/prazos/2025-12-19_antes.png`
- Depois:
  - `docs/screenshots/prazos/2025-12-19_depois.png`

### 🔴 Ações Fora do IDE (Ordem Cronológica)

1. Suba o servidor do ERP normalmente.
2. Acesse a tela **Prazos**.
3. Tire 2 prints (antes/depois) e salve exatamente nestes caminhos:
   - `docs/screenshots/prazos/2025-12-19_antes.png`
   - `docs/screenshots/prazos/2025-12-19_depois.png`

---

## 2025-12-01 - Destaque Visual para Processos Concluídos

### Alterações Realizadas

**Arquivo:** `mini_erp/pages/processos/ui_components.py`

**Descrição:**
Implementado destaque visual em verde pastel para processos com status "Concluído" ou "Finalizado" na tabela de processos, seguindo o mesmo padrão já existente para processos "Futuro/Previsto" (roxo pastel).

**Implementação:**
- Adicionado CSS para aplicar fundo verde pastel (#E8F5E9) em linhas de processos concluídos
- Borda lateral esquerda verde (#4CAF50) de 4px para destacar visualmente
- Efeito hover com tom verde mais escuro (#C8E6C9)
- Suporte para variações de status: "Concluído" e "Finalizado"
- Classe CSS adicional `.completed-process-row` para flexibilidade futura

**Cores Utilizadas:**
- Fundo normal: `#E8F5E9` (verde pastel claro)
- Fundo hover: `#C8E6C9` (verde pastel médio)
- Borda lateral: `#4CAF50` (verde material design)

**Seletores CSS:**
```css
.q-table tbody tr[data-status="Concluído"],
.q-table tbody tr[data-status="Finalizado"],
.q-table tbody tr.completed-process-row
```

**Localização no código:**
Linhas 96-107 em `ui_components.py`

**Compatibilidade:**
- Responsivo (mobile, tablet, desktop)
- Não adiciona queries extras ao Firestore
- Segue padrão PEP 8
- Código documentado em português

---

### Histórico de Mudanças Anteriores

*(Adicionar mudanças futuras acima desta linha)*
