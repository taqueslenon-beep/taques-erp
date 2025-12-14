"""
Funções de banco de dados para gerenciamento de usuários do sistema.
"""

from typing import List, Dict, Optional, Any
from ..firebase_config import get_db
from google.cloud.firestore import SERVER_TIMESTAMP


COLECAO = 'usuarios_sistema'


def listar_usuarios() -> List[Dict[str, Any]]:
    """Lista todos os usuários do sistema."""
    try:
        db = get_db()
        docs = db.collection(COLECAO).stream()
        
        usuarios = []
        for doc in docs:
            usuario = doc.to_dict()
            usuario['_id'] = doc.id
            # Converter timestamps
            for campo in ['created_at', 'updated_at']:
                if campo in usuario and hasattr(usuario[campo], 'isoformat'):
                    usuario[campo] = usuario[campo].isoformat()
            usuarios.append(usuario)
        
        return usuarios
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []


def buscar_usuario(usuario_id: str) -> Optional[Dict[str, Any]]:
    """Busca um usuário por ID."""
    try:
        db = get_db()
        doc = db.collection(COLECAO).document(usuario_id).get()
        
        if doc.exists:
            usuario = doc.to_dict()
            usuario['_id'] = doc.id
            return usuario
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None


def buscar_usuario_por_uid(firebase_uid: str) -> Optional[Dict[str, Any]]:
    """Busca um usuário pelo UID do Firebase Auth."""
    try:
        db = get_db()
        query = db.collection(COLECAO).where('firebase_uid', '==', firebase_uid).limit(1)
        docs = list(query.stream())
        
        if docs:
            usuario = docs[0].to_dict()
            usuario['_id'] = docs[0].id
            return usuario
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário por UID: {e}")
        return None


def criar_usuario(dados: Dict[str, Any]) -> Optional[str]:
    """Cria um novo usuário e retorna o ID."""
    try:
        db = get_db()
        
        # Gera ID a partir do nome
        doc_id = dados.get('_id') or dados['nome_completo'].lower().replace(' ', '_')
        
        dados['_id'] = doc_id
        dados['created_at'] = SERVER_TIMESTAMP
        dados['updated_at'] = SERVER_TIMESTAMP
        
        db.collection(COLECAO).document(doc_id).set(dados)
        return doc_id
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return None


def atualizar_usuario(usuario_id: str, dados: Dict[str, Any]) -> bool:
    """Atualiza um usuário existente."""
    try:
        db = get_db()
        dados['updated_at'] = SERVER_TIMESTAMP
        db.collection(COLECAO).document(usuario_id).update(dados)
        return True
    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        return False


def excluir_usuario(usuario_id: str) -> bool:
    """Exclui um usuário."""
    try:
        db = get_db()
        db.collection(COLECAO).document(usuario_id).delete()
        return True
    except Exception as e:
        print(f"Erro ao excluir usuário: {e}")
        return False


def vincular_firebase_uid(usuario_id: str, firebase_uid: str) -> bool:
    """Vincula um UID do Firebase Auth a um usuário do sistema."""
    return atualizar_usuario(usuario_id, {'firebase_uid': firebase_uid})





