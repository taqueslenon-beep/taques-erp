#!/usr/bin/env python3
"""
Script para excluir prazos duplicados do parcelamento Waldir Jantsch.

Uso:
    python scripts/excluir_prazos_waldir_jantsch.py --confirmar

Exclui todos os prazos que contenham "Waldir Jantsch - São João da Barra" no título.
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db, ensure_firebase_initialized


def excluir_prazos_waldir_jantsch(confirmar=False):
    """
    Busca e exclui todos os prazos que contenham 
    'Waldir Jantsch - São João da Barra' no título.
    """
    print("\n" + "="*60)
    print("EXCLUSÃO DE PRAZOS - WALDIR JANTSCH - SÃO JOÃO DA BARRA")
    print("="*60 + "\n")
    
    # Inicializa Firebase
    ensure_firebase_initialized()
    db = get_db()
    
    # Busca todos os prazos
    print("[1] Buscando prazos na coleção 'prazos'...")
    docs = db.collection('prazos').stream()
    
    prazos_para_excluir = []
    
    for doc in docs:
        prazo = doc.to_dict()
        titulo = prazo.get('titulo', '') or ''
        
        # Verifica se é do parcelamento Waldir Jantsch
        if 'Waldir Jantsch' in titulo and 'São João da Barra' in titulo:
            prazos_para_excluir.append({
                'id': doc.id,
                'titulo': titulo
            })
    
    print(f"\n[2] Encontrados {len(prazos_para_excluir)} prazos para excluir:\n")
    
    if not prazos_para_excluir:
        print("    Nenhum prazo encontrado com esse critério.")
        return
    
    # Lista os primeiros 10 prazos
    for i, prazo in enumerate(prazos_para_excluir[:10], 1):
        print(f"    {i:3d}. {prazo['titulo'][:60]}...")
    
    if len(prazos_para_excluir) > 10:
        print(f"    ... e mais {len(prazos_para_excluir) - 10} prazos")
    
    if not confirmar:
        print(f"\n" + "-"*60)
        print(f"ATENÇÃO: Serão excluídos {len(prazos_para_excluir)} prazos!")
        print("Para confirmar, execute com: --confirmar")
        print("-"*60 + "\n")
        return
    
    # Executa exclusão
    print("\n[3] Excluindo prazos...")
    excluidos = 0
    erros = 0
    
    for prazo in prazos_para_excluir:
        try:
            db.collection('prazos').document(prazo['id']).delete()
            excluidos += 1
            print(f"    ✓ Excluído: {prazo['id']}")
        except Exception as e:
            erros += 1
            print(f"    ✗ Erro ao excluir {prazo['id']}: {e}")
    
    # Resumo
    print(f"\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"  • Excluídos com sucesso: {excluidos}")
    print(f"  • Erros: {erros}")
    print(f"\n✅ Concluído! Agora você pode recadastrar o parcelamento.\n")


if __name__ == '__main__':
    confirmar = '--confirmar' in sys.argv
    excluir_prazos_waldir_jantsch(confirmar=confirmar)

