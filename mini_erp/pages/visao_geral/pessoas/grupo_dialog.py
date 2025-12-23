"""
Dialog para criar e editar grupos de relacionamento.
"""
from typing import Optional, Callable
from nicegui import ui
from .database_grupo import criar_grupo, atualizar_grupo, obter_grupo
from .models_grupo import GrupoRelacionamento


def abrir_dialog_grupo(
    grupo: Optional[GrupoRelacionamento] = None,
    on_save: Optional[Callable] = None
):
    """
    Abre dialog para criar ou editar um grupo de relacionamento.

    Args:
        grupo: Instância de GrupoRelacionamento para edição (None para criar novo)
        on_save: Callback chamado após salvar com sucesso
    """
    is_edicao = grupo is not None
    titulo = 'Editar Grupo' if is_edicao else 'Novo Grupo'

    # Dados iniciais
    if grupo:
        dados_iniciais = {
            'nome': grupo.nome,
            'descricao': grupo.descricao,
            'icone': grupo.icone,
            'cor': grupo.cor,
            'ativo': grupo.ativo,
        }
    else:
        dados_iniciais = {
            'nome': '',
            'descricao': '',
            'icone': '',
            'cor': '#4CAF50',
            'ativo': True,
        }

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label(titulo).classes('text-xl font-bold text-gray-800')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round')

        ui.separator().classes('mb-4')

        # Container do formulário
        with ui.column().classes('w-full gap-4'):
            # Nome (obrigatório)
            nome_input = ui.input(
                label='Nome do Grupo *',
                value=dados_iniciais.get('nome', ''),
                placeholder='Ex: Schmidmeier'
            ).classes('w-full').props('dense outlined')

            # Descrição (opcional)
            descricao_input = ui.textarea(
                label='Descrição',
                value=dados_iniciais.get('descricao', ''),
                placeholder='Descrição opcional do grupo'
            ).classes('w-full').props('dense outlined rows=3')

            # Ícone (emoji)
            with ui.row().classes('w-full items-end gap-2'):
                icone_input = ui.input(
                    label='Ícone (Emoji)',
                    value=dados_iniciais.get('icone', ''),
                    placeholder='🇩🇪'
                ).classes('flex-1').props('dense outlined')
                
                # Preview do ícone
                icone_preview = ui.label(dados_iniciais.get('icone', '') or '📁').classes('text-2xl mb-2')
                
                def atualizar_preview():
                    """Atualiza preview do ícone."""
                    icone = icone_input.value or '📁'
                    icone_preview.text = icone
                
                icone_input.on('update:model-value', lambda: atualizar_preview())

            # Cor
            with ui.row().classes('w-full items-end gap-2'):
                cor_input = ui.input(
                    label='Cor (Hexadecimal)',
                    value=dados_iniciais.get('cor', '#4CAF50'),
                    placeholder='#4CAF50'
                ).classes('flex-1').props('dense outlined')
                
                # Preview da cor
                cor_preview = ui.element('div').classes('w-12 h-12 rounded border-2 border-gray-300')
                cor_preview.style(f'background-color: {dados_iniciais.get("cor", "#4CAF50")}')
                
                def atualizar_preview_cor():
                    """Atualiza preview da cor."""
                    cor = cor_input.value or '#4CAF50'
                    if not cor.startswith('#'):
                        cor = '#' + cor
                    cor_preview.style(f'background-color: {cor}')
                
                cor_input.on('update:model-value', lambda: atualizar_preview_cor())

            # Status ativo (apenas na edição)
            if is_edicao:
                ativo_checkbox = ui.checkbox(
                    'Grupo ativo',
                    value=dados_iniciais.get('ativo', True)
                ).classes('w-full')

        ui.separator().classes('my-4')

        # Botões de ação
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', icon='close', on_click=dialog.close).props('flat')
            
            def salvar():
                """Salva o grupo."""
                # Validação
                nome = nome_input.value.strip()
                if not nome:
                    ui.notify('Nome do grupo é obrigatório!', type='warning')
                    return
                
                if len(nome) < 2:
                    ui.notify('Nome deve ter pelo menos 2 caracteres!', type='warning')
                    return
                
                # Validação de cor
                cor = cor_input.value.strip()
                if cor and not cor.startswith('#'):
                    cor = '#' + cor
                
                if cor and len(cor) != 7:
                    ui.notify('Cor deve estar no formato hexadecimal (#RRGGBB)!', type='warning')
                    return
                
                try:
                    if is_edicao:
                        # Atualiza grupo existente
                        dados_atualizacao = {
                            'nome': nome,
                            'descricao': descricao_input.value.strip(),
                            'icone': icone_input.value.strip(),
                            'cor': cor or '#4CAF50',
                        }
                        
                        if 'ativo' in locals():
                            dados_atualizacao['ativo'] = ativo_checkbox.value
                        
                        if atualizar_grupo(grupo._id, dados_atualizacao):
                            ui.notify(f'Grupo "{nome}" atualizado com sucesso!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao atualizar grupo. Tente novamente.', type='negative')
                    else:
                        # Cria novo grupo
                        novo_grupo = GrupoRelacionamento(
                            nome=nome,
                            descricao=descricao_input.value.strip(),
                            icone=icone_input.value.strip(),
                            cor=cor or '#4CAF50',
                            ativo=True,
                        )
                        
                        grupo_id = criar_grupo(novo_grupo)
                        if grupo_id:
                            ui.notify(f'Grupo "{nome}" criado com sucesso!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao criar grupo. Tente novamente.', type='negative')
                except Exception as e:
                    print(f"Erro ao salvar grupo: {e}")
                    import traceback
                    traceback.print_exc()
                    ui.notify('Erro inesperado ao salvar. Tente novamente.', type='negative')
            
            ui.button('Salvar', icon='save', on_click=salvar).props('color=primary')

    dialog.open()











