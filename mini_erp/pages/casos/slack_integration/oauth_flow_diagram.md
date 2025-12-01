# Diagrama de Fluxo OAuth2 - Integração Slack

Este documento descreve o fluxo completo de autenticação OAuth2 com Slack.

---

## Fluxo de Autenticação OAuth2

```
┌─────────────┐
│   Usuário   │
│  (Navegador)│
└──────┬──────┘
       │
       │ 1. Clica em "Conectar Slack"
       │    POST /casos/slack/settings
       ▼
┌─────────────────────────────────────┐
│  Sistema TAQUES ERP                 │
│  - Gera state token (CSRF)          │
│  - Armazena em session storage      │
│  - Gera URL OAuth com state         │
└──────┬──────────────────────────────┘
       │
       │ 2. Redireciona para URL OAuth
       │    GET https://slack.com/oauth/v2/authorize
       │    ?client_id=xxx
       │    &scope=channels:read,channels:history,...
       │    &redirect_uri=xxx
       │    &state=<token_aleatorio>
       ▼
┌─────────────────────────────────────┐
│  Slack Authorization Server          │
│  - Valida client_id                  │
│  - Solicita autorização ao usuário   │
│  - Usuário autoriza permissões       │
└──────┬──────────────────────────────┘
       │
       │ 3. Usuário autoriza
       │
       │ 4. Redireciona para callback
       │    GET /casos/slack/oauth/callback
       │    ?code=<authorization_code>
       │    &state=<token_aleatorio>
       ▼
┌─────────────────────────────────────┐
│  Handler OAuth Callback              │
│  - Valida rate limiting (IP)         │
│  - Verifica state (CSRF)             │
│  - Troca code por access_token       │
└──────┬──────────────────────────────┘
       │
       │ 5. POST https://oauth2.slack.com/api/token
       │    code, client_id, client_secret
       ▼
┌─────────────────────────────────────┐
│  Slack Token Endpoint                │
│  - Valida código                     │
│  - Retorna access_token              │
│  - Retorna refresh_token (opcional)  │
└──────┬──────────────────────────────┘
       │
       │ 6. Recebe tokens
       │    { access_token, refresh_token, ... }
       ▼
┌─────────────────────────────────────┐
│  Sistema TAQUES ERP                 │
│  - Criptografa token                │
│  - Salva no Firestore               │
│  - Registra auditoria               │
│  - Redireciona para página sucesso  │
└──────┬──────────────────────────────┘
       │
       │ 7. Exibe página de sucesso
       ▼
┌─────────────┐
│   Usuário   │
│  (Navegador)│
│  Conectado! │
└─────────────┘
```

---

## Fluxo Detalhado Passo a Passo

### Passo 1: Início da Autenticação

**Local:** Página de configurações (`/casos/slack/settings`)

1. Usuário clica no botão "Conectar Slack"
2. Sistema gera token `state` aleatório usando `secrets.token_urlsafe(32)`
3. Token `state` é armazenado em `app.storage.user['slack_oauth_state']`
4. Sistema gera URL OAuth usando `get_oauth_url(state)`
5. Usuário é redirecionado para URL do Slack

**Código:**
```python
state = generate_state_token()
app.storage.user['slack_oauth_state'] = state
auth_url = get_oauth_url(state)
ui.open(auth_url, new_tab=True)
```

---

### Passo 2: Autorização no Slack

**Local:** Slack Authorization Server

1. Slack apresenta tela de autorização
2. Usuário revisa permissões solicitadas (scopes)
3. Usuário clica em "Allow" ou "Deny"
4. Se "Deny", Slack redireciona com `?error=access_denied`
5. Se "Allow", Slack gera `authorization_code` temporário

**URL de Autorização:**
```
https://slack.com/oauth/v2/authorize?
  client_id=SEU_CLIENT_ID&
  scope=channels:read,channels:history,users:read,users:read.email&
  redirect_uri=http://localhost:8080/casos/slack/oauth/callback&
  state=TOKEN_GERADO_ALEATORIAMENTE
```

---

### Passo 3: Callback OAuth

**Local:** Handler `/casos/slack/oauth/callback`

**Validações de Segurança:**

1. **Rate Limiting:**
   - Verifica se IP não excedeu 5 tentativas/minuto
   - Se excedeu, retorna erro

2. **Validação de State (CSRF):**
   - Compara `state` recebido com armazenado
   - Se não corresponder, rejeita (possível ataque CSRF)

3. **Verificação de Erros:**
   - Se Slack retornou erro (`?error=...`), registra e exibe

4. **Validação de Usuário:**
   - Verifica se usuário está autenticado
   - Obtém `user_id` do usuário atual

**Código:**
```python
# Verifica rate limit
if not _check_rate_limit(client_ip):
    return _render_error_page(...)

# Valida state (CSRF)
stored_state = app.storage.user.get('slack_oauth_state')
if state != stored_state:
    return _render_error_page(...)
```

---

### Passo 4: Troca de Código por Token

**Local:** Handler faz requisição ao Slack Token Endpoint

**Requisição:**
```http
POST https://oauth2.slack.com/api/token
Content-Type: application/x-www-form-urlencoded

code=AUTHORIZATION_CODE&
client_id=SEU_CLIENT_ID&
client_secret=SEU_CLIENT_SECRET&
redirect_uri=http://localhost:8080/casos/slack/oauth/callback
```

**Resposta de Sucesso:**
```json
{
  "ok": true,
  "access_token": "xoxb-...",
  "token_type": "bot",
  "scope": "channels:read,channels:history,...",
  "bot_user_id": "U123456",
  "app_id": "A123456",
  "team": {
    "id": "T123456",
    "name": "Meu Workspace"
  },
  "authed_user": {
    "id": "U123456"
  },
  "refresh_token": "xoxe-..."  // Opcional
}
```

**Resposta de Erro:**
```json
{
  "ok": false,
  "error": "invalid_code"
}
```

---

### Passo 5: Armazenamento Seguro

**Local:** Firestore (`slack_tokens` collection)

**Processo:**

1. **Criptografia (se configurada):**
   ```python
   if SLACK_ENCRYPTION_KEY:
       encrypted_token = encrypt_token(access_token)
   ```

2. **Armazenamento:**
   ```python
   db.collection('slack_tokens').document(user_id).set({
       'access_token': encrypted_token or access_token,
       'refresh_token': refresh_token,  # Opcional
       'created_at': datetime.now(),
       'updated_at': datetime.now(),
       'team_id': team_id,
       'team_name': team_name
   })
   ```

3. **Auditoria:**
   ```python
   save_audit_log('oauth_success', {
       'user_id': user_id,
       'team_id': team_id,
       'ip': client_ip
   }, user_id)
   ```

---

### Passo 6: Página de Sucesso

**Local:** HTML renderizado pelo handler

Usuário vê página HTML confirmando sucesso:
- Ícone de sucesso
- Mensagem de confirmação
- Link para retornar às configurações
- Opção de fechar janela automaticamente

---

## Segurança Implementada

### ✅ Proteção CSRF
- Token `state` aleatório gerado
- Comparação estrita no callback
- Rejeição imediata se não corresponder

### ✅ Rate Limiting
- Máximo 5 tentativas por minuto por IP
- Previne ataques de força bruta
- Limpeza automática de tentativas antigas

### ✅ Validação de Domínio
- Whitelist de domínios permitidos
- Previne redirecionamento malicioso
- Configurável por ambiente

### ✅ Logging Seguro
- Tokens nunca logados completos
- Apenas primeiros 10 caracteres em logs
- Auditoria completa de tentativas

### ✅ Tratamento de Erros
- Erros específicos do Slack tratados
- Mensagens claras para o usuário
- Logs detalhados para debugging

---

## Fluxo de Erro

```
┌─────────────┐
│   Erro      │
└──────┬──────┘
       │
       ├─ Token expirado/inválido
       │  → Registra erro
       │  → Exibe mensagem clara
       │  → Sugere re-autenticação
       │
       ├─ State inválido (CSRF)
       │  → Registra tentativa
       │  → Rejeita requisição
       │  → Solicita nova autorização
       │
       ├─ Rate limit excedido
       │  → Registra tentativa
       │  → Retorna erro 429
       │  → Solicita aguardar
       │
       └─ Erro de rede/Slack
          → Registra erro completo
          → Exibe mensagem genérica
          → Sugere tentar novamente
```

---

## Renovação de Token (Futuro)

```
┌─────────────────────┐
│ Token expirado      │
└──────┬──────────────┘
       │
       │ 1. Detecta token inválido
       ▼
┌─────────────────────┐
│ Tem refresh_token?  │
└──────┬──────────────┘
       │
       ├─ Sim
       │  │
       │  │ 2. POST /oauth/v2/token
       │  │    refresh_token
       │  ▼
       │  ┌─────────────────────┐
       │  │ Novo access_token   │
       │  │ Salva no Firestore  │
       │  └─────────────────────┘
       │
       └─ Não
          │
          │ 3. Solicita nova autorização
          ▼
       ┌─────────────────────┐
       │ Usuário re-autoriza │
       └─────────────────────┘
```

---

## Referências

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [Slack OAuth Guide](https://api.slack.com/authentication/oauth-v2)
- [OAuth Security Best Practices](https://oauth.net/2/security-best-practices/)



