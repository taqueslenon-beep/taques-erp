"""
utils - Utilitários para salvamento seguro e logging de dados.
"""

from .save_logger import SaveLogger
from .safe_save import safe_save, criar_auto_save

__all__ = ['SaveLogger', 'safe_save', 'criar_auto_save']

