"""
Dialogs e modais para CRUD de Oportunidades.
Integração com Leads e formulários completos.
"""
from typing import Optional, Callable, Dict, Any
from nicegui import ui
from mini_erp.core import get_leads_list
from .novos_negocios_services import (
    save_oportunidade,
    delete_oportunidade,
    buscar_oportunidade_por_id
)


# Opções de origem
ORIGEM_OPTIONS = ['Indicação', 'Relacionamento anterior', 'Internet', 'Recompra', 'DF Projetos']

# DEPRECATED: Usuários agora são buscados dinamicamente do Firebase Auth
# Mantido apenas para referência/compatibilidade
# USUARIOS_INTERNOS = ['Lenon', 'Berna', 'Douglas']


def formatar_valor_input(valor: str) -> float:
    """
    Converte string de valor formatado (R$ 1.234,56) para float.
    Remove formatação de moeda brasileira.
    """
    if not valor:
        return 0.0
    # Remove R$, espaços, pontos (milhares) e substitui vírgula por ponto
    valor_limpo = valor.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(valor_limpo)
    except:
        return 0.0


def formatar_valor_exibicao(valor: Optional[float]) -> str:
    """
    Formata valor float para exibição em input (R$ 1.234,56).
    Formato brasileiro de moeda.
    """
    if not valor or valor == 0:
        return ''
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def criar_dialog_oportunidade(
    on_save: Optional[Callable] = None,
    oportunidade_id: Optional[str] = None
) -> ui.dialog:
    """
    Cria dialog para criar ou editar oportunidade.
    
    Args:
        on_save: Função callback chamada após salvar
        oportunidade_id: ID da oportunidade para edição (None para criar)
    
    Returns:
        Dialog configurado
    """
    is_editing = oportunidade_id is not None
    titulo_dialog = 'Editar Oportunidade' if is_editing else 'Nova Oportunidade'
    
    # Busca leads
    leads = get_leads_list()
    leads_options = {'': 'Sem lead vinculado'}
    for lead in leads:
        lead_id = lead.get('_id', '')
        nome = lead.get('nome', 'Sem nome')
        nome_exibicao = lead.get('nome_exibicao', '')
        display = f"{nome}" + (f" ({nome_exibicao})" if nome_exibicao else "")
        leads_options[lead_id] = display
    
    # Carrega dados se for edição
    dados_iniciais = {}
    if is_editing:
        oportunidade = buscar_oportunidade_por_id(oportunidade_id)
        if oportunidade:
            dados_iniciais = oportunidade
        else:
            # Se não encontrou, cria dialog vazio mas avisa
            dados_iniciais = {}
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg p-6'):
        ui.label(titulo_dialog).classes('text-xl font-bold mb-4 text-gray-800')
        
        # Campos do formulário
        with ui.column().classes('w-full gap-4'):
            # Lead (dropdown)
            lead_select = ui.select(
                options=leads_options,
                label='Lead',
                value=dados_iniciais.get('lead_id', '')
            ).classes('w-full').props('outlined dense')
            
            # Nome da Oportunidade (obrigatório)
            nome_input = ui.input(
                label='Nome da Oportunidade *',
                placeholder='Digite o nome da oportunidade',
                value=dados_iniciais.get('nome', '')
            ).classes('w-full').props('outlined dense')
            
            # Função para preencher origem automaticamente quando selecionar lead (opcional)
            # Nome da oportunidade permanece independente - usuário digita manualmente
            def on_lead_selected():
                lead_id = lead_select.value
                if lead_id and lead_id in leads_options:
                    # Busca o lead selecionado
                    lead_selecionado = next((l for l in leads if l.get('_id') == lead_id), None)
                    if lead_selecionado:
                        # Preenche origem se o lead tiver (campo independente do nome)
                        origem_lead = lead_selecionado.get('origem', '')
                        if origem_lead and origem_lead in ORIGEM_OPTIONS:
                            origem_select.value = origem_lead
                            origem_select.update()
            
            lead_select.on('update:model-value', lambda: on_lead_selected())
            
            # Valor Estimado
            valor_input = ui.input(
                label='Valor Estimado (R$)',
                placeholder='Ex: 50000,00',
                value=formatar_valor_exibicao(dados_iniciais.get('valor_estimado'))
            ).classes('w-full').props('outlined dense')
            
            # Origem
            origem_select = ui.select(
                options=ORIGEM_OPTIONS,
                label='Origem',
                value=dados_iniciais.get('origem', '')
            ).classes('w-full').props('outlined dense')
            
            # Responsável
            responsavel_input = ui.input(
                label='Responsável',
                placeholder='Nome do responsável',
                value=dados_iniciais.get('responsavel', '')
            ).classes('w-full').props('outlined dense')
            
            # Observações
            observacoes_input = ui.textarea(
                label='Observações',
                placeholder='Observações sobre a oportunidade',
                value=dados_iniciais.get('observacoes', '')
            ).classes('w-full').props('outlined dense rows=3')
        
        # Botões
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            
            def salvar():
                # Validação
                if not nome_input.value or not nome_input.value.strip():
                    ui.notify('Nome da oportunidade é obrigatório!', type='warning')
                    return
                
                # Prepara dados
                dados = {
                    'nome': nome_input.value.strip(),
                    'lead_id': lead_select.value if lead_select.value else None,
                    'valor_estimado': formatar_valor_input(valor_input.value),
                    'origem': origem_select.value if origem_select.value else '',
                    'responsavel': responsavel_input.value.strip() if responsavel_input.value else '',
                    'observacoes': observacoes_input.value.strip() if observacoes_input.value else '',
                }
                
                # Se estiver editando, mantém status e resultado existentes
                if is_editing:
                    dados['status'] = dados_iniciais.get('status', 'agir')
                    if 'resultado' in dados_iniciais:
                        dados['resultado'] = dados_iniciais.get('resultado')
                else:
                    # Nova oportunidade sempre começa em 'agir'
                    dados['status'] = 'agir'
                
                try:
                    if is_editing:
                        save_oportunidade(dados, oportunidade_id)
                        ui.notify('Oportunidade atualizada com sucesso!', type='positive')
                    else:
                        save_oportunidade(dados)
                        ui.notify('Oportunidade criada com sucesso!', type='positive')
                    
                    dialog.close()
                    if on_save:
                        on_save()
                except Exception as e:
                    ui.notify(f'Erro ao salvar oportunidade: {str(e)}', type='negative')
            
            ui.button('Salvar', icon='save', on_click=salvar).props('color=primary')
    
    return dialog


def criar_dialog_excluir_oportunidade(
    oportunidade: Dict[str, Any],
    on_delete: Optional[Callable] = None
) -> ui.dialog:
    """
    Cria dialog de confirmação para excluir oportunidade.
    
    Args:
        oportunidade: Dicionário com dados da oportunidade
        on_delete: Função callback chamada após excluir
    
    Returns:
        Dialog configurado
    """
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        ui.label('Excluir Oportunidade').classes('text-xl font-bold mb-4 text-red-600')
        
        ui.label('Deseja realmente excluir esta oportunidade?').classes('text-gray-700 mb-2')
        ui.label(f'"{oportunidade.get("nome", "Sem nome")}"').classes('font-semibold text-gray-800 mb-4')
        ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-red-500 mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
            
            def excluir():
                try:
                    oportunidade_id = oportunidade.get('_id')
                    if oportunidade_id:
                        sucesso = delete_oportunidade(oportunidade_id)
                        if sucesso:
                            ui.notify('Oportunidade excluída com sucesso!', type='positive')
                            dialog.close()
                            if on_delete:
                                on_delete()
                        else:
                            ui.notify('Erro ao excluir oportunidade', type='negative')
                except Exception as e:
                    ui.notify(f'Erro ao excluir: {str(e)}', type='negative')
            
            ui.button('Excluir', icon='delete', on_click=excluir).props('color=negative')
    
    return dialog


def criar_dialog_resultado_oportunidade(
    oportunidade_id: str,
    on_save: Optional[Callable] = None
) -> ui.dialog:
    """
    Cria dialog para definir resultado quando move para Concluído.
    
    Args:
        oportunidade_id: ID da oportunidade
        on_save: Função callback chamada após salvar
    
    Returns:
        Dialog configurado
    """
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md p-6'):
        ui.label('Resultado da Oportunidade').classes('text-xl font-bold mb-4 text-gray-800')
        
        ui.label('Como foi o resultado desta oportunidade?').classes('text-gray-700 mb-4')
        
        def definir_resultado(resultado: str):
            try:
                # Busca dados existentes da oportunidade
                oportunidade = buscar_oportunidade_por_id(oportunidade_id)
                if not oportunidade:
                    ui.notify('Oportunidade não encontrada', type='negative')
                    return
                
                # Atualiza apenas o resultado, mantendo os outros campos
                dados = {**oportunidade, 'resultado': resultado}
                save_oportunidade(dados, oportunidade_id)
                
                mensagem = 'Negócio marcado como ganho!' if resultado == 'ganho' else 'Negócio marcado como perdido.'
                tipo = 'positive' if resultado == 'ganho' else 'warning'
                ui.notify(mensagem, type=tipo)
                
                dialog.close()
                if on_save:
                    on_save()
            except Exception as e:
                ui.notify(f'Erro ao salvar resultado: {str(e)}', type='negative')
        
        with ui.column().classes('w-full gap-3'):
            # Botão Ganho
            ui.button(
                '✅ Negócio Ganho',
                icon='check_circle',
                on_click=lambda: definir_resultado('ganho')
            ).classes('w-full py-3').style('background-color: #22C55E; color: white; font-weight: bold;')
            
            # Botão Perdido
            ui.button(
                '❌ Negócio Perdido',
                icon='cancel',
                on_click=lambda: definir_resultado('perdido')
            ).classes('w-full py-3').style('background-color: #EF4444; color: white; font-weight: bold;')
        
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Cancelar', on_click=dialog.close).props('flat')
    
    return dialog

