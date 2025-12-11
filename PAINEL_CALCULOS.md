# Cálculos de Processos no Painel

## Visão Geral

Este documento descreve a lógica de cálculo para distinção de processos no painel da página inicial, especificamente na aba "Totais".

## Mapeamento de Status

### Processos Concluídos

Processos que já tramitaram e foram finalizados:

- **"Concluído"**: Processo totalmente finalizado
- **"Concluído com pendências"**: Processo finalizado mas com pendências administrativas ou documentais

### Processos Ativos

Processos que continuam em tramitação no sistema:

- **"Em andamento"**: Processo ativo em tramitação
- **"Em monitoramento"**: Processo em fase de monitoramento/aguardando movimentação

## Fórmulas de Cálculo

### Total de Processos

```
Total de Processos = count(ALL processos)
```

Conta todos os processos cadastrados no sistema, independente do status.

### Processos Concluídos

```
Processos Concluídos = count(status IN ["Concluído", "Concluído com pendências"])
```

Soma dos processos com status de finalização.

### Processos Ativos

```
Processos Ativos = count(status IN ["Em andamento", "Em monitoramento"])
```

Soma dos processos que continuam ativos no sistema.

## Validação

**Importante**: A soma de Processos Concluídos + Processos Ativos pode ser **menor** que o Total de Processos.

Isso ocorre porque:
- Processos podem ter outros status não mapeados (ex: "Sem status", status customizados)
- Processos podem ter status nulo ou vazio
- O sistema permite flexibilidade para novos status no futuro

**Fórmula de validação:**
```
Processos Concluídos + Processos Ativos ≤ Total de Processos
```

## Implementação Técnica

### Localização no Código

- **Serviço de Dados**: `mini_erp/pages/painel/data_service.py`
  - Método: `get_total_processos()` - retorna `self.total_processos`
  - Método: `get_processos_concluidos()` - calcula processos concluídos
  - Método: `get_processos_ativos()` - calcula processos ativos

- **Interface Visual**: `mini_erp/pages/painel/tab_visualizations.py`
  - Função: `render_tab_totais()` - renderiza os cards na aba "Totais"

### Otimização de Performance

1. **Cache em Memória**: Os dados são carregados uma única vez via `PainelDataService`
2. **Sem Queries Adicionais**: Os cálculos usam dados já em memória (`self._processes`)
3. **Cache Duration**: 5 minutos (definido em `mini_erp/core.py` como `CACHE_DURATION`)

### Tratamento de Erros

- Se houver erro no cálculo, exibe "–" no lugar do número
- Logging de erros para troubleshooting (via `print()`)
- Fallback para zero (0) se sem dados

## Exemplo de Uso

### Cenário 1: Sistema com dados mistos

```
Total de Processos: 16
├─ Processos Concluídos: 7
│  ├─ "Concluído": 5
│  └─ "Concluído com pendências": 2
└─ Processos Ativos: 9
   ├─ "Em andamento": 6
   └─ "Em monitoramento": 3

Validação: 7 + 9 = 16 ✓
```

### Cenário 2: Sistema com processos não mapeados

```
Total de Processos: 20
├─ Processos Concluídos: 8
└─ Processos Ativos: 10
└─ Processos não mapeados: 2 (outros status)

Validação: 8 + 10 = 18 < 20 ✓
```

## Atualização de Dados

Os valores são atualizados automaticamente quando:

1. **Inicialização do Painel**: Carrega dados ao abrir a página
2. **Refresh Manual**: Recarrega dados ao atualizar a página
3. **Cache Expira**: Após 5 minutos, cache é invalidado e dados são recarregados

**Nota**: Mudanças em processos (criação/edição/deleção) requerem refresh do painel ou espera do cache expirar para refletir no painel.

## Próximas Melhorias

1. **Filtro por Área Jurídica**: Adicionar filtros para calcular por área
2. **Filtro por Cliente**: Adicionar filtros para calcular por cliente
3. **Gráficos Visuais**: Adicionar gráficos de pizza/barras para visualização
4. **Atualização em Tempo Real**: Invalidar cache automaticamente ao criar/editar processos
5. **Histórico Temporal**: Adicionar evolução dos valores ao longo do tempo

## Status Possíveis no Sistema

Conforme definido em `mini_erp/pages/processos/models.py`:

```python
STATUS_OPTIONS = [
    'Em andamento', 
    'Concluído', 
    'Concluído com pendências', 
    'Em monitoramento'
]
```

## Referências

- Arquivo de modelos: `mini_erp/pages/processos/models.py`
- Constante de status finalizados: `FINALIZED_STATUSES = {'Concluído', 'Concluído com pendências'}`
- Serviço de dados: `mini_erp/pages/painel/data_service.py`
- Visualizações: `mini_erp/pages/painel/tab_visualizations.py`








