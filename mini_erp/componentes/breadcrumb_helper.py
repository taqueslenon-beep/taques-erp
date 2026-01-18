"""
Helper para gerar breadcrumbs padronizados no sistema.

Facilita a criação de breadcrumbs consistentes em todos os módulos,
incluindo automaticamente o workspace atual quando necessário.
"""
from typing import List, Tuple, Optional
from ..gerenciadores.gerenciador_workspace import (
    obter_workspace_atual,
    obter_info_workspace
)


def gerar_breadcrumbs(
    modulo_nome: str,
    incluir_workspace: bool = True,
    url_modulo: Optional[str] = None,
    breadcrumbs_extra: Optional[List[Tuple[str, Optional[str]]]] = None
) -> List[Tuple[str, Optional[str]]]:
    """
    Gera lista de breadcrumbs padronizada para um módulo.
    
    Args:
        modulo_nome: Nome do módulo/página atual (ex: "Prazos", "Casos")
        incluir_workspace: Se True, inclui o workspace atual no início
        url_modulo: URL do módulo (opcional, se None não será clicável)
        breadcrumbs_extra: Lista adicional de breadcrumbs (ex: [("Detalhes", None)])
    
    Returns:
        Lista de tuplas (label, url) para usar no parâmetro breadcrumbs do layout()
    
    Exemplos:
        # Breadcrumb simples com workspace
        breadcrumbs = gerar_breadcrumbs("Prazos")
        # Resultado: [("Visão geral do escritório", "/visao-geral/painel"), ("Prazos", None)]
        
        # Breadcrumb com URL do módulo
        breadcrumbs = gerar_breadcrumbs("Prazos", url_modulo="/prazos")
        # Resultado: [("Visão geral do escritório", "/visao-geral/painel"), ("Prazos", "/prazos")]
        
        # Breadcrumb sem workspace
        breadcrumbs = gerar_breadcrumbs("Prazos", incluir_workspace=False)
        # Resultado: [("Prazos", None)]
        
        # Breadcrumb com níveis extras
        breadcrumbs = gerar_breadcrumbs(
            "Caso",
            url_modulo="/casos/123",
            breadcrumbs_extra=[("Detalhes", None)]
        )
        # Resultado: [("Visão geral do escritório", "/visao-geral/painel"), 
        #             ("Caso", "/casos/123"), ("Detalhes", None)]
    """
    breadcrumbs = []
    
    # Adiciona workspace atual se solicitado
    if incluir_workspace:
        workspace_id = obter_workspace_atual()
        workspace_info = obter_info_workspace(workspace_id)
        
        if workspace_info:
            workspace_nome = workspace_info.get('nome', 'Workspace')
            workspace_rota = workspace_info.get('rota_inicial', '/')
            breadcrumbs.append((workspace_nome, workspace_rota))
    
    # Adiciona módulo atual
    breadcrumbs.append((modulo_nome, url_modulo))
    
    # Adiciona breadcrumbs extras se fornecidos
    if breadcrumbs_extra:
        breadcrumbs.extend(breadcrumbs_extra)
    
    return breadcrumbs









