# Submódulo Criminal
# Gestão de cenário criminal, benefícios penais, condenações e cumprimento de penas

from .cenario import render_cenario_criminal
from .beneficios import render_beneficios_penais
from .condenacoes import render_condenacoes_criminais
from .cumprimento import render_cumprimento_penas

__all__ = [
    'render_cenario_criminal',
    'render_beneficios_penais',
    'render_condenacoes_criminais',
    'render_cumprimento_penas',
]

