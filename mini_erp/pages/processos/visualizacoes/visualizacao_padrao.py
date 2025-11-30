"""
visualizacao_padrao.py - Página simplificada do módulo de Processos.

Exibe todos os processos cadastrados no Firebase em uma tabela limpa.
"""

import json
from pathlib import Path

from nicegui import app, ui, context
from ....core import layout, get_processes_list, get_clients_list, get_opposing_parties_list, get_cases_list, invalidate_cache
from ....auth import is_authenticated
from ..ui_components import BODY_SLOT_AREA, BODY_SLOT_STATUS, TABELA_PROCESSOS_CSS
from ..utils import normalize_name_for_display
from ..modais.modal_processo import render_process_dialog
from ..modais.modal_protocolo import render_protocol_dialog
from ..modais.modal_processo_futuro import render_future_process_dialog


def _get_priority_name(name: str, people_list: list) -> str:
    """
    Busca pessoa na lista e retorna nome de exibição usando regra centralizada.
    
    MIGRADO: Agora usa get_display_name() para consistência em todo o sistema.
    Faz busca bidirecional (nome completo → display_name e display_name → nome completo).
    Sempre em MAIÚSCULAS.
    """
    from ....core import get_display_name
    
    if not name:
        return ''
    
    normalized_input = normalize_name_for_display(name)
    
    # Busca pessoa na lista pelo nome, ID ou nome de exibição
    person = None
    for p in people_list:
        full_name = p.get('full_name') or p.get('name', '')
        display_name = get_display_name(p)
        normalized_full = normalize_name_for_display(full_name)
        normalized_display = normalize_name_for_display(display_name)
        
        # Busca por nome completo, ID ou nome de exibição (com fallback normalizado)
        if (
            full_name == name or 
            p.get('_id') == name or 
            display_name == name or
            display_name.upper() == name.upper() or
            (normalized_input and (
                normalized_full == normalized_input or
                normalized_display == normalized_input
            ))
        ):
            person = p
            break
    
    if person:
        # Usa função centralizada para obter nome de exibição
        display_name = get_display_name(person)
        return display_name.upper() if display_name else name.upper()
    
    # Se não encontrou, retorna o nome original em maiúsculas
    return name.upper() if name else ''


def _format_names_list(names_raw, people_list: list) -> list:
    """
    Formata lista de nomes aplicando prioridade e MAIÚSCULAS.
    Retorna lista para exibição vertical.
    """
    if not names_raw:
        return []
    
    if isinstance(names_raw, list):
        formatted = [_get_priority_name(str(n), people_list) for n in names_raw if n]
        return formatted
    else:
        name = _get_priority_name(str(names_raw), people_list)
        return [name] if name else []


def get_display_title(process):
    """Retorna título sem indentação hierárquica."""
    return process.get('title', 'Sem título')


def _get_backup_path() -> Path:
    """
    Retorna caminho do arquivo de backup de casos.
    Cria diretório de backups se ainda não existir.
    """
    project_root = Path(__file__).resolve().parents[3]
    backups_dir = project_root / 'backups'
    backups_dir.mkdir(parents=True, exist_ok=True)
    return backups_dir / 'processos_cases_backup.json'


def ensure_cases_backup(cases: list) -> None:
    """Cria backup simples dos casos quando ainda não existe."""
    try:
        backup_path = _get_backup_path()
        if backup_path.exists() and backup_path.stat().st_size > 0:
            return

        payload = {
            'total_cases': len(cases),
            'cases': cases,
        }
        backup_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding='utf-8')
        print(f"[BACKUP] Backup de casos criado em {backup_path}")
    except Exception as exc:
        print(f"[BACKUP] Falha ao criar backup de casos: {exc}")


def build_case_filter_options(all_rows: list = None) -> list:
    """
    Constrói lista de opções para o filtro de casos.
    
    Extrai casos únicos do campo 'cases_list' de todos os processos e acompanhamentos,
    garantindo que apenas casos realmente vinculados apareçam no filtro.
    
    Args:
        all_rows: Lista opcional de processos já carregados. Se None, busca do Firestore.
    
    Returns:
        Lista de strings com casos únicos, ordenados alfabeticamente.
        Primeiro item é sempre string vazia '' para opção "sem filtro".
    
    Nota:
        Esta função extrai casos dos processos (cases_list) em vez de buscar
        todos os casos do Firestore, garantindo que apenas casos vinculados
        apareçam como opções de filtro.
    """
    try:
        # Se all_rows não foi fornecido, busca processos do Firestore
        if all_rows is None:
            from ..database import get_all_processes
            all_processes = get_all_processes()
            # Converte processos para formato de rows (simula fetch_processes)
            # Mas para otimização, vamos usar fetch_processes() se necessário
            all_rows = []
        
        # Extrai todos os casos únicos de cases_list de todos os processos
        # Suporta processos normais e acompanhamentos de terceiros
        all_cases = set()
        
        for row in all_rows:
            try:
                cases_list = row.get('cases_list') or []
                # Adiciona cada caso à lista (remove duplicatas com set)
                for case in cases_list:
                    try:
                        if case is None:
                            continue
                        
                        # Converte para string e sanitiza
                        case_str = str(case).strip()
                        
                        # Validação: ignora strings vazias
                        if not case_str:
                            continue
                        
                        # Validação: garante que é uma string válida (não é número float solto)
                        # Proteção contra valores como "1.5" que podem causar erro no NiceGUI
                        try:
                            # Tenta converter para float - se conseguir e for número puro, ignora
                            float_val = float(case_str)
                            # Se for número puro sem texto, ignora (não é um caso válido)
                            if case_str.replace('.', '').replace('-', '').isdigit():
                                print(f"[CASES] ⚠️  Valor numérico puro ignorado: '{case_str}'")
                                continue
                        except (ValueError, TypeError):
                            # Não é número puro, pode ser string válida - continua
                            pass
                        
                        # Adiciona caso válido
                        all_cases.add(case_str)
                        
                    except Exception as case_exc:
                        print(f"[CASES] ⚠️  Erro ao processar caso individual '{case}': {case_exc}")
                        continue
                        
            except Exception as row_exc:
                print(f"[CASES] ⚠️  Erro ao processar row para casos: {row_exc}")
                continue
        
        # Converte para lista, ordena alfabeticamente (case-insensitive)
        # Adiciona opção vazia no início para "sem filtro"
        options = [''] + sorted(all_cases, key=str.lower)
        
        print(f"[CASES] ✓ Opções de casos construídas: {len(options)} opções (incluindo vazio)")
        return options
    
    except Exception as exc:
        print(f"[CASES] ❌ Erro ao montar opções de casos: {exc}")
        import traceback
        traceback.print_exc()
        # Retorna opção vazia em caso de erro
        return ['']


def fetch_processes():
    """
    Busca TODOS os processos do Firestore e formata para exibição.
    
    VISUALIZAÇÃO PADRÃO: Esta função retorna TODOS os processos cadastrados,
    incluindo processos normais E acompanhamentos de terceiros.
    Sem nenhum filtro aplicado. Os filtros são aplicados posteriormente
    na função filter_rows() quando o usuário seleciona opções nos dropdowns.
    
    Returns:
        Lista de dicionários prontos para a tabela (TODOS os processos + acompanhamentos).
    """
    try:
        # Buscar processos normais
        raw = get_processes_list()
        print(f"[FETCH_PROCESSOS] Processos normais encontrados: {len(raw)}")
        
        # Buscar acompanhamentos de terceiros e adicionar à lista
        try:
            from ..database import obter_todos_acompanhamentos
            acompanhamentos = obter_todos_acompanhamentos()
            print(f"[FETCH_PROCESSOS] Acompanhamentos encontrados: {len(acompanhamentos)}")
            
            # Adicionar acompanhamentos à lista raw
            for acomp in acompanhamentos:
                # Marcar como acompanhamento para processamento posterior
                acomp['_is_third_party_monitoring'] = True
                
                # DEBUG: Verificar se acompanhamento tem casos
                cases_debug = acomp.get('cases') or acomp.get('casos') or acomp.get('case_ids') or []
                if cases_debug:
                    print(f"[FETCH_PROCESSOS] Acompanhamento '{acomp.get('title', 'Sem título')}' tem casos: {cases_debug}")
                else:
                    print(f"[FETCH_PROCESSOS] ⚠️  Acompanhamento '{acomp.get('title', 'Sem título')}' NÃO tem casos vinculados")
                
                raw.append(acomp)
            
            print(f"[FETCH_PROCESSOS] Total combinado (processos + acompanhamentos): {len(raw)}")
        except Exception as e:
            print(f"[FETCH_PROCESSOS] Erro ao buscar acompanhamentos: {e}")
            import traceback
            traceback.print_exc()
        
        # Log geral de processos buscados
        print(f"[FETCH_PROCESSES] Total de processos retornados do banco: {len(raw)}")
        
        # DEBUG: Rastreamento específico do processo "RECURSO ESPECIAL"
        recurso_especial = None
        for p in raw:
            if 'RECURSO ESPECIAL' in (p.get('title') or '').upper():
                recurso_especial = p
                print(f"[DEBUG RECURSO ESPECIAL] ✓ Encontrado no banco:")
                print(f"  Título: {p.get('title')}")
                print(f"  Status: '{p.get('status')}' (tipo: {type(p.get('status'))})")
                print(f"  Process Type: '{p.get('process_type')}'")
                print(f"  Doc ID: {p.get('_id')}")
                print(f"  Todos os campos: {list(p.keys())}")
                break
        
        if not recurso_especial:
            print(f"[DEBUG RECURSO ESPECIAL] ❌ NÃO encontrado no banco!")
            print(f"[DEBUG] Total de processos retornados: {len(raw)}")
            print(f"[DEBUG] Títulos dos primeiros 5: {[p.get('title', 'Sem título')[:50] for p in raw[:5]]}")
        
        # DEBUG: Busca processos com "Jandir" no título ou clientes
        processos_jandir = []
        for p in raw:
            titulo = (p.get('title') or '').upper()
            clientes = p.get('clients', [])
            clientes_str = ' '.join(str(c) for c in clientes).upper()
            
            if 'JANDIR' in titulo or 'JANDIR' in clientes_str:
                processos_jandir.append({
                    'id': p.get('_id'),
                    'titulo': p.get('title'),
                    'clientes': clientes,
                    'status': p.get('status')
                })
        
        if processos_jandir:
            print(f"[DEBUG JANDIR] Encontrados {len(processos_jandir)} processo(s) relacionados a Jandir:")
            for proc in processos_jandir:
                print(f"  - ID: {proc['id']}")
                print(f"    Título: {proc['titulo']}")
                print(f"    Clientes: {proc['clientes']}")
                print(f"    Status: {proc['status']}")
        else:
            print(f"[DEBUG JANDIR] Nenhum processo encontrado com 'Jandir' no título ou clientes")
        
        # DEBUG: Lista processos sem clientes
        processos_sem_clientes = [p for p in raw if not p.get('clients') or (isinstance(p.get('clients'), list) and len(p.get('clients')) == 0)]
        if processos_sem_clientes:
            print(f"[DEBUG] ⚠️  Encontrados {len(processos_sem_clientes)} processo(s) sem clientes:")
            for p in processos_sem_clientes[:5]:  # Mostra apenas os 5 primeiros
                print(f"  - {p.get('title', 'Sem título')} (ID: {p.get('_id')})")
        
        # Debug: verifica processos futuros
        future_processes = [p for p in raw if p.get('process_type') == 'Futuro' or p.get('status') == 'Futuro/Previsto']
        if future_processes:
            print(f"[DEBUG] Encontrados {len(future_processes)} processos futuros: {[p.get('title') for p in future_processes]}")
        
        # Carrega listas de pessoas para buscar siglas/display_names
        clients_list = get_clients_list()
        opposing_list = get_opposing_parties_list()
        all_people = clients_list + opposing_list

        # Cache único de casos para evitar consultas repetidas
        all_cases = get_cases_list()
        case_titles_by_id = {}
        for case in all_cases:
            case_id = case.get('_id') or case.get('id')
            case_title = case.get('title') or ''
            if case_id and case_title:
                case_titles_by_id[str(case_id)] = str(case_title).strip()
        
        rows = []
        rows_count_before = 0
        rows_count_after = 0
        recurso_especial_in_rows = False
        
        for proc in raw:
            rows_count_before += 1
            
            # Verificar se é um acompanhamento de terceiro
            is_third_party = proc.get('_is_third_party_monitoring', False)
            
            # Debug: verifica processos sem status ou com status diferente
            proc_status = proc.get('status') or ''
            proc_title = proc.get('title') or proc.get('process_title') or 'Sem título'
            if not proc_status and proc.get('process_type') == 'Futuro':
                print(f"[DEBUG] Processo sem status encontrado: {proc_title} (process_type: {proc.get('process_type')})")
            
            if is_third_party:
                # É um acompanhamento de terceiro - processar de forma diferente
                print(f"[FETCH_PROCESSOS] Processando acompanhamento: {proc_title}")
                
                # REGRA: Acompanhamentos mostram "NA" em Clientes e Parte Contrária
                clients_list = ['NA']
                opposing_list = ['NA']
                
                # Título do acompanhamento (definir antes de usar nos logs)
                display_title = proc.get('title') or proc.get('process_title') or proc.get('titulo') or 'Acompanhamento de Terceiro'
                
                # Extrai casos vinculados - acompanhamentos podem ter casos
                # IMPORTANTE: Verificar múltiplos campos possíveis para compatibilidade
                # CORREÇÃO: Adiciona validação e tratamento de erros para prevenir ValueError
                cases_list = []
                try:
                    cases_raw = proc.get('cases') or proc.get('casos') or proc.get('case_ids') or []
                    if isinstance(cases_raw, list):
                        for c in cases_raw:
                            try:
                                if c is None:
                                    continue
                                case_str = str(c).strip()
                                if case_str:
                                    cases_list.append(case_str)
                            except Exception as case_exc:
                                print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar caso de acompanhamento '{c}': {case_exc}")
                                continue
                    elif isinstance(cases_raw, str):
                        # Se for string, pode ser uma lista separada por vírgula ou um único caso
                        try:
                            if cases_raw:
                                cases_list = [c.strip() for c in cases_raw.split(',') if c.strip()]
                        except Exception as str_exc:
                            print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar casos como string '{cases_raw}': {str_exc}")
                            cases_list = []
                    else:
                        try:
                            if cases_raw:
                                case_str = str(cases_raw).strip()
                                if case_str:
                                    cases_list = [case_str]
                        except Exception as single_exc:
                            print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar caso único '{cases_raw}': {single_exc}")
                            cases_list = []
                except Exception as cases_exc:
                    print(f"[FETCH_PROCESSOS] ⚠️  Erro ao extrair casos do acompanhamento: {cases_exc}")
                    cases_list = []
                
                # Log para debug
                if cases_list:
                    print(f"[FETCH_PROCESSOS] Acompanhamento '{display_title}' tem casos: {cases_list}")
                else:
                    print(f"[FETCH_PROCESSOS] ⚠️  Acompanhamento '{display_title}' NÃO tem casos vinculados")
                
            else:
                # É um processo normal - processar normalmente
                # Extrai e formata clientes (prioridade + MAIÚSCULAS) - retorna lista
                clients_raw = proc.get('clients') or proc.get('client') or []
                clients_list = _format_names_list(clients_raw, all_people)

                # Extrai e formata partes contrárias (prioridade + MAIÚSCULAS) - retorna lista
                opposing_raw = proc.get('opposing_parties') or []
                opposing_list = _format_names_list(opposing_raw, all_people)

                # Extrai casos vinculados - retorna lista
                # IMPORTANTE: Verificar múltiplos campos (cases, case_ids) para compatibilidade
                # CORREÇÃO: Adiciona validação e tratamento de erros para prevenir ValueError
                cases_raw = proc.get('cases') or []
                case_ids = proc.get('case_ids') or []
                
                cases_list = []
                
                # Processar casos diretos (títulos) do campo 'cases'
                try:
                    if cases_raw:
                        if isinstance(cases_raw, list):
                            for c in cases_raw:
                                try:
                                    if c is None:
                                        continue
                                    case_str = str(c).strip()
                                    if case_str:
                                        cases_list.append(case_str)
                                except Exception as case_exc:
                                    print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar caso '{c}': {case_exc}")
                                    continue
                        else:
                            try:
                                case_str = str(cases_raw).strip()
                                if case_str:
                                    cases_list.append(case_str)
                            except Exception as case_exc:
                                print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar caso único '{cases_raw}': {case_exc}")
                except Exception as cases_raw_exc:
                    print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar cases_raw: {cases_raw_exc}")
                
                # Se tiver case_ids, converter IDs para títulos
                try:
                    if case_ids and isinstance(case_ids, list):
                        # Buscar títulos dos casos pelos IDs (cache para evitar múltiplas buscas)
                        all_cases = get_cases_list()
                        case_titles_by_id = {}
                        for case in all_cases:
                            try:
                                case_id = case.get('_id') or case.get('id')
                                case_title = case.get('title') or ''
                                if case_id and case_title:
                                    case_titles_by_id[str(case_id)] = str(case_title).strip()
                            except Exception as case_map_exc:
                                print(f"[FETCH_PROCESSOS] ⚠️  Erro ao mapear caso: {case_map_exc}")
                                continue
                        
                        # Converter IDs para títulos e adicionar à lista
                        for cid in case_ids:
                            try:
                                if cid:
                                    case_title = case_titles_by_id.get(str(cid), str(cid).strip())
                                    # Evitar duplicatas
                                    if case_title and case_title not in cases_list:
                                        cases_list.append(case_title)
                            except Exception as cid_exc:
                                print(f"[FETCH_PROCESSOS] ⚠️  Erro ao converter case_id '{cid}': {cid_exc}")
                                continue
                except Exception as case_ids_exc:
                    print(f"[FETCH_PROCESSOS] ⚠️  Erro ao processar case_ids: {case_ids_exc}")
                
                # Remover duplicatas mantendo ordem
                seen = set()
                cases_list = [c for c in cases_list if c and (c not in seen and not seen.add(c))]
                
                # Título simples sem indentação hierárquica
                display_title = get_display_title(proc)

            # =====================================================
            # PROCESSAMENTO DE DATA DE ABERTURA (APROXIMADA)
            # =====================================================
            # Suporta 3 formatos:
            # - AAAA (apenas ano): 2008 → ordena como 2008/00/00
            # - MM/AAAA (mês/ano): 09/2008 → ordena como 2008/09/00
            # - DD/MM/AAAA (completa): 05/09/2008 → ordena como 2008/09/05
            # =====================================================
            data_abertura_raw = proc.get('data_abertura') or ''
            data_abertura_display = ''
            data_abertura_sort = ''  # Formato AAAA/MM/DD para ordenação correta
            
            if data_abertura_raw:
                try:
                    data_abertura_raw = data_abertura_raw.strip()
                    
                    # Formato: AAAA (apenas ano) - 4 dígitos
                    if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                        data_abertura_display = data_abertura_raw
                        data_abertura_sort = f"{data_abertura_raw}/00/00"
                    
                    # Formato: MM/AAAA (mês e ano) - 7 caracteres
                    elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                        partes = data_abertura_raw.split('/')
                        if len(partes) == 2:
                            data_abertura_display = data_abertura_raw
                            data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
                    
                    # Formato: DD/MM/AAAA (completa) - 10 caracteres
                    elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                        partes = data_abertura_raw.split('/')
                        if len(partes) == 3:
                            data_abertura_display = data_abertura_raw
                            data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
                    
                    # Formato legado: YYYY-MM-DD
                    elif '-' in data_abertura_raw:
                        partes = data_abertura_raw.split('-')
                        if len(partes) == 3:
                            data_abertura_display = f"{partes[2]}/{partes[1]}/{partes[0]}"
                            data_abertura_sort = f"{partes[0]}/{partes[1]}/{partes[2]}"
                        else:
                            data_abertura_display = data_abertura_raw
                    
                    else:
                        # Fallback - mantém valor original
                        data_abertura_display = data_abertura_raw
                        
                except Exception:
                    data_abertura_display = data_abertura_raw
            
            # Processamento de data para acompanhamentos (se ainda não processado)
            if is_third_party and not data_abertura_display:
                data_abertura_raw = proc.get('data_de_abertura') or proc.get('start_date') or ''
                if data_abertura_raw:
                    # Mesma lógica de processamento de data
                    try:
                        data_abertura_raw = data_abertura_raw.strip()
                        if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                            data_abertura_display = data_abertura_raw
                            data_abertura_sort = f"{data_abertura_raw}/00/00"
                        elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                            partes = data_abertura_raw.split('/')
                            if len(partes) == 2:
                                data_abertura_display = data_abertura_raw
                                data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
                        elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                            partes = data_abertura_raw.split('/')
                            if len(partes) == 3:
                                data_abertura_display = data_abertura_raw
                                data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
                        else:
                            data_abertura_display = data_abertura_raw
                    except Exception:
                        data_abertura_display = data_abertura_raw
            
            # Título já foi processado acima (dentro do if/else)
            if not is_third_party:
                display_title = get_display_title(proc)
            
            # Garante que processos futuros tenham status correto
            # CORREÇÃO: Normaliza status vazio/None para garantir que todos os processos apareçam
            proc_status = proc.get('status')
            
            # Se status é None, string vazia ou apenas espaços, trata como vazio
            if not proc_status or (isinstance(proc_status, str) and not proc_status.strip()):
                proc_status = ''
            
            # Se processo é do tipo "Futuro" e não tem status, define como "Futuro/Previsto"
            if proc.get('process_type') == 'Futuro' and not proc_status:
                proc_status = 'Futuro/Previsto'
            
            # Garante que status seja sempre uma string (não None)
            proc_status = proc_status or ''
            
            # DEBUG: Rastreamento específico do processo "RECURSO ESPECIAL"
            is_recurso_especial = 'RECURSO ESPECIAL' in display_title.upper()
            if is_recurso_especial:
                print(f"[DEBUG RECURSO ESPECIAL] Processando para tabela:")
                print(f"  Status original: '{proc.get('status')}'")
                print(f"  Status final: '{proc_status}'")
                print(f"  Process Type: '{proc.get('process_type')}'")
                print(f"  Título: '{display_title}'")
            
            row_data = {
                '_id': proc.get('_id') or proc.get('id', ''),
                'data_abertura': data_abertura_display,
                'data_abertura_sort': data_abertura_sort,  # Formato AAAA/MM/DD para ordenação
                'title': display_title,
                'title_raw': proc.get('title') or proc.get('process_title') or proc.get('titulo') or proc.get('searchable_title') or '(sem título)',  # Título original para busca
                'number': proc.get('number') or proc.get('process_number') or '',
                'clients_list': clients_list,  # Já é ['NA'] para acompanhamentos
                'opposing_list': opposing_list,  # Já é ['NA'] para acompanhamentos
                'cases_list': cases_list,
                'system': proc.get('system') or '',
                'status': proc_status,
                'area': proc.get('area') or proc.get('area_direito') or '',
                'link': proc.get('link') or proc.get('link_do_processo') or '',
                'is_third_party_monitoring': is_third_party,  # Marca como acompanhamento para aplicar cores
            }
            
            if is_third_party:
                print(f"[FETCH_PROCESSOS] Row de acompanhamento criada: título='{display_title}', casos={cases_list}")
            
            rows.append(row_data)
            rows_count_after += 1
            
            if is_recurso_especial:
                recurso_especial_in_rows = True
                print(f"[DEBUG RECURSO ESPECIAL] ✓ Adicionado à lista de rows")
                print(f"  Row data: {row_data}")
        
        # DEBUG: Validação final
        print(f"[FETCH_PROCESSES] Total processos no banco: {len(raw)}")
        print(f"[FETCH_PROCESSES] Total rows criadas: {len(rows)}")
        
        # Verifica se processos de Jandir foram adicionados às rows
        rows_jandir = [r for r in rows if 'JANDIR' in (r.get('title') or '').upper() or any('JANDIR' in str(c).upper() for c in r.get('clients_list', []))]
        if rows_jandir:
            print(f"[FETCH_PROCESSES] ✓ Processo(s) de Jandir adicionado(s) às rows: {len(rows_jandir)}")
        elif processos_jandir:
            print(f"[FETCH_PROCESSES] ⚠️  Processo(s) de Jandir encontrado(s) no banco mas NÃO adicionado(s) às rows!")
        
        if recurso_especial and not recurso_especial_in_rows:
            print(f"[DEBUG RECURSO ESPECIAL] ❌ ERRO: Processo encontrado no banco mas NÃO foi adicionado às rows!")
        elif recurso_especial_in_rows:
            print(f"[DEBUG RECURSO ESPECIAL] ✓ Processo adicionado com sucesso às rows")
        
        # Ordena por título
        rows.sort(key=lambda r: (r.get('title') or '').lower())
        return rows
    except Exception as e:
        print(f"Erro ao buscar processos: {e}")
        return []


# Colunas da tabela com larguras otimizadas
# REGRA: Coluna "Data" (data de abertura) sempre como primeira coluna nas visualizações de processos
# Usa campo data_abertura_sort (AAAA/MM/DD) para ordenação cronológica correta
COLUMNS = [
    {'name': 'data_abertura', 'label': 'Data', 'field': 'data_abertura_sort', 'align': 'center', 'sortable': True, 'style': 'width: 90px; min-width: 90px;'},
    {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True, 'style': 'width: 120px; max-width: 120px;'},
    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True, 'style': 'width: 280px; max-width: 280px;'},
    {'name': 'cases', 'label': 'Casos', 'field': 'cases', 'align': 'left', 'style': 'width: 180px; min-width: 180px;'},
    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 180px;'},
    {'name': 'clients', 'label': 'Clientes', 'field': 'clients', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
    {'name': 'opposing', 'label': 'Parte Contrária', 'field': 'opposing', 'align': 'left', 'style': 'width: 100px; max-width: 100px;'},
    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 150px;'},
]


@ui.page('/processos')
def processos():
    """Página principal de processos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    with layout('Processos', breadcrumbs=[('Processos', None)]):
        # Aplicar CSS padrão de cores alternadas para tabelas de processos
        ui.add_head_html(TABELA_PROCESSOS_CSS)
        
        # VISUALIZAÇÃO PADRÃO: Todos os processos (sem filtros)
        # Filtro via URL: filter=futuro_previsto (processos futuros) ou filter=acompanhamentos_terceiros
        # Não há necessidade de verificar URL via JavaScript aqui, pois já é feito no Python abaixo
        
        # Verificar parâmetro de filtro da URL para acompanhamentos de terceiros
        initial_filter_acompanhamentos = False
        try:
            # Tenta ler query parameter da URL do contexto
            if hasattr(context, 'client') and hasattr(context.client, 'request'):
                from urllib.parse import parse_qs, urlparse
                request_url = str(context.client.request.url) if hasattr(context.client.request, 'url') else ''
                if request_url:
                    parsed = urlparse(request_url)
                    query_params = parse_qs(parsed.query)
                    # Verifica se há filtro de acompanhamentos de terceiros
                    if query_params.get('filter') and 'acompanhamentos_terceiros' in query_params.get('filter', [])[0]:
                        initial_filter_acompanhamentos = True
                        print("[PROCESSOS] Filtro de acompanhamentos de terceiros detectado na URL")
        except Exception as e:
            print(f"[PROCESSOS] Erro ao ler parâmetro da URL: {e}")
        
        # Função de callback para atualizar após salvar processo
        def on_process_saved():
            """
            Callback chamado após salvar um processo.
            Invalida cache e recarrega a tabela.
            """
            print("[PROCESSO SALVO] Invalidando cache e recarregando tabela...")
            
            # Invalida cache de processos e clientes (clientes podem ter mudado)
            invalidate_cache('processes')
            invalidate_cache('clients')
            
            # Log de debug: verifica quantos processos existem após invalidar cache
            from ....core import get_processes_list
            processos_apos_cache = get_processes_list()
            print(f"[PROCESSO SALVO] Total de processos após invalidar cache: {len(processos_apos_cache)}")
            
            # Recarrega tabela
            refresh_table(force_reload=True)
            
            print("[PROCESSO SALVO] Tabela recarregada com sucesso!")
        
        # Função de callback para atualizar após salvar protocolo
        def on_protocol_saved():
            invalidate_cache('protocols')
            # Atualiza tabela caso algum processo mostre contagem de protocolos
            refresh_table(force_reload=True)
        
        # Criar modal completo com barra lateral (uma vez para toda a página)
        process_dialog, open_process_modal = render_process_dialog(
            on_success=on_process_saved
        )
        
        # Modal de protocolo independente
        protocol_dialog, open_protocol_modal = render_protocol_dialog(
            on_success=on_protocol_saved
        )
        
        # Modal de processo futuro
        future_process_dialog, open_future_process_modal = render_future_process_dialog(
            on_success=on_process_saved
        )
        
        # Estado dos filtros (usando variáveis Python simples)
        # VISUALIZAÇÃO PADRÃO: Todos os processos (sem filtros aplicados)
        # Filtro via URL só é aplicado quando há explicitamente filter=futuro_previsto (caso especial do painel)
        initial_status_filter = ''
        try:
            # Tenta ler query parameter da URL do contexto (apenas quando vem do painel)
            if hasattr(context, 'client') and hasattr(context.client, 'request'):
                from urllib.parse import parse_qs, urlparse
                request_url = str(context.client.request.url) if hasattr(context.client.request, 'url') else ''
                if request_url:
                    parsed = urlparse(request_url)
                    query_params = parse_qs(parsed.query)
                    # Só aplica filtro se houver explicitamente filter=futuro_previsto na URL
                    if query_params.get('filter') and 'futuro_previsto' in query_params.get('filter', [])[0]:
                        initial_status_filter = 'Futuro/Previsto'
        except:
            # Se houver erro ao ler URL, mantém vazio (visualização padrão = todos)
            pass
        
        # Inicializa todos os filtros vazios (visualização padrão mostra TODOS os processos)
        search_term = {'value': ''}
        filter_area = {'value': ''}
        filter_case = {'value': ''}
        filter_client = {'value': ''}
        filter_parte = {'value': ''}
        filter_opposing = {'value': ''}
        filter_status = {'value': initial_status_filter}  # Vazio por padrão, só preenchido se vier da URL do painel
        data_cache = {'rows': None}

        # Persiste estado do filtro de casos para manter seleção ao navegar
        saved_filters = app.storage.user.get('processos_filters', {})
        if isinstance(saved_filters, dict):
            filter_case['value'] = saved_filters.get('case', '')
        
        # Referência para render_table (será definida depois)
        render_table_ref = {'func': None}
        
        # Função para atualizar tabela
        def refresh_table(force_reload: bool = False):
            if force_reload:
                data_cache['rows'] = None
                reload_case_options()
            if render_table_ref['func']:
                render_table_ref['func'].refresh()

        def load_rows(force_reload: bool = False):
            """Busca processos/acompanhamentos com cache simples para evitar consultas redundantes."""
            if force_reload or data_cache['rows'] is None:
                if initial_filter_acompanhamentos:
                    print("[LOAD_ROWS] Carregando acompanhamentos de terceiros (modo dedicado)")
                    data_cache['rows'] = fetch_acompanhamentos_terceiros()
                else:
                    print("[LOAD_ROWS] Carregando lista completa de processos")
                    data_cache['rows'] = fetch_processes()
            return data_cache['rows'] or []
        
        # Função para extrair opções únicas dos dados
        def get_filter_options():
            """
            Extrai valores únicos de cada campo para popular os dropdowns de filtros.
            
            Para o filtro de casos, extrai de cases_list dos processos (não do Firestore),
            garantindo que apenas casos realmente vinculados apareçam como opções.
            
            CORREÇÃO: Adiciona validação e sanitização para prevenir erros de ValueError.
            """
            try:
                all_rows = load_rows()
                print(f"[FILTER_OPTIONS] Processando {len(all_rows)} rows para opções de filtro")
                
                # Função auxiliar para sanitizar valores de lista
                def sanitize_list_values(values_list, field_name):
                    """Sanitiza valores de uma lista, removendo inválidos."""
                    sanitized = set()
                    for val in values_list:
                        try:
                            if val is None:
                                continue
                            val_str = str(val).strip()
                            if val_str:
                                sanitized.add(val_str)
                        except Exception as e:
                            print(f"[FILTER_OPTIONS] ⚠️  Valor inválido ignorado em {field_name}: '{val}' - {e}")
                            continue
                    return sorted(sanitized)
                
                # Área - validação simples
                areas = []
                for r in all_rows:
                    try:
                        area = r.get('area', '')
                        if area and str(area).strip():
                            areas.append(str(area).strip())
                    except Exception as e:
                        print(f"[FILTER_OPTIONS] ⚠️  Erro ao processar área: {e}")
                        continue
                
                # Casos - usa função dedicada com validação
                cases = build_case_filter_options(all_rows)
                
                # Clientes - sanitização
                clients = []
                for r in all_rows:
                    try:
                        clients_list = r.get('clients_list', []) or []
                        for c in clients_list:
                            if c and str(c).strip():
                                clients.append(str(c).strip())
                    except Exception as e:
                        print(f"[FILTER_OPTIONS] ⚠️  Erro ao processar clientes: {e}")
                        continue
                
                # Parte (mesmo que clientes)
                parte = clients.copy()
                
                # Parte contrária - sanitização
                opposing = []
                for r in all_rows:
                    try:
                        opposing_list = r.get('opposing_list', []) or []
                        for o in opposing_list:
                            if o and str(o).strip():
                                opposing.append(str(o).strip())
                    except Exception as e:
                        print(f"[FILTER_OPTIONS] ⚠️  Erro ao processar parte contrária: {e}")
                        continue
                
                # Status - sanitização
                statuses = []
                for r in all_rows:
                    try:
                        status = r.get('status', '')
                        if status and str(status).strip():
                            statuses.append(str(status).strip())
                    except Exception as e:
                        print(f"[FILTER_OPTIONS] ⚠️  Erro ao processar status: {e}")
                        continue
                
                # Constrói dicionário de opções com validação final
                options = {
                    'area': [''] + sanitize_list_values(areas, 'area'),
                    'cases': cases,  # Já sanitizado em build_case_filter_options
                    'clients': [''] + sanitize_list_values(clients, 'clients'),
                    'parte': [''] + sanitize_list_values(parte, 'parte'),
                    'opposing': [''] + sanitize_list_values(opposing, 'opposing'),
                    'status': [''] + sanitize_list_values(statuses, 'status')
                }
                
                print(f"[FILTER_OPTIONS] ✓ Opções construídas: área={len(options['area'])}, casos={len(options['cases'])}, clientes={len(options['clients'])}, status={len(options['status'])}")
                return options
                
            except Exception as exc:
                print(f"[FILTER_OPTIONS] ❌ Erro crítico ao construir opções de filtro: {exc}")
                import traceback
                traceback.print_exc()
                # Retorna opções vazias em caso de erro crítico
                return {
                    'area': [''],
                    'cases': [''],
                    'clients': [''],
                    'parte': [''],
                    'opposing': [''],
                    'status': ['']
                }
        
        # Filtros discretos em uma linha
        filter_options = get_filter_options()
        filter_selects = {}

        def persist_filter_state():
            """Guarda filtro de caso na sessão do usuário."""
            app.storage.user['processos_filters'] = {'case': filter_case.get('value', '')}

        def reload_case_options():
            """
            Atualiza dropdown de casos com dados mais recentes.
            
            Recarrega processos e reconstrói opções de casos a partir de cases_list
            dos processos, garantindo que novos casos vinculados apareçam no filtro.
            """
            if 'case' in filter_selects:
                # Recarrega processos para obter cases_list atualizado
                all_rows = load_rows(force_reload=True)
                new_options = build_case_filter_options(all_rows)
                filter_selects['case'].options = new_options
                filter_selects['case'].update()
        
        # Função auxiliar para criar filtros discretos
        def create_filter_dropdown(label, options, state_dict, width_class='min-w-[140px]', initial_value='', on_change_callback=None):
            """
            Cria dropdown de filtro com validação de opções.
            
            CORREÇÃO: Valida e sanitiza opções antes de passar para ui.select
            para prevenir erros de ValueError.
            """
            try:
                # Validação: garante que options é uma lista
                if not isinstance(options, list):
                    print(f"[FILTER_DROPDOWN] ⚠️  Opções não são lista para '{label}': {type(options)}")
                    options = ['']
                
                # Sanitização: remove valores inválidos
                valid_options = []
                for opt in options:
                    try:
                        # Converte para string e valida
                        if opt is None:
                            continue
                        
                        opt_str = str(opt).strip()
                        
                        # Ignora strings vazias (exceto a primeira que é permitida)
                        if not opt_str and len(valid_options) > 0:
                            continue
                        
                        # Validação adicional: verifica se não é número float problemático
                        # NiceGUI pode rejeitar valores como "1.5" em alguns contextos
                        try:
                            float_val = float(opt_str)
                            # Se for número puro sem texto, pode causar problema
                            # Mas se tiver texto junto (ex: "1.5 - Bituva / 2020"), é válido
                            if opt_str.replace('.', '').replace('-', '').replace(' ', '').isdigit():
                                # Número puro - pode ser problemático, mas vamos tentar
                                print(f"[FILTER_DROPDOWN] ⚠️  Valor numérico puro em '{label}': '{opt_str}'")
                        except (ValueError, TypeError):
                            # Não é número, continua normalmente
                            pass
                        
                        # Adiciona opção válida
                        valid_options.append(opt_str if opt_str else '')
                        
                    except Exception as opt_exc:
                        print(f"[FILTER_DROPDOWN] ⚠️  Opção inválida ignorada em '{label}': '{opt}' - {opt_exc}")
                        continue
                
                # Garante que há pelo menos uma opção vazia
                if not valid_options or (valid_options and valid_options[0] != ''):
                    valid_options = [''] + valid_options
                
                # Valida initial_value
                if initial_value and initial_value not in valid_options:
                    print(f"[FILTER_DROPDOWN] ⚠️  Valor inicial '{initial_value}' não está nas opções válidas para '{label}', usando ''")
                    initial_value = ''
                
                print(f"[FILTER_DROPDOWN] Criando dropdown '{label}' com {len(valid_options)} opções válidas")
                
                # Cria select com opções validadas
                select = ui.select(valid_options, label=label, value=initial_value).props('clearable dense outlined').classes(width_class)
                
                # Estilo discreto e minimalista
                select.style('font-size: 12px; border-color: #d1d5db;')
                select.classes('filter-select')
                
                # Callback para atualizar filtro quando valor mudar
                def on_filter_change():
                    try:
                        state_dict['value'] = select.value if select.value else ''
                        if on_change_callback:
                            on_change_callback()
                        refresh_table()
                    except Exception as change_exc:
                        print(f"[FILTER_DROPDOWN] ⚠️  Erro no callback de mudança para '{label}': {change_exc}")
                
                # Registrar callback
                select.on('update:model-value', on_filter_change)
                return select
                
            except Exception as exc:
                print(f"[FILTER_DROPDOWN] ❌ Erro crítico ao criar dropdown '{label}': {exc}")
                import traceback
                traceback.print_exc()
                # Retorna select vazio em caso de erro
                try:
                    return ui.select([''], label=label, value='').props('clearable dense outlined').classes(width_class)
                except:
                    # Se até isso falhar, retorna None e deixa quebrar (melhor que erro silencioso)
                    return None
        
        # Barra de pesquisa - responsiva
        with ui.row().classes('w-full items-center gap-2 sm:gap-4 mb-4 flex-wrap'):
            # Campo de busca com ícone de lupa
            with ui.input(placeholder='Pesquisar processos por título, número...').props('outlined dense clearable').classes('flex-grow w-full sm:w-auto sm:max-w-xl') as search_input:
                with search_input.add_slot('prepend'):
                    ui.icon('search').classes('text-gray-400')
            
            # Callback para atualizar pesquisa quando valor mudar
            def on_search_change():
                search_term['value'] = search_input.value if search_input.value else ''
                refresh_table()
            
            search_input.on('update:model-value', on_search_change)
            
            # Botões de ação - responsivos
            ui.button('+ Novo Processo', on_click=lambda: open_process_modal()).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')
            ui.button('+ Novo Processo Futuro', icon='schedule', on_click=lambda: open_future_process_modal()).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')
            
            # Modal de acompanhamento de terceiros
            from ..modais.modal_acompanhamento_terceiros import render_third_party_monitoring_dialog
            third_party_dialog, open_third_party_modal = render_third_party_monitoring_dialog(
                on_success=on_process_saved
            )
            
            ui.button('+ Novo Acompanhamento de Terceiro', icon='link', on_click=lambda: open_third_party_modal()).props('color=primary').classes('whitespace-nowrap w-full sm:w-auto')
            
            ui.button('+ Novo Protocolo', icon='history', on_click=lambda: open_protocol_modal()).props('outlined color=primary').classes('whitespace-nowrap w-full sm:w-auto')
            
            # Botão para acessar a visualização "Acesso aos Processos"
            ui.button('Acesso aos Processos', icon='lock_open', on_click=lambda: ui.navigate.to('/processos/acesso')).props('flat').classes('w-full sm:w-auto')
        
        # Linha de filtros - responsivo
        with ui.row().classes('w-full items-center mb-4 gap-3 flex-wrap'):
            ui.label('Filtros:').classes('text-gray-600 font-medium text-sm w-full sm:w-auto')
            # Criar filtros com rótulos limpos (sem ícones em inglês) - responsivos
            filter_selects['area'] = create_filter_dropdown('Área', filter_options['area'], filter_area, 'w-full sm:w-auto min-w-[100px] sm:min-w-[120px]')
            filter_selects['case'] = create_filter_dropdown(
                'Casos',
                filter_options['cases'],
                filter_case,
                'w-full sm:w-auto min-w-[100px] sm:min-w-[140px]',
                initial_value=filter_case['value'],
                on_change_callback=persist_filter_state,
            )
            filter_selects['client'] = create_filter_dropdown('Clientes', filter_options['clients'], filter_client, 'w-full sm:w-auto min-w-[100px] sm:min-w-[140px]')
            filter_selects['parte'] = create_filter_dropdown('Parte', filter_options['parte'], filter_parte, 'w-full sm:w-auto min-w-[100px] sm:min-w-[140px]')
            filter_selects['opposing'] = create_filter_dropdown('Parte Contrária', filter_options['opposing'], filter_opposing, 'w-full sm:w-auto min-w-[100px] sm:min-w-[170px]')
            filter_selects['status'] = create_filter_dropdown('Status', filter_options['status'], filter_status, 'w-full sm:w-auto min-w-[100px] sm:min-w-[140px]', initial_status_filter)
            
            # Aplica filtro APENAS se vier explicitamente da URL do painel (filter=futuro_previsto)
            # Se não houver parâmetro na URL, visualização padrão mostra TODOS os processos
            if initial_status_filter:
                # Caso especial: filtro veio da URL do painel, aplica após renderização
                ui.run_javascript('''
                    (function() {
                        setTimeout(function() {
                            // Encontra o select de Status e aplica o valor
                            const allSelects = document.querySelectorAll('.q-select, select');
                            allSelects.forEach(function(selectEl) {
                                const field = selectEl.closest('.q-field');
                                if (field) {
                                    const label = field.querySelector('.q-field__label');
                                    if (label && label.textContent && label.textContent.trim() === 'Status') {
                                        // Tenta atualizar via Vue
                                        const vueInstance = selectEl.__vueParentComponent || 
                                                           (selectEl.parentElement && selectEl.parentElement.__vueParentComponent);
                                        if (vueInstance && vueInstance.setProps) {
                                            vueInstance.setProps({ modelValue: 'Futuro/Previsto' });
                                        }
                                        // Dispara evento de mudança
                                        const event = new Event('update:model-value', { bubbles: true });
                                        selectEl.dispatchEvent(event);
                                    }
                                }
                            });
                        }, 800);
                    })();
                ''')
                # Aplica filtro no estado Python também
                ui.timer(0.3, lambda: refresh_table(), once=True)
            
            # Botão limpar filtros
            def clear_filters():
                filter_area['value'] = ''
                filter_case['value'] = ''
                filter_client['value'] = ''
                filter_parte['value'] = ''
                filter_opposing['value'] = ''
                filter_status['value'] = ''
                search_term['value'] = ''
                # Limpar valores dos selects
                filter_selects['area'].value = ''
                filter_selects['case'].value = ''
                filter_selects['client'].value = ''
                filter_selects['parte'].value = ''
                filter_selects['opposing'].value = ''
                filter_selects['status'].value = ''
                search_input.value = ''
                persist_filter_state()
                refresh_table()
            
            ui.button('Limpar', icon='clear_all', on_click=clear_filters).props('flat dense').classes('text-xs text-gray-600 w-full sm:w-auto')
        
        # Função de filtragem
        def filter_rows(rows):
            """
            Aplica filtros aos processos.
            
            IMPORTANTE: Se nenhum filtro estiver aplicado, retorna TODOS os processos.
            Não exclui processos com status vazio ou None quando nenhum filtro está ativo.
            """
            filtered = rows
            
            # Debug: log de filtros ativos
            active_filters = []
            if search_term['value']:
                active_filters.append(f"pesquisa='{search_term['value']}'")
            if filter_area['value']:
                active_filters.append(f"área='{filter_area['value']}'")
            if filter_case['value']:
                active_filters.append(f"caso='{filter_case['value']}'")
            if filter_client['value']:
                active_filters.append(f"cliente='{filter_client['value']}'")
            if filter_parte['value']:
                active_filters.append(f"parte='{filter_parte['value']}'")
            if filter_opposing['value']:
                active_filters.append(f"parte_contrária='{filter_opposing['value']}'")
            if filter_status['value']:
                active_filters.append(f"status='{filter_status['value']}'")
            
            if active_filters:
                print(f"[FILTER_ROWS] Aplicando filtros: {', '.join(active_filters)}")
                print(f"[FILTER_ROWS] Total de registros antes dos filtros: {len(filtered)}")
            else:
                print(f"[FILTER_ROWS] Nenhum filtro ativo - retornando todos os {len(filtered)} registros")
            
            # Filtro de pesquisa (título) - usa title_raw para não incluir indentação
            if search_term['value']:
                term = search_term['value'].lower()
                filtered = [r for r in filtered if term in (r.get('title_raw') or r.get('title') or '').lower()]
            
            # Filtro de área
            if filter_area['value']:
                area_filter_value = filter_area['value'].strip()
                filtered = [
                    r for r in filtered 
                    if (r.get('area') or '').strip() == area_filter_value
                ]
            
            # Filtro de casos
            if filter_case['value']:
                """
                Filtra processos e acompanhamentos de terceiros por caso vinculado.
                
                Lógica de filtragem:
                1. Normaliza valor do filtro (remove espaços, converte para minúsculas)
                2. Para cada processo, verifica se algum caso em cases_list corresponde
                3. Usa dupla verificação:
                   - Igualdade exata (case-insensitive): comparação direta
                   - Substring matching: verifica se filtro está contido no caso
                4. Processos com múltiplos casos aparecem se qualquer caso corresponder
                5. Acompanhamentos de terceiros são filtrados pela mesma lógica
                
                Suporta:
                - Processos normais com cases_list
                - Acompanhamentos de terceiros com cases_list
                - Múltiplos casos por processo
                - Valores None/vazios em cases_list (tratados como lista vazia)
                """
                case_filter_value = filter_case['value'].strip()
                
                # Validação: se valor vazio após strip, não aplica filtro
                if not case_filter_value:
                    print(f"[FILTER_ROWS] Filtro de casos vazio após normalização, ignorando")
                else:
                    filtered_before = len(filtered)
                    
                    # Lista para armazenar processos que passaram no filtro
                    filtered_new = []
                    
                    # Itera sobre cada processo/acompanhamento
                    for r in filtered:
                        # Obtém lista de casos (trata None como lista vazia)
                        cases_list = r.get('cases_list') or []
                        
                        # Verifica se algum caso corresponde ao filtro
                        # Dupla verificação: igualdade exata OU substring matching
                        matches = any(
                            # Igualdade exata (case-insensitive)
                            str(c).strip().lower() == case_filter_value.lower() or 
                            # Substring matching (para compatibilidade com variações)
                            case_filter_value.lower() in str(c).strip().lower()
                            for c in cases_list if c  # Ignora valores None/vazios
                        )
                        
                        # Se algum caso corresponder, mantém o processo
                        if matches:
                            filtered_new.append(r)
                    
                    # Atualiza lista filtrada
                    filtered = filtered_new
                    filtered_after = len(filtered)
                    
                    # Log de debug: mostra quantos registros foram filtrados
                    print(f"[FILTER_ROWS] Filtro por caso '{case_filter_value}': {filtered_before} → {filtered_after} registros")
                    
                    # Debug específico: verifica quantos acompanhamentos passaram no filtro
                    acompanhamentos_filtrados = [r for r in filtered if r.get('is_third_party_monitoring')]
                    if acompanhamentos_filtrados:
                        print(f"[FILTER_ROWS] ✓ {len(acompanhamentos_filtrados)} acompanhamento(s) de terceiros passaram no filtro por caso")
                        for acomp in acompanhamentos_filtrados:
                            print(f"  - {acomp.get('title')}: casos={acomp.get('cases_list')}")
                    else:
                        # Log apenas se havia acompanhamentos na lista original
                        acompanhamentos_originais = [r for r in rows if r.get('is_third_party_monitoring')]
                        if acompanhamentos_originais:
                            print(f"[FILTER_ROWS] ⚠️  Nenhum acompanhamento de terceiros passou no filtro por caso '{case_filter_value}'")
            
            # Filtro de clientes
            if filter_client['value']:
                client_filter_value = filter_client['value'].strip()
                filtered = [
                    r for r in filtered 
                    if any(str(c).strip().lower() == client_filter_value.lower() for c in (r.get('clients_list') or []))
                ]
            
            # Filtro de parte
            if filter_parte['value']:
                parte_filter_value = filter_parte['value'].strip()
                filtered = [
                    r for r in filtered 
                    if any(str(c).strip().lower() == parte_filter_value.lower() for c in (r.get('clients_list') or []))
                ]
            
            # Filtro de parte contrária
            if filter_opposing['value']:
                opposing_filter_value = filter_opposing['value'].strip()
                filtered = [
                    r for r in filtered 
                    if any(str(c).strip().lower() == opposing_filter_value.lower() for c in (r.get('opposing_list') or []))
                ]
            
            # Filtro de status
            # CORREÇÃO: Só filtra se houver valor selecionado E se o valor não for vazio
            if filter_status['value'] and filter_status['value'].strip():
                status_filter = filter_status['value'].strip()
                filtered = [r for r in filtered if (r.get('status') or '').strip() == status_filter]
            
            # Debug: log final
            if active_filters:
                print(f"[FILTER_ROWS] Total de registros após filtros: {len(filtered)}")
            
            # DEBUG: Verificar se processo "RECURSO ESPECIAL" está sendo filtrado
            recurso_especial_filtered = [r for r in filtered if 'RECURSO ESPECIAL' in (r.get('title') or '').upper()]
            if recurso_especial_filtered:
                print(f"[DEBUG FILTER] 'RECURSO ESPECIAL' está na lista filtrada ({len(filtered)} processos)")
            else:
                # Verificar se estava na lista original
                recurso_especial_original = [r for r in rows if 'RECURSO ESPECIAL' in (r.get('title') or '').upper()]
                if recurso_especial_original:
                    print(f"[DEBUG FILTER] ⚠️  'RECURSO ESPECIAL' foi FILTRADO FORA!")
                    print(f"   Status do processo: '{recurso_especial_original[0].get('status')}'")
                    print(f"   Filtro de status aplicado: '{filter_status['value']}'")
            
            return filtered

        # Função para buscar e transformar acompanhamentos em formato de processo
        def fetch_acompanhamentos_terceiros():
            """
            Busca acompanhamentos de terceiros e transforma em formato compatível com tabela de processos.
            
            Returns:
                Lista de dicionários no formato de row_data para a tabela
            """
            try:
                from ..database import obter_todos_acompanhamentos
                from ....core import get_clients_list, get_opposing_parties_list, get_cases_list
                
                acompanhamentos_raw = obter_todos_acompanhamentos()
                print(f"[FETCH_ACOMPANHAMENTOS] Total de acompanhamentos encontrados: {len(acompanhamentos_raw)}")
                
                # Carrega listas de pessoas para buscar siglas/display_names
                clients_list = get_clients_list()
                opposing_list = get_opposing_parties_list()
                all_people = clients_list + opposing_list
                
                rows = []
                
                for acomp in acompanhamentos_raw:
                    # Extrai e formata clientes
                    client_id = acomp.get('client_id', '')
                    client_name = acomp.get('client_name', '')
                    clients_raw = [client_id] if client_id else []
                    if client_name and client_name not in clients_raw:
                        clients_raw.append(client_name)
                    clients_list = _format_names_list(clients_raw, all_people)
                    
                    # Extrai e formata partes contrárias
                    third_party_name = acomp.get('third_party_name') or acomp.get('pessoa_ou_entidade_acompanhada', '')
                    opposing_list = [third_party_name] if third_party_name else []
                    
                    # Extrai casos vinculados
                    # CORREÇÃO: Adiciona validação e tratamento de erros
                    cases_list = []
                    try:
                        cases_raw = acomp.get('cases') or []
                        if isinstance(cases_raw, list):
                            for c in cases_raw:
                                try:
                                    if c is None:
                                        continue
                                    case_str = str(c).strip()
                                    if case_str:
                                        cases_list.append(case_str)
                                except Exception as case_exc:
                                    print(f"[FETCH_ACOMPANHAMENTOS] ⚠️  Erro ao processar caso '{c}': {case_exc}")
                                    continue
                        else:
                            try:
                                if cases_raw:
                                    case_str = str(cases_raw).strip()
                                    if case_str:
                                        cases_list = [case_str]
                            except Exception as single_exc:
                                print(f"[FETCH_ACOMPANHAMENTOS] ⚠️  Erro ao processar caso único '{cases_raw}': {single_exc}")
                                cases_list = []
                    except Exception as cases_exc:
                        print(f"[FETCH_ACOMPANHAMENTOS] ⚠️  Erro ao extrair casos: {cases_exc}")
                        cases_list = []
                    
                    # Processa data de abertura
                    data_abertura_raw = acomp.get('start_date') or acomp.get('data_de_abertura') or ''
                    data_abertura_display = data_abertura_raw
                    data_abertura_sort = ''
                    
                    if data_abertura_raw:
                        try:
                            data_abertura_raw = data_abertura_raw.strip()
                            if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                                data_abertura_display = data_abertura_raw
                                data_abertura_sort = f"{data_abertura_raw}/00/00"
                            elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                                partes = data_abertura_raw.split('/')
                                if len(partes) == 2:
                                    data_abertura_display = data_abertura_raw
                                    data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
                            elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                                partes = data_abertura_raw.split('/')
                                if len(partes) == 3:
                                    data_abertura_display = data_abertura_raw
                                    data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
                        except Exception:
                            data_abertura_display = data_abertura_raw
                    
                    # Título do acompanhamento - busca em múltiplos campos para compatibilidade
                    title = (
                        acomp.get('title') or 
                        acomp.get('process_title') or 
                        acomp.get('titulo') or 
                        'Acompanhamento de Terceiro'
                    )
                    print(f"[FETCH_ACOMPANHAMENTOS] Acompanhamento ID {acomp.get('_id')}: título='{title}'")
                    
                    # Status
                    status = acomp.get('status') or 'ativo'
                    
                    # Cria row_data no formato esperado pela tabela
                    # REGRA: Acompanhamentos mostram "NA" em Clientes e Parte Contrária
                    row_data = {
                        '_id': acomp.get('_id') or acomp.get('id'),
                        'data_abertura': data_abertura_display,
                        'data_abertura_sort': data_abertura_sort,
                        'title': title,
                        'title_raw': title,
                        'number': acomp.get('process_number') or acomp.get('number') or '',
                        # REGRA: Clientes e Parte Contrária são "NA" para acompanhamentos
                        'clients_list': ['NA'],  # Sempre "NA" para acompanhamentos
                        'opposing_list': ['NA'],  # Sempre "NA" para acompanhamentos
                        # Parte Ativa/Passiva são usadas internamente, mas não aparecem como Clientes/Parte Contrária
                        'cases_list': cases_list,
                        'system': acomp.get('system') or '',
                        'status': status,
                        'area': acomp.get('area') or '',
                        'link': acomp.get('link_do_processo') or acomp.get('link') or '',
                        'is_third_party_monitoring': True,  # Marca como acompanhamento para aplicar cores
                    }
                    
                    print(f"[FETCH_ACOMPANHAMENTOS] Row criada - Link: '{row_data.get('link')}', Número: '{row_data.get('number')}'")
                    
                    rows.append(row_data)
                
                print(f"[FETCH_ACOMPANHAMENTOS] Total de rows criadas: {len(rows)}")
                return rows
                
            except Exception as e:
                print(f"[FETCH_ACOMPANHAMENTOS] Erro ao buscar acompanhamentos: {e}")
                import traceback
                traceback.print_exc()
                return []
        
        @ui.refreshable
        def render_table():
            """
            Renderiza tabela de processos.
            
            VISUALIZAÇÃO PADRÃO: Mostra TODOS os processos cadastrados.
            Filtros são aplicados apenas quando o usuário seleciona opções nos dropdowns.
            Se filtro de acompanhamentos estiver ativo na URL, mostra apenas acompanhamentos.
            """
            rows = load_rows()
            
            # DEBUG: Verificar se RECURSO ESPECIAL está na lista retornada por fetch_processes()
            recurso_em_fetch = [r for r in rows if 'RECURSO ESPECIAL' in (r.get('title') or '').upper()]
            if recurso_em_fetch:
                print(f"[DEBUG RENDER] ✓ RECURSO ESPECIAL encontrado em fetch_processes()")
                print(f"  Status: {recurso_em_fetch[0].get('status')}")
                print(f"  Título: {recurso_em_fetch[0].get('title')}")
            else:
                print(f"[DEBUG RENDER] ❌ RECURSO ESPECIAL NÃO encontrado em fetch_processes()")
                print(f"  Total de processos retornados: {len(rows)}")
            
            # Debug: mostra total de processos
            print(f"[RENDER_TABLE] Total de registros carregados: {len(rows)}")
            
            # Verifica se há acompanhamentos na lista (se não estiver no modo filtro)
            if not initial_filter_acompanhamentos:
                acompanhamentos_count = sum(1 for r in rows if r.get('is_third_party_monitoring'))
                if acompanhamentos_count > 0:
                    print(f"[RENDER_TABLE] {acompanhamentos_count} acompanhamento(s) de terceiros na lista (misturados com processos)")
            else:
                print(f"[RENDER_TABLE] Modo filtro: mostrando apenas {len(rows)} acompanhamento(s) de terceiros")

            try:
                filtered_rows = filter_rows(rows)
            except Exception as exc:
                print(f"[RENDER_TABLE] Erro ao aplicar filtros: {exc}")
                ui.notify('Não foi possível aplicar filtros. Exibindo todos os processos.', type='warning')
                filtered_rows = rows

            print(f"[RENDER_TABLE] Total de registros após filtros: {len(filtered_rows)}")
            
            if not filtered_rows:
                with ui.card().classes('w-full p-8 flex justify-center items-center'):
                    ui.label('Nenhum processo encontrado para os filtros atuais.').classes('text-gray-400 italic')
                return

            # Slots customizados
            table = ui.table(columns=COLUMNS, rows=filtered_rows, row_key='_id', pagination={'rowsPerPage': 20}).classes('w-full')
            
            # Handler para clique no título (abre modal de edição)
            def handle_title_click(e):
                clicked_row = e.args
                if clicked_row and '_id' in clicked_row:
                    row_id = clicked_row['_id']
                    
                    # Verificar se é um acompanhamento de terceiro
                    is_third_party = clicked_row.get('is_third_party_monitoring', False)
                    
                    if is_third_party:
                        # É um acompanhamento de terceiro - abrir modal de acompanhamento
                        print(f"[TITLE_CLICK] Abrindo modal de edição para acompanhamento ID: {row_id}")
                        try:
                            from ..database import obter_acompanhamento_por_id
                            acompanhamento = obter_acompanhamento_por_id(row_id)
                            
                            if acompanhamento:
                                # Abrir modal de acompanhamento em modo edição
                                open_third_party_modal(monitoring_id=row_id)
                                print(f"[TITLE_CLICK] ✓ Modal de acompanhamento aberto com sucesso")
                            else:
                                ui.notify('Acompanhamento não encontrado. Pode ter sido deletado.', type='negative')
                                print(f"[TITLE_CLICK] ❌ Acompanhamento não encontrado: {row_id}")
                        except Exception as ex:
                            print(f"[TITLE_CLICK] Erro ao abrir modal de acompanhamento: {ex}")
                            import traceback
                            traceback.print_exc()
                            ui.notify(f'Erro ao abrir acompanhamento: {str(ex)}', type='negative')
                    else:
                        # É um processo normal - abrir modal de processo
                        process_id = row_id
                        all_processes = get_processes_list()
                        for idx, proc in enumerate(all_processes):
                            if proc.get('_id') == process_id:
                                open_process_modal(idx)
                                break
            
            table.on('titleClick', handle_title_click)
            
            # JavaScript para aplicar estilos nas linhas
            # Lê atributos data-* da primeira célula (data_abertura) e aplica na row pai
            def apply_row_styles():
                """
                Aplica estilos nas linhas de processos futuros e acompanhamentos de terceiros.
                
                A identificação é feita através dos atributos data-* na primeira célula:
                - data-is-third-party: indica se é acompanhamento
                - data-status: status do processo (Futuro/Previsto)
                """
                ui.run_javascript('''
                    (function() {
                        function applyStyles() {
                            const table = document.querySelector('.q-table tbody');
                            if (!table) return;
                            
                            const rows = table.querySelectorAll('tr');
                            rows.forEach(function(row) {
                                // Busca a primeira célula (data_abertura) que tem os atributos data-*
                                const firstCell = row.querySelector('td:first-child');
                                if (!firstCell) return;
                                
                                // Lê atributos da célula
                                const isThirdParty = firstCell.getAttribute('data-is-third-party') === 'true' || 
                                                    firstCell.getAttribute('data-is-third-party') === true;
                                const status = firstCell.getAttribute('data-status') || '';
                                
                                // Remove estilos anteriores
                                row.removeAttribute('data-status');
                                row.removeAttribute('data-type');
                                row.classList.remove('future-process-row');
                                row.classList.remove('third-party-monitoring-row');
                                
                                // Acompanhamentos de terceiros (prioridade sobre processos futuros)
                                if (isThirdParty) {
                                    row.setAttribute('data-type', 'third_party_monitoring');
                                    row.classList.add('third-party-monitoring-row');
                                }
                                // Processos futuros
                                else if (status === 'Futuro/Previsto') {
                                    row.setAttribute('data-status', 'Futuro/Previsto');
                                    row.classList.add('future-process-row');
                                }
                                
                                // Fallback: detecta processos futuros pelo badge de status visível
                                // (caso o atributo data-status não esteja disponível)
                                if (!row.hasAttribute('data-status') && !row.hasAttribute('data-type')) {
                                    const cells = row.querySelectorAll('td');
                                    let hasFutureBadge = false;
                                    cells.forEach(function(cell) {
                                        const badge = cell.querySelector('.q-badge');
                                        if (badge && badge.textContent.trim() === 'Futuro/Previsto') {
                                            hasFutureBadge = true;
                                        }
                                    });
                                    
                                    if (hasFutureBadge) {
                                        row.setAttribute('data-status', 'Futuro/Previsto');
                                        row.classList.add('future-process-row');
                                    }
                                }
                            });
                        }
                        
                        // Executa após renderização inicial
                        setTimeout(applyStyles, 400);
                        
                        // Observa mudanças na tabela (pagination, filtros, etc)
                        const observer = new MutationObserver(applyStyles);
                        const tableContainer = document.querySelector('.q-table');
                        if (tableContainer) {
                            observer.observe(tableContainer, { childList: true, subtree: true });
                        }
                        
                        // Re-aplica estilos após eventos de paginação/filtros
                        const paginationArea = document.querySelector('.q-table__bottom');
                        if (paginationArea) {
                            paginationArea.addEventListener('click', function() {
                                setTimeout(applyStyles, 300);
                            });
                        }
                    })();
                ''')
            
            apply_row_styles()
            
            # Slot para data de abertura - exibe DD/MM/AAAA
            # Adiciona atributos data-* na célula para permitir identificação da row
            table.add_slot('body-cell-data_abertura', '''
                <q-td :props="props" 
                      style="text-align: center; padding: 8px 12px; vertical-align: middle;"
                      :data-row-id="props.row._id"
                      :data-is-third-party="props.row.is_third_party_monitoring || false"
                      :data-status="props.row.status || ''">
                    <span v-if="props.row.data_abertura" class="text-xs text-gray-700 font-medium">{{ props.row.data_abertura }}</span>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para área com chips coloridos (pastel)
            table.add_slot('body-cell-area', BODY_SLOT_AREA)
            
            # Slot para título - clicável para abrir modal de edição
            table.add_slot('body-cell-title', '''
                <q-td :props="props" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word; max-width: 280px; padding: 8px 12px; vertical-align: middle;">
                    <span class="text-sm cursor-pointer font-medium" 
                          style="line-height: 1.4; color: #223631;"
                          @click="$parent.$emit('titleClick', props.row)">
                        {{ props.value }}
                    </span>
                </q-td>
            ''')
            
            # Slot para status (idêntico ao módulo Casos)
            table.add_slot('body-cell-status', BODY_SLOT_STATUS)
            
            # Slot para clientes - exibe múltiplos verticalmente em espaço compacto
            # REGRA: Acompanhamentos mostram "NA" em vez de lista vazia
            table.add_slot('body-cell-clients', '''
                <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 8px 8px;">
                    <div v-if="props.row.clients_list && props.row.clients_list.length > 0">
                        <div v-if="props.row.clients_list[0] === 'NA'" class="text-xs text-gray-500 italic font-medium">
                            NA
                        </div>
                        <div v-else class="flex flex-col gap-0.5">
                            <div v-for="(client, index) in props.row.clients_list" :key="index" class="text-xs text-gray-700 leading-tight font-medium" style="word-wrap: break-word; overflow-wrap: break-word;">
                                {{ client }}
                            </div>
                        </div>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para parte contrária - exibe múltiplos verticalmente em espaço compacto
            # REGRA: Acompanhamentos mostram "NA" em vez de lista vazia
            table.add_slot('body-cell-opposing', '''
                <q-td :props="props" style="white-space: normal; vertical-align: middle; max-width: 100px; padding: 8px 8px;">
                    <div v-if="props.row.opposing_list && props.row.opposing_list.length > 0">
                        <div v-if="props.row.opposing_list[0] === 'NA'" class="text-xs text-gray-500 italic font-medium">
                            NA
                        </div>
                        <div v-else class="flex flex-col gap-0.5">
                            <div v-for="(opposing, index) in props.row.opposing_list" :key="index" class="text-xs text-gray-700 leading-tight font-medium" style="word-wrap: break-word; overflow-wrap: break-word;">
                                {{ opposing }}
                            </div>
                        </div>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para casos - exibe em linha única com ajuste automático
            table.add_slot('body-cell-cases', '''
                <q-td :props="props" style="vertical-align: middle; padding: 8px 12px;">
                    <div v-if="props.row.cases_list && props.row.cases_list.length > 0" style="white-space: normal; word-wrap: break-word; overflow-wrap: break-word;">
                        <span v-for="(caso, index) in props.row.cases_list" :key="index" class="text-xs text-gray-700 font-medium">
                            {{ caso }}<span v-if="index < props.row.cases_list.length - 1">, </span>
                        </span>
                    </div>
                    <span v-else class="text-gray-400">—</span>
                </q-td>
            ''')
            
            # Slot para número - hyperlink clicável com ícone de copiar
            # PADRONIZADO: Números com e sem link têm exatamente a mesma aparência visual
            table.add_slot('body-cell-number', '''
                <q-td :props="props" style="vertical-align: middle; padding: 6px 10px;">
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <a v-if="props.row.link && props.value" 
                           :href="props.row.link" 
                           target="_blank" 
                           class="process-number-link"
                           style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; text-decoration: none; font-family: inherit;">
                            {{ props.value }}
                        </a>
                        <span v-else-if="props.value" 
                              class="process-number-text"
                              style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; font-family: inherit;">
                            {{ props.value }}
                        </span>
                        <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
                        <q-btn 
                            v-if="props.value"
                            flat dense round 
                            icon="content_copy" 
                            size="xs" 
                            color="grey"
                            class="ml-1"
                            @click.stop="$parent.$emit('copyNumber', props.value)"
                        >
                            <q-tooltip>Copiar número</q-tooltip>
                        </q-btn>
                    </div>
                </q-td>
            ''')
            
            # Handler para copiar número do processo para área de transferência
            def handle_copy_number(e):
                """
                Copia o número do processo para a área de transferência usando JavaScript.
                Compatível com Chrome, Firefox e Edge.
                """
                numero = e.args
                if numero:
                    # Escapa aspas simples no número para evitar erro de JS
                    numero_escaped = str(numero).replace("'", "\\'")
                    ui.run_javascript(f'''
                        navigator.clipboard.writeText('{numero_escaped}').then(() => {{
                            // Sucesso - notificação já exibida pelo NiceGUI
                        }}).catch(err => {{
                            console.error('Erro ao copiar:', err);
                        }});
                    ''')
                    ui.notify("Número copiado!", type="positive", position="top", timeout=1500)
            
            table.on('copyNumber', handle_copy_number)
        
        render_table_ref['func'] = render_table
        render_table()
