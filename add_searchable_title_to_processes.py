import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore

# Adiciona o diretório do projeto ao sys.path
# Isso é necessário para que o script possa importar 'firebase_config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import SERVICE_ACCOUNT_FILE

def migrate_processes():
    """
    Adiciona o campo 'title_searchable' a todos os documentos na coleção 'processes'
    que ainda não o possuem.
    """
    try:
        # Inicializa o app Firebase Admin
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        print("Conectado ao Firestore. Buscando processos...")
        
        processes_ref = db.collection('processes')
        docs = processes_ref.stream()
        
        updated_count = 0
        skipped_count = 0
        
        for doc in docs:
            process_data = doc.to_dict()
            
            # Verifica se o campo 'title_searchable' já existe
            if 'title_searchable' in process_data:
                skipped_count += 1
                continue
            
            # Verifica se há um título para usar
            if 'title' in process_data and process_data['title']:
                title = process_data['title']
                title_searchable = title.lower()
                
                # Atualiza o documento
                doc.reference.update({'title_searchable': title_searchable})
                updated_count += 1
                print(f"Atualizado processo: {doc.id} ('{title_searchable}')")
            else:
                print(f"Skipping process {doc.id} (sem título).")
                skipped_count += 1

        print("\n--- Migração Concluída ---")
        print(f"Processos atualizados: {updated_count}")
        print(f"Processos já atualizados ou ignorados: {skipped_count}")
        
    except Exception as e:
        print(f"\nOcorreu um erro durante a migração: {e}")
        print("Verifique se o arquivo de credenciais do Firebase está correto e acessível.")

if __name__ == "__main__":
    migrate_processes()
