#!/usr/bin/env python3
"""
Script para verificar se todos os dados estão salvos no Firebase
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mini_erp.firebase_config import get_db, init_firebase

def verificar_colecao(db, nome_colecao):
    """Verifica uma coleção e retorna estatísticas."""
    try:
        collection_ref = db.collection(nome_colecao)
        docs = list(collection_ref.stream())
        count = len(docs)
        
        # Verifica se há documentos
        if count > 0:
            # Pega um exemplo para verificar estrutura
            exemplo = docs[0].to_dict()
            campos = list(exemplo.keys()) if exemplo else []
            return {
                'status': 'OK',
                'count': count,
                'campos_exemplo': campos[:5]  # Primeiros 5 campos
            }
        else:
            return {
                'status': 'VAZIA',
                'count': 0,
                'campos_exemplo': []
            }
    except Exception as e:
        return {
            'status': 'ERRO',
            'count': 0,
            'erro': str(e),
            'campos_exemplo': []
        }

def main():
    print("\n" + "="*70)
    print("VERIFICAÇÃO DE DADOS NO FIREBASE - TAQUES ERP")
    print("="*70 + "\n")
    
    # Inicializa Firebase
    try:
        init_firebase()
        db = get_db()
        print("✅ Conexão com Firebase estabelecida\n")
    except Exception as e:
        print(f"❌ Erro ao conectar com Firebase: {e}")
        return
    
    # Lista de coleções principais
    colecoes = [
        'cases',              # Casos
        'processes',          # Processos
        'entregaveis',        # Entregáveis
        'prazos',             # Prazos
        'agreements',         # Acordos
        'users',              # Usuários
        'pessoas',            # Pessoas
        'vg_casos',           # Casos (visão geral)
        'prioridades',        # Prioridades
        'third_party_monitoring',  # Acompanhamento terceiros
        'slack_tokens',       # Tokens Slack
    ]
    
    resultados = {}
    total_docs = 0
    
    print("Verificando coleções:\n")
    for colecao in colecoes:
        resultado = verificar_colecao(db, colecao)
        resultados[colecao] = resultado
        total_docs += resultado['count']
        
        # Exibe resultado
        if resultado['status'] == 'OK':
            print(f"  ✅ {colecao:30s} → {resultado['count']:4d} documentos")
        elif resultado['status'] == 'VAZIA':
            print(f"  ⚠️  {colecao:30s} → {resultado['count']:4d} documentos (vazia)")
        else:
            print(f"  ❌ {colecao:30s} → ERRO: {resultado.get('erro', 'Desconhecido')}")
    
    print("\n" + "="*70)
    print(f"RESUMO:")
    print(f"  Total de documentos: {total_docs}")
    print(f"  Coleções verificadas: {len(colecoes)}")
    print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Verifica coleções críticas
    colecoes_criticas = ['cases', 'processes', 'entregaveis', 'prazos']
    problemas = []
    
    for colecao in colecoes_criticas:
        if colecao in resultados:
            if resultados[colecao]['status'] == 'ERRO':
                problemas.append(f"{colecao}: Erro ao acessar")
            elif resultados[colecao]['count'] == 0:
                problemas.append(f"{colecao}: Vazia (pode ser normal se não houver dados)")
    
    if problemas:
        print("⚠️  ATENÇÃO:")
        for problema in problemas:
            print(f"  - {problema}")
        print()
    else:
        print("✅ Todas as coleções críticas estão acessíveis\n")

if __name__ == '__main__':
    main()





