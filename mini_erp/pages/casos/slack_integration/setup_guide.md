# Guia de Configuração - Integração Slack TAQUES ERP

Este guia fornece instruções passo a passo detalhadas para configurar a integração com Slack.

## Pré-requisitos

- Conta no Slack com permissões de administrador do workspace (ou acesso para criar apps)
- Acesso ao console de desenvolvedor do Slack: https://api.slack.com/apps
- Projeto TAQUES ERP configurado e rodando

---

## Passo 1: Criar Aplicação no Slack

### 1.1 Acessar Console de Desenvolvedor

1. Acesse: https://api.slack.com/apps
2. Faça login com sua conta Slack
3. Clique no botão **"Create New App"** (canto superior direito)

### 1.2 Escolher Método de Criação

- Selecione **"From scratch"** (Do zero)
- Preencha:
  - **App Name**: `TAQUES ERP Integration` (ou nome de sua preferência)
  - **Pick a workspace**: Selecione o workspace onde a integração será usada
- Clique em **"Create App"**

---

## Passo 2: Configurar OAuth & Permissions

### 2.1 Acessar OAuth Settings

1. No menu lateral esquerdo, clique em **"OAuth & Permissions"**
2. Role até a seção **"Redirect URLs"**

### 2.2 Adicionar URL de Redirecionamento

1. Clique em **"Add New Redirect URL"**
2. Adicione a URL do seu ambiente:
   - **Desenvolvimento**: `http://localhost:8080/casos/slack/oauth/callback`
   - **Produção**: `https://seu-dominio.com/casos/slack/oauth/callback`
3. Clique em **"Save URLs"**

### 2.3 Configurar Scopes (Bot Token Scopes)

Na seção **"Scoped Bot Token Scopes"**, adicione os seguintes scopes:

#### Scopes Obrigatórios:
- ✅ `channels:read` - Ver informações básicas de canais públicos
- ✅ `channels:history` - Ver mensagens em canais públicos
- ✅ `users:read` - Ver informações sobre usuários
- ✅ `users:read.email` - Ver email de usuários

#### Scopes Recomendados (opcionais, mas úteis):
- ✅ `groups:read` - Ver informações de canais privados
- ✅ `groups:history` - Ver mensagens em canais privados
- ✅ `files:read` - Ver arquivos compartilhados em canais
- ✅ `emoji:read` - Ver emojis customizados do workspace

**Como adicionar:**
1. Clique no dropdown **"Add an OAuth Scope"**
2. Digite o nome do scope (ex: `channels:read`)
3. Selecione da lista
4. Repita para todos os scopes necessários

### 2.4 Salvar Credenciais

Após adicionar os scopes, role até o topo da página e encontre:

- **Client ID**: Copie este valor (você precisará depois)
- **Client Secret**: Clique em **"Show"** e copie (mantenha em segredo!)

---

## Passo 3: Configurar Event Subscriptions (Opcional, para Tempo Real)

Se quiser receber mensagens em tempo real via webhook:

### 3.1 Ativar Event Subscriptions

1. No menu lateral, clique em **"Event Subscriptions"**
2. Ative o toggle **"Enable Events"**

### 3.2 Configurar Request URL

1. Em **"Request URL"**, você precisará de uma URL pública acessível
2. Para desenvolvimento, use **ngrok** ou similar:
   ```bash
   ngrok http 8080
   ```
3. Copie a URL HTTPS do ngrok (ex: `https://abc123.ngrok.io`)
4. Adicione `/casos/slack/webhook` ao final
5. Cole no campo **"Request URL"**: `https://abc123.ngrok.io/casos/slack/webhook`
6. O Slack tentará validar a URL. Se aparecer ✅ "Verified", está correto

### 3.3 Subscrever Eventos

Na seção **"Subscribe to bot events"**, adicione:

- ✅ `message.channels` - Mensagens em canais públicos
- ✅ `message.groups` - Mensagens em canais privados (se usar)
- ✅ `message.changed` - Mensagens editadas
- ✅ `message.deleted` - Mensagens deletadas

Clique em **"Save Changes"**

### 3.4 Obter Signing Secret

1. No menu lateral, clique em **"Basic Information"**
2. Role até a seção **"App Credentials"**
3. Em **"Signing Secret"**, clique em **"Show"**
4. Copie o valor (você precisará depois)

---

## Passo 4: Instalar App no Workspace

### 4.1 Instalar no Workspace

1. No menu lateral, clique em **"Install App"** (ou **"OAuth & Permissions"** → **"Install App to Workspace"**)
2. Revise as permissões solicitadas
3. Clique em **"Allow"**
4. Você será redirecionado para uma página de confirmação

---

## Passo 5: Configurar Variáveis de Ambiente

### 5.1 Copiar Arquivo de Exemplo

No diretório raiz do projeto, copie o arquivo de exemplo:

```bash
cp env.example .env
```

### 5.2 Preencher Credenciais

Edite o arquivo `.env` e preencha:

```bash
# Credenciais obtidas do Slack
SLACK_CLIENT_ID=seu_client_id_aqui
SLACK_CLIENT_SECRET=seu_client_secret_aqui
SLACK_SIGNING_SECRET=seu_signing_secret_aqui

# URL base (ajuste conforme ambiente)
BASE_URL=http://localhost:8080

# Gerar chave de criptografia (execute no terminal):
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SLACK_ENCRYPTION_KEY=sua_chave_gerada_aqui
```

### 5.3 Gerar Chave de Criptografia

Execute no terminal:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie a saída e cole em `SLACK_ENCRYPTION_KEY` no arquivo `.env`.

---

## Passo 6: Verificar Configuração

### 6.1 Reiniciar Servidor

Se o servidor estiver rodando, reinicie para carregar as novas variáveis de ambiente:

```bash
# Parar servidor (Ctrl+C)
# Iniciar novamente
python3 iniciar.py
```

### 6.2 Acessar Página de Configurações

1. Acesse: `http://localhost:8080/casos/slack/settings`
2. Verifique se o status mostra **"✅ Slack configurado"**
3. Se houver erros, verifique se todas as variáveis de ambiente estão corretas

### 6.3 Testar Conexão

1. Na página de configurações, clique em **"Conectar Slack"**
2. Você será redirecionado para o Slack
3. Autorize a aplicação
4. Você será redirecionado de volta com mensagem de sucesso

---

## Troubleshooting

### Problema: "Slack não configurado"

**Solução:**
- Verifique se o arquivo `.env` existe na raiz do projeto
- Confirme que todas as variáveis estão preenchidas (sem espaços extras)
- Reinicie o servidor após alterar `.env`

### Problema: "Erro ao trocar código por token"

**Solução:**
- Verifique se `SLACK_CLIENT_ID` e `SLACK_CLIENT_SECRET` estão corretos
- Confirme que a URL de redirecionamento no Slack corresponde à `BASE_URL`
- Verifique se o app foi instalado no workspace

### Problema: "Estado inválido" (CSRF)

**Solução:**
- Isso geralmente acontece se você abrir múltiplas abas de autorização
- Feche todas as abas e tente novamente
- Certifique-se de que os cookies do navegador estão habilitados

### Problema: Webhook não valida

**Solução:**
- Certifique-se de que a URL é acessível publicamente (use ngrok para dev)
- Verifique se a rota `/casos/slack/webhook` está implementada
- Confirme que `SLACK_SIGNING_SECRET` está correto

### Problema: "Token inválido" após conectar

**Solução:**
- O token pode ter expirado ou sido revogado
- Desconecte e reconecte o Slack
- Verifique se o app ainda está instalado no workspace

---

## Próximos Passos

Após configurar com sucesso:

1. **Vincular Canal a Caso:**
   - Acesse a página de detalhes de um caso
   - Clique em "Vincular Canal Slack"
   - Busque e selecione o canal desejado

2. **Visualizar Mensagens:**
   - As mensagens do canal vinculado aparecerão automaticamente
   - Use o botão "Atualizar" para buscar novas mensagens

3. **Gerenciar Integrações:**
   - Acesse `/casos/slack/settings` para ver status
   - Desconecte se necessário
   - Veja logs de auditoria

---

## Recursos Adicionais

- [Documentação Oficial Slack API](https://api.slack.com/docs)
- [OAuth 2.0 Flow](https://api.slack.com/authentication/oauth-v2)
- [Event Subscriptions](https://api.slack.com/events-api)
- [Scopes e Permissões](https://api.slack.com/scopes)

---

## Suporte

Se encontrar problemas não listados aqui:
1. Verifique os logs do servidor
2. Consulte a documentação oficial do Slack
3. Revise o arquivo `SLACK_INTEGRATION.md` na raiz do projeto



