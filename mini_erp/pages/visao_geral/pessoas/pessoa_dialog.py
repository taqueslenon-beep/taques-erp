"""
Dialog para criar e editar pessoas do workspace Visão Geral.
"""
from typing import Optional, Callable
from nicegui import ui

from .database import criar_pessoa, atualizar_pessoa, listar_pessoas
from .database_grupo import listar_grupos
from .models import (
    TIPO_PESSOA_OPTIONS,
    TIPO_PESSOA_PADRAO,
    formatar_cpf,
    formatar_cnpj,
    extrair_digitos,
    validar_pessoa,
    criar_pessoa_vazia,
)


def abrir_dialog_pessoa(
    pessoa: Optional[dict] = None,
    on_save: Optional[Callable] = None
):
    """
    Abre dialog para criar ou editar uma pessoa.

    Args:
        pessoa: Dados da pessoa para edição (None para criar nova)
        on_save: Callback chamado após salvar com sucesso
    """
    is_edicao = pessoa is not None
    titulo = 'Editar Pessoa' if is_edicao else 'Nova Pessoa'

    # Dados iniciais
    dados = pessoa.copy() if pessoa else criar_pessoa_vazia()

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label(titulo).classes('text-xl font-bold text-gray-800')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round')

        ui.separator().classes('mb-4')

        # Container do formulário
        with ui.column().classes('w-full gap-4'):
            # Tipo de pessoa
            tipo_select = ui.select(
                options=TIPO_PESSOA_OPTIONS,
                value=dados.get('tipo_pessoa', TIPO_PESSOA_PADRAO),
                label='Tipo *'
            ).classes('w-full').props('dense outlined')

            # Nome completo
            nome_input = ui.input(
                label='Nome Completo / Razão Social *',
                value=dados.get('full_name', ''),
                placeholder='Digite o nome completo'
            ).classes('w-full').props('dense outlined')

            # Nome de exibição
            nome_exibicao_input = ui.input(
                label='Nome de Exibição *',
                value=dados.get('nome_exibicao', ''),
                placeholder='Nome para exibição no sistema'
            ).classes('w-full').props('dense outlined')

            # Container para CPF/CNPJ (muda baseado no tipo)
            doc_container = ui.element('div').classes('w-full')

            # CPF Input
            cpf_input = None
            cnpj_input = None

            def criar_campo_cpf():
                nonlocal cpf_input
                with doc_container:
                    cpf_input = ui.input(
                        label='CPF',
                        value=formatar_cpf(dados.get('cpf', '')),
                        placeholder='000.000.000-00'
                    ).classes('w-full').props('dense outlined mask="###.###.###-##"')

            def criar_campo_cnpj():
                nonlocal cnpj_input
                with doc_container:
                    cnpj_input = ui.input(
                        label='CNPJ',
                        value=formatar_cnpj(dados.get('cnpj', '')),
                        placeholder='00.000.000/0000-00'
                    ).classes('w-full').props('dense outlined mask="##.###.###/####-##"')

            def atualizar_campo_documento():
                """Atualiza campo de documento baseado no tipo selecionado."""
                doc_container.clear()
                if tipo_select.value == 'PJ':
                    criar_campo_cnpj()
                else:
                    criar_campo_cpf()

            # Evento de mudança de tipo
            tipo_select.on('update:model-value', lambda: atualizar_campo_documento())

            # Inicializa campo de documento
            atualizar_campo_documento()

            # Email e Telefone (na mesma linha)
            with ui.row().classes('w-full gap-4'):
                email_input = ui.input(
                    label='Email',
                    value=dados.get('email', ''),
                    placeholder='email@exemplo.com'
                ).classes('flex-1').props('dense outlined type=email')

                telefone_input = ui.input(
                    label='Telefone',
                    value=dados.get('telefone', ''),
                    placeholder='(00) 00000-0000'
                ).classes('flex-1').props('dense outlined')

            # Grupo de Relacionamento
            grupos = listar_grupos(apenas_ativos=True)
            opcoes_grupos = {'': 'Sem Grupo'}
            for grupo in grupos:
                opcoes_grupos[grupo._id] = f"{grupo.icone or '📦'} {grupo.nome}"
            
            grupo_select = ui.select(
                options=opcoes_grupos,
                value=dados.get('grupo_id', ''),
                label='Grupo de Relacionamento'
            ).classes('w-full').props('dense outlined')

            # Observações
            observacoes_input = ui.textarea(
                label='Observações',
                value=dados.get('observacoes', ''),
                placeholder='Observações adicionais...'
            ).classes('w-full').props('dense outlined rows=3')

        ui.separator().classes('my-4')

        # Botões de ação
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

            def salvar():
                """Valida e salva os dados da pessoa."""
                # Coleta dados do formulário
                tipo = tipo_select.value

                novos_dados = {
                    'tipo_pessoa': tipo,
                    'full_name': nome_input.value.strip(),
                    'nome_exibicao': nome_exibicao_input.value.strip(),
                    'email': email_input.value.strip(),
                    'telefone': telefone_input.value.strip(),
                    'observacoes': observacoes_input.value.strip(),
                }
                
                # Adiciona grupo de relacionamento
                grupo_id_selecionado = grupo_select.value or ''
                novos_dados['grupo_id'] = grupo_id_selecionado
                
                # Busca nome do grupo se selecionado
                if grupo_id_selecionado:
                    grupo_selecionado = next((g for g in grupos if g._id == grupo_id_selecionado), None)
                    if grupo_selecionado:
                        novos_dados['grupo_nome'] = grupo_selecionado.nome
                    else:
                        novos_dados['grupo_nome'] = ''
                else:
                    novos_dados['grupo_nome'] = ''
                
                # Garante categoria
                novos_dados['categoria'] = 'cliente'

                # Adiciona CPF ou CNPJ baseado no tipo
                if tipo == 'PF' and cpf_input:
                    novos_dados['cpf'] = extrair_digitos(cpf_input.value)
                    novos_dados['cnpj'] = ''
                elif tipo == 'PJ' and cnpj_input:
                    novos_dados['cnpj'] = extrair_digitos(cnpj_input.value)
                    novos_dados['cpf'] = ''

                # Valida dados
                valido, erro = validar_pessoa(novos_dados)
                if not valido:
                    ui.notify(erro, type='negative')
                    return

                # Verifica duplicidade de nome (exceto para edição do mesmo registro)
                pessoas_existentes = listar_pessoas()
                for p in pessoas_existentes:
                    if p.get('full_name', '').lower() == novos_dados['full_name'].lower():
                        if not is_edicao or p.get('_id') != dados.get('_id'):
                            ui.notify('Já existe uma pessoa com este nome.', type='negative')
                            return

                # Salva no Firebase
                try:
                    if is_edicao:
                        pessoa_id = dados.get('_id')
                        sucesso = atualizar_pessoa(pessoa_id, novos_dados)
                        if sucesso:
                            ui.notify('Pessoa atualizada com sucesso!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao atualizar. Tente novamente.', type='negative')
                    else:
                        pessoa_id = criar_pessoa(novos_dados)
                        if pessoa_id:
                            ui.notify('Pessoa cadastrada com sucesso!', type='positive')
                            dialog.close()
                            if on_save:
                                on_save()
                        else:
                            ui.notify('Erro ao salvar. Tente novamente.', type='negative')
                except Exception as e:
                    print(f"Erro ao salvar pessoa: {e}")
                    ui.notify('Erro ao salvar. Verifique os dados.', type='negative')

            ui.button('Salvar', on_click=salvar, icon='save').props('color=primary')

    dialog.open()


def confirmar_exclusao(pessoa: dict, on_confirm: Optional[Callable] = None):
    """
    Exibe dialog de confirmação para exclusão de pessoa.

    Args:
        pessoa: Dados da pessoa a excluir
        on_confirm: Callback chamado após confirmar exclusão
    """
    nome = pessoa.get('nome_exibicao') or pessoa.get('full_name', 'esta pessoa')

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        with ui.column().classes('w-full gap-4'):
            # Header com ícone de alerta
            with ui.row().classes('w-full items-center gap-3'):
                ui.icon('warning', color='negative', size='md')
                ui.label('Confirmar exclusão').classes('text-lg font-bold text-gray-800')

            # Mensagem
            ui.label(f'Deseja realmente excluir "{nome}"?').classes('text-gray-600')
            ui.label('Esta ação não pode ser desfeita.').classes('text-sm text-gray-400')

            # Botões
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')

                def confirmar():
                    dialog.close()
                    if on_confirm:
                        on_confirm()

                ui.button('Excluir', on_click=confirmar, icon='delete').props('color=negative')

    dialog.open()
