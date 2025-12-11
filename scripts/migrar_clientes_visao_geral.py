#!/usr/bin/env python3
"""
Script de migração para importar clientes na coleção vg_pessoas do Firebase.

Workspace: "Visão geral do escritório"
Coleção Firebase: vg_pessoas

Uso:
    # Simular (não salva):
    python scripts/migrar_clientes_visao_geral.py --dry-run

    # Executar migração real:
    python scripts/migrar_clientes_visao_geral.py
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_erp.firebase_config import get_db

# =============================================================================
# LISTA DE CLIENTES PARA IMPORTAR (110 clientes)
# =============================================================================

CLIENTES_PARA_IMPORTAR = [
    # Página 1
    {"nome": "MARCELO NIEZELSKI", "tipo": "PF"},
    {"nome": "ANTONIO ROBERTO DE OLIVEIRA", "tipo": "PF"},
    {"nome": "LÚCIA BELITZ", "tipo": "PF"},
    {"nome": "CLEBER FRIDRICH", "tipo": "PF"},
    {"nome": "JOAO CARLOS MACIEL DA SILVA", "tipo": "PF"},
    {"nome": "ALBERTO SCHOSTAK", "tipo": "PF"},
    {"nome": "JOSÉ LUIS MACIEL DA SILVA", "tipo": "PF"},
    {"nome": "ADIR GONTAREK", "tipo": "PF"},
    {"nome": "JHONNY SCHMIDMEIER", "tipo": "PF"},
    {"nome": "FRANCISCO DEMARTINI", "tipo": "PF"},
    {"nome": "RICARDO JOSÉ TEIXEIRA", "tipo": "PF"},
    {"nome": "EVANDRO DO NASCIMENTO", "tipo": "PF"},
    {"nome": "REFLORESTA IMÓVEIS LTDA - MATRIZ", "tipo": "PJ"},
    {"nome": "AZ MARTELINHO DE OURO", "tipo": "PJ"},
    {"nome": "MARIA TRINDADE NEVES", "tipo": "PF"},
    {"nome": "MARIA TERESINHA SCHROEDER", "tipo": "PF"},
    {"nome": "CARLOS AUGUSTO PAPES", "tipo": "PF"},
    {"nome": "LUCIANE SCHMIDMEIER", "tipo": "PF"},
    {"nome": "ADRIANO BLASKOSKI", "tipo": "PF"},
    {"nome": "FLAVIO CAVALHEIRO", "tipo": "PF"},
    {"nome": "JOCEL IMÓVEIS LTDA", "tipo": "PJ"},
    {"nome": "LUCIANO KOZOWSKI", "tipo": "PF"},
    {"nome": "MUNICÍPIO DE MONTE CASTELO", "tipo": "PJ"},
    {"nome": "LUIS BENEDITO BITTENCOURT PACHECO DE MIRANDA", "tipo": "PF"},
    {"nome": "LENON GUSTAVO BATISTA TAQUES", "tipo": "PF"},
    {"nome": "ANDERSON TITON", "tipo": "PF"},
    # Página 2
    {"nome": "RENATO JARDEL GURTINSKI", "tipo": "PF"},
    {"nome": "CAPITAL MATE INDÚSTRIA E COMÉRCIO LTDA ME", "tipo": "PJ"},
    {"nome": "ANDRÉ DA SILVEIRA", "tipo": "PF"},
    {"nome": "OSEIAS JAREMCZUK", "tipo": "PF"},
    {"nome": "SILMAR VOREL", "tipo": "PF"},
    {"nome": "RIVELINO BORSATO", "tipo": "PF"},
    {"nome": "MARCOS DIEGO ANDRE TONIAL", "tipo": "PF"},
    {"nome": "CARMEN LÚCIA POLONINSKI IARROCHESKI", "tipo": "PF"},
    {"nome": "VALDEMAR BECKER", "tipo": "PF"},
    {"nome": "K CUBAS EMPREENDIMENTOS IMOBILIÁRIOS", "tipo": "PJ"},
    {"nome": "KARYNA CUBAS BATISTA FREITAS", "tipo": "PF"},
    {"nome": "AMIR STEIDEL", "tipo": "PF"},
    {"nome": "EDSON LUÍS RAABE", "tipo": "PF"},
    {"nome": "MARCOS TODT", "tipo": "PF"},
    {"nome": "ELISANDRO NUNES GOMES", "tipo": "PF"},
    {"nome": "ANDERSON JOSÉ BUENO", "tipo": "PF"},
    {"nome": "SBM OFICINA MECÂNICA LTDA - MECÂNICA MASTER", "tipo": "PJ"},
    {"nome": "RICARDO JOSÉ TEIXEIRA - CNPJ", "tipo": "PJ"},
    {"nome": "PATRICIA WAWRZYNIAK JANTSCH", "tipo": "PF"},
    {"nome": "SAULO SUCHARA", "tipo": "PF"},
    {"nome": "REFLORESTA IMÓVEIS LTDA - FILIAL", "tipo": "PJ"},
    {"nome": "KEVIN ROBERT ELIAS", "tipo": "PF"},
    {"nome": "PAULO SERGIO CARVALHO", "tipo": "PF"},
    {"nome": "JOSNEI THEISS", "tipo": "PF"},
    {"nome": "DANIELLY VENEZIO RODRIGUES", "tipo": "PF"},
    {"nome": "RODRIGO BALBINOTTI", "tipo": "PF"},
    # Página 3
    {"nome": "MARCIO FABIANO HELBING", "tipo": "PF"},
    {"nome": "MARCIO FIGURA", "tipo": "PF"},
    {"nome": "RAFAEL BORSATO", "tipo": "PF"},
    {"nome": "MARIA PAULA FRIEDRICH", "tipo": "PF"},
    {"nome": "CARLOS SCHMIDMEIER", "tipo": "PF"},
    {"nome": "ARMINDO NOGARA", "tipo": "PF"},
    {"nome": "ADIR PEREIRA DA ROCHA", "tipo": "PF"},
    {"nome": "EVARISTO BLASKOVSKI", "tipo": "PF"},
    {"nome": "RENATO MUNCH", "tipo": "PF"},
    {"nome": "OSNI BATISTA", "tipo": "PF"},
    {"nome": "ELIEZER JANTSCH", "tipo": "PF"},
    {"nome": "EDSON SCHECK", "tipo": "PF"},
    {"nome": "JACQUELINE MULLER PILLATI", "tipo": "PF"},
    {"nome": "MARIO DE SOUZA", "tipo": "PF"},
    {"nome": "FAURI BATISTA", "tipo": "PF"},
    {"nome": "FRITZ MÓVEIS - FILIAL", "tipo": "PJ"},
    {"nome": "RAFAEL BONFIM DE ALMEIDA", "tipo": "PF"},
    {"nome": "DITER HERMANN MULLER", "tipo": "PF"},
    {"nome": "ANTONIO OSNY MACIEL DA SILVA", "tipo": "PF"},
    {"nome": "WANDERLEI PILLATI", "tipo": "PF"},
    {"nome": "CRCO INCORPORADORA", "tipo": "PJ"},
    {"nome": "GENEZIO KUBIACK", "tipo": "PF"},
    {"nome": "PEDRO COLAÇO", "tipo": "PF"},
    {"nome": "MARCOS HIROAKI NAGANO", "tipo": "PF"},
    {"nome": "WALDIR JANTSCH", "tipo": "PF"},
    # Página 4
    {"nome": "CÉLIO BORTOLOTTO", "tipo": "PF"},
    {"nome": "AUGUSTO SCHIMITBERGER", "tipo": "PF"},
    {"nome": "EDSON CARLOS DE MORAIS JÚNIOR", "tipo": "PF"},
    {"nome": "MATHEUS MAURO MELECHENCO", "tipo": "PF"},
    {"nome": "BIG SAFRA - IRINEÓPOLIS", "tipo": "PJ"},
    {"nome": "GILBERTO BATISTA MENDES TAQUES", "tipo": "PF"},
    {"nome": "EDENILSON ROSA DA SILVA", "tipo": "PF"},
    {"nome": "ADAO LUCACHINSKI NETO", "tipo": "PF"},
    {"nome": "FRITZ MÓVEIS - MATRIZ", "tipo": "PJ"},
    {"nome": "RACER AUTO E PICKUPS LTDA", "tipo": "PJ"},
    {"nome": "FABIANO ZANIOLO FREITAS", "tipo": "PF"},
    {"nome": "JOAO VARLEI NEVES", "tipo": "PF"},
    {"nome": "CLAUMIR DE CASTRO", "tipo": "PF"},
    {"nome": "BIG SAFRA - MAFRA", "tipo": "PJ"},
    {"nome": "EDIVAL DOBRYCHTOP", "tipo": "PF"},
    {"nome": "FÁBIO RODRIGO NEVES", "tipo": "PF"},
    {"nome": "ANA ELISA MACHADO", "tipo": "PF"},
    {"nome": "VALDENIR NEVES", "tipo": "PF"},
    {"nome": "DORVALINO KURZAVSKI", "tipo": "PF"},
    {"nome": "PAULO ROSA DA SILVA", "tipo": "PF"},
    {"nome": "HÉLIO JOSÉ BECKER", "tipo": "PF"},
    {"nome": "GF MANUTENÇÃO INDUSTRIAL LTDA", "tipo": "PJ"},
    {"nome": "DIONISIO ANTONIO SCHROEDER", "tipo": "PF"},
    {"nome": "JOSÉ ADILSON KOBICHEN", "tipo": "PF"},
    {"nome": "UNIVERSALL TELHAS E AÇOS", "tipo": "PJ"},
    # Página 5
    {"nome": "JOAO ANTONIO TOMPOROSKI", "tipo": "PF"},
    {"nome": "ISMAEL SOPCZAK", "tipo": "PF"},
    {"nome": "LUCAS MATHEUS TEIXEIRA DA SILVA", "tipo": "PF"},
    {"nome": "SILVIO MACHADO", "tipo": "PF"},
    {"nome": "VALDECIR DALCANAL", "tipo": "PF"},
    {"nome": "SCHMIDMEIER", "tipo": "PF"},
]

# Coleção Firebase de destino
COLECAO_PESSOAS = 'vg_pessoas'


def normalizar_nome(nome: str) -> str:
    """Normaliza nome para comparação (uppercase, sem espaços extras)."""
    return ' '.join(nome.upper().split())


def verificar_cliente_existente(db, nome: str) -> bool:
    """
    Verifica se um cliente com o mesmo nome já existe na coleção.

    Args:
        db: Instância do Firestore
        nome: Nome do cliente a verificar

    Returns:
        True se existe, False se não existe
    """
    nome_normalizado = normalizar_nome(nome)

    # Busca por full_name
    docs = db.collection(COLECAO_PESSOAS).where('full_name', '==', nome).limit(1).stream()
    if any(True for _ in docs):
        return True

    # Busca por nome_exibicao
    docs = db.collection(COLECAO_PESSOAS).where('nome_exibicao', '==', nome).limit(1).stream()
    if any(True for _ in docs):
        return True

    # Busca case-insensitive (carrega todos e compara)
    todos = db.collection(COLECAO_PESSOAS).stream()
    for doc in todos:
        data = doc.to_dict()
        full_name = normalizar_nome(data.get('full_name', ''))
        nome_exibicao = normalizar_nome(data.get('nome_exibicao', ''))
        if nome_normalizado == full_name or nome_normalizado == nome_exibicao:
            return True

    return False


def criar_documento_pessoa(cliente: dict) -> dict:
    """
    Cria documento de pessoa a partir dos dados do cliente.

    Args:
        cliente: Dicionário com nome e tipo do cliente

    Returns:
        Documento formatado para o Firebase
    """
    agora = datetime.now()

    return {
        'full_name': cliente['nome'],
        'nome_exibicao': cliente['nome'],
        'apelido': '',
        'tipo_pessoa': cliente['tipo'],
        'cpf': '',
        'cnpj': '',
        'email': '',
        'telefone': '',
        'endereco': '',
        'tipo_filial': 'Matriz' if cliente['tipo'] == 'PJ' else '',
        'socios': [],
        'vinculos': [],
        'observacoes': 'Importado via migração',
        'created_at': agora,
        'updated_at': agora,
    }


def executar_migracao(dry_run: bool = False):
    """
    Executa a migração dos clientes para o Firebase.

    Args:
        dry_run: Se True, apenas simula sem salvar
    """
    print("=" * 60)
    print("MIGRAÇÃO DE CLIENTES - VISÃO GERAL DO ESCRITÓRIO")
    print("=" * 60)
    print(f"Coleção Firebase: {COLECAO_PESSOAS}")
    print(f"Modo: {'SIMULAÇÃO (dry-run)' if dry_run else 'EXECUÇÃO REAL'}")
    print(f"Total de clientes na lista: {len(CLIENTES_PARA_IMPORTAR)}")
    print("=" * 60)
    print()

    # Contadores
    total = len(CLIENTES_PARA_IMPORTAR)
    importados = 0
    ja_existentes = 0
    erros = 0

    # Conecta ao Firebase
    try:
        db = get_db()
        print("✅ Conectado ao Firebase com sucesso")
        print()
    except Exception as e:
        print(f"❌ Erro ao conectar ao Firebase: {e}")
        return

    # Separa por tipo para estatísticas
    pf_count = sum(1 for c in CLIENTES_PARA_IMPORTAR if c['tipo'] == 'PF')
    pj_count = sum(1 for c in CLIENTES_PARA_IMPORTAR if c['tipo'] == 'PJ')
    print(f"📊 Estatísticas da lista:")
    print(f"   - Pessoas Físicas (PF): {pf_count}")
    print(f"   - Pessoas Jurídicas (PJ): {pj_count}")
    print()

    print("🔄 Iniciando processamento...")
    print("-" * 60)

    for i, cliente in enumerate(CLIENTES_PARA_IMPORTAR, 1):
        nome = cliente['nome']
        tipo = cliente['tipo']

        try:
            # Verifica se já existe
            if verificar_cliente_existente(db, nome):
                print(f"[{i:3d}/{total}] ⏭️  {nome} ({tipo}) - JÁ EXISTE")
                ja_existentes += 1
                continue

            # Cria documento
            documento = criar_documento_pessoa(cliente)

            if dry_run:
                print(f"[{i:3d}/{total}] 🔍 {nome} ({tipo}) - SERIA IMPORTADO")
                importados += 1
            else:
                # Salva no Firebase
                db.collection(COLECAO_PESSOAS).add(documento)
                print(f"[{i:3d}/{total}] ✅ {nome} ({tipo}) - IMPORTADO")
                importados += 1

        except Exception as e:
            print(f"[{i:3d}/{total}] ❌ {nome} ({tipo}) - ERRO: {e}")
            erros += 1

    # Relatório final
    print()
    print("=" * 60)
    print("RELATÓRIO FINAL")
    print("=" * 60)
    print(f"Total de clientes na lista:    {total}")
    print(f"Clientes importados:           {importados}")
    print(f"Clientes já existentes:        {ja_existentes}")
    print(f"Erros encontrados:             {erros}")
    print("=" * 60)

    if dry_run:
        print()
        print("⚠️  MODO SIMULAÇÃO - Nenhum dado foi salvo no Firebase")
        print("    Execute sem --dry-run para salvar os dados")
    else:
        print()
        print("✅ Migração concluída!")


def main():
    """Função principal."""
    # Verifica argumentos
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv

    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        print("Argumentos:")
        print("  --dry-run, -d    Simular migração (não salva dados)")
        print("  --help, -h       Mostrar esta ajuda")
        return

    executar_migracao(dry_run=dry_run)


if __name__ == '__main__':
    main()
