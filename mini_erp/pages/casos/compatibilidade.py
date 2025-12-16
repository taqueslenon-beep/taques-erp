"""
Módulo de compatibilidade entre formato antigo (cases) e novo (vg_casos).

Fornece funções para converter casos entre os dois formatos.
"""
from typing import Dict, Any, Optional
from datetime import datetime


def converter_vg_para_antigo(caso_vg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte um caso do formato vg_casos para formato antigo (compatível com interface do Schmidmeier).
    
    Args:
        caso_vg: Caso no formato vg_casos
        
    Returns:
        Caso no formato antigo
    """
    caso_antigo = {}
    
    # Campos básicos - mapeamento direto
    caso_antigo['_id'] = caso_vg.get('_id', '')
    caso_antigo['slug'] = caso_vg.get('slug_original', '') or caso_vg.get('_id', '')
    caso_antigo['title'] = caso_vg.get('titulo', '')
    caso_antigo['name'] = caso_vg.get('titulo', '').split(' - ')[-1].split(' / ')[0] if ' - ' in caso_vg.get('titulo', '') else caso_vg.get('titulo', '')
    caso_antigo['status'] = caso_vg.get('status', 'Em andamento')
    caso_antigo['state'] = caso_vg.get('estado', '')
    caso_antigo['category'] = caso_vg.get('categoria', 'Contencioso')
    
    # Extrair ano do título (formato: "X.Y - Nome / Ano")
    titulo = caso_vg.get('titulo', '')
    if ' / ' in titulo:
        try:
            ano_str = titulo.split(' / ')[-1]
            caso_antigo['year'] = ano_str
        except:
            caso_antigo['year'] = ''
    else:
        caso_antigo['year'] = ''
    
    # Extrair número do título (formato: "X.Y - Nome / Ano")
    if ' - ' in titulo:
        try:
            numero_str = titulo.split(' - ')[0].split('.')[-1]
            caso_antigo['number'] = int(numero_str) if numero_str.isdigit() else 0
        except:
            caso_antigo['number'] = 0
    else:
        caso_antigo['number'] = 0
    
    # Extrair mês (se não existir, usar 1)
    caso_antigo['month'] = caso_vg.get('month', 1)
    
    # Clientes
    caso_antigo['clients'] = caso_vg.get('clientes_nomes', []) or []
    
    # Observações/Descrição
    caso_antigo['observations'] = caso_vg.get('descricao', '')
    
    # Campos estratégicos
    caso_antigo['objectives'] = caso_vg.get('objetivos', '')
    caso_antigo['next_actions'] = caso_vg.get('proximas_acoes', '')
    caso_antigo['legal_considerations'] = caso_vg.get('consideracoes_legais', '')
    caso_antigo['technical_considerations'] = caso_vg.get('consideracoes_tecnicas', '')
    caso_antigo['strategy_observations'] = caso_vg.get('observacoes_estrategia', '')
    caso_antigo['theses'] = caso_vg.get('teses', []) or []
    
    # Responsáveis
    caso_antigo['responsaveis'] = caso_vg.get('responsaveis', []) or []
    
    # Parte contrária
    caso_antigo['parte_contraria'] = caso_vg.get('parte_contraria', '')
    caso_antigo['parte_contraria_nome'] = caso_vg.get('parte_contraria_nome', '')
    
    # Links
    caso_antigo['links'] = caso_vg.get('links', []) or []
    
    # Processos
    caso_antigo['processes'] = caso_vg.get('processos_titulos', []) or []
    
    # Tipo de caso (do slug_original ou título)
    slug_original = caso_vg.get('slug_original', '')
    if slug_original.startswith('1-'):
        caso_antigo['case_type'] = 'Antigo'
        caso_antigo['is_new_case'] = False
    elif slug_original.startswith('2-'):
        caso_antigo['case_type'] = 'Novo'
        caso_antigo['is_new_case'] = True
    else:
        # Tenta inferir do título
        if titulo.startswith('1.'):
            caso_antigo['case_type'] = 'Antigo'
            caso_antigo['is_new_case'] = False
        elif titulo.startswith('2.'):
            caso_antigo['case_type'] = 'Novo'
            caso_antigo['is_new_case'] = True
        else:
            caso_antigo['case_type'] = 'Antigo'
            caso_antigo['is_new_case'] = False
    
    # Campos que não são mais usados (manter vazios para compatibilidade)
    caso_antigo['swot_s'] = []
    caso_antigo['swot_w'] = []
    caso_antigo['swot_o'] = []
    caso_antigo['swot_t'] = []
    caso_antigo['maps'] = []
    caso_antigo['map_notes'] = ''
    caso_antigo['calculations'] = []
    
    return caso_antigo


def converter_antigo_para_vg(
    caso_antigo: Dict[str, Any],
    grupo_id: str,
    grupo_nome: str = "Schmidmeier"
) -> Dict[str, Any]:
    """
    Converte um caso do formato antigo para formato vg_casos.
    
    Args:
        caso_antigo: Caso no formato antigo
        grupo_id: ID do grupo Schmidmeier
        grupo_nome: Nome do grupo (padrão: "Schmidmeier")
        
    Returns:
        Caso no formato vg_casos
    """
    caso_vg = {}
    
    # Campos básicos - mapeamento
    caso_vg['titulo'] = caso_antigo.get('title', '')
    caso_vg['status'] = caso_antigo.get('status', 'Em andamento')
    caso_vg['estado'] = caso_antigo.get('state', '')
    caso_vg['categoria'] = caso_antigo.get('category', 'Contencioso')
    caso_vg['descricao'] = caso_antigo.get('observations', '')
    
    # Campos fixos para Schmidmeier
    caso_vg['nucleo'] = 'Ambiental'
    caso_vg['prioridade'] = 'P4'
    
    # Campos de grupo
    caso_vg['grupo_id'] = grupo_id
    caso_vg['grupo_nome'] = grupo_nome
    
    # Campo de referência
    caso_vg['slug_original'] = caso_antigo.get('slug', '')
    
    # Clientes
    clientes_nomes = caso_antigo.get('clients', []) or []
    if isinstance(clientes_nomes, str):
        clientes_nomes = [clientes_nomes]
    caso_vg['clientes_nomes'] = clientes_nomes
    caso_vg['clientes'] = []  # IDs serão preenchidos depois se necessário
    
    # Campos estratégicos
    caso_vg['objetivos'] = caso_antigo.get('objectives', '')
    caso_vg['proximas_acoes'] = caso_antigo.get('next_actions', '')
    caso_vg['consideracoes_legais'] = caso_antigo.get('legal_considerations', '')
    caso_vg['consideracoes_tecnicas'] = caso_antigo.get('technical_considerations', '')
    caso_vg['observacoes_estrategia'] = caso_antigo.get('strategy_observations', '')
    caso_vg['teses'] = caso_antigo.get('theses', []) or []
    
    # Responsáveis
    caso_vg['responsaveis'] = caso_antigo.get('responsaveis', []) or []
    
    # Parte contrária
    caso_vg['parte_contraria'] = caso_antigo.get('parte_contraria', '')
    caso_vg['parte_contraria_nome'] = caso_antigo.get('parte_contraria_nome', '')
    
    # Links
    caso_vg['links'] = caso_antigo.get('links', []) or []
    
    # Processos
    caso_vg['processos_titulos'] = caso_antigo.get('processes', []) or []
    caso_vg['processos_ids'] = []  # IDs serão preenchidos depois se necessário
    
    # Campos que não são mais usados (não incluir)
    # swot_*, maps, calculations não são incluídos
    
    # Timestamps
    if '_id' in caso_antigo:
        # Caso existente - manter timestamps se existirem
        pass
    else:
        # Novo caso
        caso_vg['created_at'] = datetime.now()
        caso_vg['updated_at'] = datetime.now()
    
    return caso_vg



