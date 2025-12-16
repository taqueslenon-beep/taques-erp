import os
import sys
import errno
import socket
import signal
import logging

# ============================================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================================
# Adiciona logging detalhado para diagnosticar problemas de inicialização e execução.
# O formato inclui timestamp, nome do logger, nível do log e a mensagem.
# Nível DEBUG para capturar todas as informações possíveis.
# ============================================================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=========================================================")
logger.info(">>> INICIANDO APLICAÇÃO TAQUES ERP...")
logger.info("=========================================================")


# ============================================================================
# SHIM DE COMPATIBILIDADE: importlib.metadata.packages_distributions
# ============================================================================
# Corrige o erro "module 'importlib.metadata' has no attribute 'packages_distributions'"
# que ocorre no Python 3.9 quando bibliotecas do Firebase/Google tentam acessar
# este atributo que só existe no Python 3.10+.
# ============================================================================
try:
    logger.debug("Verificando compatibilidade de 'importlib.metadata'...")
    import importlib.metadata
    # Verifica se packages_distributions existe
    if not hasattr(importlib.metadata, 'packages_distributions'):
        logger.warning("Atributo 'packages_distributions' não encontrado. Tentando shim de compatibilidade...")
        # Tenta importar do backport importlib_metadata
        try:
            import importlib_metadata
            if hasattr(importlib_metadata, 'packages_distributions'):
                importlib.metadata.packages_distributions = importlib_metadata.packages_distributions
                logger.info("✅ Shim de compatibilidade aplicado com sucesso usando 'importlib_metadata'.")
        except ImportError:
            # Se o backport não estiver disponível, cria função mínima
            logger.warning("Biblioteca 'importlib_metadata' não encontrada. Criando função 'packages_distributions' vazia.")
            def _packages_distributions():
                return {}
            importlib.metadata.packages_distributions = _packages_distributions
    else:
        logger.debug("'importlib.metadata' é compatível.")
except ImportError:
    logger.error("Falha ao importar 'importlib.metadata'.", exc_info=True)
    pass

# Agora é seguro importar nicegui e outros módulos que podem acionar Firebase
logger.debug("Importando NiceGUI...")
from nicegui import ui, app
logger.debug("NiceGUI importado com sucesso.")

# Garante que funcione tanto com `python3 -m mini_erp.main` quanto com `python3 mini_erp/main.py`
logger.debug(f"__package__ = '{__package__}'")
if __package__:
    logger.info("Executando como pacote. Importando páginas com 'from . import pages'.")
    from . import pages  # Registra todas as rotas
else:
    logger.info("Executando como script. Adicionando diretório pai ao sys.path e importando 'mini_erp.pages'.")
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import mini_erp.pages as pages

logger.info("Módulos de páginas importados. As rotas devem estar registradas.")


def is_port_available(port: int) -> bool:
    """
    Verifica se uma porta está disponível para uso.
    
    Returns:
        True se a porta estiver disponível, False caso contrário
    """
    logger.debug(f"Verificando disponibilidade da porta {port}...")
    try:
        # Primeiro tenta conectar - se conseguir, porta está em uso
        logger.debug(f"Tentando conectar a 127.0.0.1:{port} para ver se está ocupada...")
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(0.5)
        result = test_sock.connect_ex(('127.0.0.1', port))
        test_sock.close()
        if result == 0:
            logger.warning(f"Porta {port} JÁ ESTÁ EM USO (conexão bem-sucedida).")
            return False
        
        logger.debug(f"Conexão à porta {port} falhou com código {result}. Isso é bom. Tentando fazer bind...")
        # Se não conseguiu conectar, tenta fazer bind para confirmar que está livre
        bind_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bind_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_sock.bind(('127.0.0.1', port))
        bind_sock.close()
        logger.info(f"✅ Porta {port} está disponível (bind bem-sucedido).")
        return True
    except (OSError, socket.error) as e:
        logger.error(f"Erro de sistema operacional ao verificar a porta {port}: {e}", exc_info=True)
        return False
    except Exception:
        logger.error(f"Erro inesperado ao verificar a porta {port}.", exc_info=True)
        return False


def handle_segmentation_fault(signum, frame):
    """Handler para segmentation fault - tenta encerrar limpo."""
    logger.critical(f"\n❌ Erro crítico: Segmentation fault (sinal {signum}) detectado.")
    logger.critical(f"   Isso pode ocorrer quando a porta está em uso e o servidor tenta iniciar.")
    logger.critical(f"   Tente encerrar outros processos na porta ou use outra porta (APP_PORT).\n")
    # Usa os._exit() para forçar saída imediata sem executar handlers de limpeza
    os._exit(1)


def find_available_port(start_port=8081):
    """
    Encontra uma porta disponível a partir de start_port.
    Tenta portas sequencialmente até encontrar uma disponível.
    """
    port = start_port
    max_port = 65535  # Porta máxima do sistema
    attempts = 0
    
    while port <= max_port:
        if is_port_available(port):
            return port
        port += 1
        attempts += 1
        if attempts % 100 == 0:
            logger.debug(f"Verificando porta {port}... ({attempts} tentativas)")
    
    return None


def start_server_safe():
    """
    Inicia o servidor NiceGUI de forma segura, tratando erros de porta em uso.
    
    Lê a porta da variável de ambiente APP_PORT (padrão: 8081).
    Se a porta estiver em uso, tenta portas alternativas automaticamente até encontrar uma disponível.
    """
    logger.info("Iniciando o procedimento para iniciar o servidor seguro (start_server_safe)...")
    # Registra handler para segmentation fault (SIGSEGV)
    # Nota: Em alguns sistemas, isso pode não funcionar, mas ajuda quando possível
    try:
        logger.debug("Registrando handler para sinal SIGSEGV (Segmentation Fault)...")
        signal.signal(signal.SIGSEGV, handle_segmentation_fault)
    except (AttributeError, ValueError):
        logger.warning("Não foi possível registrar o handler para SIGSEGV (sinal não disponível neste sistema).")
        pass
    
    # Lê porta da variável de ambiente ou usa padrão
    base_port_str = os.environ.get('APP_PORT', '8081')
    logger.debug(f"Variável de ambiente APP_PORT='{base_port_str}'.")
    base_port = int(base_port_str)
    
    # Encontra uma porta disponível
    logger.info(f"Procurando porta disponível a partir de {base_port}...")
    port = find_available_port(base_port)
    
    if port is None:
        logger.critical(f"\n❌ Erro Fatal: Não foi possível encontrar uma porta disponível.")
        logger.critical(f"   Tente encerrar outros processos ou escolha uma porta manualmente (variável de ambiente APP_PORT).")
        logger.critical(f"   Exemplo: APP_PORT=9000 python3 -m mini_erp.main\n")
        os._exit(1)
    
    if port != base_port:
        logger.warning(f"⚠️  Porta original {base_port} estava ocupada. O servidor subirá na porta {port}.")
    else:
        logger.info(f"✅ Porta {port} está disponível.")
    
    logger.info(f"🚀 Porta {port} confirmada como disponível. Configurando o servidor NiceGUI...")
    
    # Detecta se está sendo executado via dev_server.py
    is_dev_server = os.environ.get('DEV_SERVER', '').lower() == 'true'
    logger.debug(f"Modo dev_server: {is_dev_server}")
    
    # Hot Reload: desabilitado aqui pois é gerenciado pelo dev_server.py via watchfiles
    # O dev_server.py faz o reload de forma mais controlada e customizável
    if is_dev_server:
        logger.info("🔄 Hot Reload gerenciado pelo dev_server.py (watchfiles)")
    else:
        logger.info("⚠️  Hot Reload desabilitado. Use 'python3 iniciar.py' ou 'python3 dev_server.py' para auto-reload.")
    
    # Adiciona middleware para headers anti-cache (corrige problema de cache no navegador)
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    
    class NoCacheMiddleware(BaseHTTPMiddleware):
        """Middleware que adiciona headers anti-cache em todas as respostas"""
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            # Adiciona headers anti-cache
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    
    # Registra middleware no app do NiceGUI
    app.add_middleware(NoCacheMiddleware)
    logger.info("✅ Middleware anti-cache configurado")
    
    # Configurações do servidor
    server_config = {
        'title': 'TAQUES-ERP - Sistema de Advocacia',
        'favicon': '💼',
        'port': port,
        'host': '0.0.0.0',
        'reload': False,  # CORRIGIDO: Desabilitado para evitar conflito com watchfiles (dev_server.py)
        'show': False,  # NUNCA abrir navegador automaticamente - controle externo via script
        'show_welcome_message': False,
        'storage_secret': 'taques-erp-secret-key-2024',
        'binding_refresh_interval': 3.0,
        'reconnect_timeout': 60.0,
    }
    logger.debug(f"Configurações do ui.run: {server_config}")

    try:
        logger.info(f">>> ✨ Iniciando servidor NiceGUI em http://localhost:{port} ✨ <<<")
        ui.run(**server_config)

    except (OSError, socket.error) as e:
        if hasattr(e, 'errno') and e.errno == errno.EADDRINUSE:  # Errno 48: Address already in use
            logger.critical(f"\n❌ Erro Fatal: Porta {port} já está em uso (EADDRINUSE).")
            logger.critical(f"   Isso não deveria acontecer após a verificação de porta. Pode haver uma 'race condition'.")
            logger.critical(f"   Encerre o outro processo ou escolha outra porta (variável de ambiente APP_PORT).\n")
            os._exit(1)
        else:
            logger.error(f"Erro de Sistema Operacional ao tentar iniciar o servidor.", exc_info=True)
            raise
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Servidor interrompido pelo usuário (KeyboardInterrupt).")
        os._exit(0)
    except Exception as e:
        logger.critical(f"\n❌ Erro fatal e inesperado ao iniciar o servidor.", exc_info=True)
        import traceback
        traceback.print_exc()
        os._exit(1)


# IMPORTANTE:
# Hot Reload está DESABILITADO aqui (reload=False) para evitar conflito com watchfiles.
# O dev_server.py gerencia o hot reload de forma mais robusta usando watchfiles.
# Use 'python3 iniciar.py' ou 'python3 dev_server.py' para desenvolvimento com auto-reload.
if __name__ in {"__main__", "__mp_main__"}:
    logger.info(f"Ponto de entrada (__name__='{__name__}') alcançado. Chamando start_server_safe().")
    start_server_safe()
