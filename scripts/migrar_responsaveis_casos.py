#!/usr/bin/env python3
"""
Script de migração para corrigir IDs de responsáveis nos casos.
Substitui IDs antigos (lenon_taques, gilberto_taques) pelos UIDs corretos do Firebase Auth.
"""
import sys
import os
import argparse
from typing import Dict, List, Any

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db, ensure_firebase_initialized, get_auth

COLECAO_CASOS = 'vg_casos'


def listar_usuarios_firebase():
    """Lista todos os usuários do Firebase Authentication."""
    ensure_firebase_initialized()
    auth_instance = get_auth()
    usuarios = []
    
    try:
        page = auth_instance.list_users()
        while page:
            for user in page.users:
                usuarios.append({
                    '_id': user.uid,
                    'display_name': user.display_name or '',
                    'email': user.email or '',
                    'name': user.display_name or (user.email.split('@')[0] if user.email else 'Sem nome'),
                })
            try:
                page = page.get_next_page()
            except:
                break
    except Exception as e:
        print(f"Erro ao buscar usuários: {e}")
    
    return usuarios


def criar_mapeamento_ids(usuarios_firebase: List[Dict]) -> Dict[str, str]:
    """
    Cria mapeamento de IDs antigos para novos baseado nos emails.
    
    Args:
        usuarios_firebase: Lista de usuários do Firebase Auth
    
    Returns:
        Dicionário mapeando ID antigo -> UID novo
    """
    mapeamento = {}
    
    # Mapeia por email (mais confiável)
    for usuario in usuarios_firebase:
        email = usuario.get('email', '').lower()
        uid = usuario.get('_id', '')
        name = usuario.get('name', '')
        
        if 'taqueslenon' in email or 'lenon' in name.lower():
            mapeamento['lenon_taques'] = uid
            print(f"✅ Mapeamento: lenon_taques -> {uid} ({name})")
        
        if 'taquesgiba' in email or 'gilberto' in name.lower():
            mapeamento['gilberto_taques'] = uid
            print(f"✅ Mapeamento: gilberto_taques -> {uid} ({name})")
    
    return mapeamento


def migrar_responsaveis(dry_run: bool = True):
    """
    Migra os IDs de responsáveis nos casos.
    
    Args:
        dry_run: Se True, apenas mostra o que seria alterado sem salvar
    """
    db = get_db()
    if not db:
        print("❌ Erro: Conexão com Firebase não disponível")
        return
    
    # Busca usuários do Firebase Auth
    print(f"\n{'='*80}")
    print(f"MIGRAÇÃO DE IDs DE RESPONSÁVEIS - CASOS")
    print(f"{'='*80}\n")
    print("📋 Buscando usuários do Firebase Auth...")
    
    usuarios_firebase = listar_usuarios_firebase()
    mapa_usuarios = {u['_id']: u for u in usuarios_firebase}
    
    print(f"✅ {len(usuarios_firebase)} usuários encontrados\n")
    
    # Cria mapeamento de IDs antigos para novos
    print("🔍 Criando mapeamento de IDs...")
    mapeamento_ids = criar_mapeamento_ids(usuarios_firebase)
    
    if not mapeamento_ids:
        print("❌ Erro: Não foi possível criar mapeamento de IDs")
        return
    
    print(f"\n✅ Mapeamento criado: {len(mapeamento_ids)} IDs mapeados\n")
    
    # Busca todos os casos
    print("📋 Buscando casos...")
    docs = db.collection(COLECAO_CASOS).stream()
    casos = []
    
    for doc in docs:
        caso = doc.to_dict()
        caso['_id'] = doc.id
        casos.append(caso)
    
    print(f"✅ {len(casos)} casos encontrados\n")
    
    # Estatísticas
    stats = {
        'total_casos': len(casos),
        'casos_atualizados': 0,
        'ids_substituidos': 0,
        'casos_sem_mudancas': 0,
        'erros': 0,
    }
    
    # Lista de alterações
    alteracoes = []
    
    # Processa cada caso
    print(f"{'='*80}")
    print(f"PROCESSANDO CASOS...")
    print(f"{'='*80}\n")
    
    for caso in casos:
        caso_id = caso.get('_id', 'N/A')
        titulo = caso.get('titulo', 'Sem título')[:50]
        responsaveis = caso.get('responsaveis', [])
        responsaveis_dados = caso.get('responsaveis_dados', [])
        
        # Verifica se precisa atualizar
        precisa_atualizar = False
        novos_responsaveis = []
        novos_responsaveis_dados = []
        ids_substituidos_caso = 0
        
        if isinstance(responsaveis, list):
            for resp_id in responsaveis:
                if resp_id in mapeamento_ids:
                    # ID antigo encontrado, substitui pelo novo
                    novo_id = mapeamento_ids[resp_id]
                    novos_responsaveis.append(novo_id)
                    precisa_atualizar = True
                    ids_substituidos_caso += 1
                    
                    # Busca dados do usuário no Firebase Auth
                    usuario = mapa_usuarios.get(novo_id, {})
                    novos_responsaveis_dados.append({
                        'usuario_id': novo_id,
                        'nome': usuario.get('display_name') or usuario.get('name', ''),
                        'email': usuario.get('email', ''),
                    })
                else:
                    # ID não está no mapeamento, mantém como está
                    novos_responsaveis.append(resp_id)
                    
                    # Tenta encontrar dados existentes ou busca no Firebase Auth
                    if isinstance(responsaveis_dados, list):
                        dados_existentes = next(
                            (r for r in responsaveis_dados if r.get('usuario_id') == resp_id),
                            None
                        )
                        if dados_existentes:
                            novos_responsaveis_dados.append(dados_existentes)
                        else:
                            # Busca no Firebase Auth
                            usuario = mapa_usuarios.get(resp_id, {})
                            if usuario:
                                novos_responsaveis_dados.append({
                                    'usuario_id': resp_id,
                                    'nome': usuario.get('display_name') or usuario.get('name', ''),
                                    'email': usuario.get('email', ''),
                                })
        
        if precisa_atualizar:
            alteracao = {
                'caso_id': caso_id,
                'titulo': titulo,
                'responsaveis_antigos': responsaveis,
                'responsaveis_novos': novos_responsaveis,
                'responsaveis_dados_antigos': responsaveis_dados,
                'responsaveis_dados_novos': novos_responsaveis_dados,
                'ids_substituidos': ids_substituidos_caso,
            }
            alteracoes.append(alteracao)
            stats['casos_atualizados'] += 1
            stats['ids_substituidos'] += ids_substituidos_caso
            
            if not dry_run:
                try:
                    # Atualiza o caso no Firestore
                    db.collection(COLECAO_CASOS).document(caso_id).update({
                        'responsaveis': novos_responsaveis,
                        'responsaveis_dados': novos_responsaveis_dados,
                    })
                    print(f"✅ Caso atualizado: {titulo} (IDs substituídos: {ids_substituidos_caso})")
                except Exception as e:
                    print(f"❌ Erro ao atualizar caso {caso_id}: {e}")
                    stats['erros'] += 1
            else:
                print(f"📝 [DRY-RUN] Caso seria atualizado: {titulo} (IDs substituídos: {ids_substituidos_caso})")
        else:
            stats['casos_sem_mudancas'] += 1
    
    # Relatório final
    print(f"\n{'='*80}")
    print(f"RELATÓRIO DE MIGRAÇÃO")
    print(f"{'='*80}\n")
    
    if dry_run:
        print("⚠️  MODO DRY-RUN: Nenhuma alteração foi salva\n")
    
    print(f"📊 Total de casos processados: {stats['total_casos']}")
    print(f"✅ Casos que serão atualizados: {stats['casos_atualizados']}")
    print(f"📋 IDs substituídos: {stats['ids_substituidos']}")
    print(f"➡️  Casos sem mudanças: {stats['casos_sem_mudancas']}")
    print(f"❌ Erros: {stats['erros']}")
    
    if alteracoes and dry_run:
        print(f"\n{'='*80}")
        print(f"PRÉVIA DAS ALTERAÇÕES (primeiros 10 casos)")
        print(f"{'='*80}\n")
        
        for alt in alteracoes[:10]:
            print(f"\n📄 Caso: {alt['titulo']}")
            print(f"   IDs antigos: {alt['responsaveis_antigos']}")
            print(f"   IDs novos: {alt['responsaveis_novos']}")
            print(f"   IDs substituídos: {alt['ids_substituidos']}")
    
    if not dry_run:
        print(f"\n✅ Migração concluída com sucesso!")
    else:
        print(f"\n💡 Para executar a migração, use: python3 scripts/migrar_responsaveis_casos.py --executar")
    
    print(f"{'='*80}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migra IDs de responsáveis nos casos')
    parser.add_argument(
        '--executar',
        action='store_true',
        help='Executa a migração (sem este flag, apenas mostra o que seria alterado)'
    )
    
    args = parser.parse_args()
    
    try:
        migrar_responsaveis(dry_run=not args.executar)
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()












