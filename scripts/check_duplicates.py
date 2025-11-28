#!/usr/bin/env python3
"""
Script para verificar e listar duplicatas de casos no Firebase.
Execute: python scripts/check_duplicates.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

def check_duplicates():
    """Verifica duplicatas de casos no Firebase."""
    db = get_db()
    
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE DUPLICATAS NO FIREBASE")
    print("="*60 + "\n")
    
    # Carregar todos os casos
    docs = list(db.collection('cases').stream())
    print(f"Total de documentos na coleção 'cases': {len(docs)}")
    
    # Mapear por diferentes critérios
    by_doc_id = {}
    by_slug = {}
    by_title = {}
    by_name_year = {}
    
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        slug = data.get('slug', '')
        title = data.get('title', '')
        name = data.get('name', '')
        year = data.get('year', '')
        name_year_key = f"{name}|{year}"
        
        # Por doc_id (não deveria ter duplicatas)
        if doc_id in by_doc_id:
            print(f"⚠️  ERRO: doc_id duplicado: {doc_id}")
        by_doc_id[doc_id] = data
        
        # Por slug
        if slug:
            if slug in by_slug:
                by_slug[slug].append({'doc_id': doc_id, 'title': title, 'data': data})
            else:
                by_slug[slug] = [{'doc_id': doc_id, 'title': title, 'data': data}]
        
        # Por título
        if title:
            if title in by_title:
                by_title[title].append({'doc_id': doc_id, 'slug': slug, 'data': data})
            else:
                by_title[title] = [{'doc_id': doc_id, 'slug': slug, 'data': data}]
        
        # Por nome + ano
        if name and year:
            if name_year_key in by_name_year:
                by_name_year[name_year_key].append({'doc_id': doc_id, 'title': title, 'slug': slug})
            else:
                by_name_year[name_year_key] = [{'doc_id': doc_id, 'title': title, 'slug': slug}]
    
    # Reportar duplicatas
    print("\n" + "-"*60)
    print("DUPLICATAS POR SLUG:")
    print("-"*60)
    slug_dups = {k: v for k, v in by_slug.items() if len(v) > 1}
    if slug_dups:
        for slug, items in slug_dups.items():
            print(f"\n  Slug: '{slug}' ({len(items)} documentos)")
            for item in items:
                print(f"    - doc_id: {item['doc_id']}, title: {item['title']}")
    else:
        print("  ✅ Nenhuma duplicata por slug")
    
    print("\n" + "-"*60)
    print("DUPLICATAS POR TÍTULO:")
    print("-"*60)
    title_dups = {k: v for k, v in by_title.items() if len(v) > 1}
    if title_dups:
        for title, items in title_dups.items():
            print(f"\n  Título: '{title}' ({len(items)} documentos)")
            for item in items:
                print(f"    - doc_id: {item['doc_id']}, slug: {item['slug']}")
    else:
        print("  ✅ Nenhuma duplicata por título")
    
    print("\n" + "-"*60)
    print("DUPLICATAS POR NOME+ANO:")
    print("-"*60)
    name_year_dups = {k: v for k, v in by_name_year.items() if len(v) > 1}
    if name_year_dups:
        for key, items in name_year_dups.items():
            name, year = key.split('|')
            print(f"\n  Nome: '{name}', Ano: {year} ({len(items)} documentos)")
            for item in items:
                print(f"    - doc_id: {item['doc_id']}, title: {item['title']}, slug: {item['slug']}")
    else:
        print("  ✅ Nenhuma duplicata por nome+ano")
    
    print("\n" + "-"*60)
    print("LISTA COMPLETA DE CASOS:")
    print("-"*60)
    for doc_id, data in sorted(by_doc_id.items()):
        title = data.get('title', 'SEM TÍTULO')
        slug = data.get('slug', 'SEM SLUG')
        case_type = data.get('case_type', 'SEM TIPO')
        print(f"  [{case_type}] {title}")
        print(f"       doc_id: {doc_id}")
        print(f"       slug: {slug}")
        print()
    
    print("\n" + "="*60)
    print("RESUMO:")
    print(f"  - Total de documentos: {len(docs)}")
    print(f"  - Duplicatas por slug: {len(slug_dups)}")
    print(f"  - Duplicatas por título: {len(title_dups)}")
    print(f"  - Duplicatas por nome+ano: {len(name_year_dups)}")
    print("="*60 + "\n")
    
    return {
        'total': len(docs),
        'slug_dups': slug_dups,
        'title_dups': title_dups,
        'name_year_dups': name_year_dups
    }

if __name__ == '__main__':
    check_duplicates()


