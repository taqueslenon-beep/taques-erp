"""
modais/validacoes/__init__.py - Validações por aba dos modais de acordos.
"""

from .validar_identificacao import validar_identificacao
from .validar_vinculacoes import validar_vinculacoes
from .validar_partes import validar_partes

__all__ = ['validar_identificacao', 'validar_vinculacoes', 'validar_partes']

