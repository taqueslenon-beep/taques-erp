"""
Script de migração de outros envolvidos do workspace Schmidmeier para Visão Geral.

Migra envolvidos da coleção "opposing_parties" para "vg_envolvidos".
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mini_erp.firebase_config import get_db
from mini_erp.pages.visao_geral.pessoas.database import criar_envolvido, listar_envolvidos


# Diretório para salvar mapeamentos
MAPEAMENTOS_DIR = Path(__file__).parent.parent / 'migracoes'
MAPEAMENTOS_DIR.mkdir(exist_ok=True)


def extrair_digitos(valor: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    if not valor:
        return ''
    return ''.join(filter(str.isdigit, valor))


def mapear_tipo_envolvido(tipo_antigo: str) -> str:
    """
    Mapeia tipo de envolvido do formato antigo para o novo.

    Args:
        tipo_antigo: Tipo no formato antigo (PF, PJ, Órgão Público)

    Returns:
        Tipo no formato novo (PF, PJ, Ente Público, Advogado, Técnico)
    """
    mapeamento = {
        'PF': 'PF',
        'PJ': 'PJ',
        'Órgão Público': 'Ente Público',
        'Ente Público': 'Ente Público',
        'Advogado': 'Advogado',
        'Técnico': 'Técnico',
    }
    return mapeamento.get(tipo_antigo, 'PF')


def converter_envolvido_para_novo_formato(
    envolvido_antigo: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Converte um envolvido da coleção "opposing_parties" para formato "vg_envolvidos".

    Args:
        envolvido_antigo: Dicionário do envolvido original

    Returns:
        Dicionário no formato vg_envolvidos
    """
    # Extrai nome completo
    nome_completo = (
        envolvido_antigo.get('full_name', '') or
        envolvido_antigo.get('name', '') or
        ''
    ).strip()
    
    # Extrai nome de exibição
    nome_exibicao = (
        envolvido_antigo.get('nome_exibicao', '') or
        envolvido_antigo.get('display_name', '') or
        nome_completo or
        'Sem nome'
    ).strip()
    
    # Extrai CPF/CNPJ
    cpf_cnpj = extrair_digitos(
        envolvido_antigo.get('cpf_cnpj', '') or
        envolvido_antigo.get('document', '') or
        ''
    )
    
    # Extrai email
    email = envolvido_antigo.get('email', '').strip()
    
    # Extrai telefone
    telefone = envolvido_antigo.get('telefone', '') or envolvido_antigo.get('phone', '')
    telefone = telefone.strip() if telefone else ''
    
    # Mapeia tipo de envolvido
    tipo_antigo = envolvido_antigo.get('entity_type', '') or envolvido_antigo.get('type', '') or envolvido_antigo.get('client_type', '')
    tipo_envolvido = mapear_tipo_envolvido(tipo_antigo)
    
    # Extrai observações
    observacoes = envolvido_antigo.get('observacoes', '') or envolvido_antigo.get('observations', '')
    observacoes = observacoes.strip() if observacoes else ''
    
    # Constrói dicionário no formato novo
    novo_envolvido = {
        'nome_completo': nome_completo,
        'nome_exibicao': nome_exibicao,
        'cpf_cnpj': cpf_cnpj,
        'email': email,
        'telefone': telefone,
        'tipo_envolvido': tipo_envolvido,
        'observacoes': observacoes,
    }
    
    return novo_envolvido


def verificar_duplicata(envolvido: Dict[str, Any], envolvidos_existentes: List[Dict[str, Any]]) -> Optional[str]:
    """
    Verifica se já existe um envolvido com mesmo nome ou CPF/CNPJ.

    Args:
        envolvido: Dicionário do envolvido a verificar
        envolvidos_existentes: Lista de envolvidos já existentes

    Returns:
        ID do envolvido duplicado ou None
    """
    nome_completo = envolvido.get('nome_completo', '').strip().lower()
    nome_exibicao = envolvido.get('nome_exibicao', '').strip().lower()
    cpf_cnpj = envolvido.get('cpf_cnpj', '').strip()
    
    for existente in envolvidos_existentes:
        # Verifica por nome completo
        nome_existente = existente.get('nome_completo', '').strip().lower()
        if nome_completo and nome_existente and nome_completo == nome_existente:
            return existente.get('_id')
        
        # Verifica por nome de exibição
        nome_exib_existente = existente.get('nome_exibicao', '').strip().lower()
        if nome_exibicao and nome_exib_existente and nome_exibicao == nome_exib_existente:
            return existente.get('_id')
        
        # Verifica por CPF/CNPJ (se ambos tiverem)
        cpf_cnpj_existente = existente.get('cpf_cnpj', '').strip()
        if cpf_cnpj and cpf_cnpj_existente and cpf_cnpj == cpf_cnpj_existente:
            return existente.get('_id')
    
    return None


def salvar_mapeamento(mapeamento: Dict[str, str], timestamp: str):
    """
    Salva mapeamento de IDs em arquivo JSON.

    Args:
        mapeamento: Dicionário {id_antigo: id_novo}
        timestamp: Timestamp da migração
    """
    arquivo = MAPEAMENTOS_DIR / f'mapeamento_envolvidos_{timestamp}.json'
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(mapeamento, f, indent=2, ensure_ascii=False)
    print(f"✅ Mapeamento salvo em: {arquivo}")


def carregar_mapeamento(timestamp: str) -> Optional[Dict[str, str]]:
    """
    Carrega mapeamento de IDs de um arquivo JSON.

    Args:
        timestamp: Timestamp da migração

    Returns:
        Dicionário {id_antigo: id_novo} ou None
    """
    arquivo = MAPEAMENTOS_DIR / f'mapeamento_envolvidos_{timestamp}.json'
    if not arquivo.exists():
        return None
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar mapeamento: {e}")
        return None


def migrar_envolvidos_schmidmeier(
    lista_envolvidos: List[Dict[str, Any]],
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migra lista de envolvidos do Schmidmeier para Visão Geral.

    Args:
        lista_envolvidos: Lista de envolvidos já editados pelo usuário
        dry_run: Se True, apenas simula a migração sem salvar

    Returns:
        Dicionário com resultado da migração
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    mapeamento = {}
    detalhes = []
    
    # Carrega envolvidos existentes para verificar duplicatas
    envolvidos_existentes = listar_envolvidos()
    
    total = len(lista_envolvidos)
    migrados = 0
    duplicados = 0
    erros = 0
    
    print(f"\n{'='*60}")
    print(f"🚀 INICIANDO MIGRAÇÃO DE ENVOLVIDOS")
    print(f"{'='*60}")
    print(f"Total de envolvidos para migrar: {total}")
    print(f"Modo: {'SIMULAÇÃO' if dry_run else 'REAL'}\n")
    
    for idx, envolvido_antigo in enumerate(lista_envolvidos, 1):
        try:
            # Converte para novo formato
            novo_envolvido = converter_envolvido_para_novo_formato(envolvido_antigo)
            
            # Verifica duplicata
            duplicado_id = verificar_duplicata(novo_envolvido, envolvidos_existentes)
            if duplicado_id:
                duplicados += 1
                detalhes.append({
                    'tipo': 'duplicado',
                    'nome': novo_envolvido.get('nome_exibicao', 'Sem nome'),
                    'mensagem': f'Já existe envolvido com mesmo nome/CPF/CNPJ (ID: {duplicado_id})'
                })
                print(f"⚠️  [{idx}/{total}] DUPLICADO: {novo_envolvido.get('nome_exibicao', 'Sem nome')}")
                continue
            
            # Salva no Firebase (se não for dry_run)
            if not dry_run:
                novo_id = criar_envolvido(novo_envolvido)
                if novo_id:
                    mapeamento[envolvido_antigo.get('_id', '')] = novo_id
                    envolvidos_existentes.append({**novo_envolvido, '_id': novo_id})
                    migrados += 1
                    detalhes.append({
                        'tipo': 'sucesso',
                        'nome': novo_envolvido.get('nome_exibicao', 'Sem nome'),
                        'mensagem': f'Migrado com sucesso (ID: {novo_id})'
                    })
                    print(f"✅ [{idx}/{total}] MIGRADO: {novo_envolvido.get('nome_exibicao', 'Sem nome')} → ID: {novo_id}")
                else:
                    erros += 1
                    detalhes.append({
                        'tipo': 'erro',
                        'nome': novo_envolvido.get('nome_exibicao', 'Sem nome'),
                        'mensagem': 'Erro ao criar envolvido no Firebase'
                    })
                    print(f"❌ [{idx}/{total}] ERRO: {novo_envolvido.get('nome_exibicao', 'Sem nome')}")
            else:
                # Simulação
                migrados += 1
                detalhes.append({
                    'tipo': 'simulacao',
                    'nome': novo_envolvido.get('nome_exibicao', 'Sem nome'),
                    'mensagem': 'Simulação - seria migrado'
                })
                print(f"🔵 [{idx}/{total}] SIMULAÇÃO: {novo_envolvido.get('nome_exibicao', 'Sem nome')}")
        
        except Exception as e:
            erros += 1
            nome = envolvido_antigo.get('full_name', '') or envolvido_antigo.get('name', '') or 'Desconhecido'
            detalhes.append({
                'tipo': 'erro',
                'nome': nome,
                'mensagem': f'Erro ao processar: {str(e)}'
            })
            print(f"❌ [{idx}/{total}] ERRO: {nome} - {str(e)}")
    
    # Salva mapeamento (se não for dry_run e houver migrados)
    if not dry_run and mapeamento:
        salvar_mapeamento(mapeamento, timestamp)
    
    resultado = {
        'timestamp': timestamp,
        'total': total,
        'migrados': migrados,
        'duplicados': duplicados,
        'erros': erros,
        'mapeamento': mapeamento,
        'detalhes': detalhes,
    }
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMO DA MIGRAÇÃO")
    print(f"{'='*60}")
    print(f"Total processado: {total}")
    print(f"✅ Migrados: {migrados}")
    print(f"⚠️  Duplicados: {duplicados}")
    print(f"❌ Erros: {erros}")
    print(f"{'='*60}\n")
    
    return resultado


def rollback_migracao(timestamp: str) -> bool:
    """
    Desfaz uma migração removendo os registros criados.

    Args:
        timestamp: Timestamp da migração a desfazer

    Returns:
        True se rollback foi bem-sucedido, False caso contrário
    """
    try:
        mapeamento = carregar_mapeamento(timestamp)
        if not mapeamento:
            print(f"❌ Mapeamento não encontrado para timestamp: {timestamp}")
            return False
        
        db = get_db()
        if not db:
            print("❌ Erro: Conexão com Firebase não disponível")
            return False
        
        removidos = 0
        for novo_id in mapeamento.values():
            try:
                db.collection('vg_envolvidos').document(novo_id).delete()
                removidos += 1
                print(f"✅ Removido: {novo_id}")
            except Exception as e:
                print(f"⚠️  Erro ao remover {novo_id}: {e}")
        
        print(f"\n✅ Rollback concluído: {removidos} registros removidos")
        return True
    
    except Exception as e:
        print(f"❌ Erro no rollback: {e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migra envolvidos do Schmidmeier para Visão Geral')
    parser.add_argument('--dry-run', action='store_true', help='Apenas simula a migração')
    args = parser.parse_args()
    
    # Para uso via CLI, precisaria carregar da coleção original
    # Aqui apenas demonstra o uso
    print("⚠️  Este script deve ser usado via interface web ou passando lista de envolvidos editados")
    print("Use: migrar_envolvidos_schmidmeier(lista_envolvidos, dry_run=False)")




