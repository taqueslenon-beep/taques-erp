# Correção de Filtros - Página de Processos

## Data: 2024-12-XX

## Problema Relatado
- Filtro de "Casos" não estava retornando resultados
- Nenhum dos filtros estava funcionando corretamente
- Funcionalidade estava operacional até pouco tempo atrás

## Causas Identificadas

### 1. Extração Incompleta de Casos
- **Problema**: A função `fetch_processes()` extraía casos apenas do campo `cases`, ignorando `case_ids`
- **Impacto**: Processos com casos armazenados apenas em `case_ids` não apareciam nos filtros
- **Solução**: Implementada extração de ambos os campos (`cases` e `case_ids`) com conversão de IDs para títulos

### 2. Lógica de Comparação Incorreta nos Filtros
- **Problema**: Filtros usavam comparação por substring (`in`) em vez de igualdade exata
- **Impacto**: Filtros retornavam resultados incorretos ou nenhum resultado
- **Solução**: Alterada lógica para usar igualdade exata (case-insensitive) com fallback para substring

### 3. Normalização de Dados Inconsistente
- **Problema**: Valores de filtros não eram normalizados (trim, case-insensitive)
- **Impacto**: Filtros falhavam por diferenças de espaços ou maiúsculas/minúsculas
- **Solução**: Implementada normalização consistente em todos os filtros

## Correções Implementadas

### 1. Extração de Casos (`fetch_processes()`)
```python
# ANTES: Apenas campo 'cases'
cases_raw = proc.get('cases') or []

# DEPOIS: Múltiplos campos + conversão de IDs
cases_raw = proc.get('cases') or []
case_ids = proc.get('case_ids') or []
# Converte IDs para títulos usando get_cases_list()
# Remove duplicatas mantendo ordem
```

### 2. Filtro de Casos (`filter_rows()`)
```python
# ANTES: Comparação por substring
if any(case_filter_value.lower() in str(c).lower() for c in cases_list):

# DEPOIS: Igualdade exata + substring (fallback)
matches = any(
    str(c).strip().lower() == case_filter_value.lower() or 
    case_filter_value.lower() in str(c).strip().lower()
    for c in cases_list if c
)
```

### 3. Filtros de Clientes, Parte e Parte Contrária
```python
# ANTES: Comparação direta sem normalização
filtered = [r for r in filtered if filter_client['value'] in (r.get('clients_list') or [])]

# DEPOIS: Igualdade exata com normalização
client_filter_value = filter_client['value'].strip()
filtered = [
    r for r in filtered 
    if any(str(c).strip().lower() == client_filter_value.lower() for c in (r.get('clients_list') or []))
]
```

### 4. Filtro de Área
```python
# ANTES: Comparação direta
filtered = [r for r in filtered if r.get('area') == filter_area['value']]

# DEPOIS: Normalização de espaços
area_filter_value = filter_area['value'].strip()
filtered = [
    r for r in filtered 
    if (r.get('area') or '').strip() == area_filter_value
]
```

### 5. Logs de Debug
- Adicionados logs detalhados para rastrear aplicação de filtros
- Logs mostram filtros ativos e contagem de registros antes/depois
- Facilita diagnóstico de problemas futuros

## Arquivos Modificados

1. **`mini_erp/pages/processos/processos_page.py`**
   - Função `fetch_processes()`: Extração melhorada de casos
   - Função `filter_rows()`: Lógica de filtros corrigida
   - Logs de debug adicionados

## Testes Recomendados

### Testes Individuais
1. **Filtro de Casos**
   - Selecionar um caso específico
   - Verificar se apenas processos com aquele caso aparecem
   - Testar com processos que têm casos em `case_ids` e `cases`

2. **Filtro de Clientes**
   - Selecionar um cliente específico
   - Verificar se apenas processos daquele cliente aparecem

3. **Filtro de Parte Contrária**
   - Selecionar uma parte contrária específica
   - Verificar se apenas processos com aquela parte aparecem

4. **Filtro de Área**
   - Selecionar uma área específica
   - Verificar se apenas processos daquela área aparecem

5. **Filtro de Status**
   - Selecionar um status específico
   - Verificar se apenas processos com aquele status aparecem

### Testes Combinados
- Aplicar múltiplos filtros simultaneamente
- Verificar se a interseção está correta
- Testar limpeza de filtros (botão "Limpar")

### Testes de Performance
- Verificar performance com muitos processos
- Validar que busca por texto funciona em paralelo com filtros

## Validação

### Checklist de Validação
- [ ] Filtro de Casos retorna resultados corretos
- [ ] Filtro de Clientes retorna resultados corretos
- [ ] Filtro de Parte Contrária retorna resultados corretos
- [ ] Filtro de Área retorna resultados corretos
- [ ] Filtro de Status retorna resultados corretos
- [ ] Múltiplos filtros funcionam em combinação
- [ ] Botão "Limpar" reseta todos os filtros
- [ ] Busca por texto funciona em paralelo com filtros
- [ ] Processos com casos em `case_ids` aparecem nos filtros
- [ ] Logs de debug aparecem no console

## Notas Técnicas

### Conversão de IDs para Títulos
- A função busca todos os casos uma vez e cria um mapeamento `case_id → case_title`
- Isso evita múltiplas consultas ao Firestore
- IDs não encontrados são mantidos como string (fallback)

### Remoção de Duplicatas
- Lista de casos é processada para remover duplicatas
- Ordem original é mantida
- Espaços são normalizados (trim)

### Compatibilidade
- Mantida compatibilidade com dados antigos (campo `cases`)
- Suporte para novos formatos (campo `case_ids`)
- Fallback para ambos os formatos

## Próximos Passos (Opcional)

1. **Otimização**: Cache de conversão de IDs para títulos
2. **Melhorias**: Adicionar filtros por data de abertura
3. **UX**: Adicionar indicador visual de filtros ativos
4. **Performance**: Implementar debounce em filtros se necessário


