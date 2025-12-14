#!/usr/bin/env python3
"""
Script de investigação dos dados de responsáveis nos casos.
Analisa a estrutura e inconsistências nos campos 'responsaveis' e 'responsaveis_dados'.
"""
import sys
import os
from collections import defaultdict
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


def investigar_casos():
    """Investiga a estrutura dos dados de responsáveis nos casos."""
    db = get_db()
    if not db:
        print("❌ Erro: Conexão com Firebase não disponível")
        return
    
    # Busca todos os casos
    docs = db.collection(COLECAO_CASOS).stream()
    casos = []
    
    for doc in docs:
        caso = doc.to_dict()
        caso['_id'] = doc.id
        casos.append(caso)
    
    print(f"\n{'='*80}")
    print(f"INVESTIGAÇÃO DE DADOS DE RESPONSÁVEIS - CASOS")
    print(f"{'='*80}")
    print(f"\n📊 Total de casos encontrados: {len(casos)}\n")
    
    # Estatísticas gerais (para TODOS os casos)
    stats = {
        'tem_responsaveis': 0,
        'tem_responsaveis_dados': 0,
        'tem_ambos': 0,
        'tem_nenhum': 0,
        'responsaveis_eh_array': 0,
        'responsaveis_eh_string': 0,
        'responsaveis_eh_lista_vazia': 0,
        'responsaveis_dados_eh_lista_vazia': 0,
        'responsaveis_com_ids_validos': 0,
        'responsaveis_com_nomes': 0,
        'responsaveis_com_ids_invalidos': 0,
    }
    
    # Análise detalhada
    casos_analisados = []
    usuarios_firebase = listar_usuarios_firebase()
    mapa_usuarios = {u['_id']: u for u in usuarios_firebase}
    
    print(f"📋 Usuários encontrados no Firebase Auth: {len(usuarios_firebase)}")
    for u in usuarios_firebase:
        print(f"   - {u['name']} ({u['email']}) - ID: {u['_id'][:20]}...")
    print()
    
    # Analisa TODOS os casos para estatísticas
    for caso in casos:
        responsaveis = caso.get('responsaveis', None)
        responsaveis_dados = caso.get('responsaveis_dados', None)
        
        # Estatísticas
        if responsaveis is not None:
            stats['tem_responsaveis'] += 1
            if isinstance(responsaveis, list):
                stats['responsaveis_eh_array'] += 1
                if len(responsaveis) == 0:
                    stats['responsaveis_eh_lista_vazia'] += 1
                else:
                    # Verifica se são IDs ou nomes
                    for item in responsaveis:
                        if isinstance(item, str):
                            if len(item) < 30 and ' ' in item:
                                stats['responsaveis_com_nomes'] += 1
                            elif item in mapa_usuarios:
                                stats['responsaveis_com_ids_validos'] += 1
                            else:
                                stats['responsaveis_com_ids_invalidos'] += 1
            elif isinstance(responsaveis, str):
                stats['responsaveis_eh_string'] += 1
        
        if responsaveis_dados is not None:
            stats['tem_responsaveis_dados'] += 1
            if isinstance(responsaveis_dados, list) and len(responsaveis_dados) == 0:
                stats['responsaveis_dados_eh_lista_vazia'] += 1
        
        if responsaveis is not None and responsaveis_dados is not None:
            stats['tem_ambos'] += 1
        
        if responsaveis is None and responsaveis_dados is None:
            stats['tem_nenhum'] += 1
    
    # Análise detalhada dos primeiros 20 casos
    for caso in casos[:20]:
        caso_id = caso.get('_id', 'N/A')
        titulo = caso.get('titulo', 'Sem título')[:50]
        
        responsaveis = caso.get('responsaveis', None)
        responsaveis_dados = caso.get('responsaveis_dados', None)
        
        # Análise detalhada do caso
        analise = {
            'caso_id': caso_id,
            'titulo': titulo,
            'responsaveis': responsaveis,
            'responsaveis_tipo': type(responsaveis).__name__ if responsaveis is not None else 'None',
            'responsaveis_dados': responsaveis_dados,
            'responsaveis_dados_tipo': type(responsaveis_dados).__name__ if responsaveis_dados is not None else 'None',
            'problemas': [],
        }
        
        # Verifica problemas
        if isinstance(responsaveis, list) and len(responsaveis) > 0:
            # Verifica se são IDs ou nomes
            for item in responsaveis:
                if isinstance(item, str):
                    # Verifica se é ID (geralmente longo) ou nome
                    if len(item) < 30 and ' ' in item:
                        analise['problemas'].append(f"⚠️  'responsaveis' contém NOMES em vez de IDs: {item}")
                    elif item not in mapa_usuarios:
                        analise['problemas'].append(f"⚠️  ID não encontrado no Firebase Auth: {item[:30]}...")
        
        if responsaveis_dados is not None:
            if isinstance(responsaveis_dados, list) and len(responsaveis_dados) > 0:
                for r in responsaveis_dados:
                    if not isinstance(r, dict):
                        analise['problemas'].append(f"⚠️  Item em 'responsaveis_dados' não é dicionário: {r}")
                    else:
                        usuario_id = r.get('usuario_id')
                        nome = r.get('nome', '')
                        if usuario_id and usuario_id not in mapa_usuarios:
                            analise['problemas'].append(f"⚠️  usuario_id não encontrado no Firebase Auth: {usuario_id[:30]}...")
                        elif not nome:
                            analise['problemas'].append(f"⚠️  Campo 'nome' vazio em responsaveis_dados para ID: {usuario_id[:30]}...")
        
        # Verifica inconsistência: tem IDs mas não tem dados
        if isinstance(responsaveis, list) and len(responsaveis) > 0:
            if not responsaveis_dados or (isinstance(responsaveis_dados, list) and len(responsaveis_dados) == 0):
                analise['problemas'].append("⚠️  Tem IDs em 'responsaveis' mas 'responsaveis_dados' está vazio")
        
        # Verifica inconsistência: tem dados mas não tem IDs
        if responsaveis_dados and isinstance(responsaveis_dados, list) and len(responsaveis_dados) > 0:
            if not responsaveis or (isinstance(responsaveis, list) and len(responsaveis) == 0):
                analise['problemas'].append("⚠️  Tem dados em 'responsaveis_dados' mas 'responsaveis' está vazio")
        
        casos_analisados.append(analise)
    
    # Imprime estatísticas
    print(f"\n{'='*80}")
    print(f"ESTATÍSTICAS GERAIS (todos os {len(casos)} casos)")
    print(f"{'='*80}")
    print(f"✅ Casos com campo 'responsaveis': {stats['tem_responsaveis']}")
    print(f"✅ Casos com campo 'responsaveis_dados': {stats['tem_responsaveis_dados']}")
    print(f"✅ Casos com AMBOS os campos: {stats['tem_ambos']}")
    print(f"❌ Casos SEM nenhum dos dois: {stats['tem_nenhum']}")
    print(f"\n📋 Detalhes do campo 'responsaveis':")
    print(f"   - É array: {stats['responsaveis_eh_array']}")
    print(f"   - É string: {stats['responsaveis_eh_string']}")
    print(f"   - Array vazio: {stats['responsaveis_eh_lista_vazia']}")
    print(f"   - Contém IDs válidos: {stats['responsaveis_com_ids_validos']}")
    print(f"   - Contém nomes (erro): {stats['responsaveis_com_nomes']}")
    print(f"   - Contém IDs inválidos: {stats['responsaveis_com_ids_invalidos']}")
    print(f"\n📋 Detalhes do campo 'responsaveis_dados':")
    print(f"   - Lista vazia: {stats['responsaveis_dados_eh_lista_vazia']}")
    
    # Imprime análise detalhada dos primeiros casos
    print(f"\n{'='*80}")
    print(f"ANÁLISE DETALHADA (primeiros 20 casos)")
    print(f"{'='*80}\n")
    
    for analise in casos_analisados:
        print(f"\n📄 Caso ID: {analise['caso_id']}")
        print(f"   Título: {analise['titulo']}")
        print(f"   'responsaveis': {analise['responsaveis']} (tipo: {analise['responsaveis_tipo']})")
        print(f"   'responsaveis_dados': {analise['responsaveis_dados']} (tipo: {analise['responsaveis_dados_tipo']})")
        
        if analise['problemas']:
            for problema in analise['problemas']:
                print(f"   {problema}")
        else:
            print(f"   ✅ Sem problemas detectados")
    
    # Estatísticas de inconsistências
    total_problemas = sum(len(c['problemas']) for c in casos_analisados)
    casos_com_problemas = sum(1 for c in casos_analisados if c['problemas'])
    
    print(f"\n{'='*80}")
    print(f"RESUMO DE PROBLEMAS (primeiros 20 casos)")
    print(f"{'='*80}")
    print(f"📊 Total de problemas encontrados: {total_problemas}")
    print(f"📊 Casos com problemas: {casos_com_problemas} de {len(casos_analisados)} analisados")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    try:
        investigar_casos()
    except Exception as e:
        print(f"❌ Erro durante investigação: {e}")
        import traceback
        traceback.print_exc()


