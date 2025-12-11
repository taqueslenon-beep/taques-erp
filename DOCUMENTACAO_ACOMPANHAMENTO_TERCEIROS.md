# Documentação Técnica - Acompanhamento de Terceiros

## Visão Geral

O módulo de **Acompanhamento de Terceiros** permite monitorar processos de terceiros que afetam o cliente, mesmo quando o cliente não é o responsável primário. Exemplo: processo do sócio Jandir que afeta a empresa cliente.

---

## Estrutura de Dados

### Schema do Documento

Cada acompanhamento é armazenado na coleção `third_party_monitoring` do Firestore com a seguinte estrutura:

```python
{
    "id": "uuid-string",                    # ID único do documento
    "client_id": "cliente-id",              # ID do cliente vinculado (obrigatório)
    "third_party_name": "Nome do Terceiro", # Nome da pessoa/entidade (obrigatório)
    "process_title": "Título do Acompanhamento", # Descrição/título (obrigatório)
    "process_number": "1234567-89.2023.4.05.0000", # Número do processo (opcional)
    "monitoring_type": "Processo Judicial", # Tipo de acompanhamento (obrigatório)
    "start_date": "15/01/2023",            # Data de início (obrigatório, DD/MM/AAAA)
    "status": "ativo",                      # Status: ativo | concluído | suspenso
    "observations": "Observações adicionais", # Texto livre (opcional)
    "created_at": "2025-01-XXT10:30:00",   # Timestamp ISO (gerado automaticamente)
    "updated_at": "2025-01-XXT10:30:00"    # Timestamp ISO (atualizado automaticamente)
}
```

### Constantes e Enumerações

**Status Disponíveis:**

- `ativo`: Acompanhamento em andamento
- `concluído`: Acompanhamento finalizado
- `suspenso`: Acompanhamento temporariamente pausado

**Tipos de Acompanhamento:**

- `Processo Judicial`: Processo em tramitação no Poder Judiciário
- `Processo Administrativo`: Processo em órgão administrativo
- `Outro`: Outros tipos de acompanhamento

---

## Arquitetura

### Estrutura de Arquivos

```
mini_erp/pages/processos/
├── models.py              # Schema e constantes
├── database.py            # Funções CRUD
└── processos_page.py      # Interface (botão)

mini_erp/pages/painel/
└── tab_visualizations.py  # Card contador
```

### Dependências

- **Firestore**: Banco de dados NoSQL (Firebase)
- **NiceGUI**: Framework UI usado no projeto
- **Python**: Linguagem base
- **uuid**: Geração de IDs únicos

---

## Funções CRUD

### 1. Criar Acompanhamento

```python
from mini_erp.pages.processos.database import criar_acompanhamento

dados = {
    "client_id": "cliente-123",
    "third_party_name": "Jandir Silva",
    "process_title": "Processo do sócio que afeta empresa",
    "process_number": "1234567-89.2023.4.05.0000",
    "monitoring_type": "Processo Judicial",
    "start_date": "15/01/2023",
    "status": "ativo",
    "observations": "Monitorar prazos importantes"
}

doc_id = criar_acompanhamento(dados)
```

**Retorna:** ID do documento criado no Firestore

**Exceções:** Propaga erros do Firestore

---

### 2. Obter Acompanhamentos por Cliente

```python
from mini_erp.pages.processos.database import obter_acompanhamentos_por_cliente

acompanhamentos = obter_acompanhamentos_por_cliente("cliente-123")
```

**Retorna:** Lista de dicionários, ordenados por data de criação (mais recente primeiro)

---

### 3. Obter Todos os Acompanhamentos

```python
from mini_erp.pages.processos.database import obter_todos_acompanhamentos

todos = obter_todos_acompanhamentos()
```

**Retorna:** Lista de todos os acompanhamentos cadastrados

---

### 4. Contar Acompanhamentos Ativos

```python
from mini_erp.pages.processos.database import contar_acompanhamentos_ativos

# Total geral
total = contar_acompanhamentos_ativos()

# Por cliente específico
total_cliente = contar_acompanhamentos_ativos(client_id="cliente-123")
```

**Retorna:** Número inteiro (0 se não houver)

---

### 5. Obter por ID

```python
from mini_erp.pages.processos.database import obter_acompanhamento_por_id

acompanhamento = obter_acompanhamento_por_id("doc-id-123")
```

**Retorna:** Dicionário ou `None` se não encontrado

---

### 6. Atualizar Acompanhamento

```python
from mini_erp.pages.processos.database import atualizar_acompanhamento

sucesso = atualizar_acompanhamento("doc-id-123", {
    "status": "concluído",
    "observations": "Processo finalizado"
})
```

**Retorna:** `True` se bem-sucedido, `False` caso contrário

**Nota:** Campo `updated_at` é atualizado automaticamente

---

### 7. Deletar Acompanhamento

```python
from mini_erp.pages.processos.database import deletar_acompanhamento

sucesso = deletar_acompanhamento("doc-id-123")
```

**Retorna:** `True` se bem-sucedido, `False` caso contrário

---

## Cache e Performance

### Invalidação de Cache

Todas as operações de escrita (criar, atualizar, deletar) invalidam automaticamente o cache da coleção `third_party_monitoring`.

O cache é gerenciado pelo módulo `core.py` e tem duração de **5 minutos** (300 segundos).

### Otimizações

- **Queries Filtradas**: Usa `where()` do Firestore para filtrar diretamente no banco
- **Contagem Manual**: Para contagem, usa `stream()` e conta manualmente (Firestore não tem count direto eficiente)
- **Índices**: Para melhor performance, considere criar índices compostos no Firestore:
  - `status + client_id`
  - `status + created_at`

---

## Interface do Usuário

### Botão na Página de Processos

**Localização:** `/processos`

**Código:**

```python
ui.button('+ Novo Acompanhamento de Terceiro',
          icon='link',
          on_click=on_new_monitoring)
```

**Estilo:**

- Classe: `whitespace-nowrap w-full sm:w-auto`
- Props: `color=primary` (verde escuro)

### Card no Painel

**Localização:** `/` (Painel) → Aba "Totais" → Seção PROCESSOS

**Código:**

```python
with ui.card().classes('w-64 p-4 border-l-4 cursor-pointer hover:shadow-lg transition-shadow').style('border-left-color: #f59e0b;') as acompanhamentos_card:
    ui.label('Acompanhamentos de Terceiros').classes('text-gray-500 text-sm')
    ui.label(str(total_acompanhamentos_terceiros)).classes('text-3xl font-bold').style('color: #f59e0b;')
```

**Cor:** Laranja/âmbar (`#f59e0b`) - indica "vigilância"

**Comportamento:** Clique preparado para próximas fases (atualmente mostra notificação)

---

## Tratamento de Erros

### Mensagens em Português

Todas as mensagens de erro são exibidas em português brasileiro claro.

### Erros Comuns

1. **Firebase não conectado:**

   - Erro: `Erro ao criar acompanhamento de terceiro: ...`
   - Solução: Verificar credenciais do Firebase

2. **Campos obrigatórios faltando:**

   - Validação ocorre antes de salvar
   - Campos vazios são preenchidos com valores padrão

3. **Cliente não encontrado:**
   - `client_id` deve existir na coleção `clients`
   - Validação pode ser adicionada nas próximas fases

---

## Backup e Recuperação

### Backup Automático

**Status:** Placeholder documentado (não implementado na Fase 1)

**Recomendação Futura:**

- Usar Firebase Backup automático
- Exportar coleção `third_party_monitoring` periodicamente
- Manter log de auditoria de operações CRUD

### Plano de Recuperação

1. **Restaurar do Firebase Console:**

   - Acessar Firebase Console
   - Exportar coleção `third_party_monitoring`
   - Importar em novo projeto se necessário

2. **Script de Migração:**
   - Criar script similar a `migrate_to_firestore.py`
   - Exportar/Importar dados da coleção

---

## Boas Práticas

### 1. Validação de Dados

Sempre validar campos obrigatórios antes de chamar funções CRUD:

```python
if not acompanhamento_data.get('client_id'):
    raise ValueError("client_id é obrigatório")
```

### 2. Tratamento de Erros

Sempre usar try/except ao chamar funções CRUD:

```python
try:
    doc_id = criar_acompanhamento(dados)
    print(f"Acompanhamento criado: {doc_id}")
except Exception as e:
    print(f"Erro: {e}")
```

### 3. Uso de IDs

- IDs são gerados automaticamente se não fornecidos
- Use IDs consistentes (UUID) para evitar conflitos
- Nunca modifique o campo `_id` após criação

### 4. Timestamps

- `created_at` e `updated_at` são gerenciados automaticamente
- Não modifique manualmente esses campos

---

## Segurança

### Regras do Firestore (Recomendações)

```javascript
match /third_party_monitoring/{docId} {
  // Apenas usuários autenticados podem ler/escrever
  allow read, write: if request.auth != null;

  // Validações adicionais podem ser adicionadas aqui
  allow create: if request.resource.data.keys().hasAll(['client_id', 'third_party_name', 'process_title', 'status']);
}
```

**Nota:** Configure essas regras no Firebase Console em: Firestore → Rules

---

## Testes

Veja arquivo `TESTES_ACOMPANHAMENTO_TERCEIROS.md` para instruções detalhadas de teste.

---

## Roadmap

- ✅ **Fase 1**: Estrutura base, botão e card contador
- 🔄 **Fase 2**: Modal de criação/edição
- 🔄 **Fase 3**: Tabela de visualização
- 🔄 **Fase 4**: Filtros e busca
- 🔄 **Fase 5**: Integração com processos e casos

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0 (Fase 1)







