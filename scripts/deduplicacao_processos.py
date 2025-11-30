"""
Script de Deduplicação Extrema - Módulo Processos

Este script realiza:
1. Backup completo da coleção 'processes'
2. Identificação de duplicatas
3. Validação de referências
4. Soft delete de duplicados
5. Detecção de outras duplicações
6. Investigação de causa raiz
7. Geração de relatório completo
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Adiciona o diretório do projeto ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db, init_firebase

# Inicializa Firebase
init_firebase()
db = get_db()

# Timestamp para arquivos
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)


# =============================================================================
# PASSO 1: BACKUP COMPLETO
# =============================================================================

def fazer_backup_processes() -> str:
    """
    Faz backup completo da coleção 'processes'.
    
    Returns:
        Caminho do arquivo de backup criado
    """
    print("\n" + "="*80)
    print("PASSO 1: BACKUP COMPLETO")
    print("="*80)
    
    try:
        print("📦 Coletando todos os processos do Firestore...")
        processes_ref = db.collection('processes')
        docs = processes_ref.stream()
        
        backup_data = {
            'timestamp': TIMESTAMP,
            'total_documents': 0,
            'processes': []
        }
        
        count = 0
        for doc in docs:
            process_data = doc.to_dict()
            process_data['_id'] = doc.id
            process_data['_backup_doc_id'] = doc.id  # Preserva ID original
            backup_data['processes'].append(process_data)
            count += 1
            
            if count % 100 == 0:
                print(f"  Coletados {count} processos...")
        
        backup_data['total_documents'] = count
        
        # Salva backup
        backup_filename = f"backup_processes_{TIMESTAMP}.json"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        print(f"💾 Salvando backup em: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Backup concluído: {count} processos salvos")
        print(f"📁 Arquivo: {backup_path}")
        
        return backup_path
    
    except Exception as e:
        print(f"❌ ERRO ao fazer backup: {e}")
        import traceback
        traceback.print_exc()
        raise


# =============================================================================
# PASSO 2: ANÁLISE E IDENTIFICAÇÃO
# =============================================================================

def identificar_duplicatas(numero_processo: str = "PMSC/46545/2020") -> Dict[str, Any]:
    """
    Identifica duplicatas de um processo específico.
    
    Args:
        numero_processo: Número do processo a buscar
    
    Returns:
        Dicionário com informações sobre duplicatas
    """
    print("\n" + "="*80)
    print("PASSO 2: ANÁLISE E IDENTIFICAÇÃO")
    print("="*80)
    
    try:
        print(f"🔍 Buscando processos com número: {numero_processo}")
        
        # Busca processos pelo número (tenta ambos os campos)
        docs_numero = list(db.collection('processes').where('numero', '==', numero_processo).stream())
        docs_number = list(db.collection('processes').where('number', '==', numero_processo).stream())
        
        # Combina resultados e remove duplicatas por ID
        all_docs = {}
        for doc in docs_numero + docs_number:
            all_docs[doc.id] = doc
        
        docs = list(all_docs.values())
        
        # Se não encontrou pelo número, busca por título (caso o número esteja no título)
        if len(docs) == 0:
            print(f"⚠️  Não encontrado pelo número. Buscando por título...")
            all_processes = db.collection('processes').stream()
            for doc in all_processes:
                data = doc.to_dict()
                title = data.get('title', '')
                number = data.get('number', '') or data.get('numero', '')
                
                # Verifica se número ou parte dele está no título
                if numero_processo in title or numero_processo in str(number):
                    all_docs[doc.id] = doc
            
            docs = list(all_docs.values())
        
        print(f"📊 Encontrados {len(docs)} registros com este número")
        
        if len(docs) == 0:
            print("⚠️  Nenhum processo encontrado com este número")
            return {
                'total': 0,
                'duplicatas': [],
                'original': None,
                'duplicados': []
            }
        
        # Analisa cada documento
        processos_info = []
        for doc in docs:
            data = doc.to_dict()
            processos_info.append({
                '_id': doc.id,
                'title': data.get('title', ''),
                'numero': data.get('numero', '') or data.get('number', ''),
                'data_abertura': data.get('data_abertura', ''),
                'status': data.get('status', ''),
                'createdAt': data.get('createdAt', ''),
                'updatedAt': data.get('updatedAt', ''),
                'case_ids': data.get('case_ids', []),
                'clients': data.get('clients', []),
                'opposing_parties': data.get('opposing_parties', []),
                'data': data
            })
        
        # Ordena por createdAt (mais antigo primeiro = original)
        processos_info.sort(key=lambda x: x.get('createdAt') or '')
        
        original = processos_info[0] if processos_info else None
        duplicados = processos_info[1:] if len(processos_info) > 1 else []
        
        print(f"\n📋 RESUMO:")
        print(f"  Total encontrado: {len(processos_info)}")
        print(f"  Original (mais antigo): {original['_id'] if original else 'N/A'}")
        print(f"  Duplicados: {len(duplicados)}")
        
        if original:
            print(f"\n  ORIGINAL:")
            print(f"    ID: {original['_id']}")
            print(f"    Título: {original['title']}")
            print(f"    Criado em: {original.get('createdAt', 'N/A')}")
            print(f"    Casos vinculados: {len(original.get('case_ids', []))}")
            print(f"    Clientes: {len(original.get('clients', []))}")
        
        if duplicados:
            print(f"\n  DUPLICADOS:")
            for i, dup in enumerate(duplicados, 1):
                print(f"    {i}. ID: {dup['_id']}")
                print(f"       Criado em: {dup.get('createdAt', 'N/A')}")
                print(f"       Casos: {len(dup.get('case_ids', []))}")
                print(f"       Clientes: {len(dup.get('clients', []))}")
        
        return {
            'total': len(processos_info),
            'duplicatas': processos_info,
            'original': original,
            'duplicados': duplicados,
            'numero_processo': numero_processo
        }
    
    except Exception as e:
        print(f"❌ ERRO ao identificar duplicatas: {e}")
        import traceback
        traceback.print_exc()
        raise


# =============================================================================
# PASSO 3: VALIDAÇÃO DE REFERÊNCIAS
# =============================================================================

def validar_referencias(duplicatas_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida referências antes de deletar duplicados.
    
    Args:
        duplicatas_info: Resultado de identificar_duplicatas()
    
    Returns:
        Dicionário com validação de referências
    """
    print("\n" + "="*80)
    print("PASSO 3: VALIDAÇÃO DE REFERÊNCIAS")
    print("="*80)
    
    try:
        original = duplicatas_info.get('original')
        duplicados = duplicatas_info.get('duplicados', [])
        
        if not original:
            print("⚠️  Nenhum processo original encontrado")
            return {'valido': False, 'motivo': 'Sem processo original'}
        
        validacao = {
            'original_id': original['_id'],
            'original_case_ids': original.get('case_ids', []),
            'original_clients': original.get('clients', []),
            'duplicados_referencias': [],
            'problemas': [],
            'valido': True
        }
        
        print(f"🔗 Validando referências do original (ID: {original['_id']})...")
        print(f"   Casos vinculados: {len(validacao['original_case_ids'])}")
        print(f"   Clientes: {len(validacao['original_clients'])}")
        
        # Verifica cada duplicado
        for dup in duplicados:
            dup_id = dup['_id']
            dup_case_ids = dup.get('case_ids', [])
            dup_clients = dup.get('clients', [])
            
            ref_info = {
                'duplicado_id': dup_id,
                'case_ids': dup_case_ids,
                'clients': dup_clients,
                'tem_referencias_unicas': False
            }
            
            # Verifica se duplicado tem referências que o original não tem
            casos_unicos = set(dup_case_ids) - set(validacao['original_case_ids'])
            clientes_unicos = set(dup_clients) - set(validacao['original_clients'])
            
            if casos_unicos or clientes_unicos:
                ref_info['tem_referencias_unicas'] = True
                ref_info['casos_unicos'] = list(casos_unicos)
                ref_info['clientes_unicos'] = list(clientes_unicos)
                validacao['problemas'].append(
                    f"Duplicado {dup_id} tem referências únicas: "
                    f"casos={list(casos_unicos)}, clientes={list(clientes_unicos)}"
                )
                validacao['valido'] = False
            
            validacao['duplicados_referencias'].append(ref_info)
        
        # Verifica referências em outras coleções
        print("\n🔍 Verificando referências em outras coleções...")
        
        # Verifica casos que referenciam este processo
        casos_ref = []
        for dup in [original] + duplicados:
            case_ids = dup.get('case_ids', [])
            for case_id in case_ids:
                try:
                    case_doc = db.collection('cases').document(case_id).get()
                    if case_doc.exists:
                        case_data = case_doc.to_dict()
                        process_ids = case_data.get('process_ids', [])
                        if dup['_id'] in process_ids:
                            casos_ref.append({
                                'case_id': case_id,
                                'case_title': case_data.get('title', ''),
                                'process_id': dup['_id']
                            })
                except Exception as e:
                    print(f"  ⚠️  Erro ao verificar caso {case_id}: {e}")
        
        validacao['casos_referenciando'] = casos_ref
        
        # Verifica acompanhamentos de terceiros
        acompanhamentos_ref = []
        try:
            acompanhamentos = db.collection('third_party_monitoring').stream()
            for ac in acompanhamentos:
                ac_data = ac.to_dict()
                link_processo = ac_data.get('link_do_processo') or ac_data.get('link', '')
                # Verifica se link referencia algum dos processos duplicados
                for dup in [original] + duplicados:
                    if dup['_id'] in link_processo or dup.get('numero', '') in link_processo:
                        acompanhamentos_ref.append({
                            'acompanhamento_id': ac.id,
                            'title': ac_data.get('title', ''),
                            'process_id': dup['_id']
                        })
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar acompanhamentos: {e}")
        
        validacao['acompanhamentos_referenciando'] = acompanhamentos_ref
        
        # Resumo
        print(f"\n📊 RESUMO DA VALIDAÇÃO:")
        print(f"  Válido para deleção: {'✅ SIM' if validacao['valido'] else '❌ NÃO'}")
        if validacao['problemas']:
            print(f"  ⚠️  Problemas encontrados:")
            for problema in validacao['problemas']:
                print(f"    - {problema}")
        print(f"  Casos referenciando: {len(validacao['casos_referenciando'])}")
        print(f"  Acompanhamentos referenciando: {len(validacao['acompanhamentos_referenciando'])}")
        
        return validacao
    
    except Exception as e:
        print(f"❌ ERRO ao validar referências: {e}")
        import traceback
        traceback.print_exc()
        return {'valido': False, 'erro': str(e)}


# =============================================================================
# PASSO 4: SOFT DELETE
# =============================================================================

def aplicar_soft_delete(duplicatas_info: Dict[str, Any], validacao: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica soft delete nos duplicados (marca isDeleted=true).
    
    Args:
        duplicatas_info: Resultado de identificar_duplicatas()
        validacao: Resultado de validar_referencias()
    
    Returns:
        Dicionário com resultado da operação
    """
    print("\n" + "="*80)
    print("PASSO 4: SOFT DELETE (Marcar para deleção)")
    print("="*80)
    
    if not validacao.get('valido', False):
        print("⚠️  Validação falhou. Não é seguro deletar.")
        print("   Problemas encontrados:")
        for problema in validacao.get('problemas', []):
            print(f"     - {problema}")
        resposta = input("\n   Deseja continuar mesmo assim? (sim/não): ").strip().lower()
        if resposta not in ['sim', 's', 'yes', 'y']:
            print("❌ Operação cancelada pelo usuário")
            return {'sucesso': False, 'motivo': 'Cancelado pelo usuário'}
    
    try:
        duplicados = duplicatas_info.get('duplicados', [])
        original = duplicatas_info.get('original')
        
        if not duplicados:
            print("✅ Nenhum duplicado para deletar")
            return {'sucesso': True, 'deletados': 0}
        
        print(f"🗑️  Aplicando soft delete em {len(duplicados)} duplicados...")
        print(f"   Mantendo original: {original['_id']}")
        
        timestamp_delecao = datetime.now().isoformat()
        deletados = []
        erros = []
        
        for dup in duplicados:
            dup_id = dup['_id']
            try:
                # Atualiza documento com campos de soft delete
                db.collection('processes').document(dup_id).update({
                    'isDeleted': True,
                    'deletedAt': timestamp_delecao,
                    'deletedReason': 'Deduplicação automática',
                    'originalProcessId': original['_id']
                })
                deletados.append(dup_id)
                print(f"  ✅ Marcado para deleção: {dup_id}")
            except Exception as e:
                erro_msg = f"Erro ao marcar {dup_id}: {e}"
                erros.append(erro_msg)
                print(f"  ❌ {erro_msg}")
        
        resultado = {
            'sucesso': len(erros) == 0,
            'total_duplicados': len(duplicados),
            'deletados': len(deletados),
            'ids_deletados': deletados,
            'erros': erros,
            'timestamp_delecao': timestamp_delecao,
            'original_id': original['_id']
        }
        
        print(f"\n📊 RESUMO:")
        print(f"  Total de duplicados: {len(duplicados)}")
        print(f"  Marcados para deleção: {len(deletados)}")
        print(f"  Erros: {len(erros)}")
        
        return resultado
    
    except Exception as e:
        print(f"❌ ERRO ao aplicar soft delete: {e}")
        import traceback
        traceback.print_exc()
        return {'sucesso': False, 'erro': str(e)}


# =============================================================================
# PASSO 6: DETECÇÃO DE OUTRAS DUPLICAÇÕES
# =============================================================================

def detectar_outras_duplicacoes() -> Dict[str, Any]:
    """
    Detecta outras duplicações na coleção 'processes'.
    
    Returns:
        Dicionário com todas as duplicações encontradas
    """
    print("\n" + "="*80)
    print("PASSO 6: DETECÇÃO DE OUTRAS DUPLICAÇÕES")
    print("="*80)
    
    try:
        print("🔍 Analisando todos os processos para detectar duplicações...")
        
        # Coleta todos os processos
        processes_ref = db.collection('processes')
        docs = list(processes_ref.stream())
        
        print(f"📊 Total de processos no banco: {len(docs)}")
        
        # Agrupa por número do processo
        por_numero = defaultdict(list)
        por_titulo = defaultdict(list)
        
        for doc in docs:
            data = doc.to_dict()
            # Tenta ambos os campos (numero e number)
            numero = data.get('numero', '') or data.get('number', '')
            titulo = data.get('title', '')
            
            if numero:
                por_numero[numero].append({
                    '_id': doc.id,
                    'title': titulo,
                    'numero': numero,
                    'createdAt': data.get('createdAt', '')
                })
            
            if titulo:
                por_titulo[titulo].append({
                    '_id': doc.id,
                    'title': titulo,
                    'numero': numero,
                    'createdAt': data.get('createdAt', '')
                })
        
        # Encontra duplicatas por número
        duplicatas_numero = {}
        for numero, processos in por_numero.items():
            if len(processos) > 1:
                duplicatas_numero[numero] = processos
        
        # Encontra duplicatas por título
        duplicatas_titulo = {}
        for titulo, processos in por_titulo.items():
            if len(processos) > 1:
                duplicatas_titulo[titulo] = processos
        
        resultado = {
            'total_processos': len(docs),
            'duplicatas_por_numero': duplicatas_numero,
            'duplicatas_por_titulo': duplicatas_titulo,
            'total_duplicatas_numero': len(duplicatas_numero),
            'total_duplicatas_titulo': len(duplicatas_titulo)
        }
        
        print(f"\n📊 RESUMO DE DUPLICAÇÕES:")
        print(f"  Total de processos: {len(docs)}")
        print(f"  Duplicatas por número: {len(duplicatas_numero)}")
        print(f"  Duplicatas por título: {len(duplicatas_titulo)}")
        
        if duplicatas_numero:
            print(f"\n  DUPLICAÇÕES POR NÚMERO:")
            for numero, processos in list(duplicatas_numero.items())[:10]:  # Mostra apenas 10 primeiros
                print(f"    {numero}: {len(processos)} cópias")
        
        if duplicatas_titulo:
            print(f"\n  DUPLICAÇÕES POR TÍTULO (primeiros 10):")
            for titulo, processos in list(duplicatas_titulo.items())[:10]:
                print(f"    '{titulo[:50]}...': {len(processos)} cópias")
        
        return resultado
    
    except Exception as e:
        print(f"❌ ERRO ao detectar outras duplicações: {e}")
        import traceback
        traceback.print_exc()
        return {'erro': str(e)}


# =============================================================================
# PASSO 7: INVESTIGAÇÃO DE CAUSA RAIZ
# =============================================================================

def investigar_causa_raiz(duplicatas_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Investiga a causa raiz da duplicação.
    
    Args:
        duplicatas_info: Resultado de identificar_duplicatas()
    
    Returns:
        Dicionário com análise da causa raiz
    """
    print("\n" + "="*80)
    print("PASSO 7: INVESTIGAÇÃO DE CAUSA RAIZ")
    print("="*80)
    
    try:
        duplicatas = duplicatas_info.get('duplicatas', [])
        original = duplicatas_info.get('original')
        
        if not duplicatas:
            return {'causa': 'Nenhuma duplicata encontrada'}
        
        # Analisa timestamps
        timestamps = []
        for dup in duplicatas:
            created = dup.get('createdAt', '')
            updated = dup.get('updatedAt', '')
            timestamps.append({
                '_id': dup['_id'],
                'createdAt': created,
                'updatedAt': updated
            })
        
        # Verifica se foram criados em momentos próximos (possível loop)
        timestamps_ordenados = sorted(timestamps, key=lambda x: x.get('createdAt', ''))
        
        # Analisa diferenças de tempo
        diferencas = []
        for i in range(1, len(timestamps_ordenados)):
            try:
                t1 = datetime.fromisoformat(timestamps_ordenados[i-1]['createdAt'].replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(timestamps_ordenados[i]['createdAt'].replace('Z', '+00:00'))
                diff = (t2 - t1).total_seconds()
                diferencas.append(diff)
            except:
                pass
        
        # Verifica scripts de backfill
        backfill_scripts = [
            'scripts/backfill_processes.py',
            'scripts/migrate_multiple_parent_processes.py',
            'migrate_to_firestore.py'
        ]
        
        scripts_encontrados = []
        for script in backfill_scripts:
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), script)
            if os.path.exists(script_path):
                scripts_encontrados.append(script)
        
        # Analisa dados dos processos
        dados_identicos = True
        if len(duplicatas) > 1:
            primeiro = duplicatas[0]['data']
            for dup in duplicatas[1:]:
                # Compara campos principais (ignorando _id, createdAt, updatedAt)
                campos_ignorar = ['_id', 'createdAt', 'updatedAt', 'id']
                primeiro_clean = {k: v for k, v in primeiro.items() if k not in campos_ignorar}
                dup_clean = {k: v for k, v in dup['data'].items() if k not in campos_ignorar}
                
                if primeiro_clean != dup_clean:
                    dados_identicos = False
                    break
        
        resultado = {
            'total_duplicatas': len(duplicatas),
            'timestamps': timestamps_ordenados,
            'diferencas_tempo_segundos': diferencas,
            'criados_rapidamente': any(d < 60 for d in diferencas) if diferencas else False,
            'scripts_backfill_encontrados': scripts_encontrados,
            'dados_identicos': dados_identicos,
            'possiveis_causas': []
        }
        
        # Determina possíveis causas
        if resultado['criados_rapidamente']:
            resultado['possiveis_causas'].append('Processos criados em rápida sucessão (possível loop ou requisição duplicada)')
        
        if scripts_encontrados:
            resultado['possiveis_causas'].append(f'Scripts de backfill encontrados: {", ".join(scripts_encontrados)}')
        
        if dados_identicos:
            resultado['possiveis_causas'].append('Dados idênticos entre duplicatas (cópia exata)')
        else:
            resultado['possiveis_causas'].append('Dados diferentes entre duplicatas (possível edição manual)')
        
        print(f"\n📊 ANÁLISE:")
        print(f"  Total de duplicatas: {len(duplicatas)}")
        print(f"  Dados idênticos: {'Sim' if dados_identicos else 'Não'}")
        print(f"  Criados rapidamente: {'Sim' if resultado['criados_rapidamente'] else 'Não'}")
        print(f"  Scripts de backfill: {len(scripts_encontrados)}")
        
        print(f"\n  POSSÍVEIS CAUSAS:")
        for causa in resultado['possiveis_causas']:
            print(f"    - {causa}")
        
        if diferencas:
            print(f"\n  DIFERENÇAS DE TEMPO ENTRE CRIAÇÕES:")
            for i, diff in enumerate(diferencas[:5], 1):
                print(f"    {i}. {diff:.2f} segundos")
        
        return resultado
    
    except Exception as e:
        print(f"❌ ERRO ao investigar causa raiz: {e}")
        import traceback
        traceback.print_exc()
        return {'erro': str(e)}


# =============================================================================
# PASSO 8: GERAÇÃO DE RELATÓRIO
# =============================================================================

def gerar_relatorio(
    backup_path: str,
    duplicatas_info: Dict[str, Any],
    validacao: Dict[str, Any],
    soft_delete_result: Dict[str, Any],
    outras_duplicatas: Dict[str, Any],
    causa_raiz: Dict[str, Any]
) -> str:
    """
    Gera relatório completo de deduplicação.
    
    Returns:
        Caminho do arquivo de relatório criado
    """
    print("\n" + "="*80)
    print("PASSO 8: GERAÇÃO DE RELATÓRIO")
    print("="*80)
    
    try:
        relatorio_filename = f"deduplication_report_{TIMESTAMP}.md"
        relatorio_path = os.path.join(BACKUP_DIR, relatorio_filename)
        
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            f.write(f"# Relatório de Deduplicação - Processos\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"**Timestamp:** {TIMESTAMP}\n\n")
            
            f.write("---\n\n")
            f.write("## 1. BACKUP\n\n")
            f.write(f"- **Arquivo:** `{backup_path}`\n")
            f.write(f"- **Total de processos:** {duplicatas_info.get('total', 0)}\n")
            f.write(f"- **Status:** ✅ Concluído\n\n")
            
            f.write("---\n\n")
            f.write("## 2. DUPLICATAS IDENTIFICADAS\n\n")
            f.write(f"- **Número do processo:** {duplicatas_info.get('numero_processo', 'N/A')}\n")
            f.write(f"- **Total encontrado:** {duplicatas_info.get('total', 0)}\n")
            f.write(f"- **Original (mantido):** {duplicatas_info.get('original', {}).get('_id', 'N/A')}\n")
            f.write(f"- **Duplicados:** {len(duplicatas_info.get('duplicados', []))}\n\n")
            
            if duplicatas_info.get('original'):
                orig = duplicatas_info['original']
                f.write(f"### Processo Original\n\n")
                f.write(f"- **ID:** `{orig['_id']}`\n")
                f.write(f"- **Título:** {orig.get('title', 'N/A')}\n")
                f.write(f"- **Criado em:** {orig.get('createdAt', 'N/A')}\n")
                f.write(f"- **Casos vinculados:** {len(orig.get('case_ids', []))}\n")
                f.write(f"- **Clientes:** {len(orig.get('clients', []))}\n\n")
            
            if duplicatas_info.get('duplicados'):
                f.write(f"### Processos Duplicados\n\n")
                for i, dup in enumerate(duplicatas_info['duplicados'], 1):
                    f.write(f"#### Duplicado {i}\n\n")
                    f.write(f"- **ID:** `{dup['_id']}`\n")
                    f.write(f"- **Criado em:** {dup.get('createdAt', 'N/A')}\n")
                    f.write(f"- **Casos:** {len(dup.get('case_ids', []))}\n")
                    f.write(f"- **Clientes:** {len(dup.get('clients', []))}\n\n")
            
            f.write("---\n\n")
            f.write("## 3. VALIDAÇÃO DE REFERÊNCIAS\n\n")
            f.write(f"- **Válido para deleção:** {'✅ Sim' if validacao.get('valido') else '❌ Não'}\n")
            f.write(f"- **Casos referenciando:** {len(validacao.get('casos_referenciando', []))}\n")
            f.write(f"- **Acompanhamentos referenciando:** {len(validacao.get('acompanhamentos_referenciando', []))}\n\n")
            
            if validacao.get('problemas'):
                f.write("### Problemas Encontrados\n\n")
                for problema in validacao['problemas']:
                    f.write(f"- ⚠️  {problema}\n")
                f.write("\n")
            
            f.write("---\n\n")
            f.write("## 4. SOFT DELETE\n\n")
            if soft_delete_result.get('sucesso'):
                f.write(f"- **Status:** ✅ Concluído\n")
                f.write(f"- **Total marcados:** {soft_delete_result.get('deletados', 0)}\n")
                f.write(f"- **Timestamp:** {soft_delete_result.get('timestamp_delecao', 'N/A')}\n\n")
                
                if soft_delete_result.get('ids_deletados'):
                    f.write("### IDs Marcados para Deleção\n\n")
                    for dup_id in soft_delete_result['ids_deletados']:
                        f.write(f"- `{dup_id}`\n")
                    f.write("\n")
            else:
                f.write(f"- **Status:** ❌ Falhou\n")
                f.write(f"- **Motivo:** {soft_delete_result.get('motivo', 'N/A')}\n\n")
            
            f.write("---\n\n")
            f.write("## 5. OUTRAS DUPLICAÇÕES DETECTADAS\n\n")
            f.write(f"- **Total de processos no banco:** {outras_duplicatas.get('total_processos', 0)}\n")
            f.write(f"- **Duplicatas por número:** {outras_duplicatas.get('total_duplicatas_numero', 0)}\n")
            f.write(f"- **Duplicatas por título:** {outras_duplicatas.get('total_duplicatas_titulo', 0)}\n\n")
            
            if outras_duplicatas.get('duplicatas_por_numero'):
                f.write("### Duplicatas por Número (Top 20)\n\n")
                sorted_dups = sorted(
                    outras_duplicatas['duplicatas_por_numero'].items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:20]
                for numero, processos in sorted_dups:
                    f.write(f"- **{numero}:** {len(processos)} cópias\n")
                f.write("\n")
            
            f.write("---\n\n")
            f.write("## 6. CAUSA RAIZ\n\n")
            f.write(f"- **Dados idênticos:** {'Sim' if causa_raiz.get('dados_identicos') else 'Não'}\n")
            f.write(f"- **Criados rapidamente:** {'Sim' if causa_raiz.get('criados_rapidamente') else 'Não'}\n")
            f.write(f"- **Scripts de backfill:** {len(causa_raiz.get('scripts_backfill_encontrados', []))}\n\n")
            
            if causa_raiz.get('possiveis_causas'):
                f.write("### Possíveis Causas\n\n")
                for causa in causa_raiz['possiveis_causas']:
                    f.write(f"- {causa}\n")
                f.write("\n")
            
            f.write("---\n\n")
            f.write("## 7. RECOMENDAÇÕES\n\n")
            f.write("1. **Implementar validação de duplicatas antes de salvar**\n")
            f.write("   - Verificar se processo com mesmo número já existe\n")
            f.write("   - Usar transações do Firestore para garantir atomicidade\n\n")
            f.write("2. **Adicionar índice único no campo 'numero'**\n")
            f.write("   - Prevenir duplicatas no nível do banco\n\n")
            f.write("3. **Revisar scripts de backfill**\n")
            f.write("   - Garantir idempotência (pode rodar múltiplas vezes sem duplicar)\n\n")
            f.write("4. **Implementar soft delete como padrão**\n")
            f.write("   - Filtrar processos deletados em todas as queries\n\n")
            f.write("5. **Monitorar criação de processos**\n")
            f.write("   - Adicionar logs para detectar criação duplicada\n\n")
        
        print(f"✅ Relatório gerado: {relatorio_path}")
        return relatorio_path
    
    except Exception as e:
        print(f"❌ ERRO ao gerar relatório: {e}")
        import traceback
        traceback.print_exc()
        raise


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """Executa processo completo de deduplicação."""
    print("\n" + "="*80)
    print("DEDUPLICAÇÃO EXTREMA - MÓDULO PROCESSOS")
    print("="*80)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    try:
        # PASSO 1: Backup
        backup_path = fazer_backup_processes()
        
        # PASSO 6: Detectar TODAS as duplicações primeiro
        print("\n🔍 Analisando TODAS as duplicações no banco...")
        outras_duplicatas = detectar_outras_duplicacoes()
        
        # PASSO 2: Identificar duplicatas específicas (se houver)
        # Tenta primeiro o processo mencionado
        duplicatas_info = identificar_duplicatas("PMSC/46545/2020")
        
        # Se não encontrou, processa a primeira duplicata encontrada na análise geral
        if duplicatas_info.get('total', 0) == 0 and outras_duplicatas.get('duplicatas_por_titulo'):
            print("\n⚠️  Processo específico não encontrado. Processando primeira duplicata encontrada...")
            # Pega a primeira duplicata por título
            primeira_dup = list(outras_duplicatas['duplicatas_por_titulo'].items())[0]
            titulo_dup = primeira_dup[0]
            processos_dup = primeira_dup[1]
            
            print(f"📋 Processando duplicatas do título: '{titulo_dup[:60]}...'")
            
            # Converte para formato esperado
            processos_info = []
            for p in processos_dup:
                doc_ref = db.collection('processes').document(p['_id'])
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    processos_info.append({
                        '_id': doc.id,
                        'title': data.get('title', ''),
                        'numero': data.get('numero', '') or data.get('number', ''),
                        'data_abertura': data.get('data_abertura', ''),
                        'status': data.get('status', ''),
                        'createdAt': data.get('createdAt', ''),
                        'updatedAt': data.get('updatedAt', ''),
                        'case_ids': data.get('case_ids', []),
                        'clients': data.get('clients', []),
                        'opposing_parties': data.get('opposing_parties', []),
                        'data': data
                    })
            
            processos_info.sort(key=lambda x: x.get('createdAt') or '')
            duplicatas_info = {
                'total': len(processos_info),
                'duplicatas': processos_info,
                'original': processos_info[0] if processos_info else None,
                'duplicados': processos_info[1:] if len(processos_info) > 1 else [],
                'numero_processo': titulo_dup
            }
        
        if duplicatas_info.get('total', 0) == 0:
            print("\n⚠️  Nenhuma duplicata encontrada para processar.")
            print("📊 Mas foram detectadas outras duplicações no banco (ver relatório)")
            # Gera relatório mesmo sem processar duplicatas específicas
            relatorio_path = gerar_relatorio(
                backup_path,
                {'total': 0, 'duplicatas': [], 'original': None, 'duplicados': []},
                {'valido': False, 'motivo': 'Nenhuma duplicata específica encontrada'},
                {'sucesso': False, 'motivo': 'Nenhuma duplicata para processar'},
                outras_duplicatas,
                {'causa': 'Análise geral realizada'}
            )
            return
        
        # PASSO 3: Validar referências
        validacao = validar_referencias(duplicatas_info)
        
        # PASSO 4: Soft delete
        soft_delete_result = aplicar_soft_delete(duplicatas_info, validacao)
        
        # PASSO 7: Investigar causa raiz
        causa_raiz = investigar_causa_raiz(duplicatas_info)
        
        # PASSO 8: Gerar relatório
        relatorio_path = gerar_relatorio(
            backup_path,
            duplicatas_info,
            validacao,
            soft_delete_result,
            outras_duplicatas,
            causa_raiz
        )
        
        print("\n" + "="*80)
        print("✅ DEDUPLICAÇÃO CONCLUÍDA")
        print("="*80)
        print(f"\n📁 Arquivos gerados:")
        print(f"  - Backup: {backup_path}")
        print(f"  - Relatório: {relatorio_path}")
        print(f"\n⚠️  PRÓXIMOS PASSOS:")
        print(f"  1. Revisar relatório em: {relatorio_path}")
        print(f"  2. Validar que soft delete funcionou corretamente")
        print(f"  3. Código já está atualizado para filtrar processos deletados")
        print(f"  4. Após 7 dias, considerar hard delete se tudo estiver OK")
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()

