"""
Módulo de modelos e constantes para Acordos/Parcelamentos.
Workspace: Visão Geral do Escritório
"""
# Importar núcleos do módulo de casos (mesma fonte)
from ..casos.models import NUCLEO_OPTIONS, NUCLEO_CORES

# Área do direito (copiar do módulo de processos)
AREA_OPTIONS = ['Administrativo', 'Criminal', 'Cível', 'Tributário', 'Técnico/projetos', 'Outros']

# Tipo de acordo
TIPO_ACORDO_OPTIONS = ['Judicial', 'Extrajudicial']

# Status do acordo (para uso futuro)
STATUS_ACORDO_OPTIONS = [
    'Em negociação',
    'Assinado',
    'Em cumprimento',
    'Cumprido',
    'Descumprido',
    'Cancelado'
]










