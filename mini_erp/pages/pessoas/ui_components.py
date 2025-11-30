"""
Módulo de componentes UI reutilizáveis para o módulo Pessoas.
Contém funções para criar inputs, selects e outros componentes padronizados.
"""
from typing import Optional, Callable, Dict, Any, List, Tuple
from nicegui import ui
from .models import (
    CLIENT_TYPE_OPTIONS, DEFAULT_CLIENT_TYPE, BRANCH_TYPE_OPTIONS,
    ENTITY_TYPES, BOND_TYPES
)
from .business_logic import get_people_options_for_partners


# =============================================================================
# COMPONENTES DE INPUT
# =============================================================================

def create_full_name_input() -> ui.input:
    """Cria input padronizado para nome completo."""
    return ui.input('Nome Completo *').classes('w-full mb-2')


def create_display_name_input() -> ui.input:
    """
    Cria input padronizado para nome de exibição.
    
    ATUALIZADO: Agora usa o campo padronizado 'nome_exibicao'.
    """
    return ui.input('Nome de Exibição').classes('w-full mb-2').tooltip('Nome que será exibido em todo o sistema')


def create_nickname_input() -> ui.input:
    """Cria input padronizado para apelido/sigla."""
    return ui.input('Apelido/Sigla').classes('w-full mb-2')


def create_cpf_input() -> ui.input:
    """Cria input padronizado para CPF."""
    return ui.input('CPF').classes('w-full mb-2')


def create_cnpj_input() -> ui.input:
    """Cria input padronizado para CNPJ."""
    return ui.input('CNPJ').classes('w-full mb-2')


def create_cpf_cnpj_input() -> ui.input:
    """Cria input padronizado para CPF/CNPJ (outros envolvidos)."""
    return ui.input('CPF/CNPJ (opcional)').classes('w-full mb-2')


def create_email_input() -> ui.input:
    """Cria input padronizado para email."""
    return ui.input('Email').classes('w-full mb-2')


def create_phone_input() -> ui.input:
    """Cria input padronizado para telefone."""
    return ui.input('Telefone').classes('w-full mb-2')


# =============================================================================
# COMPONENTES DE SELECT
# =============================================================================

def create_client_type_select(value: Optional[str] = None) -> ui.select:
    """Cria select padronizado para tipo de cliente."""
    # NiceGUI não aceita string vazia, usa None ou valor padrão
    if not value or value == '':
        value = DEFAULT_CLIENT_TYPE
    select = ui.select(
        options=CLIENT_TYPE_OPTIONS,
        value=value,
        label='Tipo *'
    ).classes('w-full mb-2').props('dense')
    return select


def create_entity_type_select(value: Optional[str] = None) -> ui.select:
    """Cria select padronizado para tipo de entidade."""
    # NiceGUI não aceita string vazia, usa None ou valor padrão
    if not value or value == '':
        value = 'PF'
    select = ui.select(
        options=ENTITY_TYPES,
        value=value,
        label='Tipo de Entidade *'
    ).classes('w-full mb-2').props('dense')
    return select


def create_bond_type_select(value: str = '') -> ui.select:
    """Cria select padronizado para tipo de vínculo."""
    select = ui.select(
        options=BOND_TYPES,
        label='Tipo'
    ).classes('w-full mb-3').props('dense')
    if value:
        select.value = value
    return select


def create_branch_type_select(value: Optional[str] = None) -> ui.select:
    """Cria select padronizado para tipo de filial."""
    select = ui.select(
        options=BRANCH_TYPE_OPTIONS,
        label='Type *',
        value=value
    ).classes('w-full').props('dense')
    return select


# =============================================================================
# COMPONENTES DE SÓCIOS (PARTNERS)
# =============================================================================

def create_partner_row(
    container_element: ui.element,
    partners_rows: List[Dict[str, Any]],
    partner_data: Optional[Dict[str, Any]] = None,
    on_partner_change: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Cria uma linha de sócio reutilizável.
    
    Args:
        container_element: Elemento container onde a linha será adicionada
        partners_rows: Lista que armazena dados das linhas de sócios
        partner_data: Dados opcionais do sócio (para edição)
        on_partner_change: Callback opcional quando sócio é selecionado
        
    Returns:
        Dicionário com referências aos componentes da linha
    """
    people_options, people_data = get_people_options_for_partners()
    
    row_card = ui.card().classes('w-full p-3 mb-2 bg-gray-50')
    with row_card:
        with ui.row().classes('w-full gap-2 items-end'):
            partner_select = ui.select(
                options=people_options,
                label='Person *',
                with_input=True
            ).classes('flex-grow').props('dense')
            
            partner_share = ui.input('Share (%)').classes('w-32')
            
            # Se há dados do parceiro, seleciona no dropdown
            if partner_data:
                partner_name_val = partner_data.get('full_name', '')
                # Tenta encontrar o label correspondente
                for label, value in people_options.items():
                    if value == partner_name_val:
                        partner_select.value = label
                        break
                partner_share.value = partner_data.get('share', '')
            
            def on_partner_selected():
                selected_label = partner_select.value
                if selected_label and selected_label in people_data:
                    person_info = people_data[selected_label]
                    row_data['person_name'] = person_info['value']
                    row_data['person_cpf'] = person_info.get('cpf', '')
                    row_data['person_type'] = person_info['type']
                    if on_partner_change:
                        on_partner_change(row_data)
            
            partner_select.on('update:model-value', on_partner_selected)
            
            def remove_row():
                if row_data in partners_rows:
                    partners_rows.remove(row_data)
                row_card.delete()
            
            remove_btn = ui.button(
                icon='delete',
                on_click=remove_row
            ).props('flat dense color=red size=sm')
    
    row_data = {
        'select': partner_select,
        'share': partner_share,
        'card': row_card,
        'person_name': partner_data.get('full_name', '') if partner_data else '',
        'person_cpf': partner_data.get('cpf', '') if partner_data else '',
        'person_type': partner_data.get('type', '') if partner_data else ''
    }
    partners_rows.append(row_data)
    
    return row_data


def create_partners_container(
    parent_container: ui.element,
    partners_rows: List[Dict[str, Any]],
    initial_partners: Optional[List[Dict[str, Any]]] = None
) -> ui.element:
    """
    Cria container completo de sócios com botão de adicionar.
    
    Args:
        parent_container: Container pai onde será criado
        partners_rows: Lista que armazena dados das linhas de sócios
        initial_partners: Lista opcional de sócios iniciais (para edição)
        
    Returns:
        Elemento container de sócios
    """
    partners_container = ui.element('div').classes('w-full mb-2')
    
    with partners_container:
        ui.label('Partners / Owners').classes('font-medium mb-2')
        partners_list = ui.element('div').classes('w-full mb-2')
        
        def add_partner_row():
            create_partner_row(partners_list, partners_rows)
        
        # Adiciona sócios iniciais se houver
        if initial_partners:
            for partner in initial_partners:
                create_partner_row(partners_list, partners_rows, partner)
        
        ui.button(
            'Add Partner',
            icon='add',
            on_click=add_partner_row
        ).props('flat dense color=primary size=sm')
    
    return partners_container


# =============================================================================
# COMPONENTES DE CAMPOS PJ
# =============================================================================

def create_pj_fields_container(
    parent_container: ui.element,
    client_type_select: ui.select,
    branch_type_value: Optional[str] = None
) -> Tuple[ui.element, ui.select, ui.element]:
    """
    Cria container com campos específicos de PJ (branch_type e partners).
    
    Args:
        parent_container: Container pai onde será criado
        client_type_select: Select de tipo de cliente (para toggle de visibilidade)
        branch_type_value: Valor inicial opcional para branch_type
        
    Returns:
        Tupla (branch_type_container, branch_type_select, partners_container)
    """
    # Container de branch_type
    branch_type_container = ui.element('div').classes('w-full mb-2')
    with branch_type_container:
        branch_type_select = create_branch_type_select(branch_type_value)
        branch_type_container.set_visibility(False)
    
    # Container de partners (será criado separadamente quando necessário)
    partners_container = ui.element('div').classes('w-full mb-2')
    partners_container.set_visibility(False)
    
    def toggle_pj_fields():
        is_pj = client_type_select.value == 'PJ'
        branch_type_container.set_visibility(is_pj)
        partners_container.set_visibility(is_pj)
    
    client_type_select.on('update:model-value', lambda: toggle_pj_fields())
    
    return branch_type_container, branch_type_select, partners_container


# =============================================================================
# HELPERS DE FORMATAÇÃO
# =============================================================================

def format_document_display(client: Dict[str, Any]) -> str:
    """
    Formata documento do cliente para exibição.
    
    Args:
        client: Dicionário com dados do cliente
        
    Returns:
        String formatada com CPF/CNPJ
    """
    return client.get('cpf_cnpj') or client.get('document', '')

