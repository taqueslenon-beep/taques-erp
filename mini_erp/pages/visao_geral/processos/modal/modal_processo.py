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
from mini_erp.models.prioridade import PRIORIDADE_PADRAO
from ..database import (
    criar_processo, atualizar_processo, excluir_processo,
    buscar_processo, listar_processos_pais
)
from ..models import validar_processo, criar_processo_vazio
from ..cache import cached_call
from ...pessoas.database import listar_pessoas, listar_envolvidos, listar_parceiros
from ...casos.database import listar_casos
from .aba_dados_basicos import render_aba_dados_basicos
from .aba_dados_juridicos import render_aba_dados_juridicos
from .aba_relatorio import render_aba_relatorio
from .aba_estrategia import render_aba_estrategia
from .aba_cenarios import render_aba_cenarios
from .aba_protocolos import render_aba_protocolos
from .aba_chaves_acesso import render_aba_chaves_acesso

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
        Dicionário com 'pessoas', 'casos', 'usuarios', 'processos_pais', 'envolvidos_e_parceiros'
    """
    t0 = time.time()
    print(f"[MODAL] Iniciando carregamento paralelo...")
    
    resultados = {
        'pessoas': [],
        'casos': [],
        'usuarios': [],
        'processos_pais': [],
        'envolvidos': [],
        'parceiros': []
    }
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(lambda: cached_call('pessoas', listar_pessoas)): 'pessoas',
            executor.submit(lambda: cached_call('casos', listar_casos)): 'casos',
            executor.submit(lambda: cached_call('usuarios', listar_usuarios_internos)): 'usuarios',
            executor.submit(lambda: cached_call('processos_pais', listar_processos_pais)): 'processos_pais',
            executor.submit(lambda: cached_call('envolvidos', listar_envolvidos)): 'envolvidos',
            executor.submit(lambda: cached_call('parceiros', listar_parceiros)): 'parceiros',
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
    
    # Combina envolvidos e parceiros em uma única lista
    resultados['envolvidos_e_parceiros'] = resultados['envolvidos'] + resultados['parceiros']
    
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
    
    BUGFIX 2024-12-19: Adicionado tratamento robusto de erros e logging
    detalhado para resolver problema de modal vazio no workspace VG.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [MODAL_VG] ====== ABRINDO MODAL ======")
    print(f"[{timestamp}] [MODAL_VG] Modo: {'EDIÇÃO' if processo else 'CRIAÇÃO'}")
    
    if processo:
        print(f"[{timestamp}] [MODAL_VG] Processo ID: {processo.get('_id', 'SEM_ID')}")
        print(f"[{timestamp}] [MODAL_VG] Título: {processo.get('titulo', 'SEM_TÍTULO')}")
        print(f"[{timestamp}] [MODAL_VG] Campos recebidos: {list(processo.keys())}")
    
    # Validação de dados para modo edição
    if processo and not processo.get('_id'):
        print(f"[{timestamp}] [MODAL_VG] ⚠ ALERTA: Processo recebido sem _id!")
        ui.notify('Erro: Dados do processo incompletos (sem ID).', type='warning')
    
    is_edicao = processo is not None
    
    # Copia dados de forma segura, garantindo que não seja None
    if processo:
        dados = dict(processo)  # Cria cópia segura
        print(f"[{timestamp}] [MODAL_VG] Dados copiados: {len(dados)} campos")
    else:
        dados = criar_processo_vazio()
        print(f"[{timestamp}] [MODAL_VG] Novo processo criado com dados vazios")
    
    def _normalizar_lista_texto(valor: Any) -> List[str]:
        """Normaliza valores (string/list) para lista de strings (sem vazios)."""
        if not valor:
            return []
        if isinstance(valor, list):
            return [str(v).strip() for v in valor if str(v).strip()]
        if isinstance(valor, str):
            # Aceita valores antigos salvos como "A, B, C"
            partes = [p.strip() for p in valor.split(',')]
            return [p for p in partes if p]
        return [str(valor).strip()] if str(valor).strip() else []

    # Carregar dados auxiliares em paralelo (com cache) - ANTES do state para usar no mapeamento
    dados_carregados = carregar_dados_modal()
    todas_pessoas = dados_carregados['pessoas']
    todos_casos = dados_carregados['casos']
    usuarios_internos = dados_carregados['usuarios']
    processos_pais = dados_carregados['processos_pais']
    envolvidos_e_parceiros = dados_carregados['envolvidos_e_parceiros']
    
    # Importa função de mapeamento
    from .helpers import mapear_valores_para_opcoes, format_option_for_search
    
    # Mapeia valores salvos para formato das opções do dropdown
    # Isso garante sincronização automática ao abrir modal de edição
    opposing_salvos = _normalizar_lista_texto(dados.get('parte_contraria'))
    others_salvos = _normalizar_lista_texto(dados.get('outros_envolvidos'))
    clients_salvos = dados.get('clientes', []) if isinstance(dados.get('clientes'), list) else []
    
    # Converte para formato das opções
    opposing_mapeados = mapear_valores_para_opcoes(opposing_salvos, envolvidos_e_parceiros)
    others_mapeados = mapear_valores_para_opcoes(others_salvos, envolvidos_e_parceiros)
    clients_mapeados = mapear_valores_para_opcoes(clients_salvos, todas_pessoas)
    
    # Helper para formatar processo pai
    def _format_process_option(proc: dict) -> str:
        """Formata opção de processo: Título (Número)"""
        titulo = proc.get('titulo', '') or 'Sem título'
        numero = proc.get('numero', '')
        if numero:
            return f"{titulo} ({numero})"
        return titulo
    
    # Mapeia processos pai salvos (IDs ou títulos) para formato das opções
    def _mapear_processos_pai(valores_salvos) -> list:
        """Converte IDs ou títulos de processos pai para formato de exibição."""
        if not valores_salvos:
            return []
        
        # Pode vir como string (legado) ou lista
        if isinstance(valores_salvos, str):
            valores_salvos = [v.strip() for v in valores_salvos.split(',') if v.strip()]
        
        opcoes = []
        for valor in valores_salvos:
            if not valor:
                continue
            # Busca processo por ID ou título
            proc = next((p for p in processos_pais if p.get('_id') == valor or p.get('titulo') == valor), None)
            if proc:
                opcoes.append(_format_process_option(proc))
            else:
                # Valor não encontrado, mantém como está
                opcoes.append(valor)
        return opcoes
    
    # Carrega processos pai salvos
    processos_pai_salvos = dados.get('processos_pai_ids', []) or dados.get('processo_pai_id', '')
    parent_processes_mapeados = _mapear_processos_pai(processos_pai_salvos)
    
    # Estado local
    state = {
        'is_editing': is_edicao,
        'process_id': dados.get('_id') if is_edicao else None,
        'scenarios': [],
        'protocols': dados.get('protocols', []) if isinstance(dados.get('protocols'), list) else [],
        'chaves_acesso': dados.get('chaves_acesso', []) if isinstance(dados.get('chaves_acesso'), list) else [],
        'selected_clients': clients_mapeados,
        # Parte contrária - mapeada para formato das opções
        'selected_opposing': opposing_mapeados,
        # Outros envolvidos - mapeados para formato das opções
        'selected_others': others_mapeados,
        'selected_cases': [dados.get('caso_titulo')] if dados.get('caso_titulo') else [],
        # Processos pai - suporta múltiplos
        'selected_parent_processes': parent_processes_mapeados,
    }
    
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
                        tab_chaves_acesso = ui.tab('Chaves e acesso', icon='vpn_key')
            
            # Content - LAZY LOADING das abas
            # Variáveis para controlar abas já renderizadas
            abas_renderizadas = {
                'basic': False,
                'legal': False,
                'relatory': False,
                'strategy': False,
                'scenarios': False,
                'protocols': False,
                'chaves_acesso': False
            }
            
            # Containers para referências das abas
            aba_basicos_refs = {}
            aba_juridicos_refs = {}
            aba_relatorio_refs = {}
            aba_estrategia_refs = {}
            aba_cenarios_refs = {}
            aba_protocolos_refs = {}
            aba_chaves_acesso_refs = {}
            
            # Containers para lazy loading
            container_legal = None
            container_relatory = None
            container_strategy = None
            container_scenarios = None
            container_protocols = None
            container_chaves_acesso = None
            
            with ui.column().classes('flex-grow h-full overflow-auto bg-gray-50'):
                with ui.tab_panels(tabs, value=tab_basic).classes('w-full h-full p-4 bg-transparent') as panels:
                    # TAB 1: DADOS BÁSICOS - renderiza imediatamente (é a aba inicial)
                    with ui.tab_panel(tab_basic):
                        try:
                            aba_basicos_refs = render_aba_dados_basicos(
                                state, dados, todas_pessoas, todos_casos, usuarios_internos, processos_pais, envolvidos_e_parceiros
                            )
                            abas_renderizadas['basic'] = True
                        except Exception as e:
                            print(f"[ERRO CRÍTICO] Erro ao criar aba Dados Básicos: {e}")
                            import traceback
                            traceback.print_exc()
                            with ui.column().classes('w-full gap-4 p-4'):
                                ui.label('Erro ao carregar aba Dados Básicos').classes('text-red-500 font-bold text-lg')
                                ui.label(f'Erro: {str(e)}').classes('text-red-400 text-sm')
                    
                    # TAB 2: DADOS JURÍDICOS
                    with ui.tab_panel(tab_legal):
                        try:
                            aba_juridicos_refs = render_aba_dados_juridicos(dados)
                        except Exception as e:
                            print(f"[ERRO] Erro ao renderizar aba Dados Jurídicos: {e}")
                            ui.label(f'Erro: {str(e)}').classes('text-red-500')
                    
                    # TAB 3: RELATÓRIO
                    with ui.tab_panel(tab_relatory):
                        try:
                            aba_relatorio_refs = render_aba_relatorio(dados, is_edicao)
                        except Exception as e:
                            print(f"[ERRO] Erro ao renderizar aba Relatório: {e}")
                            ui.label(f'Erro: {str(e)}').classes('text-red-500')
                    
                    # TAB 4: ESTRATÉGIA
                    with ui.tab_panel(tab_strategy):
                        try:
                            aba_estrategia_refs = render_aba_estrategia(dados, is_edicao)
                        except Exception as e:
                            print(f"[ERRO] Erro ao renderizar aba Estratégia: {e}")
                            ui.label(f'Erro: {str(e)}').classes('text-red-500')
                    
                    # TAB 5: CENÁRIOS
                    with ui.tab_panel(tab_scenarios):
                        try:
                            aba_cenarios_refs = render_aba_cenarios(state)
                        except Exception as e:
                            print(f"[ERRO] Erro ao renderizar aba Cenários: {e}")
                            ui.label(f'Erro: {str(e)}').classes('text-red-500')
                    
                    # TAB 6: PROTOCOLOS
                    with ui.tab_panel(tab_protocols):
                        try:
                            aba_protocolos_refs = render_aba_protocolos(state)
                        except Exception as e:
                            print(f"[ERRO] Erro ao renderizar aba Protocolos: {e}")
                            ui.label(f'Erro: {str(e)}').classes('text-red-500')
                    
                    # TAB 7: CHAVES E ACESSO
                    with ui.tab_panel(tab_chaves_acesso):
                        try:
                            aba_chaves_acesso_refs = render_aba_chaves_acesso(state)
                        except Exception as e:
                            print(f"[ERRO] Erro ao renderizar aba Chaves e Acesso: {e}")
                            ui.label(f'Erro: {str(e)}').classes('text-red-500')
                    
                    # Todas as abas são renderizadas de uma vez (sem lazy loading)
            
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
                    
                    # Processa processos pai (múltiplos)
                    def _find_process_by_option(option: str) -> dict:
                        """Encontra processo pelo título formatado."""
                        if not option:
                            return None
                        for p in processos_pais:
                            titulo = p.get('titulo', '') or 'Sem título'
                            numero = p.get('numero', '')
                            formatted = f"{titulo} ({numero})" if numero else titulo
                            if option == formatted or option == titulo:
                                return p
                        return None
                    
                    processos_pai_ids = []
                    processos_pai_titulos = []
                    for parent_option in state.get('selected_parent_processes', []):
                        proc = _find_process_by_option(parent_option)
                        if proc:
                            processos_pai_ids.append(proc.get('_id', ''))
                            processos_pai_titulos.append(proc.get('titulo', ''))
                    
                    # Normalizar parte contrária - extrai display_names para salvar de forma consistente
                    from .helpers import extrair_display_names
                    opposing_display_names = extrair_display_names(
                        state.get('selected_opposing', []) if isinstance(state.get('selected_opposing'), list) else [],
                        envolvidos_e_parceiros
                    )
                    parte_contraria = ', '.join(opposing_display_names) if opposing_display_names else ''

                    # Normalizar outros envolvidos - extrai display_names
                    others_display_names = extrair_display_names(
                        state.get('selected_others', []) if isinstance(state.get('selected_others'), list) else [],
                        envolvidos_e_parceiros
                    )
                    outros_envolvidos = ', '.join(others_display_names) if others_display_names else ''
                    
                    # Buscar UID do responsável pelo nome (usa lista já carregada)
                    responsavel_uid = ''
                    responsavel_nome = ''
                    if aba_basicos_refs and 'responsavel_select' in aba_basicos_refs:
                        responsavel_nome = aba_basicos_refs['responsavel_select'].value or ''
                        if responsavel_nome:
                            usuario_responsavel = next((u for u in usuarios_internos if u.get('nome') == responsavel_nome), None)
                            if usuario_responsavel:
                                responsavel_uid = usuario_responsavel.get('uid', '')
                    
                    # Processa clientes: extrai display_names para salvar de forma consistente
                    clientes_processados = extrair_display_names(
                        state.get('selected_clients', []) if isinstance(state.get('selected_clients'), list) else [],
                        todas_pessoas
                    )
                    clientes_nomes_processados = clientes_processados.copy()
                    
                    novos_dados = {
                        'titulo': aba_basicos_refs.get('title_input', {}).value.strip() if aba_basicos_refs.get('title_input') and aba_basicos_refs['title_input'].value else '',
                        'numero': aba_basicos_refs.get('number_input', {}).value.strip() if aba_basicos_refs.get('number_input') and aba_basicos_refs['number_input'].value else '',
                        'link': aba_basicos_refs.get('link_input', {}).value.strip() if aba_basicos_refs.get('link_input') and aba_basicos_refs['link_input'].value else '',
                        'tipo': aba_basicos_refs.get('type_select', {}).value if aba_basicos_refs.get('type_select') else 'Judicial',
                        'nucleo': aba_juridicos_refs.get('nucleo_select', {}).value if aba_juridicos_refs.get('nucleo_select') else 'Ambiental',
                        'tipo_ambiental': aba_juridicos_refs.get('tipo_ambiental_select', {}).value if aba_juridicos_refs.get('tipo_ambiental_select') and aba_juridicos_refs.get('nucleo_select', {}).value == 'Ambiental' else '',
                        'sistema_processual': aba_juridicos_refs.get('system_select', {}).value if aba_juridicos_refs.get('system_select') else '',
                        'area': aba_juridicos_refs.get('area_select', {}).value if aba_juridicos_refs.get('area_select') else '',
                        'estado': aba_juridicos_refs.get('estado_select', {}).value if aba_juridicos_refs.get('estado_select') else '',
                        'caso_id': selected_cases_ids[0] if selected_cases_ids else '',
                        'caso_titulo': caso_titulo,
                        'clientes': clientes_processados,
                        'clientes_nomes': clientes_nomes_processados,
                        'parte_contraria': parte_contraria,
                        'outros_envolvidos': outros_envolvidos,
                        # Processos pai - suporta múltiplos
                        'processos_pai_ids': processos_pai_ids,
                        'processos_pai_titulos': processos_pai_titulos,
                        # Mantém campo legado para compatibilidade
                        'processo_pai_id': processos_pai_ids[0] if processos_pai_ids else '',
                        'processo_pai_titulo': processos_pai_titulos[0] if processos_pai_titulos else '',
                        'status': aba_juridicos_refs.get('status_select', {}).value if aba_juridicos_refs.get('status_select') else 'Em andamento',
                        'data_abertura': aba_basicos_refs.get('data_abertura_input', {}).value.strip() if aba_basicos_refs.get('data_abertura_input') and aba_basicos_refs['data_abertura_input'].value else '',
                        'prioridade': aba_basicos_refs.get('prioridade_select', {}).value if aba_basicos_refs.get('prioridade_select') else PRIORIDADE_PADRAO,
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
                        'chaves_acesso': state.get('chaves_acesso', []),
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
            """
            Popula todos os campos do formulário com dados do processo.
            
            BUGFIX 2024-12-19: Adicionado verificações de segurança e
            logging detalhado para diagnosticar problemas de carregamento.
            """
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if not is_edicao:
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] Modo criação - nada a popular")
                return
            
            if not aba_basicos_refs:
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] ❌ ERRO: aba_basicos_refs está vazio!")
                ui.notify('Erro interno: campos não inicializados.', type='warning')
                return
            
            if not dados:
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] ❌ ERRO: dados está vazio!")
                ui.notify('Erro: dados do processo não disponíveis.', type='warning')
                return
                
            try:
                processo_id = state.get('process_id') or dados.get('_id') or 'SEM_ID'
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] Iniciando população de campos para processo ID: {processo_id}")
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] Campos disponíveis em dados: {list(dados.keys())}")
                
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
                if 'prioridade_select' in aba_basicos_refs:
                    aba_basicos_refs['prioridade_select'].value = safe_get('prioridade', PRIORIDADE_PADRAO) or PRIORIDADE_PADRAO
                
                # Campos jurídicos
                if 'nucleo_select' in aba_juridicos_refs:
                    aba_juridicos_refs['nucleo_select'].value = safe_get('nucleo', 'Ambiental') or 'Ambiental'
                if 'tipo_ambiental_select' in aba_juridicos_refs:
                    aba_juridicos_refs['tipo_ambiental_select'].value = safe_get('tipo_ambiental', 'Desmatamento') or 'Desmatamento'
                if 'system_select' in aba_juridicos_refs:
                    aba_juridicos_refs['system_select'].value = safe_get('sistema_processual', '')
                if 'area_select' in aba_juridicos_refs:
                    aba_juridicos_refs['area_select'].value = safe_get('area', '')
                if 'estado_select' in aba_juridicos_refs:
                    aba_juridicos_refs['estado_select'].value = safe_get('estado', 'Santa Catarina') or 'Santa Catarina'
                if 'status_select' in aba_juridicos_refs:
                    # Migração de status antigos para novos
                    status_antigo = safe_get('status', 'Em andamento')
                    status_mapeamento = {
                        'Ativo': 'Em andamento',
                        'Suspenso': 'Em monitoramento',
                        'Arquivado': 'Concluído',
                        'Baixado': 'Concluído',
                        'Encerrado': 'Concluído',
                    }
                    status_novo = status_mapeamento.get(status_antigo, status_antigo)
                    if status_novo not in ['Em andamento', 'Concluído', 'Em monitoramento']:
                        status_novo = 'Em andamento'
                    aba_juridicos_refs['status_select'].value = status_novo
                
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
                
                # Chaves de acesso
                if dados.get('chaves_acesso') and isinstance(dados.get('chaves_acesso'), list):
                    state['chaves_acesso'] = dados.get('chaves_acesso')
                else:
                    state['chaves_acesso'] = []
                
                # Renderizar chips e selects
                try:
                    if 'refresh_chips' in aba_basicos_refs and 'client_chips' in aba_basicos_refs:
                        aba_basicos_refs['refresh_chips'](aba_basicos_refs['client_chips'], state['selected_clients'], 'clients', todas_pessoas)
                    # Parte contrária / Outros envolvidos agora são seleção múltipla (chips nativos)
                    if 'opposing_sel' in aba_basicos_refs:
                        aba_basicos_refs['opposing_sel'].value = state.get('selected_opposing', []) or []
                    if 'others_sel' in aba_basicos_refs:
                        aba_basicos_refs['others_sel'].value = state.get('selected_others', []) or []
                    if 'cases_chips' in aba_basicos_refs:
                        aba_basicos_refs['refresh_chips'](aba_basicos_refs['cases_chips'], state['selected_cases'], 'cases', None)
                    # Processos pai - seleção múltipla
                    if 'parent_process_sel' in aba_basicos_refs:
                        aba_basicos_refs['parent_process_sel'].value = state.get('selected_parent_processes', []) or []
                except Exception as e:
                    print(f"[MODAL_VG] [POPULAR] ⚠ Erro ao renderizar chips: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] ✓ População de campos concluída com sucesso")
                
                # Feedback visual de sucesso (discreto)
                titulo_processo = dados.get('titulo', 'Processo')
                ui.notify(f'Dados carregados: {titulo_processo[:40]}...', type='info', timeout=2000)
                
            except Exception as e:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] [MODAL_VG] [POPULAR] ❌ Erro ao popular campos: {e}")
                import traceback
                traceback.print_exc()
                ui.notify(f'Erro ao carregar dados do processo: {str(e)}', type='negative')
        
        # As opções de processos pai já são carregadas no aba_dados_basicos.py
        
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

