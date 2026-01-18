"""
Script de migração de clientes do workspace Schmidmeier para Visão Geral.

Migra clientes da coleção "clients" para "vg_pessoas" com vinculação ao grupo
"Schmidmeier".
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
from mini_erp.pages.visao_geral.pessoas.database_grupo import buscar_grupo_por_nome
from mini_erp.pages.visao_geral.pessoas.database import criar_pessoa, buscar_pessoa_por_documento
from mini_erp.pages.visao_geral.pessoas.models import formatar_cpf, formatar_cnpj


# Diretório para salvar mapeamentos
MAPEAMENTOS_DIR = Path(__file__).parent.parent / 'migracoes'
MAPEAMENTOS_DIR.mkdir(exist_ok=True)


def extrair_digitos(valor: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    if not valor:
        return ''
    return ''.join(filter(str.isdigit, valor))


def converter_socio(socio_antigo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte estrutura de sócio do formato antigo para o novo.

    Args:
        socio_antigo: Sócio no formato antigo (partners)

    Returns:
        Sócio no formato novo (socios)
    """
    return {
        'full_name': socio_antigo.get('full_name', ''),
        'cpf': extrair_digitos(socio_antigo.get('cpf', '')),
        'participacao': socio_antigo.get('share', ''),
    }


def converter_vinculo(vinculo_antigo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte estrutura de vínculo do formato antigo para o novo.

    Args:
        vinculo_antigo: Vínculo no formato antigo (bonds)

    Returns:
        Vínculo no formato novo (vinculos)
    """
    # Extrai pessoa_id e pessoa_nome do campo 'person'
    person = vinculo_antigo.get('person', '')
    
    return {
        'pessoa_id': '',  # Será preenchido depois se necessário
        'pessoa_nome': person,
        'tipo': vinculo_antigo.get('type', ''),
    }


def converter_cliente_para_pessoa(
    cliente: Dict[str, Any],
    grupo_id: str,
    grupo_nome: str
) -> Dict[str, Any]:
    """
    Converte um cliente da coleção "clients" para formato "vg_pessoas".

    Args:
        cliente: Dicionário do cliente original
        grupo_id: ID do grupo Schmidmeier
        grupo_nome: Nome do grupo Schmidmeier

    Returns:
        Dicionário no formato vg_pessoas
    """
    # Extrai documento (CPF ou CNPJ)
    cpf = extrair_digitos(cliente.get('cpf', ''))
    cnpj = extrair_digitos(cliente.get('cnpj', ''))
    cpf_cnpj = cliente.get('cpf_cnpj', '') or cliente.get('document', '')
    if cpf_cnpj:
        cpf_cnpj = extrair_digitos(cpf_cnpj)
    
    # Determina tipo de pessoa
    tipo_pessoa = cliente.get('client_type', 'PF')
    if tipo_pessoa not in ['PF', 'PJ']:
        tipo_pessoa = 'PF'
    
    # Formata documento para exibição
    if tipo_pessoa == 'PJ' and cnpj:
        cpf_cnpj_formatado = formatar_cnpj(cnpj)
    elif cpf:
        cpf_cnpj_formatado = formatar_cpf(cpf)
    else:
        cpf_cnpj_formatado = cpf_cnpj
    
    # Converte sócios
    socios = []
    if cliente.get('partners'):
        socios = [converter_socio(s) for s in cliente.get('partners', [])]
    
    # Converte vínculos
    vinculos = []
    if cliente.get('bonds'):
        vinculos = [converter_vinculo(v) for v in cliente.get('bonds', [])]
    
    # Nome de exibição (prioridade: nome_exibicao > display_name > full_name)
    nome_exibicao = (
        cliente.get('nome_exibicao', '').strip() or
        cliente.get('display_name', '').strip() or
        cliente.get('full_name', '').strip() or
        cliente.get('name', '').strip()
    )
    
    # Monta pessoa no formato novo
    pessoa = {
        'full_name': cliente.get('full_name', '') or cliente.get('name', ''),
        'nome_exibicao': nome_exibicao,
        'apelido': cliente.get('nickname', ''),
        'tipo_pessoa': tipo_pessoa,
        'cpf': cpf,
        'cnpj': cnpj,
        'cpf_cnpj_formatado': cpf_cnpj_formatado,
        'email': cliente.get('email', ''),
        'telefone': cliente.get('phone', ''),
        'endereco': '',  # Campo não existe no modelo antigo
        'tipo_filial': cliente.get('branch_type', 'Matriz'),
        'socios': socios,
        'vinculos': vinculos,
        'grupo_id': grupo_id,
        'grupo_nome': grupo_nome,
        'categoria': 'cliente',
        'observacoes': '',
        'created_at': cliente.get('created_at'),
        'updated_at': datetime.now(),
    }
    
    return pessoa


def verificar_duplicata(cpf: str, cnpj: str) -> Optional[str]:
    """
    Verifica se já existe pessoa com mesmo CPF ou CNPJ.

    Args:
        cpf: CPF a verificar
        cnpj: CNPJ a verificar

    Returns:
        ID da pessoa existente ou None
    """
    try:
        # Busca por CPF
        if cpf:
            pessoa = buscar_pessoa_por_documento(cpf)
            if pessoa:
                return pessoa.get('_id')
        
        # Busca por CNPJ
        if cnpj:
            pessoa = buscar_pessoa_por_documento(cnpj)
            if pessoa:
                return pessoa.get('_id')
        
        return None
    except Exception as e:
        print(f"Erro ao verificar duplicata: {e}")
        return None


def salvar_mapeamento(mapeamento: Dict[str, str], timestamp: str):
    """
    Salva mapeamento de IDs em arquivo JSON.

    Args:
        mapeamento: Dicionário {id_antigo: id_novo}
        timestamp: Timestamp da migração
    """
    try:
        arquivo = MAPEAMENTOS_DIR / f'mapeamento_clientes_{timestamp}.json'
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'mapeamento': mapeamento,
                'total': len(mapeamento)
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ Mapeamento salvo em: {arquivo}")
    except Exception as e:
        print(f"⚠️  Erro ao salvar mapeamento: {e}")


def carregar_mapeamento(timestamp: str) -> Optional[Dict[str, str]]:
    """
    Carrega mapeamento de IDs de arquivo JSON.

    Args:
        timestamp: Timestamp da migração

    Returns:
        Dicionário de mapeamento ou None
    """
    try:
        arquivo = MAPEAMENTOS_DIR / f'mapeamento_clientes_{timestamp}.json'
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('mapeamento', {})
    except Exception as e:
        print(f"⚠️  Erro ao carregar mapeamento: {e}")
    return None


def migrar_clientes_schmidmeier(dry_run: bool = False) -> Dict[str, Any]:
    """
    Migra clientes da coleção "clients" para "vg_pessoas".

    Args:
        dry_run: Se True, apenas simula sem fazer alterações

    Returns:
        Dicionário com relatório da migração
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    relatorio = {
        'timestamp': timestamp,
        'dry_run': dry_run,
        'total_clientes': 0,
        'migrados': 0,
        'duplicados': 0,
        'erros': 0,
        'mapeamento': {},
        'detalhes': [],
    }
    
    try:
        db = get_db()
        if not db:
            relatorio['erros'] = 1
            relatorio['detalhes'].append({
                'tipo': 'erro',
                'mensagem': 'Conexão com Firebase não disponível'
            })
            return relatorio
        
        # 1. Busca ID do grupo Schmidmeier
        print("🔍 Buscando grupo 'Schmidmeier'...")
        grupo = buscar_grupo_por_nome('Schmidmeier')
        if not grupo:
            relatorio['erros'] = 1
            relatorio['detalhes'].append({
                'tipo': 'erro',
                'mensagem': 'Grupo "Schmidmeier" não encontrado. Execute a inicialização primeiro.'
            })
            return relatorio
        
        grupo_id = grupo._id
        grupo_nome = grupo.nome
        print(f"✅ Grupo encontrado: {grupo_nome} (ID: {grupo_id})")
        
        # 2. Lista todos os clientes da coleção "clients"
        print("\n📋 Listando clientes da coleção 'clients'...")
        docs = db.collection('clients').stream()
        clientes = []
        
        for doc in docs:
            cliente = doc.to_dict()
            cliente['_id'] = doc.id
            clientes.append(cliente)
        
        relatorio['total_clientes'] = len(clientes)
        print(f"✅ {len(clientes)} cliente(s) encontrado(s)")
        
        if not clientes:
            relatorio['detalhes'].append({
                'tipo': 'info',
                'mensagem': 'Nenhum cliente encontrado para migrar'
            })
            return relatorio
        
        # 3. Processa cada cliente
        print("\n🔄 Iniciando migração...")
        for cliente in clientes:
            cliente_id_antigo = cliente.get('_id', '')
            cliente_nome = cliente.get('full_name', '') or cliente.get('name', '')
            
            try:
                # Extrai documentos
                cpf = extrair_digitos(cliente.get('cpf', ''))
                cnpj = extrair_digitos(cliente.get('cnpj', ''))
                
                # Verifica duplicata
                pessoa_existente_id = verificar_duplicata(cpf, cnpj)
                if pessoa_existente_id:
                    relatorio['duplicados'] += 1
                    relatorio['detalhes'].append({
                        'tipo': 'duplicado',
                        'cliente': cliente_nome,
                        'id_antigo': cliente_id_antigo,
                        'id_existente': pessoa_existente_id,
                        'mensagem': f'Cliente "{cliente_nome}" já existe (ID: {pessoa_existente_id})'
                    })
                    print(f"⚠️  Duplicado: {cliente_nome}")
                    continue
                
                # Converte para formato novo
                pessoa = converter_cliente_para_pessoa(cliente, grupo_id, grupo_nome)
                
                if dry_run:
                    # Apenas simula
                    pessoa_id_novo = f"SIMULADO_{cliente_id_antigo}"
                    print(f"🔍 [DRY RUN] Migraria: {cliente_nome}")
                else:
                    # Cria pessoa
                    pessoa_id_novo = criar_pessoa(pessoa)
                    if not pessoa_id_novo:
                        raise Exception("Falha ao criar pessoa")
                    print(f"✅ Migrado: {cliente_nome} → {pessoa_id_novo}")
                
                # Salva mapeamento
                relatorio['mapeamento'][cliente_id_antigo] = pessoa_id_novo
                relatorio['migrados'] += 1
                relatorio['detalhes'].append({
                    'tipo': 'sucesso',
                    'cliente': cliente_nome,
                    'id_antigo': cliente_id_antigo,
                    'id_novo': pessoa_id_novo,
                    'mensagem': f'Cliente "{cliente_nome}" migrado com sucesso'
                })
                
            except Exception as e:
                relatorio['erros'] += 1
                relatorio['detalhes'].append({
                    'tipo': 'erro',
                    'cliente': cliente_nome,
                    'id_antigo': cliente_id_antigo,
                    'mensagem': f'Erro ao migrar: {str(e)}'
                })
                print(f"❌ Erro ao migrar {cliente_nome}: {e}")
                import traceback
                traceback.print_exc()
        
        # 4. Salva mapeamento
        if not dry_run and relatorio['mapeamento']:
            salvar_mapeamento(relatorio['mapeamento'], timestamp)
        
        # 5. Resumo
        print("\n" + "="*60)
        print("📊 RESUMO DA MIGRAÇÃO")
        print("="*60)
        print(f"Total de clientes: {relatorio['total_clientes']}")
        print(f"✅ Migrados: {relatorio['migrados']}")
        print(f"⚠️  Duplicados: {relatorio['duplicados']}")
        print(f"❌ Erros: {relatorio['erros']}")
        print("="*60)
        
    except Exception as e:
        relatorio['erros'] += 1
        relatorio['detalhes'].append({
            'tipo': 'erro',
            'mensagem': f'Erro geral: {str(e)}'
        })
        print(f"❌ Erro geral na migração: {e}")
        import traceback
        traceback.print_exc()
    
    return relatorio


def rollback_migracao(timestamp: str) -> bool:
    """
    Desfaz uma migração removendo os registros criados.

    Args:
        timestamp: Timestamp da migração a desfazer

    Returns:
        True se rollback bem-sucedido
    """
    try:
        db = get_db()
        if not db:
            print("❌ Conexão com Firebase não disponível")
            return False
        
        # Carrega mapeamento
        mapeamento = carregar_mapeamento(timestamp)
        if not mapeamento:
            print(f"❌ Mapeamento não encontrado para timestamp: {timestamp}")
            return False
        
        print(f"🔄 Iniciando rollback de {len(mapeamento)} registro(s)...")
        
        # Remove cada registro migrado
        removidos = 0
        for id_antigo, id_novo in mapeamento.items():
            try:
                if id_novo.startswith('SIMULADO_'):
                    continue  # Pula simulações
                
                db.collection('vg_pessoas').document(id_novo).delete()
                removidos += 1
                print(f"✅ Removido: {id_novo}")
            except Exception as e:
                print(f"⚠️  Erro ao remover {id_novo}: {e}")
        
        print(f"✅ Rollback concluído: {removidos} registro(s) removido(s)")
        return True
        
    except Exception as e:
        print(f"❌ Erro no rollback: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migra clientes do Schmidmeier')
    parser.add_argument('--dry-run', action='store_true', help='Apenas simula sem fazer alterações')
    parser.add_argument('--rollback', type=str, help='Timestamp da migração para desfazer')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migracao(args.rollback)
    else:
        relatorio = migrar_clientes_schmidmeier(dry_run=args.dry_run)
        print(f"\n📄 Relatório salvo com timestamp: {relatorio['timestamp']}")
















