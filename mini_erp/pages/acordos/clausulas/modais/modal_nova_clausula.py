"""
clausula_dialog.py - Dialog/Modal para criar e editar cláusulas de acordo.

Modal para adicionar/editar cláusulas com validações dinâmicas e campos condicionais.
"""

from nicegui import ui
from datetime import datetime
from typing import Optional, Callable, Dict, Any

from .....core import PRIMARY_COLOR
from ..business_logic import (
    validar_clausula, formatar_data_para_exibicao, formatar_data_para_iso,
    validate_tipo_clausula, validate_titulo_clausula, validate_datas_clausula,
    validate_comprovacao
)
from ..models import CLAUSULA_TIPO_OPTIONS, CLAUSULA_STATUS_OPTIONS, CLAUSULA_STATUS_CUMPRIDA
from ...utils import make_required_label


def limpar_campo(valor):
    """Limpa valor vindo de inputs de forma segura, prevenindo .strip() em None."""
    if valor is None:
        return ''
    if not isinstance(valor, str):
        valor = str(valor)
    return valor.strip()


def criar_dialog_nova_clausula(
    on_save_callback: Optional[Callable] = None,
    clausula_edit: Optional[Dict[str, Any]] = None,
    edit_index: Optional[int] = None
):
    """
    Cria dialog para adicionar/editar cláusula.
    
    Args:
        on_save_callback: Callback executado ao salvar (recebe dados da cláusula)
        clausula_edit: Dados da cláusula para edição (None para nova)
        edit_index: Índice da cláusula sendo editada (None para nova)
    
    Returns:
        tuple: (dialog_component, open_function)
    """
    
    is_editing = clausula_edit is not None
    
    # CSS para corrigir erro aria-hidden no backdrop
    dialog_css = '''
        .q-dialog__backdrop {
            pointer-events: auto !important;
        }
        .q-dialog__backdrop[aria-hidden="true"] {
            pointer-events: none !important;
        }
    '''
    ui.add_head_html(f'<style>{dialog_css}</style>')
    
    with ui.dialog().props('persistent') as dialog, ui.card().classes('w-full max-w-2xl p-0 overflow-hidden'):
        with ui.column().classes('w-full gap-0'):
            # Header
            with ui.row().classes('w-full items-center justify-between p-4').style(f'background-color: {PRIMARY_COLOR};'):
                dialog_title = ui.label('NOVA CLÁUSULA' if not is_editing else 'EDITAR CLÁUSULA').classes('text-lg font-bold text-white')
                ui.button(icon='close', on_click=dialog.close).props('flat dense round').classes('text-white')
            
            # Content
            with ui.column().classes('w-full p-6 gap-4 overflow-auto').style('max-height: calc(90vh - 120px);'):
                
                # ============================================================
                # SEÇÃO 1: INFORMAÇÕES BÁSICAS
                # ============================================================
                with ui.card().classes('w-full p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                    ui.label('📋 Informações Básicas').classes('text-base font-bold mb-3')
                    with ui.column().classes('w-full gap-4'):
                        # Tipo de Cláusula (OBRIGATÓRIO - NOVO)
                        tipo_clausula_select = ui.select(
                            CLAUSULA_TIPO_OPTIONS,
                            label=make_required_label('Tipo de Cláusula')
                        ).classes('w-full').props('outlined dense')
                        tipo_clausula_select.tooltip('Indique se esta cláusula é geral ou específica')
                        
                        # Título da Cláusula (OBRIGATÓRIO)
                        titulo_input = ui.input(
                            make_required_label('Título da Cláusula'),
                            placeholder='Ex: Obrigações do Cliente'
                        ).classes('w-full').props('outlined dense')
                        titulo_input.tooltip('Título descritivo da cláusula (máximo 200 caracteres)')
                        
                        # Número da Cláusula (OPCIONAL - antes era obrigatório)
                        numero_input = ui.input(
                            'Número da Cláusula',
                            placeholder='Ex: 1, 2.1, 3.2.1'
                        ).classes('w-full').props('outlined dense')
                        numero_input.tooltip('Número ou identificador da cláusula (opcional)')
                        
                        # Descrição Breve (OPCIONAL - antes era obrigatório)
                        descricao_input = ui.textarea(
                            'Descrição Breve',
                            placeholder='Resumo do conteúdo da cláusula...'
                        ).classes('w-full').props('outlined dense rows=4')
                        descricao_input.tooltip('Descrição resumida do conteúdo da cláusula (opcional)')
                        
                        # Status (OBRIGATÓRIO)
                        status_select = ui.select(
                            CLAUSULA_STATUS_OPTIONS,
                            label=make_required_label('Status'),
                            value='Pendente' if not is_editing else None
                        ).classes('w-full').props('outlined dense')
                        status_select.tooltip('Status atual da cláusula')
                
                # ============================================================
                # SEÇÃO 2: PRAZOS (OPCIONAL)
                # ============================================================
                with ui.card().classes('w-full p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
                    ui.label('📅 Prazos (Opcional)').classes('text-base font-bold mb-3')
                    with ui.column().classes('w-full gap-4'):
                        # Prazo de Segurança (OPCIONAL - antes era obrigatório)
                        prazo_seguranca_input = ui.input(
                            'Prazo de Segurança',
                            placeholder='DD/MM/AAAA'
                        ).classes('w-full').props('outlined dense')
                        prazo_seguranca_input.tooltip('Data limite de segurança (opcional, formato DD/MM/AAAA)')
                        
                        # Prazo Fatal (OPCIONAL - antes era obrigatório)
                        prazo_fatal_input = ui.input(
                            'Prazo Fatal',
                            placeholder='DD/MM/AAAA'
                        ).classes('w-full').props('outlined dense')
                        prazo_fatal_input.tooltip('Data limite fatal (opcional, deve ser após prazo de segurança)')
                
                # ============================================================
                # SEÇÃO 3: COMPROVAÇÃO (CONDICIONAL - apenas se Status = "Cumprida")
                # ============================================================
                comprovacao_container = ui.column().classes('w-full gap-4')
                comprovacao_container.visible = False  # Inicialmente oculto
                
                def toggle_comprovacao():
                    """Mostra/oculta seção de comprovação baseado no status."""
                    try:
                        if not status_select:
                            return
                        status = status_select.value
                        if not status:
                            return
                        
                        if status == CLAUSULA_STATUS_CUMPRIDA:
                            if comprovacao_container:
                                comprovacao_container.visible = True
                        else:
                            if comprovacao_container:
                                comprovacao_container.visible = False
                            # Limpa campos de comprovação quando oculto (só se existirem)
                            try:
                                if 'descricao_comprovacao_input' in locals() and descricao_comprovacao_input and hasattr(descricao_comprovacao_input, 'value'):
                                    descricao_comprovacao_input.value = ''
                            except:
                                pass
                            try:
                                if 'link_comprovacao_input' in locals() and link_comprovacao_input and hasattr(link_comprovacao_input, 'value'):
                                    link_comprovacao_input.value = ''
                            except:
                                pass
                    except Exception as e:
                        # Silenciosamente ignora erros de DOM
                        pass
                
                # Listener para mudança de status (usando on_value_change sem lambda problemática)
                def on_status_change():
                    toggle_comprovacao()
                status_select.on_value_change(on_status_change)
                
                with comprovacao_container:
                    with ui.card().classes('w-full p-4').style('border: 1px solid #4CAF50; box-shadow: 0 1px 3px rgba(76, 175, 80, 0.2); background-color: #f1f8f4;'):
                        ui.label('✅ Comprovação').classes('text-base font-bold mb-3 text-green-700')
                        with ui.column().classes('w-full gap-4'):
                            # Descrição de Comprovação (OBRIGATÓRIO se Status = Cumprida)
                            descricao_comprovacao_label = ui.label(make_required_label('Descrição de Comprovação'))
                            descricao_comprovacao_input = ui.textarea(
                                '',
                                placeholder='Descreva como/onde a cláusula foi cumprida'
                            ).classes('w-full').props('outlined dense rows=4 maxlength=1000')
                            descricao_comprovacao_input.tooltip('Explique em detalhes o cumprimento da cláusula (obrigatório para cláusulas cumpridas)')
                            
                            # Link de Comprovação (OPCIONAL)
                            link_comprovacao_input = ui.input(
                                'Link de Comprovação',
                                placeholder='https://exemplo.com/comprovacao'
                            ).classes('w-full').props('outlined dense maxlength=500')
                            link_comprovacao_input.tooltip('Cole um link que comprove o cumprimento (ex: documento, email, página)')
            
            # Footer
            with ui.row().classes('w-full justify-end gap-2 p-4').style(f'background-color: #f9fafb; border-top: 1px solid #e5e7eb;'):
                # Variável para controlar loading
                saving = False
                
                def do_save():
                    nonlocal saving
                    
                    # Previne múltiplos cliques
                    if saving:
                        return
                    
                    try:
                        saving = True
                        
                        def obter_valor_input(campo_input):
                            """Coleta valor do input usando limpar_campo para evitar AttributeError."""
                            valor_bruto = campo_input.value if campo_input else None
                            return limpar_campo(valor_bruto)
                        
                        # Coletar dados com tratamento defensivo de None
                        tipo_clausula_val = limpar_campo(
                            tipo_clausula_select.value if tipo_clausula_select else None
                        )
                        titulo_val = obter_valor_input(titulo_input)
                        numero_val = obter_valor_input(numero_input)
                        descricao_val = obter_valor_input(descricao_input)
                        status_val = limpar_campo(
                            status_select.value if status_select else None
                        )
                        prazo_seg_val = obter_valor_input(prazo_seguranca_input)
                        prazo_fatal_val = obter_valor_input(prazo_fatal_input)
                        
                        # Log para debug (remover em produção se necessário)
                        print(f"DEBUG: Valores coletados - tipo: {tipo_clausula_val}, titulo: {titulo_val}, status: {status_val}")
                        
                        # Montar dicionário de dados
                        clausula_data = {
                            'tipo_clausula': tipo_clausula_val,
                            'titulo': titulo_val,
                            'numero': numero_val or None,
                            'descricao': descricao_val or None,
                            'status': status_val,
                            'prazo_seguranca': prazo_seg_val or None,
                            'prazo_fatal': prazo_fatal_val or None,
                        }
                        
                        # Validações individuais (mais específicas)
                        errors = []
                        
                        # Validar tipo de cláusula
                        is_valid_tipo, error_tipo = validate_tipo_clausula(clausula_data.get('tipo_clausula', ''))
                        if not is_valid_tipo:
                            errors.append(error_tipo)
                        
                        # Validar título
                        is_valid_titulo, error_titulo = validate_titulo_clausula(clausula_data.get('titulo', ''))
                        if not is_valid_titulo:
                            errors.append(error_titulo)
                        
                        # Validar status
                        status_val_raw = clausula_data.get('status', '')
                        if not status_val_raw or (isinstance(status_val_raw, str) and not status_val_raw.strip()):
                            errors.append('Status é obrigatório!')
                        elif isinstance(status_val_raw, str) and status_val_raw not in CLAUSULA_STATUS_OPTIONS:
                            errors.append(f'Status inválido! Use um dos seguintes: {", ".join(CLAUSULA_STATUS_OPTIONS)}')
                        
                        # Validar datas
                        is_valid_datas, error_datas = validate_datas_clausula(
                            clausula_data.get('prazo_seguranca'),
                            clausula_data.get('prazo_fatal')
                        )
                        if not is_valid_datas:
                            errors.append(error_datas)
                        
                        # Se houver erros básicos, mostrar e parar
                        if errors:
                            error_msg = 'Corrija os seguintes erros:\n• ' + '\n• '.join(errors)
                            ui.notify(error_msg, type='warning', timeout=6000)
                            saving = False
                            return
                        
                        # Adiciona campos de comprovação se status = "Cumprida"
                        descricao_comprov = obter_valor_input(descricao_comprovacao_input)
                        link_comprov_raw = obter_valor_input(link_comprovacao_input)
                        link_comprov = link_comprov_raw if link_comprov_raw else None
                        
                        if clausula_data['status'] == CLAUSULA_STATUS_CUMPRIDA:
                            clausula_data['descricao_comprovacao'] = descricao_comprov
                            clausula_data['link_comprovacao'] = link_comprov
                            # Preenche data de cumprimento automaticamente
                            clausula_data['data_cumprimento'] = datetime.now().isoformat()
                            
                            # Validar comprovação
                            is_valid_comprov, error_comprov = validate_comprovacao(
                                clausula_data['status'],
                                descricao_comprov,
                                link_comprov
                            )
                            if not is_valid_comprov:
                                errors.append(error_comprov)
                        else:
                            clausula_data['descricao_comprovacao'] = None
                            clausula_data['link_comprovacao'] = None
                            clausula_data['data_cumprimento'] = None
                        
                        # Se houver erros de comprovação, mostrar e parar
                        if errors:
                            error_msg = 'Corrija os seguintes erros:\n• ' + '\n• '.join(errors)
                            ui.notify(error_msg, type='warning', timeout=6000)
                            saving = False
                            return
                        
                        # Converter datas para formato ISO (YYYY-MM-DD) se preenchidas
                        if clausula_data.get('prazo_seguranca'):
                            prazo_seg_iso = formatar_data_para_iso(clausula_data['prazo_seguranca'])
                            if not prazo_seg_iso:
                                ui.notify('Prazo de Segurança inválido! Use o formato DD/MM/AAAA.', type='negative')
                                saving = False
                                return
                            clausula_data['prazo_seguranca'] = prazo_seg_iso
                        
                        if clausula_data.get('prazo_fatal'):
                            prazo_fatal_iso = formatar_data_para_iso(clausula_data['prazo_fatal'])
                            if not prazo_fatal_iso:
                                ui.notify('Prazo Fatal inválido! Use o formato DD/MM/AAAA.', type='negative')
                                saving = False
                                return
                            clausula_data['prazo_fatal'] = prazo_fatal_iso
                        
                        # Validação final completa (redundante mas segura)
                        is_valid, error_msg = validar_clausula(clausula_data)
                        if not is_valid:
                            ui.notify(error_msg, type='warning', timeout=6000)
                            saving = False
                            return
                        
                        # Callback - DEVE ser executado ANTES de fechar o dialog
                        if on_save_callback:
                            try:
                                # Executa callback e aguarda conclusão
                                on_save_callback(clausula_data, edit_index)
                            except Exception as e:
                                import traceback
                                error_trace = traceback.format_exc()
                                print(f"ERRO ao salvar cláusula: {error_trace}")  # Log para debug
                                ui.notify(f'Erro ao salvar cláusula: {str(e)}', type='negative')
                                saving = False
                                return
                        else:
                            # Se não há callback, algo está errado
                            ui.notify('Erro: callback de salvamento não configurado!', type='negative')
                            saving = False
                            return
                        
                        # Notificação de sucesso ANTES de fechar
                        mensagem_sucesso = 'Cláusula adicionada com sucesso!' if not is_editing else 'Cláusula atualizada com sucesso!'
                        ui.notify(mensagem_sucesso, type='positive', timeout=3000)
                        
                        # Fechar modal após sucesso (com pequeno delay para garantir que notificação apareça)
                        ui.timer(0.1, lambda: dialog.close(), once=True)
                        
                    except AttributeError as e:
                        # Erro específico: tentativa de fazer .strip() em None
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"ERRO AttributeError ao salvar cláusula: {error_trace}")  # Log para debug
                        ui.notify('Erro ao processar dados: algum campo está vazio ou inválido. Verifique todos os campos obrigatórios.', type='negative', timeout=6000)
                    except Exception as e:
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"ERRO inesperado ao salvar cláusula: {error_trace}")  # Log para debug
                        # Mensagem mais amigável para o usuário
                        mensagem_erro = f'Erro ao salvar cláusula: {str(e)}'
                        if 'NoneType' in str(e) or 'strip' in str(e):
                            mensagem_erro = 'Erro ao processar dados: verifique se todos os campos obrigatórios estão preenchidos corretamente.'
                        ui.notify(mensagem_erro, type='negative', timeout=6000)
                    finally:
                        saving = False
                
                ui.button('Cancelar', icon='cancel', on_click=dialog.close).props('flat')
                ui.button('Adicionar' if not is_editing else 'Salvar', icon='add' if not is_editing else 'save', on_click=do_save).props('color=primary')
    
    def open_dialog():
        """Abre o dialog para criar/editar cláusula."""
        try:
            if is_editing and clausula_edit:
                # Preencher campos com dados da cláusula
                try:
                    tipo_clausula_select.value = clausula_edit.get('tipo_clausula', '')
                except Exception:
                    pass
                
                try:
                    titulo_input.value = clausula_edit.get('titulo', '')
                except Exception:
                    pass
                
                try:
                    numero_input.value = clausula_edit.get('numero', '') or ''
                except Exception:
                    pass
                
                try:
                    descricao_input.value = clausula_edit.get('descricao', '') or ''
                except Exception:
                    pass
                
                try:
                    status_select.value = clausula_edit.get('status', 'Pendente')
                except Exception:
                    pass
                
                # Converter datas de ISO para DD/MM/AAAA
                prazo_seg = clausula_edit.get('prazo_seguranca', '')
                if prazo_seg:
                    try:
                        # Tenta converter de ISO
                        if '-' in prazo_seg and len(prazo_seg) == 10:
                            dt = datetime.strptime(prazo_seg, '%Y-%m-%d')
                            prazo_seguranca_input.value = dt.strftime('%d/%m/%Y')
                        else:
                            # Se já está em DD/MM/AAAA, usa direto
                            prazo_seguranca_input.value = prazo_seg
                    except Exception:
                        prazo_seguranca_input.value = ''
                
                prazo_fatal = clausula_edit.get('prazo_fatal', '')
                if prazo_fatal:
                    try:
                        # Tenta converter de ISO
                        if '-' in prazo_fatal and len(prazo_fatal) == 10:
                            dt = datetime.strptime(prazo_fatal, '%Y-%m-%d')
                            prazo_fatal_input.value = dt.strftime('%d/%m/%Y')
                        else:
                            # Se já está em DD/MM/AAAA, usa direto
                            prazo_fatal_input.value = prazo_fatal
                    except Exception:
                        prazo_fatal_input.value = ''
                
                # Preencher campos de comprovação se existirem
                try:
                    descricao_comprovacao_input.value = clausula_edit.get('descricao_comprovacao', '') or ''
                except Exception:
                    pass
                
                try:
                    link_comprovacao_input.value = clausula_edit.get('link_comprovacao', '') or ''
                except Exception:
                    pass
                
                # Atualizar visibilidade da seção de comprovação
                try:
                    toggle_comprovacao()
                except Exception:
                    pass
            else:
                # Limpar campos para nova cláusula
                try:
                    tipo_clausula_select.value = None
                except Exception:
                    pass
                
                try:
                    titulo_input.value = ''
                except Exception:
                    pass
                
                try:
                    numero_input.value = ''
                except Exception:
                    pass
                
                try:
                    descricao_input.value = ''
                except Exception:
                    pass
                
                try:
                    status_select.value = 'Pendente'
                except Exception:
                    pass
                
                try:
                    prazo_seguranca_input.value = ''
                except Exception:
                    pass
                
                try:
                    prazo_fatal_input.value = ''
                except Exception:
                    pass
                
                try:
                    descricao_comprovacao_input.value = ''
                except Exception:
                    pass
                
                try:
                    link_comprovacao_input.value = ''
                except Exception:
                    pass
                
                try:
                    comprovacao_container.visible = False
                except Exception:
                    pass
            
            # Abrir dialog
            dialog.open()
            
        except Exception as e:
            # Notifica erro mas não quebra
            ui.notify(f'Erro ao abrir dialog: {str(e)}', type='warning')
    
    return dialog, open_dialog
