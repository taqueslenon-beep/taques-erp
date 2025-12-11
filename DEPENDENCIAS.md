# Tecnologias e Módulos do Projeto TAQUES ERP

## 📦 Bibliotecas de Terceiros

### Principais (requirements.txt)
- **nicegui** - Framework web Python para interface
- **firebase-admin** - SDK do Firebase (Firestore, Auth, Storage)
- **reportlab** - Geração de PDFs
- **watchfiles** - Monitoramento de arquivos para desenvolvimento

### Usadas mas não listadas no requirements.txt
- **Pillow (PIL)** - Processamento de imagens (avatars)
- **requests** - Requisições HTTP (autenticação Firebase)

## 🐍 Módulos Python Padrão

### Sistema e I/O
- `os`, `sys`, `errno` - Sistema operacional
- `io`, `base64` - Manipulação de dados
- `pathlib` - Caminhos de arquivos
- `subprocess` - Execução de processos
- `webbrowser` - Abertura de navegador

### Concorrência e Tempo
- `threading` - Threads
- `asyncio` - Programação assíncrona
- `datetime`, `time` - Datas e horas

### Utilitários
- `json` - JSON
- `collections` (Counter, defaultdict) - Estruturas de dados
- `typing` - Type hints
- `contextlib` - Context managers
- `functools` - Funções utilitárias (wraps)
- `re`, `unicodedata` - Expressões regulares e normalização
- `traceback` - Rastreamento de erros
- `socket`, `signal` - Rede e sinais

## 🏗️ Módulos Internos Principais

### Core (mini_erp/)
- **core.py** - Funções centrais (cache, CRUD, formatação, layout)
- **auth.py** - Autenticação Firebase
- **firebase_config.py** - Configuração Firebase/Firestore
- **storage.py** - Upload/download de arquivos (avatars)
- **main.py** - Ponto de entrada do servidor

### Casos (mini_erp/pages/casos/)
- **models.py** - Modelos de dados
- **database.py** - Operações de banco
- **business_logic.py** - Lógica de negócio
- **ui_components.py** - Componentes de interface
- **utils.py** - Utilitários
- **duplicate_detection.py** - Detecção de duplicatas
- **admin_page.py** - Página administrativa
- **casos_page.py** - Página principal

### Processos (mini_erp/pages/processos/)
- **models.py** - Modelos de dados
- **database.py** - Operações de banco
- **business_logic.py** - Lógica de negócio
- **ui_components.py** - Componentes de interface
- **utils.py** - Utilitários
- **processos_page.py** - Página principal

### Pessoas (mini_erp/pages/pessoas/)
- **models.py** - Modelos de dados
- **database.py** - Operações de banco
- **business_logic.py** - Lógica de negócio
- **ui_components.py** - Componentes de interface
- **ui_dialogs.py** - Diálogos modais
- **ui_tables.py** - Tabelas
- **validators.py** - Validações (CPF/CNPJ)
- **pessoas_page.py** - Página principal

### Painel (mini_erp/pages/painel/)
- **models.py** - Modelos de dados
- **data_service.py** - Serviço de dados
- **chart_builders.py** - Construção de gráficos
- **helpers.py** - Funções auxiliares
- **ui_components.py** - Componentes de interface
- **tab_visualizations.py** - Visualizações por aba
- **painel_page.py** - Página principal

### Governança (mini_erp/pages/governanca/)
- **main.py** - Página principal
- **visao_geral.py** - Visão geral
- **administrativa.py** - Módulo administrativo
- **civil.py** - Módulo civil
- **tributaria.py** - Módulo tributário
- **criminal/** - Módulo criminal (beneficios, cenario, condenacoes, cumprimento)

### Outras Páginas
- **login.py** - Tela de login
- **configuracoes.py** - Configurações do usuário
- **processos_por_caso.py** - Processos vinculados a casos
- **prazos.py** - Prazos (em desenvolvimento)
- **compromissos.py** - Compromissos (em desenvolvimento)
- **acordos.py** - Acordos (em desenvolvimento)
- **riscos_mapbiomas.py** - Riscos MapBiomas

## 🔧 Scripts Utilitários (scripts/)
- **backfill_clients.py** - Preenchimento de clientes
- **backfill_processes.py** - Preenchimento de processos
- **check_duplicates.py** - Verificação de duplicatas
- **cleanup_duplicate_cases.py** - Limpeza de casos duplicados
- **diagnose_duplicates.py** - Diagnóstico de duplicatas
- **diagnose_duplicates_standalone.py** - Diagnóstico standalone
- **fetch_active_users.py** - Busca de usuários ativos
- **force_cleanup.py** - Limpeza forçada
- **run_deduplication.py** - Execução de deduplicação

## 🗄️ Banco de Dados
- **Firebase Firestore** - Banco NoSQL principal
  - Coleções: `cases`, `processes`, `clients`, `opposing_parties`, `users`, `benefits`, `agreements`, `convictions`
- **Firebase Storage** - Armazenamento de arquivos (avatars)
- **Firebase Auth** - Autenticação de usuários

## 📊 Arquitetura
- **Frontend**: NiceGUI (Python-based, renderiza HTML/CSS/JS)
- **Backend**: Python puro (sem framework adicional)
- **Banco**: Firebase Firestore (NoSQL)
- **Autenticação**: Firebase Auth (REST API)
- **Storage**: Firebase Storage
- **Cache**: Thread-safe em memória (5 minutos TTL)










