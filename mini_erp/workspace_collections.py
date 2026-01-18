"""
Constantes e helpers para coleções do Firebase por workspace.
Gerencia isolamento de dados entre workspaces diferentes.
"""

# =============================================================================
# CONSTANTES DE COLETAS POR WORKSPACE
# =============================================================================

# Workspace: Área do cliente (Schmidmeier) - Coleções padrão
SCHMIDMEIER_COLLECTIONS = {
    'pessoas': 'clients',  # Mantém nome original para compatibilidade
    'casos': 'cases',
    'processos': 'processes',
    'acordos': 'agreements',
    'configuracoes': 'configurations',
    'opposing_parties': 'opposing_parties',  # Partes contrárias
}

# Workspace: Visão geral do escritório - Coleções isoladas
VISAO_GERAL_COLLECTIONS = {
    'pessoas': 'visao_geral_escritorio_pessoas',
    'casos': 'visao_geral_escritorio_casos',
    'processos': 'visao_geral_escritorio_processos',
    'acordos': 'visao_geral_escritorio_acordos',
    'configuracoes': 'visao_geral_escritorio_configuracoes',
    'opposing_parties': 'visao_geral_escritorio_opposing_parties',
}

# Mapeamento de workspaces para suas coleções
WORKSPACE_COLLECTIONS = {
    'schmidmeier': SCHMIDMEIER_COLLECTIONS,
    'visao_geral_escritorio': VISAO_GERAL_COLLECTIONS,
}


# =============================================================================
# FUNÇÕES HELPER
# =============================================================================

def get_collection_name(collection_base: str, workspace: str = None) -> str:
    """
    Retorna o nome correto da coleção baseado no workspace.
    
    Args:
        collection_base: Nome base da coleção ('pessoas', 'casos', 'processos', etc.)
        workspace: ID do workspace ('schmidmeier' ou 'visao_geral_escritorio')
                  Se None, usa workspace atual da sessão
    
    Returns:
        Nome completo da coleção no Firestore
    """
    if workspace is None:
        from .auth import get_current_workspace
        workspace = get_current_workspace()
    
    workspace_collections = WORKSPACE_COLLECTIONS.get(workspace, SCHMIDMEIER_COLLECTIONS)
    return workspace_collections.get(collection_base, collection_base)


def get_collections_for_workspace(workspace: str) -> dict:
    """
    Retorna todas as coleções de um workspace.
    
    Args:
        workspace: ID do workspace ('schmidmeier' ou 'visao_geral_escritorio')
    
    Returns:
        Dicionário com mapeamento de coleções
    """
    return WORKSPACE_COLLECTIONS.get(workspace, SCHMIDMEIER_COLLECTIONS)





















