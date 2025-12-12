import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json


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
