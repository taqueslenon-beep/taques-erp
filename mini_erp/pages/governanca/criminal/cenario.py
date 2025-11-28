from datetime import datetime, timedelta
from typing import Optional

from nicegui import ui

from ....core import get_benefits_list, format_date_br, get_clients_list


def _parse_iso_date(date_str: Optional[str] = None):
    """Converte string de data do JSON/input em date()."""
    if not date_str:
        return None

    value = str(date_str)
    try:
        # Tenta ISO completo (2025-11-27T10:23:45)
        dt = datetime.fromisoformat(value)
    except Exception:
        try:
            # Tenta apenas data ISO (2025-11-27)
            dt = datetime.strptime(value, '%Y-%m-%d')
        except Exception:
            return None
    return dt.date()


def _add_five_years(base_date):
    """Soma 5 anos à data, lidando com anos bissextos."""
    if not base_date:
        return None
    try:
        return base_date.replace(year=base_date.year + 5)
    except ValueError:
        # Fallback simples se der erro em 29/02
        return base_date + timedelta(days=5 * 365)


def _diff_ymd(from_date, to_date):
    """
    Calcula diferença aproximada em anos, meses e dias entre duas datas.
    Retorna sempre valores não negativos (0, 0, 0) se to_date <= from_date.
    """
    if not from_date or not to_date or to_date <= from_date:
        return 0, 0, 0

    years = to_date.year - from_date.year
    months = to_date.month - from_date.month
    days = to_date.day - from_date.day

    if days < 0:
        # "Empresta" um mês
        months -= 1
        # Último dia do mês anterior a to_date
        prev_month_last_day = (datetime(to_date.year, to_date.month, 1) - timedelta(days=1)).day
        days += prev_month_last_day

    if months < 0:
        years -= 1
        months += 12

    if years < 0:
        return 0, 0, 0

    return years, months, days


def _format_diff_ymd(years: int, months: int, days: int) -> str:
    """Monta string do tipo 'X anos, Y meses e Z dias'."""
    return f'{years} anos, {months} meses e {days} dias'


def _build_cenario_acordos_rows():
    """
    Monta linhas da tabela de acordos:
    - Usa transações penais com data de cumprimento integral
    - Agrupa por beneficiário e pega a última data de cumprimento
    - Calcula, a partir dela, quando será possível:
      * firmar novo ANPP
      * firmar nova Transação Penal
      (ambos com regra de 5 anos após o cumprimento)
    """
    hoje = datetime.today().date()

    # Mapa: beneficiário -> lista de datas de cumprimento integral de transações penais
    datas_por_beneficiario: dict[str, list] = {}
    for benefit in get_benefits_list():
        if benefit.get('tipo') != 'Transação Penal':
            continue
        data_str = benefit.get('data_cumprimento_integral')
        if not data_str:
            continue
        beneficiario = benefit.get('beneficiario', '-') or '-'
        data = _parse_iso_date(data_str)
        if not data:
            continue
        datas_por_beneficiario.setdefault(beneficiario, []).append(data)

    rows = []

    # 1) Cria linhas para todos os clientes cadastrados
    for client in get_clients_list():
        beneficiario = client.get('name') or '-'
        datas = datas_por_beneficiario.get(beneficiario, [])

        if datas:
            # Cliente já teve transação penal cumprida: aplica regra dos 5 anos
            data_base = max(datas)
            data_liberacao = _add_five_years(data_base)
            if not data_liberacao:
                continue

            data_liberacao_iso = data_liberacao.isoformat()
            data_liberacao_br = format_date_br(data_liberacao_iso)

            em_veda = hoje < data_liberacao
            if em_veda:
                anos, meses, dias = _diff_ymd(hoje, data_liberacao)
            else:
                anos, meses, dias = 0, 0, 0

            texto_resto = _format_diff_ymd(anos, meses, dias)

            rows.append(
                {
                    'beneficiario': beneficiario,
                    'data_novo_anpp': data_liberacao_br,
                    'data_nova_transacao': data_liberacao_br,
                    'data_novo_sursi': data_liberacao_br,
                    # Sursi penal não é impactado pela transação: mostramos apenas texto de aptidão
                    'data_nova_suspensao_sursi': 'Apto para receber o benefício - Sursi Penal',
                    'anpp_futuro': em_veda,
                    'transacao_futuro': em_veda,
                    'sursi_futuro': em_veda,
                    'faltam_anpp': texto_resto,
                    'faltam_transacao': texto_resto,
                    'faltam_sursi': texto_resto,
                    'data_nova_prd': '-',
                    'data_fixacao': '-',
                    'data_regime_aberto': '-',
                    '_ordenacao': data_liberacao,
                }
            )
        else:
            # Cliente nunca teve transação penal cumprida: está apto para celebrar
            rows.append(
                {
                    'beneficiario': beneficiario,
                    'data_novo_anpp': 'Apto para celebrar novo ANPP',
                    'data_nova_transacao': 'Apto para celebrar nova Transação Penal',
                    'data_novo_sursi': 'Apto para receber Sursi Processual',
                    'data_nova_suspensao_sursi': 'Apto para receber o benefício - Sursi Penal',
                    'anpp_futuro': False,
                    'transacao_futuro': False,
                    'sursi_futuro': False,
                    'faltam_anpp': '',
                    'faltam_transacao': '',
                    'faltam_sursi': '',
                    'data_nova_prd': '-',
                    'data_fixacao': '-',
                    'data_regime_aberto': '-',
                    '_ordenacao': hoje,
                }
            )

    # 2) Inclui beneficiários que têm transação penal mas não constam em get_clients_list()
    nomes_clientes = {c.get('name') for c in get_clients_list()}
    for beneficiario, datas in datas_por_beneficiario.items():
        if beneficiario in nomes_clientes:
            continue
        if not datas:
            continue
        data_base = max(datas)
        data_liberacao = _add_five_years(data_base)
        if not data_liberacao:
            continue
        data_liberacao_iso = data_liberacao.isoformat()
        data_liberacao_br = format_date_br(data_liberacao_iso)
        em_veda = hoje < data_liberacao
        if em_veda:
            anos, meses, dias = _diff_ymd(hoje, data_liberacao)
        else:
            anos, meses, dias = 0, 0, 0
        texto_resto = _format_diff_ymd(anos, meses, dias)
        rows.append(
            {
                'beneficiario': beneficiario,
                'data_novo_anpp': data_liberacao_br,
                'data_nova_transacao': data_liberacao_br,
                'data_novo_sursi': data_liberacao_br,
                'data_nova_suspensao_sursi': 'Apto para receber o benefício - Sursi Penal',
                'anpp_futuro': em_veda,
                'transacao_futuro': em_veda,
                'sursi_futuro': em_veda,
                'faltam_anpp': texto_resto,
                'faltam_transacao': texto_resto,
                'faltam_sursi': texto_resto,
                'data_nova_prd': '-',
                'data_fixacao': '-',
                'data_regime_aberto': '-',
                '_ordenacao': data_liberacao,
            }
        )

    # Ordena por data de liberação / hoje (clientes mais "sensíveis" primeiro)
    rows.sort(key=lambda r: r.get('_ordenacao') or hoje)

    # Remove campo interno de ordenação antes de devolver
    for r in rows:
        r.pop('_ordenacao', None)

    return rows


def render_cenario_criminal():
    """Visão geral criminal dentro do módulo de Governança."""

    # Estilo de linhas alternadas (zebrado) para a tabela deste cenário
    ui.add_css(
        """
        .tabela-cenario-criminal .q-tr:nth-child(odd) {
            background-color: #ffffff;
        }
        .tabela-cenario-criminal .q-tr:nth-child(even) {
            background-color: #f9fafb;
        }
        """
    )

    with ui.card().classes('w-full'):
        ui.label('Cenário Criminal').classes('text-lg font-bold mb-2')

        # Apenas a planilha consolidada, sem o bloco informativo antigo.
        ui.separator().classes('my-2')
        ui.label('Planilha de elegibilidade para novos acordos penais').classes('font-semibold mb-1')
        ui.label(
            'Base: data de cumprimento integral da última transação penal registrada para cada beneficiário.'
        ).classes('text-xs text-gray-500 mb-2')

        columns_acordos = [
            {
                'name': 'beneficiario',
                'label': 'Cliente / Beneficiário',
                'field': 'beneficiario',
                'align': 'left',
            },
            {
                'name': 'data_nova_transacao',
                'label': 'Apto a celebrar nova Transação Penal',
                'field': 'data_nova_transacao',
                'align': 'center',
            },
            {
                'name': 'data_novo_anpp',
                'label': 'Apto a celebrar novo Acordo de Não Persecução Penal (ANPP)',
                'field': 'data_novo_anpp',
                'align': 'center',
            },
            {
                'name': 'data_novo_sursi',
                'label': 'Apto para nova Suspensão Condicional do Processo (Sursi Processual)',
                'field': 'data_novo_sursi',
                'align': 'center',
            },
            {
                'name': 'data_nova_suspensao_sursi',
                'label': 'Apto para nova Suspensão Condicional da Pena (Sursi Penal)',
                'field': 'data_nova_suspensao_sursi',
                'align': 'center',
            },
        ]

        rows_acordos = _build_cenario_acordos_rows()

        if rows_acordos:
            tabela = (
                ui.table(columns=columns_acordos, rows=rows_acordos)
                .classes('w-full text-xs tabela-cenario-criminal')
                .props('flat dense wrap-cells')
            )

            # Destaque visual: se a data for futura em relação a hoje, mostrar em vermelho e negrito
            tabela.add_slot(
                'body-cell-data_novo_anpp',
                '''
                <q-td :props="props">
                    <div class="flex flex-col items-center">
                        <span
                            :class="props.row.anpp_futuro ? 'text-red-600 font-bold' : 'text-green-700 font-bold'"
                        >
                            {{ props.value }}
                        </span>
                        <span
                            v-if="props.row.anpp_futuro"
                            class="text-red-600 italic text-xs"
                        >
                            (Faltam {{ props.row.faltam_anpp }})
                        </span>
                    </div>
                </q-td>
                ''',
            )

            tabela.add_slot(
                'body-cell-data_nova_transacao',
                '''
                <q-td :props="props">
                    <div class="flex flex-col items-center">
                        <span
                            :class="props.row.transacao_futuro ? 'text-red-600 font-bold' : 'text-green-700 font-bold'"
                        >
                            {{ props.value }}
                        </span>
                        <span
                            v-if="props.row.transacao_futuro"
                            class="text-red-600 italic text-xs"
                        >
                            (Faltam {{ props.row.faltam_transacao }})
                        </span>
                    </div>
                </q-td>
                ''',
            )

            tabela.add_slot(
                'body-cell-data_novo_sursi',
                '''
                <q-td :props="props">
                    <div class="flex flex-col items-center">
                        <span
                            :class="props.row.sursi_futuro ? 'text-red-600 font-bold' : 'text-green-700 font-bold'"
                        >
                            {{ props.value }}
                        </span>
                        <span
                            v-if="props.row.sursi_futuro"
                            class="text-red-600 italic text-xs"
                        >
                            (Faltam {{ props.row.faltam_sursi }})
                        </span>
                    </div>
                </q-td>
                ''',
            )


            # Sursi penal: transação não interfere; mostramos apenas texto de aptidão em verde
            tabela.add_slot(
                'body-cell-data_nova_suspensao_sursi',
                '''
                <q-td :props="props">
                    <span class="text-green-700 font-bold">
                        {{ props.value || 'Apto para receber o benefício - Sursi Penal' }}
                    </span>
                </q-td>
                ''',
            )
        else:
            ui.label(
                'Nenhum dado ainda. Preencha a data de cumprimento integral nas transações penais '
                'para ver, por beneficiário, as novas datas possíveis para ANPP e Transação Penal.'
            ).classes('text-gray-400 italic mb-2')
