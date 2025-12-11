# Relatório de Investigação - Duplicação de Processos

## Resumo Executivo

Este documento resume os findings da investigação sobre possíveis duplicações de processos no sistema TAQUES ERP.

## Análise do Código

### 1. Carregamento de Processos

**Arquivo:** `mini_erp/pages/processos/database.py`

- Função `get_all_processes()`: Wrapper que chama `get_processes_list()` do core
- Função `get_processes_list()`: Usa cache com TTL de 5 minutos (300 segundos)
- Cache thread-safe com lock para evitar consultas concorrentes

**Arquivo:** `mini_erp/core.py`

- Função `_get_collection()`: Implementa cache em memória
- Cache duration: 300 segundos (5 minutos)
- Invalidação: `invalidate_cache()` remove entrada do cache
- Problema potencial: Cache pode não ser invalidado em todas as operações de salvamento

### 2. Cache em Memória

**Localização:** `mini_erp/core.py` (linhas 20-24)

```python
_cache = {}
_cache_timestamp = {}
_cache_lock = threading.Lock()
CACHE_DURATION = 300  # 5 minutos
```

**Possíveis Problemas:**
- Cache pode conter dados desatualizados se não for invalidado corretamente
- Múltiplas instâncias do servidor podem ter caches diferentes
- TTL de 5 minutos pode ser longo demais para dados críticos

### 3. Consultas ao Firestore

**Função:** `get_processes_paged()` em `mini_erp/core.py`

- Usa queries diretas ao Firestore com filtros
- Não há verificação de duplicatas na query
- Ordenação por `title_searchable` pode causar problemas se houver duplicatas

### 4. Scripts de Backfill

**Arquivo:** `scripts/backfill_processes.py`

- Normaliza títulos e campos
- Reconstroi links com casos
- **Risco:** Pode criar duplicatas se executado múltiplas vezes sem validação

## Processos Suspeitos Identificados

1. **AIA 137428 - REFLORESTA (03/02/2020)** - Status: Em andamento
2. **AIA 39820-A - LUCIANE (12/01/2020)** - Status: Concluído
3. **AIA 39821-A - EM APP LUCIANE (12/01/2016)** - Status: Concluído
4. **PMSC/46545/2020 (25/08/2020)** - Múltiplos processos com mesmo número

## Script de Investigação

**Arquivo:** `scripts/investigar_duplicatas_processos.py`

Este script realiza:

1. ✅ Busca todos os processos diretamente do Firestore (ignorando cache)
2. ✅ Compara com processos do cache em memória
3. ✅ Identifica duplicatas por:
   - Título
   - Número de processo
   - Combinação título+número+data
4. ✅ Analisa processos suspeitos específicos
5. ✅ Gera relatório completo com findings

**Como executar:**
```bash
python scripts/investigar_duplicatas_processos.py
```

O script gera um arquivo `relatorio_duplicatas_processos_YYYYMMDD_HHMMSS.txt` com todos os findings.

## Possíveis Causas de Duplicação

### 1. Frontend (Cache)
- **Severidade:** Moderada
- **Causa:** Cache não invalidado após salvamento
- **Solução:** Garantir invalidação de cache em todas as operações de salvamento

### 2. Backend (Firestore)
- **Severidade:** Crítica
- **Causa:** Múltiplos salvamentos sem validação de unicidade
- **Solução:** Implementar validação antes de salvar

### 3. Scripts de Migração
- **Severidade:** Moderada
- **Causa:** Scripts de backfill executados múltiplas vezes
- **Solução:** Adicionar validação de existência antes de criar

### 4. Consultas Inadequadas
- **Severidade:** Baixa
- **Causa:** Queries que retornam resultados duplicados
- **Solução:** Revisar lógica de queries

## Recomendações

### Imediatas (Críticas)

1. **Executar script de investigação:**
   ```bash
   python scripts/investigar_duplicatas_processos.py
   ```

2. **Revisar relatório gerado** para identificar duplicatas reais

3. **Fazer backup completo** antes de qualquer limpeza:
   ```bash
   # Usar Firebase Console ou script de backup existente
   ```

### Curto Prazo (Moderadas)

1. **Implementar validação de unicidade:**
   - Antes de salvar processo, verificar se já existe com mesmo título+número
   - Adicionar validação em `save_process()` em `database.py`

2. **Melhorar invalidação de cache:**
   - Garantir que `invalidate_cache('processes')` seja chamado após TODOS os salvamentos
   - Adicionar logs para rastrear invalidações

3. **Reduzir TTL do cache:**
   - Considerar reduzir de 5 minutos para 1-2 minutos
   - Ou implementar invalidação mais agressiva

### Longo Prazo (Prevenção)

1. **Implementar índices únicos no Firestore:**
   - Criar índice composto (title, number) se possível
   - Ou implementar validação no código

2. **Adicionar testes de integridade:**
   - Script que roda periodicamente para detectar duplicatas
   - Alertas automáticos se duplicatas forem encontradas

3. **Documentar processo de salvamento:**
   - Fluxo claro de como processos são salvos
   - Checklist de validações antes de salvar

## Plano de Recuperação (se duplicatas forem encontradas)

### Passo 1: Backup
```bash
# Fazer backup completo do Firestore
# Usar Firebase Console ou script de backup
```

### Passo 2: Análise Manual
- Revisar cada grupo de duplicatas
- Identificar qual registro deve ser mantido
- Documentar decisões

### Passo 3: Consolidação
- Mesclar dados se necessário
- Atualizar referências em casos
- Remover duplicatas

### Passo 4: Validação
- Executar script de investigação novamente
- Verificar integridade de referências
- Testar sistema

### Passo 5: Prevenção
- Implementar validações
- Adicionar testes
- Documentar processo

## Queries para Teste no Firebase Console

### 1. Buscar processos por título específico:
```
Coleção: processes
Filtro: title == 'AIA 137428 - REFLORESTA'
```

### 2. Buscar processos por número:
```
Coleção: processes
Filtro: number == 'PMSC/46545/2020'
```

### 3. Listar todos os processos ordenados:
```
Coleção: processes
Ordenar por: _id (ou created_at se existir)
```

### 4. Buscar processos duplicados (título):
```
Coleção: processes
Agrupar por: title
Contar: documentos por título
```

## Próximos Passos

1. ✅ Script de investigação criado
2. ⏳ Executar script de investigação
3. ⏳ Revisar relatório gerado
4. ⏳ Decidir sobre ações de limpeza (se necessário)
5. ⏳ Implementar validações de prevenção

## Contato e Suporte

Para dúvidas sobre este relatório ou sobre a investigação, consulte:
- Script de investigação: `scripts/investigar_duplicatas_processos.py`
- Documentação de processos: `mini_erp/pages/processos/`

---

**Data do Relatório:** 2024-12-XX
**Versão:** 1.0








