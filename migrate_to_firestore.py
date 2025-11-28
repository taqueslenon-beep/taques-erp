Entendi! Vamos diminuir a largura e alinhar os itens mais à esquerda.

🔧 PROMPT #12.2 — Barra lateral mais estreita com itens à esquerda
Copie e cole no Cursor:

Preciso ajustar a barra lateral no arquivo mini_erp/core.py para ser mais estreita e com itens alinhados à esquerda.

## ALTERAÇÕES NA FUNÇÃO layout():

### 1. Diminuir a largura da barra lateral
Procure a linha do left_drawer e mude para:
```python
with ui.left_drawer(value=True).props('width=160 bordered persistent')
```

### 2. Ajustar o container dos itens do menu - menos padding
Dentro do left_drawer, onde tem o ui.column, mude para:
```python
with ui.column().classes('w-full px-1 pt-3 gap-0'):
```

### 3. Ajustar a função menu_item - itens mais compactos e à esquerda
Substitua a função menu_item inteira por:
```python
def menu_item(label: str, icon: str, target: str):
    """Cria item do menu de navegação."""
    with ui.link(target=target).classes('w-full px-2 py-2 flex flex-row items-center gap-2 hover:bg-white/10 rounded transition-colors no-underline'):
        ui.icon(icon, size='xs').classes('text-white/80')
        ui.label(label).classes('text-xs font-medium text-white/90')
```

### 4. Ajustar o header - mais compacto
Procure o bloco do header e ajuste para:
```python
with ui.header().classes('text-white shadow-sm h-12 flex items-center px-2').style(f'background-color: {PRIMARY_COLOR}'):
    with ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat round dense size=sm').classes('text-white'):
        pass
    ui.label('TAQUES ERP').classes('text-base font-semibold text-white tracking-wide ml-1')
```

## IMPORTANTE:
- NÃO altere nada nas páginas
- NÃO mexa na lógica de autenticação  
- Mantenha o restante do header (área do cliente, avatar, etc.)

Confirme as alterações feitas."""
Script de migração: JSON local → Firestore

Execute uma única vez para transferir os dados existentes.

"""

import json
import os
import sys

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mini_erp.firebase_config import get_db


def migrate_data():
    """Migra dados do JSON local para o Firestore."""
    
    # Carrega dados do JSON
    json_path = os.path.join(os.path.dirname(__file__), 'mini_erp_data.json')
    
    if not os.path.exists(json_path):
        print("❌ Arquivo mini_erp_data.json não encontrado!")
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("📂 Dados carregados do JSON")
    print(f"   - Cases: {len(data.get('cases', []))}")
    print(f"   - Processes: {len(data.get('processes', []))}")
    print(f"   - Clients: {len(data.get('clients', []))}")
    print(f"   - Users: {len(data.get('users', []))}")
    print(f"   - Agreements: {len(data.get('agreements', []))}")
    print(f"   - Benefits: {len(data.get('benefits', []))}")
    print(f"   - Convictions: {len(data.get('convictions', []))}")
    
    # Conecta ao Firestore
    print("\n🔥 Conectando ao Firestore...")
    db = get_db()
    
    # Migra cada coleção
    collections = ['cases', 'processes', 'clients', 'users', 'agreements', 'benefits', 'convictions', 'opposing_parties']
    
    for collection_name in collections:
        items = data.get(collection_name, [])
        if not items:
            print(f"   ⏭️  {collection_name}: vazio, pulando...")
            continue
        
        print(f"\n📤 Migrando {collection_name}...")
        collection_ref = db.collection(collection_name)
        
        for i, item in enumerate(items):
            # Usa o slug como ID se existir, senão gera um automático
            doc_id = item.get('slug') or item.get('title') or None
            
            if doc_id:
                # Remove caracteres inválidos para ID do Firestore
                doc_id = doc_id.replace('/', '-').replace(' ', '-').lower()[:100]
                collection_ref.document(doc_id).set(item)
            else:
                collection_ref.add(item)
            
            print(f"   ✅ {i+1}/{len(items)} migrado")
    
    print("\n" + "="*50)
    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*50)
    print("\nSeus dados agora estão no Firestore.")
    print("Você pode verificar em: https://console.firebase.google.com")
    
    return True


if __name__ == "__main__":
    print("="*50)
    print("🚀 MIGRAÇÃO JSON → FIRESTORE")
    print("="*50 + "\n")
    
    try:
        migrate_data()
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()

