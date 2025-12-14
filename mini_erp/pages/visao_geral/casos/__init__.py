"""
Módulo de Casos do workspace "Visão geral do escritório".
Gerencia casos de todos os clientes do escritório com coleção Firebase separada (vg_casos).
"""
from .main import casos_visao_geral, caso_detalhes
from .caso_dialog import abrir_dialog_caso, confirmar_exclusao
# NOTA: migracao_casos foi movido para ../migracao_casos.py para evitar conflitos de rota
