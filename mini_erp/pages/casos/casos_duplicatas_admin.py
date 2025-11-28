"""
Página de administração para gerenciar duplicatas de casos.

Fornece interface web para diagnosticar e corrigir duplicatas.
"""

from nicegui import ui

from ...core import layout, PRIMARY_COLOR
from ...auth import is_authenticated
from .duplicate_detection import find_duplicate_cases, deduplicate_cases


@ui.page('/casos/admin/duplicatas')
def casos_duplicatas_admin():
    """Página de administração para gerenciar duplicatas."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    with layout('Administração: Duplicatas de Casos', breadcrumbs=[('Casos', '/casos'), ('Admin', None)]):
        ui.label('🔍 Diagnóstico de Duplicatas de Casos').classes('text-2xl font-bold mb-6')
        
        # Container para resultados
        results_container = ui.column().classes('w-full')
        
        def refresh_analysis():
            """Atualiza análise de duplicatas."""
            results_container.clear()
            
            with results_container:
                ui.spinner('dots', size='lg').classes('mx-auto')
                ui.label('Analisando duplicatas...').classes('text-center text-gray-600')
            
            try:
                duplicates = find_duplicate_cases()
                stats = duplicates['stats']
                
                results_container.clear()
                
                with results_container:
                    # Estatísticas
                    with ui.card().classes('w-full p-6 mb-4'):
                        ui.label('📊 Estatísticas').classes('text-xl font-bold mb-4')
                        
                        with ui.grid(columns=4).classes('w-full gap-4'):
                            with ui.card().classes('p-4 bg-blue-50'):
                                ui.label('Total de Casos').classes('text-sm text-gray-600')
                                ui.label(str(stats['total_cases'])).classes('text-2xl font-bold text-blue-700')
                            
                            with ui.card().classes('p-4 bg-yellow-50'):
                                ui.label('Grupos Duplicados').classes('text-sm text-gray-600')
                                ui.label(str(stats['total_duplicate_groups'])).classes('text-2xl font-bold text-yellow-700')
                            
                            with ui.card().classes('p-4 bg-red-50'):
                                ui.label('Casos Duplicados').classes('text-sm text-gray-600')
                                ui.label(str(stats['total_duplicate_cases'])).classes('text-2xl font-bold text-red-700')
                            
                            with ui.card().classes('p-4 bg-green-50'):
                                ui.label('Após Dedup').classes('text-sm text-gray-600')
                                ui.label(str(stats['unique_cases_after_dedup'])).classes('text-2xl font-bold text-green-700')
                    
                    if stats['total_duplicate_cases'] == 0:
                        with ui.card().classes('w-full p-8 bg-green-50 border-2 border-green-300'):
                            ui.icon('check_circle', size='64px').classes('text-green-600 mx-auto mb-4')
                            ui.label('✅ Nenhuma duplicata encontrada!').classes('text-xl font-bold text-green-700 text-center')
                            ui.label('O sistema está íntegro.').classes('text-center text-green-600')
                    else:
                        # Duplicatas por slug
                        if duplicates['by_slug']:
                            with ui.card().classes('w-full p-6 mb-4'):
                                ui.label('🔴 Duplicatas por Slug (Crítico)').classes('text-lg font-bold mb-4')
                                
                                for slug, group in list(duplicates['by_slug'].items())[:20]:
                                    with ui.expansion(f'Slug: {slug} ({len(group)} duplicatas)', icon='warning').classes('w-full mb-2'):
                                        for case in group:
                                            with ui.row().classes('w-full items-center gap-2 p-2 bg-gray-50 rounded'):
                                                ui.label(f"ID: {case.get('_firestore_id', 'N/A')}").classes('text-xs text-gray-600')
                                                ui.label(f"Título: {case.get('title', 'Sem título')}").classes('text-sm font-medium')
                                        
                                        if len(duplicates['by_slug']) > 20:
                                            ui.label(f"... e mais {len(duplicates['by_slug']) - 20} grupo(s)").classes('text-xs text-gray-500 italic')
                        
                        # Botões de ação
                        with ui.card().classes('w-full p-6'):
                            ui.label('⚙️ Ações').classes('text-lg font-bold mb-4')
                            
                            with ui.row().classes('w-full gap-4'):
                                def run_dry_run():
                                    """Executa deduplicação em modo dry-run."""
                                    try:
                                        result = deduplicate_cases(dry_run=True)
                                        ui.notify(f'Análise concluída! {len(result["actions"])} ações seriam realizadas.', type='info')
                                        refresh_analysis()
                                    except Exception as e:
                                        ui.notify(f'Erro: {str(e)}', type='negative')
                                
                                ui.button('Simular Correção', icon='play_arrow', on_click=run_dry_run).classes('bg-yellow-600 text-white')
                                
                                def run_fix():
                                    """Executa deduplicação real."""
                                    with ui.dialog() as confirm_dialog, ui.card().classes('p-6'):
                                        ui.label('⚠️ Confirmação').classes('text-xl font-bold mb-4')
                                        ui.label('Esta operação irá modificar o banco de dados!').classes('text-red-600 mb-4')
                                        ui.label('Tem certeza que deseja continuar?').classes('mb-4')
                                        
                                        def confirm():
                                            try:
                                                result = deduplicate_cases(dry_run=False)
                                                ui.notify(f'✅ Correção concluída! {len(result["actions"])} ações realizadas.', type='positive')
                                                confirm_dialog.close()
                                                refresh_analysis()
                                            except Exception as e:
                                                ui.notify(f'Erro: {str(e)}', type='negative')
                                        
                                        with ui.row().classes('w-full justify-end gap-2'):
                                            ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                                            ui.button('Confirmar', icon='check', on_click=confirm).classes('bg-red-600 text-white')
                                    
                                    confirm_dialog.open()
                                
                                ui.button('Corrigir Duplicatas', icon='build', on_click=run_fix).classes('bg-red-600 text-white')
                                
                                ui.button('Atualizar Análise', icon='refresh', on_click=refresh_analysis).props('outline')
                
            except Exception as e:
                results_container.clear()
                with results_container:
                    with ui.card().classes('w-full p-6 bg-red-50 border-2 border-red-300'):
                        ui.label('❌ Erro ao analisar duplicatas').classes('text-xl font-bold text-red-700 mb-2')
                        ui.label(str(e)).classes('text-red-600')
                        import traceback
                        ui.code(traceback.format_exc()).classes('w-full text-xs')
        
        # Botão inicial para iniciar análise
        with ui.row().classes('w-full justify-center mb-6'):
            ui.button('Iniciar Análise', icon='search', on_click=refresh_analysis).classes('bg-primary text-white text-lg px-8 py-4')
        
        # Container inicial vazio
        with results_container:
            ui.label('Clique em "Iniciar Análise" para começar.').classes('text-center text-gray-500 italic')

