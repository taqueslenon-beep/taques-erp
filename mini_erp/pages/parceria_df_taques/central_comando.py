"""
Página Central de Comando do workspace "Parceria - DF/Taques".
Módulo exclusivo para gestão da parceria DF Projetos + Taques Advogados.
"""
from nicegui import ui
from ...core import layout
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace

# Ícones SVG oficiais do sistema (copiados de mini_erp/pages/visao_geral/casos/main.py)
SLACK_ICON = '''
<svg width="24" height="24" viewBox="0 0 54 54" xmlns="http://www.w3.org/2000/svg">
    <g fill="none">
        <path d="M19.712.133a5.381 5.381 0 0 0-5.376 5.387 5.381 5.381 0 0 0 5.376 5.386h5.376V5.52A5.381 5.381 0 0 0 19.712.133m0 14.365H5.376A5.381 5.381 0 0 0 0 19.884a5.381 5.381 0 0 0 5.376 5.387h14.336a5.381 5.381 0 0 0 5.376-5.387 5.381 5.381 0 0 0-5.376-5.386" fill="#36c5f0"/>
        <path d="M53.76 19.884a5.381 5.381 0 0 0-5.376-5.386 5.381 5.381 0 0 0-5.376 5.386v5.387h5.376a5.381 5.381 0 0 0 5.376-5.387m-14.336 0V5.52A5.381 5.381 0 0 0 34.048.133a5.381 5.381 0 0 0-5.376 5.387v14.364a5.381 5.381 0 0 0 5.376 5.387 5.381 5.381 0 0 0 5.376-5.387" fill="#2eb67d"/>
        <path d="M34.048 54a5.381 5.381 0 0 0 5.376-5.387 5.381 5.381 0 0 0-5.376-5.386h-5.376v5.386A5.381 5.381 0 0 0 34.048 54m0-14.365h14.336a5.381 5.381 0 0 0 5.376-5.386 5.381 5.381 0 0 0-5.376-5.387H34.048a5.381 5.381 0 0 0-5.376 5.387 5.381 5.381 0 0 0 5.376 5.386" fill="#ecb22e"/>
        <path d="M0 34.249a5.381 5.381 0 0 0 5.376 5.386 5.381 5.381 0 0 0 5.376-5.386v-5.387H5.376A5.381 5.381 0 0 0 0 34.25m14.336 0v14.364a5.381 5.381 0 0 0 5.376 5.387 5.381 5.381 0 0 0 5.376-5.387V34.25a5.381 5.381 0 0 0-5.376-5.387 5.381 5.381 0 0 0-5.376 5.387" fill="#e01e5a"/>
    </g>
</svg>
'''

GOOGLE_DRIVE_ICON = '''
<svg width="24" height="24" viewBox="0 0 87.3 78" xmlns="http://www.w3.org/2000/svg">
    <path d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z" fill="#0066da"/>
    <path d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44a9.06 9.06 0 0 0 -1.2 4.5h27.5z" fill="#00ac47"/>
    <path d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z" fill="#ea4335"/>
    <path d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z" fill="#00832d"/>
    <path d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684fc"/>
    <path d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#ffba00"/>
</svg>
'''


@ui.page('/parceria-df-taques/central-comando')
def central_comando():
    """
    Página principal da Central de Comando do workspace Parceria - DF/Taques.
    """
    # Verifica autenticação
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Garante que o workspace está definido na sessão
    definir_workspace('parceria_df_taques')
    
    # Renderiza página com layout padrão
    with layout('Central de Comando', breadcrumbs=[('Parceria - DF/Taques', None), ('Central de Comando', None)]):
        # Descrição discreta em uma linha com negrito
        with ui.row().classes('gap-1 flex-wrap mb-4'):
            ui.label('Área restrita à gestão.').classes('text-sm text-gray-500')
            ui.label('Funcionários e estagiários não têm acesso.').classes('text-sm text-gray-500 font-bold')
        
        # Separador
        ui.separator().classes('my-4')
        
        # Título e descrição da seção (espaçamento mínimo)
        with ui.column().classes('gap-0 mb-4'):
            ui.label('Acesso rápido').classes('text-lg font-medium text-gray-800')
            ui.label('Clique nos ícones abaixo para acessar rapidamente recursos relacionados à parceria.').classes('text-sm text-gray-500')
        
        # Lista de links alinhados (sem card)
        with ui.column().classes('w-full gap-4 max-w-2xl'):
            # Item 1: Slack - Assuntos gerais da gestão
            with ui.row().classes('items-center gap-3 p-2 hover:bg-gray-50 rounded transition-colors cursor-pointer') as item_assuntos:
                # Container do ícone com tamanho fixo
                with ui.element('div').classes('w-8 h-8 flex items-center justify-center flex-shrink-0'):
                    ui.html(SLACK_ICON, sanitize=False)
                
                # Conteúdo (título + descrição)
                with ui.column().classes('gap-0 flex-1'):
                    ui.label('Assuntos gerais da gestão').classes('font-medium text-gray-800')
                    ui.label('Canal do Slack para tratar de assuntos restritos à gestão da parceria. Não utilize para financeiro nem para casos específicos.').classes('text-sm text-gray-500')
            
            # Registrar evento de clique após criar todos os elementos
            item_assuntos.on('click', lambda: ui.run_javascript('window.open("https://taquesadvogados.slack.com/archives/C09PX3AK6UV", "_blank")'))
            
            # Item 2: Slack - Financeiro
            with ui.row().classes('items-center gap-3 p-2 hover:bg-gray-50 rounded transition-colors cursor-pointer') as item_financeiro:
                # Container do ícone com tamanho fixo
                with ui.element('div').classes('w-8 h-8 flex items-center justify-center flex-shrink-0'):
                    ui.html(SLACK_ICON, sanitize=False)
                
                # Conteúdo (título + descrição)
                with ui.column().classes('gap-0 flex-1'):
                    ui.label('Financeiro').classes('font-medium text-gray-800')
                    ui.label('Canal do Slack para notas, comprovantes e questões relacionadas ao financeiro da parceria.').classes('text-sm text-gray-500')
            
            # Registrar evento de clique após criar todos os elementos
            item_financeiro.on('click', lambda: ui.run_javascript('window.open("https://taquesadvogados.slack.com/archives/C09851NBP7Y", "_blank")'))
            
            # Item 3: Google Drive - Contratos de honorários
            with ui.row().classes('items-center gap-3 p-2 hover:bg-gray-50 rounded transition-colors cursor-pointer') as item_drive:
                # Container do ícone com tamanho fixo
                with ui.element('div').classes('w-8 h-8 flex items-center justify-center flex-shrink-0'):
                    ui.html(GOOGLE_DRIVE_ICON, sanitize=False)
                
                # Conteúdo (título + descrição)
                with ui.column().classes('gap-0 flex-1'):
                    ui.label('Contratos de honorários').classes('font-medium text-gray-800')
                    ui.label('Pasta do Google Drive com os contratos de honorários firmados em parceria por DF e Taques.').classes('text-sm text-gray-500')
            
            # Registrar evento de clique após criar todos os elementos
            item_drive.on('click', lambda: ui.run_javascript('window.open("https://drive.google.com/drive/u/1/folders/19ckrqwvGZL4hK6hlVvdAl1iv1O4nqA6S", "_blank")'))
        
        # Rodapé discreto
        with ui.row().classes('w-full mt-6'):
            ui.label('Mais funcionalidades em breve.').classes('text-xs text-gray-400 italic')


@ui.page('/parceria-df-taques/painel')
def painel_redirect():
    """
    Rota alternativa que redireciona para a Central de Comando.
    """
    ui.navigate.to('/parceria-df-taques/central-comando')









