# Módulos essenciais
from . import painel, processos_por_caso, configuracoes, login

# Módulo de processos (refatorado em subpacote)
from .processos import processos

# Módulo de casos (refatorado em subpacote)
from .casos import casos, case_detail, case_swot

# Módulo de pessoas (refatorado em subpacote)
from .pessoas import pessoas

# Módulo de acordos (refatorado em subpacote)
from .acordos import acordos

# Módulos desativados temporariamente (em desenvolvimento)
# from . import prazos, compromissos
# from . import governanca
