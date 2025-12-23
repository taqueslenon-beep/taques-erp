"""
Utilitários para consultas Firebase baseadas em workspace.
Gerencia isolamento de coleções entre workspaces diferentes.
"""
from typing import Optional
from ..firebase_config import get_db
from ..gerenciadores.gerenciador_workspace import obter_workspace_atual, obter_info_workspace


# Mapeamento de nomes de coleções base para coleções reais
MAPEAMENTO_COLECOES = {
    'pessoas': 'clients',  # Mantém compatibilidade com nome original
    'casos': 'cases',
    'processos': 'processes',
    'acordos': 'agreements',
    'configuracoes': 'configurations',
    'opposing_parties': 'opposing_parties',
}


def obter_colecao(nome_colecao: str, workspace_id: Optional[str] = None):
    """
    Retorna referência da coleção correta baseada no workspace ativo.
    
    Args:
        nome_colecao: Nome base da coleção ('pessoas', 'casos', 'processos', etc.)
        workspace_id: ID do workspace (opcional, usa workspace atual se None)
    
    Returns:
        Referência da coleção no Firestore
    
    Exemplo:
        - Se workspace ativo = "area_cliente_schmidmeier" e nome_colecao = "pessoas"
        - Retorna referência para "clients" (coleção padrão)
        
        - Se workspace ativo = "visao_geral_escritorio" e nome_colecao = "pessoas"
        - Retorna referência para "visao_geral_pessoas"
    """
    db = get_db()
    
    # Se não fornecido, usa workspace atual
    if workspace_id is None:
        workspace_id = obter_workspace_atual()
    
    # Obtém informações do workspace
    workspace_info = obter_info_workspace(workspace_id)
    if not workspace_info:
        # Fallback: usa nome da coleção diretamente
        return db.collection(nome_colecao)
    
    prefixo = workspace_info['prefixo_colecoes']
    
    # Workspace padrão (area_cliente_schmidmeier) usa coleções originais
    if workspace_id == 'area_cliente_schmidmeier':
        # Mapeia para nome original da coleção
        nome_real = MAPEAMENTO_COLECOES.get(nome_colecao, nome_colecao)
        return db.collection(nome_real)
    
    # Outros workspaces usam prefixo
    nome_real = f"{prefixo}{nome_colecao}"
    return db.collection(nome_real)


def obter_nome_colecao(nome_colecao: str, workspace_id: Optional[str] = None) -> str:
    """
    Retorna apenas o nome da coleção (sem referência) baseado no workspace.
    
    Args:
        nome_colecao: Nome base da coleção
        workspace_id: ID do workspace (opcional)
    
    Returns:
        Nome completo da coleção
    """
    if workspace_id is None:
        workspace_id = obter_workspace_atual()
    
    workspace_info = obter_info_workspace(workspace_id)
    if not workspace_info:
        return nome_colecao
    
    prefixo = workspace_info['prefixo_colecoes']
    
    # Workspace padrão usa coleções originais
    if workspace_id == 'area_cliente_schmidmeier':
        return MAPEAMENTO_COLECOES.get(nome_colecao, nome_colecao)
    
    # Outros workspaces usam prefixo
    return f"{prefixo}{nome_colecao}"
















