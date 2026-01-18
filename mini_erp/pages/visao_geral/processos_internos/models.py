"""
Modelos de dados para Processos Internos.
Define estrutura de dados e validações.
"""
from typing import TypedDict, Optional
from datetime import datetime
from .constants import (
    CATEGORIAS_PROCESSO_INTERNO,
    PRIORIDADES,
    STATUS_PROCESSO_INTERNO
)


class ProcessoInterno(TypedDict, total=False):
    """Estrutura de um processo interno no sistema."""
    _id: str                          # ID do documento no Firestore
    titulo: str                       # Título do processo (obrigatório)
    link: str                         # URL do processo (opcional)
    categoria: str                   # Categoria (obrigatório)
    prioridade: str                   # Prioridade P1-P4 (obrigatório)
    data_criacao: datetime            # Data de criação (automático)
    data_atualizacao: datetime        # Data de atualização (automático)
    criado_por: str                   # UID do usuário que criou
    criado_por_nome: str              # Nome do usuário que criou (opcional)
    status: str                       # Status (default: "ativo")


def validar_processo_interno(dados: dict) -> tuple:
    """
    Valida os dados de um processo interno antes de salvar.

    Args:
        dados: Dicionário com dados do processo interno

    Returns:
        Tupla (valido: bool, mensagem_erro: str ou None)
    """
    # Título obrigatório
    titulo = dados.get('titulo', '').strip()
    if not titulo:
        return False, 'Título do processo interno é obrigatório.'

    if len(titulo) < 3:
        return False, 'Título deve ter pelo menos 3 caracteres.'

    # Categoria obrigatória e válida
    categoria = dados.get('categoria', '').strip()
    if not categoria:
        return False, 'Categoria é obrigatória.'

    if categoria not in CATEGORIAS_PROCESSO_INTERNO:
        return False, f'Categoria inválida. Valores aceitos: {", ".join(CATEGORIAS_PROCESSO_INTERNO)}'

    # Prioridade obrigatória e válida
    prioridade = dados.get('prioridade', '').strip()
    if not prioridade:
        return False, 'Prioridade é obrigatória.'

    if prioridade not in PRIORIDADES:
        return False, f'Prioridade inválida. Valores aceitos: {", ".join(PRIORIDADES)}'

    # Link deve ser URL válida (se fornecido)
    link = dados.get('link', '').strip()
    if link:
        if not (link.startswith('http://') or link.startswith('https://')):
            return False, 'Link deve ser uma URL válida (começar com http:// ou https://)'

    # Status válido (se informado)
    status = dados.get('status', 'ativo')
    if status and status not in STATUS_PROCESSO_INTERNO:
        return False, f'Status inválido. Valores aceitos: {", ".join(STATUS_PROCESSO_INTERNO)}'

    return True, None


def criar_processo_interno_vazio() -> dict:
    """Retorna um dicionário com estrutura padrão de processo interno vazio."""
    return {
        'titulo': '',
        'link': '',
        'categoria': '',
        'prioridade': '',
        'status': 'ativo'
    }









