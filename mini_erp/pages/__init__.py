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

# Módulo de inteligência (em desenvolvimento)
from .inteligencia import inteligencia

# Módulo de visão geral do escritório (novo workspace)
# Nota: Módulo entregaveis agora está dentro de visao_geral
from . import visao_geral

# Módulo de prazos (placeholder em desenvolvimento)
from . import prazos

# Módulo de desenvolvedor (painel de ferramentas)
from .dev import dev
from .developer import developer_page

# Módulo de parceria DF/Taques (novo workspace)
from . import parceria_df_taques

# Módulo administrativo e migração
from . import admin

# Módulos desativados temporariamente (em desenvolvimento)
# from . import compromissos
# from . import governanca
