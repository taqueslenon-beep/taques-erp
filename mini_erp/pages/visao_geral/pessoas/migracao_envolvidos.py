"""
Página de migração de outros envolvidos do Schmidmeier.
Interface para editar, selecionar e migrar envolvidos.
"""
from datetime import datetime
from typing import List, Dict, Any
from nicegui import ui
from ....core import layout
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from ....firebase_config import get_db
from .models import TIPOS_ENVOLVIDO
import sys
from pathlib import Path

# Funções de migração (importadas dinamicamente para evitar importação circular)
_migracao_functions = None

def _importar_funcoes_migracao():
    """Importa funções de migração de forma lazy para evitar importação circular."""
    global _migracao_functions
    if _migracao_functions is not None:
        return _migracao_functions
    
    try:
        current_file = Path(__file__).resolve()
        scripts_path = current_file.parent.parent.parent.parent.parent / 'scripts'
        scripts_path_abs = scripts_path.resolve()
        
        if scripts_path_abs.exists() and (scripts_path_abs / 'migrar_envolvidos_schmidmeier.py').exists():
            # Adiciona ao path apenas temporariamente
            if str(scripts_path_abs) not in sys.path:
                sys.path.insert(0, str(scripts_path_abs))
            
            # Importa o módulo
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "migrar_envolvidos_schmidmeier",
                scripts_path_abs / 'migrar_envolvidos_schmidmeier.py'
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            _migracao_functions = {
                'migrar_envolvidos_schmidmeier': module.migrar_envolvidos_schmidmeier,
                'rollback_migracao': module.rollback_migracao,
                'carregar_mapeamento': module.carregar_mapeamento,
                'converter_envolvido_para_novo_formato': module.converter_envolvido_para_novo_formato,
                'extrair_digitos': module.extrair_digitos,
            }
            return _migracao_functions
        else:
            raise ImportError(f"Script não encontrado em: {scripts_path_abs}")
    except (ImportError, Exception) as e:
        print(f"⚠️  Aviso: Não foi possível importar script de migração: {e}")
        # Retorna funções stub
        def migrar_stub(lista_envolvidos, dry_run=False):
            return {
                'erro': 'Script de migração não encontrado',
                'timestamp': '',
                'total': 0,
                'migrados': 0,
                'duplicados': 0,
                'erros': 1,
                'mapeamento': {},
                'detalhes': [{'tipo': 'erro', 'mensagem': f'Script de migração não disponível: {str(e)}'}]
            }
        _migracao_functions = {
            'migrar_envolvidos_schmidmeier': migrar_stub,
            'rollback_migracao': lambda t: False,
            'carregar_mapeamento': lambda t: None,
            'converter_envolvido_para_novo_formato': lambda e: {},
            'extrair_digitos': lambda v: ''.join(filter(str.isdigit, v or '')),
        }
        return _migracao_functions

# Funções auxiliares que usam importação lazy
def extrair_digitos(valor):
    """Extrai apenas dígitos de uma string."""
    funcs = _importar_funcoes_migracao()
    return funcs['extrair_digitos'](valor)


def _obter_envolvidos_originais() -> List[Dict[str, Any]]:
    """
    Obtém lista original de envolvidos da coleção opposing_parties.

    Returns:
        Lista de envolvidos com informações para edição
    """
    try:
        db = get_db()
        if not db:
            return []
        
        docs = db.collection('opposing_parties').stream()
        envolvidos = []
        
        for doc in docs:
            envolvido = doc.to_dict()
            envolvido['_id'] = doc.id
            
            # Extrai informações para preview/edit
            nome_completo = envolvido.get('full_name', '') or envolvido.get('name', '')
            nome_exibicao = envolvido.get('nome_exibicao', '') or envolvido.get('display_name', '') or nome_completo
            tipo_antigo = envolvido.get('entity_type', '') or envolvido.get('type', '') or envolvido.get('client_type', 'PF')
            
            # Mapeia tipo
            tipo_mapeado = 'PF'
            if tipo_antigo in ['PJ', 'pj']:
                tipo_mapeado = 'PJ'
            elif tipo_antigo in ['Órgão Público', 'Ente Público', 'orgao publico']:
                tipo_mapeado = 'Ente Público'
            elif tipo_antigo in ['Advogado', 'advogado']:
                tipo_mapeado = 'Advogado'
            elif tipo_antigo in ['Técnico', 'tecnico', 'Tecnico']:
                tipo_mapeado = 'Técnico'
            
            cpf_cnpj = extrair_digitos(
                envolvido.get('cpf_cnpj', '') or
                envolvido.get('document', '') or
                ''
            )
            
            envolvidos.append({
                '_id': doc.id,
                'nome_completo': nome_completo,
                'nome_exibicao': nome_exibicao,
                'tipo_envolvido': tipo_mapeado,
                'cpf_cnpj': cpf_cnpj,
                'email': envolvido.get('email', ''),
                'telefone': envolvido.get('telefone', '') or envolvido.get('phone', ''),
                '_dados_originais': envolvido,  # Mantém dados originais
            })
        
        return envolvidos
    except Exception as e:
        print(f"Erro ao obter envolvidos: {e}")
        return []


@ui.page('/visao-geral/pessoas/migracao-envolvidos')
def migracao_envolvidos():
    """Página de migração de envolvidos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Define workspace
    definir_workspace('visao_geral_escritorio')
    
    with layout('Migração de Outros Envolvidos', breadcrumbs=[
        ('Visão geral do escritório', '/visao-geral/painel'),
        ('Pessoas', '/visao-geral/pessoas'),
        ('Migração de Envolvidos', None)
    ]):
        # Header
        with ui.card().classes('w-full mb-4'):
            ui.label('Migração de Outros Envolvidos - Schmidmeier').classes('text-2xl font-bold text-gray-800 mb-2')
            ui.label(
                'Esta ferramenta migra outros envolvidos da coleção "opposing_parties" para "vg_envolvidos". '
                'Você pode editar os dados antes de migrar.'
            ).classes('text-gray-600')
        
        # Estado da lista editável
        estado = {
            'envolvidos': [],
            'selecionados': set(),
            'em_andamento': False,
            'relatorio': None,
        }
        
        # Tabela editável (definida antes de carregar_lista para evitar problemas de referência)
        @ui.refreshable
        def refresh_tabela():
            if not estado['envolvidos']:
                ui.label('Nenhum envolvido encontrado. Clique em "Atualizar Preview" para carregar.').classes('text-gray-500')
                return
            
            # Container da tabela
            with ui.column().classes('w-full gap-2'):
                # Header com checkbox "Selecionar Todos"
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    def toggle_todos():
                        if len(estado['selecionados']) == len(estado['envolvidos']):
                            estado['selecionados'] = set()
                        else:
                            estado['selecionados'] = set(range(len(estado['envolvidos'])))
                        refresh_tabela.refresh()
                        refresh_contador.refresh()
                    
                    checkbox_todos = ui.checkbox(
                        'Selecionar Todos',
                        value=len(estado['selecionados']) == len(estado['envolvidos'])
                    ).on('update:model-value', lambda e: toggle_todos())
                
                # Tabela com linhas editáveis
                with ui.column().classes('w-full gap-2'):
                    # Header da tabela
                    with ui.row().classes('w-full items-center gap-2 p-2 bg-gray-100 rounded font-bold text-sm'):
                        ui.label('').classes('w-8')  # Checkbox
                        ui.label('Nome Completo').classes('flex-1')
                        ui.label('Nome de Exibição').classes('flex-1')
                        ui.label('Tipo').classes('w-32')
                        ui.label('CPF/CNPJ').classes('w-32')
                        ui.label('Ações').classes('w-20')
                    
                    # Linhas editáveis
                    for idx, env in enumerate(estado['envolvidos']):
                        # Captura idx em closure para evitar problemas
                        idx_capturado = idx
                        
                        with ui.row().classes('w-full items-center gap-2 p-2 border-b'):
                            # Checkbox de seleção
                            def criar_toggle(idx_local):
                                def toggle(val):
                                    if val:
                                        estado['selecionados'].add(idx_local)
                                    else:
                                        estado['selecionados'].discard(idx_local)
                                    refresh_contador.refresh()
                                return toggle
                            
                            ui.checkbox(
                                '',
                                value=idx_capturado in estado['selecionados']
                            ).on('update:model-value', criar_toggle(idx_capturado)).classes('w-8')
                            
                            # Nome completo (editável)
                            def criar_input_nome_completo(idx_local):
                                def atualizar(val):
                                    if 0 <= idx_local < len(estado['envolvidos']):
                                        estado['envolvidos'][idx_local]['nome_completo'] = val
                                return atualizar
                            
                            ui.input(
                                '',
                                value=env['nome_completo'],
                                placeholder='Nome completo'
                            ).on('update:model-value', criar_input_nome_completo(idx_capturado)).classes('flex-1').props('dense outlined')
                            
                            # Nome de exibição (editável)
                            def criar_input_nome_exibicao(idx_local):
                                def atualizar(val):
                                    if 0 <= idx_local < len(estado['envolvidos']):
                                        estado['envolvidos'][idx_local]['nome_exibicao'] = val
                                return atualizar
                            
                            ui.input(
                                '',
                                value=env['nome_exibicao'],
                                placeholder='Nome de exibição'
                            ).on('update:model-value', criar_input_nome_exibicao(idx_capturado)).classes('flex-1').props('dense outlined')
                            
                            # Tipo (dropdown editável)
                            def criar_select_tipo(idx_local):
                                def atualizar(val):
                                    if 0 <= idx_local < len(estado['envolvidos']):
                                        estado['envolvidos'][idx_local]['tipo_envolvido'] = val
                                return atualizar
                            
                            ui.select(
                                TIPOS_ENVOLVIDO,
                                value=env['tipo_envolvido'],
                                label=''
                            ).on('update:model-value', criar_select_tipo(idx_capturado)).classes('w-32').props('dense outlined')
                            
                            # CPF/CNPJ (somente leitura)
                            ui.label(env['cpf_cnpj'] or '-').classes('w-32 text-sm')
                            
                            # Botão remover
                            def criar_remover(idx_local):
                                def remover():
                                    if 0 <= idx_local < len(estado['envolvidos']):
                                        estado['envolvidos'].pop(idx_local)
                                        # Ajusta índices dos selecionados
                                        novos_selecionados = set()
                                        for sel_idx in estado['selecionados']:
                                            if sel_idx < idx_local:
                                                novos_selecionados.add(sel_idx)
                                            elif sel_idx > idx_local:
                                                novos_selecionados.add(sel_idx - 1)
                                        estado['selecionados'] = novos_selecionados
                                        refresh_tabela.refresh()
                                        refresh_contador.refresh()
                                return remover
                            
                            ui.button(
                                icon='delete',
                                on_click=criar_remover(idx_capturado)
                            ).props('flat dense color=negative').classes('w-20')
        
        # Contador de selecionados
        @ui.refreshable
        def refresh_contador():
            total = len(estado['envolvidos'])
            selecionados = len(estado['selecionados'])
            ui.label(f'{selecionados} de {total} selecionados para migração').classes('text-sm font-bold text-gray-700')
        
        # Carrega envolvidos originais (definida depois das funções refreshable)
        def carregar_lista():
            estado['envolvidos'] = _obter_envolvidos_originais()
            estado['selecionados'] = set(range(len(estado['envolvidos'])))  # Seleciona todos por padrão
            refresh_tabela.refresh()
            refresh_contador.refresh()
        
        # Card da tabela
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('Preview Editável - Envolvidos a Migrar').classes('text-xl font-bold text-gray-800')
                ui.button('Atualizar Preview', icon='refresh', on_click=carregar_lista).props('flat dense')
            
            refresh_contador()
            ui.separator().classes('my-2')
            refresh_tabela()
        
        # Área de execução
        with ui.card().classes('w-full mb-4'):
            ui.label('Executar Migração').classes('text-xl font-bold text-gray-800 mb-4')
            
            # Container de log
            log_container = ui.column().classes('w-full bg-gray-50 p-4 rounded mb-4 max-h-96 overflow-y-auto')
            
            def adicionar_log(mensagem: str, tipo: str = 'info'):
                """Adiciona mensagem ao log."""
                cor = {
                    'info': 'text-gray-700',
                    'sucesso': 'text-green-700',
                    'erro': 'text-red-700',
                    'aviso': 'text-yellow-700',
                }.get(tipo, 'text-gray-700')
                
                with log_container:
                    ui.label(f'[{datetime.now().strftime("%H:%M:%S")}] {mensagem}').classes(f'text-sm {cor}')
            
            def executar_migracao():
                """Executa a migração apenas dos selecionados."""
                if estado['em_andamento']:
                    ui.notify('Migração já em andamento!', type='warning')
                    return
                
                selecionados = [i for i in estado['selecionados'] if 0 <= i < len(estado['envolvidos'])]
                if not selecionados:
                    ui.notify('Selecione pelo menos um envolvido para migrar!', type='warning')
                    return
                
                estado['em_andamento'] = True
                log_container.clear()
                adicionar_log('🚀 Iniciando migração...', 'info')
                
                try:
                    # Prepara lista de envolvidos selecionados (com dados originais)
                    lista_para_migrar = []
                    for idx in selecionados:
                        env_editado = estado['envolvidos'][idx]
                        # Reconstrói com dados originais + edições
                        env_completo = env_editado['_dados_originais'].copy()
                        env_completo['full_name'] = env_editado['nome_completo']
                        env_completo['nome_exibicao'] = env_editado['nome_exibicao']
                        env_completo['display_name'] = env_editado['nome_exibicao']
                        env_completo['entity_type'] = env_editado['tipo_envolvido']
                        env_completo['type'] = env_editado['tipo_envolvido']
                        lista_para_migrar.append(env_completo)
                    
                    # Executa migração
                    funcs = _importar_funcoes_migracao()
                    relatorio = funcs['migrar_envolvidos_schmidmeier'](lista_para_migrar, dry_run=False)
                    estado['relatorio'] = relatorio
                    
                    # Adiciona logs do relatório
                    for detalhe in relatorio['detalhes']:
                        tipo_log = detalhe.get('tipo', 'info')
                        if tipo_log == 'sucesso':
                            tipo_log = 'sucesso'
                        elif tipo_log == 'duplicado':
                            tipo_log = 'aviso'
                        elif tipo_log == 'erro':
                            tipo_log = 'erro'
                        else:
                            tipo_log = 'info'
                        mensagem = detalhe.get('mensagem', '')
                        adicionar_log(mensagem, tipo_log)
                    
                    # Resumo
                    adicionar_log('', 'info')
                    adicionar_log('='*50, 'info')
                    adicionar_log('📊 RESUMO', 'info')
                    adicionar_log(f"Total: {relatorio['total']}", 'info')
                    adicionar_log(f"✅ Migrados: {relatorio['migrados']}", 'sucesso')
                    adicionar_log(f"⚠️  Duplicados: {relatorio['duplicados']}", 'aviso')
                    adicionar_log(f"❌ Erros: {relatorio['erros']}", 'erro')
                    adicionar_log('='*50, 'info')
                    
                    if relatorio['migrados'] > 0:
                        ui.notify(
                            f'Migração concluída! {relatorio["migrados"]} envolvido(s) migrado(s).',
                            type='positive'
                        )
                        carregar_lista()  # Recarrega lista
                        refresh_resumo.refresh()
                    else:
                        ui.notify('Nenhum envolvido foi migrado.', type='warning')
                    
                except Exception as e:
                    adicionar_log(f'❌ Erro: {str(e)}', 'erro')
                    ui.notify('Erro ao executar migração!', type='negative')
                    import traceback
                    traceback.print_exc()
                finally:
                    estado['em_andamento'] = False
            
            def executar_rollback():
                """Executa rollback da última migração."""
                if not estado['relatorio']:
                    ui.notify('Nenhuma migração para desfazer!', type='warning')
                    return
                
                timestamp = estado['relatorio'].get('timestamp')
                if not timestamp:
                    ui.notify('Timestamp não encontrado!', type='negative')
                    return
                
                # Dialog de confirmação
                with ui.dialog() as dialog_confirm, ui.card():
                    ui.label('Confirmar Rollback').classes('text-xl font-bold mb-4')
                    ui.label('Tem certeza que deseja desfazer a migração?').classes('mb-4')
                    ui.label('Esta ação removerá os registros migrados.').classes('text-sm text-gray-600 mb-4')
                    
                    def confirmar_rollback():
                        dialog_confirm.close()
                        log_container.clear()
                        adicionar_log('🔄 Iniciando rollback...', 'info')
                        
                        try:
                            funcs = _importar_funcoes_migracao()
                            sucesso = funcs['rollback_migracao'](timestamp)
                            if sucesso:
                                adicionar_log('✅ Rollback concluído com sucesso!', 'sucesso')
                                ui.notify('Rollback concluído!', type='positive')
                                carregar_lista()
                                refresh_resumo.refresh()
                                estado['relatorio'] = None
                            else:
                                adicionar_log('❌ Erro no rollback', 'erro')
                                ui.notify('Erro ao executar rollback!', type='negative')
                        except Exception as e:
                            adicionar_log(f'❌ Erro: {str(e)}', 'erro')
                            ui.notify('Erro ao executar rollback!', type='negative')
                            import traceback
                            traceback.print_exc()
                    
                    with ui.row().classes('w-full justify-end gap-2'):
                        ui.button('Cancelar', on_click=dialog_confirm.close).props('flat')
                        ui.button('Confirmar', on_click=confirmar_rollback).props('color=negative')
                
                dialog_confirm.open()
            
            # Botões de ação
            with ui.row().classes('w-full gap-2'):
                ui.button(
                    'INICIAR MIGRAÇÃO',
                    icon='play_arrow',
                    on_click=executar_migracao
                ).props('color=primary').bind_enabled_from(estado, 'em_andamento', backward=lambda x: not x)
                
                ui.button(
                    'DESFAZER (ROLLBACK)',
                    icon='undo',
                    on_click=executar_rollback
                ).props('color=negative flat').bind_enabled_from(estado, 'relatorio', backward=lambda x: x is not None)
            
            # Log
            ui.label('Log de Execução').classes('text-sm font-bold text-gray-700 mt-4 mb-2')
        
        # Resumo da última migração
        @ui.refreshable
        def refresh_resumo():
            if estado.get('relatorio'):
                relatorio = estado['relatorio']
                with ui.card().classes('w-full'):
                    ui.label('Resumo da Última Migração').classes('text-xl font-bold text-gray-800 mb-4')
                    
                    with ui.column().classes('w-full gap-2'):
                        ui.label(f"Timestamp: {relatorio.get('timestamp', 'N/A')}").classes('text-sm text-gray-600')
                        ui.label(f"Total processado: {relatorio.get('total', 0)}").classes('text-sm text-gray-600')
                        ui.label(f"✅ Migrados: {relatorio.get('migrados', 0)}").classes('text-sm text-green-700')
                        ui.label(f"⚠️  Duplicados: {relatorio.get('duplicados', 0)}").classes('text-sm text-yellow-700')
                        ui.label(f"❌ Erros: {relatorio.get('erros', 0)}").classes('text-sm text-red-700')
        
        refresh_resumo()
        
        # Carrega lista inicial
        carregar_lista()




