#!/usr/bin/env python3
"""
Script de Teste de Conexão Firebase
Testa conexões com Firebase Firestore e Firebase Storage.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

try:
    import firebase_admin
    from firebase_admin import storage
    from mini_erp.firebase_config import get_db, init_firebase
except ImportError as e:
    print(f"✗ Erro ao importar dependências: {e}")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)


def verificar_credenciais() -> Dict[str, Any]:
    """
    Verifica se as credenciais do Firebase estão configuradas.
    
    Returns:
        Dict com informações sobre as credenciais encontradas
    """
    resultado = {
        "metodo": None,
        "credenciais_presentes": False,
        "detalhes": []
    }
    
    # Verificar variáveis de ambiente
    env_vars = [
        "FIREBASE_PRIVATE_KEY_ID",
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_CLIENT_ID",
        "FIREBASE_CERT_URL"
    ]
    
    env_presentes = []
    for var in env_vars:
        if os.environ.get(var):
            env_presentes.append(var)
    
    if len(env_presentes) == len(env_vars):
        resultado["metodo"] = "variáveis_ambiente"
        resultado["credenciais_presentes"] = True
        resultado["detalhes"].append(f"✓ {len(env_presentes)} variáveis de ambiente configuradas")
    
    # Verificar arquivo JSON
    cred_path = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
    if os.path.exists(cred_path):
        resultado["metodo"] = "arquivo_json"
        resultado["credenciais_presentes"] = True
        resultado["detalhes"].append(f"✓ Arquivo firebase-credentials.json encontrado")
    
    if not resultado["credenciais_presentes"]:
        resultado["detalhes"].append("✗ Nenhuma credencial encontrada")
        resultado["detalhes"].append("  Configure variáveis de ambiente ou arquivo firebase-credentials.json")
    
    return resultado


def testar_conexao_firestore() -> Dict[str, Any]:
    """
    Testa conexão com Firebase Firestore.
    Executa operações de leitura, escrita e exclusão.
    
    Returns:
        Dict com status e mensagens do teste
    """
    resultado = {
        "sucesso": False,
        "mensagens": [],
        "erro": None
    }
    
    try:
        # Inicializar Firebase
        resultado["mensagens"].append("→ Inicializando conexão Firestore...")
        db = get_db()
        resultado["mensagens"].append("✓ Cliente Firestore obtido")
        
        # Teste de leitura
        resultado["mensagens"].append("→ Testando leitura (coleção 'users')...")
        docs = list(db.collection('users').limit(1).stream())
        resultado["mensagens"].append(f"✓ Leitura bem-sucedida ({len(docs)} documento(s) encontrado(s))")
        
        # Teste de escrita
        resultado["mensagens"].append("→ Testando escrita (documento temporário)...")
        test_doc_id = f"_test_connection_{int(datetime.now().timestamp())}"
        test_ref = db.collection('_test_connection').document(test_doc_id)
        test_ref.set({
            'teste': True,
            'timestamp': datetime.now().isoformat(),
            'mensagem': 'Documento de teste criado pelo script teste_firebase.py'
        })
        resultado["mensagens"].append(f"✓ Escrita bem-sucedida (ID: {test_doc_id})")
        
        # Teste de exclusão
        resultado["mensagens"].append("→ Testando exclusão...")
        test_ref.delete()
        resultado["mensagens"].append("✓ Exclusão bem-sucedida")
        
        resultado["sucesso"] = True
        
    except Exception as e:
        resultado["erro"] = str(e)
        resultado["mensagens"].append(f"✗ Erro: {e}")
        import traceback
        resultado["mensagens"].append(f"  Detalhes: {traceback.format_exc()}")
    
    return resultado


def testar_conexao_storage() -> Dict[str, Any]:
    """
    Testa conexão com Firebase Storage.
    Executa operações de leitura, escrita e exclusão.
    
    Returns:
        Dict com status e mensagens do teste
    """
    resultado = {
        "sucesso": False,
        "mensagens": [],
        "erro": None
    }
    
    try:
        # Obter bucket
        resultado["mensagens"].append("→ Obtendo bucket do Storage...")
        bucket = storage.bucket()
        
        if not bucket:
            resultado["erro"] = "Bucket não disponível"
            resultado["mensagens"].append("✗ Bucket não disponível")
            return resultado
        
        resultado["mensagens"].append(f"✓ Bucket obtido: {bucket.name}")
        
        # Teste de escrita
        resultado["mensagens"].append("→ Testando upload (arquivo temporário)...")
        test_blob_name = f"_test_connection/test_{int(datetime.now().timestamp())}.txt"
        blob = bucket.blob(test_blob_name)
        
        test_content = f"Teste de conexão Firebase Storage\nTimestamp: {datetime.now().isoformat()}\n"
        blob.upload_from_string(test_content, content_type='text/plain')
        resultado["mensagens"].append(f"✓ Upload bem-sucedido ({test_blob_name})")
        
        # Teste de leitura
        resultado["mensagens"].append("→ Testando leitura...")
        if blob.exists():
            resultado["mensagens"].append("✓ Arquivo existe e está acessível")
        else:
            resultado["mensagens"].append("⚠ Arquivo não encontrado após upload")
        
        # Teste de exclusão
        resultado["mensagens"].append("→ Testando exclusão...")
        blob.delete()
        resultado["mensagens"].append("✓ Exclusão bem-sucedida")
        
        resultado["sucesso"] = True
        
    except Exception as e:
        resultado["erro"] = str(e)
        resultado["mensagens"].append(f"✗ Erro: {e}")
        import traceback
        resultado["mensagens"].append(f"  Detalhes: {traceback.format_exc()}")
    
    return resultado


def exibir_relatorio(credenciais: Dict[str, Any], 
                     firestore: Dict[str, Any], 
                     storage_result: Dict[str, Any]) -> None:
    """
    Exibe relatório formatado dos testes.
    
    Args:
        credenciais: Resultado da verificação de credenciais
        firestore: Resultado do teste Firestore
        storage_result: Resultado do teste Storage
    """
    print("\n" + "=" * 60)
    print("RELATÓRIO DE TESTE DE CONEXÃO FIREBASE")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Seção: Credenciais
    print("─" * 60)
    print("1. VERIFICAÇÃO DE CREDENCIAIS")
    print("─" * 60)
    for detalhe in credenciais["detalhes"]:
        print(f"  {detalhe}")
    print()
    
    # Seção: Firestore
    print("─" * 60)
    print("2. TESTE FIRESTORE")
    print("─" * 60)
    for mensagem in firestore["mensagens"]:
        print(f"  {mensagem}")
    if firestore["erro"]:
        print(f"  ✗ Erro detalhado: {firestore['erro']}")
    print()
    
    # Seção: Storage
    print("─" * 60)
    print("3. TESTE STORAGE")
    print("─" * 60)
    for mensagem in storage_result["mensagens"]:
        print(f"  {mensagem}")
    if storage_result["erro"]:
        print(f"  ✗ Erro detalhado: {storage_result['erro']}")
    print()
    
    # Status Final
    print("=" * 60)
    print("STATUS FINAL")
    print("=" * 60)
    
    credenciais_ok = credenciais["credenciais_presentes"]
    firestore_ok = firestore["sucesso"]
    storage_ok = storage_result["sucesso"]
    
    # Firestore é obrigatório, Storage é opcional
    if credenciais_ok and firestore_ok:
        if storage_ok:
            print("✓ CONECTADO - Todas as conexões funcionando corretamente")
        else:
            print("✓ CONECTADO - Firestore funcionando (Storage não disponível - opcional)")
        print()
        sys.exit(0)
    else:
        print("✗ FALHA - Conexões críticas falharam")
        print()
        if not credenciais_ok:
            print("  • Credenciais não configuradas")
        if not firestore_ok:
            print("  • Firestore com falha (CRÍTICO)")
        if not storage_ok:
            print("  • Storage com falha (opcional - pode não estar configurado)")
        print()
        sys.exit(1)


def main():
    """Função principal do script."""
    print("Iniciando teste de conexão Firebase...")
    print()
    
    # Verificar credenciais
    credenciais = verificar_credenciais()
    
    # Testar Firestore
    firestore_result = testar_conexao_firestore()
    
    # Testar Storage
    storage_result = testar_conexao_storage()
    
    # Exibir relatório
    exibir_relatorio(credenciais, firestore_result, storage_result)


if __name__ == "__main__":
    main()

