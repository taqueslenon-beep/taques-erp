#!/usr/bin/env python3
"""
Script de diagnóstico para identificar diferenças entre processos no Firestore.
Compara processos que funcionam vs processos que não funcionam no modal VG.
"""
import sys
sys.path.insert(0, '/Users/lenontaques/Documents/taques-erp')

from mini_erp.firebase_config import get_db

def diagnostico():
    """Diagnóstico de processos na coleção vg_processos."""
    db = get_db()
    if not db:
        print("❌ Erro: Não foi possível conectar ao Firebase")
        return
    
    print("=" * 60)
    print("DIAGNÓSTICO DE PROCESSOS - COLEÇÃO vg_processos")
    print("=" * 60)
    
    # Busca todos os processos
    docs = db.collection('vg_processos').stream()
    processos = []
    
    for doc in docs:
        dados = doc.to_dict()
        dados['_id'] = doc.id
        processos.append(dados)
    
    print(f"\n📊 Total de processos: {len(processos)}")
    print("\n" + "-" * 60)
    
    # Analisa cada processo
    for idx, p in enumerate(processos[:15], 1):  # Limita a 15 para não poluir
        titulo = p.get('titulo', p.get('title', 'SEM_TITULO'))[:50]
        _id = p.get('_id', 'SEM_ID')
        
        # Campos críticos para o modal
        campos_criticos = ['titulo', 'numero', 'tipo', 'data_abertura', 'clientes', 'parte_contraria']
        campos_presentes = [c for c in campos_criticos if p.get(c)]
        campos_ausentes = [c for c in campos_criticos if not p.get(c)]
        
        # Status
        status = "✅" if len(campos_presentes) >= 4 else ("⚠️" if len(campos_presentes) >= 2 else "❌")
        
        print(f"\n{status} [{idx}] {titulo}...")
        print(f"   ID: {_id}")
        print(f"   Campos presentes: {campos_presentes}")
        if campos_ausentes:
            print(f"   Campos ausentes: {campos_ausentes}")
        
        # Mostra valores
        print(f"   titulo: {p.get('titulo', 'N/A')[:40]}...")
        print(f"   numero: {p.get('numero', 'N/A')}")
        print(f"   clientes: {p.get('clientes', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("BUSCA POR 'EDSON' ou 'RAABE'")
    print("=" * 60)
    
    for p in processos:
        titulo = str(p.get('titulo', '')).upper()
        clientes = str(p.get('clientes', '')).upper()
        if 'EDSON' in titulo or 'RAABE' in titulo or 'EDSON' in clientes or 'RAABE' in clientes:
            print(f"\n📌 Encontrado:")
            print(f"   ID: {p.get('_id')}")
            print(f"   Título: {p.get('titulo', 'N/A')}")
            print(f"   Número: {p.get('numero', 'N/A')}")
            print(f"   Clientes: {p.get('clientes', 'N/A')}")
            print(f"   Todos os campos: {list(p.keys())}")
    
    print("\n" + "=" * 60)
    print("VERIFICANDO COLEÇÃO 'processes' (módulo principal)")
    print("=" * 60)
    
    docs_main = db.collection('processes').stream()
    count_main = 0
    for doc in docs_main:
        dados = doc.to_dict()
        titulo = str(dados.get('title', dados.get('titulo', ''))).upper()
        if 'EDSON' in titulo or 'RAABE' in titulo:
            count_main += 1
            print(f"\n📌 Encontrado em 'processes':")
            print(f"   ID: {doc.id}")
            print(f"   Title: {dados.get('title', 'N/A')}")
            print(f"   Numero: {dados.get('number', dados.get('numero', 'N/A'))}")
    
    if count_main == 0:
        print("   Nenhum processo 'EDSON/RAABE' encontrado em 'processes'")
    
    print("\n✅ Diagnóstico concluído!")

if __name__ == '__main__':
    diagnostico()

