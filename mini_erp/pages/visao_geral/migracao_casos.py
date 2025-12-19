"""
Página de migração de casos do Schmidmeier para Visão Geral.
Interface para executar e monitorar a migração.

Rota: /visao-geral/migracao-casos
"""
print("=" * 60)
print("[MIGRACAO CASOS] Arquivo carregado com sucesso!")
print("=" * 60)

from datetime import datetime
from nicegui import ui, run
from ...core import layout
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace
from ...firebase_config import get_db
from .pessoas.database_grupo import buscar_grupo_por_nome
import sys
from pathlib import Path
from typing import List, Dict, Any

# Adiciona scripts ao path
print("[MIGRACAO CASOS] Tentando importar script de migração...")
try:
    current_file = Path(__file__).resolve()
    scripts_path = current_file.parent.parent.parent.parent / 'scripts'
    scripts_path_abs = scripts_path.resolve()
    
    print(f"[MIGRACAO CASOS] Caminho do script: {scripts_path_abs}")
    print(f"[MIGRACAO CASOS] Script existe? {scripts_path_abs.exists()}")
    print(f"[MIGRACAO CASOS] Arquivo existe? {(scripts_path_abs / 'migrar_casos_schmidmeier.py').exists()}")
    
    if scripts_path_abs.exists() and (scripts_path_abs / 'migrar_casos_schmidmeier.py').exists():
        sys.path.insert(0, str(scripts_path_abs))
        from migrar_casos_schmidmeier import (
            buscar_casos_schmidmeier,
            filtrar_casos_para_migrar,
            migrar_casos_schmidmeier,
            rollback_migracao,
            carregar_mapeamento,
        )
        print("[MIGRACAO CASOS] ✅ Script de migração importado com sucesso!")
    else:
        raise ImportError(f"Script não encontrado em: {scripts_path_abs}")
except (ImportError, Exception) as e:
    print(f"[MIGRACAO CASOS] ⚠️  Aviso: Não foi possível importar script de migração: {e}")
    import traceback
    traceback.print_exc()
    
    # Funções fallback
    def buscar_casos_schmidmeier():
        return []
    def filtrar_casos_para_migrar(casos):
        return []
    def migrar_casos_schmidmeier(lista_casos=None, dry_run=False):
        return False, {'erros': ['Script de migração não disponível']}
    def rollback_migracao(caminho_mapeamento):
        return False
    def carregar_mapeamento(caminho_arquivo):
        return {}


def _obter_preview_casos() -> List[Dict[str, Any]]:
    """
    Obtém preview dos casos que serão migrados.
    
    Returns:
        Lista de casos com informações para preview
    """
    try:
        todos_casos = buscar_casos_schmidmeier()
        casos_filtrados = filtrar_casos_para_migrar(todos_casos)
        
        preview = []
        for caso in casos_filtrados:
            titulo = caso.get('title', '') or caso.get('name', '')
            slug = caso.get('slug', '')
            status = caso.get('status', 'Em andamento')
            estado = caso.get('state', '')
            categoria = caso.get('category', '')
            case_type = caso.get('case_type', '')
            clientes = caso.get('clients', [])
            if isinstance(clientes, str):
                clientes = [clientes]
            
            preview.append({
                'slug': slug,
                'titulo': titulo,
                'status': status,
                'estado': estado,
                'categoria': categoria,
                'tipo': case_type,
                'clientes': ', '.join(clientes) if clientes else '-',
            })
        
        return preview
    except Exception as e:
        print(f"[MIGRACAO CASOS] Erro ao obter preview: {e}")
        import traceback
        traceback.print_exc()
        return []


@ui.page('/visao-geral/migracao-casos')
def migracao_casos():
    """Página de migração de casos."""
    print("[MIGRACAO CASOS] Rota /visao-geral/migracao-casos acessada!")
    
    if not is_authenticated():
        print("[MIGRACAO CASOS] Usuário não autenticado, redirecionando para login")
        ui.navigate.to('/login')
        return
    
    # Define workspace
    definir_workspace('visao_geral_escritorio')
    
    with layout('Migração de Casos', breadcrumbs=[
        ('Visão geral do escritório', '/visao-geral/painel'),
        ('Casos', '/visao-geral/casos'),
        ('Migração de Casos', None)
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
            ui.label('Migração de Casos - Schmidmeier → Visão Geral').classes('text-2xl font-bold text-gray-800 mb-2')
            ui.label(
                'Esta ferramenta migra casos da coleção "cases" (Schmidmeier) para "vg_casos" (Visão Geral). '
                'Por padrão, seleciona todos os casos "Antigos" e 2 casos específicos novos.'
            ).classes('text-gray-600')
        
        # Estado da interface
        estado = {
            'casos_selecionados': [],
            'em_migracao': False,
            'log_mensagens': [],
            'ultimo_mapeamento': None,
        }
        
        # Preview dos casos
        with ui.card().classes('w-full mb-4'):
            ui.label('Preview - Casos a Migrar').classes('text-xl font-bold text-gray-800 mb-4')
            
            casos_preview = _obter_preview_casos()
            
            if not casos_preview:
                ui.label('Nenhum caso encontrado para migração.').classes('text-gray-500')
            else:
                # Tabela de preview com checkboxes
                # NOTA: Não incluir coluna 'selecionado' - o NiceGUI cria checkboxes automaticamente com selection='multiple'
                colunas = [
                    {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'required': True, 'align': 'left'},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'required': True, 'align': 'left'},
                    {'name': 'estado', 'label': 'Estado', 'field': 'estado', 'required': True, 'align': 'left'},
                    {'name': 'categoria', 'label': 'Categoria', 'field': 'categoria', 'required': True, 'align': 'left'},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'required': True, 'align': 'left'},
                    {'name': 'clientes', 'label': 'Clientes', 'field': 'clientes', 'required': True, 'align': 'left'},
                ]
                
                linhas = []
                for caso in casos_preview:
                    linhas.append({
                        'slug': caso['slug'],
                        'titulo': caso['titulo'],
                        'status': caso['status'],
                        'estado': caso['estado'],
                        'categoria': caso['categoria'],
                        'tipo': caso['tipo'],
                        'clientes': caso['clientes'],
                        # Campo 'selecionado' removido - não é necessário exibir como coluna
                    })
                
                tabela = ui.table(
                    columns=colunas,
                    rows=linhas,
                    row_key='slug',
                    selection='multiple',
                ).classes('w-full')
                
                # Atualiza estado quando seleção muda
                def atualizar_selecao():
                    selecionados = tabela.selected_rows
                    estado['casos_selecionados'] = [c['slug'] for c in selecionados]
                
                tabela.on('selection', atualizar_selecao)
                
                # Inicializa com todos selecionados (todos os casos do preview)
                estado['casos_selecionados'] = [c['slug'] for c in linhas]
        
        # Área de log
        with ui.card().classes('w-full mb-4'):
            ui.label('Log de Migração').classes('text-xl font-bold text-gray-800 mb-4')
            
            log_container = ui.column().classes('w-full')
            
            def adicionar_log(mensagem: str, tipo: str = 'info'):
                """Adiciona mensagem ao log."""
                cor = {
                    'info': 'text-blue-600',
                    'success': 'text-green-600',
                    'warning': 'text-yellow-600',
                    'error': 'text-red-600',
                }.get(tipo, 'text-gray-600')
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                with log_container:
                    ui.label(f'[{timestamp}] {mensagem}').classes(f'{cor} text-sm')
                
                estado['log_mensagens'].append(f'[{timestamp}] {mensagem}')
            
            adicionar_log('Pronto para iniciar migração', 'info')
        
        # Botões de ação
        with ui.row().classes('w-full gap-4'):
            btn_migrar = ui.button(
                'INICIAR MIGRAÇÃO',
                icon='play_arrow',
                color='primary',
            ).classes('px-6 py-3')
            
            btn_rollback = ui.button(
                'DESFAZER (ROLLBACK)',
                icon='undo',
                color='negative',
            ).classes('px-6 py-3')
            
            btn_atualizar = ui.button(
                'ATUALIZAR PREVIEW',
                icon='refresh',
                color='secondary',
            ).classes('px-6 py-3')
        
        # Função de migração
        async def executar_migracao():
            if estado['em_migracao']:
                adicionar_log('Migração já em andamento', 'warning')
                return
            
            if not estado['casos_selecionados']:
                adicionar_log('Nenhum caso selecionado', 'warning')
                return
            
            estado['em_migracao'] = True
            btn_migrar.set_enabled(False)
            btn_rollback.set_enabled(False)
            btn_atualizar.set_enabled(False)
            
            try:
                adicionar_log(f'Iniciando migração de {len(estado["casos_selecionados"])} casos...', 'info')
                
                # Busca casos selecionados
                todos_casos = await run.io_bound(buscar_casos_schmidmeier)
                casos_filtrados = filtrar_casos_para_migrar(todos_casos)
                casos_selecionados = [
                    c for c in casos_filtrados 
                    if c.get('slug') in estado['casos_selecionados']
                ]
                
                adicionar_log(f'{len(casos_selecionados)} casos encontrados para migração', 'info')
                
                # Executa migração
                sucesso, resultado = await run.io_bound(
                    migrar_casos_schmidmeier,
                    lista_casos=casos_selecionados,
                    dry_run=False
                )
                
                if sucesso:
                    adicionar_log(f'✅ Migração concluída com sucesso!', 'success')
                    adicionar_log(f'   - Migrados: {resultado.get("casos_migrados", 0)}', 'success')
                    adicionar_log(f'   - Duplicados: {resultado.get("casos_duplicados", 0)}', 'warning')
                    adicionar_log(f'   - Erros: {resultado.get("casos_com_erro", 0)}', 'error' if resultado.get("casos_com_erro", 0) > 0 else 'info')
                    
                    # Salva caminho do mapeamento se disponível
                    if resultado.get('mapeamento'):
                        estado['ultimo_mapeamento'] = resultado.get('mapeamento')
                        adicionar_log('Mapeamento salvo para rollback', 'info')
                else:
                    adicionar_log('❌ Erro na migração', 'error')
                    for erro in resultado.get('erros', []):
                        adicionar_log(f'   - {erro}', 'error')
                
            except Exception as e:
                adicionar_log(f'❌ Erro inesperado: {str(e)}', 'error')
                import traceback
                traceback.print_exc()
            finally:
                estado['em_migracao'] = False
                btn_migrar.set_enabled(True)
                btn_rollback.set_enabled(True)
                btn_atualizar.set_enabled(True)
        
        # Função de rollback
        async def executar_rollback():
            if estado['em_migracao']:
                adicionar_log('Migração em andamento. Aguarde...', 'warning')
                return
            
            # Busca último arquivo de mapeamento
            mapeamentos_dir = Path(__file__).parent.parent.parent / 'migracoes'
            mapeamentos_dir.mkdir(exist_ok=True)
            
            arquivos_mapeamento = sorted(
                mapeamentos_dir.glob('mapeamento_casos_*.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if not arquivos_mapeamento:
                adicionar_log('Nenhum arquivo de mapeamento encontrado', 'warning')
                return
            
            ultimo_arquivo = arquivos_mapeamento[0]
            
            # Confirmação usando dialog do NiceGUI
            with ui.dialog() as dialog, ui.card():
                ui.label('Confirmar Rollback').classes('text-xl font-bold mb-4')
                ui.label('Tem certeza que deseja desfazer a última migração? Esta ação não pode ser revertida.').classes('mb-4')
                with ui.row():
                    ui.button('Cancelar', on_click=dialog.close).props('outline')
                    ui.button('Confirmar', on_click=dialog.submit('confirm')).props('color=negative')
            
            resposta = await dialog
            if resposta != 'confirm':
                adicionar_log('Rollback cancelado', 'info')
                return
            
            estado['em_migracao'] = True
            btn_migrar.set_enabled(False)
            btn_rollback.set_enabled(False)
            btn_atualizar.set_enabled(False)
            
            try:
                adicionar_log(f'Iniciando rollback usando: {ultimo_arquivo.name}', 'info')
                
                sucesso = await run.io_bound(
                    rollback_migracao,
                    str(ultimo_arquivo)
                )
                
                if sucesso:
                    adicionar_log('✅ Rollback concluído com sucesso!', 'success')
                else:
                    adicionar_log('❌ Erro no rollback', 'error')
                    
            except Exception as e:
                adicionar_log(f'❌ Erro inesperado no rollback: {str(e)}', 'error')
                import traceback
                traceback.print_exc()
            finally:
                estado['em_migracao'] = False
                btn_migrar.set_enabled(True)
                btn_rollback.set_enabled(True)
                btn_atualizar.set_enabled(True)
        
        # Função de atualizar preview
        async def atualizar_preview():
            if estado['em_migracao']:
                return
            
            adicionar_log('Atualizando preview...', 'info')
            ui.navigate.reload()
        
        # Conecta botões
        btn_migrar.on('click', executar_migracao)
        btn_rollback.on('click', executar_rollback)
        btn_atualizar.on('click', atualizar_preview)







