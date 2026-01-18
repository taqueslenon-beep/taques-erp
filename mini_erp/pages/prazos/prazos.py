"""
prazos.py - Página principal do módulo Prazos.

Visualização em tabela dos prazos cadastrados com CRUD completo.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Tuple
from nicegui import ui
from ...core import layout, get_display_name
from ...auth import is_authenticated
from ...firebase_config import get_db
from .database import (
    listar_prazos,
    listar_prazos_por_status,
    buscar_prazo_por_id,
    criar_prazo,
    atualizar_prazo,
    excluir_prazo,
    invalidar_cache_prazos,
    buscar_usuarios_para_select,
    buscar_clientes_para_select,
    buscar_casos_para_select,
    criar_proximo_prazo_recorrente,
    calcular_proximo_prazo_fatal,
)
from .modal_prazo import render_prazo_dialog
from .models import STATUS_LABELS
from .parcelamento_backend import (
    excluir_parcelamento_completo,
    ErroParcelamentoPrazo,
)


def formatar_data_prazo(timestamp: Any) -> str:
    """
    Formata timestamp para exibição no padrão DD/MM/AAAA.

    Args:
        timestamp: Timestamp (float ou int) ou None

    Returns:
        String formatada ou '-' se inválida
    """
    if not timestamp:
        return '-'

    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%d/%m/%Y')
        return str(timestamp)
    except Exception:
        return '-'


def calcular_prazo_seguranca(timestamp: Any) -> str:
    """
    Calcula o prazo de segurança (4 dias antes do prazo fatal).

    Args:
        timestamp: Timestamp do prazo fatal (float, int ou None)

    Returns:
        String com a data de segurança no formato DD/MM/AAAA ou '-' se inválida
    """
    if not timestamp:
        return '-'

    try:
        if isinstance(timestamp, (int, float)):
            data_fatal = datetime.fromtimestamp(timestamp)
            data_seguranca = data_fatal - timedelta(days=4)
            return data_seguranca.strftime('%d/%m/%Y')
        return '-'
    except Exception:
        return '-'


def verificar_prazo_atrasado(timestamp: Any, status: str) -> bool:
    """
    Verifica se um prazo está atrasado.

    Um prazo está atrasado quando:
    - O prazo fatal é anterior à data de hoje
    - E o status atual é 'pendente' (não concluído)

    Args:
        timestamp: Timestamp do prazo fatal (float, int ou None)
        status: Status atual do prazo ('pendente' ou 'concluido')

    Returns:
        True se o prazo está atrasado, False caso contrário
    """
    if not timestamp:
        return False

    # Só pode estar atrasado se estiver pendente
    if status.lower() != 'pendente':
        return False

    try:
        if isinstance(timestamp, (int, float)):
            data_fatal = datetime.fromtimestamp(timestamp)
            hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return data_fatal < hoje
        return False
    except Exception:
        return False


def ordenar_prazos_prioridade(prazos_lista: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ordena prazos por prioridade:
    1. Prazos atrasados (vermelho) - no topo
    2. Prazos "aguardando abertura" (rosa) - em segundo
    3. Prazos normais (resto) - depois

    Args:
        prazos_lista: Lista de dicionários com prazos

    Returns:
        Lista ordenada de prazos
    """
    from datetime import datetime
    
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def obter_prioridade_ordenacao(prazo: Dict[str, Any]) -> Tuple[int, float]:
        """
        Retorna tupla (prioridade, timestamp) para ordenação.
        Prioridade menor = aparece primeiro.
        """
        status = prazo.get('status', 'pendente').lower()
        estado_abertura = prazo.get('estado_abertura', 'aberto')
        prazo_fatal_ts = prazo.get('prazo_fatal')
        
        # 1. Prazos atrasados (prioridade 1)
        if status == 'pendente' and prazo_fatal_ts:
            try:
                if isinstance(prazo_fatal_ts, (int, float)):
                    data_fatal = datetime.fromtimestamp(prazo_fatal_ts)
                    if data_fatal < hoje:
                        return (1, prazo_fatal_ts or 0)  # Mais antigo primeiro
            except Exception:
                pass
        
        # 2. Prazos "aguardando abertura" (prioridade 2)
        if estado_abertura == 'aguardando_abertura':
            return (2, prazo_fatal_ts or 0)
        
        # 3. Prazos normais (prioridade 3)
        return (3, prazo_fatal_ts or 0)
    
    # Ordenar usando a função de prioridade
    prazos_ordenados = sorted(prazos_lista, key=obter_prioridade_ordenacao)
    
    return prazos_ordenados


def formatar_titulo_prazo(prazo: Dict[str, Any]) -> str:
    """
    Formata o título do prazo, adicionando:
    - sufixo [Parcela X/N] quando for parcela
    - emoji 🔁 quando for recorrente

    Args:
        prazo: Dicionário com dados do prazo

    Returns:
        Título formatado com emoji se recorrente
    """
    # Validação defensiva: prazo deve ser dict não None
    if prazo is None or not isinstance(prazo, dict):
        print(f"[DEBUG] formatar_titulo_prazo: prazo inválido recebido: {type(prazo)}")
        return 'Sem título'
    
    titulo = prazo.get('titulo', 'Sem título') or 'Sem título'
    is_recorrente = prazo.get('recorrente', False)

    # ---------------------------------------------------------
    # Detecção de parcela/parcelamento
    # ---------------------------------------------------------
    # Padrão do backend de parcelamento:
    # - parcelas têm: parcela_de=<id do pai>, numero_parcela_atual (1..N), total_parcelas
    # Compatibilidade extra (modal antigo/alternativo):
    # - parcelas têm: parcelamento_id, parcela_numero, parcela_total
    parcela_de = prazo.get('parcela_de')
    numero_parcela = prazo.get('numero_parcela_atual')
    total_parcelas = prazo.get('total_parcelas')

    if (numero_parcela is None) and prazo.get('parcela_numero') is not None:
        numero_parcela = prazo.get('parcela_numero')
    if (total_parcelas is None) and prazo.get('parcela_total') is not None:
        total_parcelas = prazo.get('parcela_total')

    # Considera "parcela" quando:
    # - tem parcela_de (backend), ou
    # - tem número da parcela > 0 (evita marcar o "pai" que tem 0), ou
    # - (compat) tem parcela_numero informado
    is_parcela = bool(parcela_de) or (isinstance(numero_parcela, int) and numero_parcela > 0) or bool(prazo.get('parcela_numero'))

    # Adiciona sufixo [Parcela X/N] só quando houver X e N válidos, e não duplicar
    if is_parcela and numero_parcela and total_parcelas:
        if '[Parcela' not in str(titulo):
            titulo = f"{titulo} [Parcela {numero_parcela}/{total_parcelas}]"

    # Recorrente (não conflita com parcelado, mas por segurança evitamos colocar em parcela)
    if is_recorrente and not is_parcela:
        return f"🔁 {titulo}"
    return titulo


def _prazo_e_parcela(prazo: Dict[str, Any]) -> bool:
    """Retorna True se o prazo é uma parcela (não o pai do parcelamento)."""
    if not prazo:
        return False
    if prazo.get('parcela_de'):
        return True
    # Compatibilidade: parcelamento_id + parcela_numero
    if prazo.get('parcelamento_id') and prazo.get('parcela_numero'):
        return True
    # Campo numérico do backend: numero_parcela_atual (1..N)
    n = prazo.get('numero_parcela_atual')
    return isinstance(n, int) and n > 0


# =============================================================================
# FUNÇÕES DE CÁLCULO DE SEMANAS
# =============================================================================

def obter_inicio_fim_semana(data_ref: date) -> Tuple[date, date]:
    """
    Retorna o início (segunda) e fim (domingo) da semana de uma data.

    Args:
        data_ref: Data de referência

    Returns:
        Tupla (data_inicio, data_fim) da semana
    """
    # Segunda-feira da semana
    inicio = data_ref - timedelta(days=data_ref.weekday())
    # Domingo da semana
    fim = inicio + timedelta(days=6)
    return inicio, fim


def obter_semana_passada() -> Tuple[date, date]:
    """Retorna início e fim da semana passada."""
    hoje = date.today()
    inicio_esta_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana_passada = inicio_esta_semana - timedelta(days=7)
    fim_semana_passada = inicio_semana_passada + timedelta(days=6)
    return inicio_semana_passada, fim_semana_passada


def obter_esta_semana() -> Tuple[date, date]:
    """Retorna início e fim desta semana."""
    hoje = date.today()
    return obter_inicio_fim_semana(hoje)


def obter_proxima_semana() -> Tuple[date, date]:
    """Retorna início e fim da próxima semana."""
    hoje = date.today()
    inicio_esta_semana = hoje - timedelta(days=hoje.weekday())
    inicio_proxima_semana = inicio_esta_semana + timedelta(days=7)
    fim_proxima_semana = inicio_proxima_semana + timedelta(days=6)
    return inicio_proxima_semana, fim_proxima_semana


def obter_semana_do_ano(ano: int, numero_semana: int) -> Tuple[date, date]:
    """
    Retorna início e fim de uma semana específica do ano.
    
    Semanas são calculadas de segunda a domingo.
    A primeira segunda-feira do ano marca o início da Semana 1.

    Args:
        ano: Ano (ex: 2025)
        numero_semana: Número da semana (1-53)

    Returns:
        Tupla (data_inicio, data_fim) onde:
        - data_inicio é segunda-feira
        - data_fim é domingo
    """
    # Encontrar a primeira segunda-feira do ano
    primeiro_janeiro = date(ano, 1, 1)
    
    # weekday() retorna: 0=segunda, 1=terça, ..., 6=domingo
    # Se 1º de janeiro é segunda (0), está na semana 1
    # Se é terça (1), a segunda anterior está no ano anterior
    # Se é domingo (6), a próxima segunda é dia 2
    
    if primeiro_janeiro.weekday() == 0:
        # 1º de janeiro é segunda-feira
        primeira_segunda = primeiro_janeiro
    else:
        # Calcular quantos dias até a próxima segunda
        dias_ate_segunda = 7 - primeiro_janeiro.weekday()
        primeira_segunda = primeiro_janeiro + timedelta(days=dias_ate_segunda)
    
    # Calcular início da semana desejada
    inicio = primeira_segunda + timedelta(weeks=numero_semana - 1)
    fim = inicio + timedelta(days=6)  # Domingo

    return inicio, fim


def formatar_periodo_semana(inicio: date, fim: date) -> str:
    """Formata o período da semana para exibição."""
    return f"{inicio.strftime('%d/%m')} - {fim.strftime('%d/%m/%Y')}"


def filtrar_prazos_por_semana(prazos: List[Dict[str, Any]], inicio_semana: date, fim_semana: date) -> List[Dict[str, Any]]:
    """
    Filtra prazos cujo PRAZO FATAL está dentro do período da semana.

    Args:
        prazos: Lista de prazos
        inicio_semana: Data de início da semana (segunda)
        fim_semana: Data de fim da semana (domingo)

    Returns:
        Lista de prazos filtrados
    """
    filtrados = []

    for prazo in prazos:
        prazo_fatal = prazo.get('prazo_fatal')

        if not prazo_fatal:
            continue

        try:
            # Converter para date
            if isinstance(prazo_fatal, (int, float)):
                data_fatal = datetime.fromtimestamp(prazo_fatal).date()
            else:
                continue

            # Verificar se está dentro da semana
            if inicio_semana <= data_fatal <= fim_semana:
                filtrados.append(prazo)

        except Exception as e:
            print(f"[PRAZOS] Erro ao filtrar prazo: {e}")
            continue

    return filtrados


def calcular_semanas_do_ano(ano: int) -> List[Dict[str, Any]]:
    """
    Calcula todas as semanas de um ano, incluindo as que cruzam para o próximo ano.
    
    Semanas que cruzam entre anos aparecem em ambos os anos.
    
    Args:
        ano: Ano para calcular semanas
        
    Returns:
        Lista de dicionários com:
        - 'numero': número da semana
        - 'inicio': data de início (date)
        - 'fim': data de fim (date)
        - 'ano': ano de referência
    """
    semanas = []
    numero = 1
    
    # Encontrar primeira segunda-feira do ano
    primeiro_janeiro = date(ano, 1, 1)
    
    if primeiro_janeiro.weekday() == 0:
        # 1º de janeiro é segunda-feira
        primeira_segunda = primeiro_janeiro
    else:
        # Calcular quantos dias até a próxima segunda
        dias_ate_segunda = 7 - primeiro_janeiro.weekday()
        primeira_segunda = primeiro_janeiro + timedelta(days=dias_ate_segunda)
    
    # Gerar semanas até que o início esteja no próximo ano
    inicio = primeira_segunda
    while inicio.year <= ano:
        fim = inicio + timedelta(days=6)
        
        semanas.append({
            'numero': numero,
            'inicio': inicio,
            'fim': fim,
            'ano': ano
        })
        
        # Próxima semana
        inicio = inicio + timedelta(days=7)
        numero += 1
        
        # Limite de segurança (máximo 54 semanas)
        if numero > 54:
            break
    
    return semanas


def criar_opcoes_semanas(ano: int) -> Dict[str, str]:
    """
    Cria opções de semanas para o dropdown com formato específico.
    
    Formato: "Semana X - DD/MM/AAAA a DD/MM/AAAA"
    
    Inclui semanas que cruzam entre anos:
    - Semanas do ano anterior que terminam no ano atual (aparecem em ambos)
    - Semanas do ano atual que terminam no próximo ano (aparecem em ambos)
    
    Args:
        ano: Ano para gerar semanas (obrigatório)

    Returns:
        Dicionário {valor: label} para o dropdown
        Valor: "ano-numero_semana" ou "ano-numero-proximo" para semanas do próximo ano
        Label: "Semana X - DD/MM/AAAA a DD/MM/AAAA"
    """
    opcoes = {}
    
    # Semanas do ano atual
    semanas = calcular_semanas_do_ano(ano)
    
    for semana_info in semanas:
        numero = semana_info['numero']
        inicio = semana_info['inicio']
        fim = semana_info['fim']
        
        # Formato: "Semana X - DD/MM/AAAA a DD/MM/AAAA"
        label = f"Semana {numero} - {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
        valor = f"{ano}-{numero}"
        opcoes[valor] = label
    
    # Adicionar semanas do ano anterior que cruzam para o ano atual
    if ano > 2020:  # Limite mínimo de segurança
        semanas_ano_anterior = calcular_semanas_do_ano(ano - 1)
        for semana_info in semanas_ano_anterior:
            # Se a semana termina no ano atual, incluir no dropdown
            if semana_info['fim'].year == ano:
                numero = semana_info['numero']
                inicio = semana_info['inicio']
                fim = semana_info['fim']
                
                # Usar número da semana do ano anterior, mas mostrar no ano atual
                # Criar um número único para evitar conflito (offset 200)
                numero_ajustado = numero + 200
                label = f"Semana {numero} ({ano-1}) - {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
                valor = f"{ano}-{numero_ajustado}"
                opcoes[valor] = label
    
    # Adicionar primeira semana do próximo ano se começar no ano atual
    if ano < 2030:  # Limite máximo de segurança
        semanas_proximo_ano = calcular_semanas_do_ano(ano + 1)
        if semanas_proximo_ano:
            primeira_semana = semanas_proximo_ano[0]
            # Se a primeira semana do próximo ano começa no ano atual
            if primeira_semana['inicio'].year == ano:
                numero = primeira_semana['numero']
                inicio = primeira_semana['inicio']
                fim = primeira_semana['fim']
                
                # Usar número 1 para a primeira semana do próximo ano
                label = f"Semana 1 ({ano+1}) - {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
                valor = f"{ano}-1-proximo"
                opcoes[valor] = label
    
    # Ordenar opções por data de início
    opcoes_ordenadas = {}
    items_ordenados = sorted(opcoes.items(), key=lambda x: (
        # Extrair data de início do label para ordenar
        x[1].split(' - ')[0] if ' - ' in x[1] else x[0]
    ))
    
    for valor, label in items_ordenados:
        opcoes_ordenadas[valor] = label
    
    return opcoes_ordenadas


def obter_semanas_que_cruzam_anos(ano: int) -> List[Dict[str, Any]]:
    """
    Retorna semanas que cruzam entre o ano especificado e o próximo ano.
    
    Essas semanas devem aparecer em ambos os anos.
    
    Args:
        ano: Ano de referência
        
    Returns:
        Lista de semanas que cruzam para o próximo ano
    """
    semanas_cruzadas = []
    semanas = calcular_semanas_do_ano(ano)
    
    for semana_info in semanas:
        # Se o fim da semana está no próximo ano, ela cruza
        if semana_info['fim'].year > ano:
            semanas_cruzadas.append(semana_info)
    
    return semanas_cruzadas


def formatar_lista_nomes(ids: List[str], opcoes: Dict[str, str]) -> str:
    """
    Formata lista de IDs para exibição de nomes separados por vírgula.

    Args:
        ids: Lista de IDs
        opcoes: Dicionário mapeando ID -> Nome

    Returns:
        String com nomes separados por vírgula ou '-'
    """
    if not ids:
        return '-'

    nomes = []
    for id_item in ids:
        if id_item in opcoes:
            # Extrai apenas o nome (remove email entre parênteses se houver)
            nome_completo = opcoes[id_item]
            nome = nome_completo.split(' (')[0] if ' (' in nome_completo else nome_completo
            nomes.append(nome)
        else:
            nomes.append(f"({id_item[:8]}...)")

    if not nomes:
        return '-'

    # Limita a 2 nomes para não ficar muito longo
    if len(nomes) > 2:
        return f"{', '.join(nomes[:2])}..."

    return ', '.join(nomes)


def formatar_responsaveis(responsaveis_ids: List[str], usuarios_opcoes: Dict[str, str]) -> str:
    """
    Formata lista de responsáveis usando cache local - SEM consultas Firebase.

    Args:
        responsaveis_ids: Lista de UIDs dos usuários responsáveis
        usuarios_opcoes: Dicionário de usuários (uid -> "Nome (email)")

    Returns:
        String com nomes separados por vírgula ou '-'
    """
    if not responsaveis_ids:
        return '-'

    nomes = []
    for uid in responsaveis_ids:
        if uid in usuarios_opcoes:
            # Extrai apenas o nome (remove email entre parênteses)
            nome_completo = usuarios_opcoes[uid]
            nome = nome_completo.split(' (')[0] if ' (' in nome_completo else nome_completo
            nomes.append(nome)
        else:
            nomes.append(f"({uid[:8]}...)")

    if not nomes:
        return '-'

    # Limita a 2 nomes para não ficar muito longo
    if len(nomes) > 2:
        return f"{', '.join(nomes[:2])}..."

    return ', '.join(nomes)


def obter_cor_status(status: str) -> str:
    """
    Retorna estilo CSS para badge baseado no status.

    Args:
        status: Status do prazo ('pendente' ou 'concluido')

    Returns:
        String de estilo CSS para o badge
    """
    if not status:
        return 'background-color: #d1d5db; color: #000000;'

    status_lower = status.lower()

    if status_lower == 'pendente':
        return 'background-color: #fde047; color: #000000;'  # Amarelo
    elif status_lower == 'concluido' or status_lower == 'concluído':
        return 'background-color: #4ade80; color: #000000;'  # Verde
    else:
        return 'background-color: #d1d5db; color: #000000;'  # Cinza padrão


@ui.page('/prazos')
def prazos():
    """Página principal do módulo Prazos."""
    if not is_authenticated():
        ui.navigate.to('/login')
        return

    print("[PRAZOS] Iniciando carregamento da página...")

    # CSS para cores alternadas e prazos atrasados
    ui.add_head_html('''
    <style>
        /* Container responsivo centralizado */
        .container-prazos {
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 16px;
        }
        
        /* Wrapper da tabela com scroll horizontal */
        .tabela-prazos-wrapper {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        /* Tabela com largura mínima para garantir todas colunas */
        .tabela-prazos {
            min-width: 1000px;
            width: 100%;
            table-layout: auto;
        }
        
        /* Cores alternadas nas linhas */
        .tabela-prazos tbody tr:nth-child(even) {
            background-color: #ffffff !important;
        }
        .tabela-prazos tbody tr:nth-child(odd) {
            background-color: #fafafa !important;
        }
        
        /* Prazos atrasados sobrepõem a alternância */
        .tabela-prazos tbody tr.linha-atrasada,
        .tabela-prazos tbody tr.linha-atrasada td {
            background-color: #FFCDD2 !important;
        }

        /*
         * Checkbox arredondado:
         * - O slot já usa `round` no q-checkbox, mas este CSS garante
         *   visual circular mesmo se a lib mudar detalhes internos.
         */
        .tabela-prazos .q-checkbox__bg {
            border-radius: 999px !important;
        }
        
        /* Cores das células de prazo */
        .celula-prazo-seguranca {
            background-color: #FFF9C4 !important;
            padding: 4px 8px !important;
            border-radius: 4px !important;
            display: inline-block;
            white-space: nowrap;
        }
        
        .celula-prazo-fatal {
            background-color: #FFCDD2 !important;
            padding: 4px 8px !important;
            border-radius: 4px !important;
            display: inline-block;
            white-space: nowrap;
        }
        
        /* Ajustes responsivos para telas menores */
        @media (max-width: 1200px) {
            .tabela-prazos {
                min-width: 900px;
            }
        }
        
        /* Garantir que células não quebrem linha */
        .tabela-prazos td {
            white-space: nowrap;
            vertical-align: middle;
        }
        
        /* Título pode quebrar linha e expande para preencher espaço */
        .tabela-prazos td:nth-child(2) {
            white-space: normal;
            word-break: break-word;
        }
        
        /* Clientes também pode quebrar se necessário */
        .tabela-prazos td:nth-child(4) {
            white-space: normal;
            word-break: break-word;
            max-width: 180px;
        }
        
        /* Estilos para filtros hierárquicos */
        .filtros-container {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }
        
        .grupo-filtros {
            margin-bottom: 16px;
        }
        
        .grupo-filtros:last-child {
            margin-bottom: 0;
        }
        
        .grupo-filtros-label {
            font-size: 12px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .filtro-btn {
            transition: all 0.2s ease;
            border-radius: 6px;
            font-weight: 500;
            min-width: 100px;
        }
        
        .filtro-btn.ativo {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
    </style>
    <script>
        function aplicarClasseAtrasado() {
            setTimeout(function() {
                const tabelas = document.querySelectorAll('.tabela-prazos tbody');
                tabelas.forEach(function(tbody) {
                    const linhas = tbody.querySelectorAll('tr');
                    linhas.forEach(function(linha) {
                        const celulas = linha.querySelectorAll('td');
                        let isAtrasado = false;
                        celulas.forEach(function(celula) {
                            if (celula.getAttribute('data-atrasado') === 'true') {
                                isAtrasado = true;
                            }
                        });
                        if (isAtrasado) {
                            linha.classList.add('linha-atrasada');
                        } else {
                            linha.classList.remove('linha-atrasada');
                        }
                    });
                });
            }, 100);
        }
        
        // Executa após renderização
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', aplicarClasseAtrasado);
        } else {
            aplicarClasseAtrasado();
        }
        
        // Observa mudanças na tabela
        // Só cria observer se houver elementos para observar
        function setupPrazosObserver() {
            try {
                const containers = document.querySelectorAll('.tabela-prazos');
                if (containers && containers.length > 0) {
                    containers.forEach(function(container) {
                        // Verificação rigorosa: existe, é Node válido, está no DOM
                        if (!container) return;
                        if (!(container instanceof Node)) return;
                        if (!document.contains(container)) return;
                        
                        try {
                            const observer = new MutationObserver(aplicarClasseAtrasado);
                            observer.observe(container, { childList: true, subtree: true });
                        } catch (e) {
                            // Silenciosamente ignora erros de observer (elemento pode ter sido removido)
                            console.debug('Observer error (prazos):', e.message);
                        }
                    });
                }
            } catch (e) {
                // Silenciosamente ignora erros de setup (não crítico)
                console.debug('Observer setup skipped (prazos):', e.message);
            }
        }
        
        // Executar apenas quando DOM estiver pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(setupPrazosObserver, 500);
            });
        } else {
            setTimeout(setupPrazosObserver, 500);
        }
    </script>
    ''')

    # Carregar opções EM PARALELO para reduzir tempo de carregamento
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(buscar_usuarios_para_select): 'usuarios',
            executor.submit(buscar_clientes_para_select): 'clientes',
            executor.submit(buscar_casos_para_select): 'casos',
        }

        opcoes = {}
        for future in as_completed(futures):
            key = futures[future]
            try:
                opcoes[key] = future.result()
            except Exception as e:
                print(f"[PRAZOS] Erro ao carregar {key}: {e}")
                opcoes[key] = {}

    usuarios_opcoes = opcoes.get('usuarios', {})
    clientes_opcoes = opcoes.get('clientes', {})
    casos_opcoes = opcoes.get('casos', {})

    print(f"[PRAZOS] Opções carregadas: {len(usuarios_opcoes)} usuários, {len(clientes_opcoes)} clientes, {len(casos_opcoes)} casos")

    # Estado de filtros adicionais (frontend)
    filtros_extras = {
        # Quando True, mostra somente prazos que são parcelas (numero_parcela_atual > 0 / parcela_de preenchido)
        'mostrar_apenas_parcelas': False,
    }

    # Referência para função de renderização de conteúdo (será definida depois)
    # Usando lista mutável para permitir atualização de referência
    renderizar_conteudo_ref_global = [None]

    # Estado dos filtros hierárquicos (definido aqui para escopo correto)
    # Status agora é um SET para permitir múltiplos filtros simultâneos
    filtros_ativos = {
        'status': {'pendente', 'aguardando_abertura', 'atrasado'},  # Set de status selecionados (padrão: pendentes, aguardando, atrasados)
        'temporal': None,  # 'semana', 'mes', None (todos)
        'tipo': None,  # 'simples', 'recorrente', 'parcelado', None (todos)
        'responsavel_id': None,  # ID do responsável ou None (todos)
    }

    def atualizar_tabelas():
        """Atualiza a visualização de prazos."""
        if renderizar_conteudo_ref_global[0]:
            renderizar_conteudo_ref_global[0].refresh()

    # Função para aplicar filtros combinados (definida aqui para escopo correto)
    def aplicar_filtros_combinados(prazos_lista: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aplica todos os filtros ativos à lista de prazos."""
        resultado = list(prazos_lista)
        
        # Filtro 1: Status (agora é um SET - permite múltiplos filtros simultâneos)
        status_selecionados = filtros_ativos['status']
        if status_selecionados:  # Se há algum status selecionado
            def prazo_atende_status(p):
                status_prazo = p.get('status', '').lower()
                estado_abertura = p.get('estado_abertura', 'aberto')
                prazo_fatal_ts = p.get('prazo_fatal')
                
                # Verifica cada status selecionado
                if 'pendente' in status_selecionados:
                    if status_prazo == 'pendente':
                        return True
                
                if 'aguardando_abertura' in status_selecionados:
                    if estado_abertura == 'aguardando_abertura':
                        return True
                
                if 'concluido' in status_selecionados:
                    if status_prazo == 'concluido':
                        return True
                
                if 'atrasado' in status_selecionados:
                    # Atrasado = prazo_fatal < hoje E status != 'concluido'
                    if verificar_prazo_atrasado(prazo_fatal_ts, status_prazo):
                        return True
                
                return False
            
            resultado = [p for p in resultado if prazo_atende_status(p)]
        # Se filtros_ativos['status'] estiver vazio, mostra todos
        
        # Filtro 2: Temporal (POR SEMANA / POR MÊS) - será aplicado separadamente se necessário
        
        # Filtro 3: Tipo (SIMPLES / RECORRENTE / PARCELADO)
        if filtros_ativos['tipo'] == 'simples':
            resultado = [
                p for p in resultado
                if not p.get('recorrente', False)
                and not _prazo_e_parcela(p)
            ]
        elif filtros_ativos['tipo'] == 'recorrente':
            resultado = [p for p in resultado if p.get('recorrente', False)]
        elif filtros_ativos['tipo'] == 'parcelado':
            # Usa a função _prazo_e_parcela que tem toda a lógica de detecção
            resultado = [p for p in resultado if _prazo_e_parcela(p)]
        
        # Filtro 4: Responsável
        if filtros_ativos['responsavel_id']:
            responsavel_id = filtros_ativos['responsavel_id']
            resultado = [
                p for p in resultado
                if responsavel_id in (p.get('responsaveis') or [])
            ]
        
        return resultado

    # Função callback após salvar
    def on_prazo_salvo(prazo_data: Dict[str, Any]):
        """Callback executado após salvar prazo."""
        try:
            prazo_id = prazo_data.get('_id')
            if prazo_id:
                # Invalida cache e atualiza ambas as tabelas
                invalidar_cache_prazos()
                atualizar_tabelas()
            else:
                ui.notify('Erro: ID do prazo não retornado', type='negative')
        except Exception as e:
            print(f"[ERROR] Erro ao processar prazo salvo: {e}")
            ui.notify('Erro ao atualizar lista. Tente recarregar.', type='negative')

    # Dialog para novo prazo - passa opções para evitar recarregar
    dialog_novo, open_dialog_novo = render_prazo_dialog(
        on_success=on_prazo_salvo,
        usuarios_opcoes=usuarios_opcoes,
        clientes_opcoes=clientes_opcoes,
        casos_opcoes=casos_opcoes
    )

    # Função para abrir modal de edição
    def abrir_modal_edicao(prazo_id: str):
        """Abre modal de edição com dados do prazo."""
        try:
            if not prazo_id:
                ui.notify('ID do prazo não informado!', type='negative')
                return
            
            prazo = buscar_prazo_por_id(prazo_id)
            if not prazo:
                ui.notify('Prazo não encontrado!', type='negative')
                return

            # Criar dialog de edição - passa opções para evitar recarregar
            dialog_edit, open_edit = render_prazo_dialog(
                on_success=on_prazo_salvo,
                prazo_inicial=prazo,
                usuarios_opcoes=usuarios_opcoes,
                clientes_opcoes=clientes_opcoes,
                casos_opcoes=casos_opcoes
            )
            open_edit()
        except Exception as e:
            print(f"[ERROR] Erro ao abrir modal de edição: {e}")
            import traceback
            traceback.print_exc()
            ui.notify(f'Erro ao carregar dados do prazo: {str(e)}', type='negative')

    # Função para excluir prazo
    def excluir_prazo_com_confirmacao(prazo_row: Dict[str, Any]):
        """
        Exclui prazo com diálogo inteligente.
        
        Regras:
        - Se for parcela (tem 'parcela_de'): oferece "Excluir apenas esta" ou "Excluir todas"
        - Caso contrário: confirmação normal
        """
        prazo_id = prazo_row.get('id') or prazo_row.get('_id')
        titulo = prazo_row.get('titulo', 'este prazo')
        parcela_de = prazo_row.get('parcela_de')
        numero_parcela_atual = prazo_row.get('numero_parcela_atual')
        total_parcelas = prazo_row.get('total_parcelas')

        eh_parcela = bool(parcela_de) or (isinstance(numero_parcela_atual, int) and numero_parcela_atual > 0)

        # Evita consulta extra: usa cache de listar_prazos para estimar total de parcelas
        total_parcelas_est = 0
        if eh_parcela:
            try:
                todos = listar_prazos()  # usa cache
                total_parcelas_est = len([p for p in (todos or []) if p.get('parcela_de') == parcela_de])
            except Exception:
                total_parcelas_est = int(total_parcelas or 0) if total_parcelas else 0

        with ui.dialog() as dialog_excluir, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Confirmar Exclusão').classes('text-lg font-bold')
                if eh_parcela:
                    ui.label('Este prazo é uma parcela de um parcelamento.').classes('text-gray-700')
                    if numero_parcela_atual and (total_parcelas or total_parcelas_est):
                        ui.label(f'Parcela {numero_parcela_atual}/{total_parcelas or total_parcelas_est}').classes('text-sm text-gray-600')
                    ui.label('O que você deseja excluir?').classes('text-gray-700')
                else:
                    ui.label(f'Tem certeza que deseja excluir o prazo "{titulo}"?').classes('text-gray-700')

                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_excluir.close()

                    def on_confirm_excluir_apenas():
                        try:
                            sucesso = excluir_prazo(prazo_id)
                            if sucesso:
                                ui.notify('Parcela excluída com sucesso!' if eh_parcela else 'Prazo excluído com sucesso!', type='positive')
                                invalidar_cache_prazos()
                                atualizar_tabelas()
                            else:
                                ui.notify('Erro ao excluir prazo', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao excluir prazo: {e}")
                            ui.notify(f'Erro ao excluir prazo: {str(e)}', type='negative')

                        dialog_excluir.close()

                    ui.button('Cancelar', on_click=on_cancel).props('flat')
                    if eh_parcela:
                        ui.button('Excluir apenas esta parcela', on_click=on_confirm_excluir_apenas).props('color=red')

                        def on_confirm_excluir_todas():
                            try:
                                db = get_db()
                                resultado = excluir_parcelamento_completo(db=db, prazo_pai_id=parcela_de)
                                if resultado.get('sucesso'):
                                    total = resultado.get('total_excluidos') or 0
                                    ui.notify(f'Todas as {total_parcelas_est or total_parcelas or ""} parcelas foram excluídas', type='positive')
                                    invalidar_cache_prazos()
                                    atualizar_tabelas()
                                else:
                                    ui.notify('Erro ao excluir parcelamento completo', type='negative')
                            except ErroParcelamentoPrazo as e:
                                ui.notify(f'Erro ao excluir parcelamento completo: {str(e)}', type='negative')
                            except Exception as e:
                                print(f"[ERROR] Erro ao excluir parcelamento completo: {e}")
                                ui.notify('Erro ao excluir parcelamento completo', type='negative')

                            dialog_excluir.close()

                        btn_todas = ui.button('Excluir todas as parcelas', on_click=on_confirm_excluir_todas).props('color=red')
                        btn_todas.tooltip(f'Isso irá excluir todas as {total_parcelas_est or total_parcelas or "?"} parcelas deste parcelamento.')
                    else:
                        ui.button('Excluir', on_click=on_confirm_excluir_apenas).props('color=red')

        dialog_excluir.open()

    # Função para confirmar conclusão de prazo
    def confirmar_conclusao_prazo(prazo_id: str, titulo: str):
        """Mostra diálogo de confirmação para marcar prazo como concluído."""
        with ui.dialog() as dialog_confirmar, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Confirmar Conclusão').classes('text-lg font-bold')
                ui.label(f'Deseja marcar o prazo "{titulo}" como concluído?').classes('text-gray-700')

                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_confirmar.close()

                    def on_confirm():
                        try:
                            prazo = buscar_prazo_por_id(prazo_id)
                            if not prazo:
                                ui.notify('Prazo não encontrado!', type='negative')
                                dialog_confirmar.close()
                                return

                            prazo['status'] = 'concluido'
                            sucesso = atualizar_prazo(prazo_id, prazo)

                            if sucesso:
                                # Se for recorrente, criar próximo prazo
                                if prazo.get('recorrente'):
                                    novo_id = criar_proximo_prazo_recorrente(prazo)
                                    if novo_id:
                                        # Calcular nova data para exibir na notificação
                                        nova_data = calcular_proximo_prazo_fatal(prazo)
                                        if nova_data:
                                            ui.notify(
                                                f'Prazo concluído! Novo prazo criado para {nova_data.strftime("%d/%m/%Y")}',
                                                type='positive',
                                                timeout=5000
                                            )
                                        else:
                                            ui.notify('Prazo concluído! Novo prazo criado.', type='positive')
                                    else:
                                        ui.notify('Prazo concluído! (Erro ao criar próximo prazo recorrente)', type='warning')
                                else:
                                    ui.notify('Prazo concluído com sucesso!', type='positive')
                                
                                invalidar_cache_prazos()
                                atualizar_tabelas()
                            else:
                                ui.notify('Erro ao atualizar status', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao concluir prazo: {e}")
                            ui.notify(f'Erro ao concluir prazo: {str(e)}', type='negative')

                        dialog_confirmar.close()

                    ui.button('Não', on_click=on_cancel).props('flat')
                    ui.button('Sim', on_click=on_confirm).props('color=positive')

        dialog_confirmar.open()

    # Função para confirmar reabertura de prazo
    def confirmar_reabertura_prazo(prazo_id: str, titulo: str):
        """Mostra diálogo de confirmação para reabrir prazo."""
        with ui.dialog() as dialog_reabrir, ui.card().classes('w-full max-w-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label('Reabrir Prazo').classes('text-lg font-bold')
                ui.label(f'Deseja reabrir o prazo "{titulo}"?').classes('text-gray-700')

                with ui.row().classes('w-full justify-end gap-2'):
                    def on_cancel():
                        dialog_reabrir.close()

                    def on_confirm():
                        try:
                            prazo = buscar_prazo_por_id(prazo_id)
                            if not prazo:
                                ui.notify('Prazo não encontrado!', type='negative')
                                dialog_reabrir.close()
                                return

                            prazo['status'] = 'pendente'
                            sucesso = atualizar_prazo(prazo_id, prazo)

                            if sucesso:
                                invalidar_cache_prazos()
                                atualizar_tabelas()
                                ui.notify('Prazo reaberto!', type='positive')
                            else:
                                ui.notify('Erro ao atualizar status', type='negative')
                        except Exception as e:
                            print(f"[ERROR] Erro ao reabrir prazo: {e}")
                            ui.notify(f'Erro ao reabrir prazo: {str(e)}', type='negative')

                        dialog_reabrir.close()

                    ui.button('Não', on_click=on_cancel).props('flat')
                    ui.button('Sim', on_click=on_confirm).props('color=warning')

        dialog_reabrir.open()

    # Gera breadcrumb padronizado com workspace
    from ...componentes.breadcrumb_helper import gerar_breadcrumbs
    breadcrumbs = gerar_breadcrumbs('Prazos', url_modulo='/prazos')
    
    with layout('Prazos', breadcrumbs=breadcrumbs):
        # Container centralizado e responsivo
        with ui.element('div').classes('container-prazos'):
            # Estado para modo de revisão (apenas sessão - não salva no banco)
            revisao_state = {
                'prazos_revisados': set(),  # IDs dos prazos já revisados nesta sessão
            }

            # filtros_ativos e aplicar_filtros_combinados definidos fora do with para escopo correto
            
            # Declarar função stub para evitar NameError (será redefinida depois)
            def atualizar_estilo_botoes_filtros():
                pass
            
            # Interface de filtros hierárquicos (PRIMEIRO - no topo da página, antes de tudo)
            with ui.row().classes('w-full gap-3 mb-4 flex-wrap items-end'):
                # Grupo 1: Status
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Status:').classes('text-sm font-medium text-gray-600')
                    
                    # Status agora é um SET - toggle adiciona/remove do set
                    def toggle_pendentes():
                        status_set = filtros_ativos['status']
                        if 'pendente' in status_set:
                            status_set.discard('pendente')
                        else:
                            status_set.add('pendente')
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_pendentes = ui.button('Pendentes', on_click=toggle_pendentes).props('size=sm')
                    
                    def toggle_aguardando():
                        status_set = filtros_ativos['status']
                        if 'aguardando_abertura' in status_set:
                            status_set.discard('aguardando_abertura')
                        else:
                            status_set.add('aguardando_abertura')
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_aguardando = ui.button('Aguardando', on_click=toggle_aguardando).props('size=sm')
                    
                    def toggle_atrasados():
                        status_set = filtros_ativos['status']
                        if 'atrasado' in status_set:
                            status_set.discard('atrasado')
                        else:
                            status_set.add('atrasado')
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_atrasados = ui.button('Atrasados', on_click=toggle_atrasados).props('size=sm')
                    
                    def toggle_concluidos():
                        status_set = filtros_ativos['status']
                        if 'concluido' in status_set:
                            status_set.discard('concluido')
                        else:
                            status_set.add('concluido')
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_concluidos = ui.button('Concluídos', on_click=toggle_concluidos).props('size=sm')
                
                # Grupo 2: Temporal
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Temporal:').classes('text-sm font-medium text-gray-600')
                    
                    def toggle_semana():
                        novo_valor = 'semana' if filtros_ativos.get('temporal') != 'semana' else None
                        filtros_ativos['temporal'] = novo_valor
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_semana = ui.button('Semana', on_click=toggle_semana).props('size=sm outline color=grey-6')
                    
                    def toggle_mes():
                        novo_valor = 'mes' if filtros_ativos.get('temporal') != 'mes' else None
                        filtros_ativos['temporal'] = novo_valor
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_mes = ui.button('Mês', on_click=toggle_mes).props('size=sm outline color=grey-6')
                
                # Grupo 3: Tipo
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Tipo:').classes('text-sm font-medium text-gray-600')
                    
                    def toggle_simples():
                        novo_valor = 'simples' if filtros_ativos.get('tipo') != 'simples' else None
                        filtros_ativos['tipo'] = novo_valor
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_simples_filtro = ui.button('Simples', on_click=toggle_simples).props('size=sm outline color=grey-6')
                    
                    def toggle_recorrente():
                        novo_valor = 'recorrente' if filtros_ativos.get('tipo') != 'recorrente' else None
                        filtros_ativos['tipo'] = novo_valor
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_recorrente_filtro = ui.button('Recorrente', on_click=toggle_recorrente).props('size=sm outline color=grey-6')
                    
                    def toggle_parcelado():
                        novo_valor = 'parcelado' if filtros_ativos.get('tipo') != 'parcelado' else None
                        filtros_ativos['tipo'] = novo_valor
                        atualizar_estilo_botoes_filtros()
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    btn_parcelado_filtro = ui.button('Parcelado', on_click=toggle_parcelado).props('size=sm outline color=grey-6')
                
                # Grupo 4: Responsável
                with ui.row().classes('gap-2 items-center'):
                    def on_responsavel_change(e):
                        filtros_ativos['responsavel_id'] = e.value if e.value != 'None' else None
                        if renderizar_conteudo_ref_global[0]:
                            renderizar_conteudo_ref_global[0].refresh()
                    
                    select_responsavel = ui.select(
                        options={None: 'Todos', **usuarios_opcoes},
                        label='Responsável',
                        value=None,
                        on_change=on_responsavel_change
                    ).classes('w-48').props('outlined dense clearable')
            
            # Header com botão Adicionar Prazo
            with ui.row().classes('w-full gap-4 mb-4 items-center justify-end'):
                ui.button('Adicionar Prazo', icon='add', on_click=open_dialog_novo).props('color=primary').classes('font-bold')
            
            # Função para atualizar estilo dos botões baseado nos filtros ativos (definida DEPOIS dos botões)
            def atualizar_estilo_botoes_filtros():
                """Atualiza estilo visual dos botões conforme filtros ativos."""
                # Status - agora é um SET, então verificamos se cada status está no set
                status_set = filtros_ativos.get('status', set())
                
                # Cor verde padrão do sistema: #223631
                if 'pendente' in status_set:
                    btn_pendentes.props(remove='outline')
                    btn_pendentes.style('background-color: #223631 !important; color: white !important;')
                else:
                    btn_pendentes.props('outline')
                    btn_pendentes.style('background-color: transparent !important; color: #223631 !important; border-color: #223631 !important;')
                
                if 'aguardando_abertura' in status_set:
                    btn_aguardando.props(remove='outline')
                    btn_aguardando.style('background-color: #223631 !important; color: white !important;')
                else:
                    btn_aguardando.props('outline')
                    btn_aguardando.style('background-color: transparent !important; color: #223631 !important; border-color: #223631 !important;')
                
                # Atrasados: vermelho preenchido com texto branco
                if 'atrasado' in status_set:
                    btn_atrasados.props(remove='outline')
                    btn_atrasados.style('background-color: #C62828 !important; color: white !important;')
                else:
                    btn_atrasados.props('outline')
                    btn_atrasados.style('background-color: transparent !important; color: #C62828 !important; border-color: #C62828 !important;')
                
                if 'concluido' in status_set:
                    btn_concluidos.props(remove='outline')
                    btn_concluidos.style('background-color: #223631 !important; color: white !important;')
                else:
                    btn_concluidos.props('outline')
                    btn_concluidos.style('background-color: transparent !important; color: #223631 !important; border-color: #223631 !important;')
                
                # Temporal
                temporal_atual = filtros_ativos.get('temporal')
                if temporal_atual == 'semana':
                    btn_semana.props('color=primary unelevated')
                else:
                    btn_semana.props('outline color=grey-6')
                
                if temporal_atual == 'mes':
                    btn_mes.props('color=primary unelevated')
                else:
                    btn_mes.props('outline color=grey-6')
                
                # Tipo
                tipo_atual = filtros_ativos.get('tipo')
                if tipo_atual == 'simples':
                    btn_simples_filtro.props('color=primary unelevated')
                else:
                    btn_simples_filtro.props('outline color=grey-6')
                
                if tipo_atual == 'recorrente':
                    btn_recorrente_filtro.props('color=primary unelevated')
                else:
                    btn_recorrente_filtro.props('outline color=grey-6')
                
                if tipo_atual == 'parcelado':
                    btn_parcelado_filtro.props('color=primary unelevated')
                else:
                    btn_parcelado_filtro.props('outline color=grey-6')
            
            # Inicializar estilos dos botões
            atualizar_estilo_botoes_filtros()
            
            # Container para área de conteúdo (tabela) - CRIADO DEPOIS DOS FILTROS
            conteudo_container = ui.column().classes('w-full')
        
        # Função para criar tabela de prazos (sem coluna de status) - PRIMEIRO
        def criar_tabela_prazos(prazos_lista: List[Dict[str, Any]], status_filtro: str):
            """Cria tabela de prazos com os dados fornecidos."""
            # Ordenar prazos por prioridade (atrasados, aguardando abertura, resto)
            prazos_lista = ordenar_prazos_prioridade(prazos_lista)

            if not prazos_lista:
                # Mensagem quando não há prazos
                if status_filtro == 'pendente':
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('check_circle', size='48px').classes('text-green-300 mb-4')
                        ui.label('Nenhum prazo pendente').classes(
                            'text-gray-500 text-lg font-medium mb-2'
                        )
                        ui.label('Todos os prazos estão concluídos!').classes(
                            'text-sm text-gray-400 text-center'
                        )
                elif status_filtro == 'concluido':
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('pending_actions', size='48px').classes('text-yellow-300 mb-4')
                        ui.label('Nenhum prazo concluído').classes(
                            'text-gray-500 text-lg font-medium mb-2'
                        )
                        ui.label('Conclua alguns prazos para vê-los aqui').classes(
                            'text-sm text-gray-400 text-center'
                        )
                else:  # semana
                    with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                        ui.icon('event_busy', size='48px').classes('text-gray-300 mb-4')
                        ui.label('Nenhum prazo nesta semana').classes(
                            'text-gray-500 text-lg font-medium mb-2'
                        )
                        ui.label('Selecione outra semana ou adicione novos prazos').classes(
                            'text-sm text-gray-400 text-center'
                        )
                return

            # Definir colunas da tabela (sem coluna "Status" e sem "Recorrente")
            columns = [
                {'name': 'concluido', 'label': '', 'field': 'concluido', 'align': 'center', 'style': 'width: 50px;'},
                {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'style': 'min-width: 280px;'},
                {'name': 'responsaveis', 'label': 'Responsáveis', 'field': 'responsaveis', 'align': 'left', 'style': 'width: 180px;'},
                {'name': 'clientes', 'label': 'Clientes', 'field': 'clientes', 'align': 'left', 'style': 'width: 180px;'},
                {'name': 'prazo_seguranca', 'label': 'Prazo de Segurança', 'field': 'prazo_seguranca', 'align': 'center', 'style': 'width: 130px;'},
                {'name': 'prazo_fatal', 'label': 'Prazo Fatal', 'field': 'prazo_fatal', 'align': 'center', 'style': 'width: 110px;'},
                {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 80px;'},
            ]

            # Preparar linhas
            rows = []
            for indice, prazo in enumerate(prazos_lista):
                # Formatações - usando cache local (sem consultas Firebase)
                titulo = formatar_titulo_prazo(prazo)

                responsaveis_ids = prazo.get('responsaveis', [])
                responsaveis_texto = formatar_responsaveis(responsaveis_ids, usuarios_opcoes)

                clientes_ids = prazo.get('clientes', [])
                clientes_texto = formatar_lista_nomes(clientes_ids, clientes_opcoes)

                prazo_fatal_ts = prazo.get('prazo_fatal')
                prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
                prazo_seguranca_texto = calcular_prazo_seguranca(prazo_fatal_ts)

                status = prazo.get('status', 'pendente')
                esta_concluido = status.lower() == 'concluido'
                esta_atrasado = verificar_prazo_atrasado(prazo_fatal_ts, status)
                estado_abertura = prazo.get('estado_abertura', 'aberto')
                esta_aguardando_abertura = estado_abertura == 'aguardando_abertura'

                # Detecção de parcelamento (badge) - usa campos do backend
                is_parcelado = bool(
                    prazo.get('parcela_de') is not None or
                    prazo.get('numero_parcela_atual') is not None or
                    prazo.get('total_parcelas') is not None
                )

                rows.append({
                    'id': prazo.get('_id'),
                    '_indice': indice,
                    'concluido': esta_concluido,
                    'atrasado': esta_atrasado,
                    'aguardando_abertura': esta_aguardando_abertura,
                    'titulo': titulo,
                    # Campos extras para UI/ações
                    'is_parcelado': is_parcelado,
                    'parcela_de': prazo.get('parcela_de'),
                    'numero_parcela_atual': prazo.get('numero_parcela_atual'),
                    'total_parcelas': prazo.get('total_parcelas'),
                    'responsaveis': responsaveis_texto,
                    'clientes': clientes_texto,
                    'prazo_seguranca': prazo_seguranca_texto,
                    'prazo_fatal': prazo_fatal_texto,
                    'acoes': prazo.get('_id'),
                })

            # Wrapper para scroll horizontal em telas menores
            with ui.element('div').classes('tabela-prazos-wrapper'):
                # Criar tabela
                table = ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='id'
                ).classes('w-full tabela-prazos').props('flat dense')

            # Slot para linha completa - aplica cor de fundo para prazos atrasados (vermelho) e aguardando abertura (azul)
            table.add_slot('body', '''
                <q-tr :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2 !important;' : (props.row.aguardando_abertura ? 'background-color: #BBDEFB !important;' : '')">
                    <q-td key="concluido" :props="props" style="vertical-align: middle;">
                        <q-checkbox
                            :model-value="props.row.concluido"
                            @update:model-value="(val) => $parent.$emit('toggle-status', {row: props.row, value: val})"
                            color="green"
                            size="md"
                            round
                        >
                            <q-tooltip>{{ props.row.concluido ? "Reabrir prazo" : "Marcar como concluído" }}</q-tooltip>
                        </q-checkbox>
                    </q-td>
                    <q-td key="titulo" :props="props" style="vertical-align: middle;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span>{{ props.row.titulo }}</span>
                            <q-badge
                                v-if="props.row.is_parcelado"
                                style="background-color:#c7d2fe; color:#111827; border: 1px solid rgba(0,0,0,0.08);"
                                class="px-2 py-1"
                            >
                                Parcelado
                            </q-badge>
                        </div>
                    </q-td>
                    <q-td key="responsaveis" :props="props" style="vertical-align: middle;">
                        {{ props.row.responsaveis }}
                    </q-td>
                    <q-td key="clientes" :props="props" style="vertical-align: middle;">
                        {{ props.row.clientes }}
                    </q-td>
                    <q-td key="prazo_seguranca" :props="props" style="vertical-align: middle; text-align: center;">
                        <span class="celula-prazo-seguranca">{{ props.row.prazo_seguranca }}</span>
                    </q-td>
                    <q-td key="prazo_fatal" :props="props" :style="props.row.atrasado ? 'vertical-align: middle; text-align: center; font-weight: bold;' : 'vertical-align: middle; text-align: center;'">
                        <span class="celula-prazo-fatal" :style="props.row.atrasado ? 'background-color: #EF9A9A !important;' : ''">{{ props.row.prazo_fatal }}</span>
                    </q-td>
                    <q-td key="acoes" :props="props" style="vertical-align: middle;">
                        <q-btn flat round dense icon="edit" color="primary" size="sm" @click="$parent.$emit('edit', props.row)">
                            <q-tooltip>Editar</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense icon="delete" color="negative" size="sm" @click="$parent.$emit('delete', props.row)">
                            <q-tooltip>Excluir</q-tooltip>
                        </q-btn>
                    </q-td>
                </q-tr>
            ''')

            # Handler para toggle de status COM CONFIRMAÇÃO
            def on_toggle_status(data):
                """Handler para alterar status via checkbox - abre diálogo de confirmação."""
                prazo_row = data.get('row')
                novo_valor = data.get('value')
                prazo_id = prazo_row.get('id')
                titulo = prazo_row.get('titulo', 'este prazo')

                if prazo_id:
                    if novo_valor:
                        # Marcar como concluído - pedir confirmação
                        confirmar_conclusao_prazo(prazo_id, titulo)
                    else:
                        # Reabrir prazo - pedir confirmação
                        confirmar_reabertura_prazo(prazo_id, titulo)

            # Handlers para ações
            def on_edit_tb(prazo_row):
                """Handler para editar prazo."""
                # Validação defensiva
                if prazo_row is None or not isinstance(prazo_row, dict):
                    ui.notify('Erro: Dados do prazo não recebidos', type='negative')
                    return
                
                prazo_id = prazo_row.get('id')
                if prazo_id:
                    abrir_modal_edicao(prazo_id)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            def on_delete_tb(prazo_row):
                """Handler para excluir prazo."""
                if prazo_row is None or not isinstance(prazo_row, dict):
                    ui.notify('Erro: Dados do prazo não recebidos', type='negative')
                    return
                
                prazo_id = prazo_row.get('id')
                if prazo_id:
                    excluir_prazo_com_confirmacao(prazo_row)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            table.on('toggle-status', lambda e: on_toggle_status(e.args))
            table.on('edit', lambda e: on_edit_tb(e.args))
            table.on('delete', lambda e: on_delete_tb(e.args))
        
        # Função para atualizar visualização baseada nos filtros (DEPOIS de criar_tabela_prazos estar definida)
        @ui.refreshable
        def renderizar_conteudo():
            """Renderiza conteúdo baseado nos filtros ativos."""
            try:
                todos_prazos = listar_prazos()
                prazos_filtrados = aplicar_filtros_combinados(todos_prazos)
                
                # Se filtro temporal está ativo, aplicar filtro de semana/mês
                if filtros_ativos['temporal'] == 'semana':
                    hoje = date.today()
                    inicio_semana = hoje - timedelta(days=hoje.weekday())
                    fim_semana = inicio_semana + timedelta(days=6)
                    prazos_filtrados = filtrar_prazos_por_semana(prazos_filtrados, inicio_semana, fim_semana)
                elif filtros_ativos['temporal'] == 'mes':
                    hoje = date.today()
                    inicio_mes = date(hoje.year, hoje.month, 1)
                    if hoje.month == 12:
                        fim_mes = date(hoje.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        fim_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
                    prazos_filtrados = [
                        p for p in prazos_filtrados
                        if p.get('prazo_fatal') and inicio_mes <= datetime.fromtimestamp(p.get('prazo_fatal')).date() <= fim_mes
                    ]
                
                # Criar tabela diretamente (sem container - @ui.refreshable gerencia isso)
                prazos_filtrados = ordenar_prazos_prioridade(prazos_filtrados)
                criar_tabela_prazos(prazos_filtrados, filtros_ativos['status'] or 'todos')
                
            except Exception as e:
                print(f"[ERROR] Erro ao renderizar conteúdo: {e}")
                import traceback
                traceback.print_exc()
                ui.notify('Erro ao carregar prazos', type='negative')
        
        # Salvar referência global para atualizar_tabelas() e para os callbacks dos botões
        renderizar_conteudo_ref_global[0] = renderizar_conteudo
        
        # Renderizar conteúdo inicial dentro do container
        with conteudo_container:
            renderizar_conteudo()

        # Função para criar tabela COM coluna de status (para aba Por Semana)
        def criar_tabela_prazos_com_status(prazos_lista: List[Dict[str, Any]]):
            """Cria tabela de prazos com coluna de status (para visualização Por Semana)."""
            # Ordenar prazos por prioridade (atrasados, aguardando abertura, resto)
            prazos_lista = ordenar_prazos_prioridade(prazos_lista)

            if not prazos_lista:
                with ui.card().classes('w-full p-8 flex flex-col items-center justify-center'):
                    ui.icon('event_busy', size='48px').classes('text-gray-300 mb-4')
                    ui.label('Nenhum prazo nesta semana').classes(
                        'text-gray-500 text-lg font-medium mb-2'
                    )
                    ui.label('Selecione outra semana ou adicione novos prazos').classes(
                        'text-sm text-gray-400 text-center'
                    )
                return

            # Definir colunas da tabela COM coluna de status
            columns = [
                {'name': 'concluido', 'label': '', 'field': 'concluido', 'align': 'center', 'style': 'width: 50px;'},
                {'name': 'titulo', 'label': 'Título', 'field': 'titulo', 'align': 'left', 'style': 'min-width: 280px;'},
                {'name': 'responsaveis', 'label': 'Responsáveis', 'field': 'responsaveis', 'align': 'left', 'style': 'width: 160px;'},
                {'name': 'prazo_seguranca', 'label': 'Prazo Seg.', 'field': 'prazo_seguranca', 'align': 'center', 'style': 'width: 100px;'},
                {'name': 'prazo_fatal', 'label': 'Prazo Fatal', 'field': 'prazo_fatal', 'align': 'center', 'style': 'width: 100px;'},
                {'name': 'status', 'label': 'Status', 'field': 'status_label', 'align': 'center', 'style': 'width: 100px;'},
                {'name': 'acoes', 'label': 'Ações', 'field': 'acoes', 'align': 'center', 'style': 'width: 80px;'},
            ]

            # Preparar linhas
            rows = []
            for indice, prazo in enumerate(prazos_lista):
                titulo = formatar_titulo_prazo(prazo)

                responsaveis_ids = prazo.get('responsaveis', [])
                responsaveis_texto = formatar_responsaveis(responsaveis_ids, usuarios_opcoes)

                prazo_fatal_ts = prazo.get('prazo_fatal')
                prazo_fatal_texto = formatar_data_prazo(prazo_fatal_ts)
                prazo_seguranca_texto = calcular_prazo_seguranca(prazo_fatal_ts)

                status = prazo.get('status', 'pendente')
                esta_concluido = status.lower() == 'concluido'
                esta_atrasado = verificar_prazo_atrasado(prazo_fatal_ts, status)
                estado_abertura = prazo.get('estado_abertura', 'aberto')
                esta_aguardando_abertura = estado_abertura == 'aguardando_abertura'

                # Determinar status_label para exibição
                if esta_concluido:
                    status_label = 'Concluído'
                    status_value = 'concluido'
                elif esta_atrasado:
                    status_label = 'Atrasado'
                    status_value = 'atrasado'
                else:
                    status_label = 'Pendente'
                    status_value = 'pendente'

                is_parcelado = bool(
                    prazo.get('parcela_de') is not None or
                    prazo.get('numero_parcela_atual') is not None or
                    prazo.get('total_parcelas') is not None
                )

                rows.append({
                    'id': prazo.get('_id'),
                    '_indice': indice,
                    'concluido': esta_concluido,
                    'atrasado': esta_atrasado,
                    'aguardando_abertura': esta_aguardando_abertura,
                    'titulo': titulo,
                    'is_parcelado': is_parcelado,
                    'parcela_de': prazo.get('parcela_de'),
                    'numero_parcela_atual': prazo.get('numero_parcela_atual'),
                    'total_parcelas': prazo.get('total_parcelas'),
                    'responsaveis': responsaveis_texto,
                    'prazo_seguranca': prazo_seguranca_texto,
                    'prazo_fatal': prazo_fatal_texto,
                    'status_label': status_label,
                    'status_value': status_value,
                    'acoes': prazo.get('_id'),
                })

            # Wrapper para scroll horizontal em telas menores
            with ui.element('div').classes('tabela-prazos-wrapper'):
                # Criar tabela
                table = ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='id'
                ).classes('w-full tabela-prazos').props('flat dense')

            # Slot para linha completa - aplica cor de fundo para prazos atrasados (vermelho) e aguardando abertura (azul)
            table.add_slot('body', '''
                <q-tr :props="props" :style="props.row.atrasado ? 'background-color: #FFCDD2 !important;' : (props.row.aguardando_abertura ? 'background-color: #BBDEFB !important;' : '')">
                    <q-td key="concluido" :props="props" style="vertical-align: middle;">
                        <q-checkbox
                            :model-value="props.row.concluido"
                            @update:model-value="(val) => $parent.$emit('toggle-status', {row: props.row, value: val})"
                            color="green"
                            size="md"
                            round
                        >
                            <q-tooltip>{{ props.row.concluido ? "Reabrir prazo" : "Marcar como concluído" }}</q-tooltip>
                        </q-checkbox>
                    </q-td>
                    <q-td key="titulo" :props="props" style="vertical-align: middle;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span>{{ props.row.titulo }}</span>
                            <q-badge
                                v-if="props.row.is_parcelado"
                                style="background-color:#c7d2fe; color:#111827; border: 1px solid rgba(0,0,0,0.08);"
                                class="px-2 py-1"
                            >
                                Parcelado
                            </q-badge>
                        </div>
                    </q-td>
                    <q-td key="responsaveis" :props="props" style="vertical-align: middle;">
                        {{ props.row.responsaveis }}
                    </q-td>
                    <q-td key="prazo_seguranca" :props="props" style="vertical-align: middle; text-align: center;">
                        <span class="celula-prazo-seguranca">{{ props.row.prazo_seguranca }}</span>
                    </q-td>
                    <q-td key="prazo_fatal" :props="props" :style="props.row.atrasado ? 'vertical-align: middle; text-align: center; font-weight: bold;' : 'vertical-align: middle; text-align: center;'">
                        <span class="celula-prazo-fatal" :style="props.row.atrasado ? 'background-color: #EF9A9A !important;' : ''">{{ props.row.prazo_fatal }}</span>
                    </q-td>
                    <q-td key="status" :props="props" style="vertical-align: middle; text-align: center;">
                        <q-badge
                            :style="props.row.status_value === 'atrasado' ? 'background-color: #EF5350; color: white;' :
                                    props.row.status_value === 'concluido' ? 'background-color: #4CAF50; color: white;' :
                                    'background-color: #FFC107; color: black;'"
                            class="px-3 py-1"
                        >
                            {{ props.row.status_label }}
                        </q-badge>
                    </q-td>
                    <q-td key="acoes" :props="props" style="vertical-align: middle;">
                        <q-btn flat round dense icon="edit" color="primary" size="sm" @click="$parent.$emit('edit', props.row)">
                            <q-tooltip>Editar</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense icon="delete" color="negative" size="sm" @click="$parent.$emit('delete', props.row)">
                            <q-tooltip>Excluir</q-tooltip>
                        </q-btn>
                    </q-td>
                </q-tr>
            ''')

            # Handler para toggle de status
            def on_toggle_status(data):
                prazo_row = data.get('row')
                novo_valor = data.get('value')
                prazo_id = prazo_row.get('id')
                titulo = prazo_row.get('titulo', 'este prazo')

                if prazo_id:
                    if novo_valor:
                        confirmar_conclusao_prazo(prazo_id, titulo)
                    else:
                        confirmar_reabertura_prazo(prazo_id, titulo)

            def on_edit_tb(prazo_row):
                """Handler para editar prazo (tabela com status)."""
                if prazo_row is None or not isinstance(prazo_row, dict):
                    ui.notify('Erro: Dados do prazo não recebidos', type='negative')
                    return
                
                prazo_id = prazo_row.get('id')
                if prazo_id:
                    abrir_modal_edicao(prazo_id)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            def on_delete_tb(prazo_row):
                """Handler para excluir prazo (tabela com status)."""
                if prazo_row is None or not isinstance(prazo_row, dict):
                    ui.notify('Erro: Dados do prazo não recebidos', type='negative')
                    return
                
                prazo_id = prazo_row.get('id')
                if prazo_id:
                    excluir_prazo_com_confirmacao(prazo_row)
                else:
                    ui.notify('Erro: ID do prazo não encontrado', type='negative')

            table.on('toggle-status', lambda e: on_toggle_status(e.args))
            table.on('edit', lambda e: on_edit_tb(e.args))
            table.on('delete', lambda e: on_delete_tb(e.args))

    print("[PRAZOS] Página carregada com sucesso!")
