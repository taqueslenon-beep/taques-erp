"""
Página de migração/vinculação de Processos → Casos (Visão Geral).

Objetivo: facilitar o vínculo em lote de processos (vg_processos) a um Caso (vg_casos).

Rota: /visao-geral/migracao-processos
"""

from datetime import datetime
from typing import Dict, Any, List

from nicegui import ui

from ..core import layout
from ..auth import is_authenticated
from ..gerenciadores.gerenciador_workspace import definir_workspace
from ..firebase_config import ensure_firebase_initialized

from .processos.database import listar_processos, atualizar_campos_processo
from .casos.database import listar_casos


def _fmt_text(v: Any) -> str:
    return (str(v).strip() if v is not None else '').strip()


@ui.page('/visao-geral/migracao-processos')
def migracao_processos():
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    ensure_firebase_initialized()
    definir_workspace('visao_geral_escritorio')

    with layout('Migração de Processos', breadcrumbs=[
        ('Visão geral do escritório', '/visao-geral/painel'),
        ('Processos', '/visao-geral/processos'),
        ('Migração de Processos', None),
    ]):
        with ui.card().classes('w-full mb-4'):
            ui.label('Migração de Processos → Casos').classes('text-2xl font-bold text-gray-800 mb-2')
            ui.label(
                'Aqui você vincula processos já cadastrados aos seus respectivos Casos. '
                'Selecione um Caso e marque os processos na lista para vincular em lote.'
            ).classes('text-gray-600')

        estado: Dict[str, Any] = {
            'caso_selecionado': None,
            'somente_sem_caso': True,
        }

        # Carrega casos (para dropdown)
        casos = listar_casos()
        casos_opts: Dict[str, str] = {}
        for c in casos:
            cid = _fmt_text(c.get('_id'))
            titulo = _fmt_text(c.get('titulo') or c.get('title') or 'Sem título')
            nucleo = _fmt_text(c.get('nucleo') or '')
            label = titulo
            if nucleo:
                label = f'{titulo} — {nucleo}'
            # Ajuda quando existem títulos iguais
            label = f'{label} ({cid[:6]})' if cid else label
            if cid:
                casos_opts[cid] = label

        # Controles
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('w-full items-center gap-3 flex-wrap'):
                caso_select = ui.select(
                    options=casos_opts,
                    label='Selecione o Caso para vincular',
                    with_input=True,
                ).classes('min-w-[320px] flex-grow').props('outlined dense use-input fill-input')

                somente_sem_caso = ui.checkbox(
                    'Mostrar apenas processos sem Caso',
                    value=True,
                ).classes('mt-1')

        # Tabela de processos
        with ui.card().classes('w-full mb-4'):
            ui.label('Processos (marque e vincule)').classes('text-xl font-bold text-gray-800 mb-3')

            @ui.refreshable
            def render_tabela():
                processos = listar_processos()
                linhas: List[Dict[str, Any]] = []

                for p in processos:
                    pid = _fmt_text(p.get('_id'))
                    titulo = _fmt_text(p.get('titulo') or 'Sem título')
                    numero = _fmt_text(p.get('numero') or '')
                    caso_titulo = _fmt_text(p.get('caso_titulo') or '')
                    caso_id = _fmt_text(p.get('caso_id') or '')
                    clientes = p.get('clientes_nomes') if isinstance(p.get('clientes_nomes'), list) else []
                    clientes_txt = ', '.join([_fmt_text(x) for x in clientes if _fmt_text(x)]) if clientes else ''

                    if somente_sem_caso.value and caso_id:
                        continue

                    linhas.append({
                        '_id': pid,
                        'titulo': titulo,
                        'numero': numero or '-',
                        'caso_atual': caso_titulo or ('—' if not caso_id else f'({caso_id[:6]})'),
                        'clientes': clientes_txt or '—',
                    })

                colunas = [
                    {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'sortable': True},
                    {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left', 'sortable': True},
                    {'name': 'clientes', 'label': 'Clientes', 'field': 'clientes', 'align': 'left'},
                    {'name': 'caso_atual', 'label': 'Caso atual', 'field': 'caso_atual', 'align': 'left'},
                ]

                tabela = ui.table(
                    columns=colunas,
                    rows=linhas,
                    row_key='_id',
                    selection='multiple',
                    pagination={'rowsPerPage': 20},
                ).classes('w-full')

                return tabela

            tabela_ref = {'table': None}

            def _render():
                tabela_ref['table'] = render_tabela()

            _render()

            # Ações
            with ui.row().classes('w-full items-center gap-3 mt-4 flex-wrap'):
                def atualizar_lista():
                    render_tabela.refresh()

                ui.button('Atualizar lista', icon='refresh', on_click=atualizar_lista).props('color=secondary').classes('whitespace-nowrap')

                def vincular_em_lote():
                    caso_id = caso_select.value
                    if not caso_id:
                        ui.notify('Selecione um Caso primeiro.', type='warning')
                        return

                    caso_label = casos_opts.get(caso_id, '')
                    caso_titulo = caso_label.split(' — ')[0].strip() if caso_label else ''
                    if not caso_titulo:
                        # fallback: pega antes do " (xxxxxx)"
                        caso_titulo = caso_label.split(' (')[0].strip() if caso_label else ''

                    tabela = tabela_ref.get('table')
                    if not tabela:
                        ui.notify('Tabela não disponível.', type='negative')
                        return

                    selecionados = tabela.selected_rows or []
                    if not selecionados:
                        ui.notify('Selecione pelo menos 1 processo.', type='warning')
                        return

                    ok = 0
                    erro = 0
                    for row in selecionados:
                        pid = row.get('_id')
                        if not pid:
                            continue
                        sucesso = atualizar_campos_processo(pid, {
                            'caso_id': caso_id,
                            'caso_titulo': caso_titulo,
                        })
                        if sucesso:
                            ok += 1
                        else:
                            erro += 1

                    ui.notify(f'Vinculados: {ok} | Erros: {erro}', type='positive' if erro == 0 else 'warning')
                    render_tabela.refresh()

                ui.button('Vincular processos selecionados ao Caso', icon='link', on_click=vincular_em_lote).props('color=primary').classes('whitespace-nowrap')

        with ui.card().classes('w-full'):
            ui.label('Dica').classes('text-lg font-bold text-gray-800 mb-1')
            ui.label(
                'Se você quiser, eu também posso adicionar um “Importar planilha do Eproc” aqui para criar processos automaticamente '
                'e já abrir essa tela para vincular.'
            ).classes('text-gray-600')


