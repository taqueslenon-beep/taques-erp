from nicegui import ui
from ..core import layout

@ui.page('/compromissos')
def compromissos():
    with layout('Compromissos', breadcrumbs=[('Compromissos', None)]):
        ui.label('Agenda e Compromissos aqui.').classes('text-gray-600')


