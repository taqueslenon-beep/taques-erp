"""
Módulo de dialogs para o módulo Pessoas.
Gerencia criação, edição e operações de clientes, outros envolvidos e vínculos.
"""
from typing import Optional, Dict, Any, List, Callable, Tuple, Tuple
from nicegui import ui
from ...core import get_full_name, get_display_name, format_cpf, format_cnpj
from .database import (
    get_clients_list, get_opposing_parties_list,
    save_client, delete_client, save_opposing_party, delete_opposing_party,
    invalidate_cache, get_client_by_index,
    get_leads_list, save_lead, delete_lead
)
from .validators import (
    validate_client_documents, extract_client_documents,
    normalize_entity_type, normalize_client_type_for_display
)
from .business_logic import (
    process_partners_from_rows, get_all_people_options,
    clean_person_name_from_label, validate_bond_not_self,
    check_bond_exists, create_bond_data
)
from .models import DEFAULT_CLIENT_TYPE, CLIENT_TYPE_LABELS, LEAD_ORIGEM_OPTIONS
from .ui_components import (
    create_full_name_input, create_display_name_input, create_nickname_input,
    create_cpf_input, create_cnpj_input, create_cpf_cnpj_input,
    create_email_input, create_phone_input,
    create_client_type_select, create_entity_type_select, create_bond_type_select,
    create_partner_row
)


# =============================================================================
# CLIENT DIALOGS
# =============================================================================

def create_new_client_dialog(
    render_clients_table: Callable,
    render_bonds_map: Callable
) -> ui.dialog:
    """
    Cria dialog para cadastrar novo cliente.
    
    Args:
        render_clients_table: Função refreshable para atualizar tabela de clientes
        render_bonds_map: Função refreshable para atualizar mapa de vínculos
        
    Returns:
        Dialog configurado
    """
    with ui.dialog() as new_client_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Novo Cliente').classes('text-lg font-bold mb-4')
        
        # Campos básicos
        c_full_name = create_full_name_input()
        c_display_name = create_display_name_input()
        c_nickname = create_nickname_input()
        c_client_type = create_client_type_select()
        c_cpf = create_cpf_input()
        c_cnpj = create_cnpj_input()
        
        # Campos PJ
        c_branch_type_container = ui.element('div').classes('w-full mb-2')
        c_branch_type = None
        c_partners_container = ui.element('div').classes('w-full mb-2')
        c_partners_rows = []
        
        def toggle_pj_fields():
            is_pj = c_client_type.value == 'PJ'
            c_branch_type_container.set_visibility(is_pj)
            c_partners_container.set_visibility(is_pj)
        
        c_client_type.on('update:model-value', lambda: toggle_pj_fields())
        
        with c_branch_type_container:
            c_branch_type = ui.select(
                options=['Matriz', 'Filial'],
                label='Type *',
                value=None
            ).classes('w-full').props('dense')
            c_branch_type_container.set_visibility(False)
        
        with c_partners_container:
            partners_list = ui.element('div').classes('w-full mb-2')
            
            def add_partner_row():
                create_partner_row(partners_list, c_partners_rows)
            
            ui.label('Partners / Owners').classes('font-medium mb-2')
            ui.button('Add Partner', icon='add', on_click=add_partner_row).props('flat dense color=primary size=sm')
            c_partners_container.set_visibility(False)
        
        c_email = create_email_input()
        c_phone = create_phone_input()
        c_phone.classes('w-full mb-4')
        
        def save_client_handler():
            if not c_full_name.value:
                ui.notify('Nome Completo é obrigatório!', type='warning')
                return
            if any(get_full_name(c) == c_full_name.value for c in get_clients_list()):
                ui.notify('Cliente com este nome já existe!', type='warning')
                return
            
            client_type, cpf_digits, cnpj_digits, error = validate_client_documents(
                c_client_type.value, c_cpf.value, c_cnpj.value
            )
            if error:
                ui.notify(error, type='warning')
                return
            
            # Validações específicas para PJ
            partners = []
            if client_type == 'PJ':
                if not c_branch_type.value:
                    ui.notify('Tipo é obrigatório para Pessoa Jurídica!', type='warning')
                    return
                
                partners = process_partners_from_rows(c_partners_rows)
            
            new_client = {
                'full_name': c_full_name.value,
                'nome_exibicao': c_display_name.value or '',  # Campo padronizado
                'display_name': c_display_name.value or '',   # Mantido para compatibilidade
                'nickname': c_nickname.value or '',
                'client_type': client_type,
                'cpf': cpf_digits,
                'cnpj': cnpj_digits,
                'email': c_email.value or '',
                'phone': c_phone.value or '',
                'bonds': []
            }
            
            # Adiciona campos específicos de PJ
            if client_type == 'PJ':
                new_client['branch_type'] = c_branch_type.value
                new_client['partners'] = partners
            
            save_client(new_client)
            invalidate_cache('clients')
            render_clients_table.refresh()
            render_bonds_map.refresh()
            new_client_dialog.close()
            
            # Limpa campos
            c_full_name.value = ''
            c_display_name.value = ''
            c_nickname.value = ''
            c_client_type.value = DEFAULT_CLIENT_TYPE
            c_client_type.update()
            c_cpf.value = ''
            c_cnpj.value = ''
            c_email.value = ''
            c_phone.value = ''
            if c_branch_type:
                c_branch_type.value = None
                c_branch_type.update()
            for row in c_partners_rows:
                row['card'].delete()
            c_partners_rows.clear()
            toggle_pj_fields()
            
            ui.notify('Cliente cadastrado!')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Salvar', on_click=save_client_handler).classes('bg-primary text-white')
    
    return new_client_dialog


def create_edit_client_dialog(
    render_clients_table: Callable,
    render_bonds_map: Callable
) -> Tuple[ui.dialog, Callable]:
    """
    Cria dialog para editar cliente existente.
    
    Args:
        render_clients_table: Função refreshable para atualizar tabela de clientes
        render_bonds_map: Função refreshable para atualizar mapa de vínculos
        
    Returns:
        Tupla (dialog, open_edit_client_function)
    """
    with ui.dialog() as edit_client_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Editar Cliente').classes('text-lg font-bold mb-4')
        
        edit_c_full_name = create_full_name_input()
        edit_c_display_name = create_display_name_input()
        edit_c_nickname = create_nickname_input()
        edit_c_type = create_client_type_select()
        edit_c_cpf = create_cpf_input()
        edit_c_cnpj = create_cnpj_input()
        
        # Campos PJ
        edit_c_branch_type_container = ui.element('div').classes('w-full mb-2')
        edit_c_branch_type = None
        edit_c_partners_container = ui.element('div').classes('w-full mb-2')
        edit_c_partners_rows = []
        
        def toggle_edit_pj_fields():
            is_pj = edit_c_type.value == 'PJ'
            edit_c_branch_type_container.set_visibility(is_pj)
            edit_c_partners_container.set_visibility(is_pj)
        
        edit_c_type.on('update:model-value', lambda: toggle_edit_pj_fields())
        
        with edit_c_branch_type_container:
            edit_c_branch_type = ui.select(
                options=['Matriz', 'Filial'],
                label='Type *',
                value=None
            ).classes('w-full').props('dense')
            edit_c_branch_type_container.set_visibility(False)
        
        with edit_c_partners_container:
            edit_c_partners_list = ui.element('div').classes('w-full mb-2')
            
            def add_edit_partner_row(partner_data=None):
                create_partner_row(edit_c_partners_list, edit_c_partners_rows, partner_data)
            
            ui.label('Partners / Owners').classes('font-medium mb-2')
            ui.button('Add Partner', icon='add', on_click=lambda: add_edit_partner_row()).props('flat dense color=primary size=sm')
            edit_c_partners_container.set_visibility(False)
        
        edit_c_email = create_email_input()
        edit_c_phone = create_phone_input()
        edit_c_phone.classes('w-full mb-4')
        edit_client_index = None
        
        def open_edit_client(client):
            nonlocal edit_client_index
            edit_client_index = get_clients_list().index(client)
            edit_c_full_name.value = get_full_name(client)
            edit_c_display_name.value = client.get('nome_exibicao') or client.get('display_name', '')
            edit_c_nickname.value = client.get('nickname', '')
            current_type = client.get('client_type')
            if current_type not in CLIENT_TYPE_LABELS:
                current_type = DEFAULT_CLIENT_TYPE
            edit_c_type.value = current_type
            edit_c_type.update()
            cpf_digits, cnpj_digits = extract_client_documents(client)
            edit_c_cpf.value = format_cpf(cpf_digits) if cpf_digits else ''
            edit_c_cnpj.value = format_cnpj(cnpj_digits) if cnpj_digits else ''
            edit_c_email.value = client.get('email', '')
            edit_c_phone.value = client.get('phone', '')
            
            # Limpa sócios anteriores
            for row in edit_c_partners_rows:
                row['card'].delete()
            edit_c_partners_rows.clear()
            
            # Carrega dados específicos de PJ
            if current_type == 'PJ':
                if edit_c_branch_type:
                    edit_c_branch_type.value = client.get('branch_type')
                    edit_c_branch_type.update()
                
                # Carrega sócios existentes
                partners = client.get('partners', [])
                for partner in partners:
                    add_edit_partner_row(partner)
                
                toggle_edit_pj_fields()
            else:
                toggle_edit_pj_fields()
            
            edit_client_dialog.open()
        
        def save_edit_client():
            if not edit_c_full_name.value:
                ui.notify('Nome Completo é obrigatório!', type='warning')
                return
            
            client_type, cpf_digits, cnpj_digits, error = validate_client_documents(
                edit_c_type.value, edit_c_cpf.value, edit_c_cnpj.value
            )
            if error:
                ui.notify(error, type='warning')
                return
            
            # Validações específicas para PJ
            partners = []
            if client_type == 'PJ':
                if not edit_c_branch_type or not edit_c_branch_type.value:
                    ui.notify('Tipo é obrigatório para Pessoa Jurídica!', type='warning')
                    return
                
                partners = process_partners_from_rows(edit_c_partners_rows)
            
            if edit_client_index is not None:
                client = get_clients_list()[edit_client_index]
                existing_bonds = client.get('bonds', [])
                updated_client = {
                    'full_name': edit_c_full_name.value,
                    'nome_exibicao': edit_c_display_name.value or '',  # Campo padronizado
                    'display_name': edit_c_display_name.value or '',   # Mantido para compatibilidade
                    'nickname': edit_c_nickname.value or '',
                    'client_type': client_type,
                    'cpf': cpf_digits,
                    'cnpj': cnpj_digits,
                    'email': edit_c_email.value or '',
                    'phone': edit_c_phone.value or '',
                    'bonds': existing_bonds,
                    'created_at': client.get('created_at')
                }
                
                # Adiciona ou remove campos específicos de PJ
                if client_type == 'PJ':
                    updated_client['branch_type'] = edit_c_branch_type.value
                    updated_client['partners'] = partners
                else:
                    updated_client.pop('branch_type', None)
                    updated_client.pop('partners', None)
                
                # Preserva _id se existir
                if '_id' in client:
                    updated_client['_id'] = client['_id']
                save_client(updated_client)
                invalidate_cache('clients')
                render_clients_table.refresh()
                render_bonds_map.refresh()
                edit_client_dialog.close()
                ui.notify('Cliente atualizado!')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Salvar', on_click=save_edit_client).classes('bg-primary text-white')
    
    return edit_client_dialog, open_edit_client


# =============================================================================
# OPPOSING PARTY DIALOGS
# =============================================================================

def create_new_opposing_dialog(
    render_opposing_table: Callable
) -> ui.dialog:
    """
    Cria dialog para cadastrar novo outro envolvido.
    
    Args:
        render_opposing_table: Função refreshable para atualizar tabela
        
    Returns:
        Dialog configurado
    """
    with ui.dialog() as new_opposing_dialog, ui.card().classes('w-full max-w-md p-6'):
        ui.label('Novo Outro Envolvido').classes('text-lg font-bold mb-4')
        
        op_full_name = create_full_name_input()
        op_display_name = create_display_name_input()
        op_nickname = create_nickname_input()
        op_cpf_cnpj = create_cpf_cnpj_input()
        op_entity_type = create_entity_type_select('PF')
        op_email = create_email_input()
        op_phone = create_phone_input()
        op_phone.classes('w-full mb-4')
        
        def save_opposing():
            if not op_full_name.value:
                ui.notify('Nome Completo é obrigatório!', type='warning')
                return
            if any(get_full_name(op) == op_full_name.value for op in get_opposing_parties_list()):
                ui.notify('Outro envolvido com este nome já existe!', type='warning')
                return
            new_opposing = {
                'full_name': op_full_name.value,
                'nome_exibicao': op_display_name.value or '',  # Campo padronizado
                'display_name': op_display_name.value or '',   # Mantido para compatibilidade
                'nickname': op_nickname.value or '',
                'cpf_cnpj': op_cpf_cnpj.value or '',
                'entity_type': normalize_entity_type(op_entity_type.value),
                'email': op_email.value or '',
                'phone': op_phone.value or ''
            }
            save_opposing_party(new_opposing)
            invalidate_cache('opposing_parties')
            render_opposing_table.refresh()
            new_opposing_dialog.close()
            
            # Limpa campos
            op_full_name.value = ''
            op_display_name.value = ''
            op_nickname.value = ''
            op_cpf_cnpj.value = ''
            op_entity_type.value = 'PF'
            op_email.value = ''
            op_phone.value = ''
            ui.notify('Outro envolvido cadastrado!')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Salvar', on_click=save_opposing).classes('bg-primary text-white')
    
    return new_opposing_dialog


def create_edit_opposing_dialog(
    render_opposing_table: Callable
) -> Tuple[ui.dialog, Callable]:
    """
    Cria dialog para editar outro envolvido existente.
    
    Args:
        render_opposing_table: Função refreshable para atualizar tabela
        
    Returns:
        Tupla (dialog, open_edit_opposing_function)
    """
    with ui.dialog() as edit_opposing_dialog, ui.card().classes('w-full max-w-md p-6'):
        ui.label('Editar Outro Envolvido').classes('text-lg font-bold mb-4')
        
        edit_op_full_name = create_full_name_input()
        edit_op_display_name = create_display_name_input()
        edit_op_nickname = create_nickname_input()
        edit_op_cpf_cnpj = create_cpf_cnpj_input()
        edit_op_entity_type = create_entity_type_select('PF')
        edit_op_email = create_email_input()
        edit_op_phone = create_phone_input()
        edit_op_phone.classes('w-full mb-4')
        edit_opposing_index = None
        
        def open_edit_opposing(opposing):
            nonlocal edit_opposing_index
            edit_opposing_index = get_opposing_parties_list().index(opposing)
            edit_op_full_name.value = get_full_name(opposing)
            edit_op_display_name.value = opposing.get('nome_exibicao') or opposing.get('display_name', '')
            edit_op_nickname.value = opposing.get('nickname', '')
            edit_op_cpf_cnpj.value = opposing.get('cpf_cnpj') or opposing.get('document', '')
            edit_op_entity_type.value = normalize_entity_type(opposing.get('entity_type', 'PF'))
            edit_op_entity_type.update()
            edit_op_email.value = opposing.get('email', '')
            edit_op_phone.value = opposing.get('phone', '')
            edit_opposing_dialog.open()
        
        def save_edit_opposing():
            if not edit_op_full_name.value:
                ui.notify('Nome Completo é obrigatório!', type='warning')
                return
            if edit_opposing_index is not None:
                opposing = get_opposing_parties_list()[edit_opposing_index]
                updated_opposing = {
                    'full_name': edit_op_full_name.value,
                    'nome_exibicao': edit_op_display_name.value or '',  # Campo padronizado
                    'display_name': edit_op_display_name.value or '',   # Mantido para compatibilidade
                    'nickname': edit_op_nickname.value or '',
                    'cpf_cnpj': edit_op_cpf_cnpj.value or '',
                    'entity_type': normalize_entity_type(edit_op_entity_type.value),
                    'email': edit_op_email.value or '',
                    'phone': edit_op_phone.value or '',
                    'created_at': opposing.get('created_at')
                }
                # Preserva _id se existir
                if '_id' in opposing:
                    updated_opposing['_id'] = opposing['_id']
                save_opposing_party(updated_opposing)
                invalidate_cache('opposing_parties')
                render_opposing_table.refresh()
                edit_opposing_dialog.close()
                ui.notify('Outro envolvido atualizado!')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Salvar', on_click=save_edit_opposing).classes('bg-primary text-white')
    
    return edit_opposing_dialog, open_edit_opposing


# =============================================================================
# BOND DIALOG
# =============================================================================

def create_add_bond_dialog(
    render_bonds_map: Callable
) -> Tuple[ui.dialog, Callable, Callable]:
    """
    Cria dialog para adicionar vínculo entre pessoas.
    
    Args:
        render_bonds_map: Função refreshable para atualizar mapa de vínculos
        
    Returns:
        Tupla (dialog, open_add_bond_function, remove_bond_function)
    """
    with ui.dialog() as add_bond_dialog, ui.card().classes('w-full max-w-sm p-4'):
        add_bond_title = ui.label('Adicionar Vínculo').classes('font-bold mb-3')
        add_bond_client_idx = {'value': None}
        
        bond_person_select = ui.select(
            options=[],
            label='Pessoa',
            with_input=True
        ).classes('w-full mb-2').props('dense')
        
        bond_type_select = create_bond_type_select()
        
        def save_bond():
            if not bond_person_select.value or not bond_type_select.value:
                ui.notify('Preencha todos os campos!', type='warning')
                return
            
            idx = add_bond_client_idx['value']
            if idx is None or idx >= len(get_clients_list()):
                return
            
            client = get_clients_list()[idx]
            person_label = bond_person_select.value
            person_name = clean_person_name_from_label(person_label)
            
            if not validate_bond_not_self(person_label, get_full_name(client)):
                ui.notify('Não é possível vincular a si mesmo!', type='warning')
                return
            
            if check_bond_exists(client, person_name):
                ui.notify('Vínculo já existe!', type='warning')
                return
            
            if 'bonds' not in client:
                client['bonds'] = []
            
            bond_data = create_bond_data(person_label, bond_type_select.value)
            client['bonds'].append(bond_data)
            
            save_client(client)
            invalidate_cache('clients')
            add_bond_dialog.close()
            render_bonds_map.refresh()
            ui.notify('Vínculo adicionado!')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=add_bond_dialog.close).props('flat dense')
            ui.button('Salvar', on_click=save_bond).props('dense color=primary')
    
    def open_add_bond(client_idx):
        add_bond_client_idx['value'] = client_idx
        client = get_clients_list()[client_idx]
        add_bond_title.text = f"Vínculo - {get_display_name(client)}"
        bond_person_select.options = get_all_people_options()
        bond_person_select.value = None
        bond_type_select.value = None
        bond_person_select.update()
        add_bond_dialog.open()
    
    def remove_bond(client_idx, bond_idx):
        client = get_clients_list()[client_idx]
        client['bonds'].pop(bond_idx)
        save_client(client)
        invalidate_cache('clients')
        render_bonds_map.refresh()
        ui.notify('Vínculo removido!')
    
    return add_bond_dialog, open_add_bond, remove_bond


# =============================================================================
# LEAD DIALOGS
# =============================================================================

def create_new_lead_dialog(
    render_leads_table: Callable
) -> ui.dialog:
    """
    Cria dialog para cadastrar novo lead.
    
    Args:
        render_leads_table: Função refreshable para atualizar tabela
        
    Returns:
        Dialog configurado
    """
    with ui.dialog() as new_lead_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Novo Lead').classes('text-lg font-bold mb-4')
        
        # Campos obrigatórios - Nome e Nome de Exibição (na mesma linha)
        with ui.row().classes('w-full gap-4 mb-2'):
            lead_nome = ui.input('Nome *').classes('flex-1')
            lead_nome_exibicao = ui.input('Nome de Exibição').classes('flex-1')
        
        # Campos opcionais
        lead_email = create_email_input()
        lead_telefone = create_phone_input()
        lead_telefone.label = 'Telefone'
        
        lead_endereco = ui.input('Endereço').classes('w-full mb-2')
        lead_cidade = ui.input('Cidade').classes('w-full mb-2')
        lead_estado = ui.input('Estado').classes('w-full mb-2')
        lead_cep = ui.input('CEP').classes('w-full mb-2')
        lead_cpf_cnpj = create_cpf_cnpj_input()
        
        # Campo origem como dropdown
        lead_origem = ui.select(
            options=LEAD_ORIGEM_OPTIONS,
            label='Origem',
            value=None
        ).classes('w-full mb-2').props('dense')
        
        lead_observacoes = ui.textarea('Observações').classes('w-full mb-4').props('rows=3')
        
        def save_lead_handler():
            if not lead_nome.value:
                ui.notify('Nome é obrigatório!', type='warning')
                return
            
            new_lead = {
                'nome': lead_nome.value,
                'nome_exibicao': lead_nome_exibicao.value or '',
                'email': lead_email.value or '',
                'telefone': lead_telefone.value or '',
                'endereco': lead_endereco.value or '',
                'cidade': lead_cidade.value or '',
                'estado': lead_estado.value or '',
                'cep': lead_cep.value or '',
                'cpf_cnpj': lead_cpf_cnpj.value or '',
                'observacoes': lead_observacoes.value or '',
                'origem': lead_origem.value or ''
            }
            
            save_lead(new_lead)
            invalidate_cache('pessoas')
            render_leads_table.refresh()
            new_lead_dialog.close()
            
            # Limpa campos
            lead_nome.value = ''
            lead_nome_exibicao.value = ''
            lead_email.value = ''
            lead_telefone.value = ''
            lead_endereco.value = ''
            lead_cidade.value = ''
            lead_estado.value = ''
            lead_cep.value = ''
            lead_cpf_cnpj.value = ''
            lead_origem.value = None
            lead_origem.update()
            lead_observacoes.value = ''
            
            ui.notify('Lead cadastrado!')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Salvar', on_click=save_lead_handler).classes('bg-primary text-white')
    
    return new_lead_dialog


def create_edit_lead_dialog(
    render_leads_table: Callable
) -> Tuple[ui.dialog, Callable]:
    """
    Cria dialog para editar lead existente.
    
    Args:
        render_leads_table: Função refreshable para atualizar tabela
        
    Returns:
        Tupla (dialog, open_edit_lead_function)
    """
    edit_lead_index = {'value': None}
    
    with ui.dialog() as edit_lead_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Editar Lead').classes('text-lg font-bold mb-4')
        
        # Nome e Nome de Exibição (na mesma linha)
        with ui.row().classes('w-full gap-4 mb-2'):
            edit_lead_nome = ui.input('Nome *').classes('flex-1')
            edit_lead_nome_exibicao = ui.input('Nome de Exibição').classes('flex-1')
        
        edit_lead_email = create_email_input()
        edit_lead_telefone = create_phone_input()
        edit_lead_telefone.label = 'Telefone'
        
        edit_lead_endereco = ui.input('Endereço').classes('w-full mb-2')
        edit_lead_cidade = ui.input('Cidade').classes('w-full mb-2')
        edit_lead_estado = ui.input('Estado').classes('w-full mb-2')
        edit_lead_cep = ui.input('CEP').classes('w-full mb-2')
        edit_lead_cpf_cnpj = create_cpf_cnpj_input()
        
        edit_lead_origem = ui.select(
            options=LEAD_ORIGEM_OPTIONS,
            label='Origem',
            value=None
        ).classes('w-full mb-2').props('dense')
        
        edit_lead_observacoes = ui.textarea('Observações').classes('w-full mb-4').props('rows=3')
        
        def open_edit_lead(lead):
            leads_list = get_leads_list()
            try:
                edit_lead_index['value'] = leads_list.index(lead)
            except ValueError:
                edit_lead_index['value'] = None
            
            edit_lead_nome.value = lead.get('nome') or lead.get('full_name', '')
            edit_lead_nome_exibicao.value = lead.get('nome_exibicao', '')
            edit_lead_email.value = lead.get('email', '')
            edit_lead_telefone.value = lead.get('telefone', '')
            edit_lead_endereco.value = lead.get('endereco', '')
            edit_lead_cidade.value = lead.get('cidade', '')
            edit_lead_estado.value = lead.get('estado', '')
            edit_lead_cep.value = lead.get('cep', '')
            edit_lead_cpf_cnpj.value = lead.get('cpf_cnpj', '')
            edit_lead_origem.value = lead.get('origem', '')
            edit_lead_origem.update()
            edit_lead_observacoes.value = lead.get('observacoes', '')
            edit_lead_dialog.open()
        
        def save_edit_lead():
            if not edit_lead_nome.value:
                ui.notify('Nome é obrigatório!', type='warning')
                return
            
            idx = edit_lead_index['value']
            if idx is not None and 0 <= idx < len(get_leads_list()):
                lead = get_leads_list()[idx]
                updated_lead = {
                    'nome': edit_lead_nome.value,
                    'nome_exibicao': edit_lead_nome_exibicao.value or '',
                    'email': edit_lead_email.value or '',
                    'telefone': edit_lead_telefone.value or '',
                    'endereco': edit_lead_endereco.value or '',
                    'cidade': edit_lead_cidade.value or '',
                    'estado': edit_lead_estado.value or '',
                    'cep': edit_lead_cep.value or '',
                    'cpf_cnpj': edit_lead_cpf_cnpj.value or '',
                    'observacoes': edit_lead_observacoes.value or '',
                    'origem': edit_lead_origem.value or '',
                    'tipo_pessoa': 'lead',
                    'status_lead': 'lead',
                    'data_cadastro': lead.get('data_cadastro'),
                    'created_at': lead.get('created_at')
                }
                
                # Preserva _id se existir
                if '_id' in lead:
                    updated_lead['_id'] = lead['_id']
                
                save_lead(updated_lead)
                invalidate_cache('pessoas')
                render_leads_table.refresh()
                edit_lead_dialog.close()
                ui.notify('Lead atualizado!')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Salvar', on_click=save_edit_lead).classes('bg-primary text-white')
    
    return edit_lead_dialog, open_edit_lead

