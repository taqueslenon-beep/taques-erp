# Módulo de Benefícios Penais
# Gestão de transações penais, ANPP, suspensões e substituições

from nicegui import ui
from ....core import (
    save_data, get_clients_list, get_cases_list,
    get_processes_list, get_benefits_list, format_date_br
)

# Status possíveis para transação penal
TRANSACAO_PENAL_STATUS = [
    'Proposta', 
    'Em análise', 
    'Aceita', 
    'Homologada', 
    'Em cumprimento', 
    'Cumprida', 
    'Descumprida', 
    'Arquivada'
]


def get_beneficiarios():
    """Retorna lista de clientes para seleção"""
    return [c.get('name', '') for c in get_clients_list() if c.get('name')]


def get_casos():
    """Retorna lista de casos para seleção"""
    return [c.get('title', '') for c in get_cases_list() if c.get('title')]


def get_processos():
    """Retorna lista de processos para seleção"""
    return [p.get('number', '') for p in get_processes_list() if p.get('number')]


def render_beneficios_penais():
    """Renderiza a aba de benefícios penais com dialogs e tabela"""
    
    # Variável para armazenar o ID do benefício sendo editado
    editing_benefit_id = {'value': None}
    
    # ========================================
    # DIALOG - Nova Transação Penal
    # ========================================
    with ui.dialog() as transacao_penal_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Nova Transação Penal').classes('text-lg font-bold mb-4')
        
        tp_beneficiario = ui.select(
            options=get_beneficiarios(),
            label='Beneficiário',
            with_input=True
        ).classes('w-full mb-3').props('dense')
        
        tp_casos = ui.select(
            options=get_casos(),
            label='Casos Vinculados',
            multiple=True,
            with_input=True
        ).classes('w-full mb-3').props('dense use-chips')
        
        tp_processos = ui.select(
            options=get_processos(),
            label='Processos Vinculados',
            multiple=True,
            with_input=True
        ).classes('w-full mb-3').props('dense use-chips')
        
        tp_crime = ui.input(
            label='Crime Imputado',
            placeholder='Ex: Art. 38 da Lei 9.605/98'
        ).classes('w-full mb-3').props('dense')
        
        tp_status = ui.select(
            options=TRANSACAO_PENAL_STATUS,
            label='Status',
            value='Proposta'
        ).classes('w-full mb-3').props('dense')
        
        def save_transacao_penal():
            if not tp_beneficiario.value:
                ui.notify('Selecione um beneficiário!', type='warning')
                return
            if not tp_crime.value:
                ui.notify('Informe o crime imputado!', type='warning')
                return
            
            import uuid
            from datetime import datetime
            
            get_benefits_list().append({
                'id': str(uuid.uuid4())[:8],
                'beneficiario': tp_beneficiario.value,
                'tipo': 'Transação Penal',
                'status': tp_status.value or 'Proposta',
                'casos': tp_casos.value or [],
                'processos': tp_processos.value or [],
                'crime': tp_crime.value,
                'observacoes': f'Crime: {tp_crime.value}',
                # Campo poderá ser preenchido depois na aba "Marcos e Prazos"
                'data_cumprimento_integral': None,
                'observacoes_cumprimento_integral': '',
                'created_at': datetime.now().isoformat()
            })
            save_data()
            render_benefits_table.refresh()
            transacao_penal_dialog.close()
            
            # Limpa campos
            tp_beneficiario.value = None
            tp_casos.value = []
            tp_processos.value = []
            tp_crime.value = ''
            tp_status.value = 'Proposta'
            
            ui.notify('Transação Penal cadastrada com sucesso!')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=transacao_penal_dialog.close).props('flat dense')
            ui.button('Salvar', on_click=save_transacao_penal).props('dense color=primary')
    
    # ========================================
    # DIALOG - Editar Transação Penal (com menu lateral)
    # ========================================
    with ui.dialog() as edit_transacao_dialog, ui.card().classes('w-full max-w-3xl p-0'):
        ui.label('Editar Transação Penal').classes('text-lg font-bold p-4 pb-2')
        
        with ui.row().classes('w-full h-96'):
            # Menu lateral verde
            with ui.column().classes('w-48 h-full items-start').style('background-color: #223631;'):
                with ui.tabs().props('vertical dense align=left shrink').classes('w-full text-white text-left items-start justify-start').style('background-color: #223631;') as edit_tabs:
                    tab_dados = ui.tab('Dados Gerais', icon='description').props('inline-label').classes('text-white')
                    tab_marcos = ui.tab('Marcos e Prazos', icon='event').props('inline-label').classes('text-white')
            
            # Conteúdo das abas
            with ui.tab_panels(edit_tabs, value=tab_dados).classes('flex-1 p-4'):
                # Aba Dados Gerais
                with ui.tab_panel(tab_dados).classes('p-0'):
                    edit_beneficiario = ui.select(
                        options=get_beneficiarios(),
                        label='Beneficiário',
                        with_input=True
                    ).classes('w-full mb-3').props('dense')
                    
                    edit_casos = ui.select(
                        options=get_casos(),
                        label='Casos Vinculados',
                        multiple=True,
                        with_input=True
                    ).classes('w-full mb-3').props('dense use-chips')
                    
                    edit_processos = ui.select(
                        options=get_processos(),
                        label='Processos Vinculados',
                        multiple=True,
                        with_input=True
                    ).classes('w-full mb-3').props('dense use-chips')
                    
                    edit_crime = ui.input(
                        label='Crime Imputado',
                        placeholder='Ex: Art. 38 da Lei 9.605/98'
                    ).classes('w-full mb-3').props('dense')
                    
                    edit_status = ui.select(
                        options=TRANSACAO_PENAL_STATUS,
                        label='Status',
                        value='Proposta'
                    ).classes('w-full mb-3').props('dense')
                
                # Aba Marcos e Prazos
                with ui.tab_panel(tab_marcos).classes('p-0'):
                    with ui.column().classes('w-full h-full items-start justify-start'):
                        ui.label('Marcos e Prazos').classes('text-lg font-bold mb-3')
                        
                        # 3. Data do Cumprimento Integral do Acordo
                        ui.label('3. Data do Cumprimento Integral do Acordo:').classes('font-semibold mb-1')
                        
                        edit_data_cumprimento = ui.input(
                            label='Data do Cumprimento Integral do Acordo',
                            placeholder='Selecione a data em que o acordo foi totalmente cumprido'
                        ).classes('w-full mb-2').props('dense type=date')
                        
                        edit_observacoes_cumprimento = ui.textarea(
                            label='Observações sobre o cumprimento integral',
                            placeholder='Use este espaço para registrar observações importantes sobre o cumprimento integral do acordo.'
                        ).classes('w-full mb-2').props('dense autogrow')
                        
                        ui.label(
                            'Este é o "marco zero": a partir desta data começa a contar o prazo de 5 anos de impedimento '
                            'para uma nova transação penal.'
                        ).classes('text-sm text-gray-500')
        
        def update_transacao_penal():
            if not edit_beneficiario.value:
                ui.notify('Selecione um beneficiário!', type='warning')
                return
            if not edit_crime.value:
                ui.notify('Informe o crime imputado!', type='warning')
                return
            
            # Encontra o benefício pelo ID
            benefit_id = editing_benefit_id['value']
            idx = next((i for i, b in enumerate(get_benefits_list()) if b.get('id') == benefit_id), None)
            
            if idx is not None:
                get_benefits_list()[idx].update({
                    'beneficiario': edit_beneficiario.value,
                    'casos': edit_casos.value or [],
                    'processos': edit_processos.value or [],
                    'crime': edit_crime.value,
                    'status': edit_status.value or 'Proposta',
                    'observacoes': f'Crime: {edit_crime.value}',
                    'data_cumprimento_integral': edit_data_cumprimento.value,
                    'observacoes_cumprimento_integral': edit_observacoes_cumprimento.value,
                })
                save_data()
                render_benefits_table.refresh()
                edit_transacao_dialog.close()
                ui.notify('Transação Penal atualizada com sucesso!')
            else:
                ui.notify('Erro: benefício não encontrado!', type='negative')
        
        with ui.row().classes('w-full justify-end gap-2 p-4 pt-0'):
            ui.button('Cancelar', on_click=edit_transacao_dialog.close).props('flat dense')
            ui.button('Salvar Alterações', on_click=update_transacao_penal).props('dense color=primary')
    
        def open_edit_dialog(benefit_data):
            """Abre o dialog de edição com dados pré-preenchidos"""
            benefit_id = benefit_data.get('id')
            editing_benefit_id['value'] = benefit_id
            
            # Busca dados completos do benefício
            benefit = next((b for b in get_benefits_list() if b.get('id') == benefit_id), None)
            if benefit:
                edit_beneficiario.value = benefit.get('beneficiario', '')
                edit_casos.value = benefit.get('casos', [])
                edit_processos.value = benefit.get('processos', [])
                edit_crime.value = benefit.get('crime', '')
                edit_status.value = benefit.get('status', 'Proposta')
                edit_data_cumprimento.value = benefit.get('data_cumprimento_integral', None)
                edit_observacoes_cumprimento.value = benefit.get('observacoes_cumprimento_integral', '')
                edit_transacao_dialog.open()
    
    # ========================================
    # DIALOG - Editar Suspensão Condicional do Processo (Sursi Processual)
    # ========================================
    with ui.dialog() as edit_suspensao_dialog, ui.card().classes('w-full max-w-3xl p-0'):
        ui.label('Editar Suspensão Condicional do Processo').classes('text-lg font-bold p-4 pb-2')

        with ui.row().classes('w-full h-96'):
            # Menu lateral verde
            with ui.column().classes('w-48 h-full items-start').style('background-color: #223631;'):
                with ui.tabs().props('vertical dense align=left shrink').classes('w-full text-white text-left items-start justify-start').style('background-color: #223631;') as edit_susp_tabs:
                    tab_susp_dados = ui.tab('Dados Gerais', icon='description').props('inline-label').classes('text-white')
                    tab_susp_marcos = ui.tab('Marcos e Prazos', icon='event').props('inline-label').classes('text-white')

            # Conteúdo das abas
            with ui.tab_panels(edit_susp_tabs, value=tab_susp_dados).classes('flex-1 p-4'):
                # Aba Dados Gerais
                with ui.tab_panel(tab_susp_dados).classes('p-0'):
                    edit_susp_beneficiario = ui.select(
                        options=get_beneficiarios(),
                        label='Beneficiário',
                        with_input=True,
                    ).classes('w-full mb-3').props('dense')

                    edit_susp_casos = ui.select(
                        options=get_casos(),
                        label='Casos Vinculados',
                        multiple=True,
                        with_input=True,
                    ).classes('w-full mb-3').props('dense use-chips')

                    edit_susp_processos = ui.select(
                        options=get_processos(),
                        label='Processos Vinculados',
                        multiple=True,
                        with_input=True,
                    ).classes('w-full mb-3').props('dense use-chips')

                    edit_susp_crime = ui.input(
                        label='Crime / Fato imputado',
                        placeholder='Ex: Art. 121, §4º, do CP ou descrição do fato',
                    ).classes('w-full mb-3').props('dense')

                    edit_susp_status = ui.select(
                        options=[
                            'Pendente',
                            'Deferido',
                            'Em cumprimento',
                            'Cumprido',
                            'Revogado',
                            'Descumprido',
                        ],
                        label='Status',
                        value='Pendente',
                    ).classes('w-full mb-3').props('dense')

                # Aba Marcos e Prazos
                with ui.tab_panel(tab_susp_marcos).classes('p-0'):
                    with ui.column().classes('w-full h-full items-start justify-start'):
                        ui.label('Marcos e Prazos da Suspensão').classes('text-lg font-bold mb-3')

                        edit_susp_data_inicio = ui.input(
                            label='Data de início da suspensão',
                            placeholder='Selecione a data em que começou a suspensão do processo',
                        ).classes('w-full mb-2').props('dense type=date')

                        edit_susp_prazo_anos = ui.select(
                            options=['2', '3', '4'],
                            label='Prazo da suspensão (em anos)',
                        ).classes('w-full mb-2').props('dense')

                        ui.label(
                            'O prazo da suspensão é contado a partir da data de início, de acordo com o número de anos '
                            'definido na decisão judicial.'
                        ).classes('text-sm text-gray-500 mb-3')

                        edit_susp_observacoes_decisao = ui.textarea(
                            label='Observações conforme decisão judicial',
                            placeholder='Descreva, em resumo, o que foi fixado na decisão (ex.: condições, observações do juiz, etc.).',
                        ).classes('w-full mb-2').props('dense autogrow')

        def update_suspensao_condicional():
            """Atualiza dados de uma Suspensão Condicional do Processo existente."""
            if not edit_susp_beneficiario.value:
                ui.notify('Selecione um beneficiário!', type='warning')
                return
            if not edit_susp_crime.value:
                ui.notify('Informe o crime ou fato imputado!', type='warning')
                return

            # Converte prazo em anos (2, 3 ou 4) para meses para armazenamento
            prazo_meses = None
            if edit_susp_prazo_anos.value:
                try:
                    anos = int(str(edit_susp_prazo_anos.value).strip())
                    prazo_meses = anos * 12
                except ValueError:
                    ui.notify('Selecione um prazo válido (2, 3 ou 4 anos).', type='warning')
                    return

            benefit_id = editing_benefit_id['value']
            idx = next((i for i, b in enumerate(get_benefits_list()) if b.get('id') == benefit_id), None)

            if idx is not None:
                get_benefits_list()[idx].update(
                    {
                        'beneficiario': edit_susp_beneficiario.value,
                        'casos': edit_susp_casos.value or [],
                        'processos': edit_susp_processos.value or [],
                        'crime': edit_susp_crime.value,
                        'status': edit_susp_status.value or 'Pendente',
                        'condicoes': get_benefits_list()[idx].get('condicoes', ''),
                        'data_inicio_suspensao': edit_susp_data_inicio.value,
                        'prazo_suspensao_meses': prazo_meses,
                        'observacoes_decisao_suspensao': edit_susp_observacoes_decisao.value or '',
                    }
                )
                save_data()
                render_benefits_table.refresh()
                edit_suspensao_dialog.close()
                ui.notify('Suspensão condicional do processo atualizada com sucesso!')
            else:
                ui.notify('Erro: benefício não encontrado!', type='negative')

        with ui.row().classes('w-full justify-end gap-2 p-4 pt-0'):
            ui.button('Cancelar', on_click=edit_suspensao_dialog.close).props('flat dense')
            ui.button('Salvar Alterações', on_click=update_suspensao_condicional).props('dense color=primary')

        def open_edit_suspensao(benefit_data):
            """Abre o dialog de edição específico para Suspensão Condicional do Processo."""
            benefit_id = benefit_data.get('id')
            editing_benefit_id['value'] = benefit_id

            benefit = next((b for b in get_benefits_list() if b.get('id') == benefit_id), None)
            if benefit:
                edit_susp_beneficiario.value = benefit.get('beneficiario', '')
                edit_susp_casos.value = benefit.get('casos', [])
                edit_susp_processos.value = benefit.get('processos', [])
                edit_susp_crime.value = benefit.get('crime', '')
                edit_susp_status.value = benefit.get('status', 'Pendente')
                edit_susp_data_inicio.value = benefit.get('data_inicio_suspensao', None)
                prazo_valor = benefit.get('prazo_suspensao_meses', None)
                if prazo_valor:
                    try:
                        anos = int(prazo_valor) // 12
                        edit_susp_prazo_anos.value = str(anos)
                    except Exception:
                        edit_susp_prazo_anos.value = None
                else:
                    edit_susp_prazo_anos.value = None
                edit_susp_observacoes_decisao.value = benefit.get('observacoes_decisao_suspensao', '')
                edit_suspensao_dialog.open()

    # ========================================
    # DIALOG - Novo Acordo de Não Persecução Penal (ANPP)
    # ========================================
    with ui.dialog() as anpp_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Novo Acordo de Não Persecução Penal (ANPP)').classes('text-lg font-bold mb-4')

        anpp_beneficiario = ui.select(
            options=get_beneficiarios(),
            label='Beneficiário',
            with_input=True,
        ).classes('w-full mb-3').props('dense')

        anpp_casos = ui.select(
            options=get_casos(),
            label='Casos Vinculados',
            multiple=True,
            with_input=True,
        ).classes('w-full mb-3').props('dense use-chips')

        anpp_processos = ui.select(
            options=get_processos(),
            label='Processos Vinculados',
            multiple=True,
            with_input=True,
        ).classes('w-full mb-3').props('dense use-chips')

        anpp_fato = ui.input(
            label='Fato/Investigação abrangidos',
            placeholder='Descreva o fato ou investigação a que o ANPP se refere',
        ).classes('w-full mb-3').props('dense')

        anpp_data_cumprimento = ui.input(
            label='Data de cumprimento do acordo (se já cumprido)',
        ).classes('w-full mb-3').props('dense type=date')

        anpp_condicoes = ui.textarea(
            label='Condições do acordo',
            placeholder='Ex: prestação de serviços, pagamento de multa, obrigações específicas...',
        ).classes('w-full mb-3').props('dense rows=3')

        anpp_status = ui.select(
            options=TRANSACAO_PENAL_STATUS,
            label='Status',
            value='Proposta',
        ).classes('w-full mb-3').props('dense')

        def save_anpp():
            if not anpp_beneficiario.value:
                ui.notify('Selecione um beneficiário!', type='warning')
                return
            if not anpp_fato.value:
                ui.notify('Descreva o fato/objeto do ANPP!', type='warning')
                return

            import uuid
            from datetime import datetime

            get_benefits_list().append(
                {
                    'id': str(uuid.uuid4())[:8],
                    'beneficiario': anpp_beneficiario.value,
                    'tipo': 'ANPP',
                    'status': anpp_status.value or 'Proposta',
                    'casos': anpp_casos.value or [],
                    'processos': anpp_processos.value or [],
                    'crime': anpp_fato.value,
                    'condicoes': anpp_condicoes.value or '',
                    'observacoes': f'ANPP: {anpp_fato.value}',
                    'data_cumprimento_integral': anpp_data_cumprimento.value or None,
                    'observacoes_cumprimento_integral': '',
                    'created_at': datetime.now().isoformat(),
                }
            )

            save_data()
            render_benefits_table.refresh()

            # Limpa campos
            anpp_beneficiario.value = None
            anpp_casos.value = []
            anpp_processos.value = []
            anpp_fato.value = ''
            anpp_condicoes.value = ''
            anpp_status.value = 'Proposta'
            anpp_data_cumprimento.value = ''

            anpp_dialog.close()
            ui.notify('ANPP cadastrado com sucesso!')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=anpp_dialog.close).props('flat dense')
            ui.button('Salvar', on_click=save_anpp).props('dense color=primary')
    
    # ========================================
    # DIALOG - Nova Suspensão Condicional do Processo (Sursi Processual)
    # ========================================
    with ui.dialog() as suspensao_dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label('Nova Suspensão Condicional do Processo (Sursi Processual)').classes('text-lg font-bold mb-4')

        susp_beneficiario = ui.select(
            options=get_beneficiarios(),
            label='Beneficiário',
            with_input=True,
        ).classes('w-full mb-3').props('dense')

        susp_casos = ui.select(
            options=get_casos(),
            label='Casos Vinculados',
            multiple=True,
            with_input=True,
        ).classes('w-full mb-3').props('dense use-chips')

        susp_processos = ui.select(
            options=get_processos(),
            label='Processos Vinculados',
            multiple=True,
            with_input=True,
        ).classes('w-full mb-3').props('dense use-chips')

        susp_crime = ui.input(
            label='Crime / Fato imputado',
            placeholder='Ex: Art. 121, §4º, do CP ou descrição do fato'
        ).classes('w-full mb-3').props('dense')

        susp_data_inicio = ui.input(
            label='Data de início da suspensão',
            placeholder='Selecione a data em que começou a suspensão do processo'
        ).classes('w-full mb-3').props('dense type=date')

        susp_prazo_anos = ui.select(
            options=['2', '3', '4'],
            label='Prazo da suspensão (em anos)',
            value='2',
        ).classes('w-full mb-3').props('dense')

        susp_condicoes = ui.textarea(
            label='Condições da suspensão',
            placeholder='Ex: comparecimento mensal em juízo, proibição de ausentar-se da comarca, etc.'
        ).classes('w-full mb-3').props('dense autogrow')

        susp_status = ui.select(
            options=[
                'Pendente',
                'Deferido',
                'Em cumprimento',
                'Cumprido',
                'Revogado',
                'Descumprido',
            ],
            label='Status',
            value='Pendente',
        ).classes('w-full mb-4').props('dense')

        def save_suspensao():
            """Salva nova Suspensão Condicional do Processo."""
            if not susp_beneficiario.value:
                ui.notify('Selecione um beneficiário!', type='warning')
                return
            if not susp_crime.value:
                ui.notify('Informe o crime ou fato imputado!', type='warning')
                return

            import uuid
            from datetime import datetime

            # Converte prazo em anos (2, 3 ou 4) para meses para armazenamento
            prazo_meses = None
            if susp_prazo_anos.value:
                try:
                    anos = int(str(susp_prazo_anos.value).strip())
                    prazo_meses = anos * 12
                except ValueError:
                    ui.notify('Selecione um prazo válido (2, 3 ou 4 anos).', type='warning')
                    return

            get_benefits_list().append(
                {
                    'id': str(uuid.uuid4())[:8],
                    'beneficiario': susp_beneficiario.value,
                    'tipo': 'Suspensão Condicional',
                    'status': susp_status.value or 'Pendente',
                    'casos': susp_casos.value or [],
                    'processos': susp_processos.value or [],
                    'crime': susp_crime.value,
                    'condicoes': susp_condicoes.value or '',
                    'data_inicio_suspensao': susp_data_inicio.value or None,
                    'prazo_suspensao_meses': prazo_meses,
                    'observacoes': f'Sursi processual referente a: {susp_crime.value}',
                    # Mantém campos de cumprimento para compatibilidade geral
                    'data_cumprimento_integral': None,
                    'observacoes_cumprimento_integral': '',
                    'created_at': datetime.now().isoformat(),
                }
            )

            save_data()
            render_benefits_table.refresh()

            # Limpa campos
            susp_beneficiario.value = None
            susp_casos.value = []
            susp_processos.value = []
            susp_crime.value = ''
            susp_data_inicio.value = ''
            susp_prazo_anos.value = '2'
            susp_condicoes.value = ''
            susp_status.value = 'Pendente'

            suspensao_dialog.close()
            ui.notify('Suspensão condicional do processo cadastrada com sucesso!')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=suspensao_dialog.close).props('flat dense')
            ui.button('Salvar', on_click=save_suspensao).props('dense color=primary')
    
    with ui.dialog() as substituicao_dialog:
        with ui.card().classes('w-full max-w-lg p-6'):
            ui.label('Nova Substituição da Pena').classes('text-lg font-bold mb-4')
            ui.label('Em desenvolvimento...').classes('text-gray-400 italic')
            ui.button('Fechar', on_click=substituicao_dialog.close).props('flat dense')
    
    # ========================================
    # BOTÕES - Novos Benefícios
    # ========================================
    with ui.row().classes('w-full justify-end mb-3 gap-2 flex-wrap'):
        ui.button('Nova Transação Penal', icon='add_circle', on_click=transacao_penal_dialog.open).props('dense size=sm color=primary')
        ui.button('Novo ANPP', icon='handshake', on_click=anpp_dialog.open).props('dense size=sm color=primary')
        ui.button('Nova Suspensão Condicional do Processo (Sursi Processual)', icon='pause_circle', on_click=suspensao_dialog.open).props('dense size=sm color=primary')
        ui.button('Nova Substituição de Pena', icon='swap_horiz', on_click=substituicao_dialog.open).props('dense size=sm color=primary')
    
    # ========================================
    # TABELA - Benefícios Cadastrados
    # ========================================
    with ui.card().classes('w-full'):
        ui.label('Benefícios Penais Cadastrados').classes('font-bold text-lg mb-3')
        
        @ui.refreshable
        def render_benefits_table():
            def remove_benefit(benefit_id):
                idx = next((i for i, b in enumerate(get_benefits_list()) if b.get('id') == benefit_id), None)
                if idx is not None:
                    get_benefits_list().pop(idx)
                    save_data()
                    render_benefits_table.refresh()
                    ui.notify('Benefício removido!')
            
            def render_table_for_type(tipo: str, show_date: bool = False):
                """Renderiza uma tabela filtrada por tipo de benefício."""
                # Filtra benefícios pelo tipo
                filtered = [b for b in get_benefits_list() if b.get('tipo') == tipo]
                if not filtered:
                    ui.label('Nenhum benefício deste tipo cadastrado.').classes('text-gray-400 italic py-4')
                    return
                
                columns = [
                    {'name': 'beneficiario', 'label': 'Beneficiário', 'field': 'beneficiario', 'align': 'left'},
                    {'name': 'tipo', 'label': 'Benefício', 'field': 'tipo', 'align': 'left'},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                    {'name': 'casos', 'label': 'Casos', 'field': 'casos', 'align': 'left'},
                    {'name': 'processos', 'label': 'Processos', 'field': 'processos', 'align': 'left'},
                    {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
                ]

                if show_date:
                    # Insere colunas de datas antes das ações
                    if tipo in ('ANPP', 'Transação Penal'):
                        # Para ANPP e Transação Penal: data de cumprimento + fim da quarentena de 5 anos
                        columns.insert(
                            5,
                            {
                                'name': 'data_cumprimento',
                                'label': 'Data de Cumprimento do Acordo',
                                'field': 'data_cumprimento',
                                'align': 'center',
                            },
                        )
                        columns.insert(
                            6,
                            {
                                'name': 'fim_quarentena',
                                'label': 'Fim da quarentena de 5 anos',
                                'field': 'fim_quarentena',
                                'align': 'center',
                            },
                        )
                    elif tipo == 'Suspensão Condicional':
                        # Para Suspensão Condicional do Processo: início / fim do período de prova
                        columns.insert(
                            5,
                            {
                                'name': 'inicio_prova',
                                'label': 'Início do período de prova',
                                'field': 'inicio_prova',
                                'align': 'center',
                            },
                        )
                        columns.insert(
                            6,
                            {
                                'name': 'fim_prova',
                                'label': 'Fim do período de prova',
                                'field': 'fim_prova',
                                'align': 'center',
                            },
                        )
                        columns.insert(
                            7,
                            {
                                'name': 'apto_novo_crime',
                                'label': 'Apto para novo processo',
                                'field': 'apto_novo_crime',
                                'align': 'center',
                            },
                        )
                    else:
                        columns.insert(
                            5,
                            {
                                'name': 'data_cumprimento',
                                'label': 'Data Cumprimento do Acordo',
                                'field': 'data_cumprimento',
                                'align': 'center',
                            },
                        )
                
                rows = []
                for benefit in filtered:
                    casos_str = ', '.join(benefit.get('casos', [])) if benefit.get('casos') else '-'
                    processos_str = ', '.join(benefit.get('processos', [])) if benefit.get('processos') else '-'
                    row = {
                        'id': benefit.get('id'),
                        'beneficiario': benefit.get('beneficiario', ''),
                        'tipo': benefit.get('tipo', ''),
                        'status': benefit.get('status', ''),
                        'casos': casos_str,
                        'processos': processos_str,
                    }
                    if show_date:
                        if tipo in ('ANPP', 'Transação Penal'):
                            data_cumpr = benefit.get('data_cumprimento_integral')
                            row['data_cumprimento'] = format_date_br(data_cumpr)

                            # Para ANPP e Transação Penal, calcula automaticamente o fim da quarentena de 5 anos
                            if data_cumpr:
                                from datetime import datetime, timedelta

                                try:
                                    base = datetime.fromisoformat(str(data_cumpr)).date()
                                except Exception:
                                    try:
                                        base = datetime.strptime(str(data_cumpr), '%Y-%m-%d').date()
                                    except Exception:
                                        base = None

                                if base:
                                    try:
                                        fim = base.replace(year=base.year + 5)
                                    except ValueError:
                                        fim = base + timedelta(days=5 * 365)

                                    # Define string formatada e status (já passou ou não)
                                    from datetime import date as _date

                                    hoje = _date.today()
                                    row['fim_quarentena'] = format_date_br(fim.isoformat())
                                    row['fim_quarentena_futuro'] = fim > hoje
                                else:
                                    row['fim_quarentena'] = '-'
                                    row['fim_quarentena_futuro'] = None
                            else:
                                row['fim_quarentena'] = '-'
                                row['fim_quarentena_futuro'] = None
                        elif tipo == 'Suspensão Condicional':
                            # Início do período de prova = data de início da suspensão
                            data_inicio = benefit.get('data_inicio_suspensao')
                            row['inicio_prova'] = format_date_br(data_inicio)

                            # Fim do período de prova = data de início + prazo (2, 3 ou 4 anos)
                            data_fim = None
                            prazo_meses = benefit.get('prazo_suspensao_meses')
                            if data_inicio and prazo_meses:
                                from datetime import datetime, timedelta, date as _date

                                try:
                                    base = datetime.fromisoformat(str(data_inicio)).date()
                                except Exception:
                                    try:
                                        base = datetime.strptime(str(data_inicio), '%Y-%m-%d').date()
                                    except Exception:
                                        base = None

                                if base:
                                    anos = int(prazo_meses) // 12
                                    try:
                                        data_fim = base.replace(year=base.year + anos)
                                    except ValueError:
                                        data_fim = base + timedelta(days=anos * 365)

                                    hoje = _date.today()
                                    row['fim_prova'] = format_date_br(data_fim.isoformat())
                                    # True se ainda não expirou (futuro), False se já expirou
                                    row['fim_prova_futuro'] = data_fim > hoje
                                    # Apto para novo processo sem revogação: somente após o fim do período de prova
                                    row['apto_novo_crime'] = 'Sim' if not row['fim_prova_futuro'] else 'Não'
                                else:
                                    row['fim_prova'] = '-'
                                    row['fim_prova_futuro'] = None
                                    row['apto_novo_crime'] = '-'
                            else:
                                row['fim_prova'] = '-'
                                row['fim_prova_futuro'] = None
                                row['apto_novo_crime'] = '-'
                        else:
                            # Outros tipos com apenas data de cumprimento simples
                            data_cumpr = benefit.get('data_cumprimento_integral')
                            row['data_cumprimento'] = format_date_br(data_cumpr)
                    rows.append(row)
                
                table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full').props('flat dense')
                
                # Slot para status com badge colorido
                table.add_slot('body-cell-status', '''
                    <q-td :props="props">
                        <q-badge 
                            :color="props.value === 'Homologada' || props.value === 'Cumprida' || props.value === 'Deferido' || props.value === 'Cumprido' ? 'green' : 
                                    props.value === 'Aceita' || props.value === 'Elegível' ? 'teal' :
                                    props.value === 'Em análise' || props.value === 'Proposta' || props.value === 'Pendente' || props.value === 'Em cumprimento' ? 'orange' : 
                                    props.value === 'Descumprida' || props.value === 'Indeferido' || props.value === 'Revogado' || props.value === 'Arquivada' ? 'red' : 'grey'">
                            {{ props.value }}
                        </q-badge>
                    </q-td>
                ''')

                if show_date:
                    if tipo in ('ANPP', 'Transação Penal'):
                        # Data de cumprimento em azul escuro e negrito
                        table.add_slot('body-cell-data_cumprimento', '''
                            <q-td :props="props">
                                <span class="text-blue-800 font-bold">
                                    {{ props.value || '-' }}
                                </span>
                            </q-td>
                        ''')

                        # Fim da quarentena: verde escuro se já passou, vermelho se ainda não passou
                        table.add_slot('body-cell-fim_quarentena', '''
                            <q-td :props="props">
                                <span
                                    :class="props.row.fim_quarentena_futuro ? 'text-red-600 font-bold' : 'text-green-700 font-bold'"
                                >
                                    {{ props.value || '-' }}
                                </span>
                            </q-td>
                        ''')
                    elif tipo == 'Suspensão Condicional':
                        # Início do período de prova em azul escuro e negrito
                        table.add_slot('body-cell-inicio_prova', '''
                            <q-td :props="props">
                                <span class="text-blue-800 font-bold">
                                    {{ props.value || '-' }}
                                </span>
                            </q-td>
                        ''')

                        # Fim do período de prova: verde se já expirou, vermelho se ainda está em curso
                        table.add_slot('body-cell-fim_prova', '''
                            <q-td :props="props">
                                <span
                                    :class="props.row.fim_prova_futuro ? 'text-red-600 font-bold' : 'text-green-700 font-bold'"
                                >
                                    {{ props.value || '-' }}
                                </span>
                            </q-td>
                        ''')
                        # Apto para ser processado por outro crime sem revogação
                        table.add_slot('header-cell-apto_novo_crime', '''
                            <q-th :props="props">
                                Apto para ser processado por outro crime
                                <i>sem a revogação da suspensão condicional do processo</i>
                            </q-th>
                        ''')
                        table.add_slot('body-cell-apto_novo_crime', '''
                            <q-td :props="props">
                                <span
                                    :class="props.value === 'Sim' ? 'text-green-700 font-bold' : (props.value === 'Não' ? 'text-red-600 font-bold' : 'text-gray-500')"
                                >
                                    {{ props.value || '-' }}
                                </span>
                            </q-td>
                        ''')
                    else:
                        # Data de cumprimento em badge padrão (para outros tipos)
                        table.add_slot('body-cell-data_cumprimento', '''
                            <q-td :props="props">
                                <q-badge v-if="props.value && props.value !== '-'" color="primary" text-color="white">
                                    {{ props.value }}
                                </q-badge>
                                <span v-else>-</span>
                            </q-td>
                        ''')
                
                # Slot para ações (editar e excluir)
                table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn flat dense icon="edit" color="primary" @click="$parent.$emit('edit', props.row)" size="sm"/>
                        <q-btn flat dense icon="delete" color="red" @click="$parent.$emit('delete', props.row)" size="sm"/>
                    </q-td>
                ''')
                
                def handle_edit(e):
                    row = e.args
                    # Para Suspensão Condicional do Processo, abre modal específico
                    if row.get('tipo') == 'Suspensão Condicional':
                        open_edit_suspensao(row)
                    else:
                        open_edit_dialog(row)

                table.on('edit', handle_edit)
                table.on('delete', lambda e: remove_benefit(e.args['id']))

            # Grupos de planilhas empilhados (sem sub-abas)
            with ui.expansion('Transações Penais', icon='gavel', value=True).classes('w-full mb-3 text-base font-semibold'):
                render_table_for_type('Transação Penal', show_date=True)

            with ui.expansion('Acordos de Não Persecução Penal (ANPP)', icon='handshake').classes('w-full mb-3 text-base font-semibold'):
                render_table_for_type('ANPP', show_date=True)

            with ui.expansion('Suspensão Condicional do Processo (Sursi Processual)', icon='pause_circle').classes('w-full mb-3 text-base font-semibold'):
                render_table_for_type('Suspensão Condicional', show_date=True)

            with ui.expansion('Suspensão Condicional da Pena (Sursi Penal)', icon='pause_circle').classes('w-full mb-3 text-base font-semibold'):
                render_table_for_type('Substituição da Pena', show_date=False)
        
        render_benefits_table()
