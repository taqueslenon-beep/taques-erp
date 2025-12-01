from nicegui import ui
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("🟢 Iniciando servidor de teste...")

@ui.page('/')
def home():
    logger.info("📍 Página / acessada")
    ui.label('✅ SERVIDOR RESPONDENDO')

@ui.page('/teste')
def teste():
    logger.info("📍 Página /teste acessada")
    ui.label('✅ TESTE OK')

logger.info("🟢 Servidor pronto na porta 8080")
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host='127.0.0.1', port=8080, show=True, show_welcome_message=False)
