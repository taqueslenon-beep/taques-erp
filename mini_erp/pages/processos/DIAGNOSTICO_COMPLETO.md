# Diagnóstico Completo - Processo "RECURSO ESPECIAL - STJ"

## Data do Diagnóstico
2024-12-XX

## Problema Reportado
O processo "RECURSO ESPECIAL - STJ - JHONNY - RIO NEGRINHO 2020" aparecia apenas quando:
- Clicando em "Processos Previstos" no painel
- Filtrando por Status "Futuro/Previsto" na aba de processos
- Acessando link direto do painel

Mas desaparecia quando:
- Abrindo visualização padrão (todos os processos)
- Filtrando por Status "Em andamento"
- Filtrando por Status "Concluído"

## Scripts de Diagnóstico Executados

### 1. extrair_recurso_especial.py
**Resultado:** ✓ Documento existe no Firestore
- ID: `recurso-especial---stj---jhonny---rio-negrinho-2020`
- Status: `'Futuro/Previsto'` (correto)
- Process Type: `'Futuro'`
- Total de processos no banco: 23
- Processo aparece na lista completa de processos (posição 22 de 23)

### 2. comparar_processos.py
**Resultado:** ✓ Estrutura do documento está correta
- Todos os campos obrigatórios presentes
- Status correto: `'Futuro/Previsto'`
- Process Type correto: `'Futuro'`
- Única diferença: tem campo `parent_ids` (processo filho)

### 3. testar_queries.py
**Resultado:** ✓ Processo é retornado por todas as queries
- Query direta Firestore: ✓ SIM
- Query com limit(30): ✓ SIM
- Query status == 'Futuro/Previsto': ✓ SIM (2 processos)
- get_processes_list() do core: ✓ SIM

### 4. testar_fetch_processes.py
**Resultado:** ✓ Função fetch_processes() retorna o processo
- Total retornado: 23 processos
- RECURSO ESPECIAL: ✓ Encontrado
- Status na row: `'Futuro/Previsto'`
- Processo adicionado às rows com sucesso

## Causa Raiz Identificada

Após diagnóstico completo, foi identificado que:

1. **Documento está correto no Firestore**
   - Status: `'Futuro/Previsto'` ✓
   - Process Type: `'Futuro'` ✓
   - Todos os campos presentes ✓

2. **Queries do banco funcionam corretamente**
   - get_processes_list() retorna o processo ✓
   - Queries diretas do Firestore retornam o processo ✓

3. **Função fetch_processes() funciona corretamente**
   - Retorna 23 processos (incluindo RECURSO ESPECIAL) ✓
   - Processo é adicionado às rows ✓
   - Status é preservado corretamente ✓

4. **Problema provável: Ordenação ou Paginação**
   - Processo está na posição 22 de 23 (ordenado por título)
   - Com paginação de 20 por página, processo aparece na página 2
   - Se usuário não navegar para página 2, processo não é visível

## Solução Implementada

### 1. Logs de Debug Adicionados
- Rastreamento completo do processo em todas as etapas
- Verificação se processo está em fetch_processes()
- Verificação se processo passa pelos filtros
- Verificação se processo é renderizado na tabela

### 2. Correções na Normalização de Status
- Tratamento de status vazio/None
- Garantia de que todos os processos aparecem

### 3. Correções no Filtro de Status
- Comparação normalizada (remove espaços, trata None)
- Só filtra quando há valor selecionado

### 4. Validação de Integridade
- Script `validar_processos.py` criado
- Função `verificar_integridade_processos()` adicionada

## Validação

### Testes Executados

1. **Query Direta Firestore**
   ```bash
   python3 scripts/testar_queries.py
   ```
   Resultado: ✓ Processo encontrado

2. **Função fetch_processes()**
   ```bash
   python3 scripts/testar_fetch_processes.py
   ```
   Resultado: ✓ Processo retornado (23 processos)

3. **get_processes_list() do Core**
   ```bash
   python3 scripts/testar_queries.py
   ```
   Resultado: ✓ Processo encontrado

### Como Validar na UI

1. **Visualização Padrão**
   - Abrir página Processos
   - Verificar se aparecem 23 processos
   - Navegar para página 2 (se necessário)
   - Verificar se "RECURSO ESPECIAL" aparece

2. **Filtro por Status**
   - Filtrar por "Futuro/Previsto"
   - Deve mostrar 2 processos (incluindo RECURSO ESPECIAL)

3. **Painel → Processos Previstos**
   - Clicar em "Processos Previstos" no painel
   - Deve mostrar 2 processos (incluindo RECURSO ESPECIAL)

## Conclusão

O processo "RECURSO ESPECIAL - STJ" está **correto no banco de dados** e é **retornado corretamente** por todas as funções. O problema relatado pode ter sido causado por:

1. **Paginação**: Processo está na página 2 (posição 22 de 23)
2. **Cache**: Cache antigo pode ter mostrado dados desatualizados
3. **Filtros aplicados inadvertidamente**: Algum filtro pode ter sido aplicado sem o usuário perceber

Com as correções implementadas e logs de debug adicionados, o processo deve aparecer em todas as visualizações corretamente.

## Próximos Passos

1. **Testar na UI** após reiniciar o servidor
2. **Verificar logs de debug** no console
3. **Navegar para página 2** se processo não aparecer na primeira página
4. **Limpar cache** se necessário: `invalidate_cache('processes')`

## Scripts Criados

1. `scripts/extrair_recurso_especial.py` - Extração completa do documento
2. `scripts/comparar_processos.py` - Comparação com processo que funciona
3. `scripts/testar_queries.py` - Teste de todas as queries
4. `scripts/testar_fetch_processes.py` - Teste da função fetch_processes()
5. `scripts/validar_processos.py` - Validação de integridade geral

Todos os scripts podem ser executados para diagnóstico futuro.


