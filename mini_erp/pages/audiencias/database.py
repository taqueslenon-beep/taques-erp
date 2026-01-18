"""
Funções de acesso ao banco de dados para o módulo de Audiências.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ...firebase_config import get_db


def listar_audiencias() -> List[Dict[str, Any]]:
    """
    Lista todas as audiências ordenadas por data.
    
    Returns:
        Lista de audiências
    """
    try:
        db = get_db()
        docs = db.collection('audiencias').stream()
        audiencias = []
        for doc in docs:
            audiencia = doc.to_dict()
            audiencia['_id'] = doc.id
            audiencias.append(audiencia)
        
        # Ordenar por data_hora (mais recentes primeiro)
        audiencias.sort(key=lambda x: x.get('data_hora', 0), reverse=True)
        
        return audiencias
    except Exception as e:
        print(f"[ERROR] Erro ao listar audiências: {e}")
        return []


def buscar_audiencia_por_id(audiencia_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma audiência por ID.
    
    Args:
        audiencia_id: ID da audiência
    
    Returns:
        Dicionário com dados da audiência ou None
    """
    try:
        db = get_db()
        doc_ref = db.collection('audiencias').document(audiencia_id)
        doc = doc_ref.get()
        if doc.exists:
            audiencia = doc.to_dict()
            audiencia['_id'] = doc.id
            return audiencia
        return None
    except Exception as e:
        print(f"[ERROR] Erro ao buscar audiência: {e}")
        return None


def criar_audiencia(dados: Dict[str, Any]) -> Optional[str]:
    """
    Cria uma nova audiência.
    
    Args:
        dados: Dados da audiência
    
    Returns:
        ID da audiência criada ou None em caso de erro
    """
    try:
        db = get_db()
        
        # Adiciona timestamp de criação
        dados['criado_em'] = datetime.now().timestamp()
        dados['atualizado_em'] = datetime.now().timestamp()
        
        doc_ref = db.collection('audiencias').document()
        doc_ref.set(dados)
        return doc_ref.id
    except Exception as e:
        print(f"[ERROR] Erro ao criar audiência: {e}")
        return None


def atualizar_audiencia(audiencia_id: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza uma audiência existente.
    
    Args:
        audiencia_id: ID da audiência
        dados: Dados a atualizar
    
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    try:
        db = get_db()
        
        # Adiciona timestamp de atualização
        dados['atualizado_em'] = datetime.now().timestamp()
        
        doc_ref = db.collection('audiencias').document(audiencia_id)
        doc_ref.update(dados)
        return True
    except Exception as e:
        print(f"[ERROR] Erro ao atualizar audiência: {e}")
        return False


def excluir_audiencia(audiencia_id: str) -> bool:
    """
    Exclui uma audiência.
    
    Args:
        audiencia_id: ID da audiência
    
    Returns:
        True se excluído com sucesso, False caso contrário
    """
    try:
        db = get_db()
        doc_ref = db.collection('audiencias').document(audiencia_id)
        doc_ref.delete()
        return True
    except Exception as e:
        print(f"[ERROR] Erro ao excluir audiência: {e}")
        return False


def buscar_processos_para_select() -> Dict[str, str]:
    """
    Busca processos para popular select.
    
    Returns:
        Dicionário {id: nome_processo}
    """
    try:
        db = get_db()
        docs = db.collection('processes').stream()
        
        resultado = {}
        for doc in docs:
            proc = doc.to_dict()
            proc_id = doc.id
            numero = proc.get('numero_processo', '')
            titulo = proc.get('titulo', '')
            label = f"{numero} - {titulo}" if numero and titulo else numero or titulo or proc_id
            resultado[proc_id] = label
        
        return resultado
    except Exception as e:
        print(f"[ERROR] Erro ao buscar processos: {e}")
        return {}


def buscar_usuarios_para_select() -> Dict[str, str]:
    """
    Busca usuários para popular select de Responsável.
    Retorna apenas Lenon Taques e Gilberto Taques.
    
    Returns:
        Dicionário {id: nome_usuario}
    """
    try:
        db = get_db()
        
        # Buscar todos os usuários do sistema
        docs = db.collection('usuarios_sistema').stream()
        
        resultado = {}
        
        print("[DEBUG] Buscando usuários para audiências...")
        
        # Processar todos os usuários
        for doc in docs:
            usuario = doc.to_dict()
            usuario_id = doc.id
            nome = usuario.get('nome', '')
            email = usuario.get('email', '')
            
            print(f"[DEBUG] Usuário encontrado: nome='{nome}', email='{email}', ID={usuario_id}")
            
            # Normalizar para comparação
            nome_lower = nome.lower() if nome else ''
            email_lower = email.lower() if email else ''
            busca_completa = f"{nome_lower} {email_lower}"
            
            # Identificar Lenon Taques
            if 'lenon' in busca_completa and ('taques' in busca_completa or 'taqueslenon' in email_lower):
                # SEMPRE usar "Lenon Taques" como label
                resultado[usuario_id] = 'Lenon Taques'
                print(f"[DEBUG] ✓ Lenon Taques identificado e adicionado (nome original: '{nome}')")
            
            # Identificar Gilberto Taques
            elif ('gilberto' in busca_completa or 'giba' in busca_completa) and ('taques' in busca_completa or 'taquesgiba' in email_lower):
                # SEMPRE usar "Gilberto Taques" como label
                resultado[usuario_id] = 'Gilberto Taques'
                print(f"[DEBUG] ✓ Gilberto Taques identificado e adicionado (nome original: '{nome}')")
        
        print(f"[DEBUG] Total de usuários filtrados: {len(resultado)}")
        print(f"[DEBUG] Resultado final: {resultado}")
        
        # Se não encontrou nenhum usuário, adiciona opções fixas
        if not resultado:
            print("[WARNING] Nenhum usuário encontrado no Firebase. Adicionando opções de fallback.")
            resultado = {
                'lenon_taques': 'Lenon Taques',
                'gilberto_taques': 'Gilberto Taques'
            }
        
        return resultado
    except Exception as e:
        print(f"[ERROR] Erro ao buscar usuários: {e}")
        import traceback
        traceback.print_exc()
        # Retorna opções de fallback em caso de erro
        return {
            'lenon_taques': 'Lenon Taques',
            'gilberto_taques': 'Gilberto Taques'
        }


def buscar_clientes_para_select() -> Dict[str, str]:
    """
    Busca clientes para popular select.
    Busca da coleção vg_pessoas (módulo Pessoas de Visão Geral).
    
    Returns:
        Dicionário {id: nome_cliente}
    """
    try:
        db = get_db()
        docs = db.collection('vg_pessoas').where('categoria', '==', 'cliente').stream()
        
        resultado = {}
        for doc in docs:
            cliente = doc.to_dict()
            cliente_id = doc.id
            # Prioriza nome_exibicao, depois full_name, depois nome
            nome = cliente.get('nome_exibicao') or cliente.get('full_name') or cliente.get('nome') or cliente_id
            resultado[cliente_id] = nome
        
        return resultado
    except Exception as e:
        print(f"[ERROR] Erro ao buscar clientes: {e}")
        return {}
