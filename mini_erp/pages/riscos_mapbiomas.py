from nicegui import ui
from ..core import layout

@ui.page('/riscos-mapbiomas')
def riscos_mapbiomas_page():
    with layout('Riscos / Alertas MapBiomas', [('Riscos / Alertas MapBiomas', None)]):
        ui.label('em construção').classes('text-lg text-gray-600')


