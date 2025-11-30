# Relatório de Deduplicação - Processos

**Data:** 30/11/2025 04:41:52
**Timestamp:** 20251130_044150

---

## 1. BACKUP

- **Arquivo:** `/Users/lenontaques/Desktop/taques-erp/backups/backup_processes_20251130_044150.json`
- **Total de processos:** 2
- **Status:** ✅ Concluído

---

## 2. DUPLICATAS IDENTIFICADAS

- **Número do processo:** TERMO CIRCUNSTANCIADO - JOCEL, CARLOS E SR. FRIEDRICH - CONTAGEM 2008
- **Total encontrado:** 2
- **Original (mantido):** ação-penal---jocel,-calros-e-sr.-friedrich
- **Duplicados:** 1

### Processo Original

- **ID:** `ação-penal---jocel,-calros-e-sr.-friedrich`
- **Título:** TERMO CIRCUNSTANCIADO - JOCEL, CARLOS E SR. FRIEDRICH - CONTAGEM 2008
- **Criado em:** 
- **Casos vinculados:** 1
- **Clientes:** 3

### Processos Duplicados

#### Duplicado 1

- **ID:** `termo-circunstanciado---jocel,-carlos-e-sr.-friedrich---contagem-2008`
- **Criado em:** 
- **Casos:** 1
- **Clientes:** 3

---

## 3. VALIDAÇÃO DE REFERÊNCIAS

- **Válido para deleção:** ✅ Sim
- **Casos referenciando:** 2
- **Acompanhamentos referenciando:** 0

---

## 4. SOFT DELETE

- **Status:** ✅ Concluído
- **Total marcados:** 1
- **Timestamp:** 2025-11-30T04:41:52.244997

### IDs Marcados para Deleção

- `termo-circunstanciado---jocel,-carlos-e-sr.-friedrich---contagem-2008`

---

## 5. OUTRAS DUPLICAÇÕES DETECTADAS

- **Total de processos no banco:** 26
- **Duplicatas por número:** 2
- **Duplicatas por título:** 1

### Duplicatas por Número (Top 20)

- **02026.002103/2008-15:** 3 cópias
- **02026.002104/2008-51:** 2 cópias

---

## 6. CAUSA RAIZ

- **Dados idênticos:** Não
- **Criados rapidamente:** Não
- **Scripts de backfill:** 3

### Possíveis Causas

- Scripts de backfill encontrados: scripts/backfill_processes.py, scripts/migrate_multiple_parent_processes.py, migrate_to_firestore.py
- Dados diferentes entre duplicatas (possível edição manual)

---

## 7. RECOMENDAÇÕES

1. **Implementar validação de duplicatas antes de salvar**
   - Verificar se processo com mesmo número já existe
   - Usar transações do Firestore para garantir atomicidade

2. **Adicionar índice único no campo 'numero'**
   - Prevenir duplicatas no nível do banco

3. **Revisar scripts de backfill**
   - Garantir idempotência (pode rodar múltiplas vezes sem duplicar)

4. **Implementar soft delete como padrão**
   - Filtrar processos deletados em todas as queries

5. **Monitorar criação de processos**
   - Adicionar logs para detectar criação duplicada

