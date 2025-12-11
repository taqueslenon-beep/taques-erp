"""
Página de Login
"""
from nicegui import ui, app
from ..auth import login_user, fazer_logout_com_notificacao

PRIMARY_COLOR = '#223631'

@ui.page('/login')
def login_page():
    """Página de login do sistema."""
    
    # Se já está logado, redireciona para home
    if app.storage.user.get('user'):
        ui.navigate.to('/')
        return
    
    ui.colors(primary=PRIMARY_COLOR)
    
    # Container centralizado
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gray-100'):
        
        # Card de login
        with ui.card().classes('w-96 p-8'):
            
            # Logo/Título
            with ui.column().classes('w-full items-center mb-6'):
                ui.label('TAQUES ERP').classes('text-2xl font-bold').style(f'color: {PRIMARY_COLOR}')
                ui.label('Faça login para continuar').classes('text-gray-500 text-sm')
            
            # Mensagem de erro (inicialmente oculta)
            error_label = ui.label('').classes('text-red-500 text-sm text-center w-full hidden')
            
            # Campo de email
            email_input = ui.input(
                label='Email',
                placeholder='seu@email.com'
            ).classes('w-full').props('outlined')
            
            # Campo de senha
            password_input = ui.input(
                label='Senha',
                password=True,
                password_toggle_button=True
            ).classes('w-full').props('outlined')
            
            # Função de login
            async def do_login():
                email = email_input.value
                password = password_input.value
                
                if not email or not password:
                    error_label.text = 'Preencha email e senha'
                    error_label.classes(remove='hidden')
                    return
                
                # Mostra loading
                login_btn.props('loading')
                error_label.classes(add='hidden')
                
                # Tenta fazer login
                result = login_user(email, password)
                
                if result['success']:
                    # Salva usuário na sessão
                    app.storage.user['user'] = result['user']
                    
                    # Carrega workspace persistido do localStorage ou usa padrão
                    from ..gerenciadores.gerenciador_workspace import carregar_workspace_persistido, definir_workspace
                    workspace_id = carregar_workspace_persistido()
                    definir_workspace(workspace_id)
                    
                    ui.notify('Login realizado com sucesso!', type='positive')
                    ui.navigate.to('/')
                else:
                    error_label.text = result['message']
                    error_label.classes(remove='hidden')
                    login_btn.props(remove='loading')
            
            # Botão de login
            login_btn = ui.button(
                'Entrar',
                on_click=do_login
            ).classes('w-full mt-4').style(f'background-color: {PRIMARY_COLOR}')
            
            # Permite login com Enter
            password_input.on('keydown.enter', do_login)
            email_input.on('keydown.enter', lambda _e=None: password_input.run_method('focus'))


@ui.page('/logout')
def logout_page():
    """Página de logout com reinicialização completa."""
    fazer_logout_com_notificacao()
