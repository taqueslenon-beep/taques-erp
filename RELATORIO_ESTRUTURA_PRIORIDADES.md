======================================================================
RELATÓRIO DE ESTRUTURA - SISTEMA DE PRIORIDADES
======================================================================

WORKSPACE: Visão Geral do Escritório
MÓDULO: Casos
LOCALIZAÇÃO: mini_erp/pages/visao_geral/casos/

======================================================================
ARQUIVOS IDENTIFICADOS
======================================================================

1. LISTAGEM DE CASOS:
   Arquivo: mini_erp/pages/visao_geral/casos/main.py
   Função: casos_visao_geral()
   Rota: /visao-geral/casos
   Linhas: 163-1357 (aproximadamente)
   Descrição: Página principal com cards responsivos, filtros e listagem

2. DETALHES DO CASO:
   Arquivo: mini_erp/pages/visao_geral/casos/main.py
   Função: caso_detalhes(caso_id)
   Rota: /visao-geral/casos/{caso_id}
   Linhas: 464-1357 (aproximadamente)
   Descrição: Página de detalhes com 8 abas:
   - Dados básicos
   - Processos
   - Relatório geral do caso
   - Vistorias
   - Estratégia geral
   - Próximas ações
   - Slack
   - Links úteis

3. CRIAÇÃO/EDIÇÃO DE CASO:
   Arquivo: mini_erp/pages/visao_geral/casos/caso_dialog.py
   Função: abrir_dialog_caso(caso, on_save)
   Descrição: Dialog modal para criar ou editar caso
   Campos atuais:
   - titulo (obrigatório)
   - nucleo (obrigatório)
   - status
   - categoria
   - estado
   - clientes (multi-select)
   - descricao

4. MODELS:
   Arquivo: mini_erp/pages/visao_geral/casos/models.py
   Descrição: Define constantes e estruturas de dados
   Constantes principais:
   - NUCLEO_OPTIONS
   - STATUS_OPTIONS
   - CATEGORIA_OPTIONS
   - ESTADOS
   - Caso (TypedDict)
   Funções auxiliares:
   - obter_cor_nucleo()
   - obter_cor_status()
   - obter_cor_categoria()
   - criar_caso_vazio()
   - validar_caso()

5. DATABASE:
   Arquivo: mini_erp/pages/visao_geral/casos/database.py
   Coleção Firestore: vg_casos
   Funções principais:
   - listar_casos()
   - buscar_caso(caso_id)
   - criar_caso(dados)
   - atualizar_caso(caso_id, dados)
   - excluir_caso(caso_id)
   - contar_casos()
   - listar_casos_por_nucleo(nucleo)
   - listar_casos_por_status(status)

======================================================================
MENU/NAVEGAÇÃO
======================================================================

SIDEBAR:
Arquivo: mini_erp/componentes/sidebar_base.py
Linhas: 362-370
Menu "Visão Geral do Escritório":
- Painel (/visao-geral/painel)
- Casos (/visao-geral/casos) ← MÓDULO ALVO
- Processos (/visao-geral/processos)
- Acordos (/visao-geral/acordos)
- Pessoas (/visao-geral/pessoas)
- Configurações (/visao-geral/configuracoes)

ROTA DE CASOS:
Rota principal: /visao-geral/casos
Rota de detalhes: /visao-geral/casos/{caso_id}

WORKSPACE ID:
ID: visao_geral_escritorio
Definido em: mini_erp/gerenciadores/gerenciador_workspace.py

======================================================================
ESTRUTURA DE DADOS ATUAL
======================================================================

COLEÇÃO FIRESTORE:
Nome: vg_casos
(Nota: workspace_collections.py define como 'visao_geral_escritorio_casos',
 mas database.py usa 'vg_casos' - verificar qual está em uso)

CAMPOS DO CASO (models.py - Caso TypedDict):
- _id: str
- titulo: str (obrigatório)
- nucleo: str (obrigatório)
- status: str
- categoria: str
- estado: str
- clientes: List[str]
- clientes_nomes: List[str]
- descricao: str
- created_at: Any
- updated_at: Any

CAMPOS A ADICIONAR:
- prioridade: str (P1, P2, P3, P4) - default: P4

======================================================================
BACK-END DE PRIORIDADES (JÁ CRIADO)
======================================================================

LOCALIZAÇÃO:
- mini_erp/models/prioridade.py
- mini_erp/database/prioridades_db.py
- mini_erp/database/casos_db.py

FUNÇÕES DISPONÍVEIS:
1. prioridades_db.py:
   - inicializar_prioridades()
   - listar_prioridades()
   - obter_prioridade(codigo)
   - obter_cor_prioridade(codigo)
   - obter_ordem_prioridade(codigo)

2. casos_db.py:
   - atualizar_prioridade_caso(caso_id, prioridade)
   - listar_casos_por_prioridade(prioridade)
   - contar_casos_por_prioridade()
   - obter_casos_sem_prioridade()
   - aplicar_prioridade_padrao_casos_sem_prioridade()

OBSERVAÇÃO:
O back-end criado usa a coleção 'cases' (workspace padrão).
Para o workspace "Visão Geral", será necessário adaptar para usar
a coleção 'vg_casos' ou criar funções específicas.

======================================================================
PRÓXIMOS PASSOS - IMPLEMENTAÇÃO FRONT-END
======================================================================

1. ADICIONAR CAMPO PRIORIDADE NO MODELO:
   Arquivo: mini_erp/pages/visao_geral/casos/models.py
   - Adicionar 'prioridade' no TypedDict Caso
   - Adicionar constante PRIORIDADE_OPTIONS = ['P1', 'P2', 'P3', 'P4']
   - Adicionar função obter_cor_prioridade(codigo)
   - Atualizar criar_caso_vazio() para incluir prioridade padrão (P4)

2. ADICIONAR PRIORIDADE NO DIALOG DE CRIAÇÃO/EDIÇÃO:
   Arquivo: mini_erp/pages/visao_geral/casos/caso_dialog.py
   - Adicionar select de prioridade no formulário
   - Exibir badge colorido com a cor da prioridade
   - Validar prioridade ao salvar

3. EXIBIR PRIORIDADE NA LISTAGEM:
   Arquivo: mini_erp/pages/visao_geral/casos/main.py
   - Adicionar badge de prioridade nos cards de casos
   - Adicionar filtro por prioridade
   - Ordenar por prioridade (opcional)

4. EXIBIR PRIORIDADE NA PÁGINA DE DETALHES:
   Arquivo: mini_erp/pages/visao_geral/casos/main.py
   - Adicionar badge de prioridade no header
   - Permitir edição de prioridade na aba "Dados básicos"

5. ADAPTAR FUNÇÕES DE DATABASE:
   Arquivo: mini_erp/pages/visao_geral/casos/database.py
   - Adicionar função atualizar_prioridade_caso()
   - Adicionar função listar_casos_por_prioridade()
   - Adicionar função contar_casos_por_prioridade()
   (Ou adaptar as funções de mini_erp/database/casos_db.py para usar vg_casos)

6. INICIALIZAR PRIORIDADES NO FIRESTORE:
   - Chamar inicializar_prioridades() na inicialização do sistema
   - Ou criar script de migração para criar prioridades

======================================================================
ARQUIVOS QUE SERÃO MODIFICADOS
======================================================================

1. mini_erp/pages/visao_geral/casos/models.py
   - Adicionar campo prioridade
   - Adicionar constantes de prioridades
   - Adicionar funções auxiliares

2. mini_erp/pages/visao_geral/casos/caso_dialog.py
   - Adicionar select de prioridade no formulário

3. mini_erp/pages/visao_geral/casos/main.py
   - Adicionar badge de prioridade nos cards
   - Adicionar filtro por prioridade
   - Adicionar badge na página de detalhes

4. mini_erp/pages/visao_geral/casos/database.py
   - Adicionar funções de prioridade (ou adaptar casos_db.py)

5. (Opcional) mini_erp/main.py ou mini_erp/core.py
   - Chamar inicializar_prioridades() na inicialização

======================================================================
CONFIRMAÇÃO
======================================================================

✅ Casos está dentro do workspace "Visão Geral do Escritório"
✅ Rota confirmada: /visao-geral/casos
✅ Menu confirmado: Sidebar em sidebar_base.py
✅ Estrutura de arquivos mapeada
✅ Back-end de prioridades já criado (precisa adaptação para vg_casos)

======================================================================
OBSERVAÇÕES IMPORTANTES
======================================================================

1. DISCREPÂNCIA DE COLETAS:
   - workspace_collections.py define: 'visao_geral_escritorio_casos'
   - database.py usa: 'vg_casos'
   - Verificar qual está em uso e padronizar

2. BACK-END CRIADO:
   - O back-end em mini_erp/database/casos_db.py usa coleção 'cases'
   - Será necessário adaptar para 'vg_casos' ou criar funções específicas
   - Ou usar as funções existentes adaptando o nome da coleção

3. PRIORIDADES NO FIRESTORE:
   - Collection: prioridades
   - Documentos: P1, P2, P3, P4
   - Campos: codigo, cor_hex, ordem, descricao_interna
   - Esta coleção é GLOBAL (não específica de workspace)

======================================================================



