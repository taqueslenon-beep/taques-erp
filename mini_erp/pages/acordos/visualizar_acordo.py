"""
visualizar_acordo.py - Página de visualização individual de acordos.

Exibe detalhes completos de um acordo, incluindo:
- Barra numérica no topo
- Informações do caso vinculado
- Demais informações do acordo
"""

from typing import Optional, Dict, Any
from nicegui import ui
from ...core import layout, get_case_by_slug, get_display_name
from ...auth import is_authenticated
from .database import buscar_acordo_por_id
from .acordos_page import formatar_data, obter_cor_status


def formatar_caso(caso: dict) -> str:
    """Formata caso para exibição."""
    title = caso.get('title', 'Sem título')
    number = caso.get('number', '')
    if number:
        return f"{title} ({number})"
    return title


@ui.page('/acordos/{acordo_id}')
def visualizar_acordo(acordo_id: str):
    """Página de visualização individual de acordo."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Buscar dados do acordo
    acordo = buscar_acordo_por_id(acordo_id)
    
    if not acordo:
        with layout('Acordo não encontrado', breadcrumbs=[('Acordos', '/acordos'), ('Visualizar', None)]):
            with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                ui.icon('error', size='48px').classes('text-red-400 mb-4')
                ui.label('Acordo não encontrado').classes(
                    'text-red-600 text-lg font-medium mb-2'
                )
                ui.label('O acordo solicitado não existe ou foi removido.').classes(
                    'text-sm text-gray-500 text-center mb-4'
                )
                ui.button('Voltar para Acordos', on_click=lambda: ui.navigate.to('/acordos')).props(
                    'color=primary'
                )
        return
    
    # Extrair dados do acordo
    titulo = acordo.get('titulo') or acordo.get('title') or 'Sem título'
    numero = acordo.get('numero') or acordo.get('number') or acordo.get('_id', '')[:8]
    data_celebracao = acordo.get('data_celebracao') or acordo.get('data_assinatura') or acordo.get('data')
    status = acordo.get('status') or 'Sem status'
    casos = acordo.get('casos', [])
    processos = acordo.get('processos', [])
    clausulas = acordo.get('clausulas', [])
    
    # Buscar informações do primeiro caso vinculado (se houver)
    caso_vinculado = None
    caso_id_para_link = None
    
    # Verificar se há caso_id direto no acordo
    caso_id_direto = acordo.get('caso_id') or acordo.get('case_id')
    
    if casos:
        primeiro_caso = casos[0] if isinstance(casos, list) else casos
        
        # Se o caso já vem completo (com título, number, etc), usar diretamente
        if isinstance(primeiro_caso, dict) and primeiro_caso.get('title'):
            caso_vinculado = primeiro_caso
            caso_id_para_link = primeiro_caso.get('_id') or primeiro_caso.get('id') or primeiro_caso.get('slug')
        else:
            # Caso contrário, buscar pelo ID
            caso_id = primeiro_caso.get('_id') if isinstance(primeiro_caso, dict) else str(primeiro_caso)
            caso_id = caso_id or caso_id_direto
            
            if caso_id:
                caso_id_para_link = caso_id
                # Buscar caso completo no Firestore
                caso_vinculado = get_case_by_slug(caso_id)
                if not caso_vinculado:
                    # Se não encontrou por slug, tentar buscar na lista de casos
                    from ...core import get_cases_list
                    casos_list = get_cases_list()
                    for caso_item in casos_list:
                        if (caso_item.get('_id') == caso_id or 
                            caso_item.get('slug') == caso_id):
                            caso_vinculado = caso_item
                            break
    elif caso_id_direto:
        # Se não há lista de casos mas há caso_id direto
        caso_id_para_link = caso_id_direto
        caso_vinculado = get_case_by_slug(caso_id_direto)
        if not caso_vinculado:
            from ...core import get_cases_list
            casos_list = get_cases_list()
            for caso_item in casos_list:
                if (caso_item.get('_id') == caso_id_direto or 
                    caso_item.get('slug') == caso_id_direto):
                    caso_vinculado = caso_item
                    break
    
    with layout(f'Acordo: {titulo[:50]}', breadcrumbs=[('Acordos', '/acordos'), ('Visualizar', None)]):
        
        # Função para abrir edição (definida antes para poder ser usada em múltiplos lugares)
        def abrir_edicao():
            """Abre modal de edição."""
            from .modais import render_acordo_dialog
            from .database import salvar_acordo, invalidar_cache_acordos
            
            def on_success(acordo_data):
                try:
                    acordo_id_save = acordo_data.get('_id') or acordo_id
                    salvar_acordo(acordo_data, acordo_id=acordo_id_save)
                    invalidar_cache_acordos()
                    ui.notify('Acordo atualizado!', type='positive')
                    # Recarregar página
                    ui.navigate.to(f'/acordos/{acordo_id}')
                except Exception as e:
                    print(f"[ERROR] Erro ao salvar: {e}")
                    ui.notify('Erro ao salvar acordo', type='negative')
            
            dialog, open_dialog = render_acordo_dialog(
                on_success=on_success,
                acordo_inicial=acordo
            )
            open_dialog()
        
        # ===== BARRA NUMÉRICA (antes do título) =====
        with ui.row().classes('w-full mb-4 items-center gap-3'):
            # Badge numérico destacado
            ui.badge(
                f'#{numero}' if numero else f'ID: {acordo_id[:8]}',
                color='primary'
            ).props('outlined').classes('text-lg font-bold px-4 py-2')
            
            # Separador visual
            ui.separator().props('vertical').classes('h-8')
            
            # Status do acordo (mesmo padrão do modal de processos)
            status_style = obter_cor_status(status)
            with ui.html(f'''
                <q-badge 
                    style="{status_style} border: 1px solid rgba(0,0,0,0.1);"
                    class="px-3 py-1 text-sm font-medium"
                >
                    {status}
                </q-badge>
            '''):
                pass
        
        # ===== TÍTULO PRINCIPAL =====
        with ui.card().classes('w-full p-6 mb-4').style('border: 1px solid #e5e7eb;'):
            # Título clicável
            ui.button(
                titulo,
                on_click=abrir_edicao
            ).props('flat').classes('text-2xl font-bold text-gray-800 mb-2 p-0 text-left justify-start').style(
                'cursor: pointer; text-decoration: none;'
            ).tooltip('Clique para editar o acordo')
            
            if data_celebracao:
                data_formatada = formatar_data(data_celebracao)
                with ui.row().classes('items-center gap-2 mt-2'):
                    ui.icon('event', size='20px').classes('text-gray-500')
                    ui.label(f'Data de Celebração: {data_formatada}').classes('text-sm text-gray-600')
        
        # ===== CASO VINCULADO =====
        with ui.card().classes('w-full p-6 mb-4').style('border: 1px solid #e5e7eb;'):
            ui.label('🔗 Caso Vinculado').classes('text-lg font-bold text-gray-800 mb-4')
            
            if caso_vinculado:
                # Número do processo/caso
                caso_number = caso_vinculado.get('number', '')
                caso_title = caso_vinculado.get('title', 'Sem título')
                caso_status = caso_vinculado.get('status', 'Sem status')
                caso_slug = caso_vinculado.get('slug') or caso_vinculado.get('_id')
                
                with ui.column().classes('w-full gap-3'):
                    # Número do processo
                    if caso_number:
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('description', size='20px').classes('text-gray-500')
                            ui.label(f'Número: {caso_number}').classes('text-sm font-medium text-gray-700')
                    
                    # Título do caso
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('folder', size='20px').classes('text-gray-500')
                        ui.label(f'Título: {caso_title}').classes('text-sm font-medium text-gray-700')
                    
                    # Status do caso
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('info', size='20px').classes('text-gray-500')
                        ui.label(f'Status: {caso_status}').classes('text-sm font-medium text-gray-700')
                    
                    # Link para abrir o caso
                    caso_link_id = caso_id_para_link or caso_slug
                    if caso_link_id:
                        def abrir_caso():
                            """Navega para a página do caso."""
                            ui.navigate.to(f'/casos/{caso_link_id}')
                        
                        ui.button(
                            'Abrir Caso',
                            icon='open_in_new',
                            on_click=abrir_caso
                        ).props('color=primary outlined').classes('mt-2')
            else:
                # Mensagem quando não há caso vinculado
                with ui.row().classes('items-center gap-2 text-gray-400'):
                    ui.icon('info', size='20px')
                    ui.label('Nenhum caso vinculado').classes('text-sm italic')
        
        # ===== PROCESSOS RELACIONADOS =====
        if processos:
            with ui.card().classes('w-full p-6 mb-4').style('border: 1px solid #e5e7eb;'):
                ui.label('⚖️ Processos Relacionados').classes('text-lg font-bold text-gray-800 mb-4')
                
                with ui.column().classes('w-full gap-2'):
                    for processo in processos:
                        processo_id = processo.get('_id') or processo.get('id')
                        processo_title = processo.get('title', 'Sem título')
                        processo_number = processo.get('number', '')
                        
                        with ui.row().classes('items-center gap-2 p-2 bg-gray-50 rounded'):
                            ui.icon('gavel', size='18px').classes('text-orange-500')
                            if processo_number:
                                ui.label(f'{processo_title} ({processo_number})').classes('text-sm')
                            else:
                                ui.label(processo_title).classes('text-sm')
        
        # ===== CLÁUSULAS =====
        with ui.card().classes('w-full p-6 mb-4').style('border: 1px solid #e5e7eb;'):
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('📋 Cláusulas').classes('text-lg font-bold text-gray-800')
                
                # Botão para abrir modal de visualização
                from .modais import render_visualizar_clausulas_dialog
                
                def abrir_modal_clausulas():
                    """Abre modal de visualização de cláusulas."""
                    dialog, open_dialog = render_visualizar_clausulas_dialog(
                        clausulas=clausulas,
                        titulo_acordo=titulo
                    )
                    open_dialog()
                
                ui.button(
                    'Visualizar Cláusulas',
                    icon='table_chart',
                    on_click=abrir_modal_clausulas
                ).props('color=primary outlined').classes('font-medium')
            
            # Resumo das cláusulas
            if clausulas:
                total_clausulas = len(clausulas)
                cumpridas = sum(1 for c in clausulas if c.get('status') == 'Cumprida')
                pendentes = sum(1 for c in clausulas if c.get('status') == 'Pendente')
                atrasadas = sum(1 for c in clausulas if c.get('status') == 'Atrasada')
                
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    with ui.card().classes('flex-1 min-w-32 p-3').style('border: 1px solid #e0e0e0;'):
                        ui.label('Total').classes('text-xs text-gray-500 mb-1')
                        ui.label(str(total_clausulas)).classes('text-xl font-bold text-gray-800')
                    
                    with ui.card().classes('flex-1 min-w-32 p-3').style('border: 1px solid #e0e0e0;'):
                        ui.label('Cumpridas').classes('text-xs text-gray-500 mb-1')
                        ui.label(str(cumpridas)).classes('text-xl font-bold text-green-600')
                    
                    with ui.card().classes('flex-1 min-w-32 p-3').style('border: 1px solid #e0e0e0;'):
                        ui.label('Pendentes').classes('text-xs text-gray-500 mb-1')
                        ui.label(str(pendentes)).classes('text-xl font-bold text-orange-600')
                    
                    with ui.card().classes('flex-1 min-w-32 p-3').style('border: 1px solid #e0e0e0;'):
                        ui.label('Atrasadas').classes('text-xs text-gray-500 mb-1')
                        ui.label(str(atrasadas)).classes('text-xl font-bold text-red-600')
                
                ui.label(f'Clique em "Visualizar Cláusulas" para ver a tabela completa com {total_clausulas} cláusula(s).').classes(
                    'text-sm text-gray-500 italic mt-2'
                )
            else:
                ui.label('Nenhuma cláusula cadastrada').classes('text-sm text-gray-400 italic')
        
        # ===== BOTÕES DE AÇÃO =====
        with ui.row().classes('w-full gap-4 mt-6'):
            ui.button(
                'Voltar',
                icon='arrow_back',
                on_click=lambda: ui.navigate.to('/acordos')
            ).props('outlined')
            
            ui.button(
                'Editar',
                icon='edit',
                on_click=abrir_edicao
            ).props('color=primary')

