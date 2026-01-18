import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json
import atexit
import logging
import threading
import time

logger = logging.getLogger(__name__)


def init_firebase():
    """Inicializa conexão com Firebase."""
    if not firebase_admin._apps:
        # Configuração do projeto Firebase
        firebase_config = {
            "type": "service_account",
            "project_id": "taques-erp",
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL", ""),
            "client_id": os.environ.get("FIREBASE_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get("FIREBASE_CERT_URL", "")
        }
        
        # Para desenvolvimento local, usar arquivo JSON se existir
        local_cred_path = os.path.join(os.path.dirname(__file__), '..', 'firebase-credentials.json')
        
        if os.path.exists(local_cred_path):
            cred = credentials.Certificate(local_cred_path)
        else:
            cred = credentials.Certificate(firebase_config)
        
        # Configurações adicionais (Storage)
        # Bucket correto: taques-erp.firebasestorage.app
        options = {
            'storageBucket': 'taques-erp.firebasestorage.app'
        }
        
        # Pode haver cenários (scripts CLI, reloads) em que o app
        # padrão já foi inicializado. Nesses casos, apenas reutilizamos
        # o app existente em vez de lançar erro.
        try:
            firebase_admin.initialize_app(cred, options)
        except ValueError as e:
            if "The default Firebase app already exists" not in str(e):
                raise
    
    return firestore.client()


def ensure_firebase_initialized():
    """
    Garante que Firebase Admin está inicializado e Auth está disponível.
    Retorna True se inicializado com sucesso, False caso contrário.
    """
    try:
        # Inicializa se necessário
        if not firebase_admin._apps:
            init_firebase()
        
        # Verifica se Auth está acessível (tenta uma operação simples)
        # Não vamos listar usuários aqui, apenas verificar se o módulo está disponível
        # A verificação real será feita quando tentar usar auth.list_users()
        return True
    except Exception as e:
        print(f"[FIREBASE_INIT] Erro ao garantir inicialização: {e}")
        import traceback
        traceback.print_exc()
        return False


# Cliente Firestore global
db = None


def get_db():
    """Retorna instância do Firestore."""
    global db
    if db is None:
        db = init_firebase()
    return db


def get_auth():
    """
    Retorna instância do Firebase Auth.
    Garante que Firebase está inicializado antes de retornar.
    """
    ensure_firebase_initialized()
    return auth


# ============================================================================
# SHUTDOWN LIMPO DO FIREBASE/gRPC
# ============================================================================
# Previne segmentation fault durante shutdown do Python quando threads do gRPC
# tentam acessar o GIL que já foi destruído.
# ============================================================================

_shutdown_in_progress = threading.Lock()
_shutdown_complete = False


def shutdown_firebase_cleanly():
    """
    Encerra Firebase Admin SDK de forma limpa, aguardando threads do gRPC terminarem.
    Deve ser chamado antes do Python finalizar para evitar segmentation fault.
    """
    global _shutdown_complete
    
    # Evita múltiplas chamadas simultâneas
    if not _shutdown_in_progress.acquire(blocking=False):
        return
    
    if _shutdown_complete:
        _shutdown_in_progress.release()
        return
    
    try:
        logger.info("Encerrando Firebase Admin SDK de forma limpa...")
        
        # Fecha clientes Firestore se existirem
        global db
        if db is not None:
            try:
                # Firestore client não tem método close explícito, mas podemos limpar a referência
                db = None
            except Exception as e:
                logger.warning(f"Erro ao limpar cliente Firestore: {e}")
        
        # Aguarda um pouco para threads do gRPC finalizarem operações pendentes
        # Isso evita que threads tentem acessar o GIL durante o shutdown
        time.sleep(0.5)
        
        # Tenta encerrar apps do Firebase se existirem
        if firebase_admin._apps:
            try:
                # Não há método explícito de shutdown no firebase_admin,
                # mas limpar as referências ajuda
                for app_name in list(firebase_admin._apps.keys()):
                    try:
                        # Deleta o app (isso deve encerrar conexões gRPC)
                        firebase_admin.delete_app(firebase_admin._apps[app_name])
                    except Exception as e:
                        logger.debug(f"Erro ao deletar app {app_name}: {e}")
            except Exception as e:
                logger.warning(f"Erro ao encerrar apps Firebase: {e}")
        
        # Aguarda mais um pouco para garantir que threads do gRPC terminaram
        time.sleep(0.5)
        
        logger.info("✅ Firebase Admin SDK encerrado com sucesso")
        _shutdown_complete = True
        
    except Exception as e:
        logger.warning(f"Erro durante shutdown do Firebase: {e}")
    finally:
        _shutdown_in_progress.release()


# Registra shutdown automático quando Python encerrar
atexit.register(shutdown_firebase_cleanly)
