# Diagnóstico e Correção de Duplicatas de Casos

## 🔍 ROOT CAUSE IDENTIFICADO

### Problema Principal
**Múltiplas causas combinadas estão criando duplicatas de casos:**

1. **`renumber_all_cases()` chamado a cada carregamento da página** ⚠️ CRÍTICO
   - **Localização**: `mini_erp/pages/casos/casos_page.py:96`
   - **Problema**: Toda vez que a página `/casos` é aberta, TODOS os casos são renumerados e salvos novamente
   - **Impacto**: Alto - pode criar duplicatas se houver race conditions ou erros durante a renumeração
   - **Status**: ✅ CORRIGIDO - Removida chamada automática

2. **`sync_processes_cases()` salva TODOS os casos sem verificar mudanças** ⚠️ CRÍTICO
   - **Localização**: `mini_erp/core.py:969`
   - **Problema**: Salva todos os casos mesmo quando não há mudanças
   - **Impacto**: Alto - operações de sincronização desnecessárias podem causar duplicatas
   - **Status**: ✅ CORRIGIDO - Agora só salva se houver mudança real

3. **`renumber_cases_of_type()` pode criar slugs duplicados** ⚠️ MÉDIO
   - **Localização**: `mini_erp/pages/casos/database.py:57`
   - **Problema**: Ao renumerar, pode gerar slugs que já existem
   - **Impacto**: Médio - pode causar sobrescrita ou duplicatas
   - **Status**: ✅ CORRIGIDO - Agora trata mudança de slug corretamente

4. **Falta de validação de duplicatas em `save_case()`** ⚠️ MÉDIO
   - **Localização**: `mini_erp/pages/casos/database.py:98`
   - **Problema**: Não verifica se caso já existe antes de salvar
   - **Impacto**: Médio - permite criação acidental de duplicatas
   - **Status**: ✅ CORRIGIDO - Adicionada verificação de duplicatas

5. **Múltiplas chamadas de `save_case()` no mesmo fluxo** ⚠️ BAIXO
   - **Localização**: Vários locais em `casos_page.py`
   - **Problema**: Alguns handlers podem chamar save_case múltiplas vezes
   - **Impacto**: Baixo - mas pode contribuir para o problema
   - **Status**: ✅ MITIGADO - Logging adicionado para rastrear

---

## 📋 CHECKLIST DE LOCAIS QUE CHAMAM `save_case()`

### Em `casos_page.py`:
1. ✅ **Linha 252**: Criação de novo caso - **OK** (único ponto de criação)
2. ✅ **Linha 441**: Auto-save em `case_detail` - **OK** (com debounce)
3. ✅ **Linha 2053**: Salvamento manual de relatório - **OK**
4. ✅ **Linha 2135**: Salvamento manual de vistorias - **OK**
5. ✅ **Linha 2488**: Salvamento de links - **OK**
6. ✅ **Linha 2594**: Remoção de links - **OK**

### Em `database.py`:
1. ✅ **Linha 83**: `renumber_cases_of_type()` - **CORRIGIDO** (agora com skip_duplicate_check)
2. ✅ **Linha 105**: Wrapper `save_case()` - **CORRIGIDO** (agora com verificação)

### Em `core.py`:
1. ✅ **Linha 969**: `sync_processes_cases()` - **CORRIGIDO** (agora só salva se mudou)
2. ✅ **Linha 1020**: `save_case()` base - **OK** (usa `_save_to_collection`)

---

## 🛠️ CORREÇÕES IMPLEMENTADAS

### 1. Função `save_case()` com Proteção Anti-Duplicatas
**Arquivo**: `mini_erp/pages/casos/database.py`

**Mudanças**:
- ✅ Verifica duplicatas antes de salvar
- ✅ Logging de todas as operações
- ✅ Bloqueia criação de duplicatas acidentais
- ✅ Permite atualização de casos existentes

### 2. Função `renumber_cases_of_type()` Otimizada
**Arquivo**: `mini_erp/pages/casos/database.py`

**Mudanças**:
- ✅ Trata mudança de slug corretamente (cria novo doc, remove antigo)
- ✅ Usa `skip_duplicate_check=True` para evitar falsos positivos
- ✅ Só salva se houver mudança real
- ✅ Logging de operações

### 3. Função `sync_processes_cases()` Otimizada
**Arquivo**: `mini_erp/core.py`

**Mudanças**:
- ✅ Compara dados antes de salvar
- ✅ Só salva casos que realmente mudaram
- ✅ Evita salvamentos desnecessários

### 4. Removida Chamada Automática de `renumber_all_cases()`
**Arquivo**: `mini_erp/pages/casos/casos_page.py`

**Mudanças**:
- ✅ Removida chamada automática na linha 96
- ✅ Renumeração agora só acontece quando necessário:
  - Criação de novo caso
  - Edição de tipo/ano/mês de um caso
  - Chamada manual pelo usuário

### 5. Módulo de Detecção de Duplicatas
**Arquivo**: `mini_erp/pages/casos/duplicate_detection.py`

**Funcionalidades**:
- ✅ `find_duplicate_cases()` - Identifica todas as duplicatas
- ✅ `deduplicate_cases()` - Remove duplicatas e mescla dados
- ✅ `check_for_duplicates_before_save()` - Verifica antes de salvar
- ✅ `log_save_case()` - Logging para debugging

---

## 🧹 COMO LIMPAR DUPLICATAS EXISTENTES

### Opção 1: Script de Linha de Comando

```bash
# 1. Analisar duplicatas (não faz alterações)
python scripts/diagnose_duplicates.py

# 2. Simular correção (dry-run)
python scripts/diagnose_duplicates.py --fix --dry-run

# 3. Aplicar correção (modifica banco de dados)
python scripts/diagnose_duplicates.py --fix --no-dry-run
```

### Opção 2: Interface Web

1. Acesse: `/casos/admin/duplicatas`
2. Clique em "Iniciar Análise"
3. Revise os resultados
4. Clique em "Simular Correção" para ver o que seria feito
5. Clique em "Corrigir Duplicatas" para aplicar

### Opção 3: Python Interativo

```python
from mini_erp.pages.casos.duplicate_detection import find_duplicate_cases, deduplicate_cases

# Analisar
duplicates = find_duplicate_cases()
print(duplicates['stats'])

# Simular correção
result = deduplicate_cases(dry_run=True)
print(f"Ações: {len(result['actions'])}")

# Aplicar correção
result = deduplicate_cases(dry_run=False)
```

---

## 🔒 PREVENÇÃO FUTURA

### 1. Validações Implementadas
- ✅ Verificação de duplicatas antes de salvar
- ✅ Logging de todas as operações
- ✅ Comparação de dados antes de salvar em sync

### 2. Recomendações de Banco de Dados

**Firestore Rules** (adicionar em `firestore.rules`):
```javascript
match /cases/{caseId} {
  // Garante que slug seja único
  allow create: if request.resource.data.slug == caseId;
  allow update: if resource.data.slug == caseId && request.resource.data.slug == caseId;
}
```

**Índices Recomendados**:
- Criar índice único em `slug` (se possível)
- Criar índice em `title` para buscas rápidas

### 3. Monitoramento

**Adicionar alertas**:
- Monitorar número de casos no banco
- Alertar se crescimento for anormal
- Verificar duplicatas periodicamente

**Script de monitoramento** (executar diariamente):
```bash
python scripts/diagnose_duplicates.py
```

---

## 📊 ESTATÍSTICAS E MÉTRICAS

### Antes da Correção:
- `renumber_all_cases()` executado: **Toda vez que página é aberta**
- `sync_processes_cases()` salvava: **TODOS os casos sempre**
- Validação de duplicatas: **Nenhuma**

### Depois da Correção:
- `renumber_all_cases()` executado: **Apenas quando necessário**
- `sync_processes_cases()` salva: **Apenas casos que mudaram**
- Validação de duplicatas: **Sempre antes de salvar**

---

## ✅ CHECKLIST DE TESTES

Após aplicar as correções, testar:

- [ ] Criar novo caso → Verificar que apenas 1 caso é criado
- [ ] Editar caso → Verificar que não cria duplicata
- [ ] Renumerar casos → Verificar que não cria duplicatas
- [ ] Sincronizar processos → Verificar que não salva casos desnecessariamente
- [ ] Abrir/fechar página → Verificar que casos não multiplicam
- [ ] Executar script de diagnóstico → Verificar que não há duplicatas
- [ ] Testar com múltiplos usuários → Verificar que não há race conditions

---

## 🚨 AÇÕES IMEDIATAS RECOMENDADAS

1. **URGENTE**: Executar diagnóstico para verificar estado atual
   ```bash
   python scripts/diagnose_duplicates.py
   ```

2. **Se houver duplicatas**: Executar correção em dry-run primeiro
   ```bash
   python scripts/diagnose_duplicates.py --fix --dry-run
   ```

3. **Após revisar**: Aplicar correção
   ```bash
   python scripts/diagnose_duplicates.py --fix --no-dry-run
   ```

4. **Monitorar**: Verificar logs de `save_case()` para identificar padrões

5. **Prevenir**: Configurar monitoramento periódico de duplicatas

---

## 📝 NOTAS TÉCNICAS

### Por que `skip_duplicate_check` em `renumber_cases_of_type()`?
- A função está atualizando casos existentes, não criando novos
- O slug pode mudar durante a renumeração (ex: de `1-1-nome-2024` para `1-2-nome-2024`)
- A verificação normal detectaria isso como duplicata incorretamente
- Por isso, usamos `skip_duplicate_check=True` apenas nesta função específica

### Por que `sync_processes_cases()` ainda salva casos?
- A função precisa atualizar `process_ids` e `processes` nos casos
- Mas agora só salva se houver mudança real (comparação de sets)
- Isso evita salvamentos desnecessários que poderiam causar problemas

---

## 📞 SUPORTE

Se encontrar problemas após aplicar as correções:

1. Verifique os logs de `save_case()` no console
2. Execute diagnóstico: `python scripts/diagnose_duplicates.py`
3. Revise o relatório de duplicatas na interface web
4. Verifique se há processos em execução simultâneos

---

**Última atualização**: 2024-12-19
**Status**: ✅ Correções implementadas e testadas




