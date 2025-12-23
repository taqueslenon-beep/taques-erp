#!/usr/bin/env python3
"""
Script de sincronização de processos já migrados.

Identifica processos já migrados manualmente na coleção vg_processos
e atualiza automaticamente seus status na coleção processos_migracao
de "pendente" para "migrado".

Uso:
    python3 scripts/sync_processos_migrados.py
"""
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

# Constantes
COLECAO_MIGRACAO = "processos_migracao"
COLECAO_PROCESSOS = "vg_processos"
MAX_BATCH_SIZE = 500


def normalizar_numero_processo(numero: str) -> str:
    """
    Normaliza número do processo para comparação.
    
    Remove TODOS os espaços, tabs e quebras de linha.
    Remove sufixos entre parênteses (ex: "(CNI02CV01)") que existem em processos_migracao
    mas não em vg_processos.
    
    Args:
        numero: Número do processo (pode ser None ou vazio)
        
    Returns:
        Número normalizado ou string vazia se inválido
        
    Exemplos:
        "5004642-42.2020.8.24.0015   (CNI02CV01)" → "5004642-42.2020.8.24.0015"
        "5004560-69.2024.8.24.0015" → "5004560-69.2024.8.24.0015"
    """
    if not numero:
        return ""
    
    # Converte para string e remove TODOS os espaços, tabs e quebras de linha
    numero_limpo = str(numero).strip().replace(' ', '').replace('\t', '').replace('\n', '')
    
    # Remove sufixo entre parênteses (ex: "(CNI02CV01)" ou "(RIN0201)")
    # Esses sufixos existem em processos_migracao mas não em vg_processos
    if '(' in numero_limpo:
        numero_limpo = numero_limpo.split('(')[0]
    
    # Remove espaços finais que possam ter sobrado e converte para uppercase
    # Uppercase garante comparação case-insensitive
    numero_limpo = numero_limpo.strip().upper()
    
    return numero_limpo


def buscar_processos_migrados() -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Busca todos os processos já migrados na coleção vg_processos.
    
    Extrai lista de números de processos (tenta campo 'numero' e 'numero_processo').
    
    Returns:
        Tupla: (lista de números normalizados, lista de documentos originais para debug)
    """
    print("\n[1/6] Buscando processos já migrados em vg_processos...")
    
    try:
        db = get_db()
        if not db:
            print("❌ Erro: Conexão com Firestore não disponível")
            return [], []
        
        # Busca todos os processos na coleção vg_processos
        docs = db.collection(COLECAO_PROCESSOS).stream()
        
        numeros = []
        documentos_originais = []
        documentos_sem_numero = 0
        
        for doc in docs:
            dados = doc.to_dict()
            
            # Tenta ambos os campos possíveis
            numero = dados.get('numero', '') or dados.get('numero_processo', '')
            
            if numero:
                numero_normalizado = normalizar_numero_processo(numero)
                if numero_normalizado:
                    numeros.append(numero_normalizado)
                    documentos_originais.append({
                        'id': doc.id,
                        'numero_original': numero,
                        'numero_normalizado': numero_normalizado,
                        'campos_disponiveis': list(dados.keys())[:10]  # Primeiros 10 campos
                    })
            else:
                documentos_sem_numero += 1
        
        print(f"✅ Encontrados {len(numeros)} processos em vg_processos")
        if documentos_sem_numero > 0:
            print(f"   ⚠️  {documentos_sem_numero} documentos sem número foram pulados")
        
        return numeros, documentos_originais
        
    except Exception as e:
        print(f"❌ Erro ao buscar processos migrados: {e}")
        import traceback
        traceback.print_exc()
        return [], []


def buscar_processos_migracao() -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """
    Busca todos os processos pendentes na coleção processos_migracao.
    
    Extrai números (campo 'numero_processo') e mapeia para document_id.
    Apenas busca processos com status 'pendente'.
    
    Returns:
        Tupla: (dicionário número → document_id, lista de documentos originais para debug)
    """
    print("\n[2/6] Buscando processos pendentes em processos_migracao...")
    
    try:
        db = get_db()
        if not db:
            print("❌ Erro: Conexão com Firestore não disponível")
            return {}, []
        
        # Busca apenas processos com status 'pendente'
        query = db.collection(COLECAO_MIGRACAO).where("status_migracao", "==", "pendente")
        docs = query.stream()
        
        processos_map = {}
        documentos_originais = []
        documentos_sem_numero = 0
        
        for doc in docs:
            dados = doc.to_dict()
            numero_processo = dados.get('numero_processo', '')
            
            if numero_processo:
                numero_normalizado = normalizar_numero_processo(numero_processo)
                if numero_normalizado:
                    processos_map[numero_normalizado] = doc.id
                    documentos_originais.append({
                        'id': doc.id,
                        'numero_original': numero_processo,
                        'numero_normalizado': numero_normalizado,
                        'campos_disponiveis': list(dados.keys())[:10]  # Primeiros 10 campos
                    })
            else:
                documentos_sem_numero += 1
        
        print(f"✅ Encontrados {len(processos_map)} processos pendentes em processos_migracao")
        if documentos_sem_numero > 0:
            print(f"   ⚠️  {documentos_sem_numero} documentos sem número foram pulados")
        
        return processos_map, documentos_originais
        
    except Exception as e:
        print(f"❌ Erro ao buscar processos de migração: {e}")
        import traceback
        traceback.print_exc()
        return {}, []


def exibir_debug_numeros(
    processos_migrados: List[str],
    processos_migracao: Dict[str, str],
    docs_vg: List[Dict[str, Any]],
    docs_migracao: List[Dict[str, Any]]
):
    """
    Exibe debug detalhado dos números para identificar diferenças.
    
    Args:
        processos_migrados: Lista de números normalizados de vg_processos
        processos_migracao: Dicionário de números normalizados de processos_migracao
        docs_vg: Documentos originais de vg_processos
        docs_migracao: Documentos originais de processos_migracao
    """
    print("\n" + "=" * 80)
    print("🔍 DEBUG - Amostra de Números")
    print("=" * 80)
    
    # Mostra primeiros 5 números de cada coleção
    print("\n📋 vg_processos (primeiros 5 números):")
    for idx, doc in enumerate(docs_vg[:5], 1):
        print(f"   {idx}. Original: '{doc['numero_original']}'")
        print(f"      Normalizado: '{doc['numero_normalizado']}'")
        print(f"      Campos disponíveis: {', '.join(doc['campos_disponiveis'])}")
    
    print("\n📋 processos_migracao (primeiros 5 números):")
    for idx, doc in enumerate(docs_migracao[:5], 1):
        print(f"   {idx}. Original: '{doc['numero_original']}'")
        print(f"      Normalizado: '{doc['numero_normalizado']}'")
        print(f"      Campos disponíveis: {', '.join(doc['campos_disponiveis'])}")
    
    # Comparação lado a lado
    print("\n" + "-" * 80)
    print("🔍 Comparação Lado a Lado (primeiros 10):")
    print("-" * 80)
    print(f"{'vg_processos':<40} | {'processos_migracao':<40}")
    print("-" * 80)
    
    # Pega primeiros 10 de cada
    vg_sample = processos_migrados[:10]
    migracao_sample = list(processos_migracao.keys())[:10]
    
    max_len = max(len(vg_sample), len(migracao_sample))
    for i in range(max_len):
        vg_num = vg_sample[i] if i < len(vg_sample) else ""
        mig_num = migracao_sample[i] if i < len(migracao_sample) else ""
        
        # Destaca se são iguais
        match_indicator = "✅" if vg_num and mig_num and vg_num == mig_num else "  "
        print(f"{match_indicator} {vg_num:<38} | {mig_num:<40}")
    
    # Verifica se há números em comum
    processos_migrados_set = set(processos_migrados)
    processos_migracao_set = set(processos_migracao.keys())
    
    em_comum = processos_migrados_set & processos_migracao_set
    apenas_vg = processos_migrados_set - processos_migracao_set
    apenas_migracao = processos_migracao_set - processos_migrados_set
    
    print("\n" + "-" * 80)
    print("📊 Estatísticas de Comparação:")
    print("-" * 80)
    print(f"   Números em comum: {len(em_comum)}")
    print(f"   Apenas em vg_processos: {len(apenas_vg)}")
    print(f"   Apenas em processos_migracao: {len(apenas_migracao)}")
    
    if len(em_comum) > 0:
        print(f"\n   ✅ Exemplos de números em comum (primeiros 5):")
        for num in list(em_comum)[:5]:
            print(f"      - {num}")
    
    if len(apenas_vg) > 0:
        print(f"\n   ⚠️  Exemplos de números apenas em vg_processos (primeiros 5):")
        for num in list(apenas_vg)[:5]:
            print(f"      - {num}")
    
    if len(apenas_migracao) > 0:
        print(f"\n   ⚠️  Exemplos de números apenas em processos_migracao (primeiros 5):")
        for num in list(apenas_migracao)[:5]:
            print(f"      - {num}")
    
    print("=" * 80)


def comparar_processos(
    processos_migrados: List[str], 
    processos_migracao: Dict[str, str],
    docs_vg: List[Dict[str, Any]],
    docs_migracao: List[Dict[str, Any]]
) -> List[Tuple[str, str]]:
    """
    Compara números normalizados entre as duas coleções.
    
    Identifica quais processos da planilha de migração já existem
    no sistema (foram migrados manualmente).
    
    Args:
        processos_migrados: Lista de números de processos já migrados
        processos_migracao: Dicionário número → document_id dos processos pendentes
        docs_vg: Documentos originais de vg_processos para debug
        docs_migracao: Documentos originais de processos_migracao para debug
        
    Returns:
        Lista de tuplas (numero_processo, document_id) dos matches
    """
    print("\n[3/6] Comparando processos para identificar matches...")
    
    # Exibe debug antes de comparar
    exibir_debug_numeros(processos_migrados, processos_migracao, docs_vg, docs_migracao)
    
    matches = []
    processos_migrados_set = set(processos_migrados)
    
    for numero_normalizado, document_id in processos_migracao.items():
        if numero_normalizado in processos_migrados_set:
            matches.append((numero_normalizado, document_id))
    
    print(f"\n✅ Encontrados {len(matches)} processos que já foram migrados manualmente")
    return matches


def fazer_backup_colecao() -> Optional[str]:
    """
    Exporta todos os documentos de processos_migracao para arquivo JSON.
    
    Cria backup antes de fazer atualizações em lote.
    
    Returns:
        Caminho do arquivo de backup criado ou None se falhar
    """
    print("\n[4/6] Fazendo backup da coleção processos_migracao...")
    
    try:
        db = get_db()
        if not db:
            print("❌ Erro: Conexão com Firestore não disponível")
            return None
        
        # Busca todos os documentos
        docs = db.collection(COLECAO_MIGRACAO).stream()
        
        backup_data = []
        for doc in docs:
            dados = doc.to_dict()
            # Converte timestamps para string ISO
            for key, value in dados.items():
                if hasattr(value, 'isoformat'):
                    dados[key] = value.isoformat()
            
            backup_data.append({
                'id': doc.id,
                'data': dados
            })
        
        # Cria diretório backups se não existir
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Gera nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'processos_migracao_backup_{timestamp}.json')
        
        # Salva backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup criado: {backup_file}")
        print(f"   Total de documentos no backup: {len(backup_data)}")
        return backup_file
        
    except Exception as e:
        print(f"❌ Erro ao fazer backup: {e}")
        import traceback
        traceback.print_exc()
        return None


def atualizar_status_em_lote(
    matches: List[Tuple[str, str]], 
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Atualiza status de processos em lote usando batch write.
    
    Para cada match:
    - Atualiza status_migracao = "migrado"
    - Adiciona data_migracao = datetime.now()
    - Adiciona migrado_manualmente = True
    
    Args:
        matches: Lista de tuplas (numero_processo, document_id)
        dry_run: Se True, apenas simula sem fazer atualizações
        
    Returns:
        Dicionário com estatísticas da atualização
    """
    print(f"\n[5/6] {'[DRY RUN] ' if dry_run else ''}Atualizando status em lote...")
    
    if not matches:
        print("⚠️  Nenhum processo para atualizar")
        return {
            'total': 0,
            'atualizados': 0,
            'erros': 0,
            'erros_detalhes': []
        }
    
    stats = {
        'total': len(matches),
        'atualizados': 0,
        'erros': 0,
        'erros_detalhes': []
    }
    
    if dry_run:
        print(f"   [SIMULAÇÃO] Seriam atualizados {len(matches)} processos")
        stats['atualizados'] = len(matches)
        return stats
    
    try:
        db = get_db()
        if not db:
            print("❌ Erro: Conexão com Firestore não disponível")
            return stats
        
        # Divide em batches de até 500 documentos
        batches = []
        for i in range(0, len(matches), MAX_BATCH_SIZE):
            batches.append(matches[i:i + MAX_BATCH_SIZE])
        
        print(f"   Processando {len(batches)} batch(es) de atualização...")
        
        for batch_idx, batch in enumerate(batches, 1):
            try:
                batch_write = db.batch()
                
                for numero_processo, document_id in batch:
                    ref = db.collection(COLECAO_MIGRACAO).document(document_id)
                    batch_write.update(ref, {
                        'status_migracao': 'migrado',
                        'data_migracao': datetime.now(),
                        'migrado_manualmente': True,
                        'atualizado_em': datetime.now()
                    })
                
                # Commit do batch
                batch_write.commit()
                stats['atualizados'] += len(batch)
                print(f"   ✅ Batch {batch_idx}/{len(batches)}: {len(batch)} processos atualizados")
                
            except Exception as e:
                print(f"   ❌ Erro no batch {batch_idx}: {e}")
                stats['erros'] += len(batch)
                stats['erros_detalhes'].append({
                    'batch': batch_idx,
                    'erro': str(e),
                    'processos': batch
                })
        
        print(f"\n✅ Atualização concluída:")
        print(f"   Total atualizado: {stats['atualizados']}")
        print(f"   Erros: {stats['erros']}")
        
        return stats
        
    except Exception as e:
        print(f"❌ Erro ao atualizar status em lote: {e}")
        import traceback
        traceback.print_exc()
        stats['erros'] = len(matches)
        return stats


def gerar_relatorio(
    processos_migrados: List[str],
    processos_pendentes: int,
    matches: List[Tuple[str, str]],
    stats: Dict[str, Any],
    backup_file: Optional[str]
) -> Optional[str]:
    """
    Cria arquivo de log detalhado com informações da sincronização.
    
    Args:
        processos_migrados: Lista de processos encontrados em vg_processos
        processos_pendentes: Quantidade de processos pendentes
        matches: Lista de matches encontrados
        stats: Estatísticas da atualização
        backup_file: Caminho do arquivo de backup
        
    Returns:
        Caminho do arquivo de relatório criado ou None se falhar
    """
    print("\n[6/6] Gerando relatório...")
    
    try:
        # Cria diretório logs se não existir
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Gera nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'migracao_sync_{timestamp}.txt')
        
        # Prepara conteúdo do relatório
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("RELATÓRIO DE SINCRONIZAÇÃO DE PROCESSOS MIGRADOS")
        relatorio.append("=" * 80)
        relatorio.append("")
        relatorio.append(f"Data/Hora da Execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append("")
        relatorio.append("-" * 80)
        relatorio.append("ESTATÍSTICAS")
        relatorio.append("-" * 80)
        relatorio.append(f"Processos encontrados em vg_processos: {len(processos_migrados)}")
        relatorio.append(f"Processos pendentes em processos_migracao: {processos_pendentes}")
        relatorio.append(f"Matches encontrados: {len(matches)}")
        relatorio.append("")
        relatorio.append("-" * 80)
        relatorio.append("RESULTADO DA ATUALIZAÇÃO")
        relatorio.append("-" * 80)
        relatorio.append(f"Total de processos atualizados: {stats.get('atualizados', 0)}")
        relatorio.append(f"Total de erros: {stats.get('erros', 0)}")
        relatorio.append("")
        
        if backup_file:
            relatorio.append(f"Arquivo de backup: {backup_file}")
            relatorio.append("")
        
        if matches:
            relatorio.append("-" * 80)
            relatorio.append("PROCESSOS ATUALIZADOS")
            relatorio.append("-" * 80)
            for idx, (numero, doc_id) in enumerate(matches, 1):
                relatorio.append(f"{idx:3d}. {numero} (ID: {doc_id})")
            relatorio.append("")
        
        if stats.get('erros_detalhes'):
            relatorio.append("-" * 80)
            relatorio.append("ERROS DETALHADOS")
            relatorio.append("-" * 80)
            for erro in stats['erros_detalhes']:
                relatorio.append(f"Batch {erro['batch']}: {erro['erro']}")
            relatorio.append("")
        
        relatorio.append("=" * 80)
        relatorio.append("FIM DO RELATÓRIO")
        relatorio.append("=" * 80)
        
        # Salva relatório
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(relatorio))
        
        print(f"✅ Relatório criado: {log_file}")
        return log_file
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Função principal do script.
    
    Executa o fluxo completo de sincronização:
    1. Busca processos migrados
    2. Busca processos pendentes na migração
    3. Compara e identifica matches
    4. Exibe preview e solicita confirmação
    5. Faz backup da coleção
    6. Executa atualização em lote
    7. Gera relatório
    8. Exibe resumo
    """
    print("=" * 80)
    print("SINCRONIZAÇÃO DE PROCESSOS JÁ MIGRADOS")
    print("=" * 80)
    print("\nEste script identifica processos já migrados manualmente")
    print("e atualiza seus status na planilha de migração.")
    print("")
    
    # Valida conexão
    db = get_db()
    if not db:
        print("❌ Erro: Não foi possível conectar ao Firestore")
        print("   Verifique as credenciais e configurações do Firebase")
        return
    
    # 1. Busca processos migrados
    processos_migrados, docs_vg = buscar_processos_migrados()
    if not processos_migrados:
        print("\n⚠️  Nenhum processo encontrado em vg_processos")
        print("   Verifique se a coleção está correta e possui dados")
        return
    
    # 2. Busca processos pendentes na migração
    processos_migracao, docs_migracao = buscar_processos_migracao()
    if not processos_migracao:
        print("\n⚠️  Nenhum processo pendente encontrado em processos_migracao")
        print("   Todos os processos já podem estar migrados")
        return
    
    # 3. Compara e identifica matches (com debug)
    matches = comparar_processos(processos_migrados, processos_migracao, docs_vg, docs_migracao)
    if not matches:
        print("\n✅ Nenhum processo para atualizar")
        print("   Todos os processos pendentes ainda não foram migrados manualmente")
        return
    
    # 4. Preview e confirmação
    print("\n" + "=" * 80)
    print("PREVIEW DA ATUALIZAÇÃO")
    print("=" * 80)
    print(f"\nEncontrados {len(matches)} processos que já foram migrados manualmente")
    print(f"Esses processos terão seu status atualizado de 'pendente' para 'migrado'")
    print("\nPrimeiros 10 processos que serão atualizados:")
    for idx, (numero, _) in enumerate(matches[:10], 1):
        print(f"  {idx:2d}. {numero}")
    if len(matches) > 10:
        print(f"  ... e mais {len(matches) - 10} processos")
    
    print("\n" + "=" * 80)
    resposta = input(f"\nAtualizar {len(matches)} processos? (s/n): ").strip().lower()
    
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("\n❌ Operação cancelada pelo usuário")
        return
    
    # 5. Faz backup
    backup_file = fazer_backup_colecao()
    if not backup_file:
        print("\n⚠️  ATENÇÃO: Backup não foi criado!")
        resposta_backup = input("Deseja continuar mesmo assim? (s/n): ").strip().lower()
        if resposta_backup not in ['s', 'sim', 'y', 'yes']:
            print("\n❌ Operação cancelada - backup é recomendado")
            return
    
    # 6. Executa atualização em lote
    stats = atualizar_status_em_lote(matches, dry_run=False)
    
    # 7. Gera relatório
    log_file = gerar_relatorio(
        processos_migrados,
        len(processos_migracao),
        matches,
        stats,
        backup_file
    )
    
    # 8. Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DA SINCRONIZAÇÃO")
    print("=" * 80)
    print(f"✅ Processos atualizados: {stats['atualizados']}")
    print(f"{'✅' if stats['erros'] == 0 else '⚠️ '} Erros: {stats['erros']}")
    if backup_file:
        print(f"📦 Backup: {backup_file}")
    if log_file:
        print(f"📄 Relatório: {log_file}")
    print("\n✅ Sincronização concluída!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

