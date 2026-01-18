"""
Serviço de migração de processos.
Lógica para processamento da planilha Excel e integração com Firestore.
"""
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from mini_erp.firebase_config import get_db
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLECAO_MIGRACAO = "processos_migracao"
COLECAO_DEFINITIVA = "vg_processos"

# Caminhos das planilhas por origem
CAMINHOS_PLANILHAS = {
    'lenon': "/Users/lenontaques/Documents/taques-erp/relatorio-processos-2025-lenon.xls",
    'gilberto': "/Users/lenontaques/Documents/taques-erp/relatorio-processos-gilberto-eproc-1-instancia.xls"
}

# Responsáveis por origem
RESPONSAVEIS = {
    'lenon': 'Lenon Taques',
    'gilberto': 'Gilberto'
}

# =============================================================================
# PROCESSOS HARDCODED DO GILBERTO (62 processos)
# Origem: Planilha EPROC - TJSC - 1ª Instância - Gilberto
# =============================================================================
PROCESSOS_GILBERTO = [
    {
        'numero_processo': '0306719-75.2017.8.24.0036',
        'data_distribuicao': '11/09/2017',
        'autores': ['COOPERATIVA DE CREDITO DE LIVRE ADMISSAO DE ASSOCIADOS DE JARAGUA DO SUL E REGIAO - SICOOB CEJASCRED'],
        'reus': ['ANDERSON JOSE BUENO'],
    },
    {
        'numero_processo': '5146888-56.2025.8.24.0930',
        'data_distribuicao': '22/10/2025',
        'autores': ['COOPERATIVA DE CREDITO DE LIVRE ADMISSAO DE ASSOCIADOS DO VALE DO CANOINHAS - SICOOB CREDICANOINHAS/SC'],
        'reus': ['JOSNEI ROGERIO MILCHESKI'],
    },
    {
        'numero_processo': '5109543-27.2023.8.24.0930',
        'data_distribuicao': '21/11/2023',
        'autores': ['COOPERATIVA DE CREDITO DE LIVRE ADMISSAO DE ASSOCIADOS DO VALE DO CANOINHAS - SICOOB CREDICANOINHAS/SC'],
        'reus': ['EVANDRO DO NASCIMENTO'],
    },
    {
        'numero_processo': '5034136-78.2024.8.24.0930',
        'data_distribuicao': '18/04/2024',
        'autores': ['SANTANDER SOCIEDADE DE CREDITO, FINANCIAMENTO E INVESTIMENTO S.A.'],
        'reus': ['JOSE CARLOS KUSS'],
    },
    {
        'numero_processo': '5133804-22.2024.8.24.0930',
        'data_distribuicao': '28/11/2024',
        'autores': ['COOPERATIVA DE CREDITO DE LIVRE ADMISSAO DE ASSOCIADOS DO VALE DO CANOINHAS - SICOOB CREDICANOINHAS/SC'],
        'reus': ['EVANDRO DO NASCIMENTO'],
    },
    {
        'numero_processo': '5006773-48.2024.8.24.0015',
        'data_distribuicao': '22/09/2024',
        'autores': ['OSEIAS JAREMCZUK'],
        'reus': ['GENESIO DE MOURA MUZEL FILHO'],
    },
    {
        'numero_processo': '5002465-66.2024.8.24.0015',
        'data_distribuicao': '16/04/2024',
        'autores': ['PAULO ROSA DA SILVA'],
        'reus': ['DIMAQ GB COMERCIO DE MAQUINAS AGRICOLAS LTDA'],
    },
    {
        'numero_processo': '5002023-37.2023.8.24.0015',
        'data_distribuicao': '10/03/2023',
        'autores': ['CRISTIAN RODINEI DE JESUS'],
        'reus': ['AMERICANAS S.A - EM RECUPERACAO JUDICIAL'],
    },
    {
        'numero_processo': '5003334-29.2024.8.24.0015',
        'data_distribuicao': '18/05/2024',
        'autores': ['CRISTIAN RODINEI DE JESUS'],
        'reus': ['AMERICANAS S.A - EM RECUPERACAO JUDICIAL'],
    },
    {
        'numero_processo': '5003981-24.2024.8.24.0015',
        'data_distribuicao': '14/06/2024',
        'autores': ['OSNI BATISTA'],
        'reus': ['MARCOS DIEGO ANDRADE TONIAL'],
    },
    {
        'numero_processo': '5004885-44.2024.8.24.0015',
        'data_distribuicao': '13/07/2024',
        'autores': ['RACER AUTO E PICK-UPS LTDA'],
        'reus': ['CRISTIANE MARIA GUGELMIN SERVICOS CONTABEIS'],
    },
    {
        'numero_processo': '5003087-48.2024.8.24.0015',
        'data_distribuicao': '08/05/2024',
        'autores': ['JOSIAS IGNASZEVSKI'],
        'reus': ['FAURI BATISTA'],
    },
    {
        'numero_processo': '5007477-32.2022.8.24.0015',
        'data_distribuicao': '14/10/2022',
        'autores': ['COOPERATIVA DE CREDITO DE LIVRE ADMISSAO DE ASSOCIADOS DO VALE DO CANOINHAS - SICOOB CREDICANOINHAS/SC'],
        'reus': ['EVANDRO DO NASCIMENTO'],
    },
    {
        'numero_processo': '5001619-49.2024.8.24.0015',
        'data_distribuicao': '14/03/2024',
        'autores': ['ANDRE PAULO LEON CELEVI'],
        'reus': ['NILTON ANTONIO CAMELLO JUNIOR'],
    },
    {
        'numero_processo': '5006625-37.2024.8.24.0015',
        'data_distribuicao': '16/09/2024',
        'autores': ['OSVALDO JOSE MACHRY'],
        'reus': ['BUENO AUTO PECAS MULTIMARCAS LTDA'],
    },
    {
        'numero_processo': '5006739-73.2024.8.24.0015',
        'data_distribuicao': '19/09/2024',
        'autores': ['GILBERTO BATISTA MENDES TAQUES'],
        'reus': ['MASTER MONTAGENS E INSTALACOES ELETRICAS LTDA'],
    },
    {
        'numero_processo': '5006740-58.2024.8.24.0015',
        'data_distribuicao': '19/09/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['EDER ANHAIA'],
    },
    {
        'numero_processo': '0300014-62.2017.8.24.0068',
        'data_distribuicao': '12/01/2017',
        'autores': ['AFRIB-ABATEDOURO E FRIGORIFICO BIONDO LTDA'],
        'reus': ['ROBERT ALVES ELIAS'],
    },
    {
        'numero_processo': '5007484-53.2024.8.24.0015',
        'data_distribuicao': '20/10/2024',
        'autores': ['OSEIAS JAREMCZUK'],
        'reus': ['GENESIO DE MOURA MUZEL FILHO'],
    },
    {
        'numero_processo': '0302158-37.2018.8.24.0015',
        'data_distribuicao': '05/06/2018',
        'autores': ['PPEDRA - COMERCIO E INTERMEDIACAO LTDA'],
        'reus': ['ANDERSON TITON'],
    },
    {
        'numero_processo': '5003266-45.2025.8.24.0015',
        'data_distribuicao': '10/05/2025',
        'autores': ['UNIVERSALL TELHAS E ACOS LTDA'],
        'reus': ['PATRICIA GUESSER ALVES SOARES'],
    },
    {
        'numero_processo': '5003267-30.2025.8.24.0015',
        'data_distribuicao': '10/05/2025',
        'autores': ['UNIVERSALL TELHAS E ACOS LTDA'],
        'reus': ['JK PRESTADORA DE SERVICOS MANUTENCAO SOLDA LTDA'],
    },
    {
        'numero_processo': '5004349-96.2025.8.24.0015',
        'data_distribuicao': '21/06/2025',
        'autores': ['UNIVERSALL TELHAS E ACOS LTDA'],
        'reus': ['METALEXPERT ESTRUTURAS METALICAS LTDA'],
    },
    {
        'numero_processo': '5004350-81.2025.8.24.0015',
        'data_distribuicao': '21/06/2025',
        'autores': ['MARCIO FIGURA'],
        'reus': ['JOAO MARIA MARTINS'],
    },
    {
        'numero_processo': '5005821-35.2025.8.24.0015',
        'data_distribuicao': '19/08/2025',
        'autores': ['UNIVERSALL TELHAS E ACOS LTDA'],
        'reus': ['PATRICIA GUESSER ALVES SOARES'],
    },
    {
        'numero_processo': '5005822-20.2025.8.24.0015',
        'data_distribuicao': '19/08/2025',
        'autores': ['UNIVERSALL TELHAS E ACOS LTDA'],
        'reus': ['JK PRESTADORA DE SERVICOS MANUTENCAO SOLDA LTDA'],
    },
    {
        'numero_processo': '5006787-95.2025.8.24.0015',
        'data_distribuicao': '22/09/2025',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['LUIS ALEXANDRE PAULO CONSTRUCOES E SERVICOS DE ENGENHARIA'],
    },
    {
        'numero_processo': '5007035-61.2025.8.24.0015',
        'data_distribuicao': '30/09/2025',
        'autores': ['CRISTIANE MARIA GUGELMIN SERVICOS CONTABEIS', 'FLAVIO ANDREI HAAG'],
        'reus': ['RACER AUTO E PICK-UPS LTDA'],
    },
    {
        'numero_processo': '5008832-72.2025.8.24.0015',
        'data_distribuicao': '05/12/2025',
        'autores': ['TOO SEGUROS S.A.'],
        'reus': ['JOSMAR MILCHESKI'],
    },
    {
        'numero_processo': '5008224-45.2023.8.24.0015',
        'data_distribuicao': '11/10/2023',
        'autores': ['JOSMAR MILCHESKI'],
        'reus': ['SANTOS & SANTOS VEICULOS LTDA'],
    },
    {
        'numero_processo': '5005985-68.2023.8.24.0015',
        'data_distribuicao': '18/07/2023',
        'autores': ['OFICINA MECANICA ZEIAS LTDA'],
        'reus': ['DOUGLAS CORREIA DE FREITAS'],
    },
    {
        'numero_processo': '5006664-68.2023.8.24.0015',
        'data_distribuicao': '14/08/2023',
        'autores': ['OSEIAS JAREMCZUK'],
        'reus': ['GENESIO DE MOURA MUZEL FILHO'],
    },
    {
        'numero_processo': '5006190-97.2023.8.24.0015',
        'data_distribuicao': '25/07/2023',
        'autores': ['PAULO ROSA DA SILVA'],
        'reus': ['DIMAQ GB COMERCIO DE MAQUINAS AGRICOLAS LTDA'],
    },
    {
        'numero_processo': '5006665-53.2023.8.24.0015',
        'data_distribuicao': '14/08/2023',
        'autores': ['OSEIAS JAREMCZUK'],
        'reus': ['DOUGLAS CORREIA DE FREITAS'],
    },
    {
        'numero_processo': '5005892-08.2023.8.24.0015',
        'data_distribuicao': '12/07/2023',
        'autores': ['SILVANO CORREA'],
        'reus': ['MOACIR POLLY 76525155991'],
    },
    {
        'numero_processo': '5007356-67.2023.8.24.0015',
        'data_distribuicao': '08/09/2023',
        'autores': ['OSEIAS JAREMCZUK'],
        'reus': ['GENESIO DE MOURA MUZEL FILHO'],
    },
    {
        'numero_processo': '5004516-21.2022.8.24.0015',
        'data_distribuicao': '21/06/2022',
        'autores': ['DONATO DE MELLO'],
        'reus': ['JAIRO CESAR DE CARVALHO'],
    },
    {
        'numero_processo': '5007870-20.2023.8.24.0015',
        'data_distribuicao': '29/09/2023',
        'autores': ['AZ MARTELINHO DE OURO LTDA'],
        'reus': ['CLEONICE DE FATIMA MARTINS BUENO'],
    },
    {
        'numero_processo': '5007871-05.2023.8.24.0015',
        'data_distribuicao': '29/09/2023',
        'autores': ['AZ MARTELINHO DE OURO LTDA'],
        'reus': ['LEOMAR ALVES CARDOSO'],
    },
    {
        'numero_processo': '5008000-10.2023.8.24.0015',
        'data_distribuicao': '04/10/2023',
        'autores': ['JOSMAR MILCHESKI'],
        'reus': ['SANTOS & SANTOS VEICULOS LTDA'],
    },
    {
        'numero_processo': '5002022-18.2024.8.24.0015',
        'data_distribuicao': '28/03/2024',
        'autores': ['AZ MARTELINHO DE OURO LTDA'],
        'reus': ['CLEONICE DE FATIMA MARTINS BUENO'],
    },
    {
        'numero_processo': '0005732-25.2010.8.24.0015',
        'data_distribuicao': '29/06/2010',
        'autores': ['ALISSA GONCALVES BUENO'],
        'reus': ['ANDERSON JOSE BUENO'],
    },
    {
        'numero_processo': '5008276-41.2023.8.24.0015',
        'data_distribuicao': '16/10/2023',
        'autores': ['WILLIAN CILAS TEIXEIRA DA SILVA'],
        'reus': ['AUTO PRATENSE LTDA'],
    },
    {
        'numero_processo': '5000803-67.2024.8.24.0015',
        'data_distribuicao': '13/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['LAERCIO JOSE ANTUNES MOREIRA'],
    },
    {
        'numero_processo': '5001210-73.2024.8.24.0015',
        'data_distribuicao': '28/02/2024',
        'autores': ['ALLAN RENAN DOS SANTOS', 'JACIARA GREIN'],
        'reus': ['LAERCIO JOSE ANTUNES MOREIRA'],
    },
    {
        'numero_processo': '5001188-15.2024.8.24.0015',
        'data_distribuicao': '28/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['MARCELO LIMA WALTRICK'],
    },
    {
        'numero_processo': '5001190-82.2024.8.24.0015',
        'data_distribuicao': '28/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['M.D.M CONSTRUTORA LTDA'],
    },
    {
        'numero_processo': '5001187-30.2024.8.24.0015',
        'data_distribuicao': '28/02/2024',
        'autores': ['JOSNEI ROGERIO MILCHESKI'],
        'reus': ['GERALDO NADROSKI 90208897968'],
    },
    {
        'numero_processo': '5000805-37.2024.8.24.0015',
        'data_distribuicao': '13/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['MARCELO LIMA WALTRICK'],
    },
    {
        'numero_processo': '5000804-52.2024.8.24.0015',
        'data_distribuicao': '13/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['M.D.M CONSTRUTORA LTDA'],
    },
    {
        'numero_processo': '5009387-60.2023.8.24.0015',
        'data_distribuicao': '29/11/2023',
        'autores': ['VALERIA APARECIDA FERREIRA BAYESTORFF'],
        'reus': ['CELSO SOARES BRAMBILA 00407166947'],
    },
    {
        'numero_processo': '5000802-82.2024.8.24.0015',
        'data_distribuicao': '13/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['GUILHERME FRANCISCO ALVES PEREIRA'],
    },
    {
        'numero_processo': '5000801-97.2024.8.24.0015',
        'data_distribuicao': '13/02/2024',
        'autores': ['S B M OFICINA MECANICA LTDA'],
        'reus': ['ANDRE FRANCISCO WATZKO'],
    },
    {
        'numero_processo': '5000501-38.2024.8.24.0015',
        'data_distribuicao': '31/01/2024',
        'autores': ['JOSMAR MILCHESKI'],
        'reus': ['SANTOS & SANTOS VEICULOS LTDA'],
    },
    {
        'numero_processo': '5004067-86.2025.8.24.0038',
        'data_distribuicao': '05/02/2025',
        'autores': ['DIDIER JIRMAR CARRASCO ARELLANO'],
        'reus': ['ANDERSON TITON'],
    },
    {
        'numero_processo': '5030904-18.2024.8.24.0038',
        'data_distribuicao': '16/07/2024',
        'autores': ['DIDIER JIRMAR CARRASCO ARELLANO'],
        'reus': ['ANDERSON TITON'],
    },
    {
        'numero_processo': '5002630-02.2024.8.24.0052',
        'data_distribuicao': '03/07/2024',
        'autores': ['MARIO DE SOUZA'],
        'reus': ['DIMAQ GB COMERCIO DE MAQUINAS AGRICOLAS LTDA'],
    },
    {
        'numero_processo': '5003984-96.2023.8.24.0052',
        'data_distribuicao': '04/09/2023',
        'autores': ['RICARDO JOSE TEIXEIRA'],
        'reus': ['LORETI APARECIDA AMBROSIO'],
    },
    {
        'numero_processo': '5003983-14.2023.8.24.0052',
        'data_distribuicao': '04/09/2023',
        'autores': ['RICARDO JOSE TEIXEIRA'],
        'reus': ['MIGUEL EDSON CORREA'],
    },
    {
        'numero_processo': '5004782-23.2024.8.24.0052',
        'data_distribuicao': '02/12/2024',
        'autores': ['RICARDO JOSE TEIXEIRA'],
        'reus': ['CRISTIANO MAIER'],
    },
    {
        'numero_processo': '5000262-20.2024.8.24.0052',
        'data_distribuicao': '24/01/2024',
        'autores': ['RICARDO JOSE TEIXEIRA'],
        'reus': ['CRISTIANO MAIER'],
    },
    {
        'numero_processo': '5001911-07.2021.8.24.0058',
        'data_distribuicao': '23/03/2021',
        'autores': ['ALEKSANDRO BRASIL LOPES'],
        'reus': ['VALDIR NOGUEIRA DE OLIVEIRA'],
    },
]

def popular_processos_gilberto() -> Dict[str, Any]:
    """
    Popula a coleção processos_migracao com os 62 processos hardcoded do Gilberto.
    Verifica se já existem antes de inserir (evita duplicatas).
    
    Returns:
        Dict com 'sucesso', 'inseridos', 'ja_existentes' e opcionalmente 'erro'
    """
    try:
        db = get_db()
        if not db:
            return {"sucesso": False, "erro": "Conexão com banco de dados indisponível."}
        
        inseridos = 0
        ja_existentes = 0
        
        for processo_data in PROCESSOS_GILBERTO:
            numero = processo_data['numero_processo']
            
            # Verifica se já existe (mesmo número E origem gilberto)
            docs = db.collection(COLECAO_MIGRACAO) \
                .where("numero_processo", "==", numero) \
                .where("origem", "==", "gilberto") \
                .limit(1).stream()
            
            if any(docs):
                ja_existentes += 1
                continue
            
            # Prepara documento no formato esperado pela migração
            processo = {
                "numero_processo": numero,
                "classe_processo": "",  # Será preenchido manualmente
                "autores_sugestao": processo_data['autores'],
                "reus_sugestao": processo_data['reus'],
                "localidade_judicial": "",
                "assunto": "",
                "data_abertura": processo_data['data_distribuicao'],
                "valor_causa": "",
                
                # Campo discriminador de origem
                "origem": "gilberto",
                
                # Campos fixos
                "sistema_processual": "eproc - TJSC - 1ª instância",
                "estado": "Santa Catarina",
                "responsavel": "Gilberto",
                "tipo_processo": "Judicial",
                "prioridade": "P4",
                "status_migracao": "pendente",
                "data_importacao": datetime.now(),
                
                # Campos vazios para preenchimento manual
                "titulo_processo": "",
                "link_eproc": "",
                "nucleo": "",
                "area_direito": "",
                "clientes": [],
                "parte_contraria": [],
                "outros_envolvidos": [],
                "casos_vinculados": [],
                "processo_pai": ""
            }
            
            db.collection(COLECAO_MIGRACAO).add(processo)
            inseridos += 1
        
        logger.info(f"[GILBERTO] Processos populados: {inseridos} inseridos, {ja_existentes} já existiam")
        
        return {
            "sucesso": True,
            "inseridos": inseridos,
            "ja_existentes": ja_existentes,
            "total": len(PROCESSOS_GILBERTO)
        }
        
    except Exception as e:
        logger.error(f"Erro ao popular processos do Gilberto: {e}")
        import traceback
        traceback.print_exc()
        return {"sucesso": False, "erro": str(e)}


def importar_planilha_migracao(origem: str = 'lenon') -> Dict[str, Any]:
    """
    Lê a planilha Excel e importa os dados para a coleção processos_migracao.
    
    Args:
        origem: 'lenon' ou 'gilberto' - identifica de qual planilha importar
    """
    try:
        caminho_planilha = CAMINHOS_PLANILHAS.get(origem, CAMINHOS_PLANILHAS['lenon'])
        responsavel = RESPONSAVEIS.get(origem, 'Lenon Taques')
        
        if not os.path.exists(caminho_planilha):
            return {"sucesso": False, "erro": f"Planilha não encontrada em: {caminho_planilha}"}

        # Lê planilha usando pandas com xlrd para .xls
        # skiprows=1 para pular o cabeçalho se necessário (conforme requisito)
        df = pd.read_excel(caminho_planilha, skiprows=1, engine='xlrd')
        
        db = get_db()
        if not db:
            return {"sucesso": False, "erro": "Conexão com banco de dados indisponível."}

        importados = 0
        pularam = 0
        
        # Mapeamento de colunas baseado no requisito
        # A:0, B:1, C:2, D:3, E:4, F:5, I:8, J:9
        
        for _, row in df.iterrows():
            try:
                numero = str(row.iloc[0]).strip()
                if not numero or numero == 'nan':
                    pularam += 1
                    continue
                
                # Verifica se já existe na migração (mesmo número E mesma origem)
                docs = db.collection(COLECAO_MIGRACAO) \
                    .where("numero_processo", "==", numero) \
                    .where("origem", "==", origem) \
                    .limit(1).stream()
                if any(docs):
                    pularam += 1
                    continue

                # Processa sugestões de nomes (C e D)
                autores = [n.strip() for n in str(row.iloc[2]).split(';') if n.strip() and n.lower() != 'nan']
                reus = [n.strip() for n in str(row.iloc[3]).split(';') if n.strip() and n.lower() != 'nan']

                # Prepara documento
                processo = {
                    "numero_processo": numero,
                    "classe_processo": str(row.iloc[1]) if str(row.iloc[1]) != 'nan' else "",
                    "autores_sugestao": autores,
                    "reus_sugestao": reus,
                    "localidade_judicial": str(row.iloc[4]) if str(row.iloc[4]) != 'nan' else "",
                    "assunto": str(row.iloc[5]) if str(row.iloc[5]) != 'nan' else "",
                    "data_abertura": str(row.iloc[8]) if str(row.iloc[8]) != 'nan' else "",
                    "valor_causa": str(row.iloc[9]) if str(row.iloc[9]) != 'nan' else "",
                    
                    # Campo discriminador de origem
                    "origem": origem,
                    
                    # Campos fixos
                    "sistema_processual": "eproc - TJSC - 1ª instância",
                    "estado": "Santa Catarina",
                    "responsavel": responsavel,
                    "tipo_processo": "Judicial",
                    "prioridade": "P4",
                    "status_migracao": "pendente",
                    "data_importacao": datetime.now(),
                    
                    # Campos vazios para preenchimento manual
                    "titulo_processo": "",
                    "link_eproc": "",
                    "nucleo": "",
                    "area_direito": "",
                    "clientes": [],
                    "parte_contraria": [],
                    "outros_envolvidos": [],
                    "casos_vinculados": [],
                    "processo_pai": ""
                }

                db.collection(COLECAO_MIGRACAO).add(processo)
                importados += 1
            except Exception as e:
                logger.error(f"Erro ao processar linha da planilha: {e}")
                pularam += 1

        return {
            "sucesso": True, 
            "importados": importados, 
            "pularam": pularam,
            "total_lido": len(df)
        }

    except Exception as e:
        logger.error(f"Erro crítico na importação: {e}")
        return {"sucesso": False, "erro": str(e)}

def obter_estatisticas_migracao(origem: str = 'lenon') -> Dict[str, Any]:
    """
    Retorna contadores de progresso da migração filtrados por origem.
    
    Args:
        origem: 'lenon' ou 'gilberto' - filtra estatísticas por origem
    """
    try:
        db = get_db()
        
        # Filtra por origem
        query = db.collection(COLECAO_MIGRACAO).where("origem", "==", origem)
        docs = list(query.stream())
        
        # Fallback: se não houver documentos com origem, busca sem filtro (compatibilidade)
        if not docs and origem == 'lenon':
            # Busca documentos que NÃO têm campo origem (dados antigos)
            all_docs = list(db.collection(COLECAO_MIGRACAO).stream())
            docs = [d for d in all_docs if d.to_dict().get("origem") in [None, '', 'lenon']]
        
        total = len(docs)
        pendentes = sum(1 for d in docs if d.to_dict().get("status_migracao") == "pendente")
        # Considera tanto "migrado" quanto "concluido" para compatibilidade
        concluidos = sum(1 for d in docs if d.to_dict().get("status_migracao") in ["migrado", "concluido"])
        
        return {
            "total": total,
            "pendentes": pendentes,
            "concluidos": concluidos,
            "progresso": (concluidos / total * 100) if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return {"total": 0, "pendentes": 0, "concluidos": 0, "progresso": 0}

def listar_processos_migracao(status: Optional[str] = None, origem: str = 'lenon') -> List[Dict[str, Any]]:
    """
    Lista processos da coleção de migração filtrados por origem.
    
    Args:
        status: 'todos', 'pendente' ou 'concluido' - filtra por status
        origem: 'lenon' ou 'gilberto' - filtra por origem da planilha
    
    Ordenação:
    - Pendentes primeiro (ordenados por data de distribuição, depois número)
    - Migrados depois (ordenados por data de distribuição, depois número)
    """
    try:
        db = get_db()
        
        # Base query filtrada por origem
        base_query = db.collection(COLECAO_MIGRACAO).where("origem", "==", origem)
        
        if status and status != "todos":
            # Compatibilidade: "concluido" também busca "migrado"
            if status == "concluido":
                # Busca processos migrados ou concluídos (não pendentes)
                docs_migrados = base_query.where("status_migracao", "==", "migrado").stream()
                docs_concluidos = base_query.where("status_migracao", "==", "concluido").stream()
                # Converte generators para listas e combina
                docs = list(docs_migrados) + list(docs_concluidos)
            else:
                docs = base_query.where("status_migracao", "==", status).stream()
        else:
            docs = base_query.stream()
        
        # Converte para lista
        docs = list(docs)
        
        # Fallback: se não houver documentos com origem e for lenon, busca dados antigos
        if not docs and origem == 'lenon':
            all_docs = list(db.collection(COLECAO_MIGRACAO).stream())
            docs = [d for d in all_docs if d.to_dict().get("origem") in [None, '', 'lenon']]
            
            # Aplica filtro de status nos dados antigos
            if status and status != "todos":
                if status == "concluido":
                    docs = [d for d in docs if d.to_dict().get("status_migracao") in ["migrado", "concluido"]]
                else:
                    docs = [d for d in docs if d.to_dict().get("status_migracao") == status]
            
        lista = []
        for doc in docs:
            d = doc.to_dict()
            d["_id"] = doc.id
            lista.append(d)
        
        # Função auxiliar para extrair data de distribuição para ordenação
        def get_data_ordenacao(processo):
            """Extrai data para ordenação, retorna datetime ou string vazia"""
            data_abertura = processo.get("data_abertura")
            if not data_abertura:
                return ""
            
            # Se for string, tenta converter
            if isinstance(data_abertura, str):
                try:
                    # Tenta vários formatos
                    formatos = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']
                    for fmt in formatos:
                        try:
                            return datetime.strptime(data_abertura.split()[0], fmt)
                        except:
                            continue
                    return data_abertura  # Retorna string se não conseguir converter
                except:
                    return data_abertura
            
            # Se já for datetime ou DatetimeWithNanoseconds
            if hasattr(data_abertura, 'isoformat'):
                try:
                    dt_str = data_abertura.isoformat()
                    if 'T' in dt_str:
                        dt_str_clean = dt_str.split('+')[0].split('Z')[0].split('.')[0]
                        return datetime.fromisoformat(dt_str_clean)
                except:
                    pass
            
            return data_abertura if hasattr(data_abertura, 'year') else ""
        
        # Ordena: pendentes primeiro, depois migrados
        # Dentro de cada grupo, ordena por data de distribuição (mais antiga primeiro), depois número
        lista.sort(key=lambda x: (
            x.get("status_migracao") not in ["pendente"],  # Pendentes primeiro (False < True)
            get_data_ordenacao(x) or "",  # Data de distribuição
            x.get("numero_processo", "")  # Número do processo como desempate
        ))
        
        return lista
    except Exception as e:
        logger.error(f"Erro ao listar processos de migração: {e}")
        return []

def salvar_processo_migracao(processo_id: str, dados: Dict[str, Any]) -> bool:
    """Atualiza dados do processo na migração e cria registro definitivo se concluído."""
    try:
        db = get_db()
        dados["atualizado_em"] = datetime.now()
        dados["status_migracao"] = "concluido"
        
        # 1. Atualiza registro temporário
        db.collection(COLECAO_MIGRACAO).document(processo_id).update(dados)
        
        # 2. Prepara e cria registro definitivo na coleção 'processos'
        doc_migracao = db.collection(COLECAO_MIGRACAO).document(processo_id).get().to_dict()
        
        processo_definitivo = {
            "titulo": doc_migracao["titulo_processo"],
            "numero": doc_migracao["numero_processo"],
            "tipo": doc_migracao["tipo_processo"],
            "sistema_processual": doc_migracao["sistema_processual"],
            "status": "Ativo", # Padrão para novos processos migrados
            "area": doc_migracao["area_direito"],
            "nucleo": doc_migracao["nucleo"],
            "estado": doc_migracao["estado"],
            "data_abertura": doc_migracao["data_abertura"],
            "link": doc_migracao["link_eproc"],
            "prioridade": doc_migracao["prioridade"],
            "responsavel_nome": doc_migracao["responsavel"],
            "clientes": doc_migracao["clientes"],
            "parte_contraria_nomes": doc_migracao["parte_contraria"],
            "outros_envolvidos": doc_migracao["outros_envolvidos"],
            "casos_ids": doc_migracao["casos_vinculados"],
            "processo_pai_id": doc_migracao["processo_pai"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "migrado": True,
            "id_migracao": processo_id
        }
        
        # Cria ou atualiza no definitivo
        # Verifica se já existe no definitivo pelo número
        existente = list(db.collection(COLECAO_DEFINITIVA).where("numero", "==", doc_migracao["numero_processo"]).limit(1).stream())
        
        if existente:
            definitivo_id = existente[0].id
            db.collection(COLECAO_DEFINITIVA).document(definitivo_id).update(processo_definitivo)
        else:
            _, doc_ref = db.collection(COLECAO_DEFINITIVA).add(processo_definitivo)
            definitivo_id = doc_ref.id
            
        # 3. Vincula ID definitivo no registro de migração
        db.collection(COLECAO_MIGRACAO).document(processo_id).update({"processo_definitivo_id": definitivo_id})
        
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar processo migrado {processo_id}: {e}")
        return False

def atualizar_status_migracao(processo_id: str, novo_status: str) -> bool:
    """
    Atualiza apenas o status de migração de um processo.
    
    Args:
        processo_id: ID do documento na coleção processos_migracao
        novo_status: "pendente" ou "migrado" (lowercase)
        
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        if novo_status not in ["pendente", "migrado"]:
            logger.error(f"Status inválido: {novo_status}. Deve ser 'pendente' ou 'migrado'")
            return False
        
        db = get_db()
        if not db:
            logger.error("Conexão com banco de dados indisponível")
            return False
        
        db.collection(COLECAO_MIGRACAO).document(processo_id).update({
            "status_migracao": novo_status,
            "atualizado_em": datetime.now()
        })
        
        logger.info(f"Status do processo {processo_id} atualizado para: {novo_status}")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar status do processo {processo_id}: {e}")
        return False

def excluir_processo_migracao(doc_id: str) -> bool:
    """
    Exclui permanentemente um processo da coleção processos_migracao.
    
    Args:
        doc_id: ID do documento a ser excluído
        
    Returns:
        True se excluído com sucesso, False caso contrário
    """
    try:
        if not doc_id:
            logger.error("ID do documento não fornecido")
            return False
        
        db = get_db()
        if not db:
            logger.error("Conexão com banco de dados indisponível")
            return False
        
        # Verifica se documento existe antes de deletar
        doc_ref = db.collection(COLECAO_MIGRACAO).document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"Documento {doc_id} não encontrado na coleção")
            return False
        
        # Obtém número do processo para log antes de deletar
        dados = doc.to_dict()
        numero_processo = dados.get('numero_processo', 'N/A')
        
        # Deleta o documento
        doc_ref.delete()
        
        logger.info(f"Processo {doc_id} (número: {numero_processo}) excluído da coleção processos_migracao")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao excluir processo {doc_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def finalizar_migracao_completa(origem: str = 'lenon') -> Dict[str, Any]:
    """
    Finaliza o processo de migração após todos os itens serem concluídos.
    
    Args:
        origem: 'lenon' ou 'gilberto' - verifica apenas processos da origem especificada
    """
    try:
        db = get_db()
        
        # Verifica se ainda há pendentes para esta origem
        query = db.collection(COLECAO_MIGRACAO) \
            .where("origem", "==", origem) \
            .where("status_migracao", "==", "pendente") \
            .limit(1)
        docs = list(query.stream())
        
        # Fallback para dados antigos (origem não definida)
        if not docs and origem == 'lenon':
            all_pendentes = list(
                db.collection(COLECAO_MIGRACAO)
                .where("status_migracao", "==", "pendente")
                .stream()
            )
            docs = [d for d in all_pendentes if d.to_dict().get("origem") in [None, '', 'lenon']]
        
        if docs:
            responsavel = RESPONSAVEIS.get(origem, origem.capitalize())
            return {"sucesso": False, "erro": f"Ainda existem processos pendentes de {responsavel}."}
        
        responsavel = RESPONSAVEIS.get(origem, origem.capitalize())
        return {"sucesso": True, "mensagem": f"Migração de {responsavel} finalizada com sucesso!"}
    except Exception as e:
        logger.error(f"Erro ao finalizar migração: {e}")
        return {"sucesso": False, "erro": str(e)}



