# Módulo de Migração Administrativa (EPROC-TJSC)

Este módulo permite a migração em lote de processos extraídos do sistema EPROC-TJSC através de uma planilha Excel (.xls).

## Como utilizar

1. **Acesso:** Acesse a rota `/admin/migracao-processos`.
2. **Importação:** Clique em "Importar Planilha" para ler os dados de `/Users/lenontaques/Documents/taques-erp/relatorio-processos-2025-lenon.xls`.
3. **Preenchimento:** Utilize a lista de processos pendentes para completar os dados necessários (Título, Clientes, Casos, etc).
4. **Sugestões:** O sistema exibe os Autores e Réus originais da planilha para facilitar o vínculo com as pessoas já cadastradas no sistema.
5. **Finalização:** Após completar todos os 106 processos, utilize o botão "Finalizar Migração" para concluir o processo.

## Estrutura Técnica

- `admin_migracao_processos.py`: Interface NiceGUI da página administrativa.
- `migracao_service.py`: Lógica de processamento e integração com Firestore.
- `migracao_models.py`: Definições de tipos para a coleção temporária `processos_migracao`.

## Coleções Firestore
- `processos_migracao`: Dados temporários e progresso da migração.
- `vg_processos`: Coleção definitiva onde os processos são criados após a conclusão.

