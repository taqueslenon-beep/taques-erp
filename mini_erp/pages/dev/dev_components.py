"""
Componentes de interface reutilizáveis para o módulo Desenvolvedor.
Componentes UI específicos do painel de desenvolvedor.
"""
from nicegui import ui
from typing import List, Dict, Any


def card_workspaces(workspaces: List[Dict[str, Any]]) -> None:
    """
    Renderiza card com lista de workspaces configurados.
    
    Args:
        workspaces: Lista de dicionários com informações dos workspaces
    """
    with ui.card().classes('w-full mb-4'):
        # Header do card
        with ui.row().classes('w-full items-center justify-between mb-3'):
            ui.label('📦 Workspaces Configurados').classes('text-lg font-bold')
            ui.label(f'Total: {len(workspaces)}').classes('text-sm text-gray-500')
        
        # Lista de workspaces
        if not workspaces:
            ui.label('Nenhum workspace configurado.').classes('text-gray-400 italic py-4')
        else:
            with ui.column().classes('w-full gap-2'):
                for workspace in workspaces:
                    with ui.row().classes('w-full items-center gap-3 p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors'):
                        # Ícone
                        ui.icon(workspace.get('icon', 'folder'), size='md').classes('text-blue-600')
                        
                        # Informações do workspace
                        with ui.column().classes('flex-grow gap-1'):
                            ui.label(workspace.get('nome', 'Sem nome')).classes('text-sm font-semibold')
                            ui.label(f"Prefixo: {workspace.get('prefixo_colecoes', '-')}").classes('text-xs text-gray-500')
                            ui.label(f"Rota: {workspace.get('rota_inicial', '-')}").classes('text-xs text-gray-400')
                        
                        # ID do workspace
                        ui.label(workspace.get('id', '-')).classes('text-xs text-gray-400 font-mono')


def card_usuarios(usuarios: List[Dict[str, Any]]) -> None:
    """
    Renderiza card com tabela de usuários cadastrados.
    
    Args:
        usuarios: Lista de dicionários com informações dos usuários
    """
    with ui.card().classes('w-full mb-4'):
        # Header do card
        with ui.row().classes('w-full items-center justify-between mb-3'):
            ui.label('👥 Usuários Cadastrados').classes('text-lg font-bold')
            ui.label(f'Total: {len(usuarios)}').classes('text-sm text-gray-500')
        
        # Tabela de usuários
        if not usuarios:
            ui.label('Nenhum usuário cadastrado.').classes('text-gray-400 italic py-4')
        else:
            # Define colunas da tabela
            columns = [
                {'name': 'nome', 'label': 'Nome', 'field': 'nome', 'align': 'left', 'sortable': True},
                {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left', 'sortable': True},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
                {'name': 'vinculado', 'label': 'Vinculado', 'field': 'vinculado', 'align': 'center', 'sortable': True},
                {'name': 'nivel_acesso', 'label': 'Nível de Acesso', 'field': 'nivel_acesso', 'align': 'center', 'sortable': True},
                {'name': 'ultimo_login', 'label': 'Último Login', 'field': 'ultimo_login', 'align': 'center', 'sortable': True},
                {'name': 'workspaces', 'label': 'Workspaces', 'field': 'workspaces', 'align': 'left'},
            ]
            
            # Prepara dados da tabela
            rows = []
            for usuario in usuarios:
                # Formata workspaces como string separada por vírgulas
                workspaces_str = ', '.join(usuario.get('workspaces', [])) if usuario.get('workspaces') else '-'
                
                rows.append({
                    'nome': usuario.get('nome_completo', '-'),
                    'email': usuario.get('email', '-'),
                    'status': usuario.get('status', '-'),
                    'vinculado': usuario.get('vinculado', False),
                    'nivel_acesso': usuario.get('nivel_acesso', '-'),
                    'ultimo_login': usuario.get('ultimo_login', '-'),
                    'workspaces': workspaces_str,
                    'sem_firebase': usuario.get('sem_firebase', False),  # Para destacar visualmente
                })
            
            # Cria tabela
            table = ui.table(
                columns=columns,
                rows=rows,
                row_key='nome'
            ).classes('w-full').props('flat dense')
            
            # Slot customizado para status (badge colorido)
            table.add_slot('body-cell-status', '''
                <q-td :props="props">
                    <q-badge 
                        :color="props.value === 'Ativo' ? 'green' : props.value === 'Desativado' ? 'red' : 'orange'"
                        :label="props.value"
                        class="q-mt-xs"
                    />
                </q-td>
            ''')
            
            # Slot customizado para vinculado (ícone ✓ ou ✗)
            table.add_slot('body-cell-vinculado', '''
                <q-td :props="props">
                    <q-icon 
                        :name="props.value ? 'check_circle' : 'cancel'"
                        :color="props.value ? 'green' : 'red'"
                        size="sm"
                    />
                </q-td>
            ''')
            
            # Slot customizado para nível de acesso (badge colorido)
            table.add_slot('body-cell-nivel_acesso', '''
                <q-td :props="props">
                    <q-badge 
                        :color="props.value === 'Desenvolvedor' ? 'amber' : 
                                props.value === 'Usuário Interno' ? 'green' : 
                                props.value === 'Usuário Externo' ? 'blue' : 
                                'grey-6'"
                        :label="props.value"
                        class="q-mt-xs"
                    />
                </q-td>
            ''')
            
            # Adiciona estilo CSS para destacar usuários sem Firebase
            ui.add_head_html('''
                <style>
                    .usuario-sem-firebase {
                        background-color: #fef3c7 !important; /* amarelo claro */
                    }
                    .usuario-sem-firebase:hover {
                        background-color: #fde68a !important; /* amarelo médio */
                    }
                </style>
            ''')
            
            # Aplica classe condicional via JavaScript após renderização da tabela
            # Identifica índices dos usuários sem Firebase
            indices_sem_firebase = [i for i, u in enumerate(usuarios) if u.get('sem_firebase', False)]
            
            if indices_sem_firebase:
                def aplicar_destaque_usuarios_sem_firebase():
                    """Aplica classe CSS para destacar usuários sem Firebase Auth"""
                    ui.run_javascript(f'''
                        setTimeout(function() {{
                            const rows = document.querySelectorAll('.q-table tbody tr');
                            const indices = {indices_sem_firebase};
                            indices.forEach(function(index) {{
                                if (rows[index]) {{
                                    rows[index].classList.add('usuario-sem-firebase');
                                }}
                            }});
                        }}, 200);
                    ''')
                
                ui.timer(0.2, aplicar_destaque_usuarios_sem_firebase, once=True)
            
            # Tooltip explicativo para usuários não vinculados
            with ui.row().classes('w-full mt-2 items-center gap-1'):
                ui.icon('info', size='xs').classes('text-blue-500')
                ui.label('💡 Usuários em amarelo não têm login no Firebase Auth (apenas em usuarios_sistema)').classes('text-xs text-gray-500 italic')









