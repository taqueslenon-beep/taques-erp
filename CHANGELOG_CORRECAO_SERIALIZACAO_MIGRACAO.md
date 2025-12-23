# Correção: Erro de Serialização JSON na Migração EPROC

## Data: 2025-12-XX

### Problema Identificado

Erro `TypeError: Type is not JSON serializable: DatetimeWithNanoseconds` ao acessar a aba MIGRAÇÃO no Painel do Desenvolvedor.

**Causa:**
- Campos de data do Firestore retornam objetos `DatetimeWithNanoseconds` que não são serializáveis em JSON
- Ao passar dados para a interface NiceGUI, ocorria erro 500 por tentativa de serialização JSON automática

### Solução Implementada

Criadas duas funções helper para converter timestamps do Firestore:

1. **`converter_datetime_firestore(valor, formato_saida='%d/%m/%Y')`**
   - Converte DatetimeWithNanoseconds para string formatada
   - Suporta datetime Python, strings e valores None
   - Retorna "-" para valores inválidos
   - Formato padrão: DD/MM/YYYY (configurável)

2. **`converter_timestamps_documento(documento: Dict[str, Any])`**
   - Converte todos os campos timestamp de um documento completo
   - Evita erros de serialização ao passar dados para UI
   - Campos convertidos: `data_abertura`, `data_importacao`, `data_distribuicao`, `created_at`, `updated_at`, `criado_em`, `atualizado_em`

### Modificações Realizadas

**Arquivo:** `mini_erp/pages/admin/admin_migracao_processos.py`

1. Adicionadas funções helper de conversão (linhas 72-171)
2. Aplicada conversão em `lista_processos_migracao()`:
   - Cada processo é convertido com `converter_timestamps_documento()` antes de processar
   - Campo `data_abertura` convertido com `converter_datetime_firestore()` para exibição
   - Dados convertidos armazenados em `processos_dict` (sem DatetimeWithNanoseconds)

### Campos Afetados

- ✅ `data_abertura` - Convertido para string formatada DD/MM/YYYY
- ✅ `data_importacao` - Convertido para ISO string
- ✅ `data_distribuicao` - Convertido para string formatada
- ✅ `created_at`, `updated_at` - Convertidos para ISO string
- ✅ Qualquer outro campo timestamp do Firestore

### Validação

- ✅ Tabela renderiza sem erros
- ✅ Ordenação por data funciona corretamente (usa string para ordenação)
- ✅ Processos com e sem datas são tratados adequadamente (exibe "-" quando ausente)
- ✅ Modal de completar recebe dados já convertidos (sem erro de serialização)

### Tratamento de Erros

- Funções de conversão incluem tratamento de exceções
- Logging de avisos quando conversão falha
- Fallback para valores originais convertidos para string em caso de erro

### Observações Técnicas

- Conversão acontece antes de passar dados para UI (NiceGUI)
- Dados convertidos mantêm compatibilidade com código existente
- Funções reutilizáveis para outros módulos que precisem converter timestamps


