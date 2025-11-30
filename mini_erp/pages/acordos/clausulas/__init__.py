"""
clausulas/__init__.py - Subseção de Cláusulas do módulo de Acordos.
"""

from .visualizacoes import lista_clausulas
from .modais.modal_nova_clausula import criar_dialog_nova_clausula

__all__ = ['lista_clausulas', 'criar_dialog_nova_clausula']

