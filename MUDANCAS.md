# REGISTRO DE MUDANÇAS - TAQUES ERP

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
