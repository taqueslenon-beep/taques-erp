# Documentação Técnica: Correção de Link e Regra "NA"

## Problema Identificado

### Bug 1: Link do Processo Não Era Salvo

**Sintoma:** Usuário preenche link no modal, salva, mas ao reabrir o link está vazio.

**Causa Raiz:** Campo `link_do_processo` era salvo, mas campo `link` (usado para exibição) não estava sendo incluído no dicionário de dados.

**Solução:** Adicionado campo `link` além de `link_do_processo` para compatibilidade.

### Bug 2: Número do Processo Não Era Salvo

**Sintoma:** Número preenchido não aparecia ao reabrir modal.

**Causa Raiz:** Campo `process_number` era salvo, mas campo `number` não.

**Solução:** Adicionado campo `number` além de `process_number`.

### Requisito: Regra "NA" para Acompanhamentos

**Motivo:** Acompanhamentos de terceiros usam "Parte Ativa/Passiva", não "Clientes/Parte Contrária".

**Solução:** Acompanhamentos mostram "NA" nas colunas "Clientes" e "Parte Contrária".

---

## Solução Implementada

### 1. Salvamento de Link e Número

#### Função `build_third_party_monitoring_data()`

**Antes:**
```python
data = {
    'link_do_processo': link_do_processo or '',
    # ❌ Campo 'link' não incluído
}
```

**Depois:**
```python
data = {
    'link_do_processo': link_do_processo or '',
    'link': link_do_processo or '',  # ✅ Compatibilidade
    'number': kwargs.get('number', ''),
    'process_number': kwargs.get('number', ''),  # ✅ Compatibilidade
}
```

#### Função `atualizar_acompanhamento()`

**Melhorias:**
```python
# Garantir que link está presente
link_value = updates.get('link_do_processo') or updates.get('link', '')
if link_value:
    updates['link_do_processo'] = link_value
    updates['link'] = link_value  # Também salvar como 'link'

# Garantir que número está presente
number_value = updates.get('process_number') or updates.get('number', '')
if number_value:
    updates['number'] = number_value
    updates['process_number'] = number_value
```

#### Função `criar_acompanhamento()`

**Melhorias:**
```python
# Garantir que link está presente
link_value = doc_data.get('link_do_processo') or doc_data.get('link', '')
if link_value:
    doc_data['link_do_processo'] = link_value
    doc_data['link'] = link_value

# Garantir que número está presente
number_value = doc_data.get('process_number') or doc_data.get('number', '')
if number_value:
    doc_data['number'] = number_value
    doc_data['process_number'] = number_value
```

### 2. Regra "NA" para Acompanhamentos

#### Função `fetch_acompanhamentos_terceiros()`

**Implementação:**
```python
row_data = {
    # ...
    # REGRA: Clientes e Parte Contrária são "NA" para acompanhamentos
    'clients_list': ['NA'],  # Sempre "NA" para acompanhamentos
    'opposing_list': ['NA'],  # Sempre "NA" para acompanhamentos
    # ...
}
```

#### Slots da Tabela

**Implementação:**
```javascript
// Slot para clientes
<div v-if="props.row.clients_list && props.row.clients_list.length > 0">
    <div v-if="props.row.clients_list[0] === 'NA'" class="text-xs text-gray-500 italic font-medium">
        NA
    </div>
    <div v-else>
        <!-- Lista normal de clientes -->
    </div>
</div>

// Slot para parte contrária (mesma lógica)
```

---

## Fluxo Completo

### Criar Acompanhamento com Link

```
1. Usuário preenche formulário
   └─ Link: "https://exemplo.com/processo"
   └─ Número: "1234567-89.2023.4.01.0001"
   
2. Clica "SALVAR"
   └─ build_third_party_monitoring_data() inclui 'link' e 'link_do_processo'
   └─ build_third_party_monitoring_data() inclui 'number' e 'process_number'
   
3. criar_acompanhamento() salva no Firestore
   └─ Garante que ambos os campos sejam salvos
   └─ Verifica pós-salvamento
   
4. Modal fecha e tabela recarrega
   └─ Acompanhamento aparece com link e número
   └─ Clientes e Parte Contrária mostram "NA"
   
5. Usuário reabre modal
   └─ open_modal() busca link em múltiplos campos
   └─ Link e número aparecem preenchidos
```

### Editar Acompanhamento

```
1. Usuário clica no título
   └─ Modal abre com dados pré-preenchidos
   └─ Link e número carregados corretamente
   
2. Usuário modifica link
   └─ Link: "https://novo-link.com"
   
3. Clica "SALVAR"
   └─ atualizar_acompanhamento() garante salvamento de ambos os campos
   └─ Verifica pós-salvamento
   
4. Modal fecha
   
5. Usuário reabre modal
   └─ Link atualizado aparece
```

---

## Mapeamento de Campos

### Link do Processo

| Campo no Firestore | Campo no Modal | Uso |
|-------------------|----------------|-----|
| `link_do_processo` | `link_input.value` | Principal |
| `link` | `link_input.value` | Compatibilidade |

### Número do Processo

| Campo no Firestore | Campo no Modal | Uso |
|-------------------|----------------|-----|
| `process_number` | `number_input.value` | Principal |
| `number` | `number_input.value` | Compatibilidade |

### Partes Envolvidas

| Tipo | Campo Firestore | Campo Tabela | Exibição |
|------|----------------|--------------|----------|
| Acompanhamento | `parte_ativa` | `clients_list` | "NA" |
| Acompanhamento | `parte_passiva` | `opposing_list` | "NA" |
| Processo | `clients` | `clients_list` | Lista normal |
| Processo | `opposing_parties` | `opposing_list` | Lista normal |

---

## Logs de Debug

### Logs de Construção de Dados

```
[BUILD_MONITORING_DATA] Campos incluídos: ['title', 'link', 'link_do_processo', ...]
[BUILD_MONITORING_DATA] Link: 'https://exemplo.com' ou 'https://exemplo.com'
[BUILD_MONITORING_DATA] Número: '1234567' ou '1234567'
[BUILD_MONITORING_DATA] Título: 'Acompanhamento de Jandir'
```

### Logs de Salvamento

```
[SALVAR ACOMPANHAMENTO] Link: 'https://exemplo.com'
[ATUALIZAR_ACOMPANHAMENTO] Link a salvar: 'https://exemplo.com' ou 'https://exemplo.com'
[ATUALIZAR_ACOMPANHAMENTO] Número a salvar: '1234567' ou '1234567'
[ATUALIZAR_ACOMPANHAMENTO] Verificação pós-salvamento:
  Link: 'https://exemplo.com'
  Número: '1234567'
```

### Logs de Carregamento

```
[OPEN_MODAL] Link carregado do acompanhamento: 'https://exemplo.com'
[OPEN_MODAL] Número carregado: '1234567'
```

---

## Testes

### Teste 1: Criar com Link e Número

1. Abrir modal de novo acompanhamento
2. Preencher:
   - Título: "Teste Link"
   - Link: "https://exemplo.com/teste"
   - Número: "1234567-89.2023.4.01.0001"
3. Salvar
4. **Esperado:** ✅ Link e número salvos
5. Reabrir modal
6. **Esperado:** ✅ Link e número aparecem preenchidos

### Teste 2: Editar Link

1. Editar acompanhamento existente
2. Modificar link: "https://novo-link.com"
3. Salvar
4. Reabrir modal
5. **Esperado:** ✅ Link atualizado aparece

### Teste 3: Exibição "NA"

1. Abrir tabela de processos
2. Filtrar por acompanhamentos
3. Verificar colunas:
   - "Clientes": deve mostrar "NA" (itálico cinza)
   - "Parte Contrária": deve mostrar "NA" (itálico cinza)
4. **Esperado:** ✅ "NA" aparece corretamente

---

## Troubleshooting

### Problema: Link ainda não aparece ao reabrir

**Solução:**
1. Verificar logs: `[OPEN_MODAL] Link carregado`
2. Verificar Firebase Console: campo `link` ou `link_do_processo` deve existir
3. Verificar se ambos os campos foram salvos

### Problema: "NA" não aparece na tabela

**Solução:**
1. Verificar se `clients_list` e `opposing_list` são `['NA']`
2. Verificar slots da tabela: devem detectar "NA"
3. Verificar se `is_third_party_monitoring` está marcado

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0  
**Status:** ✅ CORRIGIDO








