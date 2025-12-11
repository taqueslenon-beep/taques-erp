"""
safe_save.py - Funções utilitárias para salvamento seguro de dados

Fornece wrappers e helpers para garantir salvamento consistente e seguro
de dados em todo o sistema, com validação, feedback visual e logging.
"""

from typing import Any, Dict, Callable, Optional
from nicegui import ui
from datetime import datetime
from .save_logger import SaveLogger


def safe_save(
    save_function: Callable,
    dados: Dict[str, Any],
    modulo: str,
    documento_id: Optional[str] = None,
    campos_obrigatorios: list = None,
    on_success: Optional[Callable] = None,
    on_error: Optional[Callable] = None
) -> bool:
    """
    Wrapper para salvamento seguro com validação e feedback.
    
    Args:
        save_function: Função que efetivamente salva os dados
        dados: Dicionário com os dados a salvar
        modulo: Nome do módulo (para logs)
        documento_id: ID do documento (para logs)
        campos_obrigatorios: Lista de campos que não podem ser vazios
        on_success: Callback executado após sucesso
        on_error: Callback executado após erro
    
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        # 1. Validar campos obrigatórios
        if campos_obrigatorios:
            for campo in campos_obrigatorios:
                valor = dados.get(campo)
                if not valor or (isinstance(valor, str) and not valor.strip()):
                    ui.notify(f'Campo obrigatório não preenchido: {campo}', type='warning')
                    return False
        
        # 2. Remover campos None (mantém strings vazias, pois podem ser válidas)
        dados_limpos = {k: v for k, v in dados.items() if v is not None}
        
        # 3. Adicionar metadados de atualização
        dados_limpos['updated_at'] = datetime.now().isoformat()
        
        # 4. Log antes de salvar
        SaveLogger.log_save_attempt(modulo, documento_id or 'novo', dados_limpos)
        
        # 5. Executar salvamento
        resultado = save_function(dados_limpos)
        
        # 6. Log de sucesso
        SaveLogger.log_save_success(modulo, documento_id or 'novo')
        
        # 7. Feedback visual
        ui.notify('Dados salvos com sucesso!', type='positive')
        
        # 8. Callback de sucesso
        if on_success:
            on_success(resultado)
        
        return True
        
    except Exception as e:
        # Log de erro
        SaveLogger.log_save_error(modulo, documento_id or 'novo', e)
        
        # Feedback visual
        ui.notify(f'Erro ao salvar: {str(e)}', type='negative')
        
        # Callback de erro
        if on_error:
            on_error(e)
        
        return False


def criar_auto_save(
    campo_input,
    save_function: Callable,
    documento_id: str,
    campo_nome: str,
    modulo: str,
    intervalo_segundos: int = 30
):
    """
    Cria auto-save para um campo específico.
    
    Args:
        campo_input: Componente NiceGUI do campo (input, textarea, editor)
        save_function: Função para salvar o campo (recebe documento_id, campo_nome, valor)
        documento_id: ID do documento
        campo_nome: Nome do campo no banco
        modulo: Nome do módulo (para logs)
        intervalo_segundos: Intervalo entre auto-saves (padrão: 30s)
    
    Returns:
        Função para parar o auto-save (se necessário)
    """
    estado = {'ultimo_valor': campo_input.value if hasattr(campo_input, 'value') else '', 'ativo': True}
    
    async def verificar_e_salvar():
        """Loop de verificação e salvamento automático."""
        import asyncio
        
        while estado['ativo']:
            await asyncio.sleep(intervalo_segundos)
            
            if not estado['ativo']:
                break
            
            try:
                # Obter valor atual do campo
                valor_atual = campo_input.value if hasattr(campo_input, 'value') else ''
                
                # Verificar se houve mudança
                if valor_atual != estado['ultimo_valor'] and valor_atual:
                    # Salvar o campo
                    save_function(documento_id, campo_nome, valor_atual)
                    
                    # Atualizar último valor salvo
                    estado['ultimo_valor'] = valor_atual
                    
                    # Log
                    SaveLogger.log_autosave(modulo, campo_nome, documento_id)
                    
                    # Feedback visual discreto
                    ui.notify('Auto-save ✓', type='info', position='bottom-right', timeout=1500)
                    
            except Exception as e:
                print(f"[AUTO-SAVE ERROR] [{modulo}] Erro ao salvar {campo_nome}: {e}")
                SaveLogger.log_save_error(modulo, documento_id, e)
    
    # Inicia o auto-save em background
    import asyncio
    task = asyncio.create_task(verificar_e_salvar())
    
    # Retorna função para parar o auto-save
    def parar_auto_save():
        """Para o auto-save."""
        estado['ativo'] = False
        if not task.done():
            task.cancel()
    
    return parar_auto_save

