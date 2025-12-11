# CHANGELOG - Correção: Salvamento de Link e Regra "NA" para Acompanhamentos

## [1.0.0] - 2025-01-XX

### 🐛 Correções

#### Bug: Link do Processo Não Era Salvo
- **Problema:** Campo `link` não estava sendo salvo no Firestore
- **Causa:** Campo `link_do_processo` era salvo, mas campo `link` (compatibilidade) não
- **Correção:** Adicionado campo `link` além de `link_do_processo` no dicionário de dados
- **Arquivo:** `mini_erp/pages/processos/third_party_monitoring_dialog.py`

#### Bug: Número do Processo Não Era Salvo
- **Problema:** Campo `number` não estava sendo salvo corretamente
- **Causa:** Campo `process_number` era salvo, mas campo `number` (compatibilidade) não
- **Correção:** Adicionado campo `number` além de `process_number`
- **Arquivo:** `mini_erp/pages/processos/third_party_monitoring_dialog.py`

### ✨ Funcionalidades Adicionadas

#### Regra "NA" para Clientes e Parte Contrária
- **Funcionalidade:** Acompanhamentos de terceiros mostram "NA" em "Clientes" e "Parte Contrária"
- **Motivo:** Acompanhamentos usam Parte Ativa/Passiva, não Clientes/Parte Contrária
- **Implementação:** 
  - `clients_list` e `opposing_list` são definidos como `['NA']` para acompanhamentos
  - Slots da tabela detectam "NA" e exibem em itálico cinza
- **Arquivo:** `mini_erp/pages/processos/processos_page.py`

### 📝 Melhorias

#### Logs Detalhados de Salvamento
- **Campos salvos:**
  - Link: logs antes e depois de salvar
  - Número: logs antes e depois de salvar
  - Título: logs antes e depois de salvar
- **Verificação pós-salvamento:**
  - Confirma que link foi salvo
  - Confirma que número foi salvo
  - Confirma que título foi salvo

#### Compatibilidade de Campos
- **Link:**
  - `link_do_processo` (principal)
  - `link` (compatibilidade)
  
- **Número:**
  - `process_number` (principal)
  - `number` (compatibilidade)
  
- **Data:**
  - `data_de_abertura` (principal)
  - `start_date` (compatibilidade)
  
- **Tipo:**
  - `tipo_de_processo` (principal)
  - `tipo_processo` (compatibilidade)

### 🔧 Mudanças Técnicas

#### `mini_erp/pages/processos/third_party_monitoring_dialog.py`

**Função `build_third_party_monitoring_data()`:**
```python
# ANTES:
data = {
    'link_do_processo': link_do_processo or '',
    # ❌ Campo 'link' não estava incluído
}

# DEPOIS:
data = {
    'link_do_processo': link_do_processo or '',
    'link': link_do_processo or '',  # ✅ Compatibilidade
    'tipo_de_processo': tipo_processo or 'Existente',
    'tipo_processo': tipo_processo or 'Existente',  # ✅ Compatibilidade
    'data_de_abertura': data_abertura or '',
    'start_date': data_abertura or '',  # ✅ Compatibilidade
}
```

**Função `open_modal()`:**
- Busca link em múltiplos campos ao carregar
- Logs de link e número carregados

#### `mini_erp/pages/processos/database.py`

**Função `atualizar_acompanhamento()`:**
- Garante que `link` e `link_do_processo` sejam salvos
- Garante que `number` e `process_number` sejam salvos
- Logs de verificação pós-salvamento incluem link e número

**Função `criar_acompanhamento()`:**
- Garante múltiplos campos de link e número
- Logs de verificação pós-salvamento

#### `mini_erp/pages/processos/processos_page.py`

**Função `fetch_acompanhamentos_terceiros()`:**
- `clients_list` e `opposing_list` são `['NA']` para acompanhamentos
- Link busca em múltiplos campos
- Número busca em múltiplos campos

**Slots da Tabela:**
- Detecta quando lista contém apenas "NA"
- Exibe "NA" em itálico cinza
- Mantém exibição normal para processos

### 📊 Regra "NA" Implementada

#### Lógica de Exibição

**Para Acompanhamentos:**
- `clients_list = ['NA']`
- `opposing_list = ['NA']`
- Tabela exibe "NA" em itálico cinza

**Para Processos Normais:**
- `clients_list = ['Cliente 1', 'Cliente 2', ...]`
- `opposing_list = ['Parte Contrária 1', ...]`
- Tabela exibe lista normal

#### Visual na Tabela

```
| Clientes | Parte Contrária |
|----------|------------------|
| NA       | NA              |  ← Acompanhamento (itálico cinza)
| Cliente  | Parte Contrária |  ← Processo normal
```

### 🎯 Campos Garantidos para Salvamento

#### Campos de Identificação
- ✅ Título (`title`, `process_title`, `titulo`)
- ✅ Número (`number`, `process_number`)
- ✅ Link (`link`, `link_do_processo`)
- ✅ Tipo (`tipo_processo`, `tipo_de_processo`)
- ✅ Data (`data_de_abertura`, `start_date`)

#### Campos de Partes
- ✅ Parte Ativa (`parte_ativa`, `clients`)
- ✅ Parte Passiva (`parte_passiva`, `opposing_parties`)
- ✅ Outros Envolvidos (`outros_envolvidos`, `other_parties`)

### 📋 Checklist de Correção

- [x] Campo `link` sendo salvo (além de `link_do_processo`)
- [x] Campo `number` sendo salvo (além de `process_number`)
- [x] Todos os campos de identificação sendo salvos
- [x] Regra "NA" implementada para Clientes
- [x] Regra "NA" implementada para Parte Contrária
- [x] Slots da tabela exibem "NA" corretamente
- [x] Logs detalhados de salvamento
- [x] Verificação pós-salvamento de link e número
- [x] Compatibilidade com múltiplos nomes de campos

### 🧪 Testes Realizados

#### Teste 1: Criar com Link
1. Criar novo acompanhamento
2. Preencher link: "https://exemplo.com/processo"
3. Preencher número: "1234567-89.2023.4.01.0001"
4. Salvar
5. **Resultado:** ✅ Link e número salvos, aparecem ao reabrir

#### Teste 2: Editar Link
1. Editar acompanhamento existente
2. Modificar link: "https://novo-link.com"
3. Salvar
4. Reabrir modal
5. **Resultado:** ✅ Link atualizado aparece

#### Teste 3: Exibição "NA"
1. Abrir tabela de processos
2. Filtrar por acompanhamentos
3. Verificar colunas "Clientes" e "Parte Contrária"
4. **Resultado:** ✅ Mostram "NA" em itálico cinza

### 🔍 Logs de Debug

#### Logs de Salvamento
```
[BUILD_MONITORING_DATA] Link: 'https://exemplo.com' ou 'https://exemplo.com'
[BUILD_MONITORING_DATA] Número: '1234567' ou '1234567'
[SALVAR ACOMPANHAMENTO] Link: 'https://exemplo.com'
[ATUALIZAR_ACOMPANHAMENTO] Link a salvar: 'https://exemplo.com' ou 'https://exemplo.com'
[ATUALIZAR_ACOMPANHAMENTO] Verificação pós-salvamento:
  Link: 'https://exemplo.com'
  Número: '1234567'
```

#### Logs de Carregamento
```
[OPEN_MODAL] Link carregado do acompanhamento: 'https://exemplo.com'
[OPEN_MODAL] Número carregado: '1234567'
```

### 📚 Arquivos Modificados

1. `mini_erp/pages/processos/third_party_monitoring_dialog.py`
   - `build_third_party_monitoring_data()` - Adicionado campos `link` e `number`
   - `open_modal()` - Logs de link e número carregados

2. `mini_erp/pages/processos/database.py`
   - `atualizar_acompanhamento()` - Garante salvamento de link e número
   - `criar_acompanhamento()` - Garante salvamento de link e número

3. `mini_erp/pages/processos/processos_page.py`
   - `fetch_acompanhamentos_terceiros()` - Regra "NA" implementada
   - Slots da tabela - Exibição de "NA" em itálico

### 🎯 Benefícios

1. **Dados Completos:**
   - Link sempre é salvo
   - Número sempre é salvo
   - Todos os campos de identificação salvos

2. **Compatibilidade:**
   - Múltiplos nomes de campos suportados
   - Funciona com dados antigos e novos

3. **Clareza Visual:**
   - "NA" deixa claro que não se aplica
   - Diferencia acompanhamentos de processos

4. **Diagnóstico:**
   - Logs detalhados facilitam debug
   - Verificação pós-salvamento confirma persistência

---

**Versão:** 1.0.0  
**Data:** 2025-01-XX  
**Status:** ✅ CORRIGIDO








