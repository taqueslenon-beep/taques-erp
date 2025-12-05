# Pasta de Backups

Esta pasta contém backups automáticos gerados pelo script de reinicialização do sistema.

## Arquivos Gerados

- `backup_completo_[TIMESTAMP].json` - Backup completo de todas as coleções do Firestore
- `backup_checksum_[TIMESTAMP].txt` - Checksum MD5 para validação de integridade
- `storage_inventory_[TIMESTAMP].json` - Inventário de arquivos do Firebase Storage
- `sessions_[TIMESTAMP].json` - Estado de sessões ativas (sem dados sensíveis)
- `system_restart_report_[TIMESTAMP].md` - Relatório detalhado da reinicialização
- `reinicializacao_[TIMESTAMP].log` - Log detalhado de toda a operação

## Retenção

Backups são mantidos por 30 dias. Após esse período, podem ser removidos automaticamente.

## Segurança

⚠️ **IMPORTANTE**: Esta pasta contém dados sensíveis do sistema. Não compartilhe ou exponha publicamente.

## Limpeza Manual

Para limpar backups antigos manualmente:

```bash
# Remover backups com mais de 30 dias
find backups/ -name "*.json" -mtime +30 -delete
find backups/ -name "*.txt" -mtime +30 -delete
find backups/ -name "*.md" -mtime +30 -delete
find backups/ -name "*.log" -mtime +30 -delete
```





