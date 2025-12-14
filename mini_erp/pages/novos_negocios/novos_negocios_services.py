"""
Serviços e lógica de negócio para Novos Negócios.
Gerencia CRUD de oportunidades no Firebase.
"""
from typing import List, Dict, Any, Optional
import time
from mini_erp.firebase_config import get_db, ensure_firebase_initialized, get_auth
from mini_erp.core import invalidate_cache
from mini_erp.storage import obter_display_name


# Nome da coleção no Firestore
COLLECTION_NAME = 'oportunidades'


def get_oportunidades() -> List[Dict[str, Any]]:
    """
    Busca todas as oportunidades do Firestore.
    
    Returns:
        Lista de oportunidades com seus dados
    """
    try:
        db = get_db()
        docs = db.collection(COLLECTION_NAME).stream()
        oportunidades = []
        for doc in docs:
            oportunidade = doc.to_dict()
            oportunidade['_id'] = doc.id
            oportunidades.append(oportunidade)
        return oportunidades
    except Exception as e:
        print(f"Erro ao buscar oportunidades: {e}")
        return []


def get_oportunidades_por_status(status: str) -> List[Dict[str, Any]]:
    """
    Busca oportunidades filtradas por status.
    
    Args:
        status: Status da coluna (agir, em_andamento, aguardando, monitorando, concluido)
    
    Returns:
        Lista de oportunidades com o status especificado
    """
    try:
        db = get_db()
        query = db.collection(COLLECTION_NAME).where('status', '==', status)
        docs = query.stream()
        oportunidades = []
        for doc in docs:
            oportunidade = doc.to_dict()
            oportunidade['_id'] = doc.id
            oportunidades.append(oportunidade)
        
        # Ordena por ordem (se existir)
        oportunidades.sort(key=lambda x: x.get('ordem', 999))
        return oportunidades
    except Exception as e:
        print(f"Erro ao buscar oportunidades por status: {e}")
        return []


def save_oportunidade(data: Dict[str, Any], oportunidade_id: Optional[str] = None) -> str:
    """
    Salva ou atualiza uma oportunidade no Firestore.
    
    Args:
        data: Dicionário com dados da oportunidade
        oportunidade_id: ID do documento para atualização (None para criar novo)
    
    Returns:
        ID do documento no Firestore
    """
    try:
        db = get_db()
        
        # Remove _id dos dados (é metadado)
        oportunidade_para_salvar = {k: v for k, v in data.items() if k != '_id'}
        
        # Adiciona timestamps
        agora = time.time()
        if oportunidade_id:
            # UPDATE: Atualizar oportunidade existente
            oportunidade_para_salvar['data_atualizacao'] = agora
            db.collection(COLLECTION_NAME).document(oportunidade_id).update(oportunidade_para_salvar)
            doc_id = oportunidade_id
        else:
            # CREATE: Criar nova oportunidade
            oportunidade_para_salvar['data_criacao'] = agora
            oportunidade_para_salvar['data_atualizacao'] = agora
            
            # Garante que tem status padrão
            if 'status' not in oportunidade_para_salvar:
                oportunidade_para_salvar['status'] = 'agir'
            
            # Salva no Firestore
            doc_ref = db.collection(COLLECTION_NAME).add(oportunidade_para_salvar)
            doc_id = doc_ref[1].id
        
        # Invalida cache
        invalidate_cache(COLLECTION_NAME)
        
        return doc_id
    except Exception as e:
        print(f"Erro ao salvar oportunidade: {e}")
        raise


def update_status_oportunidade(oportunidade_id: str, novo_status: str) -> bool:
    """
    Atualiza o status de uma oportunidade (mover entre colunas).
    
    Args:
        oportunidade_id: ID da oportunidade
        novo_status: Novo status (agir, em_andamento, aguardando, monitorando, concluido)
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        db = get_db()
        db.collection(COLLECTION_NAME).document(oportunidade_id).update({
            'status': novo_status,
            'data_atualizacao': time.time()
        })
        
        # Invalida cache
        invalidate_cache(COLLECTION_NAME)
        
        return True
    except Exception as e:
        print(f"Erro ao atualizar status da oportunidade: {e}")
        return False


def delete_oportunidade(oportunidade_id: str) -> bool:
    """
    Remove uma oportunidade do Firestore.
    
    Args:
        oportunidade_id: ID da oportunidade a ser removida
    
    Returns:
        True se removido com sucesso, False caso contrário
    """
    try:
        db = get_db()
        db.collection(COLLECTION_NAME).document(oportunidade_id).delete()
        
        # Invalida cache
        invalidate_cache(COLLECTION_NAME)
        
        return True
    except Exception as e:
        print(f"Erro ao deletar oportunidade: {e}")
        return False


def buscar_oportunidade_por_id(oportunidade_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma oportunidade específica por ID.
    
    Args:
        oportunidade_id: ID da oportunidade
    
    Returns:
        Dados da oportunidade ou None se não encontrada
    """
    try:
        db = get_db()
        doc = db.collection(COLLECTION_NAME).document(oportunidade_id).get()
        if doc.exists:
            oportunidade = doc.to_dict()
            oportunidade['_id'] = doc.id
            return oportunidade
        return None
    except Exception as e:
        print(f"Erro ao buscar oportunidade por ID: {e}")
        return None


def get_usuarios_ativos_firebase() -> List[Dict[str, Any]]:
    """
    Busca usuários ativos do Firebase Auth para uso em dropdowns.
    
    Returns:
        Lista de usuários ativos com:
        - uid: ID do Firebase Auth
        - nome: Nome de exibição (display_name)
        - email: Email do usuário
    """
    try:
        ensure_firebase_initialized()
        auth_instance = get_auth()
        usuarios = []
        page = auth_instance.list_users()
        
        while page:
            for user in page.users:
                # Filtra apenas usuários ativos (não desabilitados)
                if user.disabled:
                    continue
                
                # Obtém nome de exibição
                try:
                    display_name = obter_display_name(user.uid)
                    # Se retornou "Usuário" (fallback padrão), usa parte do email
                    if display_name == "Usuário":
                        display_name = user.email.split('@')[0] if user.email else 'Sem nome'
                except Exception:
                    # Fallback: usa display_name do Firebase ou parte do email
                    display_name = user.display_name or (user.email.split('@')[0] if user.email else 'Sem nome')
                
                usuarios.append({
                    'uid': user.uid,
                    'nome': display_name,
                    'email': user.email or ''
                })
            
            try:
                page = page.get_next_page()
            except (StopIteration, Exception):
                break
        
        # Ordena alfabeticamente por nome
        usuarios.sort(key=lambda x: x['nome'].lower())
        
        return usuarios
    except Exception as e:
        print(f"[NOVOS_NEGOCIOS] Erro ao buscar usuários do Firebase Auth: {e}")
        return []


def obter_estatisticas_detalhadas() -> Dict[str, Any]:
    """
    Retorna estatísticas detalhadas das oportunidades para dashboard.
    
    Returns:
        Dicionário com estatísticas agrupadas por status, núcleo, mês, origem e responsável
    """
    try:
        oportunidades = get_oportunidades()
        
        # Filtra apenas não concluídas
        ativas = [op for op in oportunidades if op.get('status') != 'concluido']
        
        # Por status
        por_status = {}
        for status in ['agir', 'em_andamento', 'aguardando', 'monitorando']:
            por_status[status] = len([op for op in ativas if op.get('status') == status])
        
        # Por núcleo
        por_nucleo = {}
        for op in ativas:
            nucleo = op.get('nucleo', 'Generalista')
            por_nucleo[nucleo] = por_nucleo.get(nucleo, 0) + 1
        
        # Por mês (usando entrada_lead ou data_criacao)
        por_mes = {}
        for op in ativas:
            # Prioriza entrada_lead (formato "MM/AAAA"), fallback para data_criacao
            entrada = op.get('entrada_lead', '')
            if not entrada:
                data_criacao = op.get('data_criacao')
                if data_criacao:
                    try:
                        from datetime import datetime
                        if isinstance(data_criacao, (int, float)):
                            dt = datetime.fromtimestamp(data_criacao)
                            entrada = f"{dt.month:02d}/{dt.year}"
                    except:
                        pass
            
            if entrada:
                por_mes[entrada] = por_mes.get(entrada, 0) + 1
        
        # Por origem
        por_origem = {}
        for op in ativas:
            origem = op.get('origem', 'Não informado')
            if not origem or origem.strip() == '':
                origem = 'Não informado'
            por_origem[origem] = por_origem.get(origem, 0) + 1
        
        # Por responsável
        por_responsavel = {}
        for op in ativas:
            responsaveis = op.get('responsavel', []) or op.get('responsaveis', [])
            if isinstance(responsaveis, str):
                responsaveis = [responsaveis]
            elif not isinstance(responsaveis, list):
                responsaveis = []
            
            for resp in responsaveis:
                if resp and str(resp).strip():
                    resp_clean = str(resp).strip()
                    por_responsavel[resp_clean] = por_responsavel.get(resp_clean, 0) + 1
        
        # Valores por status (soma dos valores estimados)
        valores_por_status = {
            'agir': 0.0,
            'em_andamento': 0.0,
            'aguardando': 0.0,
            'monitorando': 0.0
        }
        
        for op in ativas:
            status = op.get('status', 'agir')
            if status in valores_por_status:
                valor = op.get('valor_estimado', 0) or 0
                if isinstance(valor, str):
                    try:
                        # Remove formatação se for string
                        valor_limpo = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
                        valor = float(valor_limpo) if valor_limpo else 0.0
                    except:
                        valor = 0.0
                valores_por_status[status] += float(valor) if valor else 0.0
        
        return {
            'total': len(ativas),
            'por_status': por_status,
            'por_nucleo': por_nucleo,
            'por_mes': por_mes,
            'por_origem': por_origem,
            'por_responsavel': por_responsavel,
            'valores_por_status': valores_por_status
        }
    except Exception as e:
        print(f"[NOVOS_NEGOCIOS] Erro ao obter estatísticas detalhadas: {e}")
        import traceback
        traceback.print_exc()
        return {
            'total': 0,
            'por_status': {},
            'por_nucleo': {},
            'por_mes': {},
            'por_origem': {},
            'por_responsavel': {},
            'valores_por_status': {
                'agir': 0.0,
                'em_andamento': 0.0,
                'aguardando': 0.0,
                'monitorando': 0.0
            }
        }
