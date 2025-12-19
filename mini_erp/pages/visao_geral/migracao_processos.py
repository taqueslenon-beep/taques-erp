"""
Página de migração/vinculação de Processos → Casos (Visão Geral).

Dados do Eproc já carregados automaticamente (106 processos).

Rota: /visao-geral/migracao-processos
"""

from datetime import datetime
from typing import Dict, Any, List

from nicegui import ui

import re
import unicodedata
import difflib

from ...core import layout
from ...auth import is_authenticated
from ...gerenciadores.gerenciador_workspace import definir_workspace
from ...firebase_config import ensure_firebase_initialized
from ...firebase_config import get_auth
from ...storage import obter_display_name

from .processos.database import listar_processos, atualizar_campos_processo, buscar_processo_por_numero, criar_processo
from .casos.database import listar_casos
from .pessoas.database import listar_pessoas, listar_envolvidos, listar_parceiros
from .dados_processos_eproc import PROCESSOS_EPROC_2025


def _fmt_text(v: Any) -> str:
    return (str(v).strip() if v is not None else '').strip()


def _norm(s: str) -> str:
    s = _fmt_text(s).lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join([c for c in s if not unicodedata.combining(c)])
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _split_names(raw: Any) -> List[str]:
    """Divide autores/réus em lista de nomes."""
    text = _fmt_text(raw)
    if not text:
        return []
    parts = re.split(r'[;\n]| \| |, (?=[A-ZÁÉÍÓÚÃÕÇ])', text)
    cleaned = []
    for p in parts:
        p = _fmt_text(p)
        if p:
            cleaned.append(p)
    seen = set()
    out = []
    for p in cleaned:
        key = _norm(p)
        if key and key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _parse_date_to_ddmmyyyy(raw: Any) -> str:
    """Converte para DD/MM/AAAA."""
    v = raw
    if v is None or v == '':
        return ''
    try:
        if hasattr(v, 'strftime'):
            return v.strftime('%d/%m/%Y')
    except Exception:
        pass
    s = _fmt_text(v)
    if not s:
        return ''
    # YYYY-MM-DD HH:MM:SS -> DD/MM/YYYY
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        return f'{m.group(3)}/{m.group(2)}/{m.group(1)}'
    # DD/MM/YYYY
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', s)
    if m:
        return f'{m.group(1)}/{m.group(2)}/{m.group(3)}'
    return s


def _uid_lenon() -> str:
    """Busca UID do Firebase Auth cujo nome de exibição contenha 'lenon'."""
    try:
        auth_instance = get_auth()
        page = auth_instance.list_users()
        while page:
            for user in page.users:
                if user.disabled:
                    continue
                try:
                    display_name = obter_display_name(user.uid)
                    if display_name == "Usuário":
                        display_name = user.email.split('@')[0] if user.email else ''
                except Exception:
                    display_name = user.email.split('@')[0] if user.email else ''
                if 'lenon' in _norm(display_name):
                    return user.uid
            try:
                page = page.get_next_page()
            except StopIteration:
                break
        return ''
    except Exception as e:
        print(f"[MIGRACAO_PROCESSOS] Erro ao buscar UID do Lenon: {e}")
        return ''


def _melhor_match(nome: str, candidatos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Retorna melhor candidato por similaridade (difflib)."""
    alvo = _norm(nome)
    if not alvo:
        return {}
    best = None
    best_score = 0.0
    for c in candidatos:
        dn = _fmt_text(c.get('_display_name'))
        score = difflib.SequenceMatcher(None, alvo, _norm(dn)).ratio()
        if score > best_score:
            best_score = score
            best = c
    if best and best_score >= 0.78:
        return {'id': best.get('_id', ''), 'nome': best.get('_display_name', ''), 'score': best_score}
    return {}


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
                'Dados do relatório Eproc já carregados (106 processos). '
                'Selecione os processos para criar/atualizar e vincular aos Casos.'
            ).classes('text-gray-600')

        # Defaults
        default_sistema = 'eproc - TJSC - 1ª instância'
        default_responsavel_nome = 'Lenon'
        default_nucleo = 'Ambiental'

        # Carrega bases para matching
        pessoas = listar_pessoas()
        envolvidos = listar_envolvidos()
        parceiros = listar_parceiros()
        
        candidatos_autores = []
        for p in pessoas:
            dn = _fmt_text(p.get('nome_exibicao') or p.get('nome_completo') or p.get('full_name') or p.get('name') or '')
            if dn:
                candidatos_autores.append({'_id': p.get('_id', ''), '_display_name': dn})
        
        candidatos_reus = []
        for x in (envolvidos + parceiros):
            dn = _fmt_text(x.get('nome_exibicao') or x.get('nome_completo') or x.get('full_name') or x.get('name') or '')
            if dn:
                candidatos_reus.append({'_id': x.get('_id', ''), '_display_name': dn})

        lenon_uid = _uid_lenon()

        # Processos do Eproc (já carregados)
        with ui.card().classes('w-full mb-4'):
            ui.label('1) Processos do Eproc (pré-carregados)').classes('text-xl font-bold text-gray-800 mb-2')
            ui.label(f'Total: {len(PROCESSOS_EPROC_2025)} processos').classes('text-gray-600 mb-3')

            sobrescrever = ui.checkbox('Sobrescrever campos existentes do processo', value=False)

            # Monta linhas de preview
            rows_preview = []
            for proc in PROCESSOS_EPROC_2025:
                numero = _fmt_text(proc.get('numero'))
                if not numero:
                    continue
                
                classe = _fmt_text(proc.get('classe'))
                assunto = _fmt_text(proc.get('assunto'))
                titulo = ' - '.join([x for x in [classe, assunto] if x]) or f'Processo {numero}'
                
                data_dist = _fmt_text(proc.get('data_distribuicao'))
                data_abertura = _parse_date_to_ddmmyyyy(data_dist)
                
                autores_raw = _fmt_text(proc.get('autores'))
                reus_raw = _fmt_text(proc.get('reus'))
                localidade = _fmt_text(proc.get('localidade'))
                
                autores_list = _split_names(autores_raw)
                reus_list = _split_names(reus_raw)
                
                sug_autor = _melhor_match(autores_list[0], candidatos_autores) if autores_list else {}
                sug_reu = _melhor_match(reus_list[0], candidatos_reus) if reus_list else {}
                
                # Detecta núcleo pelo assunto/classe
                nucleo_auto = default_nucleo
                texto_check = _norm(classe + ' ' + assunto)
                if any(x in texto_check for x in ['ambiental', 'flora', 'degradacao', 'desmatamento', 'poluicao', 'app', 'area de preservacao']):
                    nucleo_auto = 'Ambiental'
                elif any(x in texto_check for x in ['cobranca', 'execucao fiscal', 'divida']):
                    nucleo_auto = 'Cobranças'
                else:
                    nucleo_auto = 'Generalista'
                
                rows_preview.append({
                    '_key': numero,
                    'numero': numero,
                    'titulo': titulo[:80] + '...' if len(titulo) > 80 else titulo,
                    'titulo_full': titulo,
                    'data_abertura': data_abertura or '—',
                    'localidade': localidade or '—',
                    'nucleo': nucleo_auto,
                    'autor': autores_list[0][:40] + '...' if autores_list and len(autores_list[0]) > 40 else (autores_list[0] if autores_list else '—'),
                    'autor_full': autores_list[0] if autores_list else '',
                    'sug_autor': sug_autor.get('nome', '—') if sug_autor else '—',
                    'reu': reus_list[0][:40] + '...' if reus_list and len(reus_list[0]) > 40 else (reus_list[0] if reus_list else '—'),
                    'reu_full': reus_list[0] if reus_list else '',
                    'sug_reu': sug_reu.get('nome', '—') if sug_reu else '—',
                    'autores_raw': autores_raw,
                    'reus_raw': reus_raw,
                })

            tabela_imp = ui.table(
                columns=[
                    {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left', 'sortable': True},
                    {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left'},
                    {'name': 'data_abertura', 'label': 'Data', 'field': 'data_abertura', 'align': 'left'},
                    {'name': 'localidade', 'label': 'Localidade', 'field': 'localidade', 'align': 'left'},
                    {'name': 'nucleo', 'label': 'Núcleo', 'field': 'nucleo', 'align': 'left'},
                    {'name': 'autor', 'label': 'Autor (1º)', 'field': 'autor', 'align': 'left'},
                    {'name': 'sug_autor', 'label': 'Sug. autor', 'field': 'sug_autor', 'align': 'left'},
                    {'name': 'reu', 'label': 'Réu (1º)', 'field': 'reu', 'align': 'left'},
                    {'name': 'sug_reu', 'label': 'Sug. réu', 'field': 'sug_reu', 'align': 'left'},
                ],
                rows=rows_preview,
                row_key='_key',
                selection='multiple',
                pagination={'rowsPerPage': 15},
            ).classes('w-full')

            def _importar_selecionados():
                selecionados = tabela_imp.selected_rows or []
                if not selecionados:
                    ui.notify('Selecione ao menos 1 processo.', type='warning')
                    return

                ok = 0
                atualizados = 0
                erros = 0

                for item in selecionados:
                    numero = item.get('numero', '')
                    titulo = item.get('titulo_full') or item.get('titulo') or f'Processo {numero}'
                    data_abertura = item.get('data_abertura', '')
                    if data_abertura == '—':
                        data_abertura = ''
                    nucleo_val = item.get('nucleo') or default_nucleo
                    autores_raw = item.get('autores_raw', '')
                    reus_raw = item.get('reus_raw', '')

                    autores_list = _split_names(autores_raw)
                    reus_list = _split_names(reus_raw)

                    # Monta clientes (autores) com match
                    clientes = []
                    clientes_nomes = []
                    for nome in autores_list:
                        m = _melhor_match(nome, candidatos_autores)
                        if m:
                            clientes.append(m.get('id') or m.get('nome'))
                            clientes_nomes.append(m.get('nome') or nome)
                        else:
                            clientes.append(nome)
                            clientes_nomes.append(nome)

                    # Monta parte contrária (réus)
                    reus_final = []
                    for nome in reus_list:
                        m = _melhor_match(nome, candidatos_reus)
                        reus_final.append(m.get('nome') if m else nome)
                    parte_contraria = reus_final  # lista de strings

                    patch = {
                        'numero': numero,
                        'titulo': titulo,
                        'data_abertura': data_abertura,
                        'nucleo': nucleo_val,
                        'clientes': clientes,
                        'clientes_nomes': clientes_nomes,
                        'parte_contraria': parte_contraria,
                        'responsavel': lenon_uid,
                        'responsavel_nome': default_responsavel_nome,
                        'sistema_processual': default_sistema,
                        'status': 'Em andamento',
                    }

                    try:
                        existente = buscar_processo_por_numero(numero)
                        if existente:
                            if not sobrescrever.value:
                                patch_limpo = {}
                                for k, v in patch.items():
                                    atual = existente.get(k)
                                    vazio = (atual is None) or (isinstance(atual, str) and not atual.strip()) or (isinstance(atual, list) and len(atual) == 0)
                                    if vazio and v not in [None, '', [], {}]:
                                        patch_limpo[k] = v
                                patch = patch_limpo
                            if patch:
                                atualizar_campos_processo(existente['_id'], patch)
                                atualizados += 1
                            ok += 1
                        else:
                            dados_novos = {
                                'titulo': titulo,
                                'numero': numero,
                                'tipo': 'Judicial',
                                'status': 'Em andamento',
                                'resultado': 'Pendente',
                                'area': '',
                                'estado': 'Santa Catarina',
                                'data_abertura': data_abertura,
                                'nucleo': nucleo_val,
                                'sistema_processual': default_sistema,
                                'clientes': clientes,
                                'clientes_nomes': clientes_nomes,
                                'parte_contraria': parte_contraria,
                                'responsavel': lenon_uid,
                                'responsavel_nome': default_responsavel_nome,
                            }
                            pid = criar_processo(dados_novos)
                            if pid:
                                ok += 1
                            else:
                                erros += 1
                    except Exception as e:
                        print(f"[MIGRACAO_PROCESSOS] Erro ao importar {numero}: {e}")
                        erros += 1

                ui.notify(f'Importação: OK {ok} | Atualizados {atualizados} | Erros {erros}',
                          type='positive' if erros == 0 else 'warning')
                render_tabela.refresh()

            with ui.row().classes('w-full items-center gap-3 mt-3'):
                ui.button('Selecionar todos', icon='select_all', on_click=lambda: setattr(tabela_imp, 'selected', rows_preview)).props('color=secondary dense')
                ui.button('Criar/Atualizar processos selecionados', icon='cloud_upload', on_click=_importar_selecionados).props('color=primary')

        # Carrega casos
        casos = listar_casos()
        casos_opts: Dict[str, str] = {}
        for c in casos:
            cid = _fmt_text(c.get('_id'))
            titulo = _fmt_text(c.get('titulo') or c.get('title') or 'Sem título')
            nucleo = _fmt_text(c.get('nucleo') or '')
            label = titulo
            if nucleo:
                label = f'{titulo} — {nucleo}'
            label = f'{label} ({cid[:6]})' if cid else label
            if cid:
                casos_opts[cid] = label

        # Controles de vinculação
        with ui.card().classes('w-full mb-4'):
            ui.label('2) Vincular processos a Casos').classes('text-xl font-bold text-gray-800 mb-2')
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

        # Tabela de processos já cadastrados
        with ui.card().classes('w-full mb-4'):
            ui.label('Processos cadastrados (marque e vincule ao Caso)').classes('text-lg font-bold text-gray-800 mb-3')

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
                        'titulo': titulo[:60] + '...' if len(titulo) > 60 else titulo,
                        'numero': numero or '-',
                        'caso_atual': caso_titulo or ('—' if not caso_id else f'({caso_id[:6]})'),
                        'clientes': clientes_txt[:40] + '...' if len(clientes_txt) > 40 else clientes_txt or '—',
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
