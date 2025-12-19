"""
Página de migração/vinculação de Processos → Casos (Visão Geral).

Inclui:
- Importação de planilha do Eproc (XLSX/CSV) com preview;
- Criação/atualização em lote de vg_processos;
- Vinculação em lote de processos a um Caso (vg_casos).

Rota: /visao-geral/migracao-processos
"""

from datetime import datetime
from typing import Dict, Any, List

from nicegui import ui
from nicegui import events

import io
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

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None


def _fmt_text(v: Any) -> str:
    return (str(v).strip() if v is not None else '').strip()


def _norm(s: str) -> str:
    s = _fmt_text(s).lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join([c for c in s if not unicodedata.combining(c)])
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _split_names(raw: Any) -> List[str]:
    """Divide autores/réus vindos da planilha em lista de nomes."""
    text = _fmt_text(raw)
    if not text:
        return []
    # separadores comuns
    parts = re.split(r'[;\n]| \| |, (?=[A-ZÁÉÍÓÚÃÕÇ])', text)
    cleaned = []
    for p in parts:
        p = _fmt_text(p)
        if p:
            cleaned.append(p)
    # remove duplicados preservando ordem
    seen = set()
    out = []
    for p in cleaned:
        key = _norm(p)
        if key and key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _parse_date_to_ddmmyyyy(raw: Any) -> str:
    """Converte várias entradas para DD/MM/AAAA (ou mantém texto)."""
    v = raw
    if v is None or v == '':
        return ''
    # pandas Timestamp / datetime
    try:
        if hasattr(v, 'strftime'):
            return v.strftime('%d/%m/%Y')
    except Exception:
        pass
    s = _fmt_text(v)
    if not s:
        return ''
    # Formatos comuns do Eproc: "29/08/2025 18:48:51" ou "29/08/2025"
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', s)
    if m:
        return f'{m.group(1)}/{m.group(2)}/{m.group(3)}'
    # fallback: mantém (ex: "2025" ou "09/2025")
    return s


def _detectar_coluna(cols: List[str], chaves: List[str]) -> str:
    """Tenta escolher uma coluna pelo nome (heurística simples)."""
    cols_norm = {c: _norm(c) for c in cols}
    for key in chaves:
        for original, n in cols_norm.items():
            if key in n:
                return original
    return ''


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
                'Aqui você vincula processos já cadastrados aos seus respectivos Casos. '
                'Selecione um Caso e marque os processos na lista para vincular em lote.'
            ).classes('text-gray-600')

        estado: Dict[str, Any] = {
            'caso_selecionado': None,
            'somente_sem_caso': True,
            'df': None,
            'import_rows': [],
        }

        # ---------------------------------------------------------------------
        # 1) IMPORTAÇÃO DE PLANILHA (EPROC)
        # ---------------------------------------------------------------------
        with ui.card().classes('w-full mb-4'):
            ui.label('1) Importar planilha do Eproc').classes('text-xl font-bold text-gray-800 mb-2')
            ui.label(
                'Faça upload do XLSX/CSV exportado do Eproc. Depois escolha quais colunas representam número, autores, réus, '
                'data de distribuição (vira a data de abertura) e núcleo.'
            ).classes('text-gray-600 mb-3')

            if pd is None:
                ui.label('⚠️ pandas/openpyxl não estão disponíveis neste ambiente.').classes('text-red-600')
            else:
                # Defaults pedidos
                default_sistema = 'eproc - TJSC - 1ª instância'
                default_responsavel_nome = 'Lenon'
                default_nucleo = 'Ambiental'

                # Carrega bases para matching (uma vez)
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

                # Estado da UI
                mapping = {
                    'numero': None,
                    'titulo': None,
                    'autores': None,
                    'reus': None,
                    'data_dist': None,
                    'nucleo': None,
                }

                sobrescrever = ui.checkbox('Sobrescrever campos existentes do processo', value=False)

                with ui.row().classes('w-full items-center gap-3 flex-wrap'):
                    upload = ui.upload(
                        label='Upload planilha (XLSX/CSV)',
                        auto_upload=True,
                        max_files=1,
                    ).props('flat color=primary')

                    sheet_name_input = ui.input('Aba (opcional)', placeholder='Ex: Planilha1').props('dense outlined').classes('w-56')

                preview_container = ui.column().classes('w-full mt-2')

                def _ler_planilha(nome_arquivo: str, content: bytes):
                    ext = (nome_arquivo or '').lower()
                    buf = io.BytesIO(content)
                    if ext.endswith('.csv'):
                        # tenta ; e ,
                        try:
                            return pd.read_csv(buf, sep=';', dtype=str)
                        except Exception:
                            buf.seek(0)
                            return pd.read_csv(buf, sep=',', dtype=str)
                    # xlsx/xls
                    if sheet_name_input.value and sheet_name_input.value.strip():
                        return pd.read_excel(buf, sheet_name=sheet_name_input.value.strip(), dtype=str)
                    return pd.read_excel(buf, dtype=str)

                def _montar_rows(df):
                    cols = list(df.columns)
                    # auto-detect
                    mapping['numero'] = mapping['numero'] or _detectar_coluna(cols, ['nº do processo', 'no do processo', 'numero do processo', 'número do processo', 'processo'])
                    mapping['data_dist'] = mapping['data_dist'] or _detectar_coluna(cols, ['data de autuacao', 'data de autuação', 'data de distribuicao', 'data de distribuição', 'data'])
                    mapping['autores'] = mapping['autores'] or _detectar_coluna(cols, ['autor', 'autores', 'parte autora'])
                    mapping['reus'] = mapping['reus'] or _detectar_coluna(cols, ['reu', 'réu', 'acusado', 'demandado', 'parte re'])
                    mapping['titulo'] = mapping['titulo'] or _detectar_coluna(cols, ['classe', 'classe da acao', 'classe da ação', 'assunto', 'titulo'])
                    mapping['nucleo'] = mapping['nucleo'] or _detectar_coluna(cols, ['nucleo', 'núcleo'])

                    # UI de mapping
                    preview_container.clear()
                    with preview_container:
                        ui.label('Mapeamento de colunas').classes('text-sm font-bold text-gray-700')
                        with ui.row().classes('w-full gap-3 flex-wrap'):
                            sel_numero = ui.select(cols, label='Coluna: Número', value=mapping['numero']).props('dense outlined').classes('w-64')
                            sel_titulo = ui.select(['(auto)'] + cols, label='Coluna: Título/Classe', value=mapping['titulo'] or '(auto)').props('dense outlined').classes('w-64')
                            sel_data = ui.select(['(vazio)'] + cols, label='Coluna: Data distribuição', value=mapping['data_dist'] or '(vazio)').props('dense outlined').classes('w-64')
                            sel_autores = ui.select(['(vazio)'] + cols, label='Coluna: Autores', value=mapping['autores'] or '(vazio)').props('dense outlined').classes('w-64')
                            sel_reus = ui.select(['(vazio)'] + cols, label='Coluna: Réus', value=mapping['reus'] or '(vazio)').props('dense outlined').classes('w-64')
                            sel_nucleo = ui.select(['(padrão)'] + cols, label='Coluna: Núcleo', value=mapping['nucleo'] or '(padrão)').props('dense outlined').classes('w-64')

                        ui.separator().classes('my-2')
                        ui.label('Preview (selecione linhas para importar/atualizar)').classes('text-sm font-bold text-gray-700')

                        # Monta preview rows (limitado)
                        rows = []
                        for _, r in df.head(200).iterrows():
                            numero = _fmt_text(r.get(sel_numero.value))
                            if not numero:
                                continue
                            titulo_raw = ''
                            if sel_titulo.value and sel_titulo.value != '(auto)':
                                titulo_raw = _fmt_text(r.get(sel_titulo.value))
                            else:
                                # auto: classe + assunto (se existirem)
                                classe = _fmt_text(r.get(_detectar_coluna(cols, ['classe'])))
                                assunto = _fmt_text(r.get(_detectar_coluna(cols, ['assunto'])))
                                titulo_raw = ' - '.join([x for x in [classe, assunto] if x]) or f'Processo {numero}'

                            data_raw = _fmt_text(r.get(sel_data.value)) if sel_data.value and sel_data.value != '(vazio)' else ''
                            data_abertura = _parse_date_to_ddmmyyyy(data_raw)

                            autores_raw = _fmt_text(r.get(sel_autores.value)) if sel_autores.value and sel_autores.value != '(vazio)' else ''
                            reus_raw = _fmt_text(r.get(sel_reus.value)) if sel_reus.value and sel_reus.value != '(vazio)' else ''
                            nucleo_raw = _fmt_text(r.get(sel_nucleo.value)) if sel_nucleo.value and sel_nucleo.value not in ['(padrão)'] else default_nucleo

                            # sugestões rápidas (somente 1º nome)
                            autores_list = _split_names(autores_raw)
                            reus_list = _split_names(reus_raw)
                            sug_autor = _melhor_match(autores_list[0], candidatos_autores) if autores_list else {}
                            sug_reu = _melhor_match(reus_list[0], candidatos_reus) if reus_list else {}

                            rows.append({
                                '_key': numero,
                                'numero': numero,
                                'titulo': titulo_raw,
                                'data_abertura': data_abertura or '—',
                                'nucleo': nucleo_raw or '—',
                                'autor': autores_list[0] if autores_list else '—',
                                'sug_autor': (sug_autor.get('nome') if sug_autor else '—'),
                                'reu': reus_list[0] if reus_list else '—',
                                'sug_reu': (sug_reu.get('nome') if sug_reu else '—'),
                            })

                        tabela_imp = ui.table(
                            columns=[
                                {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left', 'sortable': True},
                                {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left'},
                                {'name': 'data_abertura', 'label': 'Data abertura', 'field': 'data_abertura', 'align': 'left'},
                                {'name': 'nucleo', 'label': 'Núcleo', 'field': 'nucleo', 'align': 'left'},
                                {'name': 'autor', 'label': 'Autor (1º)', 'field': 'autor', 'align': 'left'},
                                {'name': 'sug_autor', 'label': 'Sugestão autor', 'field': 'sug_autor', 'align': 'left'},
                                {'name': 'reu', 'label': 'Réu (1º)', 'field': 'reu', 'align': 'left'},
                                {'name': 'sug_reu', 'label': 'Sugestão réu', 'field': 'sug_reu', 'align': 'left'},
                            ],
                            rows=rows,
                            row_key='_key',
                            selection='multiple',
                            pagination={'rowsPerPage': 10},
                        ).classes('w-full')

                        def _importar_selecionados():
                            selecionados = tabela_imp.selected_rows or []
                            if not selecionados:
                                ui.notify('Selecione ao menos 1 linha do preview.', type='warning')
                                return

                            ok = 0
                            atualizados = 0
                            erros = 0

                            for item in selecionados:
                                numero = item.get('numero', '')
                                # pega linha original do df pelo numero (primeira ocorrência)
                                try:
                                    linha = df[df[sel_numero.value].astype(str).str.strip() == numero].head(1).to_dict('records')[0]
                                except Exception:
                                    linha = {}

                                titulo = _fmt_text(item.get('titulo') or f'Processo {numero}')
                                data_abertura = _fmt_text(item.get('data_abertura'))
                                nucleo_val = _fmt_text(item.get('nucleo')) or default_nucleo

                                autores_list = _split_names(linha.get(sel_autores.value)) if sel_autores.value and sel_autores.value != '(vazio)' else []
                                reus_list = _split_names(linha.get(sel_reus.value)) if sel_reus.value and sel_reus.value != '(vazio)' else []

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

                                # Monta parte contrária (réus) com match (texto)
                                reus_final = []
                                for nome in reus_list:
                                    m = _melhor_match(nome, candidatos_reus)
                                    reus_final.append(m.get('nome') if m else nome)
                                parte_contraria = ', '.join([x for x in reus_final if _fmt_text(x)])

                                patch = {
                                    'numero': numero,
                                    'titulo': titulo,
                                    'data_abertura': data_abertura if data_abertura != '—' else '',
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
                                        # se não sobrescrever, só preenche vazios
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
                                        # cria novo (mínimo necessário)
                                        dados_novos = {
                                            'titulo': titulo,
                                            'numero': numero,
                                            'tipo': 'Judicial',
                                            'status': 'Em andamento',
                                            'resultado': 'Pendente',
                                            'area': '',
                                            'estado': 'Santa Catarina',
                                            'data_abertura': patch.get('data_abertura', ''),
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

                            ui.notify(f'Importação concluída: OK {ok} | Atualizados {atualizados} | Erros {erros}',
                                      type='positive' if erros == 0 else 'warning')
                            render_tabela.refresh()

                        ui.button('Criar/Atualizar processos selecionados', icon='cloud_upload', on_click=_importar_selecionados).props('color=primary').classes('mt-3')

                async def handle_upload(e: events.UploadEventArguments):
                    try:
                        if not hasattr(e, 'file') or e.file is None:
                            ui.notify('Upload inválido.', type='negative')
                            return

                        file_name = getattr(e.file, 'name', '') or getattr(e, 'name', '') or 'arquivo'
                        file_bytes = None

                        if hasattr(e.file, 'read'):
                            try:
                                if callable(e.file.read):
                                    file_bytes = e.file.read()
                            except Exception:
                                file_bytes = None
                        if hasattr(e.file, 'content'):
                            file_bytes = e.file.content
                        elif hasattr(e.file, 'data'):
                            file_bytes = e.file.data
                        elif hasattr(e.file, 'bytes'):
                            file_bytes = e.file.bytes

                        if not file_bytes:
                            ui.notify('Não foi possível ler o arquivo.', type='negative')
                            upload.reset()
                            return

                        df = _ler_planilha(file_name, file_bytes)
                        estado['df'] = df
                        _montar_rows(df)
                        ui.notify('Planilha carregada! Ajuste o mapeamento e selecione linhas.', type='positive')
                    except Exception as ex:
                        print(f"[MIGRACAO_PROCESSOS] Erro ao ler planilha: {type(ex).__name__}: {ex}")
                        import traceback
                        traceback.print_exc()
                        ui.notify(f'Erro ao ler planilha: {str(ex)}', type='negative')
                    finally:
                        upload.reset()

                upload.on_upload(handle_upload)

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
                'Depois de importar a planilha, você pode usar a seção abaixo para vincular processos aos Casos em lote.'
            ).classes('text-gray-600')


