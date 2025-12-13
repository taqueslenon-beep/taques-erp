"""
dados_processos.py - Dados dos processos criminais do Carlos.

Dados extraídos das 3 denúncias criminais reais.
"""

# =============================================================================
# DADOS DO RÉU
# =============================================================================

DADOS_REU = {
    "nome": "Carlos Schmidmeier",
    "cpf": "678.600.449-00",
    "nascimento": "30/07/1967",
    "idade_atual": 57,
    "endereco": "Rua Getúlio Vargas, 793, Centro, Mafra-SC",
    "profissao": "Aposentado",
    "vinculo_imoveis": "Arrendatário"
}

# =============================================================================
# PROCESSO 1 - ITAIÓPOLIS
# =============================================================================

PROCESSO_1 = {
    "id": "proc_itaiopolis",
    "numero": "5000025-80.2023.8.24.0032",
    "comarca": "Itaiópolis",
    "vara": "Vara Única",
    "data_denuncia": "11/01/2023",
    "caso_erp": "1.9 - Distrito / 2022",
    "status": "Em andamento",
    "fase": "Instrução",
    "parte_contraria": "MPSC",
    "promotor": "Pedro Roberto Decomain",
    "local_fato": "Rio da Areia, interior de Itaiópolis",
    "imovel": "Propriedade da Refloresta Imóveis Ltda.",
    "vinculo_reu": "Arrendatário",
    "area_atingida_ha": 0.96,
    "bioma": "Mata Atlântica",
    "estagio_vegetacao": "Médio de regeneração",
    "crimes": [
        {
            "artigo": "Art. 38-A",
            "lei": "Lei 9.605/98",
            "nome": "Destruição de vegetação do Bioma Mata Atlântica",
            "descricao": "Destruir ou danificar vegetação primária ou secundária, em estágio avançado ou médio de regeneração, do Bioma Mata Atlântica",
            "pena_minima_meses": 12,
            "pena_maxima_meses": 36,
            "tem_agravante_53": False
        }
    ],
    "proposta_sursis": {
        "oferecida": True,
        "prazo_anos": 2,
        "condicoes": [
            "Não se ausentar da Comarca por mais de 8 dias sem comunicação",
            "Não mudar de residência sem comunicação ao Juízo",
            "Reparação do dano via PRAD em 60 dias"
        ]
    },
    "anpp_cabivel": False,
    "motivo_anpp_incabivel": "Existência de outro processo em Mafra (antecedentes)",
    "testemunhas": [
        "Eriel Kuminek - Policial Militar Ambiental",
        "Gilson Wanderlei Cordeiro - Policial Militar Ambiental"
    ]
}

# =============================================================================
# PROCESSO 2 - MAFRA (WERKA)
# =============================================================================

PROCESSO_2 = {
    "id": "proc_mafra_werka",
    "numero": "5002716-40.2023.8.24.0041",
    "comarca": "Mafra",
    "vara": "Vara Criminal",
    "data_denuncia": "12/05/2023",
    "caso_erp": "1.7 - Werka / 2022",
    "status": "Em andamento",
    "fase": "Instrução",
    "parte_contraria": "MPSC",
    "promotor": "Nicole Lange de Almeida Pires",
    "local_fato": "Localidade de Guarupu, zona rural, Mafra/SC",
    "data_constatacao": "10/04/2022",
    "meio_utilizado": "Máquina",
    "crimes": [
        {
            "artigo": "Art. 38-A",
            "lei": "Lei 9.605/98",
            "nome": "Destruição de vegetação do Bioma Mata Atlântica",
            "descricao": "Danificou vegetação secundária, em estágio médio de regeneração, do Bioma Mata Atlântica, atingindo espécies ameaçadas de extinção",
            "fato": 1,
            "area_ha": 16.85,
            "pena_minima_meses": 12,
            "pena_maxima_meses": 36,
            "tem_agravante_53": True,
            "agravante": "Art. 53, II, 'c' - Espécies ameaçadas de extinção",
            "aumento_minimo": 1/6,
            "aumento_maximo": 1/3
        },
        {
            "artigo": "Art. 38",
            "lei": "Lei 9.605/98",
            "nome": "Destruição de floresta de APP",
            "descricao": "Danificou floresta considerada de preservação permanente, atingindo espécies ameaçadas de extinção",
            "fato": 2,
            "area_ha": 18.6,
            "pena_minima_meses": 12,
            "pena_maxima_meses": 36,
            "tem_agravante_53": True,
            "agravante": "Art. 53, II, 'c' - Espécies ameaçadas de extinção",
            "aumento_minimo": 1/6,
            "aumento_maximo": 1/3
        }
    ],
    "area_total_ha": 35.45,
    "especies_ameacadas": [
        {"nome_popular": "Araucária", "nome_cientifico": "Araucaria angustifolia"},
        {"nome_popular": "Imbuia", "nome_cientifico": "Ocotea porosa"},
        {"nome_popular": "Cedro", "nome_cientifico": "Cedrela fissilis"}
    ],
    "outras_especies": [
        "Bracatinga (Mimosa scabrela)",
        "Canela Guaicá (Ocotea puberula)",
        "Aroeira (Schinus terebinthifolia)",
        "Branquilho (Sebastiania commersoniana)",
        "Vassourão Preto (Vernonia discolor)",
        "Palmeira Jerivá (Siagrus romanzofiana)"
    ],
    "proposta_sursis": {"oferecida": False},
    "testemunhas": [
        "Ivo Moraci Adur - Policial Militar Ambiental",
        "Eriel Kuminek - Policial Militar Ambiental"
    ]
}

# =============================================================================
# PROCESSO 3 - MAFRA (LEONEL II / GREIN II)
# =============================================================================

PROCESSO_3 = {
    "id": "proc_mafra_leonel_grein",
    "numero": "5003892-54.2023.8.24.0041",
    "comarca": "Mafra",
    "vara": "Vara Criminal",
    "data_denuncia_original": "06/07/2023",
    "data_aditamento": "19/09/2025",
    "casos_erp": ["1.11 - Leonel II / 2022", "1.10 - Grein II / 2022"],
    "status": "Em andamento",
    "fase": "Instrução (pós-aditamento)",
    "parte_contraria": "MPSC",
    "promotor_aditamento": "Rayane Santana Freitas",
    "correus": [
        {"nome": "Luciane Schmidmeier", "tipo": "Pessoa Física", "vinculo": "Sócia"},
        {"nome": "Refloresta Imóveis Ltda.", "tipo": "Pessoa Jurídica", "vinculo": "Proprietária"}
    ],
    "motivo_inclusao_carlos": "Contrato de arrendamento demonstra domínio e ingerência sobre as áreas",
    "crimes": [
        {
            "artigo": "Art. 38",
            "lei": "Lei 9.605/98",
            "nome": "Destruição de floresta de APP",
            "fatos": ["I", "IV", "VI", "IX"],
            "quantidade": 4,
            "pena_minima_meses": 12,
            "pena_maxima_meses": 36,
            "tem_agravante_53": True
        },
        {
            "artigo": "Art. 38-A",
            "lei": "Lei 9.605/98",
            "nome": "Destruição de vegetação Mata Atlântica",
            "fatos": ["II", "V", "VII", "VIII"],
            "quantidade": 4,
            "pena_minima_meses": 12,
            "pena_maxima_meses": 36,
            "tem_agravante_53": True
        },
        {
            "artigo": "Art. 48",
            "lei": "Lei 9.605/98",
            "nome": "Impedir regeneração natural",
            "fatos": ["III"],
            "quantidade": 1,
            "pena_minima_meses": 6,
            "pena_maxima_meses": 12,
            "tem_agravante_53": False
        }
    ],
    "total_fatos": 9,
    "historico_processual": [
        {"data": "06/07/2023", "evento": "Denúncia recebida contra Luciane e Refloresta"},
        {"data": None, "evento": "Citação dos acusados"},
        {"data": None, "evento": "Defesa prévia - alegou ilegitimidade passiva"},
        {"data": None, "evento": "MP manifestou pela rejeição das preliminares"},
        {"data": None, "evento": "Juízo rejeitou preliminares"},
        {"data": None, "evento": "Declínio para Justiça Federal"},
        {"data": None, "evento": "MPF aditou quanto à reparação"},
        {"data": None, "evento": "Novo declínio para Justiça Estadual"},
        {"data": "19/09/2025", "evento": "MPSC adita denúncia incluindo Carlos como réu"}
    ],
    "proposta_sursis": {"oferecida": False}
}

# =============================================================================
# LISTA DE PROCESSOS
# =============================================================================

PROCESSOS = [PROCESSO_1, PROCESSO_2, PROCESSO_3]







