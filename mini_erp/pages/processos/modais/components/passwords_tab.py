"""
passwords_tab.py - Componente reutilizável para interface de "Senhas de acesso"

Este componente fornece a interface completa de gestão de senhas para ser
usada em qualquer modal de processo.
"""

from nicegui import ui
from typing import Callable, Optional
import json
from ...database import (
    get_process_passwords,
    save_process_password,
    delete_process_password
)


def render_passwords_tab(process_id_getter: Callable[[], Optional[str]], collection_name: str = 'processes'):
    """
    Renderiza a aba completa de "Senhas de acesso" como componente reutilizável.
    
    Args:
        process_id_getter: Função que retorna o ID do processo/acompanhamento atual (pode retornar None se não salvo)
        collection_name: Nome da coleção no Firestore ('processes' ou 'third_party_monitoring')
    
    Returns:
        Tupla (tab_panel, refresh_function) onde:
        - tab_panel: O ui.tab_panel criado
        - refresh_function: Função para atualizar a lista de senhas
    """
    
    # Dialog de confirmação de exclusão
    with ui.dialog() as delete_senha_dialog, ui.card().classes('p-4 w-96'):
        ui.label('Confirmar exclusão').classes('text-lg font-bold mb-3')
        ui.label('Deseja realmente excluir esta senha? Esta ação não pode ser desfeita.').classes('text-gray-700 mb-4')
        delete_senha_id_ref = {'val': None}
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=delete_senha_dialog.close).props('flat')
            
            def confirm_delete_senha():
                pid = delete_senha_id_ref['val']
                process_id = process_id_getter()
                if pid and process_id:
                    success, message = delete_process_password(process_id, pid, collection_name)
                    if success:
                        ui.notify(message, type='positive')
                        render_passwords.refresh()
                    else:
                        ui.notify(message, type='negative')
                delete_senha_dialog.close()
            
            ui.button('Excluir', on_click=confirm_delete_senha).props('color=red')
    
    # Dialog para cadastrar/editar senha
    with ui.dialog() as senha_dialog, ui.card().classes('p-4 w-[500px]'):
        senha_title_label = ui.label('Nova senha').classes('text-lg font-bold mb-3')
        
        senha_titulo_input = ui.input('Título *', placeholder='Ex: Acesso ao sistema SEI').classes('w-full').props('dense outlined')
        senha_usuario_input = ui.input('Usuário', placeholder='Nome de usuário para login').classes('w-full').props('dense outlined')
        
        # Campo de senha com toggle mostrar/ocultar
        with ui.row().classes('w-full items-end gap-2'):
            senha_password_input = ui.input('Senha *', placeholder='Senha para login', password=True).classes('flex-grow').props('dense outlined')
            senha_toggle_btn = ui.button(icon='visibility_off', on_click=lambda: toggle_password_visibility()).props('flat dense').tooltip('Mostrar/ocultar senha')
        
        senha_link_input = ui.input('Link de acesso', placeholder='https://...').classes('w-full').props('dense outlined')
        senha_obs_textarea = ui.textarea('Observações', placeholder='Notas adicionais...').classes('w-full').props('dense outlined rows=3')
        
        senha_id_ref = {'val': None}
        senha_show_password = {'val': False}
        
        def toggle_password_visibility():
            senha_show_password['val'] = not senha_show_password['val']
            if senha_show_password['val']:
                senha_password_input.props(remove='password')
                senha_toggle_btn.props(remove='icon=visibility_off')
                senha_toggle_btn.props(add='icon=visibility')
                senha_toggle_btn.tooltip('Ocultar senha')
            else:
                senha_password_input.props(add='password')
                senha_toggle_btn.props(remove='icon=visibility')
                senha_toggle_btn.props(add='icon=visibility_off')
                senha_toggle_btn.tooltip('Mostrar senha')
        
        def save_password():
            if not senha_titulo_input.value or not senha_titulo_input.value.strip():
                ui.notify('Título é obrigatório!', type='warning')
                return
            
            if not senha_password_input.value or not senha_password_input.value.strip():
                ui.notify('Senha é obrigatória!', type='warning')
                return
            
            # Validar URL se fornecida
            link = senha_link_input.value.strip()
            if link and not (link.startswith('http://') or link.startswith('https://')):
                ui.notify('Link deve começar com http:// ou https://', type='warning')
                return
            
            process_id = process_id_getter()
            if not process_id:
                ui.notify('Processo não identificado. Salve o processo primeiro.', type='warning')
                return
            
            password_data = {
                'titulo': senha_titulo_input.value.strip(),
                'usuario': senha_usuario_input.value.strip() if senha_usuario_input.value else '',
                'senha': senha_password_input.value,
                'link_acesso': link if link else '',
                'observacoes': senha_obs_textarea.value.strip() if senha_obs_textarea.value else ''
            }
            
            success, password_id, message = save_process_password(
                process_id,
                password_data,
                senha_id_ref['val'],
                collection_name
            )
            
            if success:
                ui.notify(message, type='positive')
                senha_dialog.close()
                render_passwords.refresh()
            else:
                ui.notify(message, type='negative')
        
        with ui.row().classes('w-full justify-end gap-2 mt-3'):
            ui.button('Cancelar', on_click=senha_dialog.close).props('flat')
            senha_save_btn = ui.button('Salvar', on_click=save_password).props('color=primary')
        
        def open_senha_dialog(password_id=None):
            senha_id_ref['val'] = password_id
            senha_show_password['val'] = False
            senha_password_input.props(add='password')
            senha_toggle_btn.props(remove='icon=visibility')
            senha_toggle_btn.props(add='icon=visibility_off')
            senha_toggle_btn.tooltip('Mostrar senha')
            
            process_id = process_id_getter()
            
            if password_id and process_id:
                # Edição - carregar dados
                senhas = get_process_passwords(process_id, collection_name)
                senha_data = next((s for s in senhas if s.get('id') == password_id), None)
                if senha_data:
                    senha_title_label.text = 'Editar senha'
                    senha_save_btn.text = 'Salvar'
                    senha_titulo_input.value = senha_data.get('titulo', '')
                    senha_usuario_input.value = senha_data.get('usuario', '')
                    senha_password_input.value = senha_data.get('senha', '')
                    senha_link_input.value = senha_data.get('link_acesso', '')
                    senha_obs_textarea.value = senha_data.get('observacoes', '')
                else:
                    ui.notify('Senha não encontrada', type='warning')
                    return
            else:
                # Nova senha
                senha_title_label.text = 'Nova senha'
                senha_save_btn.text = 'Salvar'
                senha_titulo_input.value = ''
                senha_usuario_input.value = ''
                senha_password_input.value = ''
                senha_link_input.value = ''
                senha_obs_textarea.value = ''
            
            senha_dialog.open()
    
    # Renderizar conteúdo dentro do tab_panel existente
    # Header com botão de adicionar
    with ui.row().classes('w-full justify-between items-center mb-4'):
        ui.label('🔑 Senhas de acesso').classes('text-lg font-bold text-gray-800')
        ui.button(
            '+ Nova senha',
            icon='add',
            on_click=lambda: (
                open_senha_dialog(None) if process_id_getter() else
                ui.notify('Salve o processo primeiro para adicionar senhas', type='warning')
            )
        ).props('flat dense color=primary')
    
    @ui.refreshable
    def render_passwords():
        process_id = process_id_getter()
        
        if not process_id:
            with ui.card().classes('w-full p-6 text-center'):
                ui.label('💡 Salve o processo primeiro para gerenciar senhas').classes('text-gray-500')
            return
        
        senhas = get_process_passwords(process_id, collection_name)
        
        if not senhas:
            with ui.card().classes('w-full p-6 text-center'):
                ui.label('Nenhuma senha cadastrada').classes('text-gray-400 italic')
            return
        
        for senha in senhas:
            senha_id = senha.get('id')
            senha_show = {'val': False}
            
            with ui.card().classes('w-full p-4 mb-3').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                # Título
                ui.label(senha.get('titulo', 'Sem título')).classes('text-base font-bold text-gray-800 mb-3')
                
                # Usuário
                if senha.get('usuario'):
                    with ui.row().classes('w-full items-center gap-2 mb-2'):
                        ui.icon('person').classes('text-gray-500')
                        ui.label(senha.get('usuario')).classes('text-sm text-gray-700 flex-grow')
                        
                        def copy_usuario(u=senha.get('usuario')):
                            u_json = json.dumps(u)
                            ui.run_javascript(f'navigator.clipboard.writeText({u_json})')
                            ui.notify('Usuário copiado!', type='positive')
                        
                        ui.button(icon='content_copy', on_click=copy_usuario).props('flat dense size=sm').tooltip('Copiar usuário')
                
                # Senha
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    ui.icon('lock').classes('text-gray-500')
                    senha_display_label = ui.label('••••••••').classes('text-sm text-gray-700 font-mono flex-grow')
                    
                    def toggle_senha_show():
                        senha_show['val'] = not senha_show['val']
                        if senha_show['val']:
                            senha_display_label.text = senha.get('senha', '')
                            toggle_senha_btn.props(remove='icon=visibility_off')
                            toggle_senha_btn.props(add='icon=visibility')
                            toggle_senha_btn.tooltip('Ocultar senha')
                        else:
                            senha_display_label.text = '••••••••'
                            toggle_senha_btn.props(remove='icon=visibility')
                            toggle_senha_btn.props(add='icon=visibility_off')
                            toggle_senha_btn.tooltip('Mostrar senha')
                    
                    toggle_senha_btn = ui.button(icon='visibility_off', on_click=toggle_senha_show).props('flat dense size=sm').tooltip('Mostrar senha')
                    
                    def copy_senha(s=senha.get('senha')):
                        s_json = json.dumps(s)
                        ui.run_javascript(f'navigator.clipboard.writeText({s_json})')
                        ui.notify('Senha copiada!', type='positive')
                    
                    ui.button(icon='content_copy', on_click=copy_senha).props('flat dense size=sm').tooltip('Copiar senha')
                
                # Link de acesso
                if senha.get('link_acesso'):
                    with ui.row().classes('w-full items-center gap-2 mb-2'):
                        ui.icon('link').classes('text-gray-500')
                        link_url = senha.get('link_acesso')
                        
                        def open_link(l=link_url):
                            ui.run_javascript(f'window.open("{l}", "_blank")')
                        
                        ui.link(link_url, target='_blank').classes('text-sm text-blue-600 hover:underline flex-grow')
                        ui.button(icon='open_in_new', on_click=lambda l=link_url: open_link(l)).props('flat dense size=sm').tooltip('Abrir link')
                
                # Observações
                if senha.get('observacoes'):
                    ui.label(senha.get('observacoes')).classes('text-xs text-gray-500 mt-2 italic')
                
                # Botões de ação
                with ui.row().classes('w-full justify-end gap-2 mt-3'):
                    ui.button('Editar', icon='edit', on_click=lambda pid=senha_id: open_senha_dialog(pid)).props('flat dense size=sm color=primary')
                    
                    def delete_senha(pid=senha_id):
                        delete_senha_id_ref['val'] = pid
                        delete_senha_dialog.open()
                    
                    ui.button('Excluir', icon='delete', on_click=lambda pid=senha_id: delete_senha(pid)).props('flat dense size=sm color=red')
    
    render_passwords()
    
    return render_passwords.refresh

