"""
Módulo de páginas do workspace "Visão geral do escritório".
"""
from . import painel, processos, acordos, configuracoes, dashboard_oportunidades
# Telas de migração
from . import migracao_casos, migracao_processos
# Módulos que são subpacotes completos
from .pessoas import pessoas_visao_geral
# Importa módulo pessoas completo para registrar todas as rotas (incluindo migracao_clientes)
from . import pessoas
from .casos import casos_visao_geral
from .entregaveis import entregaveis_page
# Módulo de Novos Negócios
from ..novos_negocios import novos_negocios
# Módulo Central de Comando (apenas para administradores)
from . import central_comando





