#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Backup Completo do Firestore - TAQUES ERP
====================================================

Exporta TODOS os dados do Firestore para arquivo JSON.

Uso:
    python3 backup_firestore.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from mini_erp.firebase_config import get_db, ensure_firebase_initialized


# Diretório para salvar backups
BACKUPS_DIR = Path(__file__).parent / 'backups'
BACKUPS_DIR.mkdir(exist_ok=True)


# Lista de coleções conhecidas do sistema
COLECOES_CONHECIDAS = [
    # Coleções principais
    'cases',
    'processes',
    'clients',
    'opposing_parties',
    'users',
    'benefits',
    'agreements',
    'convictions',
    'prioridades',
    'entregaveis',
    'vg_casos',
    'vg_envolvidos',
    'vg_processos',
    'vg_pessoas',
    'vg_entregaveis',
    'vg_compromissos',
    'vg_tarefas',
    'vg_prazos',
    'vg_novos_negocios',
    'vg_contatos',
    'vg_usuarios',
    # Outras coleções possíveis
    'third_party_monitoring',
    'configurations',
    'workspaces',
    'acompanhamentos',
    'tarefas',
    'compromissos',
    'prazos',
    'novos_negocios',
    'contatos',
    'pessoas',
]


def converter_timestamp_para_json(obj: Any) -> Any:
    """
    Converte objetos Timestamp do Firestore para formato JSON serializável.
    
    Args:
        obj: Objeto a converter
        
    Returns:
        Objeto convertido para formato JSON
    """
    from google.cloud.firestore_v1 import Timestamp
    
    if isinstance(obj, Timestamp):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: converter_timestamp_para_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [converter_timestamp_para_json(item) for item in obj]
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif hasattr(obj, 'timestamp'):
        return obj.timestamp()
    else:
        return obj


def exportar_colecao(db, nome_colecao: str) -> List[Dict[str, Any]]:
    """
    Exporta uma coleção do Firestore para lista de documentos.
    
    Args:
        db: Instância do Firestore
        nome_colecao: Nome da coleção
        
    Returns:
        Lista de documentos no formato [{"id": "...", "dados": {...}}, ...]
    """
    documentos = []
    
    try:
        print(f"  📦 Exportando coleção: {nome_colecao}...", end=' ', flush=True)
        
        collection_ref = db.collection(nome_colecao)
        docs = list(collection_ref.stream())
        
        for doc in docs:
            try:
                dados = doc.to_dict()
                if dados is None:
                    dados = {}
                
                # Converte timestamps e outros tipos não serializáveis
                dados = converter_timestamp_para_json(dados)
                
                documentos.append({
                    "id": doc.id,
                    "dados": dados
                })
            except Exception as e:
                print(f"\n    ⚠️  Erro ao processar documento {doc.id}: {e}")
                continue
        
        print(f"✅ {len(documentos)} documentos")
        return documentos
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def descobrir_colecoes(db) -> List[str]:
    """
    Tenta descobrir todas as coleções do Firestore.
    
    Nota: O Firestore Admin SDK não permite listar coleções diretamente.
    Esta função tenta descobrir coleções conhecidas e outras através de tentativas.
    
    Args:
        db: Instância do Firestore
        
    Returns:
        Lista de nomes de coleções encontradas
    """
    colecoes_encontradas = []
    
    # Primeiro, tenta as coleções conhecidas
    print("\n🔍 Descobrindo coleções...")
    
    for nome_colecao in COLECOES_CONHECIDAS:
        try:
            # Tenta acessar a coleção (não carrega todos os documentos, apenas verifica se existe)
            collection_ref = db.collection(nome_colecao)
            # Tenta pegar apenas 1 documento para verificar se a coleção existe
            docs = list(collection_ref.limit(1).stream())
            # Se chegou aqui sem erro, a coleção existe
            colecoes_encontradas.append(nome_colecao)
            print(f"  ✓ {nome_colecao}")
        except Exception:
            # Coleção não existe ou erro ao acessar
            pass
    
    # Tenta descobrir outras coleções usando a API REST (se possível)
    # Nota: Isso requer permissões especiais e pode não funcionar
    # Por enquanto, usamos apenas as coleções conhecidas
    
    return colecoes_encontradas


def criar_backup() -> Optional[str]:
    """
    Cria backup completo do Firestore.
    
    Returns:
        Caminho do arquivo de backup criado ou None em caso de erro
    """
    try:
        print("\n" + "="*60)
        print("🔄 BACKUP FIRESTORE - TAQUES ERP")
        print("="*60)
        
        # Inicializa Firebase
        print("\n📡 Conectando ao Firebase...")
        if not ensure_firebase_initialized():
            print("❌ Erro: Não foi possível inicializar Firebase")
            return None
        
        db = get_db()
        if not db:
            print("❌ Erro: Não foi possível obter conexão com Firestore")
            return None
        
        print("✅ Firebase conectado\n")
        
        # Descobre coleções
        colecoes = descobrir_colecoes(db)
        
        if not colecoes:
            print("⚠️  Nenhuma coleção encontrada. Verifique as credenciais do Firebase.")
            return None
        
        print(f"\n📊 Total de coleções encontradas: {len(colecoes)}\n")
        
        # Estrutura do backup
        data_backup = datetime.now().isoformat()
        backup_data = {
            "data_backup": data_backup,
            "colecoes": {},
            "resumo": {
                "total_colecoes": 0,
                "total_documentos": 0
            }
        }
        
        # Exporta cada coleção
        total_documentos = 0
        
        print("📥 Exportando dados...\n")
        for idx, nome_colecao in enumerate(colecoes, 1):
            print(f"[{idx}/{len(colecoes)}] ", end='')
            documentos = exportar_colecao(db, nome_colecao)
            backup_data["colecoes"][nome_colecao] = documentos
            total_documentos += len(documentos)
        
        # Atualiza resumo
        backup_data["resumo"]["total_colecoes"] = len(colecoes)
        backup_data["resumo"]["total_documentos"] = total_documentos
        
        # Salva arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"backup_firestore_{timestamp}.json"
        caminho_arquivo = BACKUPS_DIR / nome_arquivo
        
        print(f"\n💾 Salvando backup em: {caminho_arquivo}...")
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        tamanho_arquivo = caminho_arquivo.stat().st_size
        tamanho_mb = tamanho_arquivo / (1024 * 1024)
        
        # Mostra resumo
        print("\n" + "="*60)
        print("✅ BACKUP CONCLUÍDO COM SUCESSO")
        print("="*60)
        print(f"📁 Arquivo: {caminho_arquivo}")
        print(f"📊 Coleções exportadas: {backup_data['resumo']['total_colecoes']}")
        print(f"📄 Documentos exportados: {backup_data['resumo']['total_documentos']}")
        print(f"💾 Tamanho: {tamanho_mb:.2f} MB")
        print(f"🕐 Data/Hora: {data_backup}")
        print("="*60 + "\n")
        
        return str(caminho_arquivo)
        
    except Exception as e:
        print(f"\n❌ ERRO AO CRIAR BACKUP: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Função principal."""
    try:
        caminho_backup = criar_backup()
        
        if caminho_backup:
            print(f"✅ Backup salvo com sucesso em: {caminho_backup}")
            return 0
        else:
            print("❌ Falha ao criar backup")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Backup interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
