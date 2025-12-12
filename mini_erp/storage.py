from firebase_admin import storage, auth, firestore
from PIL import Image
import io
import time

def fazer_upload_avatar(user_uid, image_file):
    """
    Faz upload da imagem para Firebase Storage.
    
    Args:
        user_uid: ID do usuário
        image_file: Objeto file-like com a imagem (bytes)
        
    Returns:
        URL pública da imagem ou None em caso de erro
    """
    print(f"[UPLOAD AVATAR] Iniciando para UID: {user_uid}")
    
    if not user_uid:
        print("[UPLOAD AVATAR] ERRO: user_uid não fornecido")
        return None
    
    if not image_file:
        print("[UPLOAD AVATAR] ERRO: image_file não fornecido")
        return None
    
    try:
        # Garantir que estamos no início do arquivo
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        # Validar imagem
        print("[UPLOAD AVATAR] Validando imagem...")
        img = Image.open(image_file)
        
        # Verificar se a imagem é válida
        img.verify()
        
        # Reabrir após verify (verify fecha o arquivo)
        image_file.seek(0)
        img = Image.open(image_file)
        
        # Converter para RGBA para suportar transparência
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Redimensionar para 200x200 mantendo proporção
        # Usa thumbnail para manter aspect ratio
        print("[UPLOAD AVATAR] Redimensionando imagem...")
        try:
            # PIL 10.0+ usa Image.Resampling
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        except AttributeError:
            # Versões antigas do PIL usam Image diretamente
            img.thumbnail((200, 200), Image.LANCZOS)
        
        # Converter para bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        image_size = len(img_bytes.getvalue())
        print(f"[UPLOAD AVATAR] Tamanho da imagem processada: {image_size} bytes")
        
        # Upload para Firebase Storage
        print("[UPLOAD AVATAR] Obtendo bucket do Firebase Storage...")
        bucket = storage.bucket()
        if not bucket:
            print("[UPLOAD AVATAR] ERRO: Bucket do Firebase Storage não disponível")
            return None
        
        print(f"[UPLOAD AVATAR] Bucket: {bucket.name}")
        
        blob_path = f'avatars/{user_uid}.png'
        print(f"[UPLOAD AVATAR] Caminho: {blob_path}")
        
        blob = bucket.blob(blob_path)
        
        # Metadados para cache
        blob.cache_control = 'public, max-age=31536000'  # Cache por 1 ano
        
        # Upload do arquivo
        print("[UPLOAD AVATAR] Fazendo upload...")
        blob.upload_from_string(
            img_bytes.getvalue(),
            content_type='image/png'
        )
        print("[UPLOAD AVATAR] Upload concluído!")
        
        # Gerar URL pública
        print("[UPLOAD AVATAR] Tornando blob público...")
        try:
            blob.make_public()
            print("[UPLOAD AVATAR] Blob tornado público com sucesso")
        except Exception as public_err:
            print(f"[UPLOAD AVATAR] AVISO: Erro ao tornar público: {type(public_err).__name__}: {str(public_err)}")
            # Continua mesmo assim, pode já ser público
        
        url = blob.public_url
        final_url = f"{url}?t={int(time.time())}"
        print(f"[UPLOAD AVATAR] Upload concluído! URL: {final_url}")
        
        return final_url
        
    except Exception as e:
        print(f"[UPLOAD AVATAR] ERRO: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def obter_url_avatar(user_uid):
    """Obtém URL do avatar do usuário"""
    print(f"[BUSCAR AVATAR] Buscando para UID: {user_uid}")
    
    if not user_uid:
        print("[BUSCAR AVATAR] ERRO: user_uid não fornecido")
        return None
    
    try:
        print("[BUSCAR AVATAR] Obtendo bucket do Firebase Storage...")
        bucket = storage.bucket()
        if not bucket:
            print("[BUSCAR AVATAR] ERRO: Bucket do Firebase Storage não disponível")
            return None
        
        print(f"[BUSCAR AVATAR] Bucket: {bucket.name}")
        
        blob_path = f'avatars/{user_uid}.png'
        blob = bucket.blob(blob_path)
        
        print(f"[BUSCAR AVATAR] Verificando se blob existe: {blob_path}")
        blob_exists = blob.exists()
        print(f"[BUSCAR AVATAR] Blob existe: {blob_exists}")
        
        if blob_exists:
            # Garante que o blob é público
            try:
                blob.make_public()
                print("[BUSCAR AVATAR] Blob tornado público (ou já era público)")
            except Exception as public_err:
                print(f"[BUSCAR AVATAR] AVISO: Erro ao tornar público: {type(public_err).__name__}: {str(public_err)}")
                # Continua mesmo assim, pode já ser público
            
            url = blob.public_url
            final_url = f"{url}?t={int(time.time())}"
            print(f"[BUSCAR AVATAR] URL: {final_url}")
            return final_url
        else:
            print(f"[BUSCAR AVATAR] Nenhum avatar encontrado para {user_uid}")
            return None
    except Exception as e:
        print(f"[BUSCAR AVATAR] ERRO: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def deletar_avatar(user_uid):
    """Deleta o avatar do usuário"""
    print(f"[DELETAR AVATAR] Tentando deletar avatar para UID: {user_uid}")
    
    try:
        bucket = storage.bucket()
        if not bucket:
            print("[DELETAR AVATAR] ERRO: Bucket do Firebase Storage não disponível")
            return False
        
        blob = bucket.blob(f'avatars/{user_uid}.png')
        if blob.exists():
            blob.delete()
            print(f"[DELETAR AVATAR] Avatar deletado com sucesso para {user_uid}")
            return True
        else:
            print(f"[DELETAR AVATAR] Avatar não existe para {user_uid}")
            return True  # Considera sucesso se não existir
    except Exception as e:
        print(f"[DELETAR AVATAR] ERRO: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def definir_display_name(user_uid, display_name):
    """Define o nome de exibição do usuário"""
    try:
        # Validação básica
        if not display_name or len(display_name) < 2 or len(display_name) > 50:
            return False
            
        # Atualizar custom claims
        user = auth.get_user(user_uid)
        custom_claims = user.custom_claims or {}
        custom_claims['display_name'] = display_name
        
        auth.set_custom_user_claims(user_uid, custom_claims)
        
        # Também salvar no Firestore para redundância e facilidade de acesso
        db = firestore.client()
        db.collection('users').document(user_uid).set({
            'display_name': display_name,
            'email': user.email,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        return True
    except Exception as e:
        print(f"Erro ao definir display_name: {e}")
        return False

def obter_display_name(user_uid):
    """Obtém o nome de exibição do usuário"""
    try:
        user = auth.get_user(user_uid)
        if user.custom_claims and 'display_name' in user.custom_claims:
            return user.custom_claims['display_name']
        
        # Fallback para Firestore
        db = firestore.client()
        doc = db.collection('users').document(user_uid).get()
        if doc.exists:
            data = doc.to_dict()
            if 'display_name' in data:
                return data['display_name']
        
        # Se não houver, retornar parte do email ou nome do user object
        if user.display_name:
            return user.display_name
            
        return user.email.split('@')[0]
    except Exception as e:
        print(f"Erro ao obter display_name: {e}")
        return "Usuário"
