"""
Sistema de auto-save para campos de texto longo do módulo de processos.

Este módulo implementa salvamento automático periódico para campos
como relatório, estratégia e cenários.
"""

from typing import Optional, Callable
from datetime import datetime
import asyncio
from nicegui import ui

from ..core import save_process as save_process_to_firestore
from .database import get_all_processes


# =============================================================================
# FUNÇÕES DE AUTO-SAVE
# =============================================================================

async def auto_save_field(
    processo_id: str,
    campo_nome: str,
    campo_componente: ui.editor,
    status_label: Optional[ui.label] = None,
    intervalo_segundos: int = 30
):
    """
    Implementa auto-save para um campo de texto longo.
    
    Args:
        processo_id: ID do processo no Firestore
        campo_nome: Nome do campo no Firestore (ex: 'relatory_facts')
        campo_componente: Componente ui.editor do NiceGUI
        status_label: Label opcional para mostrar status de salvamento
        intervalo_segundos: Intervalo entre verificações (padrão: 30s)
    """
    if not processo_id:
        print(f"[AUTO-SAVE] ⚠️  Processo ID não fornecido para campo {campo_nome}")
        return
    
    estado = {
        'ultimo_valor': campo_componente.value or '',
        'salvando': False,
        'ativo': True
    }
    
    print(f"[AUTO-SAVE] Iniciado para processo {processo_id}, campo {campo_nome}")
    
    while estado['ativo']:
        try:
            await asyncio.sleep(intervalo_segundos)
            
            if not estado['ativo']:
                break
            
            valor_atual = campo_componente.value or ''
            
            # Verifica se houve mudança
            if valor_atual != estado['ultimo_valor'] and not estado['salvando']:
                estado['salvando'] = True
                
                if status_label:
                    status_label.text = 'Salvando...'
                    status_label.classes(remove='text-green-600 text-red-600')
                    status_label.classes(add='text-blue-600')
                
                try:
                    # Busca processo atual
                    processos = get_all_processes()
                    processo_atual = None
                    for proc in processos:
                        if proc.get('_id') == processo_id:
                            processo_atual = proc.copy()
                            break
                    
                    if not processo_atual:
                        print(f"[AUTO-SAVE] ⚠️  Processo {processo_id} não encontrado")
                        if status_label:
                            status_label.text = 'Erro: processo não encontrado'
                            status_label.classes(remove='text-blue-600')
                            status_label.classes(add='text-red-600')
                        estado['salvando'] = False
                        continue
                    
                    # Atualiza apenas o campo específico
                    processo_atual[campo_nome] = valor_atual
                    processo_atual['_id'] = processo_id
                    
                    # Salva no Firestore
                    save_process_to_firestore(processo_atual, doc_id=processo_id, sync=False)
                    
                    estado['ultimo_valor'] = valor_atual
                    timestamp = datetime.now().strftime('%H:%M')
                    
                    if status_label:
                        status_label.text = f'Salvo às {timestamp}'
                        status_label.classes(remove='text-blue-600 text-red-600')
                        status_label.classes(add='text-green-600')
                    
                    print(f"[AUTO-SAVE] ✓ Processo {processo_id} - Campo {campo_nome} salvo às {timestamp}")
                    
                except Exception as e:
                    print(f"[AUTO-SAVE] ❌ ERRO ao salvar campo {campo_nome}: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    if status_label:
                        status_label.text = 'Erro ao salvar'
                        status_label.classes(remove='text-blue-600 text-green-600')
                        status_label.classes(add='text-red-600')
                
                finally:
                    estado['salvando'] = False
        
        except asyncio.CancelledError:
            print(f"[AUTO-SAVE] Cancelado para campo {campo_nome}")
            estado['ativo'] = False
            break
        except Exception as e:
            print(f"[AUTO-SAVE] ❌ ERRO inesperado no auto-save de {campo_nome}: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(intervalo_segundos)  # Aguarda antes de tentar novamente


def criar_campo_com_auto_save(
    label: str,
    campo_nome: str,
    processo_id_ref: dict,
    valor_inicial: str = '',
    intervalo_segundos: int = 30,
    placeholder: str = ''
) -> tuple:
    """
    Cria um campo de texto longo (ui.editor) com auto-save.
    
    Args:
        label: Label do campo
        campo_nome: Nome do campo no Firestore
        processo_id_ref: Dicionário com referência ao ID do processo (ex: {'val': 'process_id'})
        valor_inicial: Valor inicial do campo
        intervalo_segundos: Intervalo entre salvamentos (padrão: 30s)
        placeholder: Texto placeholder
    
    Returns:
        Tupla (campo_componente, status_label, task_ref)
        - campo_componente: Componente ui.editor
        - status_label: Label de status
        - task_ref: Referência para a task de auto-save (para cancelar se necessário)
    """
    # Criar campo
    campo = ui.editor(placeholder=placeholder).classes('w-full').style('height: 200px')
    campo.value = valor_inicial
    
    # Indicador de status
    status_label = ui.label('').classes('text-xs text-gray-400')
    
    # Referência para a task
    task_ref = {'val': None}
    
    # Função para iniciar auto-save quando processo_id estiver disponível
    def iniciar_auto_save():
        processo_id = processo_id_ref.get('val')
        if processo_id:
            task = asyncio.create_task(
                auto_save_field(
                    processo_id,
                    campo_nome,
                    campo,
                    status_label,
                    intervalo_segundos
                )
            )
            task_ref['val'] = task
            print(f"[AUTO-SAVE] Task criada para campo {campo_nome}, processo {processo_id}")
        else:
            print(f"[AUTO-SAVE] ⚠️  Processo ID não disponível ainda para campo {campo_nome}")
    
    # Inicia auto-save após um pequeno delay (permite que o processo seja salvo primeiro)
    ui.timer(2.0, iniciar_auto_save, once=True)
    
    return campo, status_label, task_ref


def parar_auto_save(task_ref: dict):
    """
    Para o auto-save de um campo.
    
    Args:
        task_ref: Referência para a task de auto-save
    """
    if task_ref.get('val'):
        task_ref['val'].cancel()
        task_ref['val'] = None
        print(f"[AUTO-SAVE] Auto-save parado")

