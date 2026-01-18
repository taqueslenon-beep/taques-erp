"""
Página de migração de clientes do Schmidmeier.
Interface para executar e monitorar a migração.
"""
from datetime import datetime
from nicegui import ui
from ....core import layout
from ....auth import is_authenticated
from ....gerenciadores.gerenciador_workspace import definir_workspace
from ....firebase_config import get_db
from .database_grupo import buscar_grupo_por_nome
import sys
from pathlib import Path

# Adiciona scripts ao path
try:
    # Calcula caminho absoluto para o diretório scripts
    current_file = Path(__file__).resolve()
    scripts_path = current_file.parent.parent.parent.parent.parent / 'scripts'
    scripts_path_abs = scripts_path.resolve()
    
    if scripts_path_abs.exists() and (scripts_path_abs / 'migrar_clientes_schmidmeier.py').exists():
        sys.path.insert(0, str(scripts_path_abs))
        from migrar_clientes_schmidmeier import (
            migrar_clientes_schmidmeier,
            rollback_migracao,
            carregar_mapeamento,
            converter_cliente_para_pessoa,
            extrair_digitos,
        )
    else:
        raise ImportError(f"Script não encontrado em: {scripts_path_abs}")
except (ImportError, Exception) as e:
    # Fallback se não conseguir importar
    print(f"⚠️  Aviso: Não foi possível importar script de migração: {e}")
    def migrar_clientes_schmidmeier(dry_run=False):
        return {
            'erro': 'Script de migração não encontrado',
            'timestamp': '',
            'total_clientes': 0,
            'migrados': 0,
            'duplicados': 0,
            'erros': 1,
            'mapeamento': {},
            'detalhes': [{'tipo': 'erro', 'mensagem': 'Script de migração não disponível'}]
        }
    def rollback_migracao(timestamp):
        return False
    def carregar_mapeamento(timestamp):
        return None
    def converter_cliente_para_pessoa(cliente, grupo_id, grupo_nome):
        return {}
    def extrair_digitos(valor):
        return ''.join(filter(str.isdigit, valor or ''))


def _obter_preview_clientes() -> list:
    """
    Obtém preview dos clientes que serão migrados.

    Returns:
        Lista de clientes com informações para preview
    """
    try:
        db = get_db()
        if not db:
            return []
        
        docs = db.collection('clients').stream()
        clientes = []
        
        for doc in docs:
            cliente = doc.to_dict()
            cliente['_id'] = doc.id
            
            # Extrai informações para preview
            nome = cliente.get('full_name', '') or cliente.get('name', '')
            tipo = cliente.get('client_type', 'PF')
            cpf = extrair_digitos(cliente.get('cpf', ''))
            cnpj = extrair_digitos(cliente.get('cnpj', ''))
            documento = cpf or cnpj or 'Sem documento'
            
            clientes.append({
                '_id': doc.id,
                'nome': nome,
                'tipo': tipo,
                'documento': documento,
                'email': cliente.get('email', ''),
            })
        
        return clientes
    except Exception as e:
        print(f"Erro ao obter preview: {e}")
        return []


@ui.page('/visao-geral/pessoas/migracao-clientes')
def migracao_clientes():
    """Página de migração de clientes."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return
    
    # Define workspace
    definir_workspace('visao_geral_escritorio')
    
    with layout('Migração de Clientes', breadcrumbs=[
        ('Visão geral do escritório', '/visao-geral/painel'),
        ('Pessoas', '/visao-geral/pessoas'),
        ('Migração de Clientes', None)
    ]):
        # Verifica se grupo existe
        grupo = buscar_grupo_por_nome('Schmidmeier')
        if not grupo:
            with ui.card().classes('w-full'):
                ui.icon('error', size='48px', color='negative')
                ui.label('Grupo "Schmidmeier" não encontrado').classes('text-lg text-gray-600 mt-2')
                ui.label('Execute a inicialização do grupo primeiro.').classes('text-sm text-gray-400')
            return
        
        # Header
        with ui.card().classes('w-full mb-4'):
            ui.label('Migração de Clientes - Schmidmeier').classes('text-2xl font-bold text-gray-800 mb-2')
            ui.label(
                'Esta ferramenta migra clientes da coleção "clients" para "vg_pessoas" '
                'com vinculação ao grupo "Schmidmeier".'
            ).classes('text-gray-600')
        
        # Preview dos clientes
        with ui.card().classes('w-full mb-4'):
            ui.label('Preview - Clientes a Migrar').classes('text-xl font-bold text-gray-800 mb-4')
            
            @ui.refreshable
            def refresh_preview():
                clientes = _obter_preview_clientes()
                
                if not clientes:
                    ui.label('Nenhum cliente encontrado na coleção "clients".').classes('text-gray-500')
                    return
                
                # Tabela de preview
                dados_tabela = []
                for cliente in clientes:
                    dados_tabela.append({
                        'nome': cliente['nome'],
                        'tipo': cliente['tipo'],
                        'documento': cliente['documento'],
                        'email': cliente['email'] or '-',
                    })
                
                colunas = [
                    {'name': 'nome', 'label': 'Nome', 'field': 'nome', 'align': 'left', 'sortable': True},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'center'},
                    {'name': 'documento', 'label': 'CPF/CNPJ', 'field': 'documento', 'align': 'left'},
                    {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
                ]
                
                ui.table(
                    columns=colunas,
                    rows=dados_tabela,
                    row_key='nome',
                    pagination={'rowsPerPage': 10}
                ).classes('w-full')
                
                ui.label(f'Total: {len(clientes)} cliente(s)').classes('text-sm text-gray-600 mt-2')
            
            refresh_preview()
        
        # Área de execução
        with ui.card().classes('w-full mb-4'):
            ui.label('Executar Migração').classes('text-xl font-bold text-gray-800 mb-4')
            
            # Estado da migração
            estado_migracao = {'em_andamento': False, 'relatorio': None}
            
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
                """Executa a migração."""
                if estado_migracao['em_andamento']:
                    ui.notify('Migração já em andamento!', type='warning')
                    return
                
                estado_migracao['em_andamento'] = True
                log_container.clear()
                adicionar_log('🚀 Iniciando migração...', 'info')
                
                try:
                    # Executa migração
                    relatorio = migrar_clientes_schmidmeier(dry_run=False)
                    estado_migracao['relatorio'] = relatorio
                    
                    # Adiciona logs do relatório
                    for detalhe in relatorio['detalhes']:
                        tipo_log = detalhe.get('tipo', 'info')
                        mensagem = detalhe.get('mensagem', '')
                        adicionar_log(mensagem, tipo_log)
                    
                    # Resumo
                    adicionar_log('', 'info')
                    adicionar_log('='*50, 'info')
                    adicionar_log('📊 RESUMO', 'info')
                    adicionar_log(f"Total: {relatorio['total_clientes']}", 'info')
                    adicionar_log(f"✅ Migrados: {relatorio['migrados']}", 'sucesso')
                    adicionar_log(f"⚠️  Duplicados: {relatorio['duplicados']}", 'aviso')
                    adicionar_log(f"❌ Erros: {relatorio['erros']}", 'erro')
                    adicionar_log('='*50, 'info')
                    
                    if relatorio['migrados'] > 0:
                        ui.notify(
                            f'Migração concluída! {relatorio["migrados"]} cliente(s) migrado(s).',
                            type='positive'
                        )
                        refresh_preview.refresh()
                        refresh_resumo.refresh()
                    else:
                        ui.notify('Nenhum cliente foi migrado.', type='warning')
                    
                except Exception as e:
                    adicionar_log(f'❌ Erro: {str(e)}', 'erro')
                    ui.notify('Erro ao executar migração!', type='negative')
                    import traceback
                    traceback.print_exc()
                finally:
                    estado_migracao['em_andamento'] = False
            
            def executar_rollback():
                """Executa rollback da última migração."""
                if not estado_migracao['relatorio']:
                    ui.notify('Nenhuma migração para desfazer!', type='warning')
                    return
                
                timestamp = estado_migracao['relatorio'].get('timestamp')
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
                            sucesso = rollback_migracao(timestamp)
                            if sucesso:
                                adicionar_log('✅ Rollback concluído com sucesso!', 'sucesso')
                                ui.notify('Rollback concluído!', type='positive')
                                refresh_preview.refresh()
                                refresh_resumo.refresh()
                                estado_migracao['relatorio'] = None
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
                    'Iniciar Migração',
                    icon='play_arrow',
                    on_click=executar_migracao
                ).props('color=primary').bind_enabled_from(estado_migracao, 'em_andamento', backward=lambda x: not x)
                
                ui.button(
                    'Desfazer (Rollback)',
                    icon='undo',
                    on_click=executar_rollback
                ).props('color=negative flat').bind_enabled_from(estado_migracao, 'relatorio', backward=lambda x: x is not None)
            
            # Log
            ui.label('Log de Execução').classes('text-sm font-bold text-gray-700 mt-4 mb-2')
            # log_container já foi criado acima
        
        # Resumo da última migração
        @ui.refreshable
        def refresh_resumo():
            if estado_migracao.get('relatorio'):
                relatorio = estado_migracao['relatorio']
                with ui.card().classes('w-full'):
                    ui.label('Resumo da Última Migração').classes('text-xl font-bold text-gray-800 mb-4')
                    
                    with ui.column().classes('w-full gap-2'):
                        ui.label(f"Timestamp: {relatorio.get('timestamp', 'N/A')}").classes('text-sm text-gray-600')
                        ui.label(f"Total de clientes: {relatorio.get('total_clientes', 0)}").classes('text-sm text-gray-600')
                        ui.label(f"✅ Migrados: {relatorio.get('migrados', 0)}").classes('text-sm text-green-700')
                        ui.label(f"⚠️  Duplicados: {relatorio.get('duplicados', 0)}").classes('text-sm text-yellow-700')
                        ui.label(f"❌ Erros: {relatorio.get('erros', 0)}").classes('text-sm text-red-700')
        
        refresh_resumo()
















