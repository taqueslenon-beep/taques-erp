"""
Modelos de dados para o sistema de migração de processos.
Define a estrutura dos registros temporários na coleção processos_migracao.
"""
from typing import TypedDict, List, Any, Optional
from datetime import datetime

class ProcessoMigracao(TypedDict, total=False):
    """Estrutura de um processo em fase de migração."""
    _id: str
    
    # Dados extraídos da planilha (informativos e base)
    numero_processo: str          # Coluna A
    classe_processo: str          # Coluna B
    autores_sugestao: List[str]   # Coluna C (array de nomes)
    reus_sugestao: List[str]      # Coluna D (array de nomes)
    localidade_judicial: str      # Coluna E
    assunto: str                  # Coluna F
    data_abertura: str            # Coluna I
    valor_causa: str              # Coluna J
    
    # Dados preenchidos automaticamente
    sistema_processual: str       # Fixo: "eproc - TJSC - 1ª instância"
    estado: str                   # Fixo: "Santa Catarina"
    responsavel: str              # Fixo: "Lenon Taques"
    tipo_processo: str            # Fixo: "Judicial"
    prioridade: str               # Padrão: "P4"
    status_migracao: str          # "pendente" ou "concluido"
    data_importacao: Any          # Timestamp da importação
    
    # Dados a serem preenchidos manualmente
    titulo_processo: str
    link_eproc: str
    nucleo: str
    area_direito: str
    clientes: List[str]           # IDs de pessoas
    parte_contraria: List[str]    # IDs de pessoas
    outros_envolvidos: List[str]  # IDs de pessoas
    casos_vinculados: List[str]   # IDs de casos
    processo_pai: str             # ID de processo
    
    # Auditoria
    processo_definitivo_id: str   # ID na coleção 'processos' após conclusão
    atualizado_em: Any



