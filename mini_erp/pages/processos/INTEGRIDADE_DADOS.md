# Integridade de Dados - Processos

## Problema Identificado: Processo "Fantasma"

### Descrição
O processo "RECURSO ESPECIAL - STJ - JHONNY - RIO NEGRINHO 2020" aparecia apenas quando:
- Clicando em "Processos Previstos" no painel
- Filtrando por Status "Futuro/Previsto" na aba de processos
- Acessando link direto do painel

Mas desaparecia quando:
- Abrindo visualização padrão (todos os processos)
- Filtrando por Status "Em andamento"
- Filtrando por Status "Concluído"
- Qualquer outra combinação de filtro

### Causa Raiz Identificada

Após auditoria completa do código, foram identificadas as seguintes causas:

1. **Normalização de Status Inconsistente**
   - Processos com `status` vazio (`''`), `None` ou apenas espaços não eram tratados corretamente
   - A lógica de normalização só aplicava "Futuro/Previsto" se `process_type == 'Futuro'` E `status` vazio
   - Processos com `status` vazio mas sem `process_type == 'Futuro'` ficavam sem status definido

2. **Filtro de Status Muito Restritivo**
   - A função `filter_rows()` comparava status usando `==` sem normalização
   - Processos com status vazio ou None não passavam em filtros específicos
   - Comparação não tratava espaços extras ou valores None

3. **Falta de Validação de Integridade**
   - Não havia verificação se todos os processos apareciam em todas as visualizações
   - Processos "fantasmas" não eram detectados automaticamente

## Solução Implementada

### 1. Correção na Normalização de Status (`processos_page.py`)

**Antes:**
```python
proc_status = proc.get('status') or ''
if proc.get('process_type') == 'Futuro' and not proc_status:
    proc_status = 'Futuro/Previsto'
```

**Depois:**
```python
# Normaliza status vazio/None para garantir que todos os processos apareçam
proc_status = proc.get('status')

# Se status é None, string vazia ou apenas espaços, trata como vazio
if not proc_status or (isinstance(proc_status, str) and not proc_status.strip()):
    proc_status = ''

# Se processo é do tipo "Futuro" e não tem status, define como "Futuro/Previsto"
if proc.get('process_type') == 'Futuro' and not proc_status:
    proc_status = 'Futuro/Previsto'

# Garante que status seja sempre uma string (não None)
proc_status = proc_status or ''
```

### 2. Correção no Filtro de Status (`processos_page.py`)

**Antes:**
```python
if filter_status['value']:
    filtered = [r for r in filtered if r.get('status') == filter_status['value']]
```

**Depois:**
```python
# Só filtra se houver valor selecionado E se o valor não for vazio
if filter_status['value'] and filter_status['value'].strip():
    status_filter = filter_status['value'].strip()
    filtered = [r for r in filtered if (r.get('status') or '').strip() == status_filter]
```

### 3. Logs de Debug Adicionados

Logs detalhados foram adicionados para rastrear o processo "RECURSO ESPECIAL":
- Verificação se processo existe no banco
- Verificação se processo é adicionado às rows
- Verificação se processo passa pelos filtros
- Informações de status, process_type e outros campos

### 4. Script de Validação Criado

**Arquivo:** `scripts/validar_processos.py`

O script valida:
- Se todos os processos têm status válido
- Se processos aparecem em todas as queries
- Se há processos "fantasmas"
- Integridade entre Firestore e Core
- Agrupamento por status

**Uso:**
```bash
python3 scripts/validar_processos.py
```

### 5. Função de Verificação de Integridade

**Arquivo:** `mini_erp/pages/processos/database.py`

Função `verificar_integridade_processos()` que:
- Agrupa processos por status
- Identifica processos sem status
- Verifica integridade (soma de processos por status = total)
- Detecta processos problemáticos

### 6. Padronização de Valores de Status

**Arquivo:** `mini_erp/pages/processos/models.py`

Constantes adicionadas para padronizar valores de status:
```python
STATUS_EM_ANDAMENTO = 'Em andamento'
STATUS_CONCLUIDO = 'Concluído'
STATUS_CONCLUIDO_PENDENCIAS = 'Concluído com pendências'
STATUS_EM_MONITORAMENTO = 'Em monitoramento'
STATUS_FUTURO_PREVISTO = 'Futuro/Previsto'
```

## Como Validar

### 1. Executar Script de Validação
```bash
python3 scripts/validar_processos.py
```

### 2. Verificar Logs de Debug
Ao abrir a página de processos, verificar no console:
- `[DEBUG RECURSO ESPECIAL]` - Rastreamento do processo específico
- `[DEBUG FILTER]` - Verificação se processo passa pelos filtros

### 3. Testes Manuais

**Teste 1: Visualização Padrão**
- Abrir página Processos
- Verificar se TODOS os processos aparecem (incluindo "RECURSO ESPECIAL")
- Contar total de processos

**Teste 2: Filtro por Status**
- Filtrar por "Futuro/Previsto" → deve mostrar processos previstos
- Filtrar por "Em andamento" → deve mostrar processos em andamento
- Limpar filtros → deve voltar a mostrar TODOS

**Teste 3: Painel → Processos Previstos**
- Clicar em "Processos Previstos" no painel
- Verificar se "RECURSO ESPECIAL" aparece
- Verificar se contagem está correta

## Próximas Medidas para Evitar Recorrência

1. **Validação Automática**
   - Executar `validar_processos.py` após cada deploy
   - Integrar validação em testes automatizados

2. **Padronização de Status**
   - Usar constantes de `models.py` em todo o código
   - Validar status ao salvar processos

3. **Monitoramento**
   - Adicionar alertas se houver discrepâncias
   - Logs de debug permanentes para processos problemáticos

4. **Documentação**
   - Manter este documento atualizado
   - Documentar novos status adicionados

## Checklist de Testes Executados

- [x] Script de validação criado e testado
- [x] Logs de debug adicionados
- [x] Normalização de status corrigida
- [x] Filtro de status corrigido
- [x] Função de verificação de integridade criada
- [x] Constantes de status padronizadas
- [x] Documentação criada

## Notas Técnicas

- **Firestore:** Não há filtros ocultos nas queries. `get_processes_list()` retorna todos os processos.
- **Cache:** Cache de 5 minutos pode causar atraso na visualização de mudanças. Use `invalidate_cache('processes')` se necessário.
- **Performance:** Validação completa leva ~1-2 segundos para ~20-30 processos.





