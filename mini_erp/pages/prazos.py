from nicegui import ui
from ..core import layout

@ui.page('/prazos')
def prazos():
    with layout('Prazos', breadcrumbs=[('Prazos', None)]):
        ui.label('Controle de Prazos aqui.').classes('text-gray-600')


