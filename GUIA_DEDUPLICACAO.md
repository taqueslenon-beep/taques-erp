# Guia de Deduplicação - Módulo Processos

## ✅ O que foi implementado

1. **Script de deduplicação completo** (`scripts/deduplicacao_processos.py`)
   - Backup automático antes de qualquer operação
   - Identificação de duplicatas
   - Validação de referências
   - Soft delete (marcação para deleção)
   - Detecção de outras duplicações
   - Investigação de causa raiz
   - Geração de relatório completo

2. **Filtro de processos deletados**
   - Atualizado `core.py` para filtrar processos com `isDeleted=True`
   - Atualizado `get_processes_paged()` para ignorar deletados
   - Atualizado `get_child_processes()` para ignorar deletados

3. **Função de restauração**
   - Adicionada `restore_process()` em `database.py` para recuperar processos deletados

## 🚀 Como executar

### Passo 1: Executar script de deduplicação

```bash
cd /Users/lenontaques/Desktop/taques-erp
python scripts/deduplicacao_processos.py
```

O script irá:
1. Fazer backup completo da coleção 'processes'
2. Identificar duplicatas do processo "PMSC/46545/2020"
3. Validar referências antes de deletar
4. Aplicar soft delete nos duplicados
5. Detectar outras duplicações no banco
6. Investigar causa raiz
7. Gerar relatório completo

### Passo 2: Revisar resultados

Após execução, verifique:

1. **Backup**: `backups/backup_processes_[TIMESTAMP].json`
   - Confirme que todos os processos foram salvos

2. **Relatório**: `backups/deduplication_report_[TIMESTAMP].md`
   - Revise duplicatas encontradas
   - Verifique validação de referências
   - Analise causa raiz identificada

### Passo 3: Validar no frontend

1. Reinicie o servidor (se estiver rodando)
2. Acesse o módulo de Processos
3. Verifique que processos duplicados não aparecem mais
4. Confirme que contadores estão corretos

## ⚠️ Importante

- **Soft Delete**: Processos não são deletados fisicamente, apenas marcados
- **Recuperação**: Use `restore_process(doc_id)` se precisar restaurar
- **Hard Delete**: Após 7 dias de validação, considere deletar fisicamente

## 🔧 Funções disponíveis

### Restaurar processo deletado

```python
from mini_erp.pages.processos.database import restore_process

# Restaura processo pelo ID
restore_process('process_id_aqui')
```

### Verificar processos deletados (para debug)

```python
from mini_erp.firebase_config import get_db

db = get_db()
deleted = db.collection('processes').where('isDeleted', '==', True).stream()
for doc in deleted:
    print(f"Deletado: {doc.id} - {doc.to_dict().get('title')}")
```

## 📊 Estrutura de Soft Delete

Processos deletados recebem os campos:
- `isDeleted`: `true`
- `deletedAt`: timestamp ISO da deleção
- `deletedReason`: "Deduplicação automática"
- `originalProcessId`: ID do processo original mantido

## 🎯 Próximos passos recomendados

1. **Validação de duplicatas antes de salvar**
   - Adicionar verificação em `save_process()` para evitar duplicatas

2. **Índice único no Firestore**
   - Criar índice composto para campo `numero` (se possível)

3. **Monitoramento**
   - Adicionar logs quando processo é criado
   - Alertar se número já existe

4. **Revisão de scripts de backfill**
   - Garantir idempotência (pode rodar múltiplas vezes sem duplicar)

## 📝 Notas

- O script é seguro: faz backup antes de qualquer modificação
- Soft delete permite recuperação se necessário
- Frontend já está atualizado para não mostrar processos deletados
- Relatório completo é gerado automaticamente





