"""Script para listar usuários ativos no Firestore.
Execute:  python scripts/fetch_active_users.py
"""

import json
import os
import sys
from typing import List, Dict

# Corrige ausência de packages_distributions em Python <3.10
import importlib.metadata as _ilm

if not hasattr(_ilm, "packages_distributions"):
    def _dummy_packages_distributions():
        """Fallback vazio para evitar erro em libs que esperam a função."""
        return {}

    _ilm.packages_distributions = _dummy_packages_distributions  # type: ignore

    # Garante que outros módulos que importarem depois vejam o patch
    sys.modules["importlib.metadata"].packages_distributions = _dummy_packages_distributions  # type: ignore

# Garante que a pasta raiz do projeto esteja no sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from mini_erp.firebase_config import get_db


def get_active_users() -> List[Dict]:
    """Retorna lista de usuários com status ativo.

    Estrutura esperada do documento `users`:
      - name  (str)
      - email (str)
      - status (str)   -> 'active' | 'inactive'
        ou
      - active (bool)  -> True | False
    """
    db = get_db()
    users_ref = db.collection("users")

    # Primeiro tenta filtrar pelo campo `status` == 'active'
    query = users_ref.where("status", "==", "active")
    docs = list(query.stream())

    # Caso não haja resultados, tenta pelo campo booleano `active` == True
    if not docs:
        query = users_ref.where("active", "==", True)
        docs = list(query.stream())

    # Se ainda vazio, busca todos os documentos (pode não haver campo de status)
    if not docs:
        docs = list(users_ref.stream())

    result: List[Dict] = []
    for doc in docs:
        data = doc.to_dict() or {}
        result.append(
            {
                "name": data.get("name") or data.get("full_name") or "(sem nome)",
                "email": data.get("email") or "-",
                "status": data.get("status", "active" if data.get("active", True) else "inactive"),
            }
        )

    # Ordena alfabeticamente para leitura fácil
    result.sort(key=lambda x: x["name"].lower())
    return result


if __name__ == "__main__":
    users = get_active_users()
    print(json.dumps(users, ensure_ascii=False, indent=2))
