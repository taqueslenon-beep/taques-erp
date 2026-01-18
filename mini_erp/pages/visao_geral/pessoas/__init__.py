"""
Módulo de Pessoas do workspace "Visão geral do escritório".
Gerencia pessoas cadastradas no sistema com coleção Firebase separada (vg_pessoas).
"""
from .main import pessoas_visao_geral
from .estatisticas import pessoas_estatisticas
from . import migracao_clientes  # Registra rota /visao-geral/pessoas/migracao-clientes
from . import migracao_envolvidos  # Registra rota /visao-geral/pessoas/migracao-envolvidos