# Criação de Usuários no Sistema TAQUES-ERP

## Data: 2024-12-19

## Objetivo

Criar 3 novos usuários no sistema com permissão de "usuário" (não administrador), garantindo que apareçam corretamente na interface e no Firebase Firestore.

## Usuários Criados

1. **Flaviana Friedrich**

   - Email: flaviana.friedrich@gmail.com
   - Nome de exibição: Flaviana Friedrich
   - Permissão: usuario
   - Status: ativo

2. **Douglas Prado Marcos**

   - Email: douglasmarco@gmail.com
   - Nome de exibição: Douglas Prado Marcos
   - Permissão: usuario
   - Status: ativo

3. **Berna Taques**
   - Email: bernataques@gmail.com
   - Nome de exibição: Berna Taques
   - Permissão: usuario
   - Status: ativo

## Estrutura no Firestore

Coleção: `users`

Estrutura do documento:

```json
{
  "email": "email@exemplo.com",
  "nome_exibicao": "Nome Completo",
  "permissao": "usuario",
  "status": "ativo",
  "data_criacao": "timestamp",
  "data_atualizacao": "timestamp",
  "criado_por": "sistema"
}
```

## Script Criado

**Arquivo**: `scripts/criar_usuarios.py`

**Funcionalidades**:

- Validação de email duplicado antes de criar
- Validação de campos obrigatórios
- Registro automático de timestamps
- Listagem de todos os usuários após criação

**Execução**:

```bash
python3 scripts/criar_usuarios.py
```

## Validações Implementadas

1. ✅ Verificação de email duplicado antes de criar
2. ✅ Validação de campos obrigatórios (email, nome_exibicao)
3. ✅ Validação de valores permitidos (permissao: usuario/administrador, status: ativo/inativo)
4. ✅ Registro automático de data_criacao e data_atualizacao
5. ✅ Campo criado_por preenchido automaticamente

## Onde os Usuários Aparecem

Os usuários criados na coleção `users` do Firestore aparecem em:

1. **Página de Entregáveis** - Para seleção de responsável
2. **Página de Casos** - Para seleção de usuários relacionados
3. **Qualquer interface que use `get_users_list()`** - Função do `core.py` que retorna todos os usuários

**Nota**: A interface de Configurações (`/configuracoes`) lista usuários do Firebase Authentication (não do Firestore), então os novos usuários não aparecerão automaticamente lá. Para aparecerem na interface de Configurações, é necessário criar contas no Firebase Authentication também.

## Resultado

✅ **3 usuários criados com sucesso**

- Flaviana Friedrich
- Douglas Prado Marcos
- Berna Taques

Todos os usuários foram criados na coleção `users` do Firestore e estão disponíveis para uso no sistema.

## Criação de Contas no Firebase Authentication

**Data**: 2024-12-19

### Objetivo

Criar contas de autenticação no Firebase Authentication para os 3 usuários, permitindo que façam login no sistema e apareçam na página de Configurações.

### Script Criado

**Arquivo**: `scripts/criar_usuarios_auth.py`

**Funcionalidades**:

- Cria contas no Firebase Authentication
- Verifica se email já existe antes de criar
- Define senha inicial padrão
- Vincula display_name nos custom claims
- Atualiza Firestore com UID do Auth
- Marca `auth_vinculado: true` no documento

**Execução**:

```bash
python3 scripts/criar_usuarios_auth.py
```

### Usuários Criados no Firebase Auth

1. **Flaviana Friedrich**

   - Email: flaviana.friedrich@gmail.com
   - UID: NtKX2TEy63ZNXe6hIDuklVK7u4W2
   - Senha inicial: Taques@2024

2. **Douglas Prado Marcos**

   - Email: douglasmarco@gmail.com
   - UID: GR9HT6EsIHZNH1EJgEviPo84aCt1
   - Senha inicial: Taques@2024

3. **Berna Taques**
   - Email: bernataques@gmail.com
   - UID: MlGBIwu80CeCy1OU7cF3F5yw3Ej2
   - Senha inicial: Taques@2024

### Estrutura Atualizada no Firestore

Após criação no Firebase Auth, os documentos foram atualizados com:

```json
{
  "email": "email@exemplo.com",
  "nome_exibicao": "Nome Completo",
  "permissao": "usuario",
  "status": "ativo",
  "uid": "uid_do_firebase_auth",
  "auth_vinculado": true,
  "data_criacao": "timestamp",
  "data_atualizacao": "timestamp",
  "criado_por": "sistema"
}
```

### Validações Implementadas

1. ✅ Verificação de email duplicado no Firebase Auth antes de criar
2. ✅ Verificação de existência do usuário no Firestore
3. ✅ Validação de senha (mínimo 6 caracteres)
4. ✅ Definição de display_name nos custom claims
5. ✅ Atualização automática do Firestore com UID
6. ✅ Marcação de `auth_vinculado: true`

### Onde os Usuários Aparecem Agora

Após criação no Firebase Auth, os usuários aparecem em:

1. **Página de Configurações** (`/configuracoes`) - Lista de usuários do Firebase Auth
2. **Página de Entregáveis** - Para seleção de responsável
3. **Página de Casos** - Para seleção de usuários relacionados
4. **Tela de Login** - Podem fazer login com email e senha

### Resultado Final

✅ **3 contas criadas com sucesso no Firebase Authentication**

- Flaviana Friedrich
- Douglas Prado Marcos
- Berna Taques

✅ **Documentos do Firestore atualizados com UIDs**

- Todos os documentos marcados com `auth_vinculado: true`
- UIDs vinculados corretamente

### Importante

⚠️ **Senha Inicial**: Todos os usuários receberam a senha inicial `Taques@2024`

- Os usuários devem trocar a senha no primeiro login
- Envie as credenciais de forma segura para cada usuário

### Próximos Passos

1. Informar aos usuários suas credenciais de acesso
2. Recomendar troca de senha no primeiro login
3. Verificar se aparecem corretamente na página de Configurações
