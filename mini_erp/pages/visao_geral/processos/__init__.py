"""
Módulo de Processos do workspace Visão Geral do Escritório.

Este módulo gerencia processos jurídicos e administrativos do escritório.
100% independente do módulo Schmidmeier.
"""
from .constants import (
    TIPOS_PROCESSO,
    STATUS_PROCESSO,
    RESULTADOS_PROCESSO,
    AREAS_PROCESSO,
    SISTEMAS_PROCESSUAIS,
    ESTADOS,
    PARTE_CONTRARIA_TIPOS,
    COLECAO_PROCESSOS,
    STATUS_CORES,
    RESULTADO_CORES,
    AREA_CORES,
    SCENARIO_TYPE_OPTIONS,
    SCENARIO_CHANCE_OPTIONS,
    SCENARIO_IMPACT_OPTIONS,
    SCENARIO_STATUS_OPTIONS,
)
from .models import (
    Processo,
    obter_cor_status,
    obter_cor_resultado,
    obter_cor_area,
    criar_processo_vazio,
    validar_processo,
)
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
from .page.main import processos_visao_geral
from .modal.modal_processo import abrir_modal_processo, confirmar_exclusao

# Alias para compatibilidade
abrir_dialog_processo = abrir_modal_processo

__all__ = [
    # Constantes
    'TIPOS_PROCESSO',
    'STATUS_PROCESSO',
    'RESULTADOS_PROCESSO',
    'AREAS_PROCESSO',
    'SISTEMAS_PROCESSUAIS',
    'ESTADOS',
    'PARTE_CONTRARIA_TIPOS',
    'COLECAO_PROCESSOS',
    'STATUS_CORES',
    'RESULTADO_CORES',
    'AREA_CORES',
    'SCENARIO_TYPE_OPTIONS',
    'SCENARIO_CHANCE_OPTIONS',
    'SCENARIO_IMPACT_OPTIONS',
    'SCENARIO_STATUS_OPTIONS',
    # Models
    'Processo',
    'obter_cor_status',
    'obter_cor_resultado',
    'obter_cor_area',
    'criar_processo_vazio',
    'validar_processo',
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
    # Página principal
    'processos_visao_geral',
    # Modal
    'abrir_modal_processo',
    'abrir_dialog_processo',  # Alias para compatibilidade
    'confirmar_exclusao',
]





