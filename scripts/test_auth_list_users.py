#!/usr/bin/env python3
"""
Script de teste para verificar se auth.list_users() funciona corretamente.
Execute: python scripts/test_auth_list_users.py
"""
import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import init_firebase, ensure_firebase_initialized, get_auth
from firebase_admin import auth
import traceback


def test_auth_list_users():
    """Testa se auth.list_users() funciona corretamente"""
    print("\n" + "="*70)
    print("TESTE: auth.list_users()")
    print("="*70 + "\n")
    
    try:
        # 1. Verifica inicialização do Firebase
        print("[TESTE] 1. Verificando inicialização do Firebase...")
        if not ensure_firebase_initialized():
            print("[TESTE] ✗ Firebase não está inicializado")
            return False
        print("[TESTE] ✓ Firebase inicializado")
        
        # 2. Obtém instância do Auth
        print("[TESTE] 2. Obtendo instância do Firebase Auth...")
        auth_instance = get_auth()
        if auth_instance is None:
            print("[TESTE] ✗ Não foi possível obter instância do Auth")
            return False
        print("[TESTE] ✓ Instância do Auth obtida")
        
        # 3. Testa list_users() com limite pequeno
        print("[TESTE] 3. Testando auth.list_users(max_results=1)...")
        try:
            page = auth_instance.list_users(max_results=1)
            print(f"[TESTE] ✓ auth.list_users() executado com sucesso")
            print(f"[TESTE]   Tipo do resultado: {type(page)}")
            
            # 4. Tenta iterar sobre os usuários
            print("[TESTE] 4. Iterando sobre usuários...")
            user_count = 0
            for user in page.users:
                user_count += 1
                print(f"[TESTE]   Usuário {user_count}:")
                print(f"[TESTE]     - UID: {user.uid}")
                print(f"[TESTE]     - Email: {user.email}")
                print(f"[TESTE]     - Disabled: {user.disabled}")
                print(f"[TESTE]     - Custom Claims: {user.custom_claims}")
            
            print(f"[TESTE] ✓ {user_count} usuário(s) encontrado(s) na primeira página")
            
            # 5. Testa get_next_page()
            print("[TESTE] 5. Testando get_next_page()...")
            try:
                next_page = page.get_next_page()
                if next_page:
                    print(f"[TESTE] ✓ Próxima página obtida com {len(next_page.users)} usuários")
                else:
                    print("[TESTE] ✓ Não há próxima página (esperado se houver poucos usuários)")
            except StopIteration:
                print("[TESTE] ✓ StopIteration (fim das páginas)")
            except Exception as next_err:
                print(f"[TESTE] ⚠ Erro ao obter próxima página: {next_err}")
                print(f"[TESTE]   Tipo: {type(next_err).__name__}")
            
            print("\n" + "-"*70)
            print("RESULTADO: ✓ TESTE PASSOU")
            print("-"*70 + "\n")
            return True
            
        except ImportError as import_err:
            print(f"[TESTE] ✗ Erro de importação: {import_err}")
            traceback.print_exc()
            return False
        except AttributeError as attr_err:
            print(f"[TESTE] ✗ Erro de atributo: {attr_err}")
            print(f"[TESTE]   Auth pode não estar disponível")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"[TESTE] ✗ Erro ao executar auth.list_users(): {e}")
            print(f"[TESTE]   Tipo do erro: {type(e).__name__}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"[TESTE] ✗ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        return False


def test_list_all_users():
    """Testa listagem completa de usuários"""
    print("\n" + "="*70)
    print("TESTE: Listagem completa de usuários")
    print("="*70 + "\n")
    
    try:
        ensure_firebase_initialized()
        auth_instance = get_auth()
        
        print("[TESTE] Listando todos os usuários...")
        usuarios = []
        page = auth_instance.list_users()
        page_count = 0
        
        while page:
            page_count += 1
            print(f"[TESTE] Processando página {page_count}...")
            usuarios.extend(page.users)
            
            try:
                page = page.get_next_page()
            except StopIteration:
                break
            except Exception as e:
                print(f"[TESTE] ⚠ Erro ao obter próxima página: {e}")
                break
        
        print(f"\n[TESTE] ✓ Total de {len(usuarios)} usuário(s) encontrado(s) em {page_count} página(s)")
        
        # Lista resumida
        for i, user in enumerate(usuarios[:10], 1):  # Mostra apenas os 10 primeiros
            print(f"  {i}. {user.email} (UID: {user.uid[:8]}...)")
        
        if len(usuarios) > 10:
            print(f"  ... e mais {len(usuarios) - 10} usuário(s)")
        
        return True
        
    except Exception as e:
        print(f"[TESTE] ✗ Erro: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTES DE FIREBASE AUTH - list_users()")
    print("="*70)
    
    # Teste básico
    test1_ok = test_auth_list_users()
    
    # Teste completo (se o básico passou)
    if test1_ok:
        test2_ok = test_list_all_users()
    else:
        print("\n[TESTE] Pulando teste completo devido a falha no teste básico")
        test2_ok = False
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO DOS TESTES")
    print("="*70)
    print(f"  Teste básico (list_users): {'✓ PASSOU' if test1_ok else '✗ FALHOU'}")
    print(f"  Teste completo (todos usuários): {'✓ PASSOU' if test2_ok else '✗ FALHOU' if test1_ok else '⏭ PULADO'}")
    print("="*70 + "\n")











