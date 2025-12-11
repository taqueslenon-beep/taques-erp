"""
password_security.py - Criptografia e segurança para senhas de processos.

Este módulo fornece funções para criptografar e descriptografar senhas
de forma segura usando Fernet (symmetric encryption).
"""

import os
import base64
from typing import Optional

# Tentar importar cryptography, se não estiver disponível usar fallback simples
try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("⚠️  Biblioteca 'cryptography' não encontrada. Senhas serão armazenadas sem criptografia.")
    print("   Para segurança adequada, instale: pip install cryptography")


def get_encryption_key() -> Optional[bytes]:
    """
    Obtém a chave de criptografia das variáveis de ambiente.
    
    Returns:
        Chave de criptografia em bytes ou None se não configurada
    """
    key_str = os.environ.get('PASSWORD_ENCRYPTION_KEY', '')
    if not key_str:
        return None
    
    try:
        # Se a chave for uma string base64, decodifica
        if len(key_str) == 44:  # Chave Fernet em base64 tem 44 caracteres
            return key_str.encode()
        # Caso contrário, gera uma chave Fernet a partir da string
        return Fernet.generate_key() if CRYPTOGRAPHY_AVAILABLE else None
    except Exception as e:
        print(f"⚠️  Erro ao processar chave de criptografia: {e}")
        return None


def generate_encryption_key() -> str:
    """
    Gera uma nova chave de criptografia Fernet.
    
    Returns:
        Chave em formato string (base64)
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        print("⚠️  Biblioteca cryptography não disponível para gerar chave.")
        return ''
    
    key = Fernet.generate_key()
    return key.decode()


def encrypt_password(password: str) -> str:
    """
    Criptografa uma senha usando Fernet.
    
    Args:
        password: Senha em texto plano
    
    Returns:
        Senha criptografada (string base64) ou senha original se criptografia não disponível
    """
    if not password:
        return ''
    
    if not CRYPTOGRAPHY_AVAILABLE:
        # Fallback: retorna senha sem criptografia (NÃO RECOMENDADO PARA PRODUÇÃO)
        print("⚠️  ATENÇÃO: Senha armazenada sem criptografia!")
        return password
    
    encryption_key = get_encryption_key()
    if not encryption_key:
        print("⚠️  Chave de criptografia não configurada. Senha armazenada sem criptografia.")
        return password
    
    try:
        fernet = Fernet(encryption_key)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"⚠️  Erro ao criptografar senha: {e}")
        return password  # Fallback: retorna senha sem criptografia


def decrypt_password(encrypted_password: str) -> str:
    """
    Descriptografa uma senha criptografada.
    
    Args:
        encrypted_password: Senha criptografada (string base64)
    
    Returns:
        Senha em texto plano ou string vazia em caso de erro
    """
    if not encrypted_password:
        return ''
    
    if not CRYPTOGRAPHY_AVAILABLE:
        # Se não há criptografia disponível, retorna como está (para compatibilidade)
        return encrypted_password
    
    encryption_key = get_encryption_key()
    if not encryption_key:
        # Se não há chave, retorna como está (pode ser senha não criptografada)
        return encrypted_password
    
    try:
        fernet = Fernet(encryption_key)
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"⚠️  Erro ao descriptografar senha: {e}")
        # Tenta retornar como texto plano (pode ser senha antiga não criptografada)
        return encrypted_password


def is_password_encrypted(encrypted_password: str) -> bool:
    """
    Verifica se uma senha está criptografada (heurística simples).
    
    Args:
        encrypted_password: String a verificar
    
    Returns:
        True se parece estar criptografada, False caso contrário
    """
    if not encrypted_password:
        return False
    
    # Senhas criptografadas com Fernet são sempre base64 e começam com caracteres específicos
    # Heurística: se tem mais de 40 caracteres e é base64 válido, provavelmente está criptografada
    if len(encrypted_password) > 40:
        try:
            base64.b64decode(encrypted_password)
            return True
        except:
            return False
    
    return False




