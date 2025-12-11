"""
calculos_penas.py - Lógica de cálculo de penas e cenários de condenação.
"""

# =============================================================================
# CONSTANTES DAS PENAS BASE
# =============================================================================

PENAS_BASE = {
    "art_38": {"min": 12, "max": 36, "descricao": "Detenção de 1 a 3 anos"},
    "art_38a": {"min": 12, "max": 36, "descricao": "Detenção de 1 a 3 anos"},
    "art_48": {"min": 6, "max": 12, "descricao": "Detenção de 6 meses a 1 ano"}
}

# =============================================================================
# CAUSA DE AUMENTO DO ART. 53, II, "c"
# =============================================================================

AGRAVANTE_53 = {
    "aumento_minimo": 1/6,  # 16.67%
    "aumento_maximo": 1/3,  # 33.33%
    "descricao": "Espécies ameaçadas de extinção"
}

# =============================================================================
# CENÁRIOS DE CÁLCULO
# =============================================================================

CENARIOS = {
    "otimista": {
        "nome": "Cenário Otimista",
        "descricao": "Absolvição ou condenação mínima em apenas 1 processo",
        "cor": "#22c55e",  # verde
        "icone": "sentiment_satisfied",
        "premissas": [
            "Absolvição por ausência de laudo pericial (jurisprudência STJ)",
            "Ou condenação apenas no processo de Itaiópolis",
            "Pena-base no mínimo legal",
            "Reconhecimento de atenuantes"
        ],
        "calculo": {
            "crimes": [{"artigo": "Art. 38-A", "quantidade": 1, "pena_meses": 12}],
            "pena_total_meses": 12,
            "pena_total_texto": "1 ano",
            "regime": "Aberto",
            "substituicao_possivel": True,
            "penas_alternativas": [
                "Prestação de serviços à comunidade",
                "Prestação pecuniária"
            ]
        },
        "probabilidade_prisao": "Baixa",
        "consequencias": [
            "Sem prisão efetiva",
            "Cumprimento de medidas alternativas",
            "Multa",
            "Obrigação de reparar dano ambiental (PRAD)"
        ]
    },
    "intermediario": {
        "nome": "Cenário Intermediário",
        "descricao": "Condenação em todos os processos com continuidade delitiva",
        "cor": "#f59e0b",  # amarelo/laranja
        "icone": "warning",
        "premissas": [
            "Condenação em todos os processos",
            "Reconhecimento de continuidade delitiva (crimes agrupados)",
            "Pena-base um pouco acima do mínimo",
            "Aplicação parcial de agravantes"
        ],
        "calculo": {
            "crimes": [
                {"grupo": "Art. 38 (5 crimes)", "pena_base": 14, "continuidade": 1.5, "pena_final": 21},
                {"grupo": "Art. 38-A (6 crimes)", "pena_base": 14, "continuidade": 1.5, "pena_final": 21},
                {"grupo": "Art. 48 (1 crime)", "pena_base": 6, "continuidade": 1, "pena_final": 6}
            ],
            "pena_total_meses": 48,
            "pena_total_texto": "4 anos",
            "regime": "Semiaberto",
            "substituicao_possivel": False
        },
        "probabilidade_prisao": "Média-Alta",
        "consequencias": [
            "Cumprimento em colônia agrícola/industrial",
            "Trabalho externo durante o dia",
            "Progressão para aberto após 1/6 da pena",
            "Multas elevadas",
            "Reparação integral do dano"
        ]
    },
    "pessimista": {
        "nome": "Cenário Pessimista",
        "descricao": "Condenação plena com concurso material (soma das penas)",
        "cor": "#ef4444",  # vermelho
        "icone": "dangerous",
        "premissas": [
            "Condenação por todos os 12 crimes",
            "Concurso material (penas somadas)",
            "Penas-base elevadas pela extensão do dano",
            "Aplicação de todas as agravantes"
        ],
        "calculo": {
            "crimes": [
                {"processo": "Itaiópolis", "artigo": "Art. 38-A", "qtd": 1, "pena_unit": 24, "subtotal": 24},
                {"processo": "Mafra/Werka", "artigo": "Art. 38-A + Art. 53", "qtd": 1, "pena_unit": 28, "subtotal": 28},
                {"processo": "Mafra/Werka", "artigo": "Art. 38 + Art. 53", "qtd": 1, "pena_unit": 28, "subtotal": 28},
                {"processo": "Mafra/Leonel-Grein", "artigo": "Art. 38 + Art. 53", "qtd": 4, "pena_unit": 28, "subtotal": 112},
                {"processo": "Mafra/Leonel-Grein", "artigo": "Art. 38-A + Art. 53", "qtd": 4, "pena_unit": 28, "subtotal": 112},
                {"processo": "Mafra/Leonel-Grein", "artigo": "Art. 48", "qtd": 1, "pena_unit": 9, "subtotal": 9}
            ],
            "pena_total_meses": 313,
            "pena_total_texto": "26 anos e 1 mês",
            "pena_realista_minima_meses": 84,
            "pena_realista_maxima_meses": 216,
            "pena_realista_texto": "7 a 18 anos (faixa realista)",
            "regime": "Fechado",
            "substituicao_possivel": False
        },
        "probabilidade_prisao": "Alta",
        "consequencias": [
            "Início em regime fechado",
            "Cumprimento em penitenciária",
            "Progressão após 1/6 (regime fechado → semiaberto)",
            "Multas muito elevadas",
            "Bloqueio de bens para garantir reparação",
            "Ficha criminal permanente"
        ]
    }
}

# =============================================================================
# TIMELINE DE QUANDO PODE HAVER PRISÃO
# =============================================================================

TIMELINE_PRISAO = {
    "fase_atual": "Instrução Processual",
    "etapas": [
        {
            "fase": "Sentença de 1ª Instância",
            "descricao": "Juiz da Comarca profere sentença",
            "prazo_estimado": "6 a 18 meses",
            "prisao_possivel": False,
            "observacao": "Ainda cabe recurso"
        },
        {
            "fase": "Apelação - TJSC",
            "descricao": "Recurso ao Tribunal de Justiça de Santa Catarina",
            "prazo_estimado": "12 a 24 meses",
            "prisao_possivel": False,
            "observacao": "Ainda cabe recurso aos tribunais superiores"
        },
        {
            "fase": "Recurso Especial - STJ",
            "descricao": "Recurso ao Superior Tribunal de Justiça",
            "prazo_estimado": "12 a 36 meses",
            "prisao_possivel": False,
            "observacao": "Última instância para matéria legal"
        },
        {
            "fase": "Recurso Extraordinário - STF",
            "descricao": "Recurso ao Supremo Tribunal Federal",
            "prazo_estimado": "12 a 24 meses",
            "prisao_possivel": False,
            "observacao": "Última instância para matéria constitucional"
        },
        {
            "fase": "Trânsito em Julgado",
            "descricao": "Não há mais recursos possíveis",
            "prazo_estimado": "-",
            "prisao_possivel": True,
            "observacao": "PRISÃO PODE SER DETERMINADA"
        }
    ],
    "prazo_total_estimado": "3 a 8 anos até trânsito em julgado",
    "excecao_prisao_preventiva": {
        "possivel": True,
        "condicoes": [
            "Se houver ameaça a testemunhas",
            "Se houver risco de fuga",
            "Se cometer novos crimes ambientais",
            "Se descumprir medidas cautelares"
        ],
        "observacao": "Prisão preventiva pode ocorrer a QUALQUER MOMENTO"
    }
}


