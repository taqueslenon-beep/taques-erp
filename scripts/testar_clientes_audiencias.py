#!/usr/bin/env python3
"""
Script de Teste - Clientes em Audiências
Testa a função buscar_clientes_para_select() após correção
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mini_erp.pages.audiencias.database import buscar_clientes_para_select

def testar_clientes():
    """Testa busca de clientes para audiências"""
    print("=" * 80)
    print("🧪 TESTE - BUSCA DE CLIENTES PARA AUDIÊNCIAS")
    print("=" * 80)
    
    print("\n📞 Chamando buscar_clientes_para_select()...")
    clientes = buscar_clientes_para_select()
    
    print(f"\n✅ Total de clientes retornados: {len(clientes)}")
    
    # Procurar Ricardo José Teixeira
    print("\n" + "=" * 80)
    print("🔎 PROCURANDO: Ricardo José Teixeira")
    print("=" * 80)
    
    ricardo_encontrado = False
    for cliente_id, nome in clientes.items():
        nome_lower = nome.lower()
        if 'ricardo' in nome_lower and 'teixeira' in nome_lower:
            print(f"✅ ENCONTRADO!")
            print(f"   ID: {cliente_id}")
            print(f"   Nome: {nome}")
            ricardo_encontrado = True
            break
    
    if not ricardo_encontrado:
        print("❌ NÃO ENCONTRADO na lista de clientes!")
        print("\n   Nomes parecidos:")
        for cliente_id, nome in list(clientes.items())[:10]:
            nome_lower = nome.lower()
            if 'ricardo' in nome_lower or 'teixeira' in nome_lower:
                print(f"      - {nome} (ID: {cliente_id})")
    
    # Mostrar amostra
    print("\n" + "=" * 80)
    print("📋 PRIMEIROS 15 CLIENTES (ordem alfabética):")
    print("=" * 80)
    for i, (cliente_id, nome) in enumerate(list(clientes.items())[:15], 1):
        print(f"   {i:2d}. {nome}")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 80)
    
    if ricardo_encontrado:
        print("\n🎉 SUCESSO! Ricardo José Teixeira está disponível para seleção.")
    else:
        print("\n⚠️  ATENÇÃO! Ricardo José Teixeira NÃO foi encontrado.")
    
    return ricardo_encontrado


if __name__ == '__main__':
    resultado = testar_clientes()
    sys.exit(0 if resultado else 1)
