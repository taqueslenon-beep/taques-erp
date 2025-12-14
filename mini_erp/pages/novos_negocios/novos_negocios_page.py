"""
Página principal do módulo Novos Negócios.
Sistema CRM com visualização Kanban para gestão de oportunidades de negócio.
"""
from datetime import datetime
from nicegui import ui
from mini_erp.core import layout
from mini_erp.auth import is_authenticated
from mini_erp.gerenciadores.gerenciador_workspace import definir_workspace
from .novos_negocios_kanban_ui import render_kanban_novos_negocios


@ui.page('/visao-geral/novos-negocios')
def novos_negocios():
    """Página principal de Novos Negócios do workspace Visão geral do escritório."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    # Define o workspace
    definir_workspace('visao_geral_escritorio')

    _renderizar_pagina_novos_negocios()


def _renderizar_pagina_novos_negocios():
    """Renderiza o conteúdo da página de Novos Negócios."""
    with layout('Novos Negócios', breadcrumbs=[('Visão geral do escritório', '/visao-geral/painel'), ('Novos Negócios', None)]):
        # Container principal
        with ui.column().classes('w-full gap-4'):
            # Header (título removido - já vem do layout())
            with ui.row().classes('w-full justify-between items-center mb-4'):
                with ui.column().classes('gap-0'):
                    ui.label('Funil de vendas e oportunidades').classes('text-sm text-gray-500 -mt-2 mb-2')
                
                # Botão Nova Oportunidade será conectado após dialog ser criado
                btn_nova_oportunidade = ui.button('+ Nova Oportunidade', icon='add').props('color=primary')
            
            # Estado para controlar qual oportunidade está sendo editada/excluída
            estado_edicao = {'oportunidade_id': None}
            estado_exclusao = {'oportunidade': None}
            estado_resultado = {'oportunidade_id': None}
            
            # Kanban (refreshable)
            # IMPORTANTE: Todo conteúdo que deve ser atualizado deve estar DENTRO desta função
            @ui.refreshable
            def kanban_area():
                def abrir_edicao(oid: str):
                    """Abre dialog de edição com o ID da oportunidade."""
                    print(f"[DEBUG] abrir_edicao - ID: {oid}")
                    
                    # 1. Busca os dados PRIMEIRO
                    oportunidade = buscar_oportunidade_por_id(oid)
                    print(f"[DEBUG] Dados encontrados: {oportunidade is not None}")
                    
                    if not oportunidade:
                        ui.notify('Oportunidade não encontrada', type='negative')
                        return
                    
                    if oportunidade:
                        print(f"[DEBUG] Nome: {oportunidade.get('nome')}")
                        print(f"[DEBUG] Origem: {oportunidade.get('origem')}")
                    
                    # 2. Atualiza estado
                    estado_edicao['oportunidade_id'] = oid
                    
                    # 3. Atualiza opções dos dropdowns
                    atualizar_opcoes_leads(oportunidade.get('lead_id'))
                    atualizar_opcoes_responsaveis()
                    
                    # 4. Preenche campos ANTES de abrir o dialog
                    carregar_dados_edicao(oid)
                    
                    # 5. Abre o dialog (campos já preenchidos)
                    dialog_editar_oportunidade.open()
                
                # Container principal - tudo dentro dele será substituído no refresh
                with ui.element('div').classes('w-full'):
                    render_kanban_novos_negocios(
                        on_refresh=kanban_area.refresh,
                        on_edit_oportunidade=abrir_edicao,
                        on_delete_oportunidade=lambda op: [estado_exclusao.update({'oportunidade': op}), dialog_confirmar_exclusao.open()],
                        on_resultado_oportunidade=lambda oid: [estado_resultado.update({'oportunidade_id': oid}), dialog_resultado.open()]
                    )
            
            kanban_area()
            
            # ====================================================================
            # DIALOGS - Criados uma vez e reutilizados
            # ====================================================================
            
            # Dialog Nova/Editar Oportunidade
            with ui.dialog() as dialog_editar_oportunidade, ui.card().classes('w-full max-w-lg p-6'):
                titulo_dialog_label = ui.label('Nova Oportunidade').classes('text-xl font-bold mb-4 text-gray-800')
                
                # Campos do formulário (criados uma vez)
                from mini_erp.core import get_leads_list
                from .novos_negocios_services import buscar_oportunidade_por_id, save_oportunidade
                from .novos_negocios_dialogs import ORIGEM_OPTIONS, formatar_valor_input, formatar_valor_exibicao
                from mini_erp.models.prioridade import CODIGOS_PRIORIDADE, PRIORIDADE_PADRAO
                from mini_erp.pages.visao_geral.casos.models import NUCLEO_OPTIONS, obter_cor_nucleo
                
                # Inicializa select de leads com opção de criar novo
                leads_inicial = get_leads_list()
                leads_options_inicial = {
                    '__novo__': '+ Criar Novo Lead',
                    '': 'Sem lead vinculado'
                }
                # Adiciona separador visual
                if leads_inicial:
                    leads_options_inicial['__separador__'] = '────────────────'
                for lead in leads_inicial:
                    lead_id = lead.get('_id', '')
                    nome = lead.get('nome', 'Sem nome')
                    nome_exibicao = lead.get('nome_exibicao', '')
                    # Exibe nome_exibicao apenas se for diferente do nome
                    if nome_exibicao and nome_exibicao.strip() and nome_exibicao.strip().upper() != nome.strip().upper():
                        display = f"{nome} ({nome_exibicao})"
                    else:
                        display = nome
                    leads_options_inicial[lead_id] = display
                
                lead_select = ui.select(
                    options=leads_options_inicial,
                    label='Lead'
                ).classes('w-full').props('outlined dense')
                
                # Função para atualizar opções de leads
                def atualizar_opcoes_leads(lead_id_selecionado=None):
                    """Atualiza opções de leads no select."""
                    leads = get_leads_list()
                    leads_options = {
                        '__novo__': '+ Criar Novo Lead',
                        '': 'Sem lead vinculado'
                    }
                    # Adiciona separador visual
                    if leads:
                        leads_options['__separador__'] = '────────────────'
                    for lead in leads:
                        lead_id = lead.get('_id', '')
                        nome = lead.get('nome', 'Sem nome')
                        nome_exibicao = lead.get('nome_exibicao', '')
                        # Exibe nome_exibicao apenas se for diferente do nome
                        if nome_exibicao and nome_exibicao.strip() and nome_exibicao.strip().upper() != nome.strip().upper():
                            display = f"{nome} ({nome_exibicao})"
                        else:
                            display = nome
                        leads_options[lead_id] = display
                    lead_select.options = leads_options
                    lead_select.update()
                    # Seleciona o lead recém-criado se fornecido
                    if lead_id_selecionado:
                        lead_select.value = lead_id_selecionado
                        lead_select.update()
                    return leads
                
                nome_input = ui.input(
                    label='Nome da Oportunidade *',
                    placeholder='Digite o nome da oportunidade'
                ).classes('w-full').props('outlined dense')
                
                # Campo Valor Estimado com máscara de moeda
                valor_input = ui.input(
                    label='Valor Estimado',
                    placeholder='R$ 0,00'
                ).classes('w-full').props('outlined dense')
                
                # JavaScript para formatação automática de moeda em tempo real
                def configurar_mascara_moeda():
                    """Configura máscara de moeda no campo valor com formatação em tempo real."""
                    element_id = valor_input.id
                    ui.run_javascript(f'''
                        setTimeout(function() {{
                            const element = document.querySelector('[data-nicegui-element-id="{element_id}"]');
                            if (!element) return;
                            const input = element.querySelector('input');
                            if (!input) return;
                            
                            // Formata valor para moeda brasileira
                            function formatarMoeda(valor) {{
                                // Remove tudo que não é número
                                let numeros = valor.replace(/\\D/g, '');
                                if (!numeros || numeros === '0') return '';
                                
                                // Converte string para número (mantém como reais, não divide por 100)
                                let valorNumero = parseFloat(numeros);
                                
                                // Formata como R$ X.XXX,XX
                                return 'R$ ' + valorNumero.toLocaleString('pt-BR', {{
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                }});
                            }}
                            
                            // Aplica formatação ao digitar (em tempo real)
                            input.addEventListener('input', function(e) {{
                                let valor_atual = e.target.value;
                                
                                // Remove formatação atual para obter apenas números
                                let numeros = valor_atual.replace(/\\D/g, '');
                                
                                if (numeros) {{
                                    // Formata imediatamente
                                    let valorFormatado = formatarMoeda(numeros);
                                    e.target.value = valorFormatado;
                                    // Posiciona cursor no final
                                    setTimeout(function() {{
                                        e.target.setSelectionRange(valorFormatado.length, valorFormatado.length);
                                    }}, 0);
                                }} else {{
                                    e.target.value = '';
                                }}
                            }}, true); // Use capture phase para pegar antes de outros handlers
                            
                            // Mantém formatação ao perder foco
                            input.addEventListener('blur', function(e) {{
                                let numeros = e.target.value.replace(/\\D/g, '');
                                if (numeros && numeros !== '0') {{
                                    e.target.value = formatarMoeda(numeros);
                                }} else {{
                                    e.target.value = '';
                                }}
                            }});
                        }}, 100);
                    ''')
                
                # Configura máscara após dialog ser criado
                configurar_mascara_moeda()
                
                # Campo Entrada do Lead (Mês/Ano)
                # Obtém mês e ano atual para pré-seleção
                data_atual = datetime.now()
                mes_atual = f"{data_atual.month:02d}"  # Formato: "01", "02", etc.
                ano_atual = str(data_atual.year)
                
                # Opções de mês
                meses_opcoes = {
                    '01': 'Janeiro',
                    '02': 'Fevereiro',
                    '03': 'Março',
                    '04': 'Abril',
                    '05': 'Maio',
                    '06': 'Junho',
                    '07': 'Julho',
                    '08': 'Agosto',
                    '09': 'Setembro',
                    '10': 'Outubro',
                    '11': 'Novembro',
                    '12': 'Dezembro',
                }
                
                # Opções de ano (ano atual - 2 até ano atual + 3)
                ano_inicial = data_atual.year - 2
                ano_final = data_atual.year + 3
                anos_opcoes = {str(ano): str(ano) for ano in range(ano_inicial, ano_final + 1)}
                
                ui.label('Entrada do Lead').classes('text-sm font-medium text-gray-700')
                with ui.row().classes('w-full gap-2'):
                    mes_select = ui.select(
                        options=meses_opcoes,
                        label='Mês',
                        value=mes_atual
                    ).classes('flex-1').props('dense outlined')
                    
                    ano_select = ui.select(
                        options=anos_opcoes,
                        label='Ano',
                        value=ano_atual
                    ).classes('flex-1').props('dense outlined')
                
                # Campo Núcleo (obrigatório, padrão: Generalista)
                nucleo_select = ui.select(
                    options=NUCLEO_OPTIONS,  # ['Ambiental', 'Cobranças', 'Generalista']
                    value='Generalista',  # Default: Generalista
                    label='Núcleo *'
                ).classes('w-full').props('outlined dense')
                
                origem_select = ui.select(
                    options=ORIGEM_OPTIONS,
                    label='Origem'
                ).classes('w-full').props('outlined dense')
                
                # Campo Prioridade
                prioridade_select = ui.select(
                    options=CODIGOS_PRIORIDADE,  # ['P1', 'P2', 'P3', 'P4']
                    value=PRIORIDADE_PADRAO,  # Default: P4
                    label='Prioridade'
                ).classes('w-full').props('outlined dense')
                
                # Campo Responsável como dropdown múltiplo - busca usuários reais do Firebase
                from .novos_negocios_services import get_usuarios_ativos_firebase
                
                def atualizar_opcoes_responsaveis():
                    """Atualiza opções de responsáveis com usuários do Firebase."""
                    usuarios = get_usuarios_ativos_firebase()
                    responsaveis_options = {}
                    for usuario in usuarios:
                        # Usa o nome como chave e valor (ex: "Lenon Taques" -> "Lenon Taques")
                        nome = usuario.get('nome', 'Sem nome')
                        responsaveis_options[nome] = nome
                    responsavel_select.options = responsaveis_options
                    responsavel_select.update()
                    return usuarios
                
                # Inicializa opções vazias (será atualizado ao abrir o dialog)
                responsavel_select = ui.select(
                    options={},
                    label='Responsável',
                    multiple=True,
                    value=[]
                ).classes('w-full').props('outlined dense use-chips clearable')
                
                # Atualiza opções na primeira vez
                atualizar_opcoes_responsaveis()
                
                # Campo Link do Slack
                link_slack_input = ui.input(
                    label='Link do Slack',
                    placeholder='https://slack.com/...'
                ).classes('w-full').props('outlined dense')
                
                observacoes_input = ui.textarea(
                    label='Observações',
                    placeholder='Observações sobre a oportunidade'
                ).classes('w-full').props('outlined dense rows=3')
                
                # Dialog de criar novo lead (será criado quando necessário)
                dialog_novo_lead_ref = {'dialog': None}
                
                # Função para criar novo lead
                def abrir_dialog_novo_lead():
                    """Abre dialog para criar novo lead."""
                    from mini_erp.pages.visao_geral.pessoas.main import abrir_dialog_lead
                    
                    def ao_salvar_lead():
                        """Callback chamado após salvar lead."""
                        # Atualiza lista de leads e seleciona o novo
                        leads_atualizados = get_leads_list()
                        if leads_atualizados:
                            # Pega o último lead criado (assumindo que é o mais recente)
                            novo_lead = leads_atualizados[-1]
                            novo_lead_id = novo_lead.get('_id')
                            # Atualiza opções e seleciona
                            atualizar_opcoes_leads(novo_lead_id)
                            # Preenche campos automaticamente
                            if not nome_input.value:
                                nome_input.value = novo_lead.get('nome', '')
                            origem_lead = novo_lead.get('origem', '')
                            if origem_lead and origem_lead in ORIGEM_OPTIONS:
                                origem_select.value = origem_lead
                                origem_select.update()
                    
                    abrir_dialog_lead(on_save=ao_salvar_lead)
                
                # Função para preencher automaticamente quando selecionar lead
                def on_lead_selected():
                    lead_id = lead_select.value
                    if lead_id == '__novo__':
                        # Abre dialog para criar novo lead
                        abrir_dialog_novo_lead()
                        # Reseta seleção
                        lead_select.value = ''
                        lead_select.update()
                    elif lead_id and lead_id not in ['', '__separador__']:
                        leads_atual = get_leads_list()
                        lead_selecionado = next((l for l in leads_atual if l.get('_id') == lead_id), None)
                        if lead_selecionado:
                            if not nome_input.value:
                                nome_input.value = lead_selecionado.get('nome', '')
                            origem_lead = lead_selecionado.get('origem', '')
                            if origem_lead and origem_lead in ORIGEM_OPTIONS:
                                origem_select.value = origem_lead
                                origem_select.update()
                
                lead_select.on('update:model-value', lambda: on_lead_selected())
                
                # Função para carregar dados na edição
                def carregar_dados_edicao(oportunidade_id: str):
                    """Carrega dados da oportunidade para edição."""
                    if not oportunidade_id:
                        return
                    
                    oportunidade = buscar_oportunidade_por_id(oportunidade_id)
                    if not oportunidade:
                        ui.notify('Oportunidade não encontrada', type='negative')
                        return
                    
                    # Atualiza título do dialog
                    titulo_dialog_label.text = 'Editar Oportunidade'
                    
                    # Nome da Oportunidade
                    nome_input.value = oportunidade.get('nome', '') or ''
                    
                    # Lead - busca lead_id
                    lead_id = oportunidade.get('lead_id')
                    if lead_id:
                        lead_select.value = lead_id
                    else:
                        lead_select.value = ''
                    lead_select.update()
                    
                    # Valor Estimado (formata com R$)
                    valor = oportunidade.get('valor_estimado')
                    if valor and valor != 0:
                        # Formata como R$ X.XXX,XX (formato brasileiro)
                        valor_formatado = f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                        valor_input.value = valor_formatado
                    else:
                        valor_input.value = ''
                    
                    # Entrada do Lead (formato "MM/AAAA")
                    entrada_lead = oportunidade.get('entrada_lead', '')
                    if entrada_lead and '/' in entrada_lead:
                        try:
                            mes_valor, ano_valor = entrada_lead.split('/')
                            mes_select.value = mes_valor
                            ano_select.value = ano_valor
                            mes_select.update()
                            ano_select.update()
                        except Exception as e:
                            # Se formato inválido, mantém valores padrão (mês/ano atual)
                            print(f"Erro ao parsear entrada_lead: {e}")
                            pass
                    else:
                        # Se não tem entrada_lead, mantém valores atuais (já estão pré-selecionados)
                        pass
                    
                    # Núcleo
                    nucleo_val = oportunidade.get('nucleo', 'Generalista')
                    nucleo_select.value = nucleo_val if nucleo_val in NUCLEO_OPTIONS else 'Generalista'
                    nucleo_select.update()
                    
                    # Origem
                    origem_val = oportunidade.get('origem', '')
                    origem_select.value = origem_val if origem_val else ''
                    origem_select.update()
                    
                    # Prioridade
                    prioridade_val = oportunidade.get('prioridade', PRIORIDADE_PADRAO)
                    prioridade_select.value = prioridade_val if prioridade_val else PRIORIDADE_PADRAO
                    prioridade_select.update()
                    
                    # Responsável - tenta ambos os nomes (responsavel e responsaveis) para compatibilidade
                    responsavel_val = oportunidade.get('responsavel') or oportunidade.get('responsaveis') or []
                    if isinstance(responsavel_val, str) and responsavel_val.strip():
                        # Se for string antiga, converte para array
                        responsavel_select.value = [responsavel_val.strip()]
                    elif isinstance(responsavel_val, list):
                        # Garante que é lista de strings não vazias
                        responsavel_select.value = [r for r in responsavel_val if r and str(r).strip()]
                    else:
                        responsavel_select.value = []
                    responsavel_select.update()
                    
                    # Link do Slack
                    link_slack_val = oportunidade.get('link_slack', '')
                    link_slack_input.value = link_slack_val if link_slack_val else ''
                    
                    # Observações
                    observacoes_val = oportunidade.get('observacoes', '')
                    observacoes_input.value = observacoes_val if observacoes_val else ''
                
                # Função para limpar campos (nova oportunidade)
                def limpar_campos():
                    """Limpa todos os campos do formulário para nova oportunidade."""
                    titulo_dialog_label.text = 'Nova Oportunidade'
                    nome_input.value = ''
                    valor_input.value = ''
                    lead_select.value = ''
                    lead_select.update()
                    # Reseta Entrada do Lead para valores atuais
                    mes_select.value = mes_atual
                    ano_select.value = ano_atual
                    mes_select.update()
                    ano_select.update()
                    nucleo_select.value = 'Generalista'
                    nucleo_select.update()
                    origem_select.value = ''
                    origem_select.update()
                    prioridade_select.value = PRIORIDADE_PADRAO
                    prioridade_select.update()
                    responsavel_select.value = []
                    responsavel_select.update()
                    link_slack_input.value = ''
                    observacoes_input.value = ''
                    # Limpa o estado para indicar nova oportunidade
                    estado_edicao['oportunidade_id'] = None
                
                # Função de salvar
                def salvar_oportunidade():
                    # Validação
                    if not nome_input.value or not nome_input.value.strip():
                        ui.notify('Nome da oportunidade é obrigatório!', type='warning')
                        return
                    
                    # Processa valor monetário (remove formatação R$)
                    valor_str = valor_input.value or ''
                    valor_float = formatar_valor_input(valor_str)
                    
                    # Valida lead_id (não pode ser __novo__ ou __separador__)
                    lead_id = lead_select.value
                    if lead_id in ['__novo__', '__separador__']:
                        lead_id = None
                    
                    # Busca nome do lead para salvar junto com a oportunidade (cache)
                    lead_nome = ''
                    if lead_id:
                        try:
                            leads_atual = get_leads_list()
                            lead_encontrado = next((l for l in leads_atual if l.get('_id') == lead_id), None)
                            if lead_encontrado:
                                # Usa nome_exibicao se existir, senão usa nome
                                lead_nome = lead_encontrado.get('nome_exibicao') or lead_encontrado.get('nome', '')
                        except:
                            pass
                    
                    # Prepara responsável (array de strings)
                    responsaveis_val = responsavel_select.value
                    if not responsaveis_val:
                        responsaveis_val = []
                    elif isinstance(responsaveis_val, str):
                        responsaveis_val = [responsaveis_val]
                    
                    # Prepara Entrada do Lead (formato MM/AAAA)
                    entrada_lead = ''
                    if mes_select.value and ano_select.value:
                        entrada_lead = f"{mes_select.value}/{ano_select.value}"
                    
                    # Prepara dados
                    dados = {
                        'nome': nome_input.value.strip(),
                        'lead_id': lead_id if lead_id else None,
                        'lead_nome': lead_nome,  # Nome do lead para exibição no card
                        'valor_estimado': valor_float,
                        'entrada_lead': entrada_lead,
                        'nucleo': nucleo_select.value or 'Generalista',  # Núcleo (obrigatório, padrão: Generalista)
                        'origem': origem_select.value if origem_select.value else '',
                        'prioridade': prioridade_select.value or PRIORIDADE_PADRAO,
                        'responsavel': responsaveis_val,  # Array de strings
                        'link_slack': link_slack_input.value.strip() if link_slack_input.value else '',
                        'observacoes': observacoes_input.value.strip() if observacoes_input.value else '',
                    }
                    
                    try:
                        if estado_edicao['oportunidade_id']:
                            # Edição: mantém status e resultado
                            oportunidade_atual = buscar_oportunidade_por_id(estado_edicao['oportunidade_id'])
                            if oportunidade_atual:
                                dados['status'] = oportunidade_atual.get('status', 'agir')
                                if 'resultado' in oportunidade_atual:
                                    dados['resultado'] = oportunidade_atual.get('resultado')
                            
                            save_oportunidade(dados, estado_edicao['oportunidade_id'])
                            ui.notify('Oportunidade atualizada com sucesso!', type='positive')
                            estado_edicao['oportunidade_id'] = None
                        else:
                            # Nova: status padrão
                            dados['status'] = 'agir'
                            save_oportunidade(dados)
                            ui.notify('Oportunidade criada com sucesso!', type='positive')
                        
                        dialog_editar_oportunidade.close()
                        kanban_area.refresh()
                    except Exception as e:
                        ui.notify(f'Erro ao salvar oportunidade: {str(e)}', type='negative')
                
                # Botões
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Cancelar', on_click=dialog_editar_oportunidade.close).props('flat')
                    ui.button('Salvar', icon='save', on_click=salvar_oportunidade).props('color=primary')
                
                # Atualiza campos quando dialog abre
                def ao_abrir_dialog():
                    """Evento ao abrir dialog - usado apenas para NOVA oportunidade."""
                    # Se já tem ID no estado, a edição já carregou os dados
                    # Não fazer nada aqui para evitar sobrescrever
                    oportunidade_id = estado_edicao.get('oportunidade_id')
                    if oportunidade_id:
                        # Edição: dados já foram carregados em abrir_edicao()
                        print(f"[DEBUG] ao_abrir_dialog - Edição detectada, dados já carregados")
                        return
                    
                    # Nova oportunidade: limpa campos e carrega opções
                    print(f"[DEBUG] ao_abrir_dialog - Nova oportunidade, limpando campos")
                    atualizar_opcoes_leads(None)
                    atualizar_opcoes_responsaveis()
                    limpar_campos()
                
                dialog_editar_oportunidade.on('open', ao_abrir_dialog)
            
            # Dialog Confirmar Exclusão
            with ui.dialog() as dialog_confirmar_exclusao, ui.card().classes('w-full max-w-md p-6'):
                ui.label('Excluir Oportunidade').classes('text-xl font-bold mb-4 text-red-600')
                
                nome_oportunidade_label = ui.label('').classes('font-semibold text-gray-800 mb-4')
                ui.label('Deseja realmente excluir esta oportunidade?').classes('text-gray-700 mb-2')
                ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')
                
                def excluir_oportunidade():
                    from .novos_negocios_services import delete_oportunidade
                    
                    oportunidade = estado_exclusao.get('oportunidade')
                    if oportunidade and oportunidade.get('_id'):
                        try:
                            sucesso = delete_oportunidade(oportunidade['_id'])
                            if sucesso:
                                ui.notify('Oportunidade excluída com sucesso!', type='positive')
                                dialog_confirmar_exclusao.close()
                                estado_exclusao['oportunidade'] = None
                                kanban_area.refresh()
                            else:
                                ui.notify('Erro ao excluir oportunidade', type='negative')
                        except Exception as e:
                            ui.notify(f'Erro ao excluir: {str(e)}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancelar', on_click=dialog_confirmar_exclusao.close).props('flat')
                    ui.button('Excluir', icon='delete', on_click=excluir_oportunidade).props('color=negative')
                
                # Atualiza nome quando dialog abre
                def ao_abrir_exclusao():
                    oportunidade = estado_exclusao.get('oportunidade')
                    if oportunidade:
                        nome_oportunidade_label.text = f'"{oportunidade.get("nome", "Sem nome")}"'
                
                dialog_confirmar_exclusao.on('open', ao_abrir_exclusao)
            
            # Dialog Resultado
            with ui.dialog() as dialog_resultado, ui.card().classes('w-full max-w-md p-6'):
                ui.label('Resultado da Oportunidade').classes('text-xl font-bold mb-4 text-gray-800')
                ui.label('Como foi o resultado desta oportunidade?').classes('text-gray-700 mb-4')
                
                def definir_resultado(resultado: str):
                    from .novos_negocios_services import buscar_oportunidade_por_id, save_oportunidade
                    
                    oportunidade_id = estado_resultado.get('oportunidade_id')
                    if not oportunidade_id:
                        return
                    
                    try:
                        oportunidade = buscar_oportunidade_por_id(oportunidade_id)
                        if not oportunidade:
                            ui.notify('Oportunidade não encontrada', type='negative')
                            return
                        
                        # Atualiza apenas o resultado
                        dados = {**oportunidade, 'resultado': resultado}
                        save_oportunidade(dados, oportunidade_id)
                        
                        mensagem = 'Negócio marcado como ganho!' if resultado == 'ganho' else 'Negócio marcado como perdido.'
                        tipo = 'positive' if resultado == 'ganho' else 'warning'
                        ui.notify(mensagem, type=tipo)
                        
                        dialog_resultado.close()
                        estado_resultado['oportunidade_id'] = None
                        kanban_area.refresh()
                    except Exception as e:
                        ui.notify(f'Erro ao salvar resultado: {str(e)}', type='negative')
                
                with ui.column().classes('w-full gap-3'):
                    ui.button(
                        '✅ Negócio Ganho',
                        icon='check_circle',
                        on_click=lambda: definir_resultado('ganho')
                    ).classes('w-full py-3').style('background-color: #22C55E; color: white; font-weight: bold;')
                    
                    ui.button(
                        '❌ Negócio Perdido',
                        icon='cancel',
                        on_click=lambda: definir_resultado('perdido')
                    ).classes('w-full py-3').style('background-color: #EF4444; color: white; font-weight: bold;')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Cancelar', on_click=dialog_resultado.close).props('flat')
            
            # Conecta botão nova oportunidade
            def abrir_dialog_nova():
                estado_edicao['oportunidade_id'] = None
                dialog_editar_oportunidade.open()
            
            btn_nova_oportunidade.on('click', abrir_dialog_nova)
