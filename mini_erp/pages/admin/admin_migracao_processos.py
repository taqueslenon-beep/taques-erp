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
    finalizar_migracao_completa, atualizar_status_migracao,
    excluir_processo_migracao, popular_processos_gilberto
)
from .validacao_pessoas_migracao import (
    validar_pessoas_migracao, cadastrar_pessoas_em_massa,
    preparar_pessoas_para_ui
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
from typing import Dict, Any

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


def obter_nome_pessoa(pessoa_id):
    """Busca nome de uma pessoa por ID para converter vínculo em string."""
    try:
        from ..visao_geral.pessoas.database import listar_pessoas_colecao_people
        pessoas = listar_pessoas_colecao_people()
        pessoa = next((p for p in pessoas if p.get('_id') == pessoa_id), None)
        if pessoa:
            return {
                'nome': pessoa.get('nome_exibicao', pessoa.get('nome', 'Não informado')),
                'tipo': pessoa.get('tipo', 'PF')
            }
        return {'nome': 'Não informado', 'tipo': 'PF'}
    except Exception as e:
        logger.error(f"Erro ao buscar nome da pessoa {pessoa_id}: {e}")
        return {'nome': 'Não informado', 'tipo': 'PF'}


def converter_datetime_firestore(valor, formato_saida='%d/%m/%Y'):
    """
    Converte DatetimeWithNanoseconds do Firestore para string formatada.
    Trata também datetime Python e valores None/null.
    
    Args:
        valor: Valor que pode ser DatetimeWithNanoseconds, datetime, string, None ou outro tipo
        formato_saida: Formato de saída strftime (padrão: '%d/%m/%Y')
        
    Returns:
        String formatada conforme formato_saida ou "-" se None/inválido
    """
    if valor is None:
        return '-'
    
    try:
        # Se já for string, tenta converter para datetime e formatar
        if isinstance(valor, str):
            if valor.lower() in ('nan', 'none', ''):
                return '-'
            
            # Tenta converter string de data para datetime e formatar
            try:
                # Tenta formatos comuns de data/hora
                formatos_tentativa = [
                    '%Y-%m-%d %H:%M:%S',      # 2018-08-02 09:20:17
                    '%Y-%m-%dT%H:%M:%S',      # 2018-08-02T09:20:17
                    '%Y-%m-%dT%H:%M:%S.%f',   # 2018-08-02T09:20:17.123456
                    '%Y-%m-%dT%H:%M:%S.%fZ',  # 2018-08-02T09:20:17.123456Z
                    '%Y-%m-%d',                # 2018-08-02
                    '%d/%m/%Y',                # 02/08/2018 (já formatado)
                    '%d/%m/%Y %H:%M:%S',       # 02/08/2018 09:20:17
                ]
                
                for fmt in formatos_tentativa:
                    try:
                        dt = datetime.strptime(valor, fmt)
                        return dt.strftime(formato_saida)
                    except ValueError:
                        continue
                
                # Se nenhum formato funcionou, tenta usar fromisoformat
                if 'T' in valor or ' ' in valor:
                    dt_str_clean = valor.split('+')[0].split('Z')[0].split('.')[0]
                    dt = datetime.fromisoformat(dt_str_clean)
                    return dt.strftime(formato_saida)
                
            except (ValueError, AttributeError):
                # Se não conseguir converter, retorna string original
                # (pode ser um texto que não é data)
                pass
            
            # Se já estiver no formato desejado ou não conseguir converter, retorna como está
            return valor
        
        # Se for DatetimeWithNanoseconds do Firestore, tem método isoformat
        if hasattr(valor, 'isoformat'):
            try:
                # Tenta usar isoformat diretamente (funciona com DatetimeWithNanoseconds)
                dt_str = valor.isoformat()
                # Converte string ISO para datetime Python para formatar
                if 'T' in dt_str:
                    # Remove timezone para compatibilidade
                    dt_str_clean = dt_str.split('+')[0].split('Z')[0]
                    if '.' in dt_str_clean:
                        dt_str_clean = dt_str_clean.split('.')[0]
                    dt = datetime.fromisoformat(dt_str_clean)
                else:
                    dt = datetime.fromisoformat(dt_str)
                return dt.strftime(formato_saida)
            except (AttributeError, ValueError, TypeError) as e:
                # Fallback: tenta usar strftime se disponível
                if hasattr(valor, 'strftime'):
                    try:
                        return valor.strftime(formato_saida)
                    except:
                        pass
                # Último recurso: converte para string
                return str(valor)[:10] if len(str(valor)) > 10 else str(valor)
        
        # Se tiver método strftime (datetime Python)
        if hasattr(valor, 'strftime'):
            return valor.strftime(formato_saida)
        
        # Fallback: converte para string
        valor_str = str(valor)
        if valor_str.lower() in ('nan', 'none', ''):
            return '-'
        return valor_str
        
    except Exception as e:
        logger.warning(f"Erro ao converter data do Firestore: {e} (tipo: {type(valor).__name__})")
        return '-'


def converter_timestamps_documento(documento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte todos os campos DatetimeWithNanoseconds de um documento do Firestore.
    Evita erros de serialização JSON ao passar dados para a UI.
    
    Args:
        documento: Dicionário com dados do Firebase (pode conter DatetimeWithNanoseconds)
        
    Returns:
        Dicionário com todos os timestamps convertidos para string ISO
    """
    if not documento:
        return documento
    
    documento_convertido = dict(documento)
    
    # Campos que podem ser timestamp do Firestore
    campos_timestamp = ['data_abertura', 'data_importacao', 'data_distribuicao', 
                        'created_at', 'updated_at', 'criado_em', 'atualizado_em']
    
    for campo in campos_timestamp:
        if campo in documento_convertido and documento_convertido[campo] is not None:
            try:
                valor = documento_convertido[campo]
                # Se for DatetimeWithNanoseconds ou datetime, converte para ISO string
                if hasattr(valor, 'isoformat'):
                    documento_convertido[campo] = valor.isoformat()
                elif hasattr(valor, 'strftime'):
                    documento_convertido[campo] = valor.strftime('%Y-%m-%dT%H:%M:%S')
                elif not isinstance(valor, str):
                    # Se não for string, converte (pode ser número timestamp)
                    documento_convertido[campo] = str(valor)
            except Exception as e:
                logger.warning(f"Erro ao converter campo {campo}: {e}")
                # Mantém valor original em caso de erro
                documento_convertido[campo] = str(documento_convertido[campo]) if documento_convertido[campo] else None
    
    return documento_convertido


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
                        
                        # Área: só passa valor se existir na lista (Garante valor padrão)
                        area_valor = processo.get('area_direito', '')
                        if not area_valor or area_valor not in AREAS_PROCESSO:
                            area_valor = 'Cível'
                        
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
                        # Validação inicial
                        titulo_limpo = titulo_input.value.strip() if titulo_input.value else ""
                        if not titulo_limpo:
                            ui.notify('❌ Título é obrigatório!', type='negative')
                            return

                        # Preparar dados compatíveis com validação
                        dados_processo = {
                            # ===== CAMPOS OBRIGATÓRIOS =====
                            'numero': processo['numero_processo'],
                            'titulo': titulo_limpo,
                            'tipo': 'Judicial',
                            'status': 'Ativo',  # Valor padrão válido conforme constants.py
                            'resultado': 'Pendente',
                            
                            # ===== ÁREA (OBRIGATÓRIA - GARANTIR VALOR VÁLIDO) =====
                            'area': area_input.value if area_input.value else 'Cível',
                            
                            # ===== OUTROS CAMPOS =====
                            'nucleo': nucleo_input.value or '',
                            'sistema_processual': processo.get('sistema_processual', 'eproc - TJSC - 1ª instância'),
                            'estado': processo.get('estado', 'Santa Catarina'),
                            'responsavel': processo.get('responsavel', 'Lenon Taques'),
                            'prioridade': prioridade_input.value or 'P4',
                            'link_eproc': link_input.value or '',
                            'data_abertura': processo.get('data_abertura'),
                            
                            # ===== CLIENTES (LISTA DE IDs - CORRETO) =====
                            'clientes': clientes_input.value or [],
                            
                            # ===== PARTE CONTRÁRIA (CONVERTER DE LISTA PARA STRING) =====
                            'parte_contraria': '',
                            'parte_contraria_tipo': 'PF',
                            
                            # ===== OUTROS ENVOLVIDOS (LISTA DE IDs - MANTER) =====
                            'outros_envolvidos': outros_input.value or [],
                            
                            # ===== CASOS VINCULADOS =====
                            'casos_vinculados': casos_input.value or [],
                            
                            # ===== PROCESSOS FILHOS (GARANTIR LISTA) =====
                            'processos_filhos_ids': [],
                            
                            'observacoes': f"Migrado em {datetime.now().strftime('%d/%m/%Y')}",
                        }

                        # TRATAR PARTE CONTRÁRIA (CONVERTER LISTA -> STRING)
                        parte_contraria_ids = contraria_input.value or []
                        if parte_contraria_ids:
                            # Buscar nome da primeira pessoa selecionada
                            info_pessoa = obter_nome_pessoa(parte_contraria_ids[0])
                            dados_processo['parte_contraria'] = info_pessoa['nome']
                            dados_processo['parte_contraria_tipo'] = info_pessoa['tipo']
                        else:
                            dados_processo['parte_contraria'] = 'Não informado'

                        # VALIDAR DADOS ANTES DE SALVAR (Logs para Debug)
                        print("\n" + "="*80)
                        print("VALIDANDO DADOS ANTES DE SALVAR NO WORKSPACE")
                        print("="*80)
                        print(f"Título: {dados_processo.get('titulo')}")
                        print(f"Número: {dados_processo.get('numero')}")
                        print(f"Área: {dados_processo.get('area')}")
                        print(f"Status: {dados_processo.get('status')}")
                        print(f"Tipo: {dados_processo.get('tipo')}")
                        print(f"Parte Contrária: {dados_processo.get('parte_contraria')} ({dados_processo.get('parte_contraria_tipo')})")
                        print(f"Clientes (qtd): {len(dados_processo.get('clientes', []))}")
                        print("="*80)

                        # Validações críticas redundantes
                        if not dados_processo.get('area'):
                            ui.notify('❌ Área do Direito é obrigatória!', type='negative')
                            return
                        
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
                                # Detecta origem do processo atual para buscar próximos da mesma origem
                                origem_atual = processo.get('origem', 'lenon')
                                await asyncio.sleep(0.3)
                                proximos = listar_processos_migracao(status='pendente', origem=origem_atual)
                                
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


def render_migracao_interface():
    """
    Renderiza interface de migração com sub-abas por origem (Lenon/Gilberto).
    Sistema de abas para separar planilhas EPROC de diferentes responsáveis.
    """
    # Carregar cache do sistema (necessário para os selects no modal)
    carregar_cache_sistema()
    
    # Estilos específicos da migração (layout horizontal otimizado)
    ui.add_head_html('''
        <style>
            /* Cards de status e pendentes */
            .card-pendente { border-left: 5px solid #fbbf24; }
            .card-concluido { border-left: 5px solid #10b981; }
            
            /* Estilos da tabela de migração */
            .tabela-migracao tbody tr.tabela-migracao-linha {
                transition: background-color 0.2s;
            }
            .tabela-migracao tbody tr.tabela-migracao-linha:hover {
                background-color: #f3f4f6 !important;
            }
            .tabela-migracao tbody tr.tabela-migracao-linha-pendente {
                border-left: 4px solid #fbbf24 !important;
            }
            .tabela-migracao tbody tr.tabela-migracao-linha-concluida {
                border-left: 4px solid #10b981 !important;
            }
            
            /* Estilos para ícones de cópia */
            .copy-icon {
                transition: opacity 0.2s, color 0.2s;
            }
            .copy-icon:hover {
                opacity: 1 !important;
                color: #4b5563 !important;
            }
            .tabela-migracao tbody tr:hover .copy-icon {
                opacity: 0.8;
            }
            
            /* Estilos para sub-abas de migração */
            .sub-abas-migracao {
                background-color: #f3f4f6;
                border-radius: 8px;
                padding: 4px;
            }
            .sub-abas-migracao .q-tab {
                min-height: 40px;
                padding: 0 16px;
            }
            
            /* Barra de informações horizontal */
            .barra-info-migracao {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px 16px;
            }
            
            /* Tabela full width */
            .tabela-migracao-fullwidth {
                width: 100% !important;
            }
            .tabela-migracao-fullwidth .q-table {
                width: 100% !important;
            }
            
            /* Responsividade da barra de informações */
            @media (max-width: 768px) {
                .barra-info-migracao {
                    flex-direction: column !important;
                    gap: 12px !important;
                }
                .barra-info-item {
                    width: 100% !important;
                }
            }
        </style>
    ''')
    
    # Sistema de Sub-abas por Origem
    with ui.tabs().classes('w-full sub-abas-migracao') as tabs_migracao:
        tab_lenon = ui.tab('EPROC - TJSC - 1ª instância - Lenon')
        tab_gilberto = ui.tab('EPROC - TJSC - 1ª instância - Gilberto')
    
    with ui.tab_panels(tabs_migracao, value=tab_lenon).classes('w-full'):
        # Painel Lenon (conteúdo atual)
        with ui.tab_panel(tab_lenon):
            criar_interface_migracao_lenon()
        
        # Painel Gilberto (novo)
        with ui.tab_panel(tab_gilberto):
            criar_interface_migracao_gilberto()


def criar_interface_migracao_lenon():
    """
    Interface de migração EPROC - TJSC - 1ª instância - Lenon.
    Layout horizontal otimizado: [Barra Info] → [Tabela Full Width]
    """
    # Estado local para filtros e seleção
    estado = {
        'filtro_status': 'todos',
        'processos_selecionados': set()  # IDs dos processos selecionados
    }

    # Handler para importar planilha
    async def handle_import():
        with ui.dialog() as loading, ui.card().classes('items-center p-8'):
            ui.spinner(size='lg', color='primary')
            ui.label('Processando planilha...').classes('mt-4 font-medium')
        loading.open()
        res = importar_planilha_migracao(origem='lenon')
        loading.close()
        if res['sucesso']:
            ui.notify(f"✅ {res['importados']} processos importados!", type='positive')
            area_progresso.refresh()
            lista_processos_migracao.refresh()
        else:
            ui.notify(f"❌ {res['erro']}", type='negative')

    # Container principal vertical
    with ui.column().classes('w-full gap-4'):
        
        # BARRA DE INFORMAÇÕES HORIZONTAL
        with ui.row().classes('w-full items-center justify-between gap-4 barra-info-migracao flex-wrap'):
            
            # Item 1: Botão Importar + Badge de processos
            with ui.row().classes('items-center gap-3 barra-info-item'):
                ui.button('IMPORTAR', icon='upload_file', on_click=handle_import).props('color=primary dense unelevated')
                
                @ui.refreshable
                def badge_total():
                    stats = obter_estatisticas_migracao(origem='lenon')
                    if stats['total'] > 0:
                        with ui.badge(f"{stats['total']} PROCESSOS", color='positive').classes('px-3 py-1'):
                            pass
                    else:
                        with ui.badge('NENHUM PROCESSO', color='grey').classes('px-3 py-1'):
                            pass
                badge_total()
            
            # Item 2: Progresso da migração
            @ui.refreshable
            def area_progresso():
                stats = obter_estatisticas_migracao(origem='lenon')
                with ui.row().classes('items-center gap-3 barra-info-item'):
                    ui.label('PROGRESSO:').classes('text-xs font-bold text-gray-500')
                    ui.label(f"{stats['concluidos']} de {stats['total']}").classes('text-sm font-bold text-[#223631]')
                    with ui.element('div').classes('w-32'):
                        ui.linear_progress(value=stats['progresso']/100).classes('rounded-full').props('color=positive stripe')
                    ui.label(f"{stats['progresso']:.0f}%").classes('text-xs text-gray-500 font-medium')
            area_progresso()
            
            # Item 3: Filtro de status + Botão finalizar
            with ui.row().classes('items-center gap-3 barra-info-item'):
                ui.select(
                    {'todos': 'Todos', 'pendente': 'Pendentes', 'concluido': 'Concluídos'},
                    value='todos',
                    label='Filtrar',
                    on_change=lambda e: (estado.update({'filtro_status': e.value}), lista_processos_migracao.refresh())
                ).classes('w-32').props('outlined dense')
                
                ui.button('FINALIZAR', icon='verified', on_click=lambda: finalizar_fluxo()).props('color=positive outline dense no-caps')

        # TABELA DE PROCESSOS - FULL WIDTH
        with ui.column().classes('w-full tabela-migracao-fullwidth'):
            @ui.refreshable
            def lista_processos_migracao():
                processos = listar_processos_migracao(status=estado.get('filtro_status', 'todos'), origem='lenon')
                if not processos:
                    with ui.column().classes('w-full items-center justify-center py-20 text-gray-400'):
                        ui.icon('inventory_2', size='xl').classes('mb-2')
                        ui.label('Nenhum processo nesta categoria').classes('italic')
                    return

                # Definir colunas da tabela
                COLUNAS_TABELA_MIGRACAO = [
                    {'name': 'selecionado', 'label': '', 'field': 'selecionado', 'align': 'center', 'sortable': False, 'style': 'width: 50px;'},
                    {'name': 'numero', 'label': 'Número do Processo', 'field': 'numero', 'align': 'left', 'sortable': True, 'style': 'width: 250px;'},
                    {'name': 'data_distribuicao', 'label': 'Data de Distribuição', 'field': 'data_distribuicao', 'align': 'left', 'sortable': True, 'style': 'width: 150px;'},
                    {'name': 'partes', 'label': 'Partes', 'field': 'partes', 'align': 'left', 'sortable': False},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 120px;'},
                    {'name': 'acoes', 'label': '', 'field': 'acoes', 'align': 'right', 'sortable': False, 'style': 'width: 150px;'},
                ]

                # Preparar dados da tabela
                rows = []
                processos_dict = {}  # Mapeia _id para processo completo
                
                for p in processos:
                    # Converte timestamps do documento completo para evitar erro de serialização JSON
                    p_convertido = converter_timestamps_documento(p)
                    
                    processo_id = p_convertido.get('_id', '')
                    status = p_convertido.get('status_migracao', 'pendente')
                    num_limpo = limpar_numero_processo(p_convertido.get('numero_processo', ''))
                    
                    # Formatar data de distribuição (usando data_abertura se disponível)
                    # Converte DatetimeWithNanoseconds do Firestore para string formatada
                    # Formato de saída: DD/MM/YYYY (padrão brasileiro, sem hora)
                    data_abertura_raw = p_convertido.get('data_abertura')
                    data_formatada = converter_datetime_firestore(data_abertura_raw, formato_saida='%d/%m/%Y')
                    
                    # Formatar partes (autores e réus)
                    partes_lista = []
                    if p_convertido.get('autores_sugestao'):
                        partes_lista.extend([f"🔵 {a}" for a in p_convertido.get('autores_sugestao', [])[:2]])  # Limita a 2 autores
                    if p_convertido.get('reus_sugestao'):
                        partes_lista.extend([f"🔴 {r}" for r in p_convertido.get('reus_sugestao', [])[:2]])  # Limita a 2 réus
                    partes_str = ', '.join(partes_lista) if partes_lista else 'Não informado'
                    if len(partes_str) > 80:
                        partes_str = partes_str[:77] + '...'
                    
                    # Armazena processo convertido (sem DatetimeWithNanoseconds) no dicionário
                    processos_dict[processo_id] = p_convertido
                    
                    # Determina se está selecionado baseado no status (migrado = selecionado)
                    # Checkbox reflete o status: marcado = migrado, desmarcado = pendente
                    is_migrado = status in ['migrado', 'concluido']  # Compatibilidade com "concluido"
                    
                    # Armazena número original (antes de limpar) para cópia
                    numero_original = p_convertido.get('numero_processo', '')
                    
                    rows.append({
                        '_id': processo_id,
                        'selecionado': is_migrado,  # Checkbox reflete status: marcado = migrado
                        'numero': num_limpo,  # Número limpo para exibição
                        'numero_original': numero_original,  # Número original para cópia
                        'data_distribuicao': data_formatada,  # Data formatada para exibição e cópia
                        'partes': partes_str,
                        'status': 'migrado' if is_migrado else 'pendente',  # Normaliza para "migrado"
                        'status_label': 'Migrado' if is_migrado else 'Pendente',
                        'classe_processo': p_convertido.get('classe_processo', 'Classe não informada'),
                    })

                # Criar tabela com classe CSS customizada para linhas
                table = ui.table(
                    columns=COLUNAS_TABELA_MIGRACAO,
                    rows=rows,
                    row_key='_id'
                ).classes('w-full tabela-migracao').props('flat dense bordered')

                # Slot para checkbox no header (checkbox mestre) - calcula estado dinamicamente
                # Checkbox mestre marca APENAS processos pendentes
                processos_pendentes = [r for r in rows if r['status'] == 'pendente']
                total_pendentes = len(processos_pendentes)
                pendentes_marcados = sum(1 for r in processos_pendentes if r['selecionado'])
                todos_pendentes_selecionados = total_pendentes > 0 and pendentes_marcados == total_pendentes
                alguns_pendentes_selecionados = pendentes_marcados > 0 and pendentes_marcados < total_pendentes
                
                # Slot para checkbox no header (checkbox mestre)
                # Nota: Usa valores booleanos JavaScript para Vue
                checkbox_indeterminate_attr = ':indeterminate="true"' if alguns_pendentes_selecionados else ''
                checkbox_checked_value = 'true' if todos_pendentes_selecionados else 'false'
                
                table.add_slot('header-cell-selecionado', f'''
                    <q-th :props="props" style="text-align: center;">
                        <q-checkbox 
                            :model-value={checkbox_checked_value}
                            {checkbox_indeterminate_attr}
                            @update:model-value="$parent.$emit('toggle-all', $event)"
                            dense
                        />
                    </q-th>
                ''')

                # Slot para checkbox no body
                table.add_slot('body-cell-selecionado', '''
                    <q-td :props="props" style="text-align: center;">
                        <q-checkbox 
                            :model-value="props.row.selecionado"
                            @update:model-value="$parent.$emit('toggle-select', {id: props.row._id, value: $event})"
                            dense
                        />
                    </q-td>
                ''')
                
                # Slot para número do processo com ícone de cópia
                table.add_slot('body-cell-numero', '''
                    <q-td :props="props" style="text-align: left;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="flex: 1;">{{ props.row.numero }}</span>
                            <q-icon 
                                name="content_copy" 
                                size="14px" 
                                class="copy-icon"
                                style="color: #9ca3af; cursor: pointer; opacity: 0.6; transition: opacity 0.2s;"
                                @click.stop="$parent.$emit('copiar-numero', props.row)"
                            />
                        </div>
                    </q-td>
                ''')
                
                # Slot para data de distribuição com ícone de cópia
                table.add_slot('body-cell-data_distribuicao', '''
                    <q-td :props="props" style="text-align: left;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="flex: 1;">{{ props.row.data_distribuicao }}</span>
                            <q-icon 
                                name="content_copy" 
                                size="14px" 
                                class="copy-icon"
                                style="color: #9ca3af; cursor: pointer; opacity: 0.6; transition: opacity 0.2s;"
                                @click.stop="$parent.$emit('copiar-data', props.row)"
                            />
                        </div>
                    </q-td>
                ''')

                # Slot para status (badge colorido)
                table.add_slot('body-cell-status', '''
                    <q-td :props="props" style="text-align: center;">
                        <q-badge 
                            :color="props.row.status === 'migrado' ? 'green' : 'amber'"
                            :label="props.row.status_label"
                            class="q-mt-xs"
                        />
                    </q-td>
                ''')

                # Slot para botão de ações
                def refresh_ui():
                    area_progresso.refresh()
                    lista_processos_migracao.refresh()

                table.add_slot('body-cell-acoes', '''
                    <q-td :props="props" style="text-align: right;">
                        <div style="display: flex; gap: 4px; justify-content: flex-end; align-items: center;">
                            <q-btn 
                                :label="props.row.status === 'migrado' ? 'EDITAR' : 'COMPLETAR'"
                                icon="edit_note"
                                flat
                                dense
                                color="primary"
                                no-caps
                                @click="$parent.$emit('completar', props.row)"
                            />
                            <q-btn 
                                icon="delete"
                                flat
                                dense
                                color="negative"
                                @click="$parent.$emit('excluir', props.row)"
                            >
                                <q-tooltip>Excluir processo da lista</q-tooltip>
                            </q-btn>
                        </div>
                    </q-td>
                ''')

                # Handler para checkbox mestre (selecionar/desselecionar apenas pendentes)
                async def handle_toggle_all(e):
                    checked = e.args
                    processos_pendentes_ids = [row['_id'] for row in rows if row['status'] == 'pendente']
                    
                    if checked:
                        # Marca todos os pendentes como migrados
                        for processo_id in processos_pendentes_ids:
                            sucesso = atualizar_status_migracao(processo_id, 'migrado')
                            if not sucesso:
                                ui.notify(f'❌ Erro ao atualizar processo {processo_id}', type='negative')
                                return
                        ui.notify(f'✅ {len(processos_pendentes_ids)} processos marcados como migrados', type='positive', timeout=2000)
                    else:
                        # Desmarca todos os migrados (volta para pendente)
                        processos_migrados_ids = [row['_id'] for row in rows if row['status'] == 'migrado']
                        for processo_id in processos_migrados_ids:
                            sucesso = atualizar_status_migracao(processo_id, 'pendente')
                            if not sucesso:
                                ui.notify(f'❌ Erro ao atualizar processo {processo_id}', type='negative')
                                return
                        if processos_migrados_ids:
                            ui.notify(f'✅ {len(processos_migrados_ids)} processos voltaram para pendente', type='info', timeout=2000)
                    
                    # Atualiza UI
                    area_progresso.refresh()
                    lista_processos_migracao.refresh()
                
                table.on('toggle-all', handle_toggle_all)

                # Handler para checkbox individual - atualiza status no Firestore
                async def handle_toggle_select(e):
                    data = e.args
                    processo_id = data.get('id')
                    checked = data.get('value', False)
                    
                    # Determina novo status baseado no checkbox
                    novo_status = 'migrado' if checked else 'pendente'
                    
                    # Atualiza no Firestore
                    sucesso = atualizar_status_migracao(processo_id, novo_status)
                    
                    if sucesso:
                        # Atualiza UI imediatamente
                        area_progresso.refresh()
                        lista_processos_migracao.refresh()
                        
                        # Feedback visual discreto
                        status_label = 'Migrado' if checked else 'Pendente'
                        ui.notify(
                            f'✓ Status alterado para: {status_label}',
                            type='positive' if checked else 'info',
                            timeout=1500,
                            position='top-right'
                        )
                    else:
                        # Reverte mudança visual se update falhou
                        ui.notify(
                            f'❌ Erro ao atualizar status do processo',
                            type='negative',
                            timeout=3000
                        )
                        # Força refresh para reverter estado visual
                        lista_processos_migracao.refresh()
                
                table.on('toggle-select', handle_toggle_select)
                
                # Handler para copiar número do processo
                def handle_copiar_numero(e):
                    """
                    Copia número do processo para a área de transferência.
                    
                    CORREÇÃO: Remove sufixo entre parênteses antes de copiar usando função
                    limpar_numero_processo() para manter consistência.
                    Exemplo: "5000817-85.2023.8.24.0015   (CNICR01)" → "5000817-85.2023.8.24.0015"
                    """
                    row_data = e.args
                    numero_original = row_data.get('numero_original', row_data.get('numero', ''))
                    
                    if not numero_original:
                        ui.notify('❌ Número não disponível', type='negative', timeout=2000)
                        return
                    
                    # Remove sufixo entre parênteses usando função existente
                    # Esta função já remove códigos como "(CNICR01)", "(RIN0201)", etc.
                    numero_limpo = limpar_numero_processo(numero_original)
                    
                    if not numero_limpo:
                        ui.notify('❌ Número inválido', type='negative', timeout=2000)
                        return
                    
                    # Escapa caracteres especiais para JavaScript
                    numero_escapado = str(numero_limpo).replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                    
                    # Usa JavaScript para copiar para clipboard e exibe notificação
                    ui.run_javascript(f'''
                        (async function() {{
                            try {{
                                if (navigator.clipboard && navigator.clipboard.writeText) {{
                                    await navigator.clipboard.writeText("{numero_escapado}");
                                }} else {{
                                    // Fallback para navegadores antigos
                                    var textArea = document.createElement("textarea");
                                    textArea.value = "{numero_escapado}";
                                    textArea.style.position = "fixed";
                                    textArea.style.left = "-999999px";
                                    textArea.style.top = "-999999px";
                                    document.body.appendChild(textArea);
                                    textArea.focus();
                                    textArea.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(textArea);
                                }}
                            }} catch (err) {{
                                console.error("Erro ao copiar:", err);
                            }}
                        }})();
                    ''')
                    
                    # Feedback visual imediato
                    ui.notify('📋 Número copiado!', type='positive', timeout=2000, position='top-right')
                
                table.on('copiar-numero', handle_copiar_numero)
                
                # Handler para copiar data de distribuição
                def handle_copiar_data(e):
                    """Copia data de distribuição para a área de transferência"""
                    row_data = e.args
                    data_formatada = row_data.get('data_distribuicao', '')
                    
                    if not data_formatada or data_formatada == '-':
                        ui.notify('❌ Data não disponível', type='negative', timeout=2000)
                        return
                    
                    # Escapa caracteres especiais para JavaScript
                    data_escapada = str(data_formatada).replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                    
                    # Usa JavaScript para copiar para clipboard e exibe notificação
                    ui.run_javascript(f'''
                        (async function() {{
                            try {{
                                if (navigator.clipboard && navigator.clipboard.writeText) {{
                                    await navigator.clipboard.writeText("{data_escapada}");
                                }} else {{
                                    // Fallback para navegadores antigos
                                    var textArea = document.createElement("textarea");
                                    textArea.value = "{data_escapada}";
                                    textArea.style.position = "fixed";
                                    textArea.style.left = "-999999px";
                                    textArea.style.top = "-999999px";
                                    document.body.appendChild(textArea);
                                    textArea.focus();
                                    textArea.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(textArea);
                                }}
                            }} catch (err) {{
                                console.error("Erro ao copiar:", err);
                            }}
                        }})();
                    ''')
                    
                    # Feedback visual imediato
                    ui.notify('📋 Data copiada!', type='positive', timeout=2000, position='top-right')
                
                table.on('copiar-data', handle_copiar_data)

                # Handler para botão completar/editar
                def handle_completar(e):
                    row_data = e.args
                    processo_id = row_data.get('_id')
                    if processo_id and processo_id in processos_dict:
                        processo_completo = processos_dict[processo_id]
                        refresh_ui()
                        abrir_modal_completar(processo_completo, refresh_ui)
                
                table.on('completar', handle_completar)
                
                # Handler para exclusão de processo
                def handle_excluir(e):
                    """Abre modal de confirmação e exclui processo se confirmado"""
                    row_data = e.args
                    processo_id = row_data.get('_id')
                    numero_processo = row_data.get('numero', 'N/A')
                    status_processo = row_data.get('status', 'pendente')
                    
                    if not processo_id:
                        ui.notify('❌ ID do processo não encontrado', type='negative')
                        return
                    
                    # Verifica se processo está em processos_dict para obter dados completos
                    processo_completo = processos_dict.get(processo_id, {})
                    numero_original = processo_completo.get('numero_processo', numero_processo)
                    numero_limpo = limpar_numero_processo(numero_original)
                    
                    # Cria modal de confirmação
                    with ui.dialog() as dialog_excluir, ui.card().classes('w-96 p-4'):
                        ui.label('⚠️ Confirmar Exclusão').classes('text-lg font-bold text-red-600 mb-3')
                        
                        # Mensagem principal
                        ui.label(
                            f'Deseja realmente excluir o processo\n'
                            f'"{numero_limpo}"\n'
                            f'da lista de migração?'
                        ).classes('mb-4 text-center')
                        
                        # Aviso sobre ação permanente
                        with ui.card().classes('bg-red-50 p-3 mb-4 border border-red-200'):
                            ui.label(
                                'Esta ação é PERMANENTE e não pode ser desfeita.\n'
                                'O processo será removido definitivamente do Firestore.'
                            ).classes('text-sm text-red-800')
                        
                        # Aviso adicional se processo já foi migrado
                        if status_processo == 'migrado':
                            with ui.card().classes('bg-amber-50 p-3 mb-4 border border-amber-200'):
                                ui.label(
                                    '⚠️ ATENÇÃO: Este processo já foi MIGRADO.\n'
                                    'Excluir da lista não afeta o processo já cadastrado no sistema.'
                                ).classes('text-sm text-amber-800')
                        
                        # Botões de ação
                        with ui.row().classes('w-full justify-end gap-2'):
                            ui.button(
                                'Cancelar',
                                on_click=dialog_excluir.close
                            ).props('flat color=grey')
                            
                            async def confirmar_exclusao():
                                """Executa exclusão após confirmação"""
                                try:
                                    # Exclui do Firestore
                                    sucesso = excluir_processo_migracao(processo_id)
                                    
                                    if sucesso:
                                        # Fecha modal
                                        dialog_excluir.close()
                                        
                                        # Atualiza interface
                                        refresh_ui()
                                        
                                        # Notificação de sucesso
                                        ui.notify(
                                            f'✅ Processo {numero_limpo} excluído da lista',
                                            type='positive',
                                            timeout=3000,
                                            position='top-right'
                                        )
                                        
                                        logger.info(f"[EXCLUSÃO] Processo {processo_id} ({numero_limpo}) excluído com sucesso")
                                    else:
                                        # Notificação de erro
                                        ui.notify(
                                            '❌ Erro ao excluir processo',
                                            type='negative',
                                            timeout=3000
                                        )
                                        logger.error(f"[EXCLUSÃO] Erro ao excluir processo {processo_id}")
                                        
                                except Exception as ex:
                                    logger.error(f"[EXCLUSÃO] Erro crítico ao excluir: {ex}")
                                    import traceback
                                    traceback.print_exc()
                                    ui.notify(
                                        f'❌ Erro ao excluir: {str(ex)}',
                                        type='negative',
                                        timeout=5000
                                    )
                            
                            ui.button(
                                'Excluir',
                                icon='delete',
                                on_click=confirmar_exclusao
                            ).props('color=negative unelevated')
                    
                    # Abre o modal
                    dialog_excluir.open()
                
                table.on('excluir', handle_excluir)

                # Aplicar estilo de barra lateral laranja/verde nas linhas via JavaScript
                # Busca pelas células de status que contêm badges e aplica classe CSS na linha pai
                def aplicar_estilos_linhas():
                    """Aplica estilos de barra lateral baseado no status do processo"""
                    ui.run_javascript('''
                        setTimeout(function() {
                            var table = document.querySelector('.tabela-migracao .q-table tbody');
                            if (table) {
                                var tableRows = table.querySelectorAll('tr');
                                tableRows.forEach(function(row) {
                                    // Busca pela célula de status (contém badge)
                                    var statusCell = row.querySelector('td:nth-child(5)'); // 5ª coluna é status
                                    if (statusCell) {
                                        var badge = statusCell.querySelector('.q-badge');
                                        if (badge) {
                                            var badgeText = badge.textContent.trim();
                                            var rowStatus = row.querySelector('td:nth-child(5) .q-badge');
                                            
                                            // Verifica se é "Migrado" (verde) ou "Pendente" (amarelo)
                                            if (badgeText === 'Migrado') {
                                                row.classList.add('tabela-migracao-linha-concluida');
                                            } else if (badgeText === 'Pendente') {
                                                row.classList.add('tabela-migracao-linha-pendente');
                                            }
                                            row.classList.add('tabela-migracao-linha');
                                        }
                                    }
                                });
                            }
                        }, 300);
                    ''')
                
                aplicar_estilos_linhas()

            lista_processos_migracao()

    async def finalizar_fluxo():
        res = finalizar_migracao_completa(origem='lenon')
        if res['sucesso']:
            ui.notify(res['mensagem'], type='positive')
            ui.navigate.to('/visao-geral/processos')
        else:
            ui.notify(res['erro'], type='warning')


# =============================================================================
# MODAL DE VALIDAÇÃO E CADASTRO DE PESSOAS (GILBERTO)
# =============================================================================

def abrir_modal_validacao_pessoas():
    """
    Abre modal para validar pessoas não cadastradas nos processos EPROC.
    Permite selecionar e cadastrar em massa pessoas faltantes.
    """
    # Estado do modal
    estado_validacao = {
        'resultado': None,
        'pessoas_selecionadas': set(),
        'filtro_tipo': 'todos',
        'busca': '',
        'processando': False,
    }
    
    with ui.dialog() as modal, ui.card().classes('w-full max-w-5xl max-h-[90vh]'):
        # Cabeçalho
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label('🔍 Validação de Pessoas - EPROC Gilberto').classes('text-xl font-bold text-[#223631]')
            ui.button(icon='close', on_click=modal.close).props('flat round dense')
        
        ui.separator()
        
        # Área de conteúdo
        with ui.column().classes('w-full gap-4 overflow-y-auto') as conteudo_modal:
            
            # Estado inicial: botão para executar validação
            @ui.refreshable
            def area_resultado():
                if estado_validacao['processando']:
                    with ui.column().classes('w-full items-center py-16'):
                        ui.spinner('dots', size='xl', color='primary')
                        ui.label('Analisando pessoas...').classes('mt-4 text-gray-500')
                        ui.label('Comparando com cadastros existentes').classes('text-sm text-gray-400')
                    return
                
                if not estado_validacao['resultado']:
                    # Ainda não executou validação
                    with ui.column().classes('w-full items-center py-12'):
                        ui.icon('person_search', size='64px').classes('text-gray-300 mb-4')
                        ui.label('Clique para analisar pessoas').classes('text-lg text-gray-500')
                        ui.label('Compara autores e réus do EPROC com pessoas cadastradas').classes('text-sm text-gray-400 mb-6')
                        
                        async def executar_validacao():
                            estado_validacao['processando'] = True
                            area_resultado.refresh()
                            
                            # Executa validação (pode demorar)
                            resultado = validar_pessoas_migracao(origem='gilberto')
                            
                            estado_validacao['resultado'] = resultado
                            estado_validacao['processando'] = False
                            area_resultado.refresh()
                        
                        ui.button(
                            'EXECUTAR VALIDAÇÃO',
                            icon='play_arrow',
                            on_click=executar_validacao
                        ).props('color=primary unelevated size=lg')
                    return
                
                resultado = estado_validacao['resultado']
                
                if not resultado.get('sucesso'):
                    with ui.column().classes('w-full items-center py-8'):
                        ui.icon('error', size='48px').classes('text-red-400 mb-4')
                        ui.label('Erro na validação').classes('text-lg text-red-600')
                        ui.label(resultado.get('erro', 'Erro desconhecido')).classes('text-sm text-gray-500')
                    return
                
                # Resumo da validação
                resumo = resultado.get('resumo', {})
                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.card().classes('flex-1 p-4 bg-green-50 border border-green-200'):
                        ui.label(str(resumo.get('cadastradas', 0))).classes('text-2xl font-bold text-green-700')
                        ui.label('Já cadastradas').classes('text-xs text-green-600')
                    
                    with ui.card().classes('flex-1 p-4 bg-amber-50 border border-amber-200'):
                        ui.label(str(resumo.get('nao_cadastradas', 0))).classes('text-2xl font-bold text-amber-700')
                        ui.label('Não cadastradas').classes('text-xs text-amber-600')
                    
                    with ui.card().classes('flex-1 p-4 bg-blue-50 border border-blue-200'):
                        ui.label(str(resumo.get('possiveis_duplicatas', 0))).classes('text-2xl font-bold text-blue-700')
                        ui.label('Possíveis duplicatas').classes('text-xs text-blue-600')
                
                # Lista de pessoas não cadastradas
                nao_cadastradas = preparar_pessoas_para_ui(resultado.get('nao_cadastradas', []))
                duplicatas = preparar_pessoas_para_ui(resultado.get('possiveis_duplicatas', []))
                
                if not nao_cadastradas and not duplicatas:
                    with ui.column().classes('w-full items-center py-8'):
                        ui.icon('check_circle', size='48px').classes('text-green-400 mb-4')
                        ui.label('Todas as pessoas já estão cadastradas!').classes('text-lg text-green-600')
                    return
                
                # Filtros e busca
                with ui.row().classes('w-full items-center gap-4 mb-4'):
                    ui.input(
                        placeholder='Buscar por nome...',
                        on_change=lambda e: (estado_validacao.update({'busca': e.value or ''}), tabela_pessoas.refresh())
                    ).props('outlined dense clearable').classes('flex-grow')
                    
                    ui.select(
                        {'todos': 'Todos os tipos', 'PF': 'Pessoa Física', 'PJ': 'Pessoa Jurídica'},
                        value='todos',
                        label='Tipo',
                        on_change=lambda e: (estado_validacao.update({'filtro_tipo': e.value}), tabela_pessoas.refresh())
                    ).props('outlined dense').classes('w-40')
                    
                    # Contador de selecionadas
                    with ui.badge(f"{len(estado_validacao['pessoas_selecionadas'])} selecionadas", color='primary').classes('px-3 py-1'):
                        pass
                
                # Tabela de pessoas não cadastradas
                @ui.refreshable
                def tabela_pessoas():
                    # Aplicar filtros
                    lista_exibir = nao_cadastradas.copy()
                    
                    # Filtro de busca
                    if estado_validacao['busca']:
                        termo = estado_validacao['busca'].lower()
                        lista_exibir = [p for p in lista_exibir if termo in p['nome'].lower()]
                    
                    # Filtro de tipo
                    if estado_validacao['filtro_tipo'] != 'todos':
                        lista_exibir = [p for p in lista_exibir if p['tipo_pessoa'] == estado_validacao['filtro_tipo']]
                    
                    if not lista_exibir:
                        ui.label('Nenhuma pessoa encontrada com os filtros atuais.').classes('text-gray-400 italic py-4')
                        return
                    
                    # Colunas da tabela
                    colunas = [
                        {'name': 'selecionar', 'label': '', 'field': 'selecionar', 'align': 'center', 'style': 'width: 50px;'},
                        {'name': 'nome', 'label': 'Nome', 'field': 'nome', 'align': 'left', 'sortable': True},
                        {'name': 'cpf_cnpj', 'label': 'CPF/CNPJ', 'field': 'cpf_cnpj', 'align': 'left', 'style': 'width: 150px;'},
                        {'name': 'tipo_label', 'label': 'Tipo', 'field': 'tipo_label', 'align': 'center', 'style': 'width: 120px;'},
                        {'name': 'papeis_label', 'label': 'Papel', 'field': 'papeis_label', 'align': 'center', 'style': 'width: 100px;'},
                        {'name': 'qtd_processos', 'label': 'Processos', 'field': 'qtd_processos', 'align': 'center', 'style': 'width: 80px;'},
                    ]
                    
                    # Prepara rows com índice para seleção
                    rows = []
                    for i, p in enumerate(lista_exibir):
                        rows.append({
                            '_idx': i,
                            'nome': p['nome'],
                            'cpf_cnpj': p['cpf_cnpj'],
                            'tipo_pessoa': p['tipo_pessoa'],
                            'tipo_label': p['tipo_label'],
                            'papeis_label': p['papeis_label'],
                            'qtd_processos': p['qtd_processos'],
                            'selecionado': i in estado_validacao['pessoas_selecionadas'],
                            '_dados': p['_dados_originais'],
                        })
                    
                    # Tabela
                    table = ui.table(
                        columns=colunas,
                        rows=rows,
                        row_key='_idx',
                        pagination={'rowsPerPage': 15}
                    ).classes('w-full').props('flat dense bordered')
                    
                    # Header com checkbox mestre
                    todos_selecionados = len(estado_validacao['pessoas_selecionadas']) == len(lista_exibir) and len(lista_exibir) > 0
                    alguns_selecionados = 0 < len(estado_validacao['pessoas_selecionadas']) < len(lista_exibir)
                    
                    indet_attr = ':indeterminate="true"' if alguns_selecionados else ''
                    checked_val = 'true' if todos_selecionados else 'false'
                    
                    table.add_slot('header-cell-selecionar', f'''
                        <q-th :props="props" style="text-align: center;">
                            <q-checkbox 
                                :model-value={checked_val}
                                {indet_attr}
                                @update:model-value="$parent.$emit('toggle-all', $event)"
                                dense
                            />
                        </q-th>
                    ''')
                    
                    # Body checkbox
                    table.add_slot('body-cell-selecionar', '''
                        <q-td :props="props" style="text-align: center;">
                            <q-checkbox 
                                :model-value="props.row.selecionado"
                                @update:model-value="$parent.$emit('toggle-item', {idx: props.row._idx, value: $event})"
                                dense
                            />
                        </q-td>
                    ''')
                    
                    # Handler toggle all
                    def handle_toggle_all(e):
                        checked = e.args
                        if checked:
                            estado_validacao['pessoas_selecionadas'] = set(range(len(lista_exibir)))
                        else:
                            estado_validacao['pessoas_selecionadas'] = set()
                        tabela_pessoas.refresh()
                    
                    table.on('toggle-all', handle_toggle_all)
                    
                    # Handler toggle item
                    def handle_toggle_item(e):
                        data = e.args
                        idx = data.get('idx')
                        checked = data.get('value', False)
                        
                        if checked:
                            estado_validacao['pessoas_selecionadas'].add(idx)
                        else:
                            estado_validacao['pessoas_selecionadas'].discard(idx)
                        
                        tabela_pessoas.refresh()
                    
                    table.on('toggle-item', handle_toggle_item)
                
                # Renderiza tabela
                with ui.card().classes('w-full'):
                    ui.label('📋 Pessoas Não Cadastradas').classes('text-sm font-bold text-gray-600 mb-2')
                    tabela_pessoas()
                
                # Seção de possíveis duplicatas (se houver)
                if duplicatas:
                    with ui.expansion('⚠️ Possíveis Duplicatas (revisar manualmente)', icon='warning').classes('w-full mt-4'):
                        for dup in duplicatas:
                            with ui.card().classes('w-full p-3 mb-2 bg-amber-50 border border-amber-200'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('gap-0'):
                                        ui.label(dup['nome']).classes('font-medium')
                                        ui.label(f"Similar a: {dup['pessoa_similar_nome']} ({dup['similaridade_pct']})").classes('text-xs text-amber-600')
                                    ui.label(dup['tipo_label']).classes('text-xs text-gray-500')
                
                # Botão de cadastro em massa
                with ui.row().classes('w-full justify-end mt-4 gap-3'):
                    async def cadastrar_selecionadas():
                        if not estado_validacao['pessoas_selecionadas']:
                            ui.notify('Selecione pelo menos uma pessoa', type='warning')
                            return
                        
                        # Prepara lista de pessoas para cadastrar
                        pessoas_para_cadastrar = []
                        for idx in estado_validacao['pessoas_selecionadas']:
                            if idx < len(nao_cadastradas):
                                pessoas_para_cadastrar.append(nao_cadastradas[idx]['_dados_originais'])
                        
                        if not pessoas_para_cadastrar:
                            ui.notify('Nenhuma pessoa selecionada', type='warning')
                            return
                        
                        # Confirma
                        with ui.dialog() as confirm_dialog, ui.card().classes('p-4'):
                            ui.label(f'Confirmar cadastro de {len(pessoas_para_cadastrar)} pessoa(s)?').classes('font-medium mb-4')
                            
                            with ui.row().classes('w-full justify-end gap-2'):
                                ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                                
                                async def confirmar():
                                    confirm_dialog.close()
                                    estado_validacao['processando'] = True
                                    area_resultado.refresh()
                                    
                                    # Executa cadastro em massa
                                    res_cadastro = cadastrar_pessoas_em_massa(pessoas_para_cadastrar)
                                    
                                    estado_validacao['processando'] = False
                                    
                                    if res_cadastro.get('sucesso'):
                                        ui.notify(
                                            f"✅ {res_cadastro['cadastrados']} pessoa(s) cadastrada(s)!",
                                            type='positive',
                                            timeout=5000
                                        )
                                        # Limpa seleção e reexecuta validação
                                        estado_validacao['pessoas_selecionadas'] = set()
                                        estado_validacao['resultado'] = None
                                        area_resultado.refresh()
                                    else:
                                        ui.notify(
                                            f"❌ Erro: {res_cadastro.get('erro', 'Desconhecido')}",
                                            type='negative',
                                            timeout=5000
                                        )
                                        area_resultado.refresh()
                                
                                ui.button('CONFIRMAR CADASTRO', icon='check', on_click=confirmar).props('color=positive unelevated')
                        
                        confirm_dialog.open()
                    
                    qtd_selecionadas = len(estado_validacao['pessoas_selecionadas'])
                    ui.button(
                        f"CADASTRAR {qtd_selecionadas} SELECIONADA(S)" if qtd_selecionadas else "CADASTRAR SELECIONADAS",
                        icon='person_add',
                        on_click=cadastrar_selecionadas
                    ).props(f"color=positive unelevated {'disable' if not qtd_selecionadas else ''}")
            
            # Renderiza área de resultado
            area_resultado()
    
    # Abre o modal
    modal.open()


def criar_interface_migracao_gilberto():
    """
    Interface de migração EPROC - TJSC - 1ª instância - Gilberto.
    Layout horizontal otimizado: [Barra Info] → [Tabela Full Width]
    62 processos pré-carregados automaticamente.
    """
    # Estado local para filtros e seleção
    estado_gilberto = {
        'filtro_status': 'todos',
        'processos_selecionados': set(),
        'dados_carregados': False
    }

    # Popula automaticamente os processos do Gilberto no Firestore
    # (verifica se já existem antes de inserir)
    res_populate = popular_processos_gilberto()
    if res_populate['sucesso'] and res_populate.get('inseridos', 0) > 0:
        logger.info(f"[GILBERTO] {res_populate['inseridos']} processos inseridos automaticamente")
    estado_gilberto['dados_carregados'] = True

    # Container principal vertical
    with ui.column().classes('w-full gap-4'):
        
        # BARRA DE INFORMAÇÕES HORIZONTAL
        with ui.row().classes('w-full items-center justify-between gap-4 barra-info-migracao flex-wrap'):
            
            # Item 1: Badge de processos carregados
            with ui.row().classes('items-center gap-3 barra-info-item'):
                @ui.refreshable
                def badge_total_gilberto():
                    stats = obter_estatisticas_migracao(origem='gilberto')
                    with ui.badge(f"{stats['total']} PROCESSOS CARREGADOS", color='positive').classes('px-3 py-1'):
                        ui.icon('check_circle', size='14px').classes('mr-1')
                badge_total_gilberto()
                ui.label('Dados pré-carregados').classes('text-xs text-gray-500')
            
            # Item 2: Progresso da migração
            @ui.refreshable
            def area_progresso_gilberto():
                stats = obter_estatisticas_migracao(origem='gilberto')
                with ui.row().classes('items-center gap-3 barra-info-item'):
                    ui.label('PROGRESSO:').classes('text-xs font-bold text-gray-500')
                    ui.label(f"{stats['concluidos']} de {stats['total']}").classes('text-sm font-bold text-[#223631]')
                    with ui.element('div').classes('w-32'):
                        ui.linear_progress(value=stats['progresso']/100).classes('rounded-full').props('color=positive stripe')
                    ui.label(f"{stats['progresso']:.0f}%").classes('text-xs text-gray-500 font-medium')
            area_progresso_gilberto()
            
            # Item 3: Filtro de status + Botões de ação
            with ui.row().classes('items-center gap-3 barra-info-item'):
                ui.select(
                    {'todos': 'Todos', 'pendente': 'Pendentes', 'concluido': 'Concluídos'},
                    value='todos',
                    label='Filtrar',
                    on_change=lambda e: (estado_gilberto.update({'filtro_status': e.value}), lista_processos_migracao_gilberto.refresh())
                ).classes('w-32').props('outlined dense')
                
                # Botão de validação de pessoas não cadastradas
                ui.button(
                    'VALIDAR PESSOAS', 
                    icon='person_search', 
                    on_click=lambda: abrir_modal_validacao_pessoas()
                ).props('color=primary outline dense no-caps')
                
                ui.button('FINALIZAR', icon='verified', on_click=lambda: finalizar_fluxo_gilberto()).props('color=positive outline dense no-caps')

        # TABELA DE PROCESSOS - FULL WIDTH
        with ui.column().classes('w-full tabela-migracao-fullwidth'):
            @ui.refreshable
            def lista_processos_migracao_gilberto():
                processos = listar_processos_migracao(status=estado_gilberto.get('filtro_status', 'todos'), origem='gilberto')
                
                if not processos:
                    # Placeholder quando não há processos (todos foram excluídos/migrados)
                    with ui.column().classes('w-full items-center justify-center py-20'):
                        ui.icon('check_circle', size='64px').classes('text-green-300 mb-4')
                        ui.label('Nenhum processo pendente').classes('text-xl text-gray-500 font-medium')
                        ui.label('Todos os processos foram migrados ou excluídos.').classes('text-gray-400 text-sm')
                        
                        # Informação sobre recarregar dados
                        with ui.card().classes('mt-6 p-4 bg-green-50 border border-green-200'):
                            ui.label('✅ Migração concluída!').classes('text-sm font-bold text-green-800')
                            ui.label('Os 62 processos do Gilberto foram processados.').classes('text-xs text-green-600')
                    return

                # Definir colunas da tabela
                COLUNAS_TABELA_MIGRACAO = [
                    {'name': 'selecionado', 'label': '', 'field': 'selecionado', 'align': 'center', 'sortable': False, 'style': 'width: 50px;'},
                    {'name': 'numero', 'label': 'Número do Processo', 'field': 'numero', 'align': 'left', 'sortable': True, 'style': 'width: 250px;'},
                    {'name': 'data_distribuicao', 'label': 'Data de Distribuição', 'field': 'data_distribuicao', 'align': 'left', 'sortable': True, 'style': 'width: 150px;'},
                    {'name': 'partes', 'label': 'Partes', 'field': 'partes', 'align': 'left', 'sortable': False},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 120px;'},
                    {'name': 'acoes', 'label': '', 'field': 'acoes', 'align': 'right', 'sortable': False, 'style': 'width: 150px;'},
                ]

                # Preparar dados da tabela
                rows = []
                processos_dict = {}
                
                for p in processos:
                    p_convertido = converter_timestamps_documento(p)
                    
                    processo_id = p_convertido.get('_id', '')
                    status = p_convertido.get('status_migracao', 'pendente')
                    num_limpo = limpar_numero_processo(p_convertido.get('numero_processo', ''))
                    
                    data_abertura_raw = p_convertido.get('data_abertura')
                    data_formatada = converter_datetime_firestore(data_abertura_raw, formato_saida='%d/%m/%Y')
                    
                    partes_lista = []
                    if p_convertido.get('autores_sugestao'):
                        partes_lista.extend([f"🔵 {a}" for a in p_convertido.get('autores_sugestao', [])[:2]])
                    if p_convertido.get('reus_sugestao'):
                        partes_lista.extend([f"🔴 {r}" for r in p_convertido.get('reus_sugestao', [])[:2]])
                    partes_str = ', '.join(partes_lista) if partes_lista else 'Não informado'
                    if len(partes_str) > 80:
                        partes_str = partes_str[:77] + '...'
                    
                    processos_dict[processo_id] = p_convertido
                    
                    is_migrado = status in ['migrado', 'concluido']
                    numero_original = p_convertido.get('numero_processo', '')
                    
                    rows.append({
                        '_id': processo_id,
                        'selecionado': is_migrado,
                        'numero': num_limpo,
                        'numero_original': numero_original,
                        'data_distribuicao': data_formatada,
                        'partes': partes_str,
                        'status': 'migrado' if is_migrado else 'pendente',
                        'status_label': 'Migrado' if is_migrado else 'Pendente',
                        'classe_processo': p_convertido.get('classe_processo', 'Classe não informada'),
                    })

                # Criar tabela
                table = ui.table(
                    columns=COLUNAS_TABELA_MIGRACAO,
                    rows=rows,
                    row_key='_id'
                ).classes('w-full tabela-migracao').props('flat dense bordered')

                # Slots da tabela (reutilizar lógica do Lenon)
                table.add_slot('body-cell-selecionado', '''
                    <q-td :props="props" style="text-align: center;">
                        <q-checkbox 
                            :model-value="props.row.selecionado"
                            @update:model-value="$parent.$emit('toggle-select', {id: props.row._id, value: $event})"
                            dense
                        />
                    </q-td>
                ''')
                
                table.add_slot('body-cell-numero', '''
                    <q-td :props="props" style="text-align: left;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="flex: 1;">{{ props.row.numero }}</span>
                            <q-icon 
                                name="content_copy" 
                                size="14px" 
                                class="copy-icon"
                                style="color: #9ca3af; cursor: pointer; opacity: 0.6;"
                                @click.stop="$parent.$emit('copiar-numero', props.row)"
                            />
                        </div>
                    </q-td>
                ''')
                
                table.add_slot('body-cell-status', '''
                    <q-td :props="props" style="text-align: center;">
                        <q-badge 
                            :color="props.row.status === 'migrado' ? 'green' : 'amber'"
                            :label="props.row.status_label"
                            class="q-mt-xs"
                        />
                    </q-td>
                ''')

                table.add_slot('body-cell-acoes', '''
                    <q-td :props="props" style="text-align: right;">
                        <div style="display: flex; gap: 4px; justify-content: flex-end; align-items: center;">
                            <q-btn 
                                :label="props.row.status === 'migrado' ? 'EDITAR' : 'COMPLETAR'"
                                icon="edit_note"
                                flat
                                dense
                                color="primary"
                                no-caps
                                @click="$parent.$emit('completar', props.row)"
                            />
                            <q-btn 
                                icon="delete"
                                flat
                                dense
                                color="negative"
                                @click="$parent.$emit('excluir', props.row)"
                            >
                                <q-tooltip>Excluir processo da lista</q-tooltip>
                            </q-btn>
                        </div>
                    </q-td>
                ''')

                def refresh_ui_gilberto():
                    area_progresso_gilberto.refresh()
                    lista_processos_migracao_gilberto.refresh()

                # Handler para checkbox individual
                async def handle_toggle_select_gilberto(e):
                    data = e.args
                    processo_id = data.get('id')
                    checked = data.get('value', False)
                    novo_status = 'migrado' if checked else 'pendente'
                    sucesso = atualizar_status_migracao(processo_id, novo_status)
                    
                    if sucesso:
                        refresh_ui_gilberto()
                        status_label = 'Migrado' if checked else 'Pendente'
                        ui.notify(f'✓ Status alterado para: {status_label}', type='positive' if checked else 'info', timeout=1500, position='top-right')
                    else:
                        ui.notify('❌ Erro ao atualizar status', type='negative', timeout=3000)
                        lista_processos_migracao_gilberto.refresh()
                
                table.on('toggle-select', handle_toggle_select_gilberto)
                
                # Handler para copiar número
                def handle_copiar_numero_gilberto(e):
                    row_data = e.args
                    numero_original = row_data.get('numero_original', row_data.get('numero', ''))
                    if not numero_original:
                        ui.notify('❌ Número não disponível', type='negative', timeout=2000)
                        return
                    
                    numero_limpo = limpar_numero_processo(numero_original)
                    numero_escapado = str(numero_limpo).replace("'", "\\'").replace('"', '\\"')
                    
                    ui.run_javascript(f'''
                        navigator.clipboard.writeText("{numero_escapado}").catch(console.error);
                    ''')
                    ui.notify('📋 Número copiado!', type='positive', timeout=2000, position='top-right')
                
                table.on('copiar-numero', handle_copiar_numero_gilberto)

                # Handler para completar/editar
                def handle_completar_gilberto(e):
                    row_data = e.args
                    processo_id = row_data.get('_id')
                    if processo_id and processo_id in processos_dict:
                        processo_completo = processos_dict[processo_id]
                        abrir_modal_completar(processo_completo, refresh_ui_gilberto)
                
                table.on('completar', handle_completar_gilberto)
                
                # Handler para exclusão
                def handle_excluir_gilberto(e):
                    row_data = e.args
                    processo_id = row_data.get('_id')
                    numero_processo = row_data.get('numero', 'N/A')
                    
                    with ui.dialog() as dialog_excluir, ui.card().classes('w-96 p-4'):
                        ui.label('⚠️ Confirmar Exclusão').classes('text-lg font-bold text-red-600 mb-3')
                        ui.label(f'Deseja excluir "{numero_processo}" da lista?').classes('mb-4')
                        
                        with ui.row().classes('w-full justify-end gap-2'):
                            ui.button('Cancelar', on_click=dialog_excluir.close).props('flat color=grey')
                            
                            async def confirmar():
                                sucesso = excluir_processo_migracao(processo_id)
                                if sucesso:
                                    dialog_excluir.close()
                                    refresh_ui_gilberto()
                                    ui.notify(f'✅ Processo excluído', type='positive', timeout=3000)
                                else:
                                    ui.notify('❌ Erro ao excluir', type='negative')
                            
                            ui.button('Excluir', icon='delete', on_click=confirmar).props('color=negative')
                    
                    dialog_excluir.open()
                
                table.on('excluir', handle_excluir_gilberto)

            lista_processos_migracao_gilberto()

    async def finalizar_fluxo_gilberto():
        res = finalizar_migracao_completa(origem='gilberto')
        if res['sucesso']:
            ui.notify(res['mensagem'], type='positive')
            ui.navigate.to('/visao-geral/processos')
        else:
            ui.notify(res['erro'], type='warning')


@ui.page('/admin/migracao-processos')
def admin_migracao_processos():
    """Página principal de migração administrativa."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    with layout('Migração de Processos', breadcrumbs=[('Admin', None), ('Migração EPROC', None)]):
        render_migracao_interface()
