#!/usr/bin/env python3
"""
Script de diagnóstico para erros no salvamento de acompanhamentos de terceiros.

Este script testa a criação de um acompanhamento com dados mínimos
e identifica qual campo está causando erro.
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.pages.processos.database import (
    criar_acompanhamento,
    atualizar_acompanhamento,
    sanitize_for_firestore,
    THIRD_PARTY_MONITORING_COLLECTION
)
from mini_erp.firebase_config import get_db


def test_sanitize_function():
    """Testa a função de sanitização."""
    print("\n" + "="*60)
    print("TESTE 1: Função sanitize_for_firestore")
    print("="*60)
    
    test_cases = [
        {
            'name': 'Dados com None',
            'data': {
                'title': 'Teste',
                'link': None,
                'number': None,
                'parte_ativa': None,
                'scenarios': None
            }
        },
        {
            'name': 'Dados com listas None',
            'data': {
                'title': 'Teste',
                'parte_ativa': None,
                'parte_passiva': [],
                'scenarios': None
            }
        },
        {
            'name': 'Dados válidos',
            'data': {
                'title': 'Teste',
                'link': 'https://example.com',
                'number': '123',
                'parte_ativa': ['Cliente 1'],
                'scenarios': []
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n  Testando: {test_case['name']}")
        try:
            sanitized = sanitize_for_firestore(test_case['data'])
            print(f"    ✓ Sucesso: {len(sanitized)} campos sanitizados")
            print(f"    Campos: {list(sanitized.keys())}")
            
            # Verifica se há None
            has_none = any(v is None for v in sanitized.values())
            if has_none:
                print(f"    ⚠️  AVISO: Ainda há valores None no resultado!")
            else:
                print(f"    ✓ Nenhum valor None encontrado")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            import traceback
            traceback.print_exc()


def test_create_minimal():
    """Testa criação de acompanhamento com dados mínimos."""
    print("\n" + "="*60)
    print("TESTE 2: Criação de acompanhamento com dados mínimos")
    print("="*60)
    
    minimal_data = {
        'title': f'TESTE DIAGNÓSTICO {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'process_title': f'TESTE DIAGNÓSTICO {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'link_do_processo': '',
        'link': '',
        'tipo_de_processo': 'Existente',
        'data_de_abertura': '',
        'parte_ativa': [],
        'parte_passiva': [],
        'outros_envolvidos': [],
        'processos_pais': [],
        'cases': [],
        'scenarios': [],
        'protocols': [],
        'status': 'ativo'
    }
    
    print(f"\n  Dados mínimos a testar:")
    for key, value in minimal_data.items():
        value_str = str(value)[:50] if value else 'None'
        print(f"    {key}: {value_str}")
    
    try:
        doc_id = criar_acompanhamento(minimal_data)
        if doc_id:
            print(f"\n  ✓ Acompanhamento criado com sucesso! ID: {doc_id}")
            
            # Verifica se foi salvo corretamente
            db = get_db()
            doc = db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id).get()
            if doc.exists:
                print(f"  ✓ Documento encontrado no Firestore")
                doc_data = doc.to_dict()
                print(f"  Campos salvos: {list(doc_data.keys())}")
                
                # Limpa o documento de teste
                db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id).delete()
                print(f"  ✓ Documento de teste removido")
            else:
                print(f"  ⚠️  AVISO: Documento não encontrado após criação!")
        else:
            print(f"\n  ❌ Erro: criar_acompanhamento retornou None")
    except Exception as e:
        print(f"\n  ❌ Erro ao criar acompanhamento: {e}")
        import traceback
        traceback.print_exc()


def test_create_with_none_values():
    """Testa criação com valores None para identificar campos problemáticos."""
    print("\n" + "="*60)
    print("TESTE 3: Identificação de campos problemáticos com None")
    print("="*60)
    
    # Testa cada campo individualmente
    problematic_fields = []
    
    base_data = {
        'title': f'TESTE NONE {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'process_title': f'TESTE NONE {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'link_do_processo': '',
        'tipo_de_processo': 'Existente',
        'data_de_abertura': '',
        'parte_ativa': [],
        'status': 'ativo'
    }
    
    fields_to_test = [
        'link_do_processo', 'link', 'number', 'process_number',
        'system', 'area', 'nucleo', 'status', 'result',
        'parte_ativa', 'parte_passiva', 'outros_envolvidos',
        'processos_pais', 'cases', 'scenarios', 'protocols'
    ]
    
    for field in fields_to_test:
        test_data = base_data.copy()
        test_data[field] = None
        
        print(f"\n  Testando campo: {field}")
        try:
            # Sanitiza primeiro
            sanitized = sanitize_for_firestore(test_data)
            
            # Tenta criar
            doc_id = criar_acompanhamento(sanitized)
            if doc_id:
                print(f"    ✓ Campo {field} com None: OK")
                # Limpa
                db = get_db()
                db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id).delete()
            else:
                print(f"    ⚠️  Campo {field} com None: criar_acompanhamento retornou None")
                problematic_fields.append(field)
        except Exception as e:
            print(f"    ❌ Campo {field} com None: ERRO - {e}")
            problematic_fields.append(field)
    
    if problematic_fields:
        print(f"\n  ⚠️  Campos problemáticos identificados: {problematic_fields}")
    else:
        print(f"\n  ✓ Nenhum campo problemático identificado")


def test_update_with_none():
    """Testa atualização com valores None."""
    print("\n" + "="*60)
    print("TESTE 4: Atualização de acompanhamento com valores None")
    print("="*60)
    
    # Primeiro cria um acompanhamento
    test_data = {
        'title': f'TESTE UPDATE {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'process_title': f'TESTE UPDATE {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'link_do_processo': 'https://test.com',
        'tipo_de_processo': 'Existente',
        'data_de_abertura': '',
        'parte_ativa': [],
        'status': 'ativo'
    }
    
    try:
        doc_id = criar_acompanhamento(test_data)
        if not doc_id:
            print("  ❌ Não foi possível criar acompanhamento para teste")
            return
        
        print(f"  ✓ Acompanhamento criado: {doc_id}")
        
        # Testa atualização com None
        updates = {
            'link_do_processo': None,
            'number': None,
            'system': None
        }
        
        print(f"\n  Testando atualização com campos None...")
        sanitized_updates = sanitize_for_firestore(updates)
        sucesso = atualizar_acompanhamento(doc_id, sanitized_updates)
        
        if sucesso:
            print(f"  ✓ Atualização com None: OK")
        else:
            print(f"  ❌ Atualização com None: Falhou")
        
        # Limpa
        db = get_db()
        db.collection(THIRD_PARTY_MONITORING_COLLECTION).document(doc_id).delete()
        print(f"  ✓ Documento de teste removido")
        
    except Exception as e:
        print(f"  ❌ Erro no teste de atualização: {e}")
        import traceback
        traceback.print_exc()


def generate_report():
    """Gera relatório final."""
    print("\n" + "="*60)
    print("RELATÓRIO DE DIAGNÓSTICO")
    print("="*60)
    print(f"\nData/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\nTestes executados:")
    print("  1. Função sanitize_for_firestore")
    print("  2. Criação com dados mínimos")
    print("  3. Identificação de campos problemáticos")
    print("  4. Atualização com valores None")
    print("\n" + "="*60)


def main():
    """Executa todos os testes de diagnóstico."""
    print("\n" + "="*60)
    print("DIAGNÓSTICO DE ERROS NO SALVAMENTO DE ACOMPANHAMENTOS")
    print("="*60)
    
    try:
        test_sanitize_function()
        test_create_minimal()
        test_create_with_none_values()
        test_update_with_none()
        generate_report()
        
        print("\n✓ Diagnóstico concluído!")
        print("\nSe todos os testes passaram, o problema pode estar em:")
        print("  - Valores específicos dos campos")
        print("  - Combinação de campos")
        print("  - Problemas de conexão com Firestore")
        print("  - Permissões do Firestore")
        
    except Exception as e:
        print(f"\n❌ Erro fatal no diagnóstico: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

