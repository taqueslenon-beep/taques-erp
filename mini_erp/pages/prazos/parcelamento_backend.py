"""
parcelamento_backend.py - Backend de parcelamento de prazos.

Este arquivo implementa a lógica de negócio (sem UI) para:
- calcular datas de parcelas
- validar configurações
- gerar parcelas em batch (operação atômica)
- CRUD do parcelamento (status, edição de parcela, exclusão do conjunto)

Estrutura esperada no Firestore (coleção: 'prazos'):

- Prazo "pai" (tipo_prazo='parcelado'):
  {
    'titulo': str,
    'responsaveis': [uid],
    'clientes': [id],
    'casos': [id],
    'prazo_fatal': float (timestamp),
    'status': 'pendente'|'concluido',
    'tipo_prazo': 'parcelado',
    'recorrente': False,
    'config_recorrencia': None,
    'total_parcelas': int,
    'numero_parcela_atual': 0,
    'parcela_de': None,
    'intervalo_parcelas': 'semanal'|'quinzenal'|'mensal'|'anual'|'customizado',
    'dias_customizado': int|None,
    'criado_em': float,
    'atualizado_em': float,
    'criado_por': str|None,
  }

- Parcelas (tipo_prazo='parcelado', parcela_de=<id do pai>):
  {
    ...campos base...
    'titulo': '<titulo> [Parcela X/N]',
    'numero_parcela_atual': X (1..N),
    'parcela_de': '<id do pai>',
    'prazo_fatal': float (timestamp calculado),
  }
"""

from __future__ import annotations

import calendar
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


TIPOS_PRAZO_VALIDOS = {"simples", "recorrente", "parcelado"}
INTERVALOS_PARCELAS_VALIDOS = {
    "semanal",
    "quinzenal",
    "mensal",
    "anual",
    "customizado",
}


class ErroParcelamentoPrazo(ValueError):
    """Erro de validação/negócio do parcelamento de prazos."""


def _converter_para_date(data_input: Any) -> date:
    """
    Converte uma entrada (timestamp/date/datetime) para date.

    Args:
        data_input: float/int (timestamp) ou date/datetime

    Returns:
        date

    Raises:
        ErroParcelamentoPrazo: se o valor for inválido
    """
    if isinstance(data_input, date) and not isinstance(data_input, datetime):
        return data_input
    if isinstance(data_input, datetime):
        return data_input.date()
    if isinstance(data_input, (int, float)):
        try:
            return datetime.fromtimestamp(float(data_input)).date()
        except Exception as exc:
            raise ErroParcelamentoPrazo(
                "Data inicial inválida (timestamp)."
            ) from exc
    raise ErroParcelamentoPrazo(
        "Data inicial inválida. Use timestamp, date ou datetime."
    )


def _date_para_timestamp(data: date) -> float:
    """
    Converte date para timestamp (00:00:00).

    Args:
        data: date

    Returns:
        Timestamp (float)
    """
    return datetime.combine(data, datetime.min.time()).timestamp()


def _somar_mes_ajustando_dia(data_base: date, meses: int) -> date:
    """
    Soma meses mantendo o mesmo dia quando possível.

    Se o dia não existir no mês de destino (ex.: 31 em fevereiro),
    ajusta para o último dia do mês.
    """
    ano = data_base.year
    mes = data_base.month + meses
    dia = data_base.day

    while mes > 12:
        ano += 1
        mes -= 12
    while mes < 1:
        ano -= 1
        mes += 12

    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia_ajustado = min(dia, ultimo_dia)
    return date(ano, mes, dia_ajustado)


def _somar_ano_ajustando_dia(data_base: date, anos: int) -> date:
    """
    Soma anos mantendo o mesmo mês/dia quando possível.

    Trata 29/02 em anos não bissextos ajustando para 28/02.
    """
    ano = data_base.year + anos
    mes = data_base.month
    dia = data_base.day

    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia_ajustado = min(dia, ultimo_dia)
    return date(ano, mes, dia_ajustado)


def calcular_proxima_data_parcela(
    data_base: Any,
    intervalo: str,
    dias_customizado: Optional[int] = None,
) -> date:
    """
    Calcula a próxima data baseada no intervalo informado.

    Regras:
    - semanal: +7 dias
    - quinzenal: +15 dias
    - mensal: +1 mês (mesmo dia, ajusta se não existir)
    - anual: +1 ano (ajusta 29/02 quando necessário)
    - customizado: +dias_customizado
    """
    data = _converter_para_date(data_base)
    intervalo_norm = (intervalo or "").strip().lower()

    if intervalo_norm not in INTERVALOS_PARCELAS_VALIDOS:
        raise ErroParcelamentoPrazo(
            "Intervalo inválido. Use: semanal, quinzenal, mensal, "
            "anual ou customizado."
        )

    if intervalo_norm == "semanal":
        return data + timedelta(days=7)
    if intervalo_norm == "quinzenal":
        return data + timedelta(days=15)
    if intervalo_norm == "mensal":
        return _somar_mes_ajustando_dia(data, 1)
    if intervalo_norm == "anual":
        return _somar_ano_ajustando_dia(data, 1)

    # customizado
    if dias_customizado is None:
        raise ErroParcelamentoPrazo(
            "Para intervalo customizado, informe dias_customizado."
        )
    try:
        dias_int = int(dias_customizado)
    except Exception as exc:
        raise ErroParcelamentoPrazo(
            "dias_customizado inválido. Use um número inteiro."
        ) from exc
    if dias_int <= 0:
        raise ErroParcelamentoPrazo(
            "dias_customizado deve ser maior que zero."
        )
    return data + timedelta(days=dias_int)


def _validar_config_parcelamento(
    numero_parcelas: int,
    intervalo: str,
    dias_customizado: Optional[int],
) -> Tuple[int, str, Optional[int]]:
    """
    Valida parâmetros de parcelamento.
    """
    try:
        n = int(numero_parcelas)
    except Exception as exc:
        raise ErroParcelamentoPrazo(
            "Total de parcelas inválido. Use um número inteiro."
        ) from exc

    if n < 2:
        raise ErroParcelamentoPrazo(
            "Parcelamento precisa ter pelo menos 2 parcelas."
        )

    intervalo_norm = (intervalo or "").strip().lower()
    if intervalo_norm not in INTERVALOS_PARCELAS_VALIDOS:
        raise ErroParcelamentoPrazo(
            "Intervalo de parcelas inválido."
        )

    if intervalo_norm == "customizado":
        if dias_customizado is None:
            raise ErroParcelamentoPrazo(
                "Para intervalo customizado, informe dias_customizado."
            )
        try:
            dias_int = int(dias_customizado)
        except Exception as exc:
            raise ErroParcelamentoPrazo(
                "dias_customizado inválido. Use um número inteiro."
            ) from exc
        if dias_int <= 0:
            raise ErroParcelamentoPrazo(
                "dias_customizado deve ser maior que zero."
            )
        return n, intervalo_norm, dias_int

    return n, intervalo_norm, None


def _normalizar_prazo_base_para_parcelado(
    prazo_base: Dict[str, Any],
    total_parcelas: int,
    intervalo: str,
    dias_customizado: Optional[int],
) -> Dict[str, Any]:
    """
    Garante consistência dos campos mutualmente exclusivos no prazo base.
    """
    dados = dict(prazo_base or {})
    dados.pop("_id", None)

    dados["tipo_prazo"] = "parcelado"
    dados["recorrente"] = False
    dados["config_recorrencia"] = None

    dados["total_parcelas"] = int(total_parcelas)
    dados["numero_parcela_atual"] = 0
    dados["parcela_de"] = None
    dados["intervalo_parcelas"] = intervalo
    dados["dias_customizado"] = dias_customizado
    return dados


def gerar_parcelas_automaticas(
    db: Any,
    prazo_base: Dict[str, Any],
    numero_parcelas: int,
    data_inicial: Any,
    intervalo: str,
    dias_customizado: Optional[int] = None,
    collection_name: str = "prazos",
) -> Dict[str, Any]:
    """
    Gera automaticamente N parcelas no Firestore em uma operação atômica.

    Observação importante:
        - A criação é feita em UM batch, incluindo o prazo "pai".
          Se falhar, nada é criado (rollback natural do batch).

    Args:
        db: Cliente Firestore (firebase_admin.firestore.client()).
        prazo_base: Dados do prazo (título, responsáveis, clientes, casos...).
        numero_parcelas: Quantidade total de parcelas (>= 2).
        data_inicial: Data base da 1ª parcela (timestamp/date/datetime).
        intervalo: semanal|quinzenal|mensal|anual|customizado.
        dias_customizado: Obrigatório se intervalo=customizado.
        collection_name: Nome da coleção (padrão: 'prazos').

    Returns:
        {
          'prazo_pai_id': str,
          'parcelas_ids': [str],
        }
    """
    n, intervalo_norm, dias_int = _validar_config_parcelamento(
        numero_parcelas=numero_parcelas,
        intervalo=intervalo,
        dias_customizado=dias_customizado,
    )

    data_base = _converter_para_date(data_inicial)

    # Evita duplicação acidental: se alguém mandar _id no prazo_base.
    if prazo_base and prazo_base.get("_id"):
        raise ErroParcelamentoPrazo(
            "Prazo base já tem _id. Use criar_prazo_parcelado para "
            "criar um novo parcelamento, ou remova o _id."
        )

    prazo_pai_ref = db.collection(collection_name).document()
    prazo_pai_id = prazo_pai_ref.id

    dados_pai = _normalizar_prazo_base_para_parcelado(
        prazo_base=prazo_base,
        total_parcelas=n,
        intervalo=intervalo_norm,
        dias_customizado=dias_int,
    )

    if not dados_pai.get("titulo"):
        raise ErroParcelamentoPrazo("Título do prazo é obrigatório.")

    if not (dados_pai.get("responsaveis") or []):
        raise ErroParcelamentoPrazo(
            "Selecione pelo menos um responsável."
        )

    # Timestamp de criação/atualização
    now = time.time()
    dados_pai["criado_em"] = now
    dados_pai["atualizado_em"] = now

    # O pai não representa uma parcela real; mantém a data inicial como
    # referência (facilita filtros), mas as parcelas terão suas próprias datas.
    dados_pai["prazo_fatal"] = _date_para_timestamp(data_base)

    # Batch atômico: pai + N parcelas
    total_writes = 1 + n
    if total_writes > 500:
        raise ErroParcelamentoPrazo(
            "Parcelamento muito grande. Máximo de 499 parcelas por "
            "operação (limite do Firestore)."
        )

    batch = db.batch()
    batch.set(prazo_pai_ref, dados_pai)

    parcelas_ids: List[str] = []
    data_parcela = data_base

    titulo_base = str(dados_pai.get("titulo", "")).strip()
    for i in range(1, n + 1):
        if i == 1:
            data_parcela = data_base
        else:
            data_parcela = calcular_proxima_data_parcela(
                data_base=data_parcela,
                intervalo=intervalo_norm,
                dias_customizado=dias_int,
            )

        dados_parcela = dict(dados_pai)
        dados_parcela["titulo"] = f"{titulo_base} [Parcela {i}/{n}]"
        dados_parcela["numero_parcela_atual"] = i
        dados_parcela["parcela_de"] = prazo_pai_id
        dados_parcela["prazo_fatal"] = _date_para_timestamp(data_parcela)
        dados_parcela["status"] = "pendente"

        # Cada parcela é independente: pode ser editada individualmente.
        parcela_ref = db.collection(collection_name).document()
        parcelas_ids.append(parcela_ref.id)
        batch.set(parcela_ref, dados_parcela)

    try:
        batch.commit()
    except Exception as exc:
        raise ErroParcelamentoPrazo(
            "Falha ao criar parcelamento no Firestore. "
            "Nenhuma parcela foi criada."
        ) from exc

    return {"prazo_pai_id": prazo_pai_id, "parcelas_ids": parcelas_ids}


def obter_status_parcelamento(
    db: Any,
    prazo_pai_id: str,
    collection_name: str = "prazos",
) -> Dict[str, Any]:
    """
    Retorna status do parcelamento: quantas parcelas foram concluídas.
    """
    if not prazo_pai_id:
        raise ErroParcelamentoPrazo("Informe o ID do prazo pai.")

    query = db.collection(collection_name).where(
        "parcela_de", "==", prazo_pai_id
    )

    concluidas = 0
    total = 0
    for doc in query.stream():
        total += 1
        dados = doc.to_dict() or {}
        if str(dados.get("status", "")).lower() == "concluido":
            concluidas += 1

    return {
        "prazo_pai_id": prazo_pai_id,
        "total_parcelas_encontradas": total,
        "parcelas_concluidas": concluidas,
        "parcelas_pendentes": max(total - concluidas, 0),
    }


def excluir_parcelamento_completo(
    db: Any,
    prazo_pai_id: str,
    collection_name: str = "prazos",
) -> Dict[str, Any]:
    """
    Exclui o prazo pai e todas as parcelas ligadas a ele.

    Observação:
        - Operação em batches (limite 500 por commit).
        - Em caso de falha, a função informa quantos foram excluídos.
    """
    if not prazo_pai_id:
        raise ErroParcelamentoPrazo("Informe o ID do prazo pai.")

    prazos_ref = db.collection(collection_name)

    parcelas_docs = list(
        prazos_ref.where("parcela_de", "==", prazo_pai_id).stream()
    )
    parcelas_ids = [d.id for d in parcelas_docs]

    ids_excluidos: List[str] = []
    erros: List[str] = []

    # Deleta parcelas em batches
    chunk_size = 450
    for start in range(0, len(parcelas_ids), chunk_size):
        batch = db.batch()
        chunk = parcelas_ids[start:start + chunk_size]
        for doc_id in chunk:
            batch.delete(prazos_ref.document(doc_id))
        try:
            batch.commit()
            ids_excluidos.extend(chunk)
        except Exception as exc:
            erros.append(
                f"Falha ao excluir lote de parcelas (ex.: {chunk[:3]}): "
                f"{exc}"
            )
            break

    # Tenta deletar o pai por último
    try:
        prazos_ref.document(prazo_pai_id).delete()
        ids_excluidos.append(prazo_pai_id)
    except Exception as exc:
        erros.append(f"Falha ao excluir prazo pai: {exc}")

    if erros:
        return {
            "sucesso": False,
            "prazo_pai_id": prazo_pai_id,
            "ids_excluidos": ids_excluidos,
            "erros": erros,
        }

    return {
        "sucesso": True,
        "prazo_pai_id": prazo_pai_id,
        "ids_excluidos": ids_excluidos,
        "total_excluidos": len(ids_excluidos),
    }


def editar_parcela_individual(
    db: Any,
    parcela_id: str,
    dados_atualizados: Dict[str, Any],
    collection_name: str = "prazos",
) -> bool:
    """
    Edita uma parcela específica (sem alterar outras parcelas).

    Regra:
        - Bloqueia alterações nos campos de vínculo do parcelamento.
    """
    if not parcela_id:
        raise ErroParcelamentoPrazo("Informe o ID da parcela.")

    ref = db.collection(collection_name).document(parcela_id)
    doc = ref.get()
    if not doc.exists:
        raise ErroParcelamentoPrazo("Parcela não encontrada.")

    atual = doc.to_dict() or {}
    if not atual.get("parcela_de"):
        raise ErroParcelamentoPrazo(
            "Este prazo não é uma parcela (parcela_de vazio)."
        )

    dados = dict(dados_atualizados or {})
    dados.pop("_id", None)

    # Protege metadados do parcelamento
    for campo in (
        "parcela_de",
        "total_parcelas",
        "numero_parcela_atual",
        "intervalo_parcelas",
        "dias_customizado",
        "tipo_prazo",
        "recorrente",
        "config_recorrencia",
    ):
        dados.pop(campo, None)

    dados["atualizado_em"] = time.time()
    ref.update(dados)
    return True


