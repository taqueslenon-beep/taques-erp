"""
modais/abas/__init__.py - Abas dos modais de acordos.
"""

from .aba_identificacao import render_aba_identificacao
from .aba_vinculacoes import render_aba_vinculacoes
from .aba_partes import render_aba_partes

__all__ = ['render_aba_identificacao', 'render_aba_vinculacoes', 'render_aba_partes']

