"""
Cliente API do Slack para realizar chamadas à API oficial.

Este módulo gerencia:
- Autenticação com tokens OAuth
- Busca de mensagens de canais
- Listagem e busca de canais
- Obtenção de informações de usuários
- Paginação e cache de resultados
"""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time


class SlackAPIError(Exception):
    """Exceção customizada para erros da API do Slack."""
    pass


class SlackAPI:
    """
    Cliente para interagir com a API do Slack.
    
    Gerencia autenticação, rate limiting e cache de requisições.
    """
    
    BASE_URL = 'https://slack.com/api'
    
    def __init__(self, access_token: str):
        """
        Inicializa cliente com token de acesso.
        
        Args:
            access_token: Token de acesso OAuth2 do Slack
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        self._rate_limit_cache = {}
        self._cache_ttl = 900  # 15 minutos em segundos
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, use_cache: bool = False) -> Dict[str, Any]:
        """
        Realiza requisição à API do Slack com tratamento de erros e rate limiting.
        
        Args:
            method: Método HTTP (GET, POST)
            endpoint: Endpoint da API (ex: 'conversations.history')
            params: Parâmetros da query string
            data: Dados do body (para POST)
            use_cache: Se True, usa cache quando disponível
            
        Returns:
            Resposta JSON da API
            
        Raises:
            SlackAPIError: Se houver erro na requisição
        """
        # Verifica cache se habilitado
        if use_cache:
            cache_key = f"{method}:{endpoint}:{str(params)}"
            if cache_key in self._rate_limit_cache:
                cached_response, cached_time = self._rate_limit_cache[cache_key]
                if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                    return cached_response
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                raise SlackAPIError(f"Método HTTP não suportado: {method}")
            
            # Verifica rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                # Tenta novamente uma vez
                if method == 'GET':
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                else:
                    response = requests.post(url, headers=self.headers, json=data, timeout=10)
            
            response.raise_for_status()
            result = response.json()
            
            # Slack retorna ok: false em caso de erro
            if not result.get('ok', False):
                error = result.get('error', 'unknown_error')
                raise SlackAPIError(f"Erro da API Slack: {error}")
            
            # Salva no cache se habilitado
            if use_cache:
                self._rate_limit_cache[cache_key] = (result, datetime.now())
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise SlackAPIError(f"Erro de conexão com Slack: {str(e)}")
    
    def get_channel_history(self, channel_id: str, limit: int = 50, 
                           cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Busca histórico de mensagens de um canal.
        
        Args:
            channel_id: ID do canal (ex: C1234567890)
            limit: Número máximo de mensagens (máx 1000)
            cursor: Cursor de paginação para próxima página
            
        Returns:
            Dicionário com mensagens e metadados de paginação
        """
        params = {
            'channel': channel_id,
            'limit': min(limit, 1000)  # Slack limita a 1000 por requisição
        }
        
        if cursor:
            params['cursor'] = cursor
        
        return self._make_request('GET', 'conversations.history', params=params, use_cache=False)
    
    def get_all_channel_messages(self, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca todas as mensagens de um canal com paginação automática.
        
        Args:
            channel_id: ID do canal
            limit: Número máximo de mensagens a retornar
            
        Returns:
            Lista de mensagens ordenadas por timestamp (mais antigas primeiro)
        """
        all_messages = []
        cursor = None
        remaining = limit
        
        while remaining > 0:
            batch_limit = min(remaining, 1000)
            result = self.get_channel_history(channel_id, limit=batch_limit, cursor=cursor)
            
            messages = result.get('messages', [])
            if not messages:
                break
            
            all_messages.extend(messages)
            remaining -= len(messages)
            
            # Verifica se há mais páginas
            response_metadata = result.get('response_metadata', {})
            cursor = response_metadata.get('next_cursor')
            
            if not cursor:
                break
        
        # Inverte para ordem cronológica (mais antigas primeiro)
        all_messages.reverse()
        return all_messages[:limit]
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um canal específico.
        
        Args:
            channel_id: ID do canal
            
        Returns:
            Dicionário com informações do canal ou None se não encontrado
        """
        params = {'channel': channel_id}
        result = self._make_request('GET', 'conversations.info', params=params, use_cache=True)
        return result.get('channel')
    
    def list_channels(self, types: str = 'public_channel,private_channel', 
                     exclude_archived: bool = True) -> List[Dict[str, Any]]:
        """
        Lista todos os canais acessíveis.
        
        Args:
            types: Tipos de canais (public_channel, private_channel, mpim, im)
            exclude_archived: Se True, exclui canais arquivados
            
        Returns:
            Lista de canais
        """
        params = {
            'types': types,
            'exclude_archived': exclude_archived
        }
        
        all_channels = []
        cursor = None
        
        while True:
            if cursor:
                params['cursor'] = cursor
            
            result = self._make_request('GET', 'conversations.list', params=params, use_cache=True)
            channels = result.get('channels', [])
            all_channels.extend(channels)
            
            response_metadata = result.get('response_metadata', {})
            cursor = response_metadata.get('next_cursor')
            
            if not cursor:
                break
        
        return all_channels
    
    def search_channels(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca canais por nome.
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de canais que correspondem à busca
        """
        channels = self.list_channels()
        query_lower = query.lower()
        
        return [
            channel for channel in channels
            if query_lower in channel.get('name', '').lower()
        ]
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um usuário específico.
        
        Args:
            user_id: ID do usuário (ex: U1234567890)
            
        Returns:
            Dicionário com informações do usuário ou None se não encontrado
        """
        params = {'user': user_id}
        result = self._make_request('GET', 'users.info', params=params, use_cache=True)
        return result.get('user')
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa se a conexão com a API está funcionando e retorna informações detalhadas.
        
        Returns:
            Dicionário com:
            - success: bool - Se conexão foi bem-sucedida
            - team_id: str - ID do workspace (se sucesso)
            - team_name: str - Nome do workspace (se sucesso)
            - user_id: str - ID do usuário autenticado (se sucesso)
            - error: str - Mensagem de erro (se falhou)
        """
        try:
            result = self._make_request('GET', 'auth.test', use_cache=False)
            
            if result.get('ok', False):
                return {
                    'success': True,
                    'team_id': result.get('team_id'),
                    'team_name': result.get('team'),
                    'user_id': result.get('user_id'),
                    'user': result.get('user'),
                    'url': result.get('url')
                }
            else:
                error = result.get('error', 'unknown_error')
                return {
                    'success': False,
                    'error': error,
                    'message': f'API retornou erro: {error}'
                }
        except SlackAPIError as e:
            return {
                'success': False,
                'error': 'api_error',
                'message': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'connection_error',
                'message': f'Erro de conexão: {str(e)}'
            }


# =============================================================================
# FUNÇÕES HELPER
# =============================================================================

def fetch_channel_messages(access_token: str, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Função helper para buscar mensagens de um canal.
    
    Args:
        access_token: Token de acesso OAuth2
        channel_id: ID do canal
        limit: Número máximo de mensagens
        
    Returns:
        Lista de mensagens
    """
    api = SlackAPI(access_token)
    return api.get_all_channel_messages(channel_id, limit=limit)


def search_channels(access_token: str, query: str) -> List[Dict[str, Any]]:
    """
    Função helper para buscar canais.
    
    Args:
        access_token: Token de acesso OAuth2
        query: Termo de busca
        
    Returns:
        Lista de canais encontrados
    """
    api = SlackAPI(access_token)
    return api.search_channels(query)

