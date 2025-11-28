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
    try:
        # Validar imagem
        img = Image.open(image_file)
        
        # Converter para RGB se necessário (para salvar como JPEG/PNG sem alpha se der erro, mas PNG suporta RGBA)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
        
        # Redimensionar para 200x200 mantendo proporção ou cortando?
        # Vamos usar thumbnail para garantir que cabe em 200x200, mas o ideal seria crop circular.
        # Para simplicidade e seguindo o prompt: thumbnail 200x200.
        img.thumbnail((200, 200))
        
        # Converter para bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        
        # Upload para Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f'avatars/{user_uid}.png')
        
        # Metadados para cache
        blob.cache_control = 'public, max-age=31536000'  # Cache por 1 ano
        
        blob.upload_from_string(
            img_bytes.getvalue(),
            content_type='image/png'
        )
        
        # Gerar URL pública
        blob.make_public()
        url = blob.public_url
        
        # Adiciona timestamp para evitar cache do navegador imediato ao recarregar
        return f"{url}?t={int(time.time())}"
        
    except Exception as e:
        print(f"Erro ao fazer upload: {e}")
        return None

def obter_url_avatar(user_uid):
    """Obtém URL do avatar do usuário"""
    try:
        bucket = storage.bucket()
        blob = bucket.blob(f'avatars/{user_uid}.png')
        
        if blob.exists():
            # blob.make_public() # Opcional se já foi feito no upload, mas garante acesso
            return blob.public_url
        return None
    except Exception as e:
        print(f"Erro ao obter avatar: {e}")
        return None

def deletar_avatar(user_uid):
    """Deleta o avatar do usuário"""
    try:
        bucket = storage.bucket()
        blob = bucket.blob(f'avatars/{user_uid}.png')
        if blob.exists():
            blob.delete()
        return True
    except Exception as e:
        print(f"Erro ao deletar avatar: {e}")
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
