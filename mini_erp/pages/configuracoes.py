import threading
from datetime import datetime
from nicegui import ui, run, context, events
from ..core import layout
from ..firebase_config import get_db
from ..auth import is_authenticated, get_current_user
from ..storage import fazer_upload_avatar, obter_url_avatar
from firebase_admin import auth
from PIL import Image, ImageDraw
import io
import base64

@ui.page('/configuracoes')
def configuracoes():
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    current_user = get_current_user()
    if not current_user:
        ui.navigate.to('/login')
        return
    
    user_uid = current_user.get('uid')
    user_email = current_user.get('email', '')
    
    if not user_uid:
        ui.notify('Erro: Usuário não identificado. Faça login novamente.', type='negative')
        ui.navigate.to('/login')
        return
    
    with layout('Configurações', breadcrumbs=[('Configurações', None)]):
        # Estado do timer da aba Usuários (isolado para evitar interferência)
        timer_ref = {'timer': None}
        # Referência para função refresh_data (será definida dentro da aba Usuários)
        refresh_data_ref = {'func': None}
        
        with ui.tabs().classes('w-full') as tabs:
            perfil_tab = ui.tab('Perfil')
            geral_tab = ui.tab('Geral')
            usuarios_tab = ui.tab('Usuários')
        
        with ui.tab_panels(tabs, value=perfil_tab).classes('w-full bg-white p-4 rounded shadow-sm') as tab_panels:
            
            # --- PERFIL ---
            with ui.tab_panel(perfil_tab):
                ui.label('Meu Perfil').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full items-start gap-8'):
                    # Coluna do Avatar
                    with ui.column().classes('items-center gap-4'):
                        avatar_img = ui.image('https://cdn.quasar.dev/img/boy-avatar.png').classes('w-32 h-32 rounded-full shadow-md object-cover')
                        
                        # Estado de carregamento do avatar
                        avatar_loading = {'status': False}
                        
                        # Carrega avatar atual
                        async def load_current_avatar():
                            """Carrega o avatar do usuário do Firebase Storage"""
                            try:
                                if not user_uid:
                                    raise ValueError("UID do usuário não disponível")
                                
                                if avatar_loading['status']:
                                    return  # Evita múltiplas chamadas simultâneas
                                
                                avatar_loading['status'] = True
                                
                                url = await run.io_bound(obter_url_avatar, user_uid)
                                if url:
                                    # URL já vem com timestamp do storage.py
                                    avatar_img.source = url
                                else:
                                    # Avatar padrão baseado nas iniciais ou imagem genérica
                                    avatar_img.source = f'https://ui-avatars.com/api/?name={user_email}&background=random&size=200'
                            except Exception as e:
                                print(f"Erro ao carregar avatar: {e}")
                                # Fallback para avatar padrão
                                avatar_img.source = f'https://ui-avatars.com/api/?name={user_email}&background=random&size=200'
                            finally:
                                avatar_loading['status'] = False

                        ui.timer(0.1, load_current_avatar, once=True)

                        # --- EDITOR DE AVATAR ---
                        
                        # Estado do editor (usando dicionário para mutabilidade dentro de closures)
                        avatar_state = {
                            'offset_x': 0,
                            'offset_y': 0,
                            'zoom': 100,
                            'imagem_bytes': None,
                            'dialog': None,
                            'preview_img': None
                        }
                        
                        def processar_preview_sync(img_bytes, offset_x, offset_y, zoom):
                            """Processa a imagem com PIL (executado em thread separada)"""
                            try:
                                if not img_bytes:
                                    return None, None

                                # Abrir imagem
                                img = Image.open(io.BytesIO(img_bytes))
                                
                                # Converte para RGBA para garantir canal alfa
                                if img.mode != 'RGBA':
                                    img = img.convert('RGBA')
                                
                                # Redimensionar se for muito grande para melhorar performance do preview
                                if img.width > 1500 or img.height > 1500:
                                    img.thumbnail((1500, 1500))
                                
                                # Dimensões originais
                                width, height = img.size
                                
                                # Lógica de Zoom:
                                # Zoom 100% = menor dimensão da imagem cabe no círculo de 200px
                                # Zoom > 100% = imagem maior (mostra menos da imagem no círculo)
                                # Zoom < 100% = imagem menor (pode sobrar espaço)
                                
                                # Tamanho base (sem zoom) é o menor lado da imagem
                                min_dim = min(width, height)
                                
                                # Tamanho do crop baseado no zoom
                                # Se zoom = 100, crop_size = min_dim (mostra tudo do menor lado)
                                # Se zoom = 200, crop_size = min_dim / 2 (mostra metade)
                                crop_size = int(min_dim / (zoom / 100))
                                
                                center_x = width // 2
                                center_y = height // 2
                                
                                # Aplica offsets (em pixels da imagem original)
                                # Ajustamos a sensibilidade: offset 1 = 1% do tamanho do crop
                                move_x = int(offset_x * (crop_size / 100) * 2) # Multiplicador de velocidade
                                move_y = int(offset_y * (crop_size / 100) * 2)
                                
                                left = center_x - (crop_size // 2) + move_x
                                top = center_y - (crop_size // 2) + move_y
                                right = left + crop_size
                                bottom = top + crop_size
                                
                                # Faz o crop
                                img_cropped = img.crop((left, top, right, bottom))
                                
                                # Redimensiona para 200x200 (tamanho final)
                                img_resized = img_cropped.resize((200, 200), Image.Resampling.LANCZOS)
                                
                                # Cria máscara circular
                                mask = Image.new('L', (200, 200), 0)
                                draw = ImageDraw.Draw(mask)
                                draw.ellipse((0, 0, 200, 200), fill=255)
                                
                                # Aplica máscara
                                output_img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
                                output_img.paste(img_resized, (0, 0))
                                output_img.putalpha(mask)
                                
                                # Salva em bytes PNG
                                output_buffer = io.BytesIO()
                                output_img.save(output_buffer, format='PNG')
                                output_bytes = output_buffer.getvalue()
                                
                                # Gera base64 para preview
                                img_str = base64.b64encode(output_bytes).decode()
                                return f'data:image/png;base64,{img_str}', output_bytes
                                
                            except Exception as e:
                                print(f"Erro no processamento de imagem: {e}")
                                import traceback
                                traceback.print_exc()
                                return None, None

                        async def update_preview():
                            if not avatar_state['preview_img'] or not avatar_state['imagem_bytes']:
                                return
                            
                            src, _ = await run.cpu_bound(
                                processar_preview_sync, 
                                avatar_state['imagem_bytes'],
                                avatar_state['offset_x'],
                                avatar_state['offset_y'],
                                avatar_state['zoom']
                            )
                            
                            if src:
                                avatar_state['preview_img'].set_source(src)

                        async def mover_foto(direcao):
                            step = 5 # Passo de movimento
                            if direcao == 'cima': avatar_state['offset_y'] -= step
                            elif direcao == 'baixo': avatar_state['offset_y'] += step
                            elif direcao == 'esquerda': avatar_state['offset_x'] -= step
                            elif direcao == 'direita': avatar_state['offset_x'] += step
                            
                            # Atualiza preview
                            await update_preview()

                        async def salvar_avatar_editado():
                            """Salva o avatar editado no Firebase Storage"""
                            if not avatar_state['imagem_bytes']:
                                ui.notify('Nenhuma imagem para salvar.', type='warning')
                                return
                            
                            if not user_uid:
                                ui.notify('Erro: Usuário não identificado.', type='negative')
                                return

                            # Feedback visual: mostra spinner de carregamento
                            loading_notify = ui.notify(
                                'Processando imagem...', 
                                type='info', 
                                spinner=True,
                                position='top',
                                timeout=0  # Não fecha automaticamente
                            )
                            
                            try:
                                # Processa imagem final
                                _, img_bytes = await run.cpu_bound(
                                    processar_preview_sync,
                                    avatar_state['imagem_bytes'],
                                    avatar_state['offset_x'],
                                    avatar_state['offset_y'],
                                    avatar_state['zoom']
                                )
                                
                                if not img_bytes:
                                    loading_notify.dismiss()
                                    ui.notify('Erro ao processar imagem.', type='negative')
                                    return

                                # Fecha dialog antes do upload
                                if avatar_state['dialog']:
                                    avatar_state['dialog'].close()
                                
                                # Atualiza notificação
                                loading_notify.message = 'Salvando no servidor...'
                                
                                # Salva no storage
                                file_obj = io.BytesIO(img_bytes)
                                url = await run.io_bound(fazer_upload_avatar, user_uid, file_obj)
                                
                                loading_notify.dismiss()
                                
                                if url:
                                    # URL já vem com timestamp do storage.py para evitar cache
                                    # Atualiza avatar na página de configurações
                                    avatar_img.source = url
                                    
                                    # Dispara evento customizado para atualizar navbar
                                    # sem recarregar toda a página
                                    ui.run_javascript(f'''
                                        if (window.dispatchEvent) {{
                                            window.dispatchEvent(new CustomEvent('avatar-updated', {{
                                                detail: {{ url: "{url}" }}
                                            }}));
                                        }}
                                    ''')
                                    
                                    ui.notify('Avatar atualizado com sucesso!', type='positive', position='top')
                                else:
                                    ui.notify(
                                        'Erro ao salvar imagem no servidor. '
                                        'Verifique sua conexão e tente novamente.',
                                        type='negative',
                                        position='top'
                                    )
                            except Exception as ex:
                                loading_notify.dismiss()
                                print(f"Erro ao salvar avatar: {ex}")
                                import traceback
                                traceback.print_exc()
                                ui.notify(
                                    f'Erro ao salvar: {str(ex)}',
                                    type='negative',
                                    position='top'
                                )

                        def abrir_editor(imagem_bytes):
                            avatar_state['imagem_bytes'] = imagem_bytes
                            avatar_state['offset_x'] = 0
                            avatar_state['offset_y'] = 0
                            avatar_state['zoom'] = 100
                            
                            with ui.dialog() as dialog, ui.card().classes('p-0 overflow-hidden'):
                                avatar_state['dialog'] = dialog
                                
                                # Cabeçalho
                                with ui.row().classes('w-full bg-primary p-3 items-center justify-between'):
                                    ui.label('Editar Avatar').classes('text-white font-bold text-lg')
                                    ui.button(icon='close', on_click=dialog.close).props('flat round dense text-color=white')
                                
                                with ui.row().classes('p-6 gap-8 items-start'):
                                    # Coluna Controles (Esquerda)
                                    with ui.column().classes('gap-4 min-w-[200px]'):
                                        ui.label('Ajustar Posição').classes('font-bold text-gray-700')
                                        
                                        # Grid de setas
                                        with ui.element('div').classes('grid grid-cols-3 gap-2 w-32 mx-auto'):
                                            ui.element('div') # Espaço vazio
                                            ui.button(icon='keyboard_arrow_up', on_click=lambda: mover_foto('cima')).props('round dense color=primary')
                                            ui.element('div') # Espaço vazio
                                            
                                            ui.button(icon='keyboard_arrow_left', on_click=lambda: mover_foto('esquerda')).props('round dense color=primary')
                                            ui.element('div') # Centro (pode ser um reset se quiser)
                                            ui.button(icon='keyboard_arrow_right', on_click=lambda: mover_foto('direita')).props('round dense color=primary')
                                            
                                            ui.element('div') # Espaço vazio
                                            ui.button(icon='keyboard_arrow_down', on_click=lambda: mover_foto('baixo')).props('round dense color=primary')
                                            ui.element('div') # Espaço vazio
                                        
                                        ui.separator().classes('my-2')
                                        
                                        ui.label('Zoom').classes('font-bold text-gray-700')
                                        
                                        # Slider de Zoom
                                        async def on_zoom_change(e):
                                            avatar_state['zoom'] = e.value
                                            await update_preview()

                                        ui.slider(min=50, max=150, value=100, step=5, on_change=on_zoom_change).props('label-always')
                                        ui.label('50% - 150%').classes('text-xs text-gray-400 text-center w-full')

                                    # Coluna Preview (Direita)
                                    with ui.column().classes('items-center gap-2'):
                                        ui.label('Preview').classes('font-bold text-gray-700')
                                        
                                        # Container do preview com fundo xadrez para ver transparência
                                        with ui.element('div').style('width: 200px; height: 200px; background-image: linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px; border-radius: 50%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'):
                                            avatar_state['preview_img'] = ui.image().style('width: 200px; height: 200px; border-radius: 50%; object-fit: cover;')
                                
                                # Rodapé
                                with ui.row().classes('w-full justify-end gap-2 p-4 bg-gray-50'):
                                    ui.button('Cancelar', on_click=dialog.close).props('flat text-color=grey')
                                    ui.button('Salvar Avatar', on_click=salvar_avatar_editado).props('color=primary icon=save')
                            
                            dialog.open()
                            # Gera preview inicial
                            # Precisamos esperar o dialog renderizar o image? Não necessariamente.
                            # Executa update inicial
                            async def _init():
                                await update_preview()
                            ui.timer(0.1, _init, once=True)

                        # Handler de Upload Inicial
                        async def handle_upload(e: events.UploadEventArguments):
                            """Handler para upload de avatar usando estrutura correta do NiceGUI."""
                            try:
                                print(f"[UPLOAD] Iniciando - Nome: {e.name}, Tipo: {e.type}")
                                
                                # Lê os bytes do arquivo usando e.content.read()
                                img_bytes = e.content.read()
                                
                                print(f"[UPLOAD] Bytes lidos: {len(img_bytes)}")
                                
                                # Validação de tamanho (5MB)
                                if len(img_bytes) > 5 * 1024 * 1024:
                                    ui.notify('Arquivo muito grande! Máximo 5MB.', type='warning')
                                    upload_component.reset()
                                    return
                                
                                if len(img_bytes) == 0:
                                    ui.notify('Arquivo vazio ou inválido.', type='warning')
                                    upload_component.reset()
                                    return
                                
                                # Validação de tipo de arquivo
                                file_name = e.name or ''
                                if file_name:
                                    ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
                                    if ext and ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                        ui.notify('Formato não suportado! Use JPG, PNG, GIF ou WEBP.', type='negative')
                                        upload_component.reset()
                                        return
                                
                                # Valida se é realmente uma imagem válida
                                try:
                                    from PIL import Image
                                    img_test = Image.open(io.BytesIO(img_bytes))
                                    img_test.verify()
                                    print(f"[UPLOAD] Imagem válida: {img_test.format}")
                                except Exception as img_err:
                                    ui.notify('Arquivo não é uma imagem válida.', type='negative')
                                    print(f"[UPLOAD] Erro validação: {img_err}")
                                    upload_component.reset()
                                    return
                                
                                # Abre editor
                                print(f"[UPLOAD] Abrindo editor de avatar...")
                                abrir_editor(img_bytes)
                                
                            except Exception as ex:
                                print(f"[UPLOAD] Erro geral: {ex}")
                                import traceback
                                traceback.print_exc()
                                ui.notify(f'Erro ao processar arquivo: {str(ex)}', type='negative')
                                upload_component.reset()

                        upload_component = ui.upload(
                            label='Alterar Foto', 
                            auto_upload=True,
                            on_upload=handle_upload,
                            max_files=1
                        ).props('accept="image/*" flat color=primary').classes('w-full max-w-xs')
                        
                        ui.label('Máximo 5MB (JPG/PNG)').classes('text-xs text-gray-400')

                    # Coluna de Dados
                    with ui.column().classes('flex-grow max-w-md gap-4'):
                        ui.input('Email', value=user_email).props('readonly').classes('w-full')
                        
                        # Mostrar claims/role se disponível
                        role = 'Usuário'
                        try:
                            # Busca dados frescos do user para ver claims
                            # (Simplificado, assumindo que o token tem info ou carregamos do banco)
                            pass
                        except:
                            pass
                        
                        ui.input('Função', value=role).props('readonly').classes('w-full')
                        
                        ui.label('Para alterar senha ou email, contate o administrador.').classes('text-sm text-gray-500 italic mt-4')

            # --- GERAL ---
            with ui.tab_panel(geral_tab):
                ui.label('Configurações Gerais do Sistema').classes('text-lg font-bold mb-2')
                ui.switch('Modo Escuro (Em breve)')
                ui.switch('Notificações por Email', value=True)
            
            # --- USUÁRIOS ---
            with ui.tab_panel(usuarios_tab):
                
                # Helper para formatar datas
                def format_date(dt_or_ts):
                    if not dt_or_ts:
                        return '-'
                    try:
                        # Se for número (timestamp em ms)
                        if isinstance(dt_or_ts, (int, float)):
                            # Firebase timestamps são em ms
                            dt = datetime.fromtimestamp(dt_or_ts / 1000)
                            return dt.strftime('%d/%m/%Y %H:%M')
                        # Se já for datetime
                        if isinstance(dt_or_ts, datetime):
                            return dt_or_ts.strftime('%d/%m/%Y %H:%M')
                        return str(dt_or_ts)
                    except Exception:
                        return '-'

                # Função para listar usuários do Firebase Authentication
                def listar_usuarios_firebase():
                    """Lista todos os usuários do Firebase Authentication"""
                    try:
                        usuarios = []
                        page = auth.list_users()
                        
                        while page:
                            for user in page.users:
                                custom_claims = user.custom_claims or {}
                                
                                # Determina função baseada em claims
                                role = 'Usuário'
                                if custom_claims.get('admin') or custom_claims.get('role') == 'admin':
                                    role = 'Administrador'
                                elif custom_claims.get('role'):
                                    role = custom_claims.get('role').capitalize()

                                usuarios.append({
                                    'email': user.email,
                                    'uid': user.uid,
                                    'criacao': format_date(user.user_metadata.creation_timestamp),
                                    'ultimo_login': format_date(user.user_metadata.last_sign_in_timestamp),
                                    'role': role,
                                    'status': 'Inativo' if user.disabled else 'Ativo',
                                    'raw_ts': user.user_metadata.last_sign_in_timestamp or 0 # Para ordenação
                                })
                            page = page.get_next_page()
                        
                        # Ordena por último login (mais recente primeiro)
                        usuarios.sort(key=lambda x: x['raw_ts'], reverse=True)
                        return usuarios
                    except Exception as e:
                        print(f"Erro ao listar usuários: {e}")
                        return []

                # Interface
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Usuários Registrados (Firebase Auth)').classes('text-lg font-bold text-primary')
                    
                    refresh_btn = ui.button('Atualizar', icon='refresh').classes('bg-primary text-white')
                
                # Definição das colunas
                columns = [
                    {'name': 'email', 'label': 'Email / Usuário', 'field': 'email', 'align': 'left', 'sortable': True},
                    {'name': 'role', 'label': 'Função', 'field': 'role', 'align': 'left', 'sortable': True},
                    {'name': 'criacao', 'label': 'Data Criação', 'field': 'criacao', 'align': 'left', 'sortable': True},
                    {'name': 'ultimo_login', 'label': 'Último Login', 'field': 'ultimo_login', 'align': 'left', 'sortable': True},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'left', 'sortable': True},
                ]
                
                # Tabela e Loading
                users_table = ui.table(columns=columns, rows=[], row_key='uid').classes('w-full').props('flat')
                
                loading_div = ui.element('div').classes('w-full flex justify-center py-8')
                with loading_div:
                    ui.spinner('dots', size='3em', color='primary')
                    ui.label('Sincronizando com Firebase...').classes('ml-3 text-gray-500')
                
                empty_div = ui.element('div').classes('w-full text-center py-8 hidden')
                with empty_div:
                    ui.icon('person_off', size='3em', color='grey-4')
                    ui.label('Nenhum usuário encontrado').classes('text-gray-400 mt-2')

                async def refresh_data():
                    # Só atualiza se a aba Usuários estiver ativa
                    # Verifica se o timer ainda está ativo (evita chamadas após mudança de aba)
                    if timer_ref['timer'] and not timer_ref['timer'].active:
                        return
                    
                    # UI State: Loading
                    users_table.visible = False
                    empty_div.classes('hidden')
                    loading_div.set_visibility(True)
                    refresh_btn.disable()
                    
                    # Fetch Data (in background)
                    rows = await run.io_bound(listar_usuarios_firebase)
                    
                    # Verifica novamente se ainda está na aba Usuários
                    if timer_ref['timer'] and not timer_ref['timer'].active:
                        refresh_btn.enable()
                        return
                    
                    # UI State: Show Data
                    users_table.rows = rows
                    loading_div.set_visibility(False)
                    
                    if not rows:
                        empty_div.classes(remove='hidden')
                        users_table.visible = False
                    else:
                        users_table.visible = True
                    
                    refresh_btn.enable()
                    ui.notify('Lista de usuários atualizada!', type='positive', position='top')

                # Conecta botão
                refresh_btn.on_click(refresh_data)
                
                # Armazena referência para refresh_data no escopo externo
                refresh_data_ref['func'] = refresh_data
                
                # Cria timer para atualização automática (5 min)
                # Timer é criado desativado e será ativado apenas quando a aba Usuários estiver visível
                timer_ref['timer'] = ui.timer(300, refresh_data)
                timer_ref['timer'].deactivate()  # Inicia desativado
                
                # Carga inicial apenas se a aba Usuários for a aba padrão
                # Como a aba padrão é Perfil, não fazemos carga inicial automática
                # O usuário pode clicar no botão "Atualizar" ou mudar para a aba Usuários
            
            # Função para gerenciar timer baseado na aba ativa
            # Definida após a criação do timer para ter acesso a ele
            def on_tab_change(e):
                """Ativa/desativa timer da aba Usuários conforme a aba selecionada"""
                # O valor do evento é o tab selecionado
                if e.value == usuarios_tab:
                    # Ativa timer da aba usuários
                    if timer_ref['timer']:
                        timer_ref['timer'].activate()
                        print("[TIMER] Timer da aba Usuários ativado")
                        # Faz carga inicial quando entrar na aba pela primeira vez (se ainda não carregou)
                        if refresh_data_ref['func']:
                            # Verifica se precisa carregar dados iniciais
                            # Usa um timer único para não bloquear a UI
                            async def carga_inicial():
                                if refresh_data_ref['func']:
                                    await refresh_data_ref['func']()
                            ui.timer(0.1, carga_inicial, once=True)
                else:
                    # Desativa timer quando sair da aba
                    if timer_ref['timer']:
                        timer_ref['timer'].deactivate()
                        print("[TIMER] Timer da aba Usuários desativado")
            
            # Conecta evento de mudança de aba
            tabs.on('update:model-value', on_tab_change)
