"""
modais - Módulo de modais para processos.

Contém o modal principal de processo e suas abas:
- modal_processo: Modal principal que orquestra todas as 8 abas
- modal_processo_futuro: Modal para processos futuros
- modal_protocolo: Modal para protocolos independentes
- modal_acompanhamento_terceiros: Modal para acompanhamentos
- abas/: Componentes individuais de cada aba
- validacoes/: Validações específicas por aba
"""

from .modal_processo import render_process_dialog
from .modal_processo_futuro import render_future_process_dialog
from .modal_protocolo import render_protocol_dialog
from .modal_acompanhamento_terceiros import render_third_party_monitoring_dialog

__all__ = [
    'render_process_dialog',
    'render_future_process_dialog',
    'render_protocol_dialog',
    'render_third_party_monitoring_dialog',
]

