"""
modais/__init__.py - Modais do módulo de Acordos.
"""

from .modal_novo_acordo import render_acordo_dialog
from .modal_nova_clausula import render_clausula_dialog

__all__ = ['render_acordo_dialog', 'render_clausula_dialog']
