"""
save_logger.py - Sistema de log para operações de salvamento

Fornece logging estruturado para todas as operações de salvamento no sistema,
facilitando debug e auditoria de dados.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class SaveLogger:
    """Logger para operações de salvamento"""
    
    @staticmethod
    def log_save_attempt(modulo: str, documento_id: str, dados: Dict[str, Any]):
        """
        Log antes de tentar salvar.
        
        Args:
            modulo: Nome do módulo (ex: 'casos', 'processos', 'acordos')
            documento_id: ID do documento sendo salvo
            dados: Dicionário com os dados a salvar
        """
        timestamp = datetime.now().isoformat()
        campos = list(dados.keys())
        print(f"[{timestamp}] [SAVE] [{modulo}] Tentando salvar documento {documento_id}")
        print(f"[{timestamp}] [SAVE] [{modulo}] Campos: {campos}")
        print(f"[{timestamp}] [SAVE] [{modulo}] Total de campos: {len(campos)}")
    
    @staticmethod
    def log_save_success(modulo: str, documento_id: str):
        """
        Log após salvar com sucesso.
        
        Args:
            modulo: Nome do módulo
            documento_id: ID do documento salvo
        """
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [SAVE OK] [{modulo}] Documento {documento_id} salvo com sucesso")
    
    @staticmethod
    def log_save_error(modulo: str, documento_id: str, erro: Exception):
        """
        Log de erro ao salvar.
        
        Args:
            modulo: Nome do módulo
            documento_id: ID do documento que falhou ao salvar
            erro: Exceção capturada
        """
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [SAVE ERROR] [{modulo}] Erro ao salvar {documento_id}: {erro}")
        import traceback
        print(f"[{timestamp}] [SAVE ERROR] [{modulo}] Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def log_load(modulo: str, documento_id: str, campos_carregados: list):
        """
        Log ao carregar documento.
        
        Args:
            modulo: Nome do módulo
            documento_id: ID do documento carregado
            campos_carregados: Lista de campos que foram carregados
        """
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [LOAD] [{modulo}] Documento {documento_id} carregado")
        print(f"[{timestamp}] [LOAD] [{modulo}] Campos carregados: {campos_carregados}")
        print(f"[{timestamp}] [LOAD] [{modulo}] Total de campos: {len(campos_carregados)}")
    
    @staticmethod
    def log_field_change(modulo: str, campo: str, tinha_valor: bool, tem_valor: bool):
        """
        Log de mudança de campo.
        
        Args:
            modulo: Nome do módulo
            campo: Nome do campo que mudou
            tinha_valor: Se o campo tinha valor antes
            tem_valor: Se o campo tem valor agora
        """
        timestamp = datetime.now().isoformat()
        status_antes = "preenchido" if tinha_valor else "vazio"
        status_agora = "preenchido" if tem_valor else "vazio"
        print(f"[{timestamp}] [CHANGE] [{modulo}] Campo '{campo}' mudou de {status_antes} para {status_agora}")
    
    @staticmethod
    def log_autosave(modulo: str, campo: str, documento_id: str):
        """
        Log de auto-save realizado.
        
        Args:
            modulo: Nome do módulo
            campo: Nome do campo salvo automaticamente
            documento_id: ID do documento
        """
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [AUTO-SAVE] [{modulo}] Campo '{campo}' do documento {documento_id} salvo automaticamente")

