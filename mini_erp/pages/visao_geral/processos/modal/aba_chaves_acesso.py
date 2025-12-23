"""
Aba de Chaves e Acesso do modal de processo (Visão Geral).
Gerencia chaves de acesso do E-PROC para clientes e terceiros autorizados.
"""
from nicegui import ui
from typing import Dict, Any
from datetime import datetime
from mini_erp.core import format_date_br
from mini_erp.auth import get_current_user
from mini_erp.storage import obter_display_name


def render_aba_chaves_acesso(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza a aba de Chaves e Acesso do modal.
    
    Args:
        state: Estado do modal
        
    Returns:
        Dicionário com referências aos componentes criados
    """
    # Dialog para chave de acesso
    with ui.dialog() as chave_dialog, ui.card().classes('p-4 w-96'):
        chave_title_label = ui.label('Nova Chave de Acesso').classes('text-lg font-bold mb-2')
        chave_input = ui.input('Chave de acesso').classes('w-full').props('dense outlined')
        chave_desc = ui.textarea('Descrição (opcional)').classes('w-full').props('dense outlined rows=2')
        
        chave_idx_ref = {'val': None}
        
        def salvar_chave_local():
            """Salva chave de acesso no estado local."""
            chave_valor = (chave_input.value or '').strip()
            
            # Validações
            if not chave_valor:
                ui.notify('A chave não pode estar vazia.', type='negative')
                return
            
            # Verifica duplicatas
            chaves_existentes = state.get('chaves_acesso', [])
            chave_duplicada = False
            
            if chave_idx_ref['val'] is not None:
                # Modo edição: verifica duplicatas excluindo a chave atual
                for idx, chave_existente in enumerate(chaves_existentes):
                    if idx != chave_idx_ref['val']:
                        if chave_existente.get('chave', '').strip().lower() == chave_valor.lower():
                            chave_duplicada = True
                            break
            else:
                # Modo criação: verifica todas as chaves
                for chave_existente in chaves_existentes:
                    if chave_existente.get('chave', '').strip().lower() == chave_valor.lower():
                        chave_duplicada = True
                        break
            
            if chave_duplicada:
                ui.notify('Chave já cadastrada neste processo.', type='negative')
                return
            
            # Obtém usuário atual
            usuario_atual = get_current_user()
            usuario_uid = usuario_atual.get('uid', '') if usuario_atual else ''
            
            # Obtém nome de exibição do usuário
            usuario_nome = 'Usuário'
            if usuario_uid:
                try:
                    usuario_nome = obter_display_name(usuario_uid)
                    if usuario_nome == 'Usuário' and usuario_atual:
                        # Fallback: usa email se display_name não disponível
                        email = usuario_atual.get('email', '')
                        if email:
                            usuario_nome = email.split('@')[0]
                except Exception:
                    usuario_nome = 'Usuário'
            
            # Cria dados da chave
            dados_chave = {
                'chave': chave_valor,
                'descricao': (chave_desc.value or '').strip(),
                'data_criacao': datetime.now().isoformat(),
                'criado_por': usuario_uid,
                'criado_por_nome': usuario_nome,
                'ativa': True  # Por padrão, nova chave é ativa
            }
            
            # Atualiza ou adiciona chave
            if chave_idx_ref['val'] is not None:
                # Preserva campos originais ao editar
                chave_original = state['chaves_acesso'][chave_idx_ref['val']]
                dados_chave['data_criacao'] = chave_original.get('data_criacao', dados_chave['data_criacao'])
                dados_chave['criado_por'] = chave_original.get('criado_por', dados_chave['criado_por'])
                dados_chave['criado_por_nome'] = chave_original.get('criado_por_nome', dados_chave['criado_por_nome'])
                dados_chave['ativa'] = chave_original.get('ativa', True)
                state['chaves_acesso'][chave_idx_ref['val']] = dados_chave
            else:
                state['chaves_acesso'].append(dados_chave)
            
            chave_dialog.close()
            render_chaves.refresh()
            ui.notify('Chave adicionada com sucesso', type='positive')
        
        with ui.row().classes('w-full justify-end gap-2 mt-2'):
            ui.button('Cancelar', on_click=chave_dialog.close).props('flat')
            chave_save_btn = ui.button('Salvar', on_click=salvar_chave_local).props('color=primary')
        
        def abrir_dialog_chave(idx=None):
            """Abre dialog para adicionar ou editar chave."""
            chave_idx_ref['val'] = idx
            if idx is not None:
                # Modo edição
                chave_data = state['chaves_acesso'][idx]
                chave_title_label.text = 'Editar Chave de Acesso'
                chave_save_btn.text = 'Salvar'
                chave_input.value = chave_data.get('chave', '')
                chave_desc.value = chave_data.get('descricao', '')
            else:
                # Modo criação
                chave_title_label.text = 'Nova Chave de Acesso'
                chave_save_btn.text = 'Salvar'
                chave_input.value = ''
                chave_desc.value = ''
            chave_dialog.open()
    
    # Botão para adicionar nova chave
    ui.button('+ Nova Chave', icon='vpn_key', on_click=lambda: abrir_dialog_chave(None)).props('flat dense color=primary')
    
    @ui.refreshable
    def render_chaves():
        """Renderiza lista de chaves de acesso."""
        chaves = state.get('chaves_acesso', [])
        
        if not chaves:
            ui.label('Nenhuma chave de acesso cadastrada').classes('text-gray-400 italic text-sm mt-4')
            return
        
        for i, chave_data in enumerate(chaves):
            with ui.card().classes('w-full p-3 mb-2'):
                with ui.row().classes('w-full justify-between items-start'):
                    with ui.column().classes('gap-1 flex-grow'):
                        # Chave com opção de copiar
                        with ui.row().classes('items-center gap-2'):
                            chave_valor = chave_data.get('chave', '-')
                            ui.label(chave_valor).classes('font-mono font-medium text-sm')
                            
                            # Botão copiar
                            def copiar_chave(valor=chave_valor):
                                """Copia chave para área de transferência."""
                                valor_escaped = str(valor).replace("'", "\\'")
                                ui.run_javascript(f'''
                                    navigator.clipboard.writeText('{valor_escaped}').then(() => {{
                                    }}).catch(err => {{
                                        console.error('Erro ao copiar:', err);
                                    }});
                                ''')
                                ui.notify('Chave copiada!', type='positive', timeout=1500)
                            
                            ui.button(
                                icon='content_copy',
                                on_click=copiar_chave
                            ).props('flat dense size=sm').tooltip('Copiar chave')
                        
                        # Descrição
                        if chave_data.get('descricao'):
                            ui.label(chave_data.get('descricao')).classes('text-xs text-gray-600 mt-1')
                        
                        # Info de criação
                        with ui.row().classes('items-center gap-2 mt-1'):
                            data_criacao = chave_data.get('data_criacao', '')
                            if data_criacao:
                                try:
                                    # Tenta parsear ISO format
                                    dt = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
                                    data_formatada = format_date_br(dt.strftime('%Y-%m-%d'))
                                except Exception:
                                    data_formatada = data_criacao
                            else:
                                data_formatada = '-'
                            
                            criado_por = chave_data.get('criado_por_nome', 'Usuário')
                            ui.label(f'Criada em {data_formatada} por {criado_por}').classes('text-xs text-gray-500')
                        
                        # Badge de status (Ativa/Inativa)
                        ativa = chave_data.get('ativa', True)
                        if ativa:
                            ui.badge('Ativa', color='positive').props('dense')
                        else:
                            ui.badge('Inativa', color='grey').props('dense')
                    
                    # Ações
                    with ui.row().classes('gap-1'):
                        # Toggle ativar/desativar
                        def toggle_ativa(idx=i):
                            """Alterna status ativa/inativa da chave."""
                            chaves_lista = state.get('chaves_acesso', [])
                            if 0 <= idx < len(chaves_lista):
                                chaves_lista[idx]['ativa'] = not chaves_lista[idx].get('ativa', True)
                                render_chaves.refresh()
                                status = 'ativada' if chaves_lista[idx]['ativa'] else 'desativada'
                                ui.notify(f'Chave {status}', type='info', timeout=1500)
                        
                        icon_toggle = 'check_circle' if ativa else 'cancel'
                        color_toggle = 'positive' if ativa else 'grey'
                        ui.button(
                            icon=icon_toggle,
                            on_click=toggle_ativa
                        ).props('flat dense size=sm').props(f'color={color_toggle}').tooltip('Ativar/Desativar')
                        
                        # Botão editar
                        ui.button(
                            icon='edit',
                            on_click=lambda idx=i: abrir_dialog_chave(idx)
                        ).props('flat dense size=sm color=primary').tooltip('Editar')
                        
                        # Botão excluir
                        def excluir_chave(idx=i):
                            """Exclui chave com confirmação."""
                            chaves_lista = state.get('chaves_acesso', [])
                            if 0 <= idx < len(chaves_lista):
                                chave_valor = chaves_lista[idx].get('chave', 'Chave')
                                
                                with ui.dialog() as confirm_dialog, ui.card().classes('p-4'):
                                    ui.label('Confirmar Exclusão').classes('text-lg font-bold mb-2')
                                    ui.label(f'Tem certeza que deseja excluir esta chave?').classes('text-gray-600 mb-2')
                                    ui.label(f'Chave: {chave_valor}').classes('text-sm text-gray-500 font-mono mb-4')
                                    
                                    with ui.row().classes('w-full justify-end gap-2'):
                                        ui.button('Cancelar', on_click=confirm_dialog.close).props('flat')
                                        
                                        def confirmar_exclusao():
                                            chaves_lista.pop(idx)
                                            render_chaves.refresh()
                                            confirm_dialog.close()
                                            ui.notify('Chave excluída', type='info', timeout=1500)
                                        
                                        ui.button('Excluir', on_click=confirmar_exclusao).props('color=negative')
                                
                                confirm_dialog.open()
                        
                        ui.button(
                            icon='delete',
                            on_click=excluir_chave
                        ).props('flat dense size=sm color=red').tooltip('Excluir')
    
    render_chaves()
    
    return {
        'render_chaves': render_chaves,
    }


