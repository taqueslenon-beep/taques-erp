#!/usr/bin/env python3
"""
Script de Diagnóstico - Clientes no Firebase
Verifica como os clientes estão armazenados na collection vg_pessoas
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mini_erp.firebase_config import get_db

def diagnosticar_clientes():
    """Diagnostica os clientes na collection vg_pessoas"""
    print("=" * 80)
    print("🔍 DIAGNÓSTICO - CLIENTES NA COLLECTION VG_PESSOAS")
    print("=" * 80)
    
    db = get_db()
    
    # Buscar todas as pessoas
    print("\n📊 Buscando todas as pessoas...")
    docs = db.collection('vg_pessoas').stream()
    
    todas_categorias = {}
    pessoas_encontradas = []
    ricardo_encontrado = None
    
    for doc in docs:
        pessoa = doc.to_dict()
        pessoa_id = doc.id
        
        # Extrair informações
        nome = pessoa.get('nome_exibicao') or pessoa.get('full_name') or pessoa.get('nome') or '[SEM NOME]'
        categoria = pessoa.get('categoria', '[SEM CATEGORIA]')
        tipo_pessoa = pessoa.get('tipo_pessoa', '[SEM TIPO]')
        
        # Contar categorias
        if categoria not in todas_categorias:
            todas_categorias[categoria] = 0
        todas_categorias[categoria] += 1
        
        # Procurar Ricardo
        nome_lower = nome.lower()
        if 'ricardo' in nome_lower and 'teixeira' in nome_lower:
            ricardo_encontrado = {
                'id': pessoa_id,
                'nome': nome,
                'categoria': categoria,
                'tipo_pessoa': tipo_pessoa,
                'dados_completos': pessoa
            }
        
        pessoas_encontradas.append({
            'id': pessoa_id,
            'nome': nome,
            'categoria': categoria,
            'tipo_pessoa': tipo_pessoa
        })
    
    # Relatório
    print(f"\n✅ Total de pessoas encontradas: {len(pessoas_encontradas)}")
    
    print("\n" + "=" * 80)
    print("📋 CATEGORIAS ENCONTRADAS:")
    print("=" * 80)
    for cat, count in sorted(todas_categorias.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count} pessoa(s)")
    
    # Ricardo José Teixeira
    print("\n" + "=" * 80)
    print("🔎 PROCURANDO: Ricardo José Teixeira")
    print("=" * 80)
    
    if ricardo_encontrado:
        print("✅ ENCONTRADO!")
        print(f"\n   ID: {ricardo_encontrado['id']}")
        print(f"   Nome: {ricardo_encontrado['nome']}")
        print(f"   Categoria: {ricardo_encontrado['categoria']}")
        print(f"   Tipo Pessoa: {ricardo_encontrado['tipo_pessoa']}")
        print("\n   📄 Campos completos:")
        for key, value in sorted(ricardo_encontrado['dados_completos'].items()):
            if key not in ['_id']:
                valor_str = str(value)[:100]  # Limitar tamanho
                print(f"      {key}: {valor_str}")
    else:
        print("❌ NÃO ENCONTRADO!")
        print("\n   Buscando nomes parecidos...")
        nomes_parecidos = [p for p in pessoas_encontradas if 'ricardo' in p['nome'].lower() or 'teixeira' in p['nome'].lower()]
        if nomes_parecidos:
            print(f"\n   Encontrados {len(nomes_parecidos)} nome(s) parecido(s):")
            for p in nomes_parecidos[:10]:
                print(f"      - {p['nome']} (categoria: {p['categoria']}, ID: {p['id']})")
        else:
            print("   Nenhum nome parecido encontrado.")
    
    # Query atual
    print("\n" + "=" * 80)
    print("🔧 QUERY ATUAL:")
    print("=" * 80)
    print("   db.collection('vg_pessoas').where('categoria', '==', 'cliente')")
    
    docs_cliente = db.collection('vg_pessoas').where('categoria', '==', 'cliente').stream()
    clientes_filtrados = [doc.to_dict().get('nome_exibicao') or doc.to_dict().get('full_name') or doc.to_dict().get('nome') for doc in docs_cliente]
    print(f"\n   Retorna: {len(clientes_filtrados)} cliente(s)")
    
    # Sugestões
    print("\n" + "=" * 80)
    print("💡 SUGESTÕES DE CORREÇÃO:")
    print("=" * 80)
    
    if '[SEM CATEGORIA]' in todas_categorias and todas_categorias['[SEM CATEGORIA]'] > 0:
        print(f"   ⚠️  {todas_categorias['[SEM CATEGORIA]']} pessoa(s) SEM campo 'categoria'")
        print("   → Solução: Remover filtro ou adicionar fallback")
    
    if 'Cliente' in todas_categorias:
        print(f"   ⚠️  {todas_categorias['Cliente']} pessoa(s) com categoria 'Cliente' (C maiúsculo)")
        print("   → Solução: Filtro case-insensitive")
    
    categorias_cliente = [cat for cat in todas_categorias.keys() if 'cliente' in cat.lower()]
    if len(categorias_cliente) > 1:
        print(f"   ⚠️  Múltiplas variações de 'cliente': {categorias_cliente}")
        print("   → Solução: Normalizar categorias ou usar filtro flexível")
    
    print("\n" + "=" * 80)
    print("✅ DIAGNÓSTICO CONCLUÍDO")
    print("=" * 80)


if __name__ == '__main__':
    diagnosticar_clientes()
