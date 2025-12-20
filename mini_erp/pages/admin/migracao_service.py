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
CAMINHO_PLANILHA = "/Users/lenontaques/Documents/taques-erp/relatorio-processos-2025-lenon.xls"

def importar_planilha_migracao() -> Dict[str, Any]:
    """
    Lê a planilha Excel e importa os dados para a coleção processos_migracao.
    """
    try:
        if not os.path.exists(CAMINHO_PLANILHA):
            return {"sucesso": False, "erro": f"Planilha não encontrada em: {CAMINHO_PLANILHA}"}

        # Lê planilha usando pandas com xlrd para .xls
        # skiprows=1 para pular o cabeçalho se necessário (conforme requisito)
        df = pd.read_excel(CAMINHO_PLANILHA, skiprows=1, engine='xlrd')
        
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
                
                # Verifica se já existe na migração
                docs = db.collection(COLECAO_MIGRACAO).where("numero_processo", "==", numero).limit(1).stream()
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
                    
                    # Campos fixos
                    "sistema_processual": "eproc - TJSC - 1ª instância",
                    "estado": "Santa Catarina",
                    "responsavel": "Lenon Taques",
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

def obter_estatisticas_migracao() -> Dict[str, Any]:
    """Retorna contadores de progresso da migração."""
    try:
        db = get_db()
        docs = list(db.collection(COLECAO_MIGRACAO).stream())
        
        total = len(docs)
        pendentes = sum(1 for d in docs if d.to_dict().get("status_migracao") == "pendente")
        concluidos = total - pendentes
        
        return {
            "total": total,
            "pendentes": pendentes,
            "concluidos": concluidos,
            "progresso": (concluidos / total * 100) if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return {"total": 0, "pendentes": 0, "concluidos": 0, "progresso": 0}

def listar_processos_migracao(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista processos da coleção de migração."""
    try:
        db = get_db()
        query = db.collection(COLECAO_MIGRACAO)
        
        if status and status != "todos":
            query = query.where("status_migracao", "==", status)
            
        docs = query.stream()
        lista = []
        for doc in docs:
            d = doc.to_dict()
            d["_id"] = doc.id
            lista.append(d)
        
        # Ordena: pendentes primeiro
        lista.sort(key=lambda x: (x.get("status_migracao") != "pendente", x.get("numero_processo")))
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

def finalizar_migracao_completa() -> Dict[str, Any]:
    """Finaliza todo o processo de migração após todos os itens serem concluídos."""
    try:
        db = get_db()
        docs = list(db.collection(COLECAO_MIGRACAO).where("status_migracao", "==", "pendente").limit(1).stream())
        
        if docs:
            return {"sucesso": False, "erro": "Ainda existem processos pendentes de preenchimento."}
        
        # Aqui poderíamos mover para um histórico ou apenas marcar como finalizado em um config
        # Para este requisito, vamos apenas confirmar que todos estão ok
        return {"sucesso": True, "mensagem": "Migração finalizada com sucesso!"}
    except Exception as e:
        logger.error(f"Erro ao finalizar migração: {e}")
        return {"sucesso": False, "erro": str(e)}

