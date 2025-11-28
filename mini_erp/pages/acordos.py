from nicegui import ui
from ..core import layout


@ui.page('/acordos')
def acordos():
    with layout('Acordos', breadcrumbs=[('Acordos', None)]):
        ui.label('Gestão de Acordos aqui.').classes('text-gray-600')





