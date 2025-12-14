"""
Módulo de Processos do workspace "Visão geral do escritório".
Exibe todos os processos de todos os clientes do escritório.

Este arquivo redireciona para a implementação principal em processos/main.py
"""
# Importa a função principal do módulo de processos
from .processos.main import processos_visao_geral

# Exporta como 'processos' para manter compatibilidade com rotas existentes
processos = processos_visao_geral

__all__ = ['processos']





