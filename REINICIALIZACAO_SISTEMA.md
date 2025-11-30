# Reinicialização Segura do Sistema TAQUES ERP

## Visão Geral

Este documento descreve o procedimento completo para reinicialização segura do sistema TAQUES ERP, garantindo que todos os dados sejam salvos, validados e restaurados corretamente após a reinicialização.

## Objetivo

Realizar reinicialização completa e segura do sistema, garantindo que:
- ✅ Todos os dados do Firestore sejam salvos
- ✅ Estado de sessão do frontend seja preservado
- ✅ Integridade dos dados seja validada
- ✅ Sistema seja restaurado corretamente após reinicialização

## Quando Usar

Use este procedimento quando:
- Necessário reiniciar o servidor por manutenção
- Atualização crítica do sistema
- Problemas de performance que requerem reinicialização
- Mudanças de configuração que exigem restart

## Pré-requisitos

- Acesso ao servidor onde o sistema está rodando
- Credenciais Firebase configuradas
- Permissões de administrador
- Python 3.8+ instalado
- Dependências do projeto instaladas (`pip install -r requirements.txt`)

## Procedimento Passo a Passo

### 1. Preparação

Antes de iniciar, verifique:
- [ ] Nenhum usuário está executando operações críticas
- [ ] Backup anterior foi verificado (se existir)
- [ ] Espaço em disco suficiente para backups
- [ ] Conectividade com Firebase estável

### 2. Executar Script de Reinicialização

Execute o script com os parâmetros desejados:

```bash
# Reinicialização completa (recomendado)
python3 scripts/reinicializar_sistema.py --modo=completo --validar=sim --backup=sim

# Apenas criar backup (sem reiniciar)
python3 scripts/reinicializar_sistema.py --modo=backup --backup=sim

# Reinicialização sem validação (mais rápido, menos seguro)
python3 scripts/reinicializar_sistema.py --modo=completo --validar=nao --backup=sim
```

### 3. Monitorar Execução

O script executa 5 fases sequenciais:

#### FASE 1: Pré-Salvamento (5-10 minutos)
- ✅ Prepara sistema para desligamento
- ✅ Exporta dados do Firestore (todas as coleções)
- ✅ Exporta inventário do Firebase Storage
- ✅ Exporta sessões ativas
- ✅ Valida integridade do backup (MD5 checksum)

**Arquivos gerados:**
- `backups/backup_completo_[TIMESTAMP].json`
- `backups/storage_inventory_[TIMESTAMP].json`
- `backups/sessions_[TIMESTAMP].json`
- `backups/backup_checksum_[TIMESTAMP].txt`

#### FASE 2: Sincronização e Flush (2-5 minutos)
- ✅ Força sincronização com Firebase
- ✅ Limpa cache local em memória
- ✅ Fecha conexões ativas

#### FASE 3: Parada Controlada (1 minuto)
- ✅ Detecta processo do servidor
- ✅ Para servidor via SIGTERM (graceful shutdown)
- ✅ Valida que porta foi liberada

#### FASE 4: Reinicialização (2-5 minutos)
- ✅ Inicia servidor NiceGUI novamente
- ✅ Valida conectividade Firebase (Firestore, Auth, Storage)
- ✅ Restaura estado de sessão

#### FASE 5: Validação Pós-Reinicialização (5-10 minutos)
- ✅ Testes de integridade (compara backup vs Firestore)
- ✅ Testes de funcionalidade (CRUD básico)
- ✅ Testes de performance
- ✅ Gera relatório final

**Arquivo gerado:**
- `backups/system_restart_report_[TIMESTAMP].md`

### 4. Verificar Resultado

Após conclusão, verifique:
- [ ] Status final: SUCESSO ou FALHA
- [ ] Relatório em `backups/system_restart_report_[TIMESTAMP].md`
- [ ] Log detalhado em `backups/reinicializacao_[TIMESTAMP].log`
- [ ] Sistema acessível via navegador
- [ ] Dados aparecem corretamente na interface

## Checklist de Validação

### Após Reinicialização

- [ ] **Login**: Usuário consegue fazer login
- [ ] **Processos**: Lista de processos carrega corretamente
- [ ] **Casos**: Lista de casos carrega corretamente
- [ ] **Clientes**: Lista de clientes carrega corretamente
- [ ] **Criar**: É possível criar novo processo
- [ ] **Editar**: É possível editar processo existente
- [ ] **Deletar**: É possível deletar processo (teste)
- [ ] **Filtros**: Filtros funcionam corretamente
- [ ] **Performance**: Tempo de carregamento aceitável (< 3s)

### Validação de Dados

- [ ] Contagem de registros corresponde ao backup
- [ ] Nenhum documento foi corrompido
- [ ] Timestamps estão corretos
- [ ] Relacionamentos entre dados estão intactos

## Troubleshooting

### Erro: "Erro crítico. Sistema não foi alterado."

**Causa**: Falha na FASE 1 ou 2 (backup/sincronização)

**Solução**:
1. Verifique conectividade com Firebase
2. Verifique espaço em disco
3. Verifique permissões de escrita na pasta `backups/`
4. Consulte log detalhado: `backups/reinicializacao_[TIMESTAMP].log`

### Erro: "Porta não foi liberada"

**Causa**: Processo não parou corretamente

**Solução**:
1. Verifique manualmente se há processo na porta: `lsof -i :8080`
2. Mate processo manualmente: `kill -9 [PID]`
3. Execute script novamente

### Erro: "Servidor não iniciou corretamente"

**Causa**: Problema ao iniciar servidor

**Solução**:
1. Verifique se porta está disponível
2. Verifique logs do servidor
3. Tente iniciar manualmente: `python3 -m mini_erp.main`
4. Verifique dependências instaladas

### Erro: "Falha na validação Firebase"

**Causa**: Problema de conectividade ou credenciais

**Solução**:
1. Verifique credenciais Firebase em `firebase-credentials.json`
2. Verifique conectividade de rede
3. Verifique se projeto Firebase está ativo no console

### Backup muito grande ou lento

**Causa**: Muitos dados no Firestore

**Solução**:
1. Aguarde conclusão (pode levar 10-15 minutos)
2. Considere fazer backup apenas de coleções críticas
3. Verifique espaço em disco antes de iniciar

### Sessões não restauradas

**Causa**: Limitação técnica (sessões requerem contexto NiceGUI ativo)

**Solução**:
1. Não é crítico - usuários podem fazer login novamente
2. Dados do Firestore estão preservados
3. Preferências podem ser restauradas manualmente se necessário

## Estrutura de Arquivos de Backup

```
backups/
├── backup_completo_[TIMESTAMP].json      # Dados completos do Firestore
├── backup_checksum_[TIMESTAMP].txt        # MD5 checksum do backup
├── storage_inventory_[TIMESTAMP].json    # Lista de arquivos do Storage
├── sessions_[TIMESTAMP].json              # Estado de sessões
├── system_restart_report_[TIMESTAMP].md  # Relatório final
└── reinicializacao_[TIMESTAMP].log       # Log detalhado
```

## Retenção de Backups

- Backups são mantidos por **30 dias**
- Após 30 dias, backups antigos podem ser removidos automaticamente
- Sempre mantenha pelo menos o backup mais recente
- Backups críticos devem ser copiados para local externo

## Segurança e Conformidade

### LGPD
- Dados sensíveis não são expostos em logs
- Tokens de autenticação não são salvos em backups de sessão
- CPF/CNPJ são preservados mas logs não expõem valores completos

### Auditoria
- Todas as reinicializações são registradas em log
- Relatórios incluem timestamp e duração
- Histórico pode ser consultado em `backups/`

### Permissões
- Script requer acesso ao Firebase Admin SDK
- Credenciais devem estar protegidas
- Não compartilhe arquivos de backup publicamente

## Contato para Problemas Críticos

Se encontrar problemas críticos durante a reinicialização:

1. **NÃO** tente reiniciar novamente imediatamente
2. Verifique o log detalhado: `backups/reinicializacao_[TIMESTAMP].log`
3. Verifique o relatório: `backups/system_restart_report_[TIMESTAMP].md`
4. Se backup foi criado com sucesso, dados estão seguros
5. Contate administrador do sistema com:
   - Timestamp da reinicialização
   - Arquivo de log completo
   - Mensagens de erro específicas

## Histórico de Reinicializações

Para consultar histórico de reinicializações anteriores:

```bash
# Listar todos os relatórios
ls -lt backups/system_restart_report_*.md

# Ver último relatório
cat backups/system_restart_report_*.md | head -1 | xargs cat
```

## Comandos Úteis

```bash
# Verificar espaço em disco
df -h

# Verificar processos na porta
lsof -i :8080

# Verificar conectividade Firebase
python3 -c "from mini_erp.firebase_config import get_db; print('OK' if get_db() else 'ERRO')"

# Listar backups recentes
ls -lt backups/backup_completo_*.json | head -5

# Verificar checksum de um backup
md5 backups/backup_completo_[TIMESTAMP].json
```

## Notas Importantes

- ⚠️ **Nunca interrompa o script durante FASE 1 ou 2** (backup em andamento)
- ⚠️ **Sempre aguarde conclusão completa** antes de considerar operação finalizada
- ⚠️ **Verifique relatório final** antes de considerar sistema operacional
- ✅ **Backup é criado antes de qualquer alteração** - sistema pode ser restaurado se necessário
- ✅ **Script é idempotente** - pode ser executado múltiplas vezes com segurança

## Melhorias Futuras

- [ ] Restauração automática de backup em caso de falha
- [ ] Limpeza automática de backups antigos (> 30 dias)
- [ ] Notificações por email em caso de falha
- [ ] Dashboard web para monitorar status
- [ ] Backup incremental (apenas mudanças)

---

**Última atualização**: 2024-12-XX  
**Versão do script**: 1.0.0


