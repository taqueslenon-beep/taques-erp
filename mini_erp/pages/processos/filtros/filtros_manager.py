"""
filtros_manager.py - Gerencia estado compartilhado de todos os filtros.

Centraliza o gerenciamento de estado dos filtros e fornece funções
para criar, atualizar e limpar filtros.
"""

from typing import Dict, Any, Callable, Optional
from nicegui import ui


class FiltrosManager:
    """Gerencia estado e operações de todos os filtros."""
    
    def __init__(self, refresh_callback: Optional[Callable] = None):
        """
        Inicializa o gerenciador de filtros.
        
        Args:
            refresh_callback: Função chamada quando filtros mudam
        """
        self.refresh_callback = refresh_callback
        self.estado = {
            'search_term': {'value': ''},
            'area': {'value': ''},
            'case': {'value': ''},
            'client': {'value': ''},
            'parte': {'value': ''},
            'opposing': {'value': ''},
            'status': {'value': ''},
        }
        self.filter_selects: Dict[str, Any] = {}
    
    def get_estado(self, filtro_nome: str) -> Dict[str, str]:
        """Retorna o estado de um filtro específico."""
        return self.estado.get(filtro_nome, {'value': ''})
    
    def set_estado(self, filtro_nome: str, valor: str):
        """Define o valor de um filtro específico."""
        if filtro_nome in self.estado:
            self.estado[filtro_nome]['value'] = valor
            if self.refresh_callback:
                self.refresh_callback()
    
    def limpar_todos(self):
        """Limpa todos os filtros."""
        for filtro in self.estado.values():
            filtro['value'] = ''
        
        # Limpa valores dos selects
        for select in self.filter_selects.values():
            if select:
                select.value = ''
        
        if self.refresh_callback:
            self.refresh_callback()
    
    def registrar_select(self, nome: str, select_component):
        """Registra um componente select de filtro."""
        self.filter_selects[nome] = select_component
    
    def tem_filtros_ativos(self) -> bool:
        """Verifica se há algum filtro ativo."""
        return any(
            estado['value'] and str(estado['value']).strip()
            for estado in self.estado.values()
        )


def criar_gerenciador_filtros(refresh_callback: Optional[Callable] = None) -> FiltrosManager:
    """
    Factory function para criar um gerenciador de filtros.
    
    Args:
        refresh_callback: Função chamada quando filtros mudam
    
    Returns:
        Instância de FiltrosManager
    """
    return FiltrosManager(refresh_callback=refresh_callback)




