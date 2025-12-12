
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

