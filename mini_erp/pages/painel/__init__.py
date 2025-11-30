"""
Módulo Painel - Visualizações consolidadas do sistema.

Estrutura modular:
- models.py: Constantes e configurações
- helpers.py: Funções utilitárias
- data_service.py: Carregamento e agregação de dados
- chart_builders.py: Builders de configuração de gráficos EChart
- ui_components.py: Componentes de UI reutilizáveis
- tab_visualizations.py: Implementações individuais de cada aba
- painel_page.py: Página principal (orquestrador)
"""

from .painel_page import painel

__all__ = ['painel']




