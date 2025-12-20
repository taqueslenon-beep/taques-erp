# RELATÓRIO: ESTADO ATUAL DO SISTEMA DE USUÁRIOS

**Data:** 2025-01-27  
**Escopo:** Análise completa do sistema de autenticação, gerenciamento de usuários e permissões

---

## 📋 SUMÁRIO EXECUTIVO

### Status Geral

- ✅ **Autenticação**: Funcionando (Firebase Auth)
- ⚠️ **Gerenciamento de Usuários**: Parcial (apenas visualização)
- ❌ **Criação/Edição de Usuários**: Não existe na interface
- ⚠️ **Gerenciamento de Permissões**: Parcial (via scripts CLI)
- ✅ **Perfil do Usuário**: Funcionando (avatar, dados básicos)
- ⚠️ **Área do Cliente**: Existe como workspace, não como portal separado

---

## 1. VISÃO GERAL DO ESCRITÓRIO (Área Administrativa)

### 1.1 Sistema de Login/Autenticação

**Status:** ✅ **FUNCIONANDO**

**Arquivo:** `mini_erp/auth.py`

**Funcionalidades Implementadas:**

- Login com email e senha via Firebase Auth REST API
- Sessão persistida em `app.storage.user['user']`
- Decorator `@require_auth` para proteger rotas
- Logout com limpeza de cache (localStorage, sessionStorage, cookies)
- Funções auxiliares: `get_current_user()`, `is_authenticated()`, `logout_user()`

**Trecho Relevante:**

```14:63:mini_erp/auth.py
def login_user(email: str, password: str) -> dict:
    """
    Autentica usuário com email e senha via Firebase Auth.
    Retorna dict com 'success', 'message' e 'user' (se sucesso).
    """
    try:
        response = requests.post(FIREBASE_AUTH_URL, json={
            "email": email,
            "password": password,
            "returnSecureToken": True
        })

        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Login realizado com sucesso!",
                "user": {
                    "email": data.get("email"),
                    "uid": data.get("localId"),
                    "token": data.get("idToken"),
                    "refresh_token": data.get("refreshToken")
                }
            }
        else:
            error_message = data.get("error", {}).get("message", "Erro desconhecido")

            # Traduz mensagens de erro comuns
            error_translations = {
                "EMAIL_NOT_FOUND": "Email não encontrado",
                "INVALID_PASSWORD": "Senha incorreta",
                "INVALID_LOGIN_CREDENTIALS": "Email ou senha incorretos",
                "USER_DISABLED": "Usuário desativado",
                "TOO_MANY_ATTEMPTS_TRY_LATER": "Muitas tentativas. Tente novamente mais tarde."
            }

            return {
                "success": False,
                "message": error_translations.get(error_message, f"Erro: {error_message}"),
                "user": None
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erro de conexão: {str(e)}",
            "user": None
        }
```

**Página de Login:** `mini_erp/pages/login.py`

- Interface funcional
- Validação de campos
- Tratamento de erros
- Redirecionamento após login bem-sucedido

---

### 1.2 Tela de Gerenciamento de Usuários

**Status:** ⚠️ **PARCIAL** (apenas visualização)

**Localização:** `/configuracoes` → Aba "Usuários"

**Funcionalidades Existentes:**

- ✅ Listagem de todos os usuários do Firebase Auth
- ✅ Exibição de: email, função, data criação, último login, status
- ✅ Atualização automática a cada 5 minutos (quando aba ativa)
- ✅ Botão de atualização manual
- ✅ Ordenação por último login (mais recente primeiro)

**Funcionalidades FALTANDO:**

- ❌ Criar novo usuário
- ❌ Editar usuário existente
- ❌ Excluir usuário
- ❌ Alterar senha
- ❌ Alterar permissões/roles
- ❌ Ativar/desativar usuário
- ❌ Resetar senha

**Trecho Relevante:**

```452:547:mini_erp/pages/configuracoes.py
                # Função para listar usuários do Firebase Authentication
                def listar_usuarios_firebase():
                    """Lista todos os usuários do Firebase Authentication"""
                    try:
                        usuarios = []
                        page = auth.list_users()

                        while page:
                            for user in page.users:
                                custom_claims = user.custom_claims or {}

                                # Determina função baseada em claims
                                role = 'Usuário'
                                if custom_claims.get('admin') or custom_claims.get('role') == 'admin':
                                    role = 'Administrador'
                                elif custom_claims.get('role'):
                                    role = custom_claims.get('role').capitalize()

                                usuarios.append({
                                    'email': user.email,
                                    'uid': user.uid,
                                    'criacao': format_date(user.user_metadata.creation_timestamp),
                                    'ultimo_login': format_date(user.user_metadata.last_sign_in_timestamp),
                                    'role': role,
                                    'status': 'Inativo' if user.disabled else 'Ativo',
                                    'raw_ts': user.user_metadata.last_sign_in_timestamp or 0 # Para ordenação
                                })
                            page = page.get_next_page()

                        # Ordena por último login (mais recente primeiro)
                        usuarios.sort(key=lambda x: x['raw_ts'], reverse=True)
                        return usuarios
                    except Exception as e:
                        print(f"Erro ao listar usuários: {e}")
                        return []
```

---

### 1.3 Operações de Usuário

#### Operações Existentes (via código, não na interface):

- ✅ **Listar**: Implementado na aba Usuários
- ✅ **Buscar por UID**: Função `buscar_usuario_por_uid()` em `mini_erp/usuarios/database.py`
- ✅ **Criar (via script)**: Script `scripts/criar_usuarios_iniciais.py` cria usuários no Firestore

#### Operações Faltando (na interface):

- ❌ **Criar usuário**: Não há formulário na interface
- ❌ **Editar usuário**: Não há diálogo de edição
- ❌ **Excluir usuário**: Não há botão de exclusão
- ❌ **Alterar senha**: Não há funcionalidade
- ❌ **Resetar senha**: Não há funcionalidade
- ❌ **Ativar/Desativar**: Não há toggle na interface

**Arquivo de Database:** `mini_erp/usuarios/database.py`

- Funções CRUD existem, mas não são usadas na interface:
  - `criar_usuario()` - ✅ Existe
  - `atualizar_usuario()` - ✅ Existe
  - `excluir_usuario()` - ✅ Existe
  - `vincular_firebase_uid()` - ✅ Existe

---

### 1.4 Roles/Funções Existentes

**Status:** ⚠️ **PARCIAL** (definidas, mas não gerenciáveis via interface)

**Arquivo:** `mini_erp/usuarios/perfis.py`

**Perfis Definidos:**

1. **`cliente`**

   - Nome: "Cliente"
   - Descrição: Acesso apenas ao workspace do cliente específico
   - Workspaces: `['schmidmeier']`
   - Pode editar: `False`
   - Pode excluir: `False`

2. **`interno`**

   - Nome: "Usuário Interno"
   - Descrição: Acesso a todos os workspaces do escritório
   - Workspaces: `['schmidmeier', 'visao_geral']`
   - Pode editar: `True`
   - Pode excluir: `False`

3. **`admin`**
   - Nome: "Administrador"
   - Descrição: Acesso total ao sistema
   - Workspaces: `['schmidmeier', 'visao_geral']`
   - Pode editar: `True`
   - Pode excluir: `True`

**Como são Aplicados:**

- Via **Custom Claims** do Firebase Auth
- Campos usados: `perfil`, `role`, `admin`
- Lógica de detecção em `mini_erp/auth.py`:

```164:201:mini_erp/auth.py
def get_user_profile() -> Optional[str]:
    """
    Obtém o perfil do usuário atual via Firebase Auth custom_claims.

    Returns:
        Perfil do usuário: 'cliente', 'interno', 'df_projetos' ou None
    """
    try:
        user = get_current_user()
        if not user:
            return None

        uid = user.get('uid')
        if not uid:
            return None

        # Busca custom_claims do Firebase Auth
        firebase_user = admin_auth.get_user(uid)
        custom_claims = firebase_user.custom_claims or {}

        # Tenta obter perfil de diferentes campos possíveis
        perfil = custom_claims.get('perfil') or custom_claims.get('role') or custom_claims.get('profile')

        # Normaliza valores
        if perfil:
            perfil = perfil.lower()
            # Mapeia variações possíveis
            if perfil in ['cliente', 'client']:
                return 'cliente'
            elif perfil in ['interno', 'internal', 'admin']:
                return 'interno'
            elif perfil in ['df_projetos', 'df-projetos', 'projetos']:
                return 'df_projetos'

        return None
    except Exception as e:
        print(f"Erro ao obter perfil do usuário: {e}")
        return None
```

**Problema:** Não há interface para definir/alterar custom claims. Precisa ser feito via:

- Scripts Python (CLI)
- Firebase Console manualmente
- Firebase Admin SDK (código)

---

### 1.5 Perfil de Usuário

**Status:** ✅ **FUNCIONANDO** (parcialmente)

**Localização:** `/configuracoes` → Aba "Perfil"

**Funcionalidades Implementadas:**

- ✅ Upload de avatar com editor (crop, zoom, posicionamento)
- ✅ Visualização de avatar atual
- ✅ Exibição de email (somente leitura)
- ✅ Exibição de função/role (somente leitura)
- ✅ Armazenamento no Firebase Storage (`avatars/{user_uid}.png`)

**Funcionalidades Faltando:**

- ❌ Editar nome de exibição (função existe em `storage.py`, mas não usada)
- ❌ Alterar senha
- ❌ Alterar email
- ❌ Editar dados pessoais (telefone, etc.)

**Trecho Relevante - Avatar:**

```46:424:mini_erp/pages/configuracoes.py
            # --- PERFIL ---
            with ui.tab_panel(perfil_tab):
                ui.label('Meu Perfil').classes('text-lg font-bold mb-4')

                with ui.row().classes('w-full items-start gap-8'):
                    # Coluna do Avatar
                    with ui.column().classes('items-center gap-4'):
                        avatar_img = ui.image('https://cdn.quasar.dev/img/boy-avatar.png').classes('w-32 h-32 rounded-full shadow-md object-cover')

                        # Estado de carregamento do avatar
                        avatar_loading = {'status': False}

                        # Carrega avatar atual
                        async def load_current_avatar():
                            """Carrega o avatar do usuário do Firebase Storage"""
                            try:
                                if not user_uid:
                                    raise ValueError("UID do usuário não disponível")

                                if avatar_loading['status']:
                                    return  # Evita múltiplas chamadas simultâneas

                                avatar_loading['status'] = True

                                url = await run.io_bound(obter_url_avatar, user_uid)
                                if url:
                                    # URL já vem com timestamp do storage.py
                                    avatar_img.source = url
                                else:
                                    # Avatar padrão baseado nas iniciais ou imagem genérica
                                    avatar_img.source = f'https://ui-avatars.com/api/?name={user_email}&background=random&size=200'
                            except Exception as e:
                                print(f"Erro ao carregar avatar: {e}")
                                # Fallback para avatar padrão
                                avatar_img.source = f'https://ui-avatars.com/api/?name={user_email}&background=random&size=200'
                            finally:
                                avatar_loading['status'] = False

                        ui.timer(0.1, load_current_avatar, once=True)
```

**Função de Display Name (existe mas não usada):**

```129:178:mini_erp/storage.py
def definir_display_name(user_uid, display_name):
    """Define o nome de exibição do usuário"""
    try:
        # Validação básica
        if not display_name or len(display_name) < 2 or len(display_name) > 50:
            return False

        # Atualizar custom claims
        user = auth.get_user(user_uid)
        custom_claims = user.custom_claims or {}
        custom_claims['display_name'] = display_name

        auth.set_custom_user_claims(user_uid, custom_claims)

        # Também salvar no Firestore para redundância e facilidade de acesso
        db = firestore.client()
        db.collection('users').document(user_uid).set({
            'display_name': display_name,
            'email': user.email,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True)

        return True
    except Exception as e:
        print(f"Erro ao definir display_name: {e}")
        return False

def obter_display_name(user_uid):
    """Obtém o nome de exibição do usuário"""
    try:
        user = auth.get_user(user_uid)
        if user.custom_claims and 'display_name' in user.custom_claims:
            return user.custom_claims['display_name']

        # Fallback para Firestore
        db = firestore.client()
        doc = db.collection('users').document(user_uid).get()
        if doc.exists:
            data = doc.to_dict()
            if 'display_name' in data:
                return data['display_name']

        # Se não houver, retornar parte do email ou nome do user object
        if user.display_name:
            return user.display_name

        return user.email.split('@')[0]
    except Exception as e:
        print(f"Erro ao obter display_name: {e}")
        return "Usuário"
```

---

## 2. ÁREA DO CLIENTE (Portal do Cliente)

### 2.1 Existência de Área Separada

**Status:** ⚠️ **NÃO EXISTE COMO PORTAL SEPARADO**

**O que existe:**

- Workspace específico para cliente: `area_cliente_schmidmeier`
- Menu diferenciado para área do cliente (menos opções)
- Rotas normais do sistema, mas com dados filtrados por workspace

**O que NÃO existe:**

- ❌ Portal do cliente separado (rota `/cliente` ou similar)
- ❌ Interface diferenciada para clientes
- ❌ Autenticação específica para clientes
- ❌ Área pública de login para clientes

**Estrutura de Workspaces:**

```14:29:mini_erp/gerenciadores/gerenciador_workspace.py
WORKSPACES = {
    'area_cliente_schmidmeier': {
        'id': 'area_cliente_schmidmeier',
        'nome': 'Área do cliente: Schmidmeier 🇩🇪',
        'prefixo_colecoes': 'schmidmeier_',
        'rota_inicial': '/',
        'icon': 'folder_open'
    },
    'visao_geral_escritorio': {
        'id': 'visao_geral_escritorio',
        'nome': 'Visão geral do escritório',
        'prefixo_colecoes': 'visao_geral_',
        'rota_inicial': '/visao-geral/painel',
        'icon': 'business'
    }
}
```

### 2.2 Acesso do Cliente ao Sistema

**Status:** ✅ **FUNCIONANDO** (via workspace)

**Como funciona:**

1. Cliente faz login normalmente em `/login`
2. Sistema detecta perfil via custom claims
3. Cliente é redirecionado para workspace `area_cliente_schmidmeier`
4. Menu mostra apenas opções permitidas para cliente
5. Dados são filtrados por prefixo de coleção `schmidmeier_`

**Middleware de Verificação:**

```16:84:mini_erp/middlewares/verificar_workspace.py
def require_workspace_access(workspace_id: str = None, redirect_on_deny: bool = True):
    """
    Decorator para proteger rotas baseadas em workspace.
    Verifica se o usuário tem permissão para acessar o workspace da rota.

    Args:
        workspace_id: ID do workspace requerido (None para detectar automaticamente da rota)
        redirect_on_deny: Se True, redireciona para workspace permitido em caso de negação

    Exemplo:
        @ui.page('/visao-geral-escritorio/casos')
        @require_workspace_access('visao_geral_escritorio')
        def casos():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verifica autenticação primeiro
            if not is_authenticated():
                ui.navigate.to('/login')
                return

            # Se workspace_id não fornecido, tenta detectar da rota
            target_workspace = workspace_id
            if target_workspace is None:
                # Detecta workspace baseado na rota atual
                from nicegui import context
                route = context.get_client().request.path

                # Rotas /visao-geral/* pertencem ao workspace visao_geral_escritorio
                if '/visao-geral' in route:
                    target_workspace = 'visao_geral_escritorio'
                else:
                    target_workspace = 'area_cliente_schmidmeier'

            # Verifica permissão de acesso
            if not verificar_acesso_workspace(workspace_id=target_workspace):
                if redirect_on_deny:
                    # Redireciona para workspace padrão ou primeiro disponível
                    user = get_current_user()
                    if user:
                        from ..gerenciadores.gerenciador_workspace import obter_workspaces_usuario
                        workspaces_disponiveis = obter_workspaces_usuario()
                        if workspaces_disponiveis:
                            workspace_permitido = workspaces_disponiveis[0]
                            workspace_info = obter_info_workspace(workspace_permitido)
                            if workspace_info:
                                ui.notify('Você não tem permissão para acessar este workspace', type='negative')
                                ui.navigate.to(workspace_info['rota_inicial'])
                                return

                    # Fallback: redireciona para workspace padrão
                    workspace_info = obter_info_workspace(WORKSPACE_PADRAO)
                    if workspace_info:
                        ui.navigate.to(workspace_info['rota_inicial'])
                else:
                    # Apenas mostra erro sem redirecionar
                    ui.notify('Você não tem permissão para acessar este workspace', type='negative')
                return

            # Define workspace atual na sessão se tiver permissão
            from ..gerenciadores.gerenciador_workspace import definir_workspace
            definir_workspace(target_workspace)

            # Executa função original
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 2.3 Diferenciação de Permissões por Tipo de Usuário

**Status:** ✅ **FUNCIONANDO**

**Como funciona:**

- Perfil `cliente` → Acesso apenas a `area_cliente_schmidmeier`
- Perfil `interno` → Acesso a ambos workspaces
- Perfil `admin` → Acesso a ambos workspaces + permissões extras

**Lógica de Permissões:**

```85:164:mini_erp/gerenciadores/gerenciador_workspace.py
def obter_workspaces_usuario(usuario_id: Optional[str] = None) -> List[str]:
    """
    Retorna lista de workspaces que o usuário tem acesso baseado no perfil.

    Primeiro tenta buscar na coleção usuarios_sistema pelo firebase_uid.
    Se não encontrar, usa o sistema antigo de custom_claims.

    Args:
        usuario_id: UID do Firebase Auth (opcional, usa usuário atual se None)

    Returns:
        Lista de IDs de workspaces disponíveis
    """
    # Se não fornecido, usa usuário atual
    if usuario_id is None:
        user = get_current_user()
        if not user:
            return [WORKSPACE_PADRAO]
        usuario_id = user.get('uid')

    if not usuario_id:
        return [WORKSPACE_PADRAO]

    # Mapeamento de IDs de workspace da coleção para IDs do sistema
    MAPEAMENTO_WORKSPACES = {
        'schmidmeier': 'area_cliente_schmidmeier',
        'visao_geral': 'visao_geral_escritorio',
    }

    # Tenta buscar na coleção usuarios_sistema primeiro
    try:
        from ..firebase_config import get_db
        db = get_db()

        # Busca usuário pelo firebase_uid
        query = db.collection('usuarios_sistema').where('firebase_uid', '==', usuario_id).limit(1)
        docs = list(query.stream())

        if docs:
            usuario = docs[0].to_dict()
            workspaces_colecao = usuario.get('workspaces', [])

            # Converte IDs da coleção para IDs do sistema
            workspaces_sistema = []
            for ws_id in workspaces_colecao:
                ws_sistema = MAPEAMENTO_WORKSPACES.get(ws_id)
                if ws_sistema and ws_sistema in WORKSPACES:
                    workspaces_sistema.append(ws_sistema)

            if workspaces_sistema:
                return workspaces_sistema
    except Exception as e:
        print(f"Erro ao buscar usuário na coleção usuarios_sistema: {e}")

    # Fallback: usa sistema antigo de custom_claims
    from ..auth import get_user_profile
    profile = get_user_profile()

    # Perfil "cliente" → apenas workspace do cliente
    if profile == 'cliente':
        return ['area_cliente_schmidmeier']

    # Perfil "interno" ou "df_projetos" → ambos workspaces
    if profile in ['interno', 'df_projetos']:
        return ['area_cliente_schmidmeier', 'visao_geral_escritorio']

    # Se é admin (custom_claims), retorna todos
    user = get_current_user()
    if user:
        from firebase_admin import auth
        try:
            firebase_user = auth.get_user(usuario_id)
            custom_claims = firebase_user.custom_claims or {}
            if custom_claims.get('admin') or custom_claims.get('role') == 'admin':
                return ['area_cliente_schmidmeier', 'visao_geral_escritorio']
        except:
            pass

    # Default: apenas workspace do cliente (segurança)
    return [WORKSPACE_PADRAO]
```

---

## 3. FIREBASE AUTHENTICATION

### 3.1 Métodos de Autenticação Configurados

**Status:** ✅ **EMAIL/SENHA** (único método)

**Arquivo:** `mini_erp/auth.py`

**Método Atual:**

- Email/Password via Firebase Auth REST API
- Endpoint: `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword`
- API Key hardcoded no código (⚠️ **PROBLEMA DE SEGURANÇA**)

**Métodos NÃO Configurados:**

- ❌ Google Sign-In
- ❌ Facebook Sign-In
- ❌ Apple Sign-In
- ❌ Autenticação via telefone
- ❌ SSO/SAML

**Problema de Segurança:**

```11:12:mini_erp/auth.py
FIREBASE_API_KEY = "AIzaSyB5AmzmzdqBJ3WHSV8hiqKxdOf6wCM-Ol4"
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
```

⚠️ **API Key exposta no código** - Deveria estar em variável de ambiente.

---

### 3.2 Custom Claims

**Status:** ✅ **USADOS** (mas não gerenciáveis via interface)

**Para que são usados:**

1. **Perfil do usuário** (`perfil`, `role`, `profile`)
   - Valores: `cliente`, `interno`, `df_projetos`, `admin`
2. **Display name** (`display_name`)
   - Nome de exibição do usuário
3. **Permissões** (`admin`, `role`)
   - Controle de acesso a funcionalidades

**Como são definidos:**

- Via Firebase Admin SDK (código Python)
- Via Firebase Console (manual)
- Via scripts CLI (ex: `scripts/criar_usuarios_iniciais.py`)

**Problema:** Não há interface web para gerenciar custom claims. Administrador precisa:

- Usar scripts Python
- Acessar Firebase Console manualmente
- Modificar código

---

### 3.3 Tokens de Sessão

**Status:** ✅ **FUNCIONANDO**

**Como são gerenciados:**

1. **Login:** Token ID e refresh token retornados pelo Firebase Auth
2. **Armazenamento:** Salvo em `app.storage.user['user']` (sessão NiceGUI)
3. **Validação:** Decorator `@require_auth` verifica se usuário está na sessão
4. **Logout:** Remove dados da sessão e limpa cache do navegador

**Estrutura do Token na Sessão:**

```python
{
    'email': 'usuario@exemplo.com',
    'uid': 'firebase_uid',
    'token': 'id_token_jwt',
    'refresh_token': 'refresh_token_string'
}
```

**Problema Potencial:**

- Token não é validado a cada requisição (apenas verifica se existe na sessão)
- Não há renovação automática de token expirado
- Refresh token não é usado para renovar sessão

---

## 4. ESTADO ATUAL vs PLANEJADO

### 4.1 O que está Implementado e Funcionando

✅ **Autenticação Básica**

- Login com email/senha
- Logout
- Proteção de rotas
- Sessão persistida

✅ **Visualização de Usuários**

- Listagem de todos os usuários
- Informações básicas (email, função, status, datas)

✅ **Perfil do Usuário**

- Upload e edição de avatar
- Visualização de dados básicos

✅ **Sistema de Workspaces**

- Diferenciação de acesso por perfil
- Middleware de verificação de permissões

✅ **Estrutura de Dados**

- Coleção `usuarios_sistema` no Firestore
- Funções CRUD em `mini_erp/usuarios/database.py`
- Definição de perfis em `mini_erp/usuarios/perfis.py`

---

### 4.2 O que está Implementado mas Incompleto/Quebrado

⚠️ **Gerenciamento de Usuários**

- Funções CRUD existem no código, mas não há interface
- Apenas visualização funciona
- Não há formulários de criação/edição

⚠️ **Gerenciamento de Permissões**

- Perfis definidos, mas não gerenciáveis via interface
- Custom claims precisam ser definidos via scripts/console
- Não há interface para alterar perfil de usuário

⚠️ **Display Name**

- Função existe em `storage.py`, mas não é usada na interface
- Não há campo para editar nome de exibição

⚠️ **Área do Cliente**

- Existe como workspace, mas não como portal separado
- Cliente usa mesma interface, apenas com dados filtrados

---

### 4.3 O que Claramente Falta Implementar

❌ **CRUD Completo de Usuários na Interface**

- Formulário de criação de usuário
- Diálogo de edição de usuário
- Botão de exclusão (com confirmação)
- Funcionalidade de ativar/desativar usuário

❌ **Gerenciamento de Permissões na Interface**

- Seleção de perfil ao criar/editar usuário
- Alteração de custom claims via interface
- Atribuição de workspaces por usuário

❌ **Gerenciamento de Senhas**

- Alterar senha (usuário próprio)
- Resetar senha (admin)
- Primeiro acesso / senha temporária

❌ **Portal do Cliente Separado**

- Rota específica `/cliente` ou `/portal`
- Interface diferenciada para clientes
- Área pública de login para clientes

❌ **Autenticação Multi-Fator (MFA)**

- 2FA não implementado
- Autenticação via telefone não disponível

❌ **Auditoria de Usuários**

- Log de ações dos usuários
- Histórico de alterações
- Rastreamento de acessos

❌ **Validação e Segurança**

- API Key hardcoded (deveria ser variável de ambiente)
- Validação de força de senha
- Rate limiting de tentativas de login
- Bloqueio de conta após tentativas falhas

---

## 5. ARQUIVOS ANALISADOS

### Arquivos Principais

1. **`mini_erp/auth.py`** - Sistema de autenticação
2. **`mini_erp/pages/login.py`** - Página de login
3. **`mini_erp/pages/configuracoes.py`** - Gerenciamento de usuários (visualização)
4. **`mini_erp/storage.py`** - Upload de avatar e display name
5. **`mini_erp/firebase_config.py`** - Configuração do Firebase

### Arquivos de Suporte

6. **`mini_erp/usuarios/perfis.py`** - Definição de perfis
7. **`mini_erp/usuarios/database.py`** - Funções CRUD de usuários
8. **`mini_erp/gerenciadores/gerenciador_workspace.py`** - Gerenciamento de workspaces
9. **`mini_erp/middlewares/verificar_workspace.py`** - Middleware de permissões

### Scripts

10. **`scripts/criar_usuarios_iniciais.py`** - Script para criar usuários iniciais
11. **`scripts/listar_usuarios.py`** - Script para listar usuários

---

## 6. PRÓXIMOS PASSOS PRIORITÁRIOS

### Prioridade ALTA 🔴

1. **Criar Interface de Gerenciamento de Usuários**

   - Formulário de criação (email, senha, perfil)
   - Diálogo de edição (perfil, workspaces, status)
   - Botão de exclusão com confirmação
   - Funcionalidade de ativar/desativar

2. **Corrigir Segurança da API Key**

   - Mover API Key para variável de ambiente
   - Adicionar validação de força de senha
   - Implementar rate limiting

3. **Implementar Gerenciamento de Permissões**
   - Interface para alterar perfil de usuário
   - Seleção de workspaces por usuário
   - Atualização de custom claims via interface

### Prioridade MÉDIA 🟡

4. **Gerenciamento de Senhas**

   - Alterar senha (usuário próprio)
   - Resetar senha (admin)
   - Primeiro acesso / senha temporária

5. **Melhorar Perfil do Usuário**

   - Campo para editar display name
   - Editar dados pessoais (telefone, etc.)
   - Histórico de alterações

6. **Portal do Cliente**
   - Rota específica `/cliente` ou `/portal`
   - Interface diferenciada
   - Área pública de login

### Prioridade BAIXA 🟢

7. **Autenticação Multi-Fator**

   - 2FA opcional
   - Autenticação via telefone

8. **Auditoria**

   - Log de ações
   - Histórico de alterações
   - Rastreamento de acessos

9. **Autenticação Social**
   - Google Sign-In
   - Outros provedores (opcional)

---

## 7. CONCLUSÃO

O sistema de usuários está **parcialmente funcional**. A base está sólida (autenticação, sessão, workspaces), mas faltam funcionalidades críticas de gerenciamento na interface web.

**Pontos Fortes:**

- Autenticação funcionando
- Sistema de workspaces bem estruturado
- Perfis definidos e funcionais
- Avatar e perfil básico funcionando

**Pontos Fracos:**

- Falta interface de CRUD de usuários
- Custom claims não gerenciáveis via interface
- API Key exposta no código
- Portal do cliente não existe como área separada

**Recomendação:** Priorizar a criação da interface de gerenciamento de usuários (CRUD completo) e correção de segurança da API Key.

---

**Fim do Relatório**











