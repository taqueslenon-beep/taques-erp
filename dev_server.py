#!/usr/bin/env python3

"""
NiceGUI Development Server with Auto-Reload
===========================================
Monitora mudanças em arquivos .py e recarrega a aplicação automaticamente.

USO:
    python3 dev_server.py

PASSO A PASSO:
1. Salve este arquivo na raiz do seu projeto (próximo a main.py)
2. No terminal, execute: python3 dev_server.py
3. Abra http://localhost:8081 no navegador
4. Faça mudanças no código e salve (Cmd+S ou Ctrl+S)
5. A página recarrega AUTOMATICAMENTE!

Não precisa mais digitar nada no terminal ou recarregar manualmente a página.
"""

import os
import subprocess
import sys
import time
import shutil
from pathlib import Path
from watchfiles import run_process, Change, DefaultFilter

# Configuração
MAIN_FILE = "mini_erp/main.py"  # Altere se seu arquivo principal tiver outro nome
WATCH_DIRS = ["."]     # Monitora o diretório atual
PORT = int(os.environ.get('APP_PORT', '8081'))  # Lê da variável de ambiente ou usa padrão

# Flag para habilitar/desabilitar hot reload automático
# Se DISABLE_AUTO_RELOAD=true, o servidor roda sem watchfiles (reinício manual)
ENABLE_AUTO_RELOAD = os.environ.get('DISABLE_AUTO_RELOAD', '').lower() != 'true'

# Debounce para evitar reinicializações em cascata
_last_restart = 0
DEBOUNCE_SECONDS = 1.0  # CORRIGIDO: Reduzido de 2 para 1 segundo para resposta mais rápida


def limpar_cache():
    """
    Remove __pycache__ para forçar reload completo dos módulos.
    Garante que mudanças em código sejam detectadas corretamente.
    """
    pasta_projeto = os.path.dirname(os.path.abspath(__file__))
    cache_removidos = 0
    
    for root, dirs, files in os.walk(pasta_projeto):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_path)
                cache_removidos += 1
            except Exception as e:
                print(f"⚠️  Erro ao remover cache em {cache_path}: {e}")
    
    if cache_removidos > 0:
        print(f"🧹 {cache_removidos} pastas __pycache__ removidas")


class StableFilter(DefaultFilter):
    """
    Filtro otimizado para detectar mudanças em arquivos .py do projeto.
    Melhorado para ser menos restritivo e mais responsivo.
    """
    
    def __init__(self):
        super().__init__()
        # Diretórios a ignorar
        self.ignore_dirs = {
            '.git', '__pycache__', '.venv', 'venv', '.pytest_cache', 
            'node_modules', '.cursor', 'terminals', '.mypy_cache',
            'dist', 'build', 'eggs', '*.egg-info', '.tox', '.nox',
            '.coverage', 'htmlcov', '.hypothesis', 'static', 'backups'
        }
        # Extensões a ignorar
        self.ignore_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
            '.log', '.tmp', '.temp', '.swp', '.swo', '.bak',
            '.db', '.sqlite', '.sqlite3', '.json', '.lock',
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.md', '.txt', '.rst', '.csv', '.xml', '.yaml', '.yml'
        }
    
    def __call__(self, change: Change, path: str) -> bool:
        """Retorna True se o arquivo deve ser monitorado."""
        global _last_restart
        
        path_obj = Path(path)
        
        # Ignora diretórios específicos (mas permite mini_erp/ e subpastas)
        for part in path_obj.parts:
            if part in self.ignore_dirs:
                return False
            # Ignora diretórios ocultos, exceto se for parte do projeto
            if part.startswith('.') and part not in ['.nicegui']:
                return False
        
        # Só aceita arquivos .py
        if path_obj.suffix != '.py':
            return False
        
        # Ignora arquivos temporários/backup
        name = path_obj.name
        if name.startswith('.') or name.startswith('~') or name.endswith('~'):
            return False
        
        # Ignora dev_server.py e iniciar.py (evita loop infinito)
        if name in ['dev_server.py', 'iniciar.py']:
            return False
        
        # Ignora apenas scripts de backup/migração na raiz, mas permite em subpastas
        # (ex: permite mini_erp/database/migrate.py mas ignora migrate_to_firestore.py na raiz)
        if 'backup' in name.lower() and 'backups' not in str(path_obj.parent):
            # Só ignora se estiver na raiz do projeto
            if len(path_obj.parts) <= 2:  # raiz ou uma pasta abaixo
                return False
        
        # Ignora scripts de migração apenas na raiz
        if 'migrate' in name.lower() and len(path_obj.parts) <= 2:
            return False
        
        # Debounce: ignora se reiniciou muito recentemente
        now = time.time()
        if now - _last_restart < DEBOUNCE_SECONDS:
            return False
        
        _last_restart = now
        
        # Limpa cache antes de reiniciar
        limpar_cache()
        
        print(f"\n📝 Mudança detectada: {path}")
        print(f"🔄 Reiniciando servidor...")
        return True


def validate_main_file():
    """Valida se o arquivo principal existe"""
    if not Path(MAIN_FILE).exists():
        print(f"❌ Erro: Arquivo '{MAIN_FILE}' não encontrado!")
        print(f"   Altere a variável MAIN_FILE em dev_server.py")
        sys.exit(1)
    print(f"✅ Arquivo principal encontrado: {MAIN_FILE}")


def run_nicegui_app():
    """Executa a aplicação NiceGUI"""
    try:
        # Define variável de ambiente para o main.py saber que está via dev_server
        env = os.environ.copy()
        env['DEV_SERVER'] = 'true'
        env['APP_PORT'] = str(PORT)
        
        subprocess.run(
            [sys.executable, MAIN_FILE],
            check=False,
            env=env
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido")
        sys.exit(0)


def open_browser():
    """Abre o navegador após um delay para dar tempo do servidor iniciar"""
    time.sleep(4)  # Aguarda servidor iniciar
    try:
        import webbrowser
        webbrowser.open(f'http://localhost:{PORT}')
    except Exception:
        pass  # Ignora erros ao abrir navegador


def main():
    print("\n" + "="*60)
    if ENABLE_AUTO_RELOAD:
        print("🚀 NiceGUI Development Server with Auto-Reload")
    else:
        print("🚀 NiceGUI Development Server (Manual Reload)")
    print("="*60)
    
    validate_main_file()
    
    if ENABLE_AUTO_RELOAD:
        print(f"\n📁 Monitorando mudanças em: {', '.join(WATCH_DIRS)}")
        print(f"🔄 Auto-reload habilitado (debounce: {DEBOUNCE_SECONDS}s)")
        print(f"🌐 Acesse a aplicação em: http://localhost:{PORT}")
        print("\n💡 Dicas:")
        print("   • Salve qualquer arquivo .py para recarregar automaticamente")
        print("   • O servidor reinicia quando detecta mudanças")
        print("   • A página web pode precisar de refresh manual (F5) após mudanças")
        print("   • Pressione Ctrl+C para parar o servidor")
        print("\n⚠️  IMPORTANTE: Se mudanças não aparecerem:")
        print("   • Pressione F5 no navegador para forçar refresh")
        print("   • Ou Ctrl+Shift+R (hard refresh) para limpar cache")
    else:
        print(f"\n🌐 Servidor iniciando em: http://localhost:{PORT}")
        print(f"🔄 Auto-reload DESABILITADO (modo manual)")
        print(f"   Use o script 'scripts/reiniciar_servidor.sh' para reiniciar")
        print(f"   Ou pressione Ctrl+C para parar o servidor")
    
    print("\n" + "="*60 + "\n")
    
    # Abre navegador em thread separada
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        if ENABLE_AUTO_RELOAD:
            # Modo com watchfiles (auto-reload)
            run_process(
                ".",
                target=run_nicegui_app,
                watch_filter=StableFilter(),
                recursive=True
            )
        else:
            # Modo sem watchfiles (reinício manual)
            run_nicegui_app()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor encerrado")
        sys.exit(0)


if __name__ == "__main__":
    main()

