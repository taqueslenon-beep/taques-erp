"""
Módulo de páginas do workspace "Visão geral do escritório".
"""
from . import painel, processos, acordos, configuracoes, dashboard_oportunidades
# Módulos que são subpacotes completos
from .pessoas import pessoas_visao_geral
# Importa módulo pessoas completo para registrar todas as rotas (incluindo migracao_clientes)
from . import pessoas

# Importa rota de migração de casos (fora do módulo casos para evitar conflitos)
from . import migracao_casos  # Rota: /visao-geral/migracao-casos

# Importa rotas genéricas de casos
from .casos.main import casos_visao_geral, caso_detalhes
from .entregaveis import entregaveis_page
# Módulo de Novos Negócios
from ..novos_negocios import novos_negocios





