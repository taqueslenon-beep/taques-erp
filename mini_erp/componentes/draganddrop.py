"""
Componente de Drag & Drop para Kanban.
Adaptado do exemplo trello_cards do NiceGUI.

Fornece funções column() e card() para criar colunas e cards arrastáveis.
"""

from nicegui import ui
from typing import Callable, Optional, Any


def column(
    title: str,
    on_drop: Optional[Callable[[str, Any], None]] = None,
    width: str = '280px'
) -> ui.column:
    """
    Cria uma coluna do Kanban que aceita cards arrastáveis.
    
    Args:
        title: Título da coluna
        on_drop: Callback chamado quando um card é solto na coluna
                 Recebe (card_id, data) como parâmetros
        width: Largura da coluna (padrão: 280px)
    
    Returns:
        Container da coluna (ui.column)
    """
    with ui.column().classes('flex flex-col gap-2') as col:
        # Header da coluna
        with ui.card().classes('w-full p-3 bg-gray-100'):
            ui.label(title).classes('text-sm font-semibold text-gray-700')
        
        # Container para os cards (drop zone)
        cards_container = ui.column().classes('flex flex-col gap-2 min-h-[200px]')
        
        # Adiciona atributos para identificar a coluna
        col._drop_zone = cards_container
        col._on_drop = on_drop
        col._title = title
    
    return col


def card(
    card_id: str,
    content: Any,
    data: Optional[Any] = None,
    draggable: bool = True
) -> ui.card:
    """
    Cria um card arrastável para o Kanban.
    
    Args:
        card_id: ID único do card
        content: Conteúdo do card (pode ser ui.element ou função que retorna elementos)
        data: Dados adicionais do card (passados para on_drop)
        draggable: Se o card pode ser arrastado (padrão: True)
    
    Returns:
        Card arrastável (ui.card)
    """
    with ui.card().classes('w-full p-3 cursor-move hover:shadow-md transition-shadow') as card_elem:
        # Adiciona atributos para drag & drop
        card_elem._card_id = card_id
        card_elem._card_data = data
        card_elem._draggable = draggable
        
        # Renderiza o conteúdo
        if callable(content):
            content()
        else:
            # Se content é um elemento UI, adiciona diretamente
            if hasattr(content, '__enter__'):
                # É um context manager
                with content:
                    pass
            else:
                # É um elemento simples
                if hasattr(content, 'classes'):
                    content.classes('w-full')
    
    # Adiciona JavaScript para drag & drop
    if draggable:
        _make_draggable(card_elem)
    
    return card_elem


def _make_draggable(card_element: ui.card):
    """
    Adiciona funcionalidade de drag & drop ao card usando JavaScript.
    
    Args:
        card_element: Elemento do card
    """
    card_id = getattr(card_element, '_card_id', '')
    
    # JavaScript para implementar drag & drop
    ui.run_javascript(f'''
        (function() {{
            // Aguarda o elemento ser renderizado
            setTimeout(function() {{
                const card = document.querySelector('[data-card-id="{card_id}"]');
                if (!card) {{
                    // Tenta encontrar pelo ID do NiceGUI
                    const niceguiId = card_element.id || '';
                    if (niceguiId) {{
                        const elem = document.getElementById(niceguiId);
                        if (elem) {{
                            setupDragDrop(elem);
                        }}
                    }}
                    return;
                }}
                setupDragDrop(card);
            }}, 100);
            
            function setupDragDrop(element) {{
                if (!element) return;
                
                element.draggable = true;
                element.setAttribute('data-card-id', '{card_id}');
                
                element.addEventListener('dragstart', function(e) {{
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/plain', '{card_id}');
                    element.style.opacity = '0.5';
                }});
                
                element.addEventListener('dragend', function(e) {{
                    element.style.opacity = '1';
                }});
            }}
        }})();
    ''')


def setup_drop_zones():
    """
    Configura as zonas de drop (colunas) para aceitar cards arrastados.
    Deve ser chamado após criar todas as colunas.
    """
    ui.run_javascript('''
        (function() {
            // Encontra todas as colunas (drop zones)
            const dropZones = document.querySelectorAll('.drop-zone');
            
            dropZones.forEach(function(zone) {
                zone.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    zone.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                });
                
                zone.addEventListener('dragleave', function(e) {
                    zone.style.backgroundColor = '';
                });
                
                zone.addEventListener('drop', function(e) {
                    e.preventDefault();
                    zone.style.backgroundColor = '';
                    
                    const cardId = e.dataTransfer.getData('text/plain');
                    const columnTitle = zone.getAttribute('data-column-title');
                    
                    // Dispara evento customizado
                    const event = new CustomEvent('card-dropped', {
                        detail: {
                            cardId: cardId,
                            columnTitle: columnTitle
                        }
                    });
                    window.dispatchEvent(event);
                });
            });
        })();
    ''')


















