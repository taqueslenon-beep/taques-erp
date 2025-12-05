"""
Serviço de dados para o módulo Painel.
Carregamento, agregação e filtragem de dados.
"""
from collections import Counter
from typing import Dict, List, Any, Tuple

from .helpers import get_case_type, safe_float


class PainelDataService:
    """
    Serviço que gerencia todos os dados do painel.
    Carrega dados uma única vez e fornece métodos para agregação.
    """
    
    def __init__(self, cases: List[dict], processes: List[dict], 
                 clients: List[dict], opposing_parties: List[dict]):
        self._cases = cases
        self._processes = processes
        self._clients = clients
        self._opposing = opposing_parties
        
        # Mapa de casos por título para lookups rápidos
        self._cases_by_title = {c.get('title'): c for c in cases if c.get('title')}
        
        # Pré-calcula totais
        self.total_casos = len(cases)
        self.total_processos = len(processes)
        self.total_cenarios = sum(len(proc.get('scenarios', [])) for proc in processes)
    
    # =========================================================================
    # PROPRIEDADES DE ACESSO
    # =========================================================================
    @property
    def cases(self) -> List[dict]:
        return self._cases
    
    @property
    def processes(self) -> List[dict]:
        return self._processes
    
    @property
    def clients(self) -> List[dict]:
        return self._clients
    
    @property
    def opposing_parties(self) -> List[dict]:
        return self._opposing
    
    # =========================================================================
    # FILTROS POR ESTADO
    # =========================================================================
    def get_cases_by_state(self) -> Dict[str, int]:
        """Conta casos por estado."""
        return {
            'Paraná': len([c for c in self._cases if c.get('state') == 'Paraná']),
            'Santa Catarina': len([c for c in self._cases if c.get('state') == 'Santa Catarina']),
        }
    
    def get_processes_by_state(self) -> Dict[str, int]:
        """Conta processos por estado (baseado no caso vinculado)."""
        processos_parana = 0
        processos_sc = 0
        
        for proc in self._processes:
            proc_cases = proc.get('cases', [])
            for case_title in proc_cases:
                case = self._cases_by_title.get(case_title)
                if case:
                    if case.get('state') == 'Paraná':
                        processos_parana += 1
                        break
                    elif case.get('state') == 'Santa Catarina':
                        processos_sc += 1
                        break
        
        return {
            'Paraná': processos_parana,
            'Santa Catarina': processos_sc,
        }
    
    # =========================================================================
    # FILTROS POR TIPO DE CASO
    # =========================================================================
    def get_cases_by_type(self) -> Dict[str, List[dict]]:
        """Separa casos por tipo (Antigo/Novo/Futuro)."""
        return {
            'Antigo': [c for c in self._cases if get_case_type(c) == 'Antigo'],
            'Novo': [c for c in self._cases if get_case_type(c) == 'Novo'],
            'Futuro': [c for c in self._cases if get_case_type(c) == 'Futuro'],
        }
    
    def get_cases_type_counts(self) -> Dict[str, int]:
        """Conta casos por tipo."""
        cases_by_type = self.get_cases_by_type()
        return {k: len(v) for k, v in cases_by_type.items()}
    
    # =========================================================================
    # FILTROS POR CATEGORIA
    # =========================================================================
    def get_cases_by_category(self) -> Dict[str, int]:
        """Conta casos por categoria (Contencioso/Consultivo)."""
        return {
            'Contencioso': len([c for c in self._cases if c.get('category', 'Contencioso') == 'Contencioso']),
            'Consultivo': len([c for c in self._cases if c.get('category') == 'Consultivo']),
        }
    
    # =========================================================================
    # CONTAGENS POR STATUS
    # =========================================================================
    def get_cases_by_status(self) -> List[Tuple[str, int]]:
        """Conta casos por status, ordenado do maior para menor."""
        counter = Counter(case.get('status', 'Sem status') for case in self._cases)
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    def get_processes_by_status(self) -> List[Tuple[str, int]]:
        """Conta processos por status, ordenado do maior para menor."""
        counter = Counter(proc.get('status', 'Sem status') for proc in self._processes)
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    # =========================================================================
    # CÁLCULOS DE PROCESSOS POR STATUS (CONCLUÍDOS/ATIVOS)
    # =========================================================================
    def get_total_processos(self) -> int:
        """
        Retorna o total de processos cadastrados.
        
        Returns:
            Número total de processos (todos os status)
        """
        return self.total_processos
    
    def get_processos_concluidos(self) -> int:
        """
        Conta processos concluídos.
        
        Mapeamento de status:
        - "Concluído"
        - "Concluído com pendências"
        
        Returns:
            Número de processos concluídos
        """
        try:
            status_concluidos = {'Concluído', 'Concluído com pendências'}
            count = sum(1 for proc in self._processes 
                       if proc.get('status') in status_concluidos)
            return count
        except Exception as e:
            print(f"Erro ao calcular processos concluídos: {e}")
            return 0
    
    def get_processos_ativos(self) -> int:
        """
        Conta processos ativos (em tramitação).
        
        Mapeamento de status:
        - "Em andamento"
        - "Em monitoramento"
        
        Returns:
            Número de processos ativos
        """
        try:
            status_ativos = {'Em andamento', 'Em monitoramento'}
            count = sum(1 for proc in self._processes 
                       if proc.get('status') in status_ativos)
            return count
        except Exception as e:
            print(f"Erro ao calcular processos ativos: {e}")
            return 0
    
    def get_processos_previstos(self) -> int:
        """
        Conta processos futuros/previstos.
        
        Mapeamento de status:
        - "Futuro/Previsto"
        
        Returns:
            Número de processos previstos
        """
        try:
            count = sum(1 for proc in self._processes 
                       if proc.get('status') == 'Futuro/Previsto')
            return count
        except Exception as e:
            print(f"Erro ao calcular processos previstos: {e}")
            return 0
    
    # =========================================================================
    # CONTAGENS POR CLIENTE
    # =========================================================================
    def get_cases_by_client(self) -> List[Tuple[str, int]]:
        """Conta casos por cliente, ordenado do maior para menor."""
        counter = Counter()
        for caso in self._cases:
            for client in caso.get('clients', []):
                counter[client] += 1
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    def get_processes_by_client(self) -> List[Tuple[str, int]]:
        """Conta processos por cliente, ordenado do maior para menor."""
        counter = Counter()
        for proc in self._processes:
            for client in proc.get('clients', []):
                counter[client] += 1
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    def get_processes_by_client_filtered(self, status_filter: str) -> List[Tuple[str, int]]:
        """
        Conta processos por cliente com filtro de status, ordenado do maior para menor.
        
        Args:
            status_filter: 'todos' | 'em_andamento' | 'concluidos'
                - 'todos': retorna todos os processos
                - 'em_andamento': filtra por status in {'Em andamento', 'Em monitoramento'}
                - 'concluidos': filtra por status in {'Concluído', 'Concluído com pendências'}
        
        Returns:
            Lista de tuplas (cliente, quantidade) ordenada do maior para menor
        """
        counter = Counter()
        
        # Definir status permitidos baseado no filtro
        if status_filter == 'todos':
            # Não filtra - inclui todos os processos
            allowed_statuses = None
        elif status_filter == 'em_andamento':
            allowed_statuses = {'Em andamento', 'Em monitoramento'}
        elif status_filter == 'concluidos':
            allowed_statuses = {'Concluído', 'Concluído com pendências'}
        else:
            # Filtro inválido - retorna vazio
            return []
        
        # Contar processos por cliente aplicando o filtro
        for proc in self._processes:
            proc_status = proc.get('status', '')
            
            # Se não há filtro ou o status está permitido, conta o processo
            if allowed_statuses is None or proc_status in allowed_statuses:
                for client in proc.get('clients', []):
                    counter[client] += 1
        
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    # =========================================================================
    # CONTAGENS POR PARTE CONTRÁRIA
    # =========================================================================
    def get_processes_by_opposing_party(self) -> List[Tuple[str, int]]:
        """Conta processos por parte contrária, ordenado do maior para menor."""
        counter = Counter()
        for proc in self._processes:
            for opposing in proc.get('opposing_parties', []):
                counter[opposing] += 1
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    def get_processes_by_opposing_party_filtered(self, status_filter: str) -> List[Tuple[str, int]]:
        """
        Conta processos por parte contrária com filtro de status, ordenado do maior para menor.
        
        Args:
            status_filter: 'todos' | 'em_andamento' | 'concluidos'
                - 'todos': retorna todos os processos
                - 'em_andamento': filtra por status in {'Em andamento', 'Em monitoramento'}
                - 'concluidos': filtra por status in {'Concluído', 'Concluído com pendências'}
        
        Returns:
            Lista de tuplas (parte contrária, quantidade) ordenada do maior para menor
        """
        counter = Counter()
        
        # Definir status permitidos baseado no filtro
        if status_filter == 'todos':
            # Não filtra - inclui todos os processos
            allowed_statuses = None
        elif status_filter == 'em_andamento':
            allowed_statuses = {'Em andamento', 'Em monitoramento'}
        elif status_filter == 'concluidos':
            allowed_statuses = {'Concluído', 'Concluído com pendências'}
        else:
            # Filtro inválido - retorna vazio
            return []
        
        # Contar processos por parte contrária aplicando o filtro
        for proc in self._processes:
            proc_status = proc.get('status', '')
            
            # Se não há filtro ou o status está permitido, conta o processo
            if allowed_statuses is None or proc_status in allowed_statuses:
                for opposing in proc.get('opposing_parties', []):
                    counter[opposing] += 1
        
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    # =========================================================================
    # CONTAGENS POR ÁREA
    # =========================================================================
    def get_processes_by_area(self) -> List[Tuple[str, int]]:
        """Conta processos por área jurídica, ordenado do maior para menor."""
        counter = Counter()
        for proc in self._processes:
            area = proc.get('area') or 'Não informado'
            counter[area] += 1
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    # =========================================================================
    # DADOS TEMPORAIS
    # =========================================================================
    def get_cases_by_year(self) -> Counter:
        """Conta casos por ano."""
        counter = Counter()
        for case in self._cases:
            year = case.get('year')
            if year:
                counter[str(year)] += 1
        return counter
    
    def get_processes_by_year(self) -> Counter:
        """Conta processos por ano, extraindo o ano do campo data_abertura."""
        counter = Counter()
        for proc in self._processes:
            # Tenta primeiro o campo year (se existir)
            year = proc.get('year')
            
            # Se não tiver year, tenta extrair de data_abertura
            if not year:
                data_abertura = proc.get('data_abertura', '')
                if data_abertura:
                    data_abertura = str(data_abertura).strip()
                    
                    # Formato: apenas ano (AAAA)
                    if len(data_abertura) == 4 and data_abertura.isdigit():
                        year = data_abertura
                    # Formato: MM/AAAA ou DD/MM/AAAA
                    elif '/' in data_abertura:
                        partes = data_abertura.split('/')
                        # Se tiver 2 partes: MM/AAAA -> pega a última
                        # Se tiver 3 partes: DD/MM/AAAA -> pega a última
                        if len(partes) >= 2:
                            year = partes[-1].strip()
                    # Formato: AAAA-MM-DD (ISO)
                    elif '-' in data_abertura:
                        partes = data_abertura.split('-')
                        if len(partes) >= 1:
                            year = partes[0].strip()
            
            if year:
                # Valida se é um ano válido (4 dígitos)
                year_str = str(year).strip()
                if len(year_str) == 4 and year_str.isdigit():
                    counter[year_str] += 1
        return counter
    
    # =========================================================================
    # DADOS FINANCEIROS
    # =========================================================================
    def collect_financial_data(self) -> Dict[str, Any]:
        """Coleta todos os valores financeiros dos cálculos dos casos."""
        total_exposicao = 0.0
        total_pago = 0.0
        total_futuro = 0.0
        total_em_analise = 0.0
        total_confirmado = 0.0
        
        detalhes_aberto = []
        detalhes_pago = []
        detalhes_futuro = []
        
        for case in self._cases:
            calculations = case.get('calculations', [])
            case_title = case.get('title', 'Sem título')
            
            for calc in calculations:
                if calc.get('type') == 'Financeiro':
                    finance_rows = calc.get('finance_rows', [])
                    
                    for row in finance_rows:
                        value = safe_float(row.get('value', 0.0))
                        status = row.get('status', 'Em análise')
                        description = row.get('description', 'Sem descrição')
                        
                        if status == 'Recuperado':
                            total_pago += value
                            detalhes_pago.append({
                                'case': case_title,
                                'description': description,
                                'value': value
                            })
                        elif status == 'Estimado':
                            total_futuro += value
                            detalhes_futuro.append({
                                'case': case_title,
                                'description': description,
                                'value': value
                            })
                        elif status == 'Em análise':
                            total_em_analise += value
                            total_exposicao += value
                            detalhes_aberto.append({
                                'case': case_title,
                                'description': description,
                                'value': value,
                                'status': status
                            })
                        elif status == 'Confirmado':
                            total_confirmado += value
                            total_exposicao += value
                            detalhes_aberto.append({
                                'case': case_title,
                                'description': description,
                                'value': value,
                                'status': status
                            })
        
        return {
            'exposicao': total_exposicao,
            'pago': total_pago,
            'futuro': total_futuro,
            'em_analise': total_em_analise,
            'confirmado': total_confirmado,
            'detalhes_aberto': detalhes_aberto,
            'detalhes_pago': detalhes_pago,
            'detalhes_futuro': detalhes_futuro,
        }
    
    # =========================================================================
    # DADOS DO HEATMAP
    # =========================================================================
    def build_heatmap_data(self) -> Dict[str, Any]:
        """Prepara dados para o mapa de calor (empresas x áreas)."""
        heatmap_data = {}
        empresas_set = set()
        areas_set = set()
        
        # Coletar dados dos casos
        for case in self._cases:
            clients = case.get('clients', [])
            case_processes = case.get('processes', [])
            for proc_title in case_processes:
                for proc in self._processes:
                    if proc.get('title') == proc_title:
                        area = proc.get('area') or 'Não informado'
                        areas_set.add(area)
                        for client in clients:
                            empresas_set.add(client)
                            if client not in heatmap_data:
                                heatmap_data[client] = {}
                            if area not in heatmap_data[client]:
                                heatmap_data[client][area] = 0
                            heatmap_data[client][area] += 1
                        break
        
        # Coletar dados dos processos diretamente
        for proc in self._processes:
            area = proc.get('area') or 'Não informado'
            areas_set.add(area)
            clients = proc.get('clients', [])
            for client in clients:
                empresas_set.add(client)
                if client not in heatmap_data:
                    heatmap_data[client] = {}
                if area not in heatmap_data[client]:
                    heatmap_data[client][area] = 0
                heatmap_data[client][area] += 1
        
        empresas_ordenadas = sorted(empresas_set)
        areas_ordenadas = sorted(areas_set)
        
        return {
            'data': heatmap_data,
            'empresas': empresas_ordenadas,
            'areas': areas_ordenadas,
        }
    
    # =========================================================================
    # DADOS DE RESULTADO (GANHO/PERDIDO/NEUTRO)
    # =========================================================================
    def get_finalized_processes(self) -> List[dict]:
        """Retorna lista de processos com status 'Concluído' ou 'Concluído com pendências'."""
        finalized_statuses = {'Concluído', 'Concluído com pendências'}
        return [
            proc for proc in self._processes 
            if proc.get('status') in finalized_statuses
        ]
    
    def get_processes_by_result(self) -> Dict[str, Any]:
        """Coleta estatísticas de processos por resultado (Ganho/Perdido/Neutro)."""
        finalized = self.get_finalized_processes()
        
        result_counts = {
            'Ganho': 0,
            'Perdido': 0,
            'Neutro': 0,
            'Não informado': 0
        }
        
        processes_by_result = {
            'Ganho': [],
            'Perdido': [],
            'Neutro': [],
            'Não informado': []
        }
        
        for proc in finalized:
            result = proc.get('result') or 'Não informado'
            if result not in result_counts:
                result = 'Não informado'
            
            result_counts[result] += 1
            processes_by_result[result].append({
                'title': proc.get('title', 'Sem título'),
                'number': proc.get('number', '-'),
                'area': proc.get('area', '-'),
                'status': proc.get('status', '-'),
                'result': result,
                'clients': proc.get('clients', []),
                '_id': proc.get('_id'),
                '_index': self._processes.index(proc)
            })
        
        return {
            'counts': result_counts,
            'total': len(finalized),
            'processes': processes_by_result,
            'all_finalized': [
                {
                    'title': proc.get('title', 'Sem título'),
                    'number': proc.get('number', '-'),
                    'area': proc.get('area', '-'),
                    'status': proc.get('status', '-'),
                    'result': proc.get('result') or 'Não informado',
                    'clients': ', '.join(proc.get('clients', [])) or '-',
                    '_id': proc.get('_id'),
                    '_index': self._processes.index(proc)
                }
                for proc in finalized
            ]
        }

    # =========================================================================
    # DADOS DE PROBABILIDADE
    # =========================================================================
    def collect_probability_data(self) -> Dict[str, Any]:
        """Coleta dados de probabilidades das teses dos casos."""
        probabilidades_data = {
            'Alta': 0,
            'Média': 0,
            'Baixa': 0,
            'Não informado': 0
        }
        
        casos_com_probabilidade = []
        for idx, case in enumerate(self._cases):
            theses = case.get('theses', [])
            for thesis_idx, thesis in enumerate(theses):
                prob = thesis.get('probability', 'Não informado')
                if prob in probabilidades_data:
                    probabilidades_data[prob] += 1
                else:
                    probabilidades_data['Não informado'] += 1
                
                casos_com_probabilidade.append({
                    'id': f"{idx}_{thesis_idx}",
                    'case': case.get('title', 'Sem título'),
                    'thesis': thesis.get('name', 'Sem nome'),
                    'probability': prob,
                    'status': thesis.get('status', 'Não informado')
                })
        
        return {
            'counts': probabilidades_data,
            'details': casos_com_probabilidade,
            'total': sum(probabilidades_data.values()),
        }


def create_data_service(get_cases_list, get_processes_list, 
                        get_clients_list, get_opposing_parties_list) -> PainelDataService:
    """
    Factory function para criar o serviço de dados.
    Carrega todos os dados uma única vez.
    """
    return PainelDataService(
        cases=get_cases_list(),
        processes=get_processes_list(),
        clients=get_clients_list(),
        opposing_parties=get_opposing_parties_list(),
    )


