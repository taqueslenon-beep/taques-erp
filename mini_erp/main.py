import os
import sys
import errno
import socket
import signal

# ============================================================================
# SHIM DE COMPATIBILIDADE: importlib.metadata.packages_distributions
# ============================================================================
# Corrige o erro "module 'importlib.metadata' has no attribute 'packages_distributions'"
# que ocorre no Python 3.9 quando bibliotecas do Firebase/Google tentam acessar
# este atributo que só existe no Python 3.10+.
# ============================================================================
try:
    import importlib.metadata
    # Verifica se packages_distributions existe
    if not hasattr(importlib.metadata, 'packages_distributions'):
        # Tenta importar do backport importlib_metadata
        try:
            import importlib_metadata
            if hasattr(importlib_metadata, 'packages_distributions'):
                importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
        except ImportError:
            # Se o backport não estiver disponível, cria função mínima
            def _packages_distributions():
                return {}
            importlib.metadata.packages_distributions = _packages_distributions
except ImportError:
    # Se importlib.metadata não existir (muito raro), ignora
    pass

# Agora é seguro importar nicegui e outros módulos que podem acionar Firebase
from nicegui import ui

# Garante que funcione tanto com `python3 -m mini_erp.main` quanto com `python3 mini_erp/main.py`
if __package__:
    from . import pages  # Registra todas as rotas
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import mini_erp.pages as pages


def is_port_available(port: int) -> bool:
    """
    Verifica se uma porta está disponível para uso.
    
    Returns:
        True se a porta estiver disponível, False caso contrário
    """
    try:
        # Primeiro tenta conectar - se conseguir, porta está em uso
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(0.5)
        result = test_sock.connect_ex(('127.0.0.1', port))
        test_sock.close()
        if result == 0:
            # Conexão bem-sucedida = porta em uso
            return False
        
        # Se não conseguiu conectar, tenta fazer bind para confirmar que está livre
        bind_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bind_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_sock.bind(('127.0.0.1', port))
        bind_sock.close()
        return True
    except (OSError, socket.error) as e:
        # Qualquer erro significa que porta não está disponível
        return False
    except Exception:
        # Em caso de qualquer outro erro, assume que não está disponível
        return False


def handle_segmentation_fault(signum, frame):
    """Handler para segmentation fault - tenta encerrar limpo."""
    print(f"\n❌ Erro crítico: Segmentation fault detectado.")
    print(f"   Isso pode ocorrer quando a porta está em uso e o servidor tenta iniciar.")
    print(f"   Tente encerrar outros processos na porta ou use outra porta (APP_PORT).\n")
    # Usa os._exit() para forçar saída imediata sem executar handlers de limpeza
    os._exit(1)


def start_server_safe():
    """
    Inicia o servidor NiceGUI de forma segura, tratando erros de porta em uso.
    
    Lê a porta da variável de ambiente APP_PORT (padrão: 8081).
    Se a porta estiver em uso, tenta portas alternativas automaticamente (8082, 8083, etc).
    """
    # Registra handler para segmentation fault (SIGSEGV)
    # Nota: Em alguns sistemas, isso pode não funcionar, mas ajuda quando possível
    try:
        signal.signal(signal.SIGSEGV, handle_segmentation_fault)
    except (AttributeError, ValueError):
        # SIGSEGV pode não estar disponível em todos os sistemas
        pass
    
    # Lê porta da variável de ambiente ou usa padrão
    base_port = int(os.environ.get('APP_PORT', '8080'))
    port = base_port
    max_attempts = 10  # Tenta até 10 portas alternativas
    
    # Tenta encontrar uma porta disponível
    print(f"Verificando porta {port}...")
    attempts = 0
    while not is_port_available(port) and attempts < max_attempts:
        attempts += 1
        port = base_port + attempts
        print(f"Porta {base_port + attempts - 1} ocupada. Tentando porta {port}...")
    
    if not is_port_available(port):
        print(f"\n❌ Erro: Não foi possível encontrar uma porta disponível.")
        print(f"   Tente encerrar outros processos ou escolha uma porta manualmente (variável de ambiente APP_PORT).")
        print(f"   Exemplo: APP_PORT=9000 python3 -m mini_erp.main\n")
        os._exit(1)
    
    if port != base_port:
        print(f"⚠️  Porta {base_port} estava ocupada. Usando porta {port}.")
    
    print(f"✅ Porta {port} disponível. Iniciando servidor em http://localhost:{port}...")
    
    # Detecta se está sendo executado via dev_server.py
    is_dev_server = os.environ.get('DEV_SERVER', '').lower() == 'true'
    
    try:
        print(f"\n🚀 NiceGUI running on http://localhost:{port}\n")
        ui.run(
            title='TAQUES ERP', 
            favicon='💼', 
            port=port,
            host='0.0.0.0',  # Aceita conexões de qualquer IP
            reload=False,  # SEMPRE desabilitado - watchfiles do dev_server cuida disso
            show=False if is_dev_server else True,  # Desabilita auto-open quando via dev_server
            show_welcome_message=False,
            storage_secret='taques-erp-secret-key-2024',  # Necessário para sessões
            binding_refresh_interval=3.0,  # Intervalo maior = menos tráfego WebSocket (era 2.0)
            reconnect_timeout=60.0,  # Timeout MUITO maior evita desconexões (era 15.0)
        )
    except (OSError, socket.error) as e:
        if hasattr(e, 'errno') and e.errno == errno.EADDRINUSE:  # Errno 48: Address already in use
            print(f"\n❌ Erro: Porta {port} já está em uso.")
            print(f"   Encerre o outro processo ou escolha outra porta (variável de ambiente APP_PORT).")
            print(f"   Exemplo: APP_PORT=8082 python3 -m mini_erp.main\n")
            # Usa os._exit() para forçar saída imediata
            os._exit(1)
        else:
            # Re-raise outros erros OSError
            raise
    except KeyboardInterrupt:
        print("\n\nServidor interrompido pelo usuário.")
        os._exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}\n")
        import traceback
        traceback.print_exc()
        os._exit(1)


# IMPORTANTE:
# Em desenvolvimento, usamos reload=True para que mudanças no código
# sejam detectadas automaticamente e o servidor reinicie.
# Isso pode desconectar temporariamente o navegador, mas facilita o desenvolvimento.
# 
# Em produção, trocar para reload=False.
if __name__ in {"__main__", "__mp_main__"}:
    start_server_safe()
