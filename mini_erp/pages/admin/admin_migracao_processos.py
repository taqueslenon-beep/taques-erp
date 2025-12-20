"""
Página administrativa para migração em lote de processos do EPROC.
Rota: /admin/migracao-processos
"""
from nicegui import ui
from mini_erp.core import layout
from mini_erp.auth import is_authenticated
from .migracao_service import (
    importar_planilha_migracao, obter_estatisticas_migracao, 
    listar_processos_migracao, salvar_processo_migracao,
    finalizar_migracao_completa
)
from ..visao_geral.processos.constants import AREAS_PROCESSO, NUCLEOS_PROCESSO
from ..visao_geral.processos.database import listar_processos_pais, criar_processo as criar_processo_workspace
from ..visao_geral.casos.database import listar_casos
from ..visao_geral.pessoas.database import (
    listar_pessoas, criar_pessoa,
    listar_envolvidos, criar_envolvido,
    listar_parceiros, criar_parceiro
)
import logging
import re
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# FUNÇÕES AUXILIARES DE LIMPEZA E UX
# =============================================================================

def get_safe_value(processo, campo, opcoes_validas):
    """
    Retorna valor se válido nas opções, senão retorna None.
    Evita erro "Invalid value" nos ui.select().
    """
    valor = processo.get(campo, '')
    if isinstance(opcoes_validas, list):
        return valor if valor in opcoes_validas else None
    return valor


def get_safe_ids(processo, campo, opcoes_dict):
    """
    Retorna lista de IDs que realmente existem nas opções.
    Filtra IDs inválidos para evitar erros nos selects múltiplos.
    """
    ids = processo.get(campo, [])
    if not isinstance(ids, list):
        ids = []
    return [id for id in ids if id in opcoes_dict]


def limpar_numero_processo(numero):
    """
    Remove códigos entre parênteses do número do processo para melhor legibilidade.
    
    Exemplos de códigos removidos:
    - "(CNI01CV01)" 
    - "(FNSVEFE01)"
    - "(RIN0201)"
    - "(GMM0101)"
    - "(MFACR01)"
    
    Args:
        numero: Número do processo com ou sem códigos
        
    Returns:
        Número limpo sem códigos entre parênteses
        
    Nota: Esta função é APENAS para exibição. O número original permanece 
          inalterado no banco de dados.
    """
    if not numero:
        return numero
    
    try:
        # Remove qualquer coisa entre parênteses e espaços extras
        numero_limpo = re.sub(r'\s*\([^)]*\)\s*', '', numero).strip()
        return numero_limpo
    except Exception as e:
        logger.error(f"Erro ao limpar número do processo: {e}")
        return numero  # Retorna original em caso de erro

# Cache de dados para selects - DADOS REAIS DAS ABAS DO WORKSPACE
cache_sistema = {
    'clientes': [],           # Aba "Clientes" (vg_pessoas)
    'outros_envolvidos': [],  # Aba "Outros Envolvidos" (vg_envolvidos)
    'parceiros': [],          # Aba "Parceiros" (vg_parceiros)
    'casos': [],              # Casos reais do workspace
    'processos': []           # Processos para processo pai
}

def carregar_cache_sistema():
    """
    Carrega dados corretos de cada aba do módulo Pessoas do workspace.
    
    ESTRUTURA CORRETA:
    - clientes: Aba "Clientes" (vg_pessoas) → Campo "Clientes (Autores)"
    - outros_envolvidos: Aba "Outros Envolvidos" (vg_envolvidos) → Campo "Parte Contrária (Réus)"
    - parceiros: Aba "Parceiros" (vg_parceiros) → Campo "Outros Envolvidos"
    """
    try:
        logger.info("[CACHE] Iniciando carregamento de dados do sistema...")
        
        # CLIENTES - da aba "Clientes"
        from ..visao_geral.pessoas.database import listar_pessoas
        cache_sistema['clientes'] = listar_pessoas()
        logger.info(f"[CACHE] ✅ Clientes carregados: {len(cache_sistema['clientes'])}")
        
        # OUTROS ENVOLVIDOS - da aba "Outros Envolvidos"
        from ..visao_geral.pessoas.database import listar_envolvidos
        cache_sistema['outros_envolvidos'] = listar_envolvidos()
        logger.info(f"[CACHE] ✅ Outros Envolvidos carregados: {len(cache_sistema['outros_envolvidos'])}")
        
        # PARCEIROS - da aba "Parceiros"
        from ..visao_geral.pessoas.database import listar_parceiros
        cache_sistema['parceiros'] = listar_parceiros()
        logger.info(f"[CACHE] ✅ Parceiros carregados: {len(cache_sistema['parceiros'])}")
        
        # CASOS - para vinculação
        cache_sistema['casos'] = listar_casos()
        logger.info(f"[CACHE] ✅ Casos carregados: {len(cache_sistema['casos'])}")
        
        # PROCESSOS - para processo pai
        cache_sistema['processos'] = listar_processos_pais()
        logger.info(f"[CACHE] ✅ Processos carregados: {len(cache_sistema['processos'])}")
        
        logger.info("[CACHE] 🎉 Cache do sistema carregado com sucesso!")
        
    except Exception as e:
        logger.error(f"[CACHE] ❌ Erro ao carregar cache do sistema: {e}")
        import traceback
        traceback.print_exc()
        
        # Garantir que cache existe mesmo vazio para evitar erros
        cache_sistema.setdefault('clientes', [])
        cache_sistema.setdefault('outros_envolvidos', [])
        cache_sistema.setdefault('parceiros', [])
        cache_sistema.setdefault('casos', [])
        cache_sistema.setdefault('processos', [])

def criar_cliente_rapido_inline(select_component):
    """
    Cria cliente rapidamente com tipo PF/PJ e vincula automaticamente.
    Cliente é criado na aba "Clientes" (vg_pessoas).
    """
    with ui.dialog() as dialog_cliente, ui.card().classes('w-96 p-4'):
        ui.label('➕ Novo Cliente').classes('text-lg font-bold mb-3')
        
        # TIPO PF/PJ
        tipo_select = ui.select(
            ['PF', 'PJ'],
            label='Tipo',
            value='PF'
        ).classes('w-full mb-2').props('outlined')
        
        # NOME
        nome_input = ui.input(
            'Nome Completo',
            placeholder='Digite o nome completo'
        ).classes('w-full mb-2').props('outlined autofocus')
        
        # CPF/CNPJ
        cpf_input = ui.input(
            'CPF',
            placeholder='000.000.000-00'
        ).classes('w-full mb-4').props('outlined')
        
        # Atualizar labels dinamicamente
        def atualizar_campos(e):
            if e.value == 'PF':
                nome_input.label = 'Nome Completo'
                nome_input.placeholder = 'Digite o nome completo'
                cpf_input.label = 'CPF'
                cpf_input.placeholder = '000.000.000-00'
            else:
                nome_input.label = 'Razão Social'
                nome_input.placeholder = 'Digite a razão social'
                cpf_input.label = 'CNPJ'
                cpf_input.placeholder = '00.000.000/0000-00'
            nome_input.update()
            cpf_input.update()
        
        tipo_select.on('update:model-value', atualizar_campos)
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog_cliente.close).props('flat color=grey')
            
            async def salvar_cliente():
                if not nome_input.value or not nome_input.value.strip():
                    ui.notify('⚠ Nome é obrigatório', type='negative')
                    return
                
                try:
                    # Preparar dados
                    dados_cliente = {
                        'nome': nome_input.value.strip(),
                        'nome_completo': nome_input.value.strip(),
                        'nome_exibicao': nome_input.value.strip(),
                        'tipo_pessoa': tipo_select.value
                    }
                    
                    # CPF ou CNPJ
                    if tipo_select.value == 'PF':
                        dados_cliente['cpf'] = cpf_input.value.strip() if cpf_input.value else ''
                    else:
                        dados_cliente['cnpj'] = cpf_input.value.strip() if cpf_input.value else ''
                    
                    # Criar cliente na vg_pessoas
                    novo_id = criar_pessoa(dados_cliente)
                    
                    if novo_id:
                        # Recarregar cache
                        carregar_cache_sistema()
                        
                        # VINCULAR AUTOMATICAMENTE
                        atual = list(select_component.value or [])
                        if novo_id not in atual:
                            atual.append(novo_id)
                            select_component.value = atual
                            select_component.update()
                        
                        tipo_emoji = '👤' if tipo_select.value == 'PF' else '🏢'
                        ui.notify(
                            f'✅ {tipo_emoji} Cliente {nome_input.value} criado e vinculado!',
                            type='positive',
                            timeout=2000
                        )
                        dialog_cliente.close()
                        logger.info(f"[CRIAÇÃO] Cliente {tipo_select.value} criado: {nome_input.value} (ID: {novo_id})")
                    else:
                        ui.notify('❌ Erro ao criar cliente', type='negative')
                
                except Exception as e:
                    logger.error(f"Erro ao criar cliente: {e}")
                    import traceback
                    traceback.print_exc()
                    ui.notify(f'❌ Erro: {str(e)}', type='negative')
            
            ui.button('Salvar e Vincular', on_click=salvar_cliente).props('color=positive')
    
    dialog_cliente.open()


def criar_pessoa_rapida_inline(select_component, tipo_label):
    """
    Cria pessoa rapidamente com tipo PF/PJ/Ente Público e vincula automaticamente.
    
    Tipo_label determina em qual aba será criada:
    - "Parte Contrária" → cria em vg_envolvidos (Outros Envolvidos)
    - "Envolvido" → cria em vg_parceiros (Parceiros)
    """
    with ui.dialog() as dialog_pessoa, ui.card().classes('w-96 p-4'):
        ui.label(f'➕ Nova Pessoa ({tipo_label})').classes('text-lg font-bold mb-3')
        
        # TIPO PF/PJ/Ente Público
        tipo_select = ui.select(
            ['PF', 'PJ', 'Ente Público'],
            label='Tipo',
            value='PF'
        ).classes('w-full mb-2').props('outlined')
        
        # NOME
        nome_input = ui.input(
            'Nome Completo',
            placeholder='Digite o nome completo'
        ).classes('w-full mb-2').props('outlined autofocus')
        
        # CPF/CNPJ
        cpf_input = ui.input(
            'CPF',
            placeholder='000.000.000-00'
        ).classes('w-full mb-4').props('outlined')
        
        # Atualizar labels dinamicamente
        def atualizar_campos(e):
            if e.value == 'PF':
                nome_input.label = 'Nome Completo'
                nome_input.placeholder = 'Digite o nome completo'
                cpf_input.label = 'CPF'
                cpf_input.placeholder = '000.000.000-00'
            elif e.value == 'PJ':
                nome_input.label = 'Razão Social'
                nome_input.placeholder = 'Digite a razão social'
                cpf_input.label = 'CNPJ'
                cpf_input.placeholder = '00.000.000/0000-00'
            else:  # Ente Público
                nome_input.label = 'Nome do Ente'
                nome_input.placeholder = 'Ex: Município de Florianópolis'
                cpf_input.label = 'CNPJ'
                cpf_input.placeholder = '00.000.000/0000-00'
            nome_input.update()
            cpf_input.update()
        
        tipo_select.on('update:model-value', atualizar_campos)
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog_pessoa.close).props('flat color=grey')
            
            async def salvar_pessoa():
                if not nome_input.value or not nome_input.value.strip():
                    ui.notify('⚠ Nome é obrigatório', type='negative')
                    return
                
                try:
                    # Preparar dados
                    dados_pessoa = {
                        'nome': nome_input.value.strip(),
                        'nome_completo': nome_input.value.strip(),
                        'nome_exibicao': nome_input.value.strip(),
                    }
                    
                    # CPF ou CNPJ
                    if tipo_select.value == 'PF':
                        dados_pessoa['cpf'] = cpf_input.value.strip() if cpf_input.value else ''
                        dados_pessoa['tipo_envolvido'] = 'PF'
                        dados_pessoa['tipo_parceiro'] = 'PF'
                    elif tipo_select.value == 'PJ':
                        dados_pessoa['cnpj'] = cpf_input.value.strip() if cpf_input.value else ''
                        dados_pessoa['tipo_envolvido'] = 'PJ'
                        dados_pessoa['tipo_parceiro'] = 'PJ'
                    else:  # Ente Público
                        dados_pessoa['cnpj'] = cpf_input.value.strip() if cpf_input.value else ''
                        dados_pessoa['tipo_envolvido'] = 'Ente Público'
                        dados_pessoa['tipo_parceiro'] = 'Ente Público'
                    
                    # Criar na coleção correta baseado no tipo_label
                    novo_id = None
                    
                    if tipo_label == 'Parte Contrária':
                        # Criar em vg_envolvidos
                        novo_id = criar_envolvido(dados_pessoa)
                    elif tipo_label == 'Envolvido':
                        # Criar em vg_parceiros
                        novo_id = criar_parceiro(dados_pessoa)
                    else:
                        ui.notify('⚠ Tipo de pessoa inválido', type='negative')
                        return
                    
                    if novo_id:
                        # Recarregar cache
                        carregar_cache_sistema()
                        
                        # Adicionar ao select
                        atual = list(select_component.value or [])
                        if novo_id not in atual:
                            atual.append(novo_id)
                            select_component.value = atual
                            select_component.update()
                        
                        tipo_emoji = '👤' if tipo_select.value == 'PF' else ('🏢' if tipo_select.value == 'PJ' else '🏛️')
                        ui.notify(
                            f'✅ {tipo_emoji} {nome_input.value} criado e vinculado!',
                            type='positive',
                            timeout=2000
                        )
                        dialog_pessoa.close()
                        logger.info(f"[CRIAÇÃO] {tipo_label} {tipo_select.value} criado: {nome_input.value} (ID: {novo_id})")
                    else:
                        ui.notify('❌ Erro ao criar pessoa', type='negative')
                
                except Exception as e:
                    logger.error(f"Erro ao criar {tipo_label}: {e}")
                    import traceback
                    traceback.print_exc()
                    ui.notify(f'❌ Erro: {str(e)}', type='negative')
            
            ui.button('Salvar e Vincular', on_click=salvar_pessoa).props('color=positive')
    
    dialog_pessoa.open()


def sugerir_pessoa(nome, select_comp, tipo='cliente'):
    """
    Vincula pessoa/cliente sugerido da planilha ao campo correto.
    
    Args:
        nome: Nome da sugestão da planilha
        select_comp: Componente select onde adicionar
        tipo: 'cliente', 'outro_envolvido' ou 'parceiro'
    """
    busca = nome.lower()
    
    # Definir qual cache usar baseado no tipo
    if tipo == 'cliente':
        opcoes = {
            c['_id']: c.get('nome_exibicao', c.get('nome_completo', c.get('nome', '')))
            for c in cache_sistema.get('clientes', [])
        }
    elif tipo == 'outro_envolvido':
        opcoes = {
            p['_id']: p.get('nome_exibicao', p.get('nome_completo', p.get('nome', '')))
            for p in cache_sistema.get('outros_envolvidos', [])
        }
    elif tipo == 'parceiro':
        opcoes = {
            p['_id']: p.get('nome_exibicao', p.get('nome_completo', p.get('nome', '')))
            for p in cache_sistema.get('parceiros', [])
        }
    else:
        ui.notify('⚠ Tipo inválido', type='warning')
        return
    
    # Buscar correspondência (busca flexível bidirecional)
    for id_item, nome_item in opcoes.items():
        nome_item_lower = nome_item.lower()
        if busca in nome_item_lower or nome_item_lower in busca:
            atual = list(select_comp.value or [])
            if id_item not in atual:
                atual.append(id_item)
                select_comp.value = atual
                select_comp.update()
                ui.notify(f'✅ Vinculado: {nome_item}', type='info', position='top', timeout=1500)
                logger.info(f"[SUGESTÃO] Vinculado {nome} → {nome_item} (tipo: {tipo})")
                return
    
    ui.notify(f'⚠ "{nome}" não encontrado no sistema', type='warning', position='top', timeout=2000)
    logger.warning(f"[SUGESTÃO] Não encontrado: {nome} (tipo: {tipo})")


def abrir_modal_completar(processo, callback_refresh=None):
    """
    Modal OTIMIZADO E COMPACTO para completar dados do processo.
    
    Melhorias implementadas:
    - Layout compacto em 2 colunas (65% + 35%)
    - Botões inline para criar clientes/pessoas rapidamente
    - Único botão "SALVAR E PRÓXIMO" que migra direto para workspace
    - Cópia automática do número ao abrir
    - Fluxo contínuo: salva → remove da migração → abre próximo
    """
    try:
        numero_original = processo.get('numero_processo', 'SEM_NUMERO')
        numero_limpo = limpar_numero_processo(numero_original)
        
        logger.info(f"[MODAL] Abrindo modal para processo: {numero_limpo}")
        
        # CÓPIA AUTOMÁTICA DO NÚMERO AO ABRIR MODAL
        try:
            # Escapa aspas para JavaScript
            numero_escapado = numero_limpo.replace("'", "\\'").replace('"', '\\"')
            
            # Copia para clipboard usando JavaScript
            ui.run_javascript(f'''
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText("{numero_escapado}").then(
                        () => console.log("✓ Número copiado automaticamente: {numero_escapado}"),
                        (err) => console.error("✗ Erro ao copiar:", err)
                    );
                }} else {{
                    console.warn("Clipboard API não disponível neste navegador");
                }}
            ''')
            
            # Notificação discreta de confirmação
            ui.notify(
                f'📋 Número {numero_limpo} copiado!', 
                type='info', 
                position='top-right',
                timeout=2000
            )
        except Exception as e:
            logger.warning(f"[MODAL] Erro na cópia automática (não crítico): {e}")
            # Não bloqueia abertura do modal se cópia falhar
        
        # Cria o dialog
        with ui.dialog() as modal:
            with ui.card().classes('w-full max-w-6xl p-0 max-h-[90vh] overflow-hidden'):
                # Header com fundo verde e botão de cópia
                with ui.row().classes('w-full p-4 items-center justify-between').style('background-color: #223631; color: white;'):
                    # Título e botão de cópia manual
                    with ui.row().classes('items-center gap-3'):
                        ui.label(f"Processo: {numero_limpo}").classes('text-xl font-bold')
                        
                        # Botão para copiar novamente se necessário
                        def copiar_numero_novamente():
                            try:
                                numero_escapado = numero_limpo.replace("'", "\\'").replace('"', '\\"')
                                ui.run_javascript(f'''
                                    navigator.clipboard.writeText("{numero_escapado}").then(
                                        () => console.log("✓ Número copiado novamente"),
                                        (err) => console.error("✗ Erro ao copiar:", err)
                                    );
                                ''')
                                ui.notify('✓ Copiado novamente!', type='positive', timeout=1500, position='top-right')
                            except Exception as e:
                                logger.error(f"Erro ao copiar número: {e}")
                                ui.notify('Erro ao copiar', type='negative')
                        
                        ui.button(
                            icon='content_copy',
                            on_click=copiar_numero_novamente
                        ).props('flat round color=white size=sm').tooltip('Copiar número do processo')
                    
                    ui.button(icon='close', on_click=modal.close).props('flat round color=white')

                # Corpo do modal
                with ui.row().classes('w-full p-4 gap-4 overflow-y-auto max-h-[calc(90vh-140px)]'):
                    # COLUNA ESQUERDA - Formulário (65%)
                    with ui.column().classes('flex-[0.65] gap-3'):
                        ui.label('📋 Dados do Processo').classes('text-sm font-bold text-[#223631]')
                        
                        titulo_input = ui.input(
                            'Título do Processo',
                            value=processo.get('titulo_processo', ''),
                            placeholder='Ex: Ação de Cobrança - Cliente X'
                        ).classes('w-full').props('outlined')
                        
                        # CORREÇÃO: Validar valores antes de passar para os selects
                        # Núcleo: só passa valor se existir na lista
                        nucleo_valor = processo.get('nucleo', '')
                        nucleo_valor = nucleo_valor if nucleo_valor in NUCLEOS_PROCESSO else None
                        
                        # Área: só passa valor se existir na lista
                        area_valor = processo.get('area_direito', '')
                        area_valor = area_valor if area_valor in AREAS_PROCESSO else None
                        
                        # Prioridade: garante que seja P1, P2, P3 ou P4
                        prioridade_valor = processo.get('prioridade', 'P4')
                        if prioridade_valor not in ['P1', 'P2', 'P3', 'P4']:
                            prioridade_valor = 'P4'
                        
                        with ui.row().classes('w-full gap-4'):
                            nucleo_input = ui.select(
                                NUCLEOS_PROCESSO,
                                label='Núcleo',
                                value=nucleo_valor
                            ).classes('flex-1').props('outlined clearable')
                            
                            area_input = ui.select(
                                AREAS_PROCESSO,
                                label='Área do Direito',
                                value=area_valor
                            ).classes('flex-1').props('outlined clearable')
                        
                        with ui.row().classes('w-full gap-4'):
                            prioridade_input = ui.select(
                                ['P1', 'P2', 'P3', 'P4'],
                                label='Prioridade',
                                value=prioridade_valor
                            ).classes('flex-1').props('outlined')
                            
                            link_input = ui.input(
                                'Link EPROC',
                                value=processo.get('link_eproc', ''),
                                placeholder='https://eproc.tjsc.jus.br/...'
                            ).classes('flex-1').props('outlined')

                        ui.separator().classes('my-2')
                        
                        # =============================================================
                        # SEÇÃO DE VÍNCULOS DE PESSOAS - COM BOTÕES INLINE
                        # =============================================================
                        ui.label('👥 Vínculos de Pessoas').classes('text-sm font-bold text-[#223631]')
                        
                        # A) CLIENTES - da aba "Clientes" (vg_pessoas)
                        opcoes_clientes = {
                            c['_id']: c.get('nome_exibicao', c.get('nome_completo', c.get('nome', 'Sem nome')))
                            for c in cache_sistema.get('clientes', [])
                        }
                        clientes_ids = get_safe_ids(processo, 'clientes', opcoes_clientes)
                        
                        # CLIENTES com botão inline de criação
                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                            clientes_input = ui.select(
                                opcoes_clientes,
                                label='Clientes (Autores)',
                                value=clientes_ids,
                                multiple=True
                            ).classes('flex-1').props('outlined dense use-chips')
                            ui.button(
                                icon='add',
                                on_click=lambda: criar_cliente_rapido_inline(clientes_input)
                            ).props('outline color=primary dense').tooltip('Criar e vincular cliente')
                        
                        # B) PARTE CONTRÁRIA - da aba "Outros Envolvidos" (vg_envolvidos)
                        opcoes_outros_envolvidos = {
                            p['_id']: p.get('nome_exibicao', p.get('nome_completo', p.get('nome', 'Sem nome')))
                            for p in cache_sistema.get('outros_envolvidos', [])
                        }
                        contraria_ids = get_safe_ids(processo, 'parte_contraria', opcoes_outros_envolvidos)
                        
                        # PARTE CONTRÁRIA com botão inline de criação
                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                            contraria_input = ui.select(
                                opcoes_outros_envolvidos,
                                label='Parte Contrária (Réus)',
                                value=contraria_ids,
                                multiple=True
                            ).classes('flex-1').props('outlined dense use-chips')
                            ui.button(
                                icon='add',
                                on_click=lambda: criar_pessoa_rapida_inline(contraria_input, 'Parte Contrária')
                            ).props('outline color=red dense').tooltip('Criar e vincular pessoa')
                        
                        # C) OUTROS ENVOLVIDOS - da aba "Parceiros" (vg_parceiros)
                        opcoes_parceiros = {
                            p['_id']: p.get('nome_exibicao', p.get('nome_completo', p.get('nome', 'Sem nome')))
                            for p in cache_sistema.get('parceiros', [])
                        }
                        outros_ids = get_safe_ids(processo, 'outros_envolvidos', opcoes_parceiros)
                        
                        # OUTROS ENVOLVIDOS com botão inline de criação
                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                            outros_input = ui.select(
                                opcoes_parceiros,
                                label='Outros Envolvidos',
                                value=outros_ids,
                                multiple=True
                            ).classes('flex-1').props('outlined dense use-chips')
                            ui.button(
                                icon='add',
                                on_click=lambda: criar_pessoa_rapida_inline(outros_input, 'Envolvido')
                            ).props('outline color=grey dense').tooltip('Criar e vincular envolvido')
                        
                        # =============================================================
                        # SEÇÃO DE VÍNCULOS COM CASOS - DADOS REAIS DO SISTEMA
                        # =============================================================
                        ui.separator().classes('my-2')
                        ui.label('📁 Casos Vinculados').classes('text-sm font-bold text-[#223631]')
                        
                        # CASOS REAIS do workspace (vg_casos)
                        opcoes_casos = {
                            c['_id']: c.get('titulo', f"Caso {c.get('numero', 'S/N')}")
                            for c in cache_sistema.get('casos', [])
                        }
                        
                        casos_ids = processo.get('casos_vinculados', [])
                        if not isinstance(casos_ids, list):
                            casos_ids = []
                        casos_ids = [id for id in casos_ids if id in opcoes_casos]
                        
                        casos_input = ui.select(
                            opcoes_casos,
                            label='Casos',
                            value=casos_ids,
                            multiple=True
                        ).classes('w-full').props('outlined dense use-chips')

                    # COLUNA DIREITA - Sugestões da Planilha (35%)
                    with ui.column().classes('flex-[0.35] bg-amber-50 p-3 rounded-lg border border-amber-200 max-h-[calc(90vh-200px)] overflow-y-auto'):
                        ui.label('💡 Sugestões da Planilha').classes('font-bold text-amber-900 mb-1')
                        ui.label('Clique no botão + para vincular').classes('text-[10px] text-amber-700 mb-4')
                        
                        # Função auxiliar para sugerir pessoa/cliente
                        def sugerir_pessoa(nome, select_comp, tipo='pessoa'):
                            """
                            Vincula pessoa ou cliente sugerido da planilha ao campo correto.
                            
                            Args:
                                nome: Nome da sugestão da planilha
                                select_comp: Componente select onde adicionar
                                tipo: 'cliente' (busca em clientes) ou 'pessoa' (busca em pessoas)
                            """
                            busca = nome.lower()
                            
                            # Definir qual cache usar baseado no tipo
                            if tipo == 'cliente':
                                opcoes = {
                                    c['_id']: c.get('nome_exibicao', c.get('nome', c.get('full_name', '')))
                                    for c in cache_sistema.get('clientes', [])
                                }
                            else:
                                opcoes = {
                                    p['_id']: p.get('nome_exibicao', p.get('nome', p.get('full_name', '')))
                                    for p in cache_sistema.get('pessoas', [])
                                }
                            
                            # Buscar correspondência (busca flexível)
                            for id_item, nome_item in opcoes.items():
                                nome_item_lower = nome_item.lower()
                                # Busca bidirecional: nome em nome_item OU nome_item em nome
                                if busca in nome_item_lower or nome_item_lower in busca:
                                    atual = list(select_comp.value or [])
                                    if id_item not in atual:
                                        atual.append(id_item)
                                        select_comp.value = atual
                                        ui.notify(f"✓ Vinculado: {nome_item}", type='positive', position='top')
                                        logger.info(f"[SUGESTÃO] Vinculado {nome} → {nome_item} (ID: {id_item})")
                                        return
                            
                            ui.notify(f"⚠ '{nome}' não encontrado no sistema", type='warning', position='top')
                            logger.warning(f"[SUGESTÃO] Não encontrado: {nome}")
                        
                        # AUTORES - Vinculam como CLIENTES (vg_pessoas)
                        if processo.get('autores_sugestao'):
                            ui.label('Autores → Clientes:').classes('text-xs font-bold text-blue-700 mb-1')
                            for a in processo.get('autores_sugestao', []):
                                with ui.row().classes('w-full items-center justify-between bg-white p-1.5 rounded mb-1 border border-blue-100'):
                                    ui.label(a[:25]).classes('text-[10px] flex-1 truncate')
                                    ui.button(
                                        icon='add',
                                        on_click=lambda nome=a: sugerir_pessoa(nome, clientes_input, tipo='cliente')
                                    ).props('flat round dense size=xs color=blue')
                        
                        # RÉUS - Vinculam como PARTE CONTRÁRIA (vg_envolvidos)
                        if processo.get('reus_sugestao'):
                            ui.label('Réus → Parte Contrária:').classes('text-xs font-bold text-red-700 mb-1 mt-2')
                            for r in processo.get('reus_sugestao', []):
                                with ui.row().classes('w-full items-center justify-between bg-white p-1.5 rounded mb-1 border border-red-100'):
                                    ui.label(r[:25]).classes('text-[10px] flex-1 truncate')
                                    ui.button(
                                        icon='add',
                                        on_click=lambda nome=r: sugerir_pessoa(nome, contraria_input, tipo='outro_envolvido')
                                    ).props('flat round dense size=xs color=red')

                # ============ RODAPÉ - BOTÃO ÚNICO ============
                with ui.row().classes('w-full bg-gray-100 p-3 justify-end'):
                    async def salvar_e_migrar():
                        """
                        Salva processo no workspace e abre próximo automaticamente.
                        Fluxo: Valida → Cria em vg_processos → Remove de processos_migracao → Próximo
                        """
                        logger.info("=" * 80)
                        logger.info("[MIGRAÇÃO] INICIANDO SALVAMENTO DE PROCESSO")
                        logger.info("=" * 80)
                        
                        # Validação
                        if not titulo_input.value or not titulo_input.value.strip():
                            ui.notify('❌ Título é obrigatório!', type='negative')
                            logger.warning("[MIGRAÇÃO] Salvamento cancelado: título vazio")
                            return
                        
                        # Preparar dados completos para o workspace
                        # CORREÇÃO: Usar nomes de campos corretos conforme database.py
                        dados_processo = {
                            'numero': processo['numero_processo'],
                            'titulo': titulo_input.value.strip(),
                            'tipo': 'Judicial',
                            'sistema_processual': processo.get('sistema_processual', 'eproc - TJSC - 1ª instância'),
                            'status': 'Ativo',
                            'resultado': 'Pendente',
                            'area': area_input.value or '',
                            'nucleo': nucleo_input.value or '',
                            'estado': processo.get('estado', 'Santa Catarina'),
                            'comarca': '',
                            'vara': '',
                            'caso_id': '',
                            'caso_titulo': '',
                            'clientes': clientes_input.value or [],
                            'clientes_nomes': [],
                            'parte_contraria': '',
                            'parte_contraria_tipo': 'PF',
                            'grupo_id': '',
                            'grupo_nome': '',
                            'processo_pai_id': '',
                            'processo_pai_titulo': '',
                            'processos_filhos_ids': [],
                            'cenario_melhor': '',
                            'cenario_intermediario': '',
                            'cenario_pior': '',
                            'data_abertura': processo.get('data_abertura', ''),
                            'data_ultima_movimentacao': '',
                            'responsavel': '',
                            'responsavel_nome': processo.get('responsavel', 'Lenon Taques'),
                            'prioridade': prioridade_input.value or 'P4',
                            'observacoes': f"Migrado em {datetime.now().strftime('%d/%m/%Y')}",
                            'link': link_input.value.strip() if link_input.value else ''
                        }
                        
                        logger.info("[MIGRAÇÃO] Dados preparados:")
                        logger.info(f"  - Número: {dados_processo['numero']}")
                        logger.info(f"  - Título: {dados_processo['titulo']}")
                        logger.info(f"  - Núcleo: {dados_processo['nucleo']}")
                        logger.info(f"  - Área: {dados_processo['area']}")
                        logger.info(f"  - Clientes: {len(dados_processo['clientes'])} item(s)")
                        logger.info(f"  - Status: {dados_processo['status']}")
                        
                        try:
                            # CRIAR NO WORKSPACE (vg_processos)
                            logger.info("[MIGRAÇÃO] Chamando criar_processo_workspace()...")
                            processo_id = criar_processo_workspace(dados_processo)
                            logger.info(f"[MIGRAÇÃO] Resultado: {processo_id}")
                            
                            if processo_id:
                                logger.info(f"[MIGRAÇÃO] ✅ Processo criado no workspace com sucesso!")
                                logger.info(f"[MIGRAÇÃO] ID do processo criado: {processo_id}")
                                
                                # REMOVER DA MIGRAÇÃO
                                logger.info(f"[MIGRAÇÃO] Removendo processo {processo['_id']} da coleção de migração...")
                                from mini_erp.firebase_config import get_db
                                db = get_db()
                                db.collection('processos_migracao').document(processo['_id']).delete()
                                logger.info(f"[MIGRAÇÃO] ✅ Processo removido da migração")
                                
                                # Notificar sucesso
                                ui.notify('✅ Processo migrado com sucesso!', type='positive', timeout=2000)
                                modal.close()
                                
                                # Atualizar interface
                                logger.info("[MIGRAÇÃO] Atualizando interface...")
                                if callback_refresh:
                                    callback_refresh()
                                
                                # Abrir próximo pendente automaticamente
                                await asyncio.sleep(0.3)
                                proximos = listar_processos_migracao('pendente')
                                
                                if proximos:
                                    logger.info(f"[MIGRAÇÃO] Abrindo próximo processo: {proximos[0].get('numero_processo', 'DESCONHECIDO')}")
                                    abrir_modal_completar(proximos[0], callback_refresh)
                                else:
                                    logger.info("[MIGRAÇÃO] 🎉 Todos os processos foram migrados!")
                                    ui.notify('🎉 Todos os processos foram migrados!', type='positive', position='center', timeout=4000)
                            else:
                                logger.error("[MIGRAÇÃO] ❌ criar_processo_workspace retornou None ou False")
                                logger.error("[MIGRAÇÃO] Verifique a função criar_processo no database.py")
                                ui.notify('❌ Erro ao criar processo no workspace', type='negative', timeout=5000)
                        
                        except Exception as e:
                            logger.error("=" * 80)
                            logger.error("[MIGRAÇÃO] ERRO CRÍTICO AO MIGRAR PROCESSO")
                            logger.error("=" * 80)
                            logger.error(f"Tipo do erro: {type(e).__name__}")
                            logger.error(f"Mensagem: {str(e)}")
                            logger.error("Stack trace completo:")
                            import traceback
                            traceback.print_exc()
                            ui.notify(f'❌ Erro ao migrar: {str(e)}', type='negative', timeout=5000)
                    
                    ui.button(
                        'SALVAR E PRÓXIMO →',
                        icon='arrow_forward',
                        on_click=salvar_e_migrar
                    ).props('color=positive size=md no-caps').classes('px-6')

        # Abre o modal
        modal.open()
        logger.info(f"[MODAL] Modal aberto com sucesso")
        
    except Exception as e:
        logger.error(f"[MODAL] Erro ao abrir modal: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Erro ao abrir modal: {str(e)}", type='negative')


@ui.page('/admin/migracao-processos')
def admin_migracao_processos():
    """Página principal de migração administrativa."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Estilos customizados para evitar erros de renderização
    ui.add_head_html('''
        <style>
            .migracao-sidebar { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
            .card-pendente { border-left: 5px solid #fbbf24; }
            .card-concluido { border-left: 5px solid #059669; }
            .badge-pendente { background-color: #fbbf24; color: #1f2937; }
            .badge-concluido { background-color: #059669; color: white; }
        </style>
    ''')

    carregar_cache_sistema()
    
    # Estado da página
    estado = {'filtro_status': 'todos'}

    with layout('Migração de Processos', breadcrumbs=[('Admin', None), ('Migração EPROC', None)]):
        with ui.row().classes('w-full gap-0 no-wrap h-[calc(100vh-150px)]'):
            
            # SIDEBAR
            with ui.column().classes('w-1/4 p-6 migracao-sidebar h-full'):
                ui.label('Migração de Processos').classes('text-xl font-bold mb-4')
                
                async def handle_import():
                    with ui.dialog() as loading, ui.card():
                        ui.spinner(size='lg')
                        ui.label('Processando planilha...')
                    loading.open()
                    res = importar_planilha_migracao()
                    loading.close()
                    if res['sucesso']:
                        ui.notify(f"Sucesso! {res['importados']} processos importados.", type='positive')
                        area_progresso.refresh()
                        lista_processos_migracao.refresh()
                    else:
                        ui.notify(f"Erro: {res['erro']}", type='negative')

                ui.button('Importar Planilha', icon='upload_file', on_click=handle_import).classes('w-full mb-6').props('color=primary')
                
                @ui.refreshable
                def area_progresso():
                    stats = obter_estatisticas_migracao()
                    ui.label('Progresso').classes('text-sm font-medium text-gray-500 mb-2')
                    with ui.row().classes('w-full items-center gap-2 mb-1'):
                        ui.label(f"{stats['concluidos']} / {stats['total']}").classes('text-lg font-bold')
                    ui.linear_progress(value=stats['progresso']/100).classes('w-full mb-6').props('color=positive stripe')

                area_progresso()
                
                ui.select(
                    {'todos': 'Todos', 'pendente': 'Pendentes', 'concluido': 'Concluídos'},
                    value='todos',
                    label='Filtrar por Status',
                    on_change=lambda e: (setattr(estado, 'filtro_status', e.value), lista_processos_migracao.refresh())
                ).classes('w-full mb-4').props('outlined dense')

                ui.button('Finalizar Migração', icon='check_circle', on_click=lambda: finalizar_fluxo()).classes('w-full mt-auto').props('color=positive outline')

            # CONTEÚDO PRINCIPAL
            with ui.column().classes('w-3/4 p-8 h-full overflow-y-auto'):
                @ui.refreshable
                def lista_processos_migracao():
                    processos = listar_processos_migracao(estado.get('filtro_status', 'todos'))
                    if not processos:
                        ui.label('Nenhum processo encontrado.').classes('text-gray-400 italic')
                        return

                    for p in processos:
                        status = p.get('status_migracao', 'pendente')
                        # Limpa número do processo para exibição
                        numero_limpo = limpar_numero_processo(p['numero_processo'])
                        
                        with ui.card().classes(f'w-full mb-4 {"card-pendente" if status == "pendente" else "card-concluido"}'):
                            with ui.row().classes('w-full items-center justify-between'):
                                with ui.column():
                                    ui.label(numero_limpo).classes('text-lg font-bold')
                                    ui.label(p.get('classe_processo', '-')).classes('text-xs text-gray-500')
                                
                                def criar_callback_refresh():
                                    """Cria callback para atualizar a página após salvar."""
                                    def refresh():
                                        area_progresso.refresh()
                                        lista_processos_migracao.refresh()
                                    return refresh
                                
                                ui.button(
                                    'Completar' if status == 'pendente' else 'Editar', 
                                    icon='edit',
                                    on_click=lambda p=p: abrir_modal_completar(p, criar_callback_refresh())
                                ).props('flat color=primary')

                lista_processos_migracao()

        async def finalizar_fluxo():
            res = finalizar_migracao_completa()
            if res['sucesso']:
                ui.notify(res['mensagem'], type='positive')
                ui.navigate.to('/visao-geral/processos')
            else:
                ui.notify(res['erro'], type='warning')
