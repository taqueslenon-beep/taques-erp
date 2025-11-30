"""
clausulas/models.py - Modelos de dados para cláusulas.

Reexporta modelos do módulo principal de acordos.
"""

from ..models import (
    ClausulaDict,
    CLAUSULA_TIPO_OPTIONS,
    CLAUSULA_TIPO_GERAL,
    CLAUSULA_TIPO_ESPECIFICA,
    CLAUSULA_STATUS_OPTIONS,
    CLAUSULA_STATUS_CUMPRIDA,
    CLAUSULA_STATUS_PENDENTE,
    CLAUSULA_STATUS_ATRASADA,
)

__all__ = [
    'ClausulaDict',
    'CLAUSULA_TIPO_OPTIONS',
    'CLAUSULA_TIPO_GERAL',
    'CLAUSULA_TIPO_ESPECIFICA',
    'CLAUSULA_STATUS_OPTIONS',
    'CLAUSULA_STATUS_CUMPRIDA',
    'CLAUSULA_STATUS_PENDENTE',
    'CLAUSULA_STATUS_ATRASADA',
]

