import os
import sys
from typing import Dict, List

# Garante que o diretório do projeto esteja no sys.path ao executar via CLI
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from mini_erp.core import (  # noqa: E402
    get_db,
    get_processes_list,
    get_cases_list,
    get_client_id_by_name,
    get_client_name_by_id,
    invalidate_cache,
    sync_processes_cases,
    validate_case_process_integrity,
)


def ensure_list(value) -> List[str]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def normalize_title(process: Dict) -> Dict:
    """Normaliza título e title_searchable."""
    updates = {}
    title = (process.get("title") or process.get("titulo") or "").strip()
    if not title:
        return updates

    if process.get("title") != title:
        updates["title"] = title
    if process.get("titulo") != title:
        updates["titulo"] = title

    title_searchable = title.lower()
    if process.get("title_searchable") != title_searchable:
        updates["title_searchable"] = title_searchable
    return updates


def rebuild_case_links(process: Dict, cases_by_slug: Dict[str, Dict], cases_by_title: Dict[str, str]) -> Dict:
    updates = {}

    case_ids = ensure_list(process.get("case_ids"))
    case_ids = [cid for cid in case_ids if cid in cases_by_slug]

    if not case_ids:
        source_titles = []
        source_titles.extend(ensure_list(process.get("cases")))
        case_title = process.get("case_title")
        if case_title:
            source_titles.append(case_title)
        for title in source_titles:
            slug = cases_by_title.get(title)
            if slug and slug not in case_ids:
                case_ids.append(slug)

    if process.get("case_ids") != case_ids:
        updates["case_ids"] = case_ids

    case_titles = [cases_by_slug[cid]["title"] for cid in case_ids if cases_by_slug.get(cid, {}).get("title")]
    if process.get("cases") != case_titles:
        updates["cases"] = case_titles
    if case_titles and process.get("case_title") != case_titles[0]:
        updates["case_title"] = case_titles[0]

    return updates


def rebuild_client_fields(process: Dict) -> Dict:
    updates = {}
    client_name = process.get("client")

    if not client_name:
        clients_field = ensure_list(process.get("clients"))
        if clients_field:
            client_name = clients_field[0]

    if not client_name and process.get("cliente_id"):
        client_name = get_client_name_by_id(process.get("cliente_id"))

    client_id = process.get("cliente_id") or process.get("client_id")
    if not client_id and client_name:
        client_id = get_client_id_by_name(client_name) or client_name

    if client_id:
        if process.get("cliente_id") != client_id:
            updates["cliente_id"] = client_id
        if process.get("client_id") != client_id:
            updates["client_id"] = client_id
    if client_name:
        if process.get("client") != client_name:
            updates["client"] = client_name
        clients_array = [client_name]
        if process.get("clients") != clients_array:
            updates["clients"] = clients_array

    return updates


def backfill_processes():
    db = get_db()
    processes = get_processes_list()
    cases = get_cases_list()

    cases_by_slug = {case.get("slug"): case for case in cases if case.get("slug")}
    cases_by_title = {case.get("title"): case.get("slug") for case in cases if case.get("title") and case.get("slug")}

    total = len(processes)
    to_update = 0

    for process in processes:
        doc_id = process.get("_id")
        if not doc_id:
            continue

        updates = {}
        updates.update(normalize_title(process))
        updates.update(rebuild_case_links(process, cases_by_slug, cases_by_title))
        updates.update(rebuild_client_fields(process))

        if updates:
            db.collection("processes").document(doc_id).update(updates)
            to_update += 1
            print(f"Atualizado processo {doc_id} -> {list(updates.keys())}")

    if to_update:
        print(f"\nProcessos atualizados: {to_update}/{total}")
        invalidate_cache("processes")
        print("Sincronizando casos...")
        sync_processes_cases()
    else:
        print("Nenhum processo precisava de atualização.")

    print("\nExecutando validação final...")
    stats = validate_case_process_integrity()
    print(stats)


if __name__ == "__main__":
    backfill_processes()
