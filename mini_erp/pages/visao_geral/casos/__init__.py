"""
Módulo de Casos do workspace "Visão geral do escritório".
Gerencia casos de todos os clientes do escritório com coleção Firebase separada (vg_casos).
# Removido ambiente de migração (19/12/2025) - será recriado do zero
"""
from .main import casos_visao_geral, caso_detalhes
from .caso_dialog import abrir_dialog_caso, confirmar_exclusao
