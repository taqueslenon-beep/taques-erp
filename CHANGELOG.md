## [v1.9.0] - 2025-12-23

### Adicionado

- **Novos Gráficos: Clientes com Mais Processos e Partes Contrárias Mais Frequentes**: Adicionados dois novos gráficos de barras horizontais na seção "Estatísticas de Processos" do Painel da Visão Geral
  - **Gráfico "Clientes com Mais Processos"**: Exibe ranking dos top 10 clientes com mais processos ativos
    - Gradiente de cores azuis
    - Filtro por status (Em andamento, Concluído, Arquivado, Suspenso, Todos os status)
    - Conta cada cliente individualmente quando um processo possui múltiplos clientes
    - Altura dinâmica baseada na quantidade de clientes
  - **Gráfico "Partes Contrárias Mais Frequentes"**: Exibe ranking das top 10 partes contrárias mais frequentes
    - Gradiente de cores vermelhas
    - Filtro por status (Em andamento, Concluído, Arquivado, Suspenso, Todos os status)
    - Normalização de nomes para evitar duplicatas
    - Altura dinâmica baseada na quantidade de partes contrárias
  - Ambos os gráficos seguem o mesmo padrão visual e funcional dos outros gráficos da seção
  - Posicionados na terceira linha de gráficos, após "Processos por Sistema Processual"
  - Valor padrão do filtro: "Em andamento" em ambos

### Corrigido

- **Erro MutationObserver ao Cadastrar Parte Contrária (CRÍTICO)**: Corrigido erro "TypeError: Failed to execute 'observe' on 'MutationObserver': parameter 1 is not of type 'Node'" que ocorria ao digitar no campo de parte contrária no modal de novo processo
  - **Causa**: `ui.select()` com `with_input=True` cria autocomplete interno que usa MutationObserver. Quando componente é destruído (navegação entre abas, fechamento do modal), observer tenta acessar elementos DOM inexistentes
  - **Solução**: Validação robusta em múltiplas camadas no handler `_sync_opposing()`:
    - Verifica existência da referência do componente
    - Valida propriedade `value` antes de acessar
    - Try-except interno para capturar erros de acesso
    - Todos os erros de MutationObserver são silenciosamente ignorados
  - Adicionado try-except também nos handlers `_sync_others()` e `_sync_parent_processes()` para consistência
  - Fallback para evento alternativo se `on_value_change` falhar
  - Tratamento gracioso de erros durante digitação rápida ou navegação entre abas
  - Logging apenas para erros não relacionados a MutationObserver

### Adicionado

- **Mudança de Status via Checkbox na Tabela de Migração**: Implementada funcionalidade onde ao marcar o checkbox de um processo, seu status muda automaticamente de "Pendente" para "Migrado" e o processo é movido para o final da tabela
  - Checkbox reflete status: marcado = migrado, desmarcado = pendente
  - Atualização imediata no Firestore ao clicar no checkbox
  - Reordenação automática: processos pendentes no topo, migrados no final
  - Checkbox mestre marca apenas processos pendentes
  - Contador de progresso atualizado automaticamente
- **Botões de Cópia para Número e Data**: Adicionados ícones de cópia ao lado do número do processo e da data de distribuição na tabela de migração
  - Ícone discreto que aparece ao lado do texto
  - Cópia rápida para área de transferência com um clique
  - Feedback visual com notificação "Número copiado!" ou "Data copiada!"
  - Suporte a navegadores modernos (Clipboard API) e fallback para navegadores antigos
  - Ícones ficam mais visíveis no hover da linha
  - **Correção**: Número copiado agora remove sufixo entre parênteses automaticamente (ex: "(CNICR01)" é removido)
- **Filtros de Status nos Gráficos de Processos**: Adicionados dropdowns de filtro de status em 4 gráficos do painel de processos
  - Gráficos com filtro: "Processos por Núcleo", "Processos por Área", "Processos por Responsável", "Processos por Sistema Processual"
  - Opções de filtro: "Em andamento", "Concluído", "Arquivado", "Suspenso", "Todos os status"
  - Valor padrão: "Em andamento" (`em_andamento`) em todos os gráficos
  - Gráficos reativos que atualizam automaticamente ao mudar o filtro
  - Filtro aplicado em memória (sem nova query ao banco)
  - Compatibilidade com status antigos: mapeia 'Ativo' para "Em andamento", 'Encerrado'/'Baixado' para "Concluído", 'Suspenso'/'Em monitoramento' para "Suspenso"
  - Dropdowns posicionados no canto superior direito de cada card
  - Design consistente: largura `w-48`, label "Filtrar por Status"
- **Substituição: Gráfico de Processos por Ano**: Substituído gráfico "Evolução dos Processos por Data" por novo gráfico "Processos por Ano"
  - Gráfico de barras verticais agrupando processos por ano de abertura
  - Extrai ano de `data_abertura` ou `created_at` (fallback)
  - Suporta múltiplos formatos de data: ISO, DD/MM/AAAA, MM/AAAA, AAAA
  - Anos ordenados em ordem crescente
  - Valores exibidos no topo de cada barra
  - Inclui filtro de status (mesmo padrão dos outros gráficos)
  - Valor padrão do filtro: "Em andamento"
  - Cor azul consistente (#3b82f6)
  - Altura fixa de 320px (h-80)
- **Porcentagens nos Gráficos de Barras Horizontais**: Adicionadas porcentagens aos valores absolutos em todos os gráficos de barras horizontais da seção "Estatísticas de Processos"
  - Formato: "47 (90%)" ao invés de apenas "47"
  - Gráficos atualizados: "Processos por Núcleo", "Processos por Área", "Processos por Responsável", "Processos por Sistema Processual"
  - Regras de formatação:
    - Se >= 1%: arredondar para inteiro (ex: "47 (90%)")
    - Se < 1% e > 0%: 1 casa decimal (ex: "1 (0.5%)")
    - Se = 0: mostrar "0 (0%)"
  - Porcentagens calculadas automaticamente baseadas no total de processos filtrados
  - Labels posicionados no final das barras (direita)
  - Fonte negrita para melhor legibilidade
- **Script de Sincronização de Processos Migrados**: Criado script standalone para identificar processos já migrados manualmente e atualizar seus status na planilha de migração
  - Script: `scripts/sync_processos_migrados.py`
  - Identifica processos já existentes em `vg_processos` que estão pendentes em `processos_migracao`
  - Atualiza status de "pendente" para "migrado" em lote usando batch write
  - Cria backup automático da coleção antes de atualizar
  - Gera relatório detalhado com logs da sincronização
  - Confirmação do usuário antes de executar atualizações
  - Suporta até 500 atualizações por batch (limite do Firestore)
- **Exclusão de Processos da Lista de Migração**: Adicionada funcionalidade para excluir permanentemente processos da lista de migração EPROC
  - Botão de lixeira ao lado do botão "COMPLETAR" em cada linha
  - Modal de confirmação com aviso sobre ação permanente
  - Aviso especial para processos já migrados (não afeta processo no sistema)
  - Exclusão definitiva do Firestore (coleção `processos_migracao`)
  - Atualização automática da interface após exclusão (contador e barra de progresso)
    [text](http://localhost:8081/visao-geral/processos) - Notificações de sucesso/erro

### Modificado

- **Card "Processos" no Painel**: Modificado para exibir APENAS processos com status "Em andamento" (ativos), ao invés de todos os processos
  - Card agora mostra apenas processos ativos usando filtro `em_andamento`
  - Label descritivo atualizado: "Processos em andamento" (quando há processos) ou "Nenhum processo ativo" (quando zero)
  - Usa função `filtrar_processos_por_status()` para garantir consistência com outros gráficos
  - Mantém mesmo estilo visual e classes CSS
- **Formato de Data na Tabela de Migração EPROC**: Ajustado formato de exibição da coluna "Data de Distribuição" para exibir apenas data no formato brasileiro (DD/MM/YYYY), removendo hora, minutos e segundos
  - Exemplo: "02/08/2018" ao invés de "2018-08-02 09:20:17"
  - Função `converter_datetime_firestore()` agora trata strings de data/hora e converte para formato brasileiro
  - Ordenação da coluna mantida funcionando corretamente

### Técnico

- `mini_erp/pages/admin/admin_migracao_processos.py`:
  - Melhorada função `converter_datetime_firestore()` para converter strings de data em vários formatos para DD/MM/YYYY
  - Implementada lógica de atualização de status via checkbox com persistência no Firestore
  - Reordenação automática de processos (pendentes primeiro, depois migrados)
  - Adicionados slots customizados para células de número e data com ícones de cópia
  - Implementada funcionalidade de cópia para clipboard usando Clipboard API com fallback
  - Adicionados estilos CSS para hover dos ícones de cópia
- `mini_erp/pages/admin/migracao_service.py`:
  - Adicionada função `atualizar_status_migracao()` para atualizar status individual
  - Melhorada função `listar_processos_migracao()` com ordenação por status e data de distribuição
  - Suporte a múltiplos formatos de entrada: ISO, datetime com hora, apenas data, etc.
- `scripts/sync_processos_migrados.py` (NOVO):
  - Script standalone para sincronização de processos já migrados
  - Funções: `buscar_processos_migrados()`, `buscar_processos_migracao()`, `normalizar_numero_processo()`, `comparar_processos()`, `fazer_backup_colecao()`, `atualizar_status_em_lote()`, `gerar_relatorio()`
  - Usa batch write do Firestore para eficiência (máximo 500 por batch)
  - Backup automático em JSON antes de atualizar
  - Relatório detalhado em TXT com timestamp
  - Validação e tratamento de erros robusto
- `mini_erp/pages/admin/migracao_service.py`:
  - Adicionada função `excluir_processo_migracao()` para exclusão permanente de processos
  - Validação de existência do documento antes de deletar
  - Log detalhado de exclusões para auditoria
- `mini_erp/pages/admin/admin_migracao_processos.py`:
  - Adicionado botão de exclusão (ícone lixeira) na coluna de ações
  - Implementado handler `handle_excluir()` com modal de confirmação
  - Modal com avisos sobre ação permanente e processos migrados
  - Atualização automática da interface após exclusão bem-sucedida
- `mini_erp/pages/visao_geral/processos/modal/aba_dados_basicos.py`:
  - Corrigidos handlers de sincronização para campos com `with_input=True`
  - Adicionado tratamento de erros MutationObserver em `_sync_opposing()`, `_sync_others()` e `_sync_parent_processes()`
  - Validação de existência do componente antes de manipulação
  - Fallback para eventos alternativos se configuração inicial falhar

## [v1.4.0] - 2025-12-12

### Corrigido

- **Dropdown de clientes na Visão Geral do Escritório**: Resolvido bug que exibia "[object Object]" ao invés dos nomes dos clientes
- **Erro "Nenhuma pessoa encontrada"**: Unificada fonte de dados para usar coleção `vg_pessoas` consistentemente
- **Select duplicado**: Removido código redundante que criava dois selects no formulário de edição de caso

### Modificado

- `mini_erp/pages/visao_geral/casos/main.py`: Alterado import e chamada para usar `listar_pessoas()` ao invés de `listar_pessoas_colecao_people()`
- Mensagem de erro melhorada de "⚠ Erro: Nenhuma pessoa encontrada" para "Nenhum cliente cadastrado no sistema"

### Técnico

- Formato de opções do `ui.select` padronizado para `{id: nome}` (dicionário) conforme esperado pelo NiceGUI
- Fonte de dados unificada: modal de novo caso e edição de caso agora usam mesma função `listar_pessoas()`

## [v1.8.0] - 2025-12-12

### Adicionado

- Novo status "Substabelecido" para casos com cor verde claro (#86efac)
- Mapeamento de cores para o novo status em ui_components.py
- Backup script para collections do Firebase
- Relatórios de diagnóstico de bugs de usuários

### Modificado

- STATUS_OPTIONS em mini_erp/pages/casos/models.py padronizado
- Opções de status no modal "Novo Caso" da Visão Geral corrigidas
- Arquivos de configuração e core atualizados

### Corrigido

- Substituídas opções incorretas (Suspenso, Arquivado, Encerrado) pelas corretas
- Alinhamento de opções de status entre workspaces Schmidmeier e Visão Geral

## [v1.4.0] - 2025-12-12

### Adicionado

- Upload direto de foto de perfil sem editor
- Processamento automático de imagem (crop quadrado, resize 200x200)
- Logging detalhado para debug de upload de avatar
- Suporte a múltiplos formatos de imagem (JPEG, PNG, GIF, WEBP)

### Modificado

- Simplificação radical do sistema de avatar (removido editor complexo)
- Bucket do Firebase Storage atualizado para `taques-erp.firebasestorage.app`
- Leitura de arquivos adaptada para SmallFileUpload do NiceGUI

### Corrigido

- Bug de leitura de arquivo no upload (SmallFileUpload não tem `seek`)
- Erro 404 no Firebase Storage (bucket não existia)
- Erro de pickle com `run.cpu_bound()` (removido processamento em background)
- Sincronização de nome de exibição entre aba Perfil e aba Usuários

### Removido

- Editor de avatar com preview/zoom/ajuste de posição
- Código morto e imports não utilizados
- Funções `abrir_editor()`, `update_preview()`, `processar_preview_sync()`

## [v1.3.0] - 2024-12-13

### Adicionado

- **Módulo Entregáveis**: Sistema completo de gerenciamento de tarefas/entregáveis
- **Visualização Kanban**: Arrastar e soltar cards entre colunas de status
- **Colunas de Status**: Em espera (laranja), Pendente (vermelho), Em andamento (amarelo), Concluído (verde)
- **Visualização por Categoria**: Operacional, Marketing, Vendas, Administrativo, Estratégico
- **Filtros avançados**: Por categoria, prioridade e responsável
- **Ordenação automática**: Cards ordenados por prioridade (P1 primeiro)
- **Campo Link no Slack**: Vincular entregáveis a mensagens do Slack
- **CRUD completo**: Criar, visualizar, editar e excluir entregáveis
- **Drag & Drop**: Mover entregáveis entre status arrastando
- **Estatísticas no Painel**: Gráficos de entregáveis por responsável, status, categoria e prioridade
- **Contador mensal**: Total de entregáveis concluídos no mês
- **Sistema de abas no Painel**: Alternar entre estatísticas de Casos e Entregáveis

### Modificado

- **Painel**: Cards clicáveis alternam visualização de estatísticas
- **Sidebar**: Adicionado item "Entregáveis" no menu lateral

### Técnico

- Nova collection no Firestore: `entregaveis`
- Novo service: `EntregavelService`
- Novo modelo: `Entregavel`
- Integração com Firebase Auth para listar responsáveis

## [v1.10.0] - 2025-12-13

### Corrigido

- **Navegação entre Workspaces**: Restaurado funcionamento da alternância entre "Visão Geral do Escritório" e "Área do Cliente"
- **Rota Inicial**: A rota `/` agora verifica o workspace atual antes de redirecionar
- **Dropdown de Workspaces**: Correção do redirecionamento ao selecionar workspace

### Modificado

- `mini_erp/pages/painel/painel_page.py` - Lógica condicional baseada no workspace
- `mini_erp/gerenciadores/gerenciador_workspace.py` - Revertido rota_inicial do area_cliente
- `mini_erp/pages/login.py` - Ajustes no redirecionamento pós-login

## [v1.11.0] - 2025-12-19

### Adicionado

- **Prazos - Parcelamento (lista)**:
  - Badge visual "Parcelado" na coluna Título
  - Sufixo automático no título: `[Parcela X/N]` quando o prazo é uma parcela
  - Filtro: "Mostrar apenas parcelas"
  - Exclusão inteligente: "Excluir apenas esta parcela" ou "Excluir todas as parcelas"

### Modificado

- `mini_erp/pages/prazos/prazos.py`: Ajustes de UI/filtros/diálogo de exclusão para suporte a prazos parcelados
- `mini_erp/pages/prazos/modal_prazo.py`: Correção de UI do modal (botões compactos de tipo de prazo e rodapé com Cancelar/Salvar)
