# Integração com Slack - Documentação Completa

## Visão Geral

Este módulo implementa integração com Slack para exibir mensagens de canais específicos dentro da página de detalhes de casos jurídicos no sistema TAQUES ERP.

## Estrutura do Módulo

```
mini_erp/pages/casos/slack_integration/
├── __init__.py                 # Exports principais
├── slack_config.py             # Configuração OAuth e tokens
├── slack_api.py                # Cliente API do Slack
├── slack_models.py             # Modelos de dados (Message, Channel, User)
├── slack_database.py           # Operações Firestore
├── slack_events.py             # Handler de webhooks
├── slack_ui.py                 # Componentes NiceGUI
└── slack_settings_page.py      # Página de configuração
```

## Funcionalidades

### 1. Autenticação OAuth2
- Fluxo completo de autorização OAuth2 com Slack
- Armazenamento seguro de tokens (criptografia necessária em produção)
- Renovação automática de tokens expirados

### 2. Gerenciamento de Canais
- Vinculação de canais Slack a casos jurídicos
- Busca de canais por nome
- Interface intuitiva para seleção de canais

### 3. Exibição de Mensagens
- Carregamento das últimas 50 mensagens de um canal
- Thread completo com avatares, autores e timestamps
- Formatação de texto do Slack (mentions, links, negrito, etc.)
- Exibição de reações

### 4. Cache Local
- Armazenamento de mensagens no Firestore
- Cache com TTL de 24 horas
- Sincronização automática

### 5. Webhooks em Tempo Real
- Recebimento de eventos do Slack via webhook
- Validação de assinatura HMAC SHA256
- Atualização automática de cache

### 6. Auditoria
- Logs de todas as ações (vinculação, desvinculação, etc.)
- Rastreamento de usuários que realizaram ações

## Configuração

### 1. Variáveis de Ambiente

Configure as seguintes variáveis no arquivo `.env` ou nas variáveis de ambiente:

```bash
SLACK_CLIENT_ID=seu_client_id
SLACK_CLIENT_SECRET=seu_client_secret
SLACK_SIGNING_SECRET=seu_signing_secret
BASE_URL=http://localhost:8080  # URL base do sistema
```

### 2. Configuração no Slack

1. Acesse https://api.slack.com/apps
2. Crie uma nova aplicação
3. Configure OAuth & Permissions:
   - Redirect URLs: `http://localhost:8080/casos/slack/oauth/callback`
   - Scopes necessários:
     - `channels:history` - Ler histórico de mensagens
     - `channels:read` - Listar canais
     - `chat:write` - Enviar mensagens (opcional)
     - `users:read` - Obter informações de usuários
     - `users:read.email` - Obter email dos usuários

4. Configure Event Subscriptions:
   - Request URL: `http://localhost:8080/casos/slack/webhook`
   - Subscribe to events:
     - `message.channels` - Mensagens em canais públicos
     - `message.groups` - Mensagens em canais privados
     - `message.changed` - Mensagens editadas
     - `message.deleted` - Mensagens deletadas

5. Copie o Signing Secret para a variável `SLACK_SIGNING_SECRET`

### 3. Instalação de Dependências

```bash
pip install -r requirements.txt
```

As seguintes dependências são necessárias:
- `slack-sdk` - Cliente oficial do Slack
- `python-dotenv` - Gerenciamento de variáveis de ambiente
- `requests` - Para requisições HTTP

## Uso

### 1. Conectar Conta Slack

1. Acesse `/casos/slack/settings`
2. Clique em "Conectar Slack"
3. Autorize a aplicação no Slack
4. Você será redirecionado de volta e a conta será vinculada

### 2. Vincular Canal a um Caso

1. Abra a página de detalhes de um caso
2. Na seção de integração Slack, clique em "Vincular Canal"
3. Busque o canal desejado
4. Clique em "Vincular"

### 3. Visualizar Mensagens

As mensagens aparecem automaticamente na página de detalhes do caso quando um canal está vinculado.

## Arquitetura

### Fluxo de Dados

```
1. Usuário acessa página do caso
   ↓
2. Sistema busca canal vinculado (Firestore)
   ↓
3. Se encontrado, busca token do usuário (Firestore)
   ↓
4. Busca mensagens via API Slack
   ↓
5. Cache local (Firestore)
   ↓
6. Renderização na UI
```

### Webhook em Tempo Real

```
1. Slack envia evento (nova mensagem)
   ↓
2. Verificação de assinatura HMAC
   ↓
3. Processamento do evento
   ↓
4. Atualização do cache
   ↓
5. Notificação de clientes (futuro: WebSocket)
```

## Segurança

### ⚠️ IMPORTANTE - Token Storage

**ATENÇÃO**: Atualmente, os tokens são armazenados em texto plano no Firestore. Isso NÃO é seguro para produção.

**Ação necessária**:
1. Implementar criptografia antes de salvar tokens
2. Usar uma biblioteca de criptografia (ex: `cryptography`)
3. Armazenar chave de criptografia em variável de ambiente ou serviço de secretos

Exemplo de implementação futura:

```python
from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.environ.get('SLACK_TOKEN_ENCRYPTION_KEY')

def encrypt_token(token: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(encrypted_token.encode()).decode()
```

### Validação de Webhooks

Todos os webhooks são validados usando HMAC SHA256 com o `SLACK_SIGNING_SECRET`. Requisições inválidas são rejeitadas automaticamente.

### Rate Limiting

A API do Slack tem limites de taxa. O cliente implementa:
- Cache de 15 minutos para requisições repetidas
- Tratamento de erros 429 (Too Many Requests)
- Retry automático após período de espera

## Otimizações

### Cache
- Mensagens são cacheadas por 24 horas
- Requisições repetidas à API usam cache de 15 minutos
- Limpeza automática de cache expirado

### Paginação
- Uso de cursores para paginação eficiente
- Busca limitada a 50 mensagens por padrão
- Suporte para buscar mais mensagens se necessário

### Performance
- Carregamento assíncrono de mensagens
- Cache de informações de usuários
- Lazy loading de avatares e imagens

## Tratamento de Erros

### Cenários Cobertos

1. **Token inválido/expirado**
   - Mensagem clara para o usuário
   - Opção de reconectar

2. **Canal não encontrado**
   - Notificação de erro
   - Opção de vincular novo canal

3. **Slack indisponível**
   - Exibição de cache local se disponível
   - Mensagem de erro clara

4. **Webhook inválido**
   - Validação de assinatura falha
   - Log de tentativa inválida

## Extensões Futuras

### Possíveis Melhorias

1. **WebSocket para atualizações em tempo real**
   - Notificação imediata de novas mensagens
   - Sem necessidade de refresh manual

2. **Envio de mensagens**
   - Permitir responder mensagens do Slack
   - Enviar notificações de casos para canais

3. **Threads**
   - Exibição completa de threads
   - Respostas inline

4. **Filtros e Busca**
   - Filtrar mensagens por data/autor
   - Busca dentro do histórico

5. **Notificações**
   - Alertas quando novas mensagens chegam
   - Integração com sistema de notificações do ERP

## Manutenção

### Limpeza de Cache

Execute periodicamente:

```python
from mini_erp.pages.casos.slack_integration.slack_database import clear_expired_cache

count = clear_expired_cache()
print(f"Removidas {count} mensagens expiradas")
```

### Monitoramento

Verifique logs de auditoria:

```python
from mini_erp.pages.casos.slack_integration.slack_database import get_audit_logs

logs = get_audit_logs(limit=100)
for log in logs:
    print(f"{log['timestamp']}: {log['action']} - {log['details']}")
```

## Troubleshooting

### Problema: Token não está sendo salvo

**Solução**: Verifique se o Firestore está configurado corretamente e se o usuário tem permissões de escrita.

### Problema: Webhook não está funcionando

**Solução**: 
1. Verifique se `SLACK_SIGNING_SECRET` está configurado
2. Confirme que a URL do webhook está acessível publicamente (use ngrok para desenvolvimento)
3. Verifique logs do servidor para erros de validação

### Problema: Mensagens não aparecem

**Solução**:
1. Verifique se o canal está vinculado ao caso
2. Confirme que o token do usuário é válido
3. Verifique se há mensagens no canal
4. Veja logs do console para erros da API

## Boas Práticas

1. **Sempre valide tokens antes de usar**
   - Use `api.test_connection()` para verificar

2. **Trate rate limits**
   - Implemente backoff exponencial
   - Use cache quando possível

3. **Mantenha cache atualizado**
   - Limpe cache expirado regularmente
   - Atualize cache quando novas mensagens chegarem

4. **Monitore uso da API**
   - Slack tem limites de taxa
   - Evite requisições desnecessárias

5. **Documente alterações**
   - Mantenha este arquivo atualizado
   - Documente mudanças em versões futuras

## Referências

- [Slack API Documentation](https://api.slack.com/docs)
- [OAuth 2.0 Flow](https://api.slack.com/authentication/oauth-v2)
- [Event Subscriptions](https://api.slack.com/events-api)
- [Rate Limits](https://api.slack.com/docs/rate-limits)

## Contato

Para dúvidas ou problemas, consulte a documentação oficial do Slack ou entre em contato com a equipe de desenvolvimento.


