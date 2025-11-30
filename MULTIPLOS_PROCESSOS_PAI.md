# Feature: Múltiplos Processos Pai

## 📋 Resumo

Implementação completa para permitir que um processo seja vinculado a **múltiplos processos pai** (raiz), substituindo o sistema anterior que permitia apenas um processo pai.

## ✅ Entregas

### 1. Script de Migração
**Arquivo:** `scripts/migrate_multiple_parent_processes.py`

- ✅ Converte `parent_id` (string) → `parent_ids` (array)
- ✅ Cria backup automático antes da migração
- ✅ Modo dry-run para simulação
- ✅ Validação pós-migração
- ✅ Mantém compatibilidade com campo antigo

**Uso:**
```bash
# Simulação (sem alterações)
python scripts/migrate_multiple_parent_processes.py --dry-run

# Migração com backup
python scripts/migrate_multiple_parent_processes.py --backup

# Migração direta
python scripts/migrate_multiple_parent_processes.py
```

### 2. Estrutura de Dados (models.py)
**Arquivo:** `mini_erp/pages/processos/models.py`

- ✅ Campo `parent_ids: List[str]` (novo formato)
- ✅ Campo `parent_id: Optional[str]` mantido como DEPRECATED para compatibilidade
- ✅ Documentação atualizada

### 3. Operações CRUD (database.py)
**Arquivo:** `mini_erp/pages/processos/database.py`

- ✅ Função `save_process()` já suporta `parent_ids`
- ✅ Compatibilidade mantida com processos existentes

### 4. Lógica de Negócio (business_logic.py)
**Arquivo:** `mini_erp/pages/processos/business_logic.py`

- ✅ Validação de auto-vínculo (processo não pode ser pai de si mesmo)
- ✅ Validação de ciclos (detecta A → B → A)
- ✅ Função `validate_parent_cycles()` implementada
- ✅ Mensagens de erro claras em português

### 5. Interface do Usuário (process_dialog.py)
**Arquivo:** `mini_erp/pages/processos/process_dialog.py`

- ✅ Seção renomeada: "Processos Pai (opcional)"
- ✅ Seleção múltipla com autocomplete/filtro
- ✅ Chips/tags para exibir processos pai selecionados
- ✅ Botão "+" para adicionar novos processos pai
- ✅ Botão "x" em cada chip para remover processo pai
- ✅ Validação em tempo real (auto-vínculo)
- ✅ Suporte em NOVO PROCESSO e EDITAR PROCESSO

### 6. Backend (core.py)
**Arquivo:** `mini_erp/core.py`

- ✅ Função `save_process()` atualizada para suportar `parent_ids`
- ✅ Cálculo de `depth` baseado no maior depth dos processos pai
- ✅ Migração automática: `parent_id` → `parent_ids` (compatibilidade)
- ✅ Mantém campo `parent_id` para funções legadas

## 🔄 Migração de Dados

### Processo de Migração

1. **Backup Automático**
   - Script cria backup JSON com timestamp
   - Localização: `backup_processes_before_migration_YYYYMMDD_HHMMSS.json`

2. **Conversão**
   - Processos com `parent_id` → `parent_ids: [parent_id]`
   - Processos sem pai → `parent_ids: []`
   - Campo `parent_id` mantido para compatibilidade

3. **Validação**
   - Verifica se todos os processos têm `parent_ids`
   - Verifica consistência entre `parent_id` e `parent_ids`
   - Reporta problemas encontrados

### Rollback

Se necessário reverter a migração:

1. Restaurar backup JSON
2. Executar script de restauração (a ser criado se necessário)
3. Ou restaurar manualmente via Firebase Console

## 🎨 Interface do Usuário

### Novo Processo / Editar Processo

**Seção "Vínculos":**
- Campo: "Processos Pais (opcional)"
- Seleção múltipla com busca/filtro
- Chips laranja (#FF9800) para processos pai selecionados
- Botão "+" para adicionar
- Botão "x" em cada chip para remover

### Validações Visuais

- ⚠️ Aviso se tentar adicionar processo a si mesmo
- ⚠️ Aviso se processo já está na lista
- ❌ Erro se detectar ciclo na hierarquia

## 🔍 Validações Implementadas

### 1. Auto-vínculo
```python
if current_process_id in parent_ids:
    return False, 'Um processo não pode ser vinculado a si mesmo!'
```

### 2. Ciclos
```python
# Detecta: Processo A → Processo B → Processo A
validate_parent_cycles(parent_ids, current_process_id)
```

### 3. Processo Inativo
- Aviso exibido se processo selecionado estiver inativo (futuro)

## 📊 Estrutura de Dados

### Antes (Legado)
```json
{
  "parent_id": "processo_123",
  "depth": 1
}
```

### Depois (Novo)
```json
{
  "parent_ids": ["processo_123", "processo_456"],
  "parent_id": "processo_123",  // Mantido para compatibilidade
  "depth": 1  // Calculado baseado no maior depth dos pais
}
```

## 🧪 Testes Recomendados

1. **Migração**
   - [ ] Executar script com --dry-run
   - [ ] Verificar estatísticas
   - [ ] Executar migração real
   - [ ] Validar resultados

2. **Novo Processo**
   - [ ] Criar processo sem pais (raiz)
   - [ ] Criar processo com 1 pai
   - [ ] Criar processo com múltiplos pais
   - [ ] Tentar auto-vínculo (deve bloquear)
   - [ ] Tentar criar ciclo (deve bloquear)

3. **Editar Processo**
   - [ ] Adicionar processo pai
   - [ ] Remover processo pai
   - [ ] Adicionar múltiplos processos pai
   - [ ] Salvar e verificar persistência

4. **Visualização**
   - [ ] Verificar chips de processos pai
   - [ ] Verificar links clicáveis (futuro)

## 📝 Notas Técnicas

### Compatibilidade

- ✅ Processos antigos continuam funcionando
- ✅ Campo `parent_id` mantido para funções legadas
- ✅ Migração automática em `save_process()`

### Performance

- Índices Firestore recomendados:
  - `parent_ids` (array-contains)
  - `parent_id` (mantido para queries legadas)

### Funções Legadas

As seguintes funções ainda usam `parent_id`:
- `get_child_processes(parent_id)` - busca filhos de um pai específico
- `get_root_processes()` - busca processos raiz
- `build_process_tree()` - constrói árvore hierárquica

**Nota:** Essas funções podem ser atualizadas no futuro para suportar múltiplos pais, mas por enquanto mantêm compatibilidade.

## 🚀 Próximos Passos (Opcional)

1. Atualizar visualização de processos para exibir múltiplos processos pai
2. Adicionar links clicáveis para navegar entre processos pai
3. Atualizar `get_child_processes()` para buscar por `parent_ids`
4. Atualizar `build_process_tree()` para suportar múltiplos pais
5. Adicionar filtro por processo pai na lista de processos

## 📞 Suporte

Em caso de problemas:
1. Verificar logs do script de migração
2. Validar estrutura de dados no Firestore
3. Restaurar backup se necessário
4. Consultar documentação acima

---

**Data de Implementação:** 2024
**Versão:** 1.0
**Status:** ✅ Completo


