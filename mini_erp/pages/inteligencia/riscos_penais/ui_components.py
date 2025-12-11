"""
ui_components.py - Componentes de UI reutilizáveis para o módulo Riscos Penais.
"""

from nicegui import ui
from typing import Dict, Any, List, Optional


def stat_card(titulo: str, valor: str, cor: str, subtitulo: Optional[str] = None) -> None:
    """
    Cria um card de métrica/estatística.
    
    Args:
        titulo: Título do card
        valor: Valor principal a exibir
        cor: Cor do valor e da borda
        subtitulo: Texto adicional abaixo do valor (opcional)
    """
    with ui.card().classes('flex-1 min-w-48 p-4 border-l-4').style(f'border-left-color: {cor};'):
        ui.label(titulo).classes('text-gray-500 text-sm mb-1')
        ui.label(valor).classes('text-3xl font-bold').style(f'color: {cor};')
        if subtitulo:
            ui.label(subtitulo).classes('text-xs text-gray-400 mt-1')


def crime_badge(artigo: str, tem_agravante: bool = False) -> None:
    """
    Cria um badge para exibir um artigo de crime.
    
    Args:
        artigo: Artigo do crime (ex: "Art. 38-A")
        tem_agravante: Se o crime tem agravante do Art. 53
    """
    estilo_bg = '#fee2e2' if tem_agravante else '#fef3c7'
    estilo_texto = '#991b1b' if tem_agravante else '#92400e'
    
    with ui.badge(artigo).classes('px-2 py-1 text-xs font-semibold').style(f'background-color: {estilo_bg}; color: {estilo_texto};'):
        if tem_agravante:
            ui.icon('warning', size='12px').classes('ml-1')


def regime_badge(regime: str) -> None:
    """
    Cria um badge para exibir regime de cumprimento de pena.
    
    Args:
        regime: Regime (Aberto, Semiaberto, Fechado)
    """
    cores = {
        "Aberto": {"bg": "#4ade80", "text": "white"},
        "Semiaberto": {"bg": "#fbbf24", "text": "white"},
        "Fechado": {"bg": "#ef4444", "text": "white"}
    }
    
    cor = cores.get(regime, {"bg": "#6b7280", "text": "white"})
    ui.badge(regime).classes('px-3 py-1 font-semibold').style(f'background-color: {cor["bg"]}; color: {cor["text"]};')


def cenario_card(cenario: Dict[str, Any]) -> None:
    """
    Cria um card visual para um cenário de condenação.
    
    Args:
        cenario: Dicionário com dados do cenário
    """
    calculo = cenario.get('calculo', {})
    
    with ui.card().classes('flex-1 min-w-80 p-6 border-2').style(f'border-color: {cenario["cor"]};'):
        with ui.column().classes('gap-4'):
            # Cabeçalho com ícone e nome
            with ui.row().classes('items-center gap-3'):
                ui.icon(cenario['icone'], size='32px').style(f'color: {cenario["cor"]};')
                with ui.column().classes('gap-1'):
                    ui.label(cenario['nome']).classes('text-xl font-bold')
                    ui.label(cenario['descricao']).classes('text-sm text-gray-600')
            
            # Pena calculada em destaque
            ui.label(calculo.get('pena_total_texto', 'N/A')).classes('text-4xl font-bold').style(f'color: {cenario["cor"]};')
            
            # Regime
            with ui.row().classes('items-center gap-2'):
                ui.label('Regime:').classes('text-sm text-gray-600')
                regime_badge(calculo.get('regime', 'N/A'))
            
            # Probabilidade
            with ui.row().classes('items-center gap-2 mt-2'):
                ui.label('Probabilidade de prisão:').classes('text-sm font-semibold')
                ui.label(cenario.get('probabilidade_prisao', 'N/A')).classes('text-sm font-bold').style(f'color: {cenario["cor"]};')
            
            # Premissas
            ui.label('Premissas:').classes('text-sm font-semibold mt-4 mb-2')
            with ui.column().classes('gap-1 ml-4'):
                for premissa in cenario.get('premissas', []):
                    ui.label(f"• {premissa}").classes('text-sm text-gray-700')
            
            # Consequências
            ui.label('Consequências:').classes('text-sm font-semibold mt-4 mb-2')
            with ui.column().classes('gap-1 ml-4'):
                for consequencia in cenario.get('consequencias', []):
                    ui.label(f"• {consequencia}").classes('text-sm text-gray-700')


def alerta_box(titulo: str, itens: List[str], cor: str = "#dc2626") -> None:
    """
    Cria um box de alerta com lista de itens.
    
    Args:
        titulo: Título do alerta
        itens: Lista de itens a exibir
        cor: Cor da borda e do título
    """
    with ui.card().classes('w-full p-4 border-2').style(f'border-color: {cor}; background-color: #fef2f2;'):
        with ui.row().classes('items-center gap-2 mb-3'):
            ui.icon('warning', size='24px').style(f'color: {cor};')
            ui.label(titulo).classes('text-lg font-bold').style(f'color: {cor};')
        
        with ui.column().classes('gap-2 ml-2'):
            for item in itens:
                ui.label(f"• {item}").classes('text-sm').style('color: #7f1d1d;')


def copiar_numero_processo(numero: str) -> None:
    """
    Copia o número do processo para a área de transferência.
    
    Args:
        numero: Número do processo
    """
    numero_escaped = str(numero).replace("'", "\\'")
    ui.run_javascript(f'''
        navigator.clipboard.writeText('{numero_escaped}').then(() => {{
            // Sucesso
        }}).catch(err => {{
            console.error('Erro ao copiar:', err);
        }});
    ''')
    ui.notify("Número copiado!", type="positive", position="top", timeout=1500)


def timeline_vertical(etapas: List[Dict[str, Any]]) -> None:
    """
    Cria uma timeline vertical mostrando etapas processuais.
    
    Args:
        etapas: Lista de dicionários com dados de cada etapa
    """
    with ui.column().classes('gap-4 w-full'):
        for i, etapa in enumerate(etapas):
            is_last = i == len(etapas) - 1
            pode_prisao = etapa.get('prisao_possivel', False)
            
            with ui.row().classes('items-start gap-4 w-full'):
                # Indicador vertical (linha + círculo)
                with ui.column().classes('items-center gap-0'):
                    cor_circulo = '#ef4444' if pode_prisao else '#6b7280'
                    ui.icon('circle', size='20px').style(f'color: {cor_circulo};')
                    if not is_last:
                        ui.divider(vertical=True).classes('h-16')
                
                # Conteúdo da etapa
                with ui.column().classes('flex-1 gap-1 pb-6'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label(etapa['fase']).classes('font-bold text-lg')
                        if pode_prisao:
                            ui.badge('PRISÃO POSSÍVEL').classes('px-2 py-1').style('background-color: #ef4444; color: white;')
                    
                    ui.label(etapa['descricao']).classes('text-sm text-gray-700')
                    
                    with ui.row().classes('items-center gap-4 mt-2'):
                        if etapa.get('prazo_estimado'):
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('schedule', size='16px').classes('text-gray-500')
                                ui.label(f"Prazo: {etapa['prazo_estimado']}").classes('text-xs text-gray-600')
                        
                        if etapa.get('observacao'):
                            ui.label(etapa['observacao']).classes('text-xs italic text-gray-500')


