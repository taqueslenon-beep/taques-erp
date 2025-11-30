"""
Exemplo de Mapa Mental para Visualização de Hierarquia de Processos
====================================================================

Este é um exemplo ISOLADO que demonstra como um mapa mental poderia
funcionar no TAQUES ERP para visualizar a hierarquia de processos.

Para testar: python3 mapa_mental_exemplo.py
Acesse: http://localhost:8090

Este arquivo NÃO modifica nenhum código existente do sistema.
"""

from nicegui import ui

# Dados de exemplo simulando processos com hierarquia
PROCESSOS_EXEMPLO = {
    'id': 'inquerito-civil-2013',
    'title': 'INQUÉRITO CIVIL 2013 - CONTAGEM 2008',
    'status': 'Em andamento',
    'area': 'Cível',
    'children': [
        {
            'id': 'teste-filho-1',
            'title': 'TESTE - CRIAÇÃO DE PROCESSO FILHO',
            'status': 'Em andamento',
            'area': 'Criminal',
            'children': [
                {
                    'id': 'neto-1',
                    'title': 'RECURSO DO PROCESSO FILHO',
                    'status': 'Concluído',
                    'area': 'Criminal',
                    'children': []
                }
            ]
        },
        {
            'id': 'teste-filho-2',
            'title': 'EMBARGO - INQUÉRITO CIVIL',
            'status': 'Concluído',
            'area': 'Cível',
            'children': []
        },
        {
            'id': 'teste-filho-3',
            'title': 'AGRAVO DE INSTRUMENTO',
            'status': 'Em andamento',
            'area': 'Cível',
            'children': [
                {
                    'id': 'bisneto-1',
                    'title': 'RECURSO DO AGRAVO',
                    'status': 'Em andamento',
                    'area': 'Cível',
                    'children': []
                }
            ]
        }
    ]
}


def create_mindmap_page():
    """Cria a página com o mapa mental."""
    
    # Cores por nível de profundidade
    CORES_NIVEL = {
        0: {'bg': '#223631', 'border': '#223631', 'text': '#ffffff'},  # Raiz - verde escuro
        1: {'bg': '#4a7c59', 'border': '#4a7c59', 'text': '#ffffff'},  # Filho - verde médio
        2: {'bg': '#7cb890', 'border': '#7cb890', 'text': '#223631'},  # Neto - verde claro
        3: {'bg': '#a8d5ba', 'border': '#a8d5ba', 'text': '#223631'},  # Bisneto - verde muito claro
    }
    
    # Cores por status
    CORES_STATUS = {
        'Em andamento': '#fbbf24',  # Amarelo
        'Concluído': '#22c55e',      # Verde
        'Arquivado': '#9ca3af',      # Cinza
    }
    
    with ui.column().classes('w-full items-center p-8'):
        ui.label('🗺️ Mapa Mental de Processos').classes('text-3xl font-bold mb-2').style('color: #223631;')
        ui.label('Visualização hierárquica do processo e seus vínculos').classes('text-gray-600 mb-8')
        
        # Container principal do mapa mental
        with ui.card().classes('w-full max-w-6xl p-8').style('background: #f8faf9; border-radius: 16px;'):
            
            # Legenda
            with ui.row().classes('w-full justify-center gap-6 mb-8'):
                ui.label('Legenda:').classes('font-bold')
                with ui.row().classes('gap-4'):
                    for nivel, label in [(0, 'Processo Raiz'), (1, 'Filho'), (2, 'Neto'), (3, 'Bisneto')]:
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-4 h-4 rounded').style(f"background: {CORES_NIVEL[nivel]['bg']};")
                            ui.label(label).classes('text-sm')
                
                ui.label('|').classes('text-gray-300')
                
                with ui.row().classes('gap-4'):
                    for status, cor in CORES_STATUS.items():
                        with ui.row().classes('items-center gap-1'):
                            ui.element('div').classes('w-3 h-3 rounded-full').style(f"background: {cor};")
                            ui.label(status).classes('text-sm')
            
            # Mapa mental usando CSS Grid
            with ui.element('div').classes('w-full').style('''
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
            '''):
                
                def render_node(processo, nivel=0):
                    """Renderiza um nó do mapa mental recursivamente."""
                    cores = CORES_NIVEL.get(nivel, CORES_NIVEL[3])
                    status_cor = CORES_STATUS.get(processo['status'], '#9ca3af')
                    
                    with ui.column().classes('items-center'):
                        # Card do processo
                        with ui.card().classes('p-4 cursor-pointer transition-all').style(f'''
                            background: {cores['bg']};
                            border: 3px solid {cores['border']};
                            border-radius: 12px;
                            min-width: 200px;
                            max-width: 280px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        ''').on('click', lambda p=processo: ui.notify(f"Clicou em: {p['title'][:30]}...")):
                            
                            # Título
                            ui.label(processo['title']).classes('text-sm font-bold text-center').style(f'''
                                color: {cores['text']};
                                line-height: 1.3;
                            ''')
                            
                            # Status e Área
                            with ui.row().classes('w-full justify-center gap-2 mt-2'):
                                # Badge de status
                                ui.label(processo['status']).classes('text-xs px-2 py-1 rounded-full').style(f'''
                                    background: {status_cor};
                                    color: #ffffff;
                                    font-weight: 500;
                                ''')
                                # Badge de área
                                ui.label(processo['area']).classes('text-xs px-2 py-1 rounded-full').style(f'''
                                    background: rgba(255,255,255,0.2);
                                    color: {cores['text']};
                                    border: 1px solid {cores['text']}40;
                                ''')
                        
                        # Se tem filhos, renderiza conexões e filhos
                        if processo.get('children'):
                            # Linha vertical de conexão
                            ui.element('div').style('''
                                width: 3px;
                                height: 30px;
                                background: linear-gradient(to bottom, #223631, #7cb890);
                                border-radius: 2px;
                            ''')
                            
                            # Linha horizontal de conexão (se mais de 1 filho)
                            if len(processo['children']) > 1:
                                ui.element('div').style(f'''
                                    width: {min(len(processo['children']) * 200, 800)}px;
                                    height: 3px;
                                    background: linear-gradient(to right, #7cb890, #223631, #7cb890);
                                    border-radius: 2px;
                                ''')
                            
                            # Container dos filhos
                            with ui.row().classes('justify-center gap-4 flex-wrap'):
                                for child in processo['children']:
                                    with ui.column().classes('items-center'):
                                        # Linha vertical para cada filho
                                        ui.element('div').style('''
                                            width: 3px;
                                            height: 20px;
                                            background: #7cb890;
                                            border-radius: 2px;
                                        ''')
                                        # Renderiza o filho recursivamente
                                        render_node(child, nivel + 1)
                
                # Renderiza a árvore a partir da raiz
                render_node(PROCESSOS_EXEMPLO)
        
        # Informações adicionais
        with ui.card().classes('w-full max-w-6xl mt-8 p-6').style('background: #ffffff; border: 1px solid #e5e7eb;'):
            ui.label('ℹ️ Como usar este mapa mental:').classes('font-bold text-lg mb-3').style('color: #223631;')
            
            with ui.column().classes('gap-2'):
                ui.label('• Clique em qualquer processo para ver detalhes').classes('text-gray-600')
                ui.label('• Cores indicam o nível hierárquico (raiz → filho → neto → bisneto)').classes('text-gray-600')
                ui.label('• Badges coloridos mostram o status atual do processo').classes('text-gray-600')
                ui.label('• As linhas conectam processos pai aos seus filhos').classes('text-gray-600')
        
        # Botão para voltar
        ui.button('← Voltar para a Lista', on_click=lambda: ui.notify('Voltaria para a lista de processos')).classes('mt-6').props('outline')


# Página principal
@ui.page('/')
def main():
    ui.query('body').style('background: #f0f2f1;')
    create_mindmap_page()


# Rodar o servidor
if __name__ in {"__main__", "__mp_main__"}:
    print("\n" + "="*60)
    print("🗺️  EXEMPLO DE MAPA MENTAL - TAQUES ERP")
    print("="*60)
    print("Este é um exemplo isolado que NÃO modifica seu código.")
    print("\n🌐 Acesse: http://localhost:8090")
    print("💡 Pressione Ctrl+C para parar\n")
    print("="*60 + "\n")
    
    ui.run(port=8090, title='Mapa Mental - Exemplo', reload=False)
