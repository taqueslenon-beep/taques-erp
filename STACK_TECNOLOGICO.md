# Stack Tecnológico - TAQUES ERP

Sistema de gestão para escritório de advocacia desenvolvido em Python com arquitetura web moderna.

---

## Tabela Resumo

| Camada         | Tecnologia         | Versão   | Propósito Principal                 |
| -------------- | ------------------ | -------- | ----------------------------------- |
| Frontend       | NiceGUI            | Latest   | Framework web Python para interface |
| Frontend       | ECharts            | Latest   | Biblioteca de gráficos interativos  |
| Backend        | Python             | 3.9+     | Linguagem principal                 |
| Backend        | Asyncio            | Stdlib   | Programação assíncrona              |
| Banco de Dados | Firebase Firestore | Latest   | Banco NoSQL principal               |
| Banco de Dados | Firebase Storage   | Latest   | Armazenamento de arquivos           |
| Autenticação   | Firebase Auth      | REST API | Autenticação de usuários            |
| Integração     | Firebase Admin SDK | Latest   | Acesso administrativo ao Firebase   |
| Integração     | ReportLab          | Latest   | Geração de PDFs                     |
| Integração     | Pillow             | Latest   | Processamento de imagens            |
| DevOps         | Watchfiles         | Latest   | Auto-reload em desenvolvimento      |

---

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────┐
│                      NAVEGADOR WEB                          │
│                   (HTML/CSS/JavaScript)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│                      NICEGUI SERVER                         │
│            (Python + Uvicorn + FastAPI interno)             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Páginas    │  │   Módulos    │  │    Core      │       │
│  │  (UI/Views)  │  │  (Business)  │  │  (Utilitários)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                          │                                   │
│              ┌───────────▼───────────┐                       │
│              │   Cache em Memória    │                       │
│              │   (Thread-safe, 5min) │                       │
│              └───────────┬───────────┘                       │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│                    FIREBASE CLOUD                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Firestore   │  │   Storage    │  │     Auth     │       │
│  │   (NoSQL)    │  │  (Arquivos)  │  │  (Usuários)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Tecnologias de Frontend

### NiceGUI

| Atributo      | Valor                                                               |
| ------------- | ------------------------------------------------------------------- |
| **Versão**    | Latest (via pip)                                                    |
| **Propósito** | Framework web Python que gera interface HTML/CSS/JS automaticamente |
| **Site**      | https://nicegui.io                                                  |

**Características Principais:**

- Interface declarativa em Python puro
- Componentes UI pré-construídos (botões, tabelas, inputs, cards)
- Comunicação bidirecional via WebSocket
- Suporte a layouts responsivos
- Sistema de storage para sessões

**Pontos de Integração:**

- `mini_erp/main.py` - Inicialização do servidor
- `mini_erp/pages/*.py` - Todas as páginas da interface
- `mini_erp/core.py` - Layout base e componentes reutilizáveis

**Dependências:**

- Uvicorn (servidor ASGI)
- FastAPI (framework web interno)
- Starlette (toolkit ASGI)

---

### ECharts

| Atributo      | Valor                                           |
| ------------- | ----------------------------------------------- |
| **Versão**    | Latest (integrado via NiceGUI)                  |
| **Propósito** | Biblioteca JavaScript para gráficos interativos |
| **Site**      | https://echarts.apache.org                      |

**Características Principais:**

- Gráficos de barras, linhas, pizza, etc.
- Interatividade com tooltips e zoom
- Configuração via dicionários Python

**Pontos de Integração:**

- `mini_erp/pages/painel/chart_builders.py` - Configurações de gráficos
- `mini_erp/pages/painel/tab_visualizations.py` - Visualizações por aba
- `mini_erp/pages/governanca/*.py` - Gráficos de governança

---

## 2. Tecnologias de Backend

### Python

| Atributo      | Valor                          |
| ------------- | ------------------------------ |
| **Versão**    | 3.9+                           |
| **Propósito** | Linguagem principal do sistema |
| **Site**      | https://python.org             |

**Módulos Padrão Utilizados:**

| Módulo             | Propósito                                  |
| ------------------ | ------------------------------------------ |
| `asyncio`          | Programação assíncrona                     |
| `threading`        | Concorrência com threads                   |
| `datetime`         | Manipulação de datas                       |
| `json`             | Serialização de dados                      |
| `os`, `sys`        | Operações de sistema                       |
| `re`               | Expressões regulares                       |
| `collections`      | Estruturas de dados (Counter, defaultdict) |
| `typing`           | Type hints                                 |
| `functools`        | Decorators e funções utilitárias           |
| `pathlib`          | Manipulação de caminhos                    |
| `io`, `base64`     | Manipulação de bytes                       |
| `socket`, `signal` | Rede e sinais do sistema                   |

---

## 3. Tecnologias de Banco de Dados

### Firebase Firestore

| Atributo      | Valor                                          |
| ------------- | ---------------------------------------------- |
| **Versão**    | Latest (via firebase-admin SDK)                |
| **Propósito** | Banco de dados NoSQL principal                 |
| **Site**      | https://firebase.google.com/products/firestore |

**Características Principais:**

- Banco de dados de documentos (NoSQL)
- Sincronização em tempo real
- Escalabilidade automática
- Consultas compostas

**Coleções Utilizadas:**

- `cases` - Casos jurídicos
- `processes` - Processos
- `clients` - Clientes
- `opposing_parties` - Partes contrárias
- `users` - Usuários do sistema
- `benefits` - Benefícios
- `agreements` - Acordos
- `convictions` - Condenações

**Pontos de Integração:**

- `mini_erp/firebase_config.py` - Configuração e conexão
- `mini_erp/pages/*/database.py` - Operações CRUD por módulo

---

### Firebase Storage

| Atributo      | Valor                                           |
| ------------- | ----------------------------------------------- |
| **Versão**    | Latest (via firebase-admin SDK)                 |
| **Propósito** | Armazenamento de arquivos (avatars, documentos) |
| **Bucket**    | `taques-erp.appspot.com`                        |

**Pontos de Integração:**

- `mini_erp/storage.py` - Upload/download de avatars

---

### Cache em Memória

| Atributo          | Valor                           |
| ----------------- | ------------------------------- |
| **Implementação** | Customizada (dicionário Python) |
| **TTL**           | 5 minutos (300 segundos)        |
| **Thread-safe**   | Sim (via threading.Lock)        |

**Características:**

- Reduz consultas ao Firestore
- Invalidação automática por tempo
- Lock para evitar race conditions

**Pontos de Integração:**

- `mini_erp/core.py` - Variáveis `_cache`, `_cache_timestamp`, `_cache_lock`

---

## 4. Autenticação e Segurança

### Firebase Authentication

| Atributo      | Valor                                    |
| ------------- | ---------------------------------------- |
| **Versão**    | REST API v1                              |
| **Propósito** | Autenticação de usuários com email/senha |
| **Endpoint**  | `identitytoolkit.googleapis.com`         |

**Características:**

- Login com email/senha
- Tokens JWT
- Refresh tokens
- Tratamento de erros traduzido

**Pontos de Integração:**

- `mini_erp/auth.py` - Funções de login/logout
- `mini_erp/pages/login.py` - Tela de login

---

### Sistema de Sessões

| Atributo          | Valor                        |
| ----------------- | ---------------------------- |
| **Implementação** | NiceGUI Storage              |
| **Secret**        | `taques-erp-secret-key-2024` |

**Características:**

- Armazenamento de usuário logado
- Persistência entre requisições
- Limpeza automática no logout

**Pontos de Integração:**

- `mini_erp/auth.py` - `get_current_user()`, `is_authenticated()`
- Decorator `@require_auth` para proteção de rotas

---

## 5. Integrações Externas

### Firebase Admin SDK

| Atributo      | Valor                             |
| ------------- | --------------------------------- |
| **Pacote**    | `firebase-admin`                  |
| **Versão**    | Latest                            |
| **Propósito** | Acesso administrativo ao Firebase |

**Serviços Utilizados:**

- `firestore` - Banco de dados
- `storage` - Armazenamento de arquivos
- `auth` - Gerenciamento de usuários

**Configuração:**

- Credenciais via arquivo JSON local ou variáveis de ambiente
- Projeto: `taques-erp`

---

### ReportLab

| Atributo      | Valor                     |
| ------------- | ------------------------- |
| **Pacote**    | `reportlab`               |
| **Versão**    | Latest                    |
| **Propósito** | Geração de documentos PDF |
| **Site**      | https://www.reportlab.com |

**Características:**

- Criação de PDFs programaticamente
- Suporte a tabelas, imagens, estilos

---

### Pillow (PIL)

| Atributo      | Valor                              |
| ------------- | ---------------------------------- |
| **Pacote**    | `Pillow`                           |
| **Versão**    | Latest                             |
| **Propósito** | Processamento de imagens (avatars) |
| **Site**      | https://pillow.readthedocs.io      |

**Funcionalidades Utilizadas:**

- Redimensionamento de imagens (thumbnail 200x200)
- Conversão de formatos (RGB/RGBA para PNG)
- Otimização de tamanho

**Pontos de Integração:**

- `mini_erp/storage.py` - `fazer_upload_avatar()`

---

### Requests

| Atributo      | Valor                           |
| ------------- | ------------------------------- |
| **Pacote**    | `requests`                      |
| **Versão**    | Latest                          |
| **Propósito** | Cliente HTTP para APIs REST     |
| **Site**      | https://requests.readthedocs.io |

**Pontos de Integração:**

- `mini_erp/auth.py` - Chamadas à API do Firebase Auth

---

## 6. DevOps e Infraestrutura

### Watchfiles

| Atributo      | Valor                                      |
| ------------- | ------------------------------------------ |
| **Pacote**    | `watchfiles`                               |
| **Versão**    | Latest                                     |
| **Propósito** | Monitoramento de arquivos para auto-reload |
| **Site**      | https://watchfiles.helpmanual.io           |

**Características:**

- Detecta mudanças em arquivos .py
- Reinicia servidor automaticamente
- Debounce de 2 segundos

**Pontos de Integração:**

- `dev_server.py` - Servidor de desenvolvimento

---

### Servidor de Desenvolvimento

| Atributo         | Valor           |
| ---------------- | --------------- |
| **Arquivo**      | `dev_server.py` |
| **Porta Padrão** | 8080            |
| **Auto-reload**  | Sim             |

**Funcionalidades:**

- Monitoramento de mudanças em código
- Abertura automática do navegador
- Filtro inteligente (ignora **pycache**, .git, etc)
- Debounce para evitar reinicializações em cascata

---

### Scripts de Manutenção

| Script                               | Propósito                          |
| ------------------------------------ | ---------------------------------- |
| `scripts/backfill_clients.py`        | Preenchimento de dados de clientes |
| `scripts/backfill_processes.py`      | Preenchimento de processos         |
| `scripts/check_duplicates.py`        | Verificação de duplicatas          |
| `scripts/cleanup_duplicate_cases.py` | Limpeza de casos duplicados        |
| `scripts/diagnose_duplicates.py`     | Diagnóstico de duplicatas          |
| `scripts/fetch_active_users.py`      | Busca de usuários ativos           |
| `scripts/force_cleanup.py`           | Limpeza forçada                    |
| `scripts/run_deduplication.py`       | Execução de deduplicação           |

---

## 7. Estrutura de Módulos Internos

### Core (`mini_erp/`)

| Arquivo              | Propósito                                          |
| -------------------- | -------------------------------------------------- |
| `main.py`            | Ponto de entrada do servidor                       |
| `core.py`            | Funções centrais (cache, CRUD, formatação, layout) |
| `auth.py`            | Autenticação Firebase                              |
| `firebase_config.py` | Configuração Firebase/Firestore                    |
| `storage.py`         | Upload/download de arquivos                        |

### Módulos de Páginas (`mini_erp/pages/`)

Cada módulo segue a estrutura:

- `models.py` - Modelos de dados
- `database.py` - Operações de banco
- `business_logic.py` - Lógica de negócio
- `ui_components.py` - Componentes de interface
- `*_page.py` - Página principal

**Módulos Disponíveis:**

- `casos/` - Gestão de casos jurídicos
- `processos/` - Gestão de processos
- `pessoas/` - Gestão de clientes e partes
- `painel/` - Dashboard e visualizações
- `governanca/` - Governança (administrativa, civil, criminal, tributária)

---

## 8. Arquivos de Configuração

| Arquivo                     | Propósito                       |
| --------------------------- | ------------------------------- |
| `requirements.txt`          | Dependências Python             |
| `firebase-credentials.json` | Credenciais do Firebase (local) |
| `DEPENDENCIAS.md`           | Documentação de dependências    |
| `PADROES_ESTILO_NICEGUI.md` | Padrões de estilo UI            |

---

## 9. Variáveis de Ambiente

| Variável                  | Propósito                      | Padrão |
| ------------------------- | ------------------------------ | ------ |
| `APP_PORT`                | Porta do servidor              | 8080   |
| `DEV_SERVER`              | Indica execução via dev_server | false  |
| `FIREBASE_PRIVATE_KEY_ID` | ID da chave privada Firebase   | -      |
| `FIREBASE_PRIVATE_KEY`    | Chave privada Firebase         | -      |
| `FIREBASE_CLIENT_EMAIL`   | Email do cliente Firebase      | -      |
| `FIREBASE_CLIENT_ID`      | ID do cliente Firebase         | -      |
| `FIREBASE_CERT_URL`       | URL do certificado Firebase    | -      |

---

## 10. Comandos Úteis

```bash
# Iniciar servidor de desenvolvimento (com auto-reload)
python3 dev_server.py

# Iniciar servidor diretamente
python3 -m mini_erp.main

# Instalar dependências
pip install -r requirements.txt

# Executar script de manutenção
python3 scripts/check_duplicates.py
```

---

## Referências

- [NiceGUI Documentação](https://nicegui.io/documentation)
- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [Firebase Firestore](https://firebase.google.com/docs/firestore)
- [ECharts](https://echarts.apache.org/en/option.html)
- [ReportLab](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Pillow](https://pillow.readthedocs.io/en/stable/)

---

_Última atualização: Novembro 2024_





