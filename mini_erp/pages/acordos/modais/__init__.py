"""
modais/__init__.py - Modais principais do módulo de Acordos.
"""

from .modal_novo_acordo import render_acordo_dialog
from .modal_editar_acordo import render_acordo_edit_dialog

__all__ = ['render_acordo_dialog', 'render_acordo_edit_dialog']

