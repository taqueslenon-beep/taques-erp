"""
Módulo de Processos do workspace Visão Geral do Escritório.

Este módulo gerencia processos jurídicos e administrativos do escritório.
"""
from .main import processos_visao_geral
from .database import (
    listar_processos,
    buscar_processo,
    criar_processo,
    atualizar_processo,
    excluir_processo,
    contar_processos,
    listar_processos_por_caso,
    listar_processos_por_grupo,
    listar_processos_pais,
)
from .models import (
    TIPOS_PROCESSO,
    STATUS_PROCESSO,
    RESULTADOS_PROCESSO,
    AREAS_PROCESSO,
    SISTEMAS_PROCESSUAIS,
    ESTADOS,
    PARTE_CONTRARIA_TIPOS,
    Processo,
    obter_cor_status,
    obter_cor_resultado,
    obter_cor_area,
    criar_processo_vazio,
    validar_processo,
)

__all__ = [
    # Página principal
    'processos_visao_geral',
    # Database
    'listar_processos',
    'buscar_processo',
    'criar_processo',
    'atualizar_processo',
    'excluir_processo',
    'contar_processos',
    'listar_processos_por_caso',
    'listar_processos_por_grupo',
    'listar_processos_pais',
    # Models
    'TIPOS_PROCESSO',
    'STATUS_PROCESSO',
    'RESULTADOS_PROCESSO',
    'AREAS_PROCESSO',
    'SISTEMAS_PROCESSUAIS',
    'ESTADOS',
    'PARTE_CONTRARIA_TIPOS',
    'Processo',
    'obter_cor_status',
    'obter_cor_resultado',
    'obter_cor_area',
    'criar_processo_vazio',
    'validar_processo',
]



