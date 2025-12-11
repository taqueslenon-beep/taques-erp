"""
carlos_page.py - Página detalhada de análise de riscos penais do Carlos.

Dashboard visual completo para entender exposição penal.
"""

from nicegui import ui
from typing import Dict, List, Any
from ....core import layout
from ....auth import is_authenticated

from .dados_processos import DADOS_REU, PROCESSOS
from .calculos_penas import CENARIOS, TIMELINE_PRISAO
from .ui_components import (
    stat_card, crime_badge, regime_badge, cenario_card, 
    alerta_box, copiar_numero_processo, timeline_vertical
)


# =============================================================================
# FUNÇÕES AUXILIARES DE RENDERIZAÇÃO
# =============================================================================

def render_resumo_executivo():
    """Renderiza a seção de resumo executivo com 4 cards."""
    total_crimes = sum(len(p.get('crimes', [])) for p in PROCESSOS)
    comarcas = set(p['comarca'] for p in PROCESSOS)
    area_total = sum(p.get('area_atingida_ha', 0) for p in PROCESSOS if 'area_atingida_ha' in p)
    area_total += sum(p.get('area_total_ha', 0) for p in PROCESSOS if 'area_total_ha' in p)
    
    with ui.row().classes('w-full gap-4 flex-wrap mb-6'):
        stat_card('Processos Ativos', '3', '#dc2626', f'Em {len(comarcas)} comarcas')
        stat_card('Crimes Imputados', str(total_crimes), '#dc2626', 'Arts. 38, 38-A e 48')
        stat_card('Área Total Afetada', f'{area_total:.2f} ha', '#f59e0b', 'Mata Atlântica + APP')
        stat_card('Pena Máxima Teórica', '44 anos', '#991b1b', 'Concurso material')


def render_tabela_processos():
    """Renderiza tabela resumo dos processos."""
    with ui.card().classes('w-full p-4 mb-6'):
        ui.label('📋 Processos em Andamento').classes('text-lg font-bold text-gray-800 mb-4')
        
        columns = [
            {'name': 'processo', 'label': 'Processo', 'field': 'processo', 'align': 'left'},
            {'name': 'comarca', 'label': 'Comarca', 'field': 'comarca', 'align': 'left'},
            {'name': 'data', 'label': 'Data', 'field': 'data', 'align': 'center'},
            {'name': 'caso', 'label': 'Caso', 'field': 'caso', 'align': 'left'},
            {'name': 'crimes', 'label': 'Crimes', 'field': 'crimes', 'align': 'center'},
            {'name': 'area', 'label': 'Área (ha)', 'field': 'area', 'align': 'right'},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
        ]
        
        rows = []
        for p in PROCESSOS:
            caso = p.get('caso_erp') or ', '.join(p.get('casos_erp', []))
            num_crimes = len(p.get('crimes', []))
            area = p.get('area_atingida_ha') or p.get('area_total_ha', '-')
            rows.append({
                'processo': p['numero'][:25] + '...' if len(p['numero']) > 25 else p['numero'],
                'comarca': p['comarca'],
                'data': p.get('data_denuncia') or p.get('data_denuncia_original', '-'),
                'caso': caso,
                'crimes': str(num_crimes),
                'area': f'{area}' if isinstance(area, (int, float)) else area,
                'status': p['status']
            })
        
        ui.table(columns=columns, rows=rows, row_key='processo').classes('w-full').props('flat bordered')


def render_cenarios_condenacao():
    """Renderiza os 3 cenários de condenação."""
    with ui.column().classes('w-full gap-6 mb-6'):
        ui.label('🎯 Cenários Possíveis de Condenação').classes('text-2xl font-bold text-gray-800')
        ui.label('Análise baseada em jurisprudência do STJ e TJSC').classes('text-lg text-gray-600 mb-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            for cenario_key in ['otimista', 'intermediario', 'pessimista']:
                cenario_card(CENARIOS[cenario_key])


def render_calculo_detalhado():
    """Renderiza seção de cálculo detalhado em expansions."""
    with ui.column().classes('w-full gap-4 mb-6'):
        ui.label('🧮 Metodologia de Cálculo').classes('text-2xl font-bold text-gray-800 mb-4')
        
        for cenario_key, cenario in CENARIOS.items():
            with ui.expansion(cenario['nome'], icon='calculate').classes('w-full border rounded bg-gray-50 mb-2'):
                with ui.column().classes('gap-3 p-4'):
                    calculo = cenario.get('calculo', {})
                    
                    # Tabela de crimes
                    if 'crimes' in calculo:
                        with ui.table(
                            columns=[
                                {'name': 'item', 'label': 'Item', 'field': 'item', 'align': 'left'},
                                {'name': 'pena', 'label': 'Pena (meses)', 'field': 'pena', 'align': 'right'}
                            ],
                            rows=[
                                {
                                    'item': crime.get('grupo') or crime.get('artigo', ''),
                                    'pena': f"{crime.get('pena_final') or crime.get('pena_unit') or crime.get('pena_meses', 0)}"
                                }
                                for crime in calculo['crimes']
                            ]
                        ).classes('w-full').props('flat bordered'):
                            pass
                    
                    # Total
                    with ui.row().classes('items-center gap-2 mt-4'):
                        ui.label('Total:').classes('font-bold text-lg')
                        ui.label(calculo.get('pena_total_texto', 'N/A')).classes('text-xl font-bold').style(f'color: {cenario["cor"]};')
                    
                    # Regra de concurso
                    if cenario_key == 'otimista':
                        ui.label('Regra aplicada: Pena única (1 crime)').classes('text-sm text-gray-600 italic mt-2')
                    elif cenario_key == 'intermediario':
                        ui.label('Regra aplicada: Continuidade delitiva (crimes agrupados)').classes('text-sm text-gray-600 italic mt-2')
                    else:
                        ui.label('Regra aplicada: Concurso material (penas somadas)').classes('text-sm text-gray-600 italic mt-2')


def render_timeline_prisao():
    """Renderiza timeline de quando pode haver prisão."""
    with ui.card().classes('w-full p-6 mb-6'):
        ui.label('⏱️ Linha do Tempo até Possível Prisão').classes('text-2xl font-bold text-gray-800 mb-4')
        
        timeline_vertical(TIMELINE_PRISAO['etapas'])
        
        # Prazo total
        with ui.row().classes('items-center gap-2 mt-4 p-4 bg-yellow-50 rounded'):
            ui.icon('schedule', size='24px').classes('text-yellow-700')
            ui.label(f"Prazo total estimado: {TIMELINE_PRISAO['prazo_total_estimado']}").classes('font-bold text-yellow-900')
        
        # Exceção - Prisão preventiva
        if TIMELINE_PRISAO.get('excecao_prisao_preventiva', {}).get('possivel'):
            excecao = TIMELINE_PRISAO['excecao_prisao_preventiva']
            alerta_box(
                '⚠️ Exceção: Prisão Preventiva',
                excecao.get('condicoes', []),
                '#f59e0b'
            )


def render_detalhes_processo(processo: Dict[str, Any]):
    """Renderiza painel expansível com detalhes completos de um processo."""
    numero_curto = processo['numero'][:30] + '...' if len(processo['numero']) > 30 else processo['numero']
    titulo = f"{processo['comarca']} - {numero_curto}"
    
    with ui.expansion(titulo, icon='description').classes('w-full mb-4'):
        with ui.column().classes('gap-4 p-4'):
            # Aba: Dados Gerais
            with ui.expansion('Dados Gerais', icon='info').classes('w-full border rounded bg-gray-50 mb-2'):
                with ui.column().classes('gap-3 p-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label('Número:').classes('font-semibold')
                        ui.label(processo['numero']).classes('font-mono text-sm')
                        ui.button(icon='content_copy', size='sm', on_click=lambda n=processo['numero']: copiar_numero_processo(n)).props('flat dense')
                    
                    ui.separator()
                    
                    with ui.row().classes('gap-4'):
                        with ui.column().classes('gap-1'):
                            ui.label('Comarca/Vara:').classes('text-xs text-gray-500')
                            ui.label(f"{processo['comarca']} - {processo['vara']}").classes('text-sm')
                        
                        with ui.column().classes('gap-1'):
                            ui.label('Data da Denúncia:').classes('text-xs text-gray-500')
                            ui.label(processo.get('data_denuncia') or processo.get('data_denuncia_original', '-')).classes('text-sm')
                    
                    if 'promotor' in processo:
                        with ui.column().classes('gap-1'):
                            ui.label('Promotor:').classes('text-xs text-gray-500')
                            ui.label(processo['promotor']).classes('text-sm')
                    elif 'promotor_aditamento' in processo:
                        with ui.column().classes('gap-1'):
                            ui.label('Promotor (aditamento):').classes('text-xs text-gray-500')
                            ui.label(processo['promotor_aditamento']).classes('text-sm')
                    
                    caso = processo.get('caso_erp') or processo.get('casos_erp', [])
                    if isinstance(caso, list):
                        ui.label('Casos ERP:').classes('text-xs text-gray-500')
                        for c in caso:
                            ui.label(c).classes('text-sm text-blue-700')
                    else:
                        with ui.column().classes('gap-1'):
                            ui.label('Caso ERP:').classes('text-xs text-gray-500')
                            ui.label(caso).classes('text-sm text-blue-700')
                    
                    if 'local_fato' in processo:
                        with ui.column().classes('gap-1'):
                            ui.label('Local do Fato:').classes('text-xs text-gray-500')
                            ui.label(processo['local_fato']).classes('text-sm')
            
            # Aba: Crimes Imputados
            with ui.expansion('Crimes Imputados', icon='gavel').classes('w-full border rounded bg-gray-50 mb-2'):
                with ui.column().classes('gap-3 p-4'):
                    for crime in processo.get('crimes', []):
                        with ui.card().classes('p-3 border-l-4').style('border-left-color: #dc2626;'):
                            with ui.row().classes('items-center gap-2 mb-2'):
                                crime_badge(crime['artigo'], crime.get('tem_agravante_53', False))
                                ui.label(crime['nome']).classes('font-semibold text-sm')
                            
                            ui.label(crime.get('descricao', '')).classes('text-sm text-gray-700 mb-2')
                            
                            with ui.row().classes('gap-4 text-xs'):
                                ui.label(f"Pena: {crime['pena_minima_meses']}-{crime['pena_maxima_meses']} meses").classes('text-gray-600')
                                if 'area_ha' in crime:
                                    ui.label(f"Área: {crime['area_ha']} ha").classes('text-orange-600')
                            
                            if crime.get('tem_agravante_53'):
                                ui.label('⚠️ Agravante: Espécies ameaçadas (+1/6 a +1/3)').classes('text-xs text-red-700 font-semibold mt-2')
            
            # Aba: Espécies Afetadas (se houver)
            if 'especies_ameacadas' in processo or 'outras_especies' in processo:
                with ui.expansion('Espécies Afetadas', icon='forest').classes('w-full border rounded bg-gray-50 mb-2'):
                    with ui.column().classes('gap-3 p-4'):
                        if 'especies_ameacadas' in processo:
                            ui.label('Espécies Ameaçadas de Extinção:').classes('font-semibold text-red-700 mb-2')
                            for especie in processo['especies_ameacadas']:
                                nome = especie if isinstance(especie, str) else f"{especie.get('nome_popular')} ({especie.get('nome_cientifico')})"
                                with ui.row().classes('items-center gap-2 ml-4'):
                                    ui.icon('warning', size='16px').classes('text-red-600')
                                    ui.label(nome).classes('text-sm text-red-700 font-semibold')
                        
                        if 'outras_especies' in processo:
                            ui.label('Outras Espécies Nativas:').classes('font-semibold text-gray-700 mt-4 mb-2')
                            with ui.row().classes('gap-2 flex-wrap ml-4'):
                                for especie in processo['outras_especies']:
                                    ui.badge(especie).classes('px-2 py-1').style('background-color: #e5e7eb; color: #374151;')
            
            # Aba: Situação Processual
            with ui.expansion('Situação Processual', icon='timeline').classes('w-full border rounded bg-gray-50 mb-2'):
                with ui.column().classes('gap-3 p-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label('Fase:').classes('font-semibold')
                        ui.label(processo.get('fase', processo.get('status', 'Em andamento'))).classes('text-sm')
                    
                    # Proposta de sursis
                    sursis = processo.get('proposta_sursis', {})
                    if sursis.get('oferecida'):
                        ui.label('Proposta de Sursis:').classes('font-semibold text-green-700 mt-3 mb-2')
                        ui.label(f"Prazo: {sursis['prazo_anos']} anos").classes('text-sm mb-2')
                        ui.label('Condições:').classes('text-xs font-semibold')
                        for cond in sursis.get('condicoes', []):
                            ui.label(f"• {cond}").classes('text-sm ml-4')
                    else:
                        ui.label('Proposta de Sursis: Não oferecida').classes('text-sm text-gray-500 mt-3')
                    
                    # Histórico (para processo 3)
                    if 'historico_processual' in processo:
                        ui.label('Histórico Processual:').classes('font-semibold mt-4 mb-2')
                        for evento in processo['historico_processual']:
                            data = evento.get('data', '-')
                            evt = evento.get('evento', '')
                            ui.label(f"• [{data}] {evt}").classes('text-sm ml-4')
                    
                    # Corréus (para processo 3)
                    if 'correus' in processo:
                        ui.label('Corréus:').classes('font-semibold mt-4 mb-2')
                        for correu in processo['correus']:
                            nome = correu if isinstance(correu, str) else correu.get('nome', '')
                            with ui.badge(nome).classes('px-2 py-1').style('background-color: #ddd6fe; color: #4c1d95;'):
                                pass
                    
                    # Motivo de inclusão (processo 3)
                    if 'motivo_inclusao_carlos' in processo:
                        with ui.card().classes('p-3 mt-4').style('background-color: #fef3c7; border-left: 4px solid #f59e0b;'):
                            ui.label('Motivo da Inclusão:').classes('font-semibold text-yellow-800 mb-1')
                            ui.label(processo['motivo_inclusao_carlos']).classes('text-sm text-yellow-900')


def render_pontos_atencao():
    """Renderiza seção de pontos de atenção."""
    pontos = [
        "Ausência de laudo pericial pode ser tese de absolvição (jurisprudência STJ)",
        "Responsabilidade como arrendatário é reconhecida pelo STJ",
        "ANPP já foi negado em Itaiópolis",
        "Processo 3 tem 9 fatos criminosos",
        "Destruição de APP é crime mais grave",
        "Espécies ameaçadas aumentam pena em 1/6 a 1/3"
    ]
    
    alerta_box('⚠️ Pontos Críticos para a Defesa', pontos, '#dc2626')


def render_impacto_vida():
    """Renderiza seção de impacto na vida."""
    with ui.column().classes('w-full gap-4 mb-6'):
        ui.label('🏠 Consequências Práticas de uma Condenação').classes('text-2xl font-bold text-gray-800 mb-4')
        
        temas = [
            {
                'titulo': 'Efeitos na Liberdade',
                'icon': 'lock',
                'itens': [
                    'Regime de cumprimento (fechado, semiaberto ou aberto)',
                    'Progressão de regime após 1/6 da pena',
                    'Regime domiciliar para maiores de 70 anos',
                    'Prisão preventiva pode ocorrer a qualquer momento'
                ]
            },
            {
                'titulo': 'Efeitos Civis',
                'icon': 'gavel',
                'itens': [
                    'Ficha criminal permanente',
                    'Restrições para viagens internacionais',
                    'Impedimento para portar armas',
                    'Possível perda de direitos políticos'
                ]
            },
            {
                'titulo': 'Efeitos na Empresa',
                'icon': 'business',
                'itens': [
                    'Dificuldades para obtenção de licenças ambientais',
                    'Impedimento em licitações públicas',
                    'Restrições ao crédito bancário',
                    'Impacto na imagem da empresa'
                ]
            },
            {
                'titulo': 'Efeitos na Família',
                'icon': 'family_restroom',
                'itens': [
                    'Processos também envolvem Luciane (corréu)',
                    'Refloresta Imóveis também é acusada',
                    'Risco de bloqueio de bens',
                    'Impacto emocional e financeiro'
                ]
            },
            {
                'titulo': 'Custos Financeiros',
                'icon': 'attach_money',
                'itens': [
                    'Multas ambientais (podem chegar a milhões)',
                    'Custos de reparação ambiental (PRAD)',
                    'Honorários advocatícios',
                    'Possível bloqueio de bens para garantir reparação'
                ]
            }
        ]
        
        for tema in temas:
            with ui.expansion(tema['titulo'], icon=tema['icon']).classes('w-full border rounded bg-gray-50 mb-2'):
                with ui.column().classes('gap-2 p-4'):
                    for item in tema['itens']:
                        ui.label(f"• {item}").classes('text-sm text-gray-700')


def render_proximos_passos():
    """Renderiza seção de próximos passos."""
    with ui.card().classes('w-full p-6 mb-6'):
        ui.label('✅ O Que Fazer Agora').classes('text-2xl font-bold text-gray-800 mb-4')
        
        passos = [
            "Verificar existência de laudos periciais nos autos",
            "Avaliar possibilidade de acordo em algum processo",
            "Discutir estratégia de defesa unificada vs. separada",
            "Levantar custos estimados de reparação ambiental",
            "Verificar prazos processuais correndo",
            "Avaliar planejamento patrimonial preventivo"
        ]
        
        with ui.column().classes('gap-2'):
            for passo in passos:
                with ui.row().classes('items-center gap-3 p-2 hover:bg-gray-50 rounded'):
                    ui.icon('check_box_outline_blank', size='20px').classes('text-gray-400')
                    ui.label(passo).classes('text-sm text-gray-700')


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

@ui.page('/inteligencia/riscos-penais/carlos')
def carlos_page():
    """Página detalhada de análise de riscos penais do Carlos."""
    try:
        if not is_authenticated():
            ui.navigate.to('/login')
            return
        
        with layout(
            '⚖️ Análise de Riscos Penais',
            breadcrumbs=[
                ('Inteligência', '/inteligencia'),
                ('Riscos Penais - Carlos', None)
            ]
        ):
            with ui.column().classes('w-full gap-6 p-6'):
                # Header
                with ui.row().classes('items-center justify-between w-full mb-4'):
                    with ui.column().classes('gap-1'):
                        ui.label(f"Carlos Schmidmeier - CPF: {DADOS_REU['cpf']}").classes('text-gray-600 text-sm')
                    ui.button('Exportar PDF', icon='picture_as_pdf').props('outlined').on('click', lambda: ui.notify('Funcionalidade em desenvolvimento', type='info'))
                
                # Seção 2: Resumo Executivo
                render_resumo_executivo()
                
                # Seção 3: Tabela de Processos
                render_tabela_processos()
                
                # Seção 4: Cenários de Condenação
                render_cenarios_condenacao()
                
                # Seção 5: Cálculo Detalhado
                render_calculo_detalhado()
                
                # Seção 6: Timeline
                render_timeline_prisao()
                
                # Seção 7: Detalhes dos Processos
                ui.label('📂 Detalhamento dos Processos').classes('text-2xl font-bold text-gray-800 mb-4')
                for processo in PROCESSOS:
                    render_detalhes_processo(processo)
                
                # Seção 8: Pontos de Atenção
                render_pontos_atencao()
                
                # Seção 9: Impacto na Vida
                render_impacto_vida()
                
                # Seção 10: Próximos Passos
                render_proximos_passos()
        
    except Exception as e:
        print(f"Erro ao carregar página de Riscos Penais - Carlos: {e}")
        import traceback
        traceback.print_exc()

