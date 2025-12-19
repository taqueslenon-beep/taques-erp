"""
Modal principal de criação e edição de processos (Visão Geral).
Orquestra todas as abas do modal.
"""
from nicegui import ui
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from mini_erp.core import PRIMARY_COLOR, get_display_name
from mini_erp.firebase_config import ensure_firebase_initialized, get_auth
from mini_erp.storage import obter_display_name
from ..database import (
    criar_processo, atualizar_processo, excluir_processo,
    buscar_processo, listar_processos_pais
)
from ..models import validar_processo, criar_processo_vazio
from ..cache import cached_call
from ...pessoas.database import listar_pessoas
from ...casos.database import listar_casos
from .aba_dados_basicos import render_aba_dados_basicos
from .aba_dados_juridicos import render_aba_dados_juridicos
from .aba_relatorio import render_aba_relatorio
from .aba_estrategia import render_aba_estrategia
from .aba_cenarios import render_aba_cenarios
from .aba_protocolos import render_aba_protocolos

# CSS para sidebar
PROCESSES_TABLE_CSS = '''
    .process-sidebar-tabs .q-tab {
        justify-content: flex-start !important;
        flex-direction: row !important;
        padding: 6px 12px !important;
        min-height: 32px !important;
        height: 32px !important;
        font-size: 11px !important;
        color: white !important;
        border-radius: 0 !important;
        text-transform: none !important;
        text-align: left !important;
        align-items: center !important;
    }
    .process-sidebar-tabs .q-tab:hover {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
    }
    .process-sidebar-tabs .q-tab--active {
        background: rgba(255,255,255,0.12) !important;
        color: white !important;
        border-left: 2px solid rgba(255,255,255,0.8) !important;
    }
    .process-sidebar-tabs .q-tab__content {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        width: 100% !important;
    }
    .process-sidebar-tabs .q-tab__icon {
        font-size: 16px !important;
        margin: 0 !important;
        color: white !important;
        align-self: center !important;
        flex-shrink: 0 !important;
    }
    .process-sidebar-tabs .q-tab__label {
        font-weight: 400 !important;
        letter-spacing: 0.2px !important;
        color: white !important;
        text-align: left !important;
        align-self: center !important;
    }
    .process-sidebar-tabs .q-tabs__content {
        overflow: visible !important;
    }
    .process-sidebar-tabs .q-tab__indicator {
        display: none !important;
    }
'''


def carregar_dados_modal():
    """
    Carrega todos os dados necessários em paralelo usando cache.
    
    Returns:
        Dicionário com 'pessoas', 'casos', 'usuarios', 'processos_pais'
    """
    t0 = time.time()
    print(f"[MODAL] Iniciando carregamento paralelo...")
    
    resultados = {
        'pessoas': [],
        'casos': [],
        'usuarios': [],
        'processos_pais': []
    }
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(lambda: cached_call('pessoas', listar_pessoas)): 'pessoas',
            executor.submit(lambda: cached_call('casos', listar_casos)): 'casos',
            executor.submit(lambda: cached_call('usuarios', listar_usuarios_internos)): 'usuarios',
            executor.submit(lambda: cached_call('processos_pais', listar_processos_pais)): 'processos_pais',
        }
        
        for future in as_completed(futures):
            key = futures[future]
            try:
                resultados[key] = future.result()
                print(f"[MODAL] {key}: {time.time() - t0:.2f}s")
            except Exception as e:
                print(f"[MODAL] Erro ao carregar {key}: {e}")
                import traceback
                traceback.print_exc()
                resultados[key] = []
    
    print(f"[MODAL] Total carregamento: {time.time() - t0:.2f}s")
    return resultados


def listar_usuarios_internos() -> List[Dict[str, Any]]:
    """
    Lista usuários internos do Firebase Auth.
    Retorna lista de dicts com uid, email, nome, nome_exibicao.
    
    Returns:
        Lista de dicionários com informações dos usuários
    """
    try:
        # Garante que Firebase está inicializado
        ensure_firebase_initialized()
        
        # Obtém instância do Auth
        auth_instance = get_auth()
        
        # Lista usuários
        usuarios = []
        page = auth_instance.list_users()
        
        while page:
            for user in page.users:
                # Ignora usuários desabilitados
                if user.disabled:
                    continue
                
                # Obtém nome de exibição
                try:
                    display_name = obter_display_name(user.uid)
                    # Se retornou "Usuário" (fallback padrão), usa parte do email
                    if display_name == "Usuário":
                        display_name = user.email.split('@')[0] if user.email else '-'
                except Exception as e:
                    print(f"Erro ao obter display_name para {user.uid}: {e}")
                    # Fallback: usa parte do email
                    display_name = user.email.split('@')[0] if user.email else '-'
                
                usuarios.append({
                    'uid': user.uid,
                    'email': user.email or '',
                    'nome': display_name,
                    'nome_exibicao': display_name  # Para compatibilidade
                })
            
            try:
                page = page.get_next_page()
            except StopIteration:
                break
        
        # Ordena alfabeticamente por nome
        usuarios.sort(key=lambda u: u.get('nome', '').lower())
        
        return usuarios
    except Exception as e:
        print(f"Erro ao listar usuários internos: {e}")
        import traceback
        traceback.print_exc()
        return []


def abrir_modal_processo(processo: Optional[dict] = None, on_save: Optional[Callable] = None):
    """
    Abre dialog para criar ou editar um processo.
    
    Args:
        processo: Dicionário com dados do processo (None para criar novo)
        on_save: Callback executado após salvar com sucesso
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [DEBUG] Abrindo modal para processo: {processo is not None}")
    if processo:
        print(f"[{timestamp}] [DEBUG] Dados recebidos: {list(processo.keys())}")
    
    is_edicao = processo is not None
    dados = processo.copy() if processo else criar_processo_vazio()
    
    # Estado local
    state = {
        'is_editing': is_edicao,
        'process_id': dados.get('_id') if is_edicao else None,
        'processo_pai_id': dados.get('processo_pai_id', '') or '',
        'scenarios': [],
        'protocols': dados.get('protocols', []) if isinstance(dados.get('protocols'), list) else [],
        'selected_clients': dados.get('clientes', []) if isinstance(dados.get('clientes'), list) else [],
        'selected_opposing': dados.get('parte_contraria', '') if isinstance(dados.get('parte_contraria'), str) else (dados.get('parte_contraria', []) if isinstance(dados.get('parte_contraria'), list) else []),
        'selected_others': [],
        'selected_cases': [dados.get('caso_titulo')] if dados.get('caso_titulo') else [],
    }
    
    # Converter parte contrária de string para lista se necessário
    if isinstance(state['selected_opposing'], str) and state['selected_opposing']:
        state['selected_opposing'] = [state['selected_opposing']]
    
    # Carregar dados auxiliares em paralelo (com cache)
    dados_carregados = carregar_dados_modal()
    todas_pessoas = dados_carregados['pessoas']
    todos_casos = dados_carregados['casos']
    usuarios_internos = dados_carregados['usuarios']
    processos_pais = dados_carregados['processos_pais']
    
    # CSS do modal
    ui.add_head_html(f'<style>{PROCESSES_TABLE_CSS}</style>')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl p-0 overflow-hidden relative').style('height: 80vh; max-height: 80vh;'):
        with ui.row().classes('w-full h-full gap-0'):
            # Sidebar com abas
            with ui.column().classes('h-full shrink-0 justify-between').style(f'width: 170px; background: {PRIMARY_COLOR};'):
                with ui.column().classes('w-full gap-0'):
                    dialog_title = ui.label('NOVO PROCESSO' if not is_edicao else 'EDITAR PROCESSO').classes(
                        'text-xs font-medium px-3 py-2 text-white/80 uppercase tracking-wide'
                    )
                    
                    with ui.tabs().props('vertical dense no-caps inline-label').classes('w-full process-sidebar-tabs') as tabs:
                        tab_basic = ui.tab('Dados básicos', icon='description')
                        tab_legal = ui.tab('Dados jurídicos', icon='gavel')
                        tab_relatory = ui.tab('Relatório', icon='article')
                        tab_strategy = ui.tab('Estratégia', icon='lightbulb')
                        tab_scenarios = ui.tab('Cenários', icon='analytics')
                        tab_protocols = ui.tab('Protocolos', icon='history')
            
            # Content - LAZY LOADING das abas
            # Variáveis para controlar abas já renderizadas
            abas_renderizadas = {
                'basic': False,
                'legal': False,
                'relatory': False,
                'strategy': False,
                'scenarios': False,
                'protocols': False
            }
            
            # Containers para referências das abas
            aba_basicos_refs = {}
            aba_juridicos_refs = {}
            aba_relatorio_refs = {}
            aba_estrategia_refs = {}
            aba_cenarios_refs = {}
            aba_protocolos_refs = {}
            
            # Containers para lazy loading
            container_legal = None
            container_relatory = None
            container_strategy = None
            container_scenarios = None
            container_protocols = None
            
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_basic).classes('w-full h-full p-4 bg-transparent') as panels:
                    # TAB 1: DADOS BÁSICOS - renderiza imediatamente (é a aba inicial)
                    with ui.tab_panel(tab_basic):
                        try:
                            aba_basicos_refs = render_aba_dados_basicos(
                                state, dados, todas_pessoas, todos_casos, usuarios_internos, processos_pais
                            )
                            abas_renderizadas['basic'] = True
                        except Exception as e:
                            print(f"[ERRO CRÍTICO] Erro ao criar aba Dados Básicos: {e}")
                            import traceback
                            traceback.print_exc()
                            with ui.column().classes('w-full gap-4 p-4'):
                                ui.label('Erro ao carregar aba Dados Básicos').classes('text-red-500 font-bold text-lg')
                                ui.label(f'Erro: {str(e)}').classes('text-red-400 text-sm')
                    
                    # TAB 2: DADOS JURÍDICOS - lazy
                    with ui.tab_panel(tab_legal):
                        container_legal = ui.column().classes('w-full')
                        with container_legal:
                            ui.label('Carregando...').classes('text-gray-400')
                    
                    # TAB 3: RELATÓRIO - lazy
                    with ui.tab_panel(tab_relatory):
                        container_relatory = ui.column().classes('w-full')
                        with container_relatory:
                            ui.label('Carregando...').classes('text-gray-400')
                    
                    # TAB 4: ESTRATÉGIA - lazy
                    with ui.tab_panel(tab_strategy):
                        container_strategy = ui.column().classes('w-full')
                        with container_strategy:
                            ui.label('Carregando...').classes('text-gray-400')
                    
                    # TAB 5: CENÁRIOS - lazy
                    with ui.tab_panel(tab_scenarios):
                        container_scenarios = ui.column().classes('w-full')
                        with container_scenarios:
                            ui.label('Carregando...').classes('text-gray-400')
                    
                    # TAB 6: PROTOCOLOS - lazy
                    with ui.tab_panel(tab_protocols):
                        container_protocols = ui.column().classes('w-full')
                        with container_protocols:
                            ui.label('Carregando...').classes('text-gray-400')
                    
                    # Handler para mudança de aba (lazy loading)
                    def on_tab_change(e):
                        """Renderiza aba sob demanda quando usuário clica nela."""
                        current_tab = panels.value
                        
                        if current_tab == tab_legal and not abas_renderizadas['legal']:
                            print(f"[MODAL] Renderizando aba: legal")
                            container_legal.clear()
                            with container_legal:
                                nonlocal aba_juridicos_refs
                                aba_juridicos_refs = render_aba_dados_juridicos(dados)
                            abas_renderizadas['legal'] = True
                        elif current_tab == tab_relatory and not abas_renderizadas['relatory']:
                            print(f"[MODAL] Renderizando aba: relatory")
                            container_relatory.clear()
                            with container_relatory:
                                nonlocal aba_relatorio_refs
                                aba_relatorio_refs = render_aba_relatorio(dados, is_edicao)
                            abas_renderizadas['relatory'] = True
                        elif current_tab == tab_strategy and not abas_renderizadas['strategy']:
                            print(f"[MODAL] Renderizando aba: strategy")
                            container_strategy.clear()
                            with container_strategy:
                                nonlocal aba_estrategia_refs
                                aba_estrategia_refs = render_aba_estrategia(dados, is_edicao)
                            abas_renderizadas['strategy'] = True
                        elif current_tab == tab_scenarios and not abas_renderizadas['scenarios']:
                            print(f"[MODAL] Renderizando aba: scenarios")
                            container_scenarios.clear()
                            with container_scenarios:
                                nonlocal aba_cenarios_refs
                                aba_cenarios_refs = render_aba_cenarios(state)
                            abas_renderizadas['scenarios'] = True
                        elif current_tab == tab_protocols and not abas_renderizadas['protocols']:
                            print(f"[MODAL] Renderizando aba: protocols")
                            container_protocols.clear()
                            with container_protocols:
                                nonlocal aba_protocolos_refs
                                aba_protocolos_refs = render_aba_protocolos(state)
                            abas_renderizadas['protocols'] = True
                    
                    # Registra handler de mudança de aba
                    panels.on('update:model-value', on_tab_change)
            
            # Footer Actions
            with ui.row().classes('absolute bottom-0 right-0 p-4 gap-2 z-10').style('background: rgba(249, 250, 251, 0.95); border-radius: 8px 0 0 0;'):
                
                def do_delete():
                    if state['is_editing'] and state.get('process_id'):
                        if excluir_processo(state['process_id']):
                            ui.notify(f'Processo excluído!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao excluir processo.', type='negative')
                    else:
                        ui.notify('Não foi possível identificar o processo para exclusão.', type='warning')
                
                delete_btn = ui.button('EXCLUIR', icon='delete', on_click=do_delete).props('color=red').classes('hidden font-bold shadow-lg' if not is_edicao else 'font-bold shadow-lg')
                
                def do_save():
                    # Coletar dados do formulário
                    selected_cases_ids = []
                    caso_titulo = ''
                    if state['selected_cases']:
                        # Buscar ID do caso pelo título
                        caso_obj = next((c for c in todos_casos if c.get('titulo') in state['selected_cases']), None)
                        if caso_obj:
                            selected_cases_ids = [caso_obj.get('_id')]
                            caso_titulo = caso_obj.get('titulo', '')
                    
                    processo_pai_id = state.get('processo_pai_id', '') or ''
                    processo_pai_titulo = ''
                    if processo_pai_id:
                        proc_obj = buscar_processo(processo_pai_id)
                        if proc_obj:
                            processo_pai_titulo = proc_obj.get('titulo', '')
                    
                    # Normalizar parte contrária
                    parte_contraria = ''
                    if isinstance(state['selected_opposing'], list):
                        parte_contraria = ', '.join(state['selected_opposing']) if state['selected_opposing'] else ''
                    else:
                        parte_contraria = str(state['selected_opposing']) if state['selected_opposing'] else ''
                    
                    # Buscar UID do responsável pelo nome (usa lista já carregada)
                    responsavel_uid = ''
                    responsavel_nome = ''
                    if aba_basicos_refs and 'responsavel_select' in aba_basicos_refs:
                        responsavel_nome = aba_basicos_refs['responsavel_select'].value or ''
                        if responsavel_nome:
                            usuario_responsavel = next((u for u in usuarios_internos if u.get('nome') == responsavel_nome), None)
                            if usuario_responsavel:
                                responsavel_uid = usuario_responsavel.get('uid', '')
                    
                    novos_dados = {
                        'titulo': aba_basicos_refs.get('title_input', {}).value.strip() if aba_basicos_refs.get('title_input') and aba_basicos_refs['title_input'].value else '',
                        'numero': aba_basicos_refs.get('number_input', {}).value.strip() if aba_basicos_refs.get('number_input') and aba_basicos_refs['number_input'].value else '',
                        'tipo': aba_basicos_refs.get('type_select', {}).value if aba_basicos_refs.get('type_select') else 'Judicial',
                        'sistema_processual': aba_juridicos_refs.get('system_select', {}).value if aba_juridicos_refs.get('system_select') else '',
                        'area': aba_juridicos_refs.get('area_select', {}).value if aba_juridicos_refs.get('area_select') else '',
                        'estado': aba_juridicos_refs.get('estado_select', {}).value if aba_juridicos_refs.get('estado_select') else '',
                        'comarca': aba_juridicos_refs.get('comarca_input', {}).value.strip() if aba_juridicos_refs.get('comarca_input') and aba_juridicos_refs['comarca_input'].value else '',
                        'vara': aba_juridicos_refs.get('vara_input', {}).value.strip() if aba_juridicos_refs.get('vara_input') and aba_juridicos_refs['vara_input'].value else '',
                        'caso_id': selected_cases_ids[0] if selected_cases_ids else '',
                        'caso_titulo': caso_titulo,
                        'clientes': state['selected_clients'].copy(),
                        'clientes_nomes': [
                            get_display_name(next((p for p in todas_pessoas if get_display_name(p) == cid or p.get('_id') == cid), {}))
                            for cid in state['selected_clients']
                        ],
                        'parte_contraria': parte_contraria,
                        'processo_pai_id': processo_pai_id,
                        'processo_pai_titulo': processo_pai_titulo,
                        'status': aba_juridicos_refs.get('status_select', {}).value if aba_juridicos_refs.get('status_select') else 'Ativo',
                        'resultado': aba_juridicos_refs.get('result_select', {}).value if aba_juridicos_refs.get('result_select') and aba_juridicos_refs['result_select'].value and aba_juridicos_refs['result_select'].value != 'Pendente' else 'Pendente',
                        'data_abertura': aba_basicos_refs.get('data_abertura_input', {}).value.strip() if aba_basicos_refs.get('data_abertura_input') and aba_basicos_refs['data_abertura_input'].value else '',
                        'responsavel': responsavel_uid,
                        'responsavel_nome': responsavel_nome,
                        'observacoes': aba_estrategia_refs.get('observations_input', {}).value if aba_estrategia_refs.get('observations_input') else '',
                        'cenario_melhor': '',
                        'cenario_intermediario': '',
                        'cenario_pior': '',
                        'scenarios': state.get('scenarios', []),
                        'relatory_facts': aba_relatorio_refs.get('relatory_facts_input', {}).value if aba_relatorio_refs.get('relatory_facts_input') else '',
                        'relatory_timeline': aba_relatorio_refs.get('relatory_timeline_input', {}).value if aba_relatorio_refs.get('relatory_timeline_input') else '',
                        'relatory_documents': aba_relatorio_refs.get('relatory_documents_input', {}).value if aba_relatorio_refs.get('relatory_documents_input') else '',
                        'strategy_objectives': aba_estrategia_refs.get('objectives_input', {}).value if aba_estrategia_refs.get('objectives_input') else '',
                        'legal_thesis': aba_estrategia_refs.get('thesis_input', {}).value if aba_estrategia_refs.get('thesis_input') else '',
                        'strategy_observations': aba_estrategia_refs.get('observations_input', {}).value if aba_estrategia_refs.get('observations_input') else '',
                        'protocols': state.get('protocols', []),
                    }
                    
                    # Validação
                    valido, erro = validar_processo(novos_dados)
                    if not valido:
                        ui.notify(erro, type='negative')
                        return
                    
                    # Salvar
                    try:
                        if is_edicao:
                            sucesso = atualizar_processo(state['process_id'], novos_dados)
                            msg = 'Processo atualizado com sucesso!'
                        else:
                            processo_id = criar_processo(novos_dados)
                            sucesso = processo_id is not None
                            msg = 'Processo criado com sucesso!'
                        
                        if sucesso:
                            ui.notify(msg, type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao salvar processo.', type='negative')
                    except Exception as e:
                        print(f"Erro ao salvar processo: {e}")
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao salvar: {str(e)}', type='negative')
                
                ui.button('SALVAR', icon='save', on_click=do_save).props('color=primary').classes('font-bold shadow-lg')
        
        # Função auxiliar para converter None para string vazia
        def safe_get(key, default='', fallback_key=None):
            """Retorna valor do campo ou default, convertendo None para string vazia."""
            value = dados.get(key)
            if value is None and fallback_key:
                value = dados.get(fallback_key)
            if value is None or value == '':
                return default
            return str(value) if value else default
        
        # Popular campos após criar o dialog (garante que todos os campos existam)
        def populate_all_fields():
            """Popula todos os campos do formulário com dados do processo."""
            if is_edicao and aba_basicos_refs:
                try:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    processo_id = state.get('process_id') or 'SEM_ID'
                    print(f"[{timestamp}] [MODAL_VG] [POPULAR] Iniciando população de campos para processo ID: {processo_id}")
                    
                    # Campos básicos
                    if 'title_input' in aba_basicos_refs:
                        aba_basicos_refs['title_input'].value = safe_get('titulo', '', 'title')
                    if 'number_input' in aba_basicos_refs:
                        aba_basicos_refs['number_input'].value = safe_get('numero', '', 'number')
                    if 'link_input' in aba_basicos_refs:
                        aba_basicos_refs['link_input'].value = safe_get('link', '')
                    if 'type_select' in aba_basicos_refs:
                        aba_basicos_refs['type_select'].value = safe_get('tipo', 'Judicial') or 'Judicial'
                    if 'data_abertura_input' in aba_basicos_refs:
                        aba_basicos_refs['data_abertura_input'].value = safe_get('data_abertura', '')
                    
                    # Campos jurídicos
                    if 'system_select' in aba_juridicos_refs:
                        aba_juridicos_refs['system_select'].value = safe_get('sistema_processual', '')
                    if 'area_select' in aba_juridicos_refs:
                        aba_juridicos_refs['area_select'].value = safe_get('area', '')
                    if 'estado_select' in aba_juridicos_refs:
                        aba_juridicos_refs['estado_select'].value = safe_get('estado', 'Santa Catarina') or 'Santa Catarina'
                    if 'comarca_input' in aba_juridicos_refs:
                        aba_juridicos_refs['comarca_input'].value = safe_get('comarca', '')
                    if 'vara_input' in aba_juridicos_refs:
                        aba_juridicos_refs['vara_input'].value = safe_get('vara', '')
                    if 'status_select' in aba_juridicos_refs:
                        aba_juridicos_refs['status_select'].value = safe_get('status', 'Ativo') or 'Ativo'
                    if 'result_select' in aba_juridicos_refs:
                        aba_juridicos_refs['result_select'].value = safe_get('resultado', 'Pendente') or 'Pendente'
                    if 'toggle_result' in aba_juridicos_refs:
                        aba_juridicos_refs['toggle_result']()
                    
                    # Campos de relatório
                    if 'relatory_facts_input' in aba_relatorio_refs:
                        aba_relatorio_refs['relatory_facts_input'].value = safe_get('relatory_facts', '')
                    if 'relatory_timeline_input' in aba_relatorio_refs:
                        aba_relatorio_refs['relatory_timeline_input'].value = safe_get('relatory_timeline', '')
                    if 'relatory_documents_input' in aba_relatorio_refs:
                        aba_relatorio_refs['relatory_documents_input'].value = safe_get('relatory_documents', '')
                    
                    # Campos de estratégia
                    if 'objectives_input' in aba_estrategia_refs:
                        aba_estrategia_refs['objectives_input'].value = safe_get('strategy_objectives', '')
                    if 'thesis_input' in aba_estrategia_refs:
                        aba_estrategia_refs['thesis_input'].value = safe_get('legal_thesis', '')
                    if 'observations_input' in aba_estrategia_refs:
                        aba_estrategia_refs['observations_input'].value = safe_get('strategy_observations', '') or safe_get('observacoes', '')
                    
                    # Cenários
                    if dados.get('scenarios') and isinstance(dados.get('scenarios'), list):
                        state['scenarios'] = dados.get('scenarios')
                    else:
                        state['scenarios'] = []
                        if dados.get('cenario_melhor'):
                            state['scenarios'].append({'title': 'Melhor Cenário', 'type': '🟢 Positivo', 'obs': dados.get('cenario_melhor')})
                        if dados.get('cenario_intermediario'):
                            state['scenarios'].append({'title': 'Cenário Intermediário', 'type': '⚪ Neutro', 'obs': dados.get('cenario_intermediario')})
                        if dados.get('cenario_pior'):
                            state['scenarios'].append({'title': 'Pior Cenário', 'type': '🔴 Negativo', 'obs': dados.get('cenario_pior')})
                    
                    # Protocolos
                    if dados.get('protocols') and isinstance(dados.get('protocols'), list):
                        state['protocols'] = dados.get('protocols')
                    else:
                        state['protocols'] = []
                    
                    # Renderizar chips
                    try:
                        if 'refresh_chips' in aba_basicos_refs and 'client_chips' in aba_basicos_refs:
                            aba_basicos_refs['refresh_chips'](aba_basicos_refs['client_chips'], state['selected_clients'], 'clients', todas_pessoas)
                        if isinstance(state['selected_opposing'], list) and 'opposing_chips' in aba_basicos_refs:
                            aba_basicos_refs['refresh_chips'](aba_basicos_refs['opposing_chips'], state['selected_opposing'], 'opposing', todas_pessoas)
                        if 'others_chips' in aba_basicos_refs:
                            aba_basicos_refs['refresh_chips'](aba_basicos_refs['others_chips'], state['selected_others'], 'others', todas_pessoas)
                        if 'cases_chips' in aba_basicos_refs:
                            aba_basicos_refs['refresh_chips'](aba_basicos_refs['cases_chips'], state['selected_cases'], 'cases', None)
                        if state.get('processo_pai_id') and 'refresh_parent_chips' in aba_basicos_refs and 'parent_process_chips' in aba_basicos_refs:
                            aba_basicos_refs['refresh_parent_chips'](aba_basicos_refs['parent_process_chips'], state['processo_pai_id'])
                    except Exception as e:
                        print(f"[MODAL_VG] [POPULAR] ⚠ Erro ao renderizar chips: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    print(f"[{timestamp}] [MODAL_VG] [POPULAR] ✓ População de campos concluída")
                    
                except Exception as e:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] [MODAL_VG] [POPULAR] ❌ Erro ao popular campos: {e}")
                    import traceback
                    traceback.print_exc()
                    ui.notify(f'Erro ao carregar dados do processo: {str(e)}', type='warning')
        
        # Carregar opções de processos pais (usa lista já carregada em paralelo)
        if aba_basicos_refs and 'parent_process_sel' in aba_basicos_refs:
            try:
                parent_options = []
                current_id = state.get('process_id')
                
                for p in processos_pais:
                    proc_id = p.get('_id')
                    if proc_id and proc_id != current_id:
                        title = p.get('titulo') or p.get('numero') or 'Sem título'
                        number = p.get('numero', '')
                        display = f"{title}" + (f" ({number})" if number else "") + f" | {proc_id}"
                        parent_options.append(display)
                
                aba_basicos_refs['parent_process_sel'].options = parent_options if parent_options else ['— Nenhum (processo raiz) —']
            except Exception as e:
                print(f"[MODAL_VG] Erro ao carregar processos pais: {e}")
                import traceback
                traceback.print_exc()
                if 'parent_process_sel' in aba_basicos_refs:
                    aba_basicos_refs['parent_process_sel'].options = ['— Nenhum (processo raiz) —']
        
        # Popular campos após criar o dialog
        if is_edicao:
            try:
                populate_all_fields()
            except Exception as e:
                print(f"[MODAL_VG] Erro ao popular campos: {e}")
                import traceback
                traceback.print_exc()
    
    # Abrir dialog DEPOIS de popular os campos
    dialog.open()


def confirmar_exclusao(processo: dict, on_confirm: Optional[Callable] = None):
    """
    Dialog de confirmação de exclusão de processo.
    
    Args:
        processo: Dicionário com dados do processo a excluir
        on_confirm: Callback executado ao confirmar exclusão
    """
    titulo = processo.get('titulo', 'Processo')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('warning', color='negative', size='32px')
            ui.label('Confirmar Exclusão').classes('text-xl font-bold text-gray-800')
        
        ui.label(f'Deseja realmente excluir o processo "{titulo}"?').classes('text-gray-600 mb-2')
        ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')
            
            def executar_exclusao():
                dialog.close()
                if on_confirm:
                    on_confirm()
            
            ui.button('Excluir', on_click=executar_exclusao).props('color=negative')
    
    dialog.open()

