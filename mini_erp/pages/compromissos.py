from nicegui import ui
from ..core import layout
from ..componentes.breadcrumb_helper import gerar_breadcrumbs

@ui.page('/compromissos')
def compromissos():
    # Gera breadcrumb padronizado com workspace
    breadcrumbs = gerar_breadcrumbs('Compromissos', url_modulo='/compromissos')
    
    with layout('Compromissos', breadcrumbs=breadcrumbs):
        ui.label('Agenda e Compromissos aqui.').classes('text-gray-600')


