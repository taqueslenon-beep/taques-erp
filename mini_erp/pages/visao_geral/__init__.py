"""
Módulo de páginas do workspace "Visão geral do escritório".
# Removido ambiente de migração (19/12/2025) - será recriado do zero
"""
from . import painel, processos, acordos, configuracoes, dashboard_oportunidades
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





