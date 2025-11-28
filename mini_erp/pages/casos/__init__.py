"""
Módulo de Casos do ERP.

Este pacote contém todas as funcionalidades relacionadas
à gestão de casos, incluindo páginas, lógica de negócio,
operações de banco de dados e componentes de UI.

Estrutura:
- models.py: Constantes, opções e estado global
- database.py: Operações CRUD no Firestore
- business_logic.py: Lógica de negócio (cálculos, validações)
- ui_components.py: Componentes de UI reutilizáveis
- utils.py: Funções auxiliares e utilitários
- casos_page.py: Páginas NiceGUI principais
"""

# Exporta as páginas principais para compatibilidade com o sistema de rotas do NiceGUI
from .casos_page import casos, case_detail, case_swot

# Exporta componentes que podem ser usados em outros módulos
from .ui_components import render_cases_list, case_view_toggle, create_rich_text_editor

# Exporta funções de lógica de negócio úteis
from .business_logic import (
    get_case_type,
    get_case_sort_key,
    get_filtered_cases,
    calculate_case_number,
    generate_case_title
)

# Exporta operações de banco de dados
from .database import (
    remove_case,
    renumber_cases_of_type,
    renumber_all_cases,
    save_case,
    save_process
)

# Exporta modelos/constantes
from .models import (
    STATE_OPTIONS,
    CASE_TYPE_OPTIONS,
    CASE_CATEGORY_OPTIONS,
    MONTH_OPTIONS,
    YEAR_OPTIONS,
    STATUS_OPTIONS,
    PARTE_CONTRARIA_OPTIONS,
    filter_state
)

# Exporta utilitários
from .utils import (
    get_short_name_helper,
    get_state_flag_html,
    export_cases_to_pdf
)

# Exporta funções de detecção de duplicatas
from .duplicate_detection import (
    find_duplicate_cases,
    deduplicate_cases,
    check_for_duplicates_before_save
)

__all__ = [
    # Páginas
    'casos',
    'case_detail', 
    'case_swot',
    # UI Components
    'render_cases_list',
    'case_view_toggle',
    'create_rich_text_editor',
    # Business Logic
    'get_case_type',
    'get_case_sort_key',
    'get_filtered_cases',
    'calculate_case_number',
    'generate_case_title',
    # Database
    'remove_case',
    'renumber_cases_of_type',
    'renumber_all_cases',
    'save_case',
    'save_process',
    # Models
    'STATE_OPTIONS',
    'CASE_TYPE_OPTIONS',
    'CASE_CATEGORY_OPTIONS',
    'MONTH_OPTIONS',
    'YEAR_OPTIONS',
    'STATUS_OPTIONS',
    'PARTE_CONTRARIA_OPTIONS',
    'filter_state',
    # Utils
    'get_short_name_helper',
    'get_state_flag_html',
    'export_cases_to_pdf',
    # Duplicate Detection
    'find_duplicate_cases',
    'deduplicate_cases',
    'check_for_duplicates_before_save',
]

