import os
import time
from datetime import datetime
from pathlib import Path
from nicegui import ui
from ..core import layout

# Caminho raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent
MINI_ERP_DIR = PROJECT_ROOT / 'mini_erp'

# Cache de timestamps dos arquivos e histórico de mudanças
file_timestamps = {}
change_history = []

def get_python_files():
    """Retorna lista de arquivos Python do projeto."""
    files = []
    for root, dirs, filenames in os.walk(MINI_ERP_DIR):
        # Ignora __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                files.append(filepath)
    return files

def check_file_changes():
    """Verifica se algum arquivo foi modificado."""
    changes = []
    
    for filepath in get_python_files():
        try:
            mtime = os.path.getmtime(filepath)
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)
            
            if filepath in file_timestamps:
                if mtime > file_timestamps[filepath]:
                    change_info = {
                        'file': rel_path,
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'timestamp': time.time(),
                        'action': 'modified'
                    }
                    changes.append(change_info)
                    change_history.append(change_info)
                    # Mantém apenas últimas 50 mudanças
                    if len(change_history) > 50:
                        change_history.pop(0)
            else:
                # Primeira detecção do arquivo
                file_timestamps[filepath] = mtime
            
            file_timestamps[filepath] = mtime
        except Exception:
            pass
    
    return changes

@ui.page('/dev')
def dev_page():
    """Página de desenvolvimento com monitoramento em tempo real."""
    with layout('Modo Desenvolvimento', breadcrumbs=[('Dev', None)]):
        
        # Status do servidor
        status_card = ui.card().classes('w-full mb-4')
        with status_card:
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('gap-1'):
                    status_label = ui.label('🟢 Servidor Online').classes('text-lg font-bold text-green-600')
                    last_check_label = ui.label('Verificando...').classes('text-sm text-gray-500')
                
                reload_btn = ui.button('🔄 Recarregar Página', on_click=lambda: ui.run_javascript('window.location.reload()')).props('color=primary')
        
        # Estatísticas
        stats_card = ui.card().classes('w-full mb-4')
        with stats_card:
            ui.label('📊 Estatísticas').classes('text-lg font-bold mb-3')
            with ui.row().classes('w-full gap-4'):
                files_count_label = ui.label('Arquivos: 0').classes('text-sm')
                changes_count_label = ui.label('Mudanças: 0').classes('text-sm')
                uptime_label = ui.label('Uptime: 0s').classes('text-sm')
        
        # Log de mudanças
        changes_card = ui.card().classes('w-full mb-4')
        with changes_card:
            ui.label('📝 Mudanças Detectadas').classes('text-lg font-bold mb-3')
            changes_container = ui.column().classes('w-full gap-2')
        
        # Configurações
        config_card = ui.card().classes('w-full')
        with config_card:
            ui.label('⚙️ Configurações').classes('text-lg font-bold mb-3')
            auto_reload_switch = ui.switch('Recarregar automaticamente', value=True).classes('mb-2')
            check_interval_slider = ui.slider(min=0.5, max=5, step=0.5, value=2).props('label label-always').classes('w-full')
            ui.label('Intervalo de verificação (segundos)').classes('text-xs text-gray-500 mb-2')
        
        # Script de monitoramento
        start_time = time.time()
        check_interval_ref = {'value': 2.0}
        timer_ref = {'timer': None}
        
        def update_status():
            # Atualiza status do servidor
            current_time = datetime.now().strftime('%H:%M:%S')
            last_check_label.text = f'Última verificação: {current_time}'
            
            # Verifica mudanças
            changes = check_file_changes()
            
            # Atualiza estatísticas
            files_count = len(get_python_files())
            files_count_label.text = f'Arquivos: {files_count}'
            total_changes = len([c for c in change_history if c["action"] == "modified"])
            changes_count_label.text = f'Mudanças detectadas: {total_changes}'
            
            uptime_seconds = int(time.time() - start_time)
            uptime_minutes = uptime_seconds // 60
            uptime_hours = uptime_minutes // 60
            if uptime_hours > 0:
                uptime_label.text = f'Uptime: {uptime_hours}h {uptime_minutes % 60}m'
            elif uptime_minutes > 0:
                uptime_label.text = f'Uptime: {uptime_minutes}m {uptime_seconds % 60}s'
            else:
                uptime_label.text = f'Uptime: {uptime_seconds}s'
            
            # Atualiza log de mudanças (mostra últimas 10)
            changes_container.clear()
            recent_changes = [c for c in change_history if c["action"] == "modified"][-10:]
            
            if recent_changes:
                for change in reversed(recent_changes):
                    with ui.row().classes('w-full items-center gap-2 p-2 bg-yellow-50 rounded mb-1'):
                        ui.icon('edit', size='sm').classes('text-yellow-600')
                        ui.label(f'{change["file"]}').classes('text-sm flex-grow font-mono text-xs')
                        ui.label(change["time"]).classes('text-xs text-gray-500')
            else:
                ui.label('Nenhuma mudança detectada ainda.').classes('text-sm text-gray-400 italic')
            
            # Auto-reload se habilitado e houver mudanças novas
            if auto_reload_switch.value and changes:
                latest_change = changes[-1]
                ui.notify(f'📝 {latest_change["file"]} modificado. Recarregando...', type='info', timeout=2000)
                ui.timer(1.5, lambda: ui.run_javascript('window.location.reload()'), once=True)
        
        def start_monitoring():
            """Inicia ou reinicia o timer de monitoramento."""
            if timer_ref['timer']:
                timer_ref['timer'].deactivate()
            
            interval = check_interval_ref['value']
            timer_ref['timer'] = ui.timer(interval, update_status, active=True)
        
        # Atualiza intervalo quando slider muda
        def on_interval_change():
            check_interval_ref['value'] = check_interval_slider.value
            start_monitoring()
        
        check_interval_slider.on('update:model-value', lambda: on_interval_change())
        
        # Inicia monitoramento
        start_monitoring()
        
        # Atualização inicial
        update_status()
        
        # Inicializa timestamps na primeira execução
        get_python_files()
        check_file_changes()

