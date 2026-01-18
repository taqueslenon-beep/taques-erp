"""
Módulo de Validação e Cadastro em Massa de Pessoas da Migração EPROC.

Funcionalidades:
- Buscar pessoas já cadastradas no Firebase
- Extrair pessoas dos processos EPROC
- Comparar e identificar pessoas não cadastradas
- Cadastro em massa de pessoas faltantes

Coleções Firebase utilizadas:
- people: Coleção principal de pessoas
- vg_pessoas: Pessoas do workspace Visão Geral
- vg_envolvidos: Outros envolvidos
"""
import unicodedata
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from difflib import SequenceMatcher
from mini_erp.firebase_config import get_db

# Configuração de logging
logger = logging.getLogger(__name__)

# Importar dados dos processos do Gilberto
from .migracao_service import PROCESSOS_GILBERTO


# =============================================================================
# CONSTANTES
# =============================================================================

# Coleções Firebase
COLECAO_PEOPLE = 'people'
COLECAO_VG_PESSOAS = 'vg_pessoas'
COLECAO_VG_ENVOLVIDOS = 'vg_envolvidos'
COLECAO_LOGS_MIGRACAO = 'logs_migracao'

# Limiar de similaridade para detecção de duplicatas
LIMIAR_DUPLICATA = 0.90  # 90% de similaridade

# Palavras a ignorar na comparação de nomes (artigos, preposições)
PALAVRAS_IGNORAR = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'para'}


# =============================================================================
# FUNÇÕES DE NORMALIZAÇÃO
# =============================================================================

def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para comparação:
    - Remove acentos
    - Converte para minúsculas
    - Remove espaços extras
    - Remove pontuação
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    if not texto:
        return ''
    
    # Remove acentos usando unicodedata
    texto_sem_acentos = unicodedata.normalize('NFKD', texto)
    texto_sem_acentos = texto_sem_acentos.encode('ASCII', 'ignore').decode('ASCII')
    
    # Converte para minúsculas
    texto_lower = texto_sem_acentos.lower()
    
    # Remove pontuação (exceto espaços)
    texto_limpo = re.sub(r'[^\w\s]', '', texto_lower)
    
    # Remove espaços extras
    texto_final = ' '.join(texto_limpo.split())
    
    return texto_final.strip()


def normalizar_cpf_cnpj(documento: str) -> str:
    """
    Normaliza CPF/CNPJ removendo pontuação.
    
    Args:
        documento: CPF ou CNPJ com ou sem formatação
        
    Returns:
        Apenas números
    """
    if not documento:
        return ''
    
    # Remove tudo que não for dígito
    apenas_numeros = re.sub(r'\D', '', str(documento))
    
    return apenas_numeros


def extrair_cpf_cnpj_do_nome(nome: str) -> Tuple[str, str]:
    """
    Extrai CPF/CNPJ que pode estar no final do nome.
    Exemplo: "MOACIR POLLY 76525155991" -> ("MOACIR POLLY", "76525155991")
    
    Args:
        nome: Nome que pode conter CPF/CNPJ no final
        
    Returns:
        Tupla (nome_limpo, cpf_cnpj)
    """
    if not nome:
        return ('', '')
    
    # Procura sequência de 11 ou 14 dígitos no final
    padrao = r'(\d{11}|\d{14})$'
    match = re.search(padrao, nome.replace(' ', ''))
    
    if match:
        cpf_cnpj = match.group(1)
        # Remove o CPF/CNPJ do nome
        nome_limpo = re.sub(r'\s*\d{11}\s*$|\s*\d{14}\s*$', '', nome).strip()
        return (nome_limpo, cpf_cnpj)
    
    return (nome, '')


def identificar_tipo_pessoa(nome: str) -> str:
    """
    Identifica se é pessoa física (PF) ou jurídica (PJ) pelo nome.
    
    Args:
        nome: Nome da pessoa/empresa
        
    Returns:
        'PF' ou 'PJ'
    """
    if not nome:
        return 'PF'
    
    nome_upper = nome.upper()
    
    # Indicadores de pessoa jurídica
    indicadores_pj = [
        'LTDA', 'S.A.', 'S/A', 'SA ', 'EIRELI', 'ME ', 'EPP',
        'COOPERATIVA', 'SOCIEDADE', 'COMERCIO', 'SERVICOS',
        'CONSTRUTORA', 'INDUSTRIA', 'COMERCIAL', 'FINANCIAMENTO',
        'INVESTIMENTO', 'CREDITO', 'BANCO', 'SEGUROS',
        'RECUPERACAO JUDICIAL', 'PRESTADORA', 'OFICINA',
        'CONSTRUCOES', 'ENGENHARIA', 'CONTABEIS'
    ]
    
    for indicador in indicadores_pj:
        if indicador in nome_upper:
            return 'PJ'
    
    return 'PF'


def calcular_similaridade(texto1: str, texto2: str) -> float:
    """
    Calcula similaridade entre dois textos usando SequenceMatcher.
    
    Args:
        texto1: Primeiro texto
        texto2: Segundo texto
        
    Returns:
        Valor entre 0 e 1 (1 = idênticos)
    """
    if not texto1 or not texto2:
        return 0.0
    
    # Normaliza ambos os textos
    t1 = normalizar_texto(texto1)
    t2 = normalizar_texto(texto2)
    
    if not t1 or not t2:
        return 0.0
    
    # Calcula similaridade
    return SequenceMatcher(None, t1, t2).ratio()


# =============================================================================
# FUNÇÕES DE BUSCA NO FIREBASE
# =============================================================================

def buscar_pessoas_cadastradas() -> List[Dict[str, Any]]:
    """
    Busca todas as pessoas já cadastradas no Firebase.
    Combina pessoas de todas as coleções relevantes.
    
    Returns:
        Lista de pessoas com campos normalizados para comparação
    """
    try:
        db = get_db()
        if not db:
            logger.error("[VALIDAÇÃO] Conexão com Firebase não disponível")
            return []
        
        pessoas_cadastradas = []
        
        # 1. Buscar da coleção 'people' (principal)
        try:
            docs_people = db.collection(COLECAO_PEOPLE).stream()
            for doc in docs_people:
                pessoa = doc.to_dict()
                pessoa['_id'] = doc.id
                pessoa['_colecao'] = COLECAO_PEOPLE
                
                # Extrai nome
                nome = (pessoa.get('name') or 
                        pessoa.get('full_name') or 
                        pessoa.get('display_name') or 
                        pessoa.get('nome') or '')
                
                if nome:
                    pessoa['nome_original'] = nome
                    pessoa['nome_normalizado'] = normalizar_texto(nome)
                    
                    # Extrai CPF/CNPJ se existir
                    cpf_cnpj = (pessoa.get('cpf') or 
                                pessoa.get('cnpj') or 
                                pessoa.get('cpf_cnpj') or 
                                pessoa.get('documento') or '')
                    pessoa['cpf_cnpj_normalizado'] = normalizar_cpf_cnpj(cpf_cnpj)
                    
                    pessoas_cadastradas.append(pessoa)
        except Exception as e:
            logger.warning(f"[VALIDAÇÃO] Erro ao buscar coleção 'people': {e}")
        
        # 2. Buscar da coleção 'vg_pessoas'
        try:
            docs_vg = db.collection(COLECAO_VG_PESSOAS).stream()
            for doc in docs_vg:
                pessoa = doc.to_dict()
                pessoa['_id'] = doc.id
                pessoa['_colecao'] = COLECAO_VG_PESSOAS
                
                nome = pessoa.get('nome') or pessoa.get('nome_completo') or ''
                
                if nome:
                    pessoa['nome_original'] = nome
                    pessoa['nome_normalizado'] = normalizar_texto(nome)
                    
                    cpf_cnpj = pessoa.get('cpf_cnpj') or pessoa.get('documento') or ''
                    pessoa['cpf_cnpj_normalizado'] = normalizar_cpf_cnpj(cpf_cnpj)
                    
                    pessoas_cadastradas.append(pessoa)
        except Exception as e:
            logger.warning(f"[VALIDAÇÃO] Erro ao buscar coleção 'vg_pessoas': {e}")
        
        # 3. Buscar da coleção 'vg_envolvidos'
        try:
            docs_env = db.collection(COLECAO_VG_ENVOLVIDOS).stream()
            for doc in docs_env:
                pessoa = doc.to_dict()
                pessoa['_id'] = doc.id
                pessoa['_colecao'] = COLECAO_VG_ENVOLVIDOS
                
                nome = pessoa.get('nome') or pessoa.get('nome_completo') or ''
                
                if nome:
                    pessoa['nome_original'] = nome
                    pessoa['nome_normalizado'] = normalizar_texto(nome)
                    
                    cpf_cnpj = pessoa.get('cpf_cnpj') or pessoa.get('documento') or ''
                    pessoa['cpf_cnpj_normalizado'] = normalizar_cpf_cnpj(cpf_cnpj)
                    
                    pessoas_cadastradas.append(pessoa)
        except Exception as e:
            logger.warning(f"[VALIDAÇÃO] Erro ao buscar coleção 'vg_envolvidos': {e}")
        
        logger.info(f"[VALIDAÇÃO] {len(pessoas_cadastradas)} pessoas encontradas no Firebase")
        return pessoas_cadastradas
        
    except Exception as e:
        logger.error(f"[VALIDAÇÃO] Erro ao buscar pessoas cadastradas: {e}")
        import traceback
        traceback.print_exc()
        return []


# =============================================================================
# FUNÇÕES DE EXTRAÇÃO DE PESSOAS DO EPROC
# =============================================================================

def extrair_pessoas_eproc(origem: str = 'gilberto') -> List[Dict[str, Any]]:
    """
    Extrai todas as pessoas mencionadas nos processos EPROC.
    Agrupa por nome único e conta processos relacionados.
    
    Args:
        origem: 'gilberto' ou 'lenon'
        
    Returns:
        Lista de pessoas com informações agregadas
    """
    if origem != 'gilberto':
        logger.warning(f"[VALIDAÇÃO] Origem '{origem}' não suportada ainda")
        return []
    
    # Dicionário para agrupar pessoas por nome normalizado
    pessoas_dict: Dict[str, Dict[str, Any]] = {}
    
    for processo in PROCESSOS_GILBERTO:
        numero_processo = processo.get('numero_processo', '')
        
        # Processar autores
        for autor in processo.get('autores', []):
            if autor:
                _adicionar_pessoa_dict(pessoas_dict, autor, 'autor', numero_processo)
        
        # Processar réus
        for reu in processo.get('reus', []):
            if reu:
                _adicionar_pessoa_dict(pessoas_dict, reu, 'reu', numero_processo)
    
    # Converter dicionário para lista
    pessoas_lista = list(pessoas_dict.values())
    
    logger.info(f"[VALIDAÇÃO] {len(pessoas_lista)} pessoas únicas extraídas do EPROC ({origem})")
    return pessoas_lista


def _adicionar_pessoa_dict(
    pessoas_dict: Dict[str, Dict[str, Any]], 
    nome: str, 
    papel: str, 
    numero_processo: str
):
    """
    Adiciona ou atualiza pessoa no dicionário de pessoas.
    
    Args:
        pessoas_dict: Dicionário de pessoas (modificado in-place)
        nome: Nome da pessoa
        papel: 'autor' ou 'reu'
        numero_processo: Número do processo relacionado
    """
    # Extrai CPF/CNPJ se estiver no nome
    nome_limpo, cpf_cnpj = extrair_cpf_cnpj_do_nome(nome)
    
    # Chave de agrupamento: nome normalizado
    chave = normalizar_texto(nome_limpo)
    
    if not chave:
        return
    
    if chave in pessoas_dict:
        # Atualiza pessoa existente
        pessoa = pessoas_dict[chave]
        pessoa['processos_relacionados'].add(numero_processo)
        pessoa['papeis'].add(papel)
        
        # Atualiza CPF/CNPJ se encontrado
        if cpf_cnpj and not pessoa.get('cpf_cnpj'):
            pessoa['cpf_cnpj'] = cpf_cnpj
    else:
        # Cria nova pessoa
        pessoas_dict[chave] = {
            'nome_original': nome_limpo,
            'nome_normalizado': chave,
            'cpf_cnpj': cpf_cnpj,
            'cpf_cnpj_normalizado': normalizar_cpf_cnpj(cpf_cnpj),
            'tipo_pessoa': identificar_tipo_pessoa(nome_limpo),
            'papeis': {papel},
            'processos_relacionados': {numero_processo},
            'cadastrado': False,
            'similaridade': None,
            'pessoa_similar_id': None,
            'pessoa_similar_nome': None,
        }


# =============================================================================
# FUNÇÕES DE COMPARAÇÃO
# =============================================================================

def comparar_pessoas(
    pessoas_eproc: List[Dict[str, Any]], 
    pessoas_cadastradas: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compara pessoas do EPROC com pessoas cadastradas no Firebase.
    Identifica: cadastradas, não cadastradas e possíveis duplicatas.
    
    Args:
        pessoas_eproc: Lista de pessoas extraídas do EPROC
        pessoas_cadastradas: Lista de pessoas do Firebase
        
    Returns:
        Dicionário com listas: 'cadastradas', 'nao_cadastradas', 'possiveis_duplicatas'
    """
    resultado = {
        'cadastradas': [],
        'nao_cadastradas': [],
        'possiveis_duplicatas': []
    }
    
    # Criar índices para busca rápida
    indice_cpf_cnpj = {}  # CPF/CNPJ -> pessoa
    indice_nome = {}       # nome_normalizado -> pessoa
    
    for pessoa in pessoas_cadastradas:
        cpf = pessoa.get('cpf_cnpj_normalizado')
        nome = pessoa.get('nome_normalizado')
        
        if cpf:
            indice_cpf_cnpj[cpf] = pessoa
        if nome:
            indice_nome[nome] = pessoa
    
    # Comparar cada pessoa do EPROC
    for pessoa_eproc in pessoas_eproc:
        cpf_eproc = pessoa_eproc.get('cpf_cnpj_normalizado')
        nome_eproc = pessoa_eproc.get('nome_normalizado')
        
        # 1. Primeiro tenta match por CPF/CNPJ (mais confiável)
        if cpf_eproc and cpf_eproc in indice_cpf_cnpj:
            pessoa_eproc['cadastrado'] = True
            pessoa_eproc['pessoa_similar_id'] = indice_cpf_cnpj[cpf_eproc].get('_id')
            pessoa_eproc['pessoa_similar_nome'] = indice_cpf_cnpj[cpf_eproc].get('nome_original')
            pessoa_eproc['similaridade'] = 1.0
            resultado['cadastradas'].append(pessoa_eproc)
            continue
        
        # 2. Tenta match exato por nome
        if nome_eproc and nome_eproc in indice_nome:
            pessoa_eproc['cadastrado'] = True
            pessoa_eproc['pessoa_similar_id'] = indice_nome[nome_eproc].get('_id')
            pessoa_eproc['pessoa_similar_nome'] = indice_nome[nome_eproc].get('nome_original')
            pessoa_eproc['similaridade'] = 1.0
            resultado['cadastradas'].append(pessoa_eproc)
            continue
        
        # 3. Busca por similaridade de nome
        melhor_match = None
        melhor_similaridade = 0.0
        
        for pessoa_cad in pessoas_cadastradas:
            nome_cad = pessoa_cad.get('nome_normalizado', '')
            if not nome_cad:
                continue
            
            similaridade = calcular_similaridade(nome_eproc, nome_cad)
            
            if similaridade > melhor_similaridade:
                melhor_similaridade = similaridade
                melhor_match = pessoa_cad
        
        # Classifica baseado na similaridade
        if melhor_similaridade >= 1.0:
            # Match exato
            pessoa_eproc['cadastrado'] = True
            pessoa_eproc['similaridade'] = melhor_similaridade
            pessoa_eproc['pessoa_similar_id'] = melhor_match.get('_id') if melhor_match else None
            pessoa_eproc['pessoa_similar_nome'] = melhor_match.get('nome_original') if melhor_match else None
            resultado['cadastradas'].append(pessoa_eproc)
        elif melhor_similaridade >= LIMIAR_DUPLICATA:
            # Possível duplicata (similaridade entre 90% e 100%)
            pessoa_eproc['cadastrado'] = False
            pessoa_eproc['similaridade'] = melhor_similaridade
            pessoa_eproc['pessoa_similar_id'] = melhor_match.get('_id') if melhor_match else None
            pessoa_eproc['pessoa_similar_nome'] = melhor_match.get('nome_original') if melhor_match else None
            resultado['possiveis_duplicatas'].append(pessoa_eproc)
        else:
            # Não cadastrada
            pessoa_eproc['cadastrado'] = False
            pessoa_eproc['similaridade'] = melhor_similaridade
            pessoa_eproc['pessoa_similar_id'] = melhor_match.get('_id') if melhor_match else None
            pessoa_eproc['pessoa_similar_nome'] = melhor_match.get('nome_original') if melhor_match else None
            resultado['nao_cadastradas'].append(pessoa_eproc)
    
    logger.info(
        f"[VALIDAÇÃO] Resultado: "
        f"{len(resultado['cadastradas'])} cadastradas, "
        f"{len(resultado['nao_cadastradas'])} não cadastradas, "
        f"{len(resultado['possiveis_duplicatas'])} possíveis duplicatas"
    )
    
    return resultado


def validar_pessoas_migracao(origem: str = 'gilberto') -> Dict[str, Any]:
    """
    Função principal que executa toda a validação de pessoas.
    
    Args:
        origem: 'gilberto' ou 'lenon'
        
    Returns:
        Dicionário com resultados completos da validação
    """
    inicio = datetime.now()
    
    try:
        # 1. Buscar pessoas cadastradas no Firebase
        pessoas_cadastradas = buscar_pessoas_cadastradas()
        
        # 2. Extrair pessoas do EPROC
        pessoas_eproc = extrair_pessoas_eproc(origem)
        
        # 3. Comparar
        resultado_comparacao = comparar_pessoas(pessoas_eproc, pessoas_cadastradas)
        
        # 4. Preparar resultado final
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()
        
        resultado = {
            'sucesso': True,
            'origem': origem,
            'data_validacao': inicio.isoformat(),
            'duracao_segundos': duracao,
            'total_eproc': len(pessoas_eproc),
            'total_firebase': len(pessoas_cadastradas),
            'cadastradas': resultado_comparacao['cadastradas'],
            'nao_cadastradas': resultado_comparacao['nao_cadastradas'],
            'possiveis_duplicatas': resultado_comparacao['possiveis_duplicatas'],
            'resumo': {
                'cadastradas': len(resultado_comparacao['cadastradas']),
                'nao_cadastradas': len(resultado_comparacao['nao_cadastradas']),
                'possiveis_duplicatas': len(resultado_comparacao['possiveis_duplicatas']),
            }
        }
        
        logger.info(f"[VALIDAÇÃO] Concluída em {duracao:.2f}s")
        return resultado
        
    except Exception as e:
        logger.error(f"[VALIDAÇÃO] Erro na validação: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'erro': str(e),
            'origem': origem,
            'data_validacao': inicio.isoformat(),
        }


# =============================================================================
# FUNÇÕES DE CADASTRO EM MASSA
# =============================================================================

def cadastrar_pessoas_em_massa(
    pessoas: List[Dict[str, Any]], 
    colecao: str = COLECAO_VG_ENVOLVIDOS,
    usuario_uid: str = None
) -> Dict[str, Any]:
    """
    Cadastra múltiplas pessoas no Firebase usando batch write.
    
    Args:
        pessoas: Lista de pessoas a cadastrar
        colecao: Nome da coleção de destino
        usuario_uid: UID do usuário que está executando
        
    Returns:
        Dicionário com resultados do cadastro
    """
    inicio = datetime.now()
    
    try:
        db = get_db()
        if not db:
            return {
                'sucesso': False,
                'erro': 'Conexão com Firebase não disponível',
                'cadastrados': 0,
                'erros': []
            }
        
        cadastrados = 0
        erros = []
        ids_criados = []
        
        # Firebase permite no máximo 500 operações por batch
        TAMANHO_LOTE = 500
        
        for i in range(0, len(pessoas), TAMANHO_LOTE):
            lote = pessoas[i:i + TAMANHO_LOTE]
            batch = db.batch()
            
            for pessoa in lote:
                try:
                    # Prepara dados para o Firebase
                    dados = {
                        'nome': pessoa.get('nome_original', ''),
                        'nome_normalizado': pessoa.get('nome_normalizado', ''),
                        'tipo_pessoa': pessoa.get('tipo_pessoa', 'PF'),
                        'tipo_envolvido': pessoa.get('tipo_pessoa', 'PF'),
                        'cpf_cnpj': pessoa.get('cpf_cnpj', ''),
                        'origem': 'migracao_eproc',
                        'papeis_processuais': list(pessoa.get('papeis', set())),
                        'processos_relacionados': list(pessoa.get('processos_relacionados', set())),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'criado_por': usuario_uid or 'sistema',
                    }
                    
                    # Cria referência para novo documento
                    doc_ref = db.collection(colecao).document()
                    batch.set(doc_ref, dados)
                    ids_criados.append(doc_ref.id)
                    cadastrados += 1
                    
                except Exception as e:
                    erros.append({
                        'nome': pessoa.get('nome_original', 'Desconhecido'),
                        'erro': str(e)
                    })
            
            # Commit do lote
            try:
                batch.commit()
                logger.info(f"[CADASTRO] Lote de {len(lote)} pessoas commitado")
            except Exception as e:
                logger.error(f"[CADASTRO] Erro ao commitar lote: {e}")
                # Reverte contagem
                cadastrados -= len(lote)
                for pessoa in lote:
                    erros.append({
                        'nome': pessoa.get('nome_original', 'Desconhecido'),
                        'erro': f'Erro no batch commit: {str(e)}'
                    })
        
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()
        
        # Registra log no Firebase
        _registrar_log_migracao(
            tipo='cadastro_em_massa',
            dados={
                'total_tentativas': len(pessoas),
                'cadastrados': cadastrados,
                'erros': len(erros),
                'colecao': colecao,
                'usuario': usuario_uid,
                'duracao_segundos': duracao,
                'ids_criados': ids_criados,
            }
        )
        
        return {
            'sucesso': True,
            'cadastrados': cadastrados,
            'erros': erros,
            'duracao_segundos': duracao,
            'ids_criados': ids_criados,
        }
        
    except Exception as e:
        logger.error(f"[CADASTRO] Erro no cadastro em massa: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'erro': str(e),
            'cadastrados': 0,
            'erros': [{'nome': 'Geral', 'erro': str(e)}]
        }


def _registrar_log_migracao(tipo: str, dados: Dict[str, Any]):
    """
    Registra log de operação no Firestore.
    
    Args:
        tipo: Tipo de operação ('validacao', 'cadastro_em_massa', etc.)
        dados: Dados a registrar
    """
    try:
        db = get_db()
        if not db:
            return
        
        log_data = {
            'tipo': tipo,
            'data_hora': datetime.now(),
            'dados': dados,
        }
        
        db.collection(COLECAO_LOGS_MIGRACAO).add(log_data)
        logger.info(f"[LOG] Registrado log de '{tipo}'")
        
    except Exception as e:
        logger.warning(f"[LOG] Erro ao registrar log: {e}")


# =============================================================================
# FUNÇÕES AUXILIARES PARA A UI
# =============================================================================

def preparar_pessoas_para_ui(pessoas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepara lista de pessoas para exibição na interface.
    Converte sets para listas e adiciona campos de exibição.
    
    Args:
        pessoas: Lista de pessoas da validação
        
    Returns:
        Lista formatada para UI
    """
    resultado = []
    
    for i, pessoa in enumerate(pessoas):
        # Converte sets para listas (JSON não suporta sets)
        processos = pessoa.get('processos_relacionados', set())
        if isinstance(processos, set):
            processos = list(processos)
        
        papeis = pessoa.get('papeis', set())
        if isinstance(papeis, set):
            papeis = list(papeis)
        
        resultado.append({
            'indice': i,
            'nome': pessoa.get('nome_original', ''),
            'cpf_cnpj': pessoa.get('cpf_cnpj', '') or '-',
            'tipo_pessoa': pessoa.get('tipo_pessoa', 'PF'),
            'tipo_label': 'Pessoa Jurídica' if pessoa.get('tipo_pessoa') == 'PJ' else 'Pessoa Física',
            'papeis': papeis,
            'papeis_label': ', '.join(p.capitalize() for p in papeis),
            'processos_relacionados': processos,
            'qtd_processos': len(processos),
            'similaridade': pessoa.get('similaridade'),
            'similaridade_pct': f"{(pessoa.get('similaridade') or 0) * 100:.0f}%" if pessoa.get('similaridade') else '-',
            'pessoa_similar_nome': pessoa.get('pessoa_similar_nome', ''),
            'selecionado': False,
            '_dados_originais': pessoa,  # Mantém dados originais para cadastro
        })
    
    # Ordena por nome
    resultado.sort(key=lambda x: x['nome'].upper())
    
    return resultado






