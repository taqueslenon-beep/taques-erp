"""
Aba de Dados Básicos do modal de processo (Visão Geral).
"""
from nicegui import ui
from datetime import datetime
from typing import Dict, Any, List, Callable
from mini_erp.core import get_display_name
from .helpers import (
    make_required_label, get_short_name, format_option_for_search,
    get_option_value
)
from ..constants import TIPOS_PROCESSO
from mini_erp.models.prioridade import PRIORIDADE_PADRAO, CODIGOS_PRIORIDADE


def _validar_tipo_processo(tipo: str) -> str:
    """Valida e retorna tipo de processo válido."""
    if not tipo or tipo not in TIPOS_PROCESSO:
        return 'Judicial'
    return tipo


def _validar_prioridade(prioridade: str) -> str:
    """Valida e retorna prioridade válida."""
    if not prioridade or prioridade not in CODIGOS_PRIORIDADE:
        return PRIORIDADE_PADRAO
    return prioridade


def render_aba_dados_basicos(
    state: Dict[str, Any],
    dados: Dict[str, Any],
    todas_pessoas: List[Dict[str, Any]],
    todos_casos: List[Dict[str, Any]],
    usuarios_internos: List[Dict[str, Any]],
    processos_pais: List[Dict[str, Any]],
    envolvidos_e_parceiros: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Renderiza a aba de Dados Básicos do modal.
    
    Args:
        state: Estado do modal
        dados: Dados do processo (se edição)
        todas_pessoas: Lista de todas as pessoas (clientes)
        todos_casos: Lista de todos os casos
        usuarios_internos: Lista de usuários internos já carregada
        processos_pais: Lista de processos pais já carregada
        envolvidos_e_parceiros: Lista de envolvidos e parceiros para Parte Contrária e Outros Envolvidos
        
    Returns:
        Dicionário com referências aos campos criados
    """
    # Fallback para compatibilidade
    if envolvidos_e_parceiros is None:
        envolvidos_e_parceiros = []
    # Mapeamento de cores para tags
    TAG_COLORS = {
        'clients': '#4CAF50',
        'opposing': '#F44336',
        'others': '#2196F3',
        'cases': '#9C27B0'
    }

    # Helper para refresh chips (ainda usado por Clientes/Casos/Processo Pai)
    def refresh_chips(container, items, tag_type, source_list):
        safe_source = source_list or []
        chip_color = TAG_COLORS.get(tag_type, '#6B7280')
        container.clear()
        with container:
            with ui.row().classes('w-full gap-1 flex-wrap min-h-8'):
                for item in items:
                    short = get_short_name(item, safe_source) if safe_source else item
                    with ui.badge(short).classes('pr-1').style(f'background-color: {chip_color}; color: white;'):
                        ui.button(
                            icon='close',
                            on_click=lambda i=item: remove_item(items, i, container, tag_type, source_list)
                        ).props('flat dense round size=xs color=white')
    
    def remove_item(list_ref, item, container, tag_type, source_list):
        if item in list_ref:
            list_ref.remove(item)
            refresh_chips(container, list_ref, tag_type, source_list)
    
    def add_item(select, list_ref, container, tag_type, source_list):
        val = select.value
        if not val or val == '-' or val == '— Nenhum envolvido/parceiro cadastrado —':
            return
        
        if val in list_ref:
            ui.notify('Item já adicionado', type='warning', timeout=1500)
            return
        
        # O valor selecionado já é o display_name
        list_ref.append(val)
        select.value = None
        refresh_chips(container, list_ref, tag_type, source_list)
        ui.notify(f'Adicionado: {val}', type='positive', timeout=1500)
    
    # Helper para formatar opção de processo (título + número)
    def format_process_option(proc: dict) -> str:
        """Formata opção de processo para dropdown: Título (Número)"""
        titulo = proc.get('titulo', '') or 'Sem título'
        numero = proc.get('numero', '')
        if numero:
            return f"{titulo} ({numero})"
        return titulo
    
    # Helper para processos pais (suporta múltiplos)
    def get_process_id_from_option(option: str) -> str:
        """Extrai ID do processo da opção selecionada."""
        if ' | ' in option:
            return option.split(' | ')[-1].strip()
        return ''
    
    def get_process_option_with_id(proc: dict) -> str:
        """Retorna opção formatada com ID para matching: Título (Número) | ID"""
        display = format_process_option(proc)
        proc_id = proc.get('_id', '')
        return f"{display} | {proc_id}"
    
    with ui.column().classes('w-full gap-4'):
        # SEÇÃO 1 - Identificação do Processo
        with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
            ui.label('📋 Identificação do Processo').classes('text-lg font-bold mb-3')
            with ui.column().classes('w-full gap-4'):
                with ui.row().classes('w-full gap-4 items-start'):
                    title_input = ui.input(make_required_label('Título do Processo')).classes('flex-grow').props('outlined dense')
                    number_input = ui.input(make_required_label('Número do Processo')).classes('w-48').props('outlined dense')
                
                with ui.row().classes('w-full gap-4 items-center'):
                    link_input = ui.input('Link do Processo').classes('flex-grow').props('outlined dense')
                    
                    def open_link():
                        link = link_input.value.strip()
                        if link:
                            if not link.startswith(('http://', 'https://')):
                                link = 'https://' + link
                            ui.run_javascript(f'window.open("{link}", "_blank")')
                    
                    open_link_btn = ui.button('Abrir', icon='open_in_new', on_click=open_link).props('dense size=sm color=primary')
                    
                    def update_button_state():
                        if link_input.value and link_input.value.strip():
                            open_link_btn.props(remove='disabled')
                        else:
                            open_link_btn.props(add='disabled')
                    
                    link_input.on('input', update_button_state)
                    update_button_state()
                
                type_select = ui.select(
                    TIPOS_PROCESSO,
                    label=make_required_label('Tipo de processo'),
                    value=_validar_tipo_processo(dados.get('tipo', '') or '')
                ).classes('w-full').props('outlined dense')
                
                # Data de Abertura
                with ui.row().classes('items-center gap-2'):
                    data_abertura_input = ui.input(
                        'Data de Abertura',
                        placeholder='Ex: 2008, 09/2008, 05/09/2008',
                        value=dados.get('data_abertura', '')
                    ).classes('w-56').props('outlined dense')
                    
                    def validate_approximate_date(value: str) -> bool:
                        if not value or value.strip() == '':
                            return True
                        value = value.strip()
                        if len(value) == 4 and value.isdigit():
                            return 1900 <= int(value) <= 2100
                        if len(value) == 7 and '/' in value:
                            parts = value.split('/')
                            if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) == 4:
                                try:
                                    return 1 <= int(parts[0]) <= 12 and 1900 <= int(parts[1]) <= 2100
                                except ValueError:
                                    return False
                        if len(value) == 10 and value.count('/') == 2:
                            try:
                                datetime.strptime(value, '%d/%m/%Y')
                                return True
                            except ValueError:
                                return False
                        return False
                    
                    data_abertura_input.validation = {'Formato inválido': validate_approximate_date}
                    
                    # Menu popup para seleção de data
                    with ui.menu().props('anchor="bottom left" self="top left"') as date_menu:
                        with ui.card().classes('p-4 w-72'):
                            ui.label('📅 Data Aproximada').classes('text-base font-bold mb-2')
                            
                            date_type_sel = ui.select(
                                options={
                                    'full': '📆 Data completa',
                                    'month_year': '📅 Mês e ano',
                                    'year_only': '📋 Apenas ano'
                                },
                                value='full',
                                label='Precisão'
                            ).classes('w-full mb-2').props('outlined dense')
                            
                            day_sel = ui.select(
                                options=[str(i).zfill(2) for i in range(1, 32)],
                                label='Dia',
                                value='01'
                            ).classes('w-full mb-2').props('outlined dense')
                            
                            month_opts = {
                                '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março',
                                '04': 'Abril', '05': 'Maio', '06': 'Junho',
                                '07': 'Julho', '08': 'Agosto', '09': 'Setembro',
                                '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
                            }
                            month_sel = ui.select(
                                options=month_opts,
                                label='Mês',
                                value='01'
                            ).classes('w-full mb-2').props('outlined dense')
                            
                            year_opts = [str(y) for y in range(datetime.now().year, 1949, -1)]
                            year_sel = ui.select(
                                options=year_opts,
                                label='Ano',
                                value=str(datetime.now().year)
                            ).classes('w-full mb-3').props('outlined dense')
                            
                            def on_type_change():
                                t = date_type_sel.value
                                day_sel.visible = (t == 'full')
                                month_sel.visible = (t in ['full', 'month_year'])
                            
                            date_type_sel.on_value_change(on_type_change)
                            
                            def apply_selected_date():
                                t = date_type_sel.value
                                if t == 'full':
                                    data_abertura_input.value = f"{day_sel.value}/{month_sel.value}/{year_sel.value}"
                                elif t == 'month_year':
                                    data_abertura_input.value = f"{month_sel.value}/{year_sel.value}"
                                else:
                                    data_abertura_input.value = year_sel.value
                                date_menu.close()
                            
                            with ui.row().classes('w-full justify-end gap-2'):
                                ui.button('Cancelar', on_click=date_menu.close).props('flat dense')
                                ui.button('OK', on_click=apply_selected_date).props('color=primary dense')
                    
                    ui.button(icon='edit_calendar', on_click=date_menu.open).props('flat dense round').tooltip('Selecionar data aproximada')
                
                # Prioridade
                prioridade_select = ui.select(
                    CODIGOS_PRIORIDADE,
                    label='Prioridade',
                    value=_validar_prioridade(dados.get('prioridade', '') or '')
                ).classes('w-full').props('outlined dense')
                
                # Responsável pelo Processo (usa lista já carregada)
                responsavel_options = [''] + [u.get('nome', u.get('email', '')) for u in usuarios_internos]
                
                # Determina valor inicial do responsável
                responsavel_val_inicial = dados.get('responsavel_nome', '') or dados.get('responsavel', '')
                # Se for UID, converte para nome
                if responsavel_val_inicial and responsavel_val_inicial not in [u.get('nome', '') for u in usuarios_internos]:
                    usuario_resp = next((u for u in usuarios_internos if u.get('uid') == responsavel_val_inicial), None)
                    if usuario_resp:
                        responsavel_val_inicial = usuario_resp.get('nome', '')
                
                responsavel_select = ui.select(
                    options=responsavel_options,
                    label='Responsável pelo Processo',
                    value=responsavel_val_inicial
                ).classes('w-full').props('outlined dense clearable')
        
        # SEÇÃO 2 - Partes Envolvidas
        with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
            ui.label('👥 Partes Envolvidas').classes('text-lg font-bold mb-3')
            with ui.column().classes('w-full gap-4'):
                # Clientes
                client_options = [format_option_for_search(c) for c in todas_pessoas]
                with ui.row().classes('w-full gap-4'):
                    with ui.column().classes('flex-1 gap-2'):
                        with ui.row().classes('w-full gap-2 items-center'):
                            client_sel = ui.select(
                                client_options or ['-'],
                                label=make_required_label('Clientes'),
                                with_input=True
                            ).classes('flex-grow').props('dense outlined')
                            ui.button(
                                icon='add',
                                on_click=lambda: add_item(client_sel, state['selected_clients'], client_chips, 'clients', todas_pessoas)
                            ).props('flat dense').style('color: #4CAF50;')
                        client_chips = ui.column().classes('w-full')
                    
                    # Parte Contrária (usa envolvidos e parceiros, não clientes)
                    # CORREÇÃO MutationObserver: ui.select com with_input=True cria autocomplete interno
                    # que usa MutationObserver. Adicionado tratamento robusto para evitar erros
                    # quando componente é destruído durante digitação ou navegação entre abas.
                    opposing_options = [format_option_for_search(p) for p in envolvidos_e_parceiros]
                    with ui.column().classes('flex-1 gap-2'):
                        opposing_sel = ui.select(
                            opposing_options or [],
                            label='Parte Contrária',
                            value=state.get('selected_opposing', []) or [],
                            with_input=True,  # Cria autocomplete interno (pode causar MutationObserver)
                            multiple=True,
                        ).classes('w-full').props('dense outlined use-chips')

                        def _sync_opposing(_e=None):
                            """
                            Sincroniza valor do select com o state.
                            
                            CORREÇÃO MutationObserver (CRÍTICO):
                            O ui.select com with_input=True cria um autocomplete interno que usa
                            MutationObserver para detectar mudanças no DOM. Quando o componente
                            é destruído (navegação entre abas, fechamento do modal, etc.), o observer
                            ainda tenta acessar elementos que não existem mais, causando o erro:
                            "TypeError: Failed to execute 'observe' on 'MutationObserver': parameter 1 is not of type 'Node'"
                            
                            Solução: Validação robusta em múltiplas camadas antes de qualquer acesso
                            a propriedades do componente. Todos os erros são silenciosamente ignorados
                            para não interromper a experiência do usuário.
                            """
                            try:
                                # Validação 1: Verifica se referência do componente existe
                                if not opposing_sel:
                                    return
                                
                                # Validação 2: Verifica se componente tem propriedade value
                                if not hasattr(opposing_sel, 'value'):
                                    return
                                
                                # Validação 3: Acessa valor com proteção adicional
                                # Usa try-except interno para capturar erros específicos de acesso
                                try:
                                    valor_atual = opposing_sel.value
                                    if valor_atual is not None:
                                        # Garante que é lista
                                        if isinstance(valor_atual, list):
                                            state['selected_opposing'] = valor_atual
                                        else:
                                            state['selected_opposing'] = [valor_atual]
                                    else:
                                        state['selected_opposing'] = []
                                except (AttributeError, TypeError, RuntimeError, KeyError):
                                    # Erro ao acessar value - componente pode estar sendo destruído
                                    # Silenciosamente ignora - não é erro crítico
                                    return
                                    
                            except (AttributeError, TypeError):
                                # Ignora erros de MutationObserver ou componente destruído
                                # Comportamento esperado durante navegação entre abas ou fechamento do modal
                                pass
                            except Exception as ex:
                                # Log apenas erros verdadeiramente inesperados
                                # Erros de MutationObserver são silenciosamente ignorados
                                error_str = str(ex)
                                if 'MutationObserver' not in error_str and 'Node' not in error_str and 'observe' not in error_str:
                                    import logging
                                    logger = logging.getLogger(__name__)
                                    logger.debug(f"Erro ao sincronizar parte contrária (não-MutationObserver): {ex}")

                        # Configura evento com tratamento robusto de erros
                        # CORREÇÃO: Tenta múltiplas formas de binding para garantir funcionamento
                        evento_configurado = False
                        
                        # Método 1: on_value_change (padrão NiceGUI)
                        try:
                            opposing_sel.on_value_change(_sync_opposing)
                            _sync_opposing()  # Sincroniza estado inicial
                            evento_configurado = True
                        except Exception as ex:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.debug(f"on_value_change falhou, tentando fallback: {ex}")
                        
                        # Método 2: Fallback com evento Vue direto
                        if not evento_configurado:
                            try:
                                opposing_sel.on('update:model-value', _sync_opposing)
                                _sync_opposing()
                                evento_configurado = True
                            except Exception as ex:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.debug(f"Fallback update:model-value também falhou: {ex}")
                        
                        # Método 3: Sincronização manual via timer (último recurso)
                        if not evento_configurado:
                            import asyncio
                            async def sync_periodico():
                                """Sincroniza periodicamente se eventos não funcionarem"""
                                while True:
                                    await asyncio.sleep(0.5)  # A cada 500ms
                                    try:
                                        _sync_opposing()
                                    except:
                                        break  # Para se componente foi destruído
                            
                            # Não inicia timer automático - apenas como fallback se necessário
                            # asyncio.create_task(sync_periodico())
                
                # Outros Envolvidos (usa envolvidos e parceiros, não clientes)
                others_options = [format_option_for_search(p) for p in envolvidos_e_parceiros]
                with ui.column().classes('w-full gap-2'):
                    others_sel = ui.select(
                        others_options or [],
                    label='Outros Envolvidos',
                        value=state.get('selected_others', []) or [],
                        with_input=True,
                        multiple=True,
                    ).classes('w-full').props('dense outlined use-chips')

                    def _sync_others(_e=None):
                        """
                        Sincroniza valor do select com o state.
                        
                        CORREÇÃO: Adicionado try-except para evitar erro de MutationObserver
                        que ocorre quando o componente é destruído/recriado durante digitação.
                        """
                        try:
                            # Valida se o componente ainda existe antes de acessar
                            if others_sel and hasattr(others_sel, 'value'):
                                state['selected_others'] = others_sel.value or []
                        except (AttributeError, TypeError) as ex:
                            # Ignora erros de MutationObserver ou componente destruído
                            pass
                        except Exception as ex:
                            # Log apenas erros inesperados
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Erro ao sincronizar outros envolvidos: {ex}")

                    # Usa on_value_change com tratamento de erro
                    try:
                        others_sel.on_value_change(_sync_others)
                        _sync_others()
                    except Exception as ex:
                        # Se falhar ao configurar evento, tenta alternativa
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Erro ao configurar evento on_value_change: {ex}")
                        # Fallback: usa evento 'update:model-value' se disponível
                        try:
                            others_sel.on('update:model-value', _sync_others)
                        except:
                            pass
        
        # SEÇÃO 3 - Vínculos
        with ui.card().classes('w-full mb-4 p-4').style('border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'):
            ui.label('🔗 Vínculos').classes('text-lg font-bold mb-3')
            with ui.column().classes('w-full gap-4'):
                # Processos Pai (suporta múltiplos)
                # Filtra processos para não incluir o próprio processo
                current_process_id = state.get('process_id')
                parent_options = [
                    format_process_option(p) 
                    for p in processos_pais 
                    if p.get('_id') != current_process_id
                ]
                
                with ui.column().classes('w-full gap-2'):
                    parent_process_sel = ui.select(
                        options=parent_options or [],
                        label='Processos Pai (opcional - um processo pode ter múltiplos pais)',
                        value=state.get('selected_parent_processes', []) or [],
                        with_input=True,
                        multiple=True,
                    ).classes('w-full').props('dense outlined use-chips')
                    
                    def _sync_parent_processes(_e=None):
                        """
                        Sincroniza valor do select com o state.
                        
                        CORREÇÃO: Adicionado try-except para evitar erro de MutationObserver.
                        """
                        try:
                            if parent_process_sel and hasattr(parent_process_sel, 'value'):
                                state['selected_parent_processes'] = parent_process_sel.value or []
                        except (AttributeError, TypeError):
                            # Ignora erros de MutationObserver ou componente destruído
                            pass
                        except Exception as ex:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Erro ao sincronizar processos pai: {ex}")
                    
                    # Usa on_value_change com tratamento de erro
                    try:
                        parent_process_sel.on_value_change(_sync_parent_processes)
                        _sync_parent_processes()
                    except Exception as ex:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Erro ao configurar evento on_value_change: {ex}")
                        try:
                            parent_process_sel.on('update:model-value', _sync_parent_processes)
                        except:
                            pass
                
                # Casos Vinculados
                case_options = [c.get('titulo', '') for c in todos_casos if c.get('titulo')]
                with ui.row().classes('w-full gap-2 items-center'):
                    cases_sel = ui.select(
                        case_options or ['-'],
                        label='Casos Vinculados',
                        with_input=True
                    ).classes('flex-grow').props('dense outlined')
                    ui.button(
                        icon='add',
                        on_click=lambda: add_item(cases_sel, state['selected_cases'], cases_chips, 'cases', None)
                    ).props('flat dense').style('color: #9C27B0;')
                cases_chips = ui.column().classes('w-full')
    
    # Retorna referências aos campos
    return {
        'title_input': title_input,
        'number_input': number_input,
        'link_input': link_input,
        'type_select': type_select,
        'data_abertura_input': data_abertura_input,
        'prioridade_select': prioridade_select,
        'responsavel_select': responsavel_select,
        'client_sel': client_sel,
        'opposing_sel': opposing_sel,
        'others_sel': others_sel,
        'cases_sel': cases_sel,
        'parent_process_sel': parent_process_sel,
        'client_chips': client_chips,
        'cases_chips': cases_chips,
        'refresh_chips': refresh_chips,
        'format_process_option': format_process_option,
    }
