#!/usr/bin/env python3

"""

Script de migração para importar casos da planilha NOVO-MIGRACAO-V1.xlsx

para a coleção vg_casos do Firebase.



Workspace: "Visão geral do escritório"

Coleção Firebase: vg_casos



Uso:

    # Simular (não salva):

    python scripts/migrar_casos_visao_geral.py --dry-run



    # Executar migração real:

    python scripts/migrar_casos_visao_geral.py



Requisitos:

    pip install pandas openpyxl --break-system-packages

"""

import sys

import os

import argparse

from datetime import datetime

from typing import Dict, List, Optional, Tuple



# Adiciona o diretório raiz ao path para imports

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



import pandas as pd

from mini_erp.firebase_config import get_db



# =============================================================================

# CONFIGURAÇÕES

# =============================================================================



COLECAO_CASOS = 'vg_casos'

COLECAO_PESSOAS = 'vg_pessoas'

COLECAO_USUARIOS = 'usuarios_sistema'



MAPEAMENTO_RESPONSAVEIS = {

    'Lenon': ['lenon', 'lenon_taques', 'lenon_gustavo_batista_taques'],

    'Gilberto': ['gilberto', 'gilberto_taques', 'gilberto_jansen_taques'],

}



CATEGORIA_PADRAO = 'Contencioso'

ESTADO_PADRAO = ''

PRIORIDADE_PADRAO = 'P4'





# =============================================================================

# FUNÇÕES AUXILIARES

# =============================================================================



def normalizar_texto(texto: str) -> str:

    if not texto or pd.isna(texto):

        return ''

    return str(texto).strip().upper()





def buscar_cliente_por_nome(db, nome_cliente: str) -> Optional[str]:

    if not nome_cliente:

        return None

    

    nome_normalizado = normalizar_texto(nome_cliente)

    

    try:

        docs = db.collection(COLECAO_PESSOAS).stream()

        

        for doc in docs:

            pessoa = doc.to_dict()

            campos_nome = ['full_name', 'nome_exibicao', 'nome', 'apelido']

            

            for campo in campos_nome:

                valor = pessoa.get(campo, '')

                if valor and normalizar_texto(valor) == nome_normalizado:

                    return doc.id

        

        return None

    

    except Exception as e:

        print(f"    Erro ao buscar cliente '{nome_cliente}': {e}")

        return None





def buscar_responsavel_por_nome(db, nome_responsavel: str) -> Optional[str]:

    if not nome_responsavel or pd.isna(nome_responsavel):

        return None

    

    nome_limpo = str(nome_responsavel).strip()

    variacoes = MAPEAMENTO_RESPONSAVEIS.get(nome_limpo, [nome_limpo.lower()])

    

    try:

        docs = db.collection(COLECAO_USUARIOS).stream()

        

        for doc in docs:

            usuario = doc.to_dict()

            doc_id_lower = doc.id.lower()

            

            for variacao in variacoes:

                if variacao in doc_id_lower or doc_id_lower in variacao:

                    return doc.id

            

            nome_completo = usuario.get('nome_completo', '').lower()

            for variacao in variacoes:

                if variacao in nome_completo:

                    return doc.id

        

        return None

    

    except Exception as e:

        print(f"    Erro ao buscar responsável '{nome_responsavel}': {e}")

        return None





def processar_clientes(db, clientes_str: str, cache_clientes: Dict) -> Tuple[List[str], List[str], List[str]]:

    if not clientes_str or pd.isna(clientes_str):

        return [], [], []

    

    nomes = [n.strip() for n in str(clientes_str).split(',') if n.strip()]

    

    ids = []

    nomes_encontrados = []

    nomes_nao_encontrados = []

    

    for nome in nomes:

        nome_normalizado = normalizar_texto(nome)

        

        if nome_normalizado in cache_clientes:

            cliente_id = cache_clientes[nome_normalizado]

            if cliente_id:

                ids.append(cliente_id)

                nomes_encontrados.append(nome)

            else:

                nomes_nao_encontrados.append(nome)

            continue

        

        cliente_id = buscar_cliente_por_nome(db, nome)

        cache_clientes[nome_normalizado] = cliente_id

        

        if cliente_id:

            ids.append(cliente_id)

            nomes_encontrados.append(nome)

        else:

            nomes_nao_encontrados.append(nome)

    

    return ids, nomes_encontrados, nomes_nao_encontrados





def verificar_caso_existente(db, titulo: str) -> bool:

    if not titulo:

        return False

    

    try:

        query = db.collection(COLECAO_CASOS).where('titulo', '==', titulo).limit(1)

        docs = list(query.stream())

        return len(docs) > 0

    except Exception as e:

        print(f"    Erro ao verificar caso existente: {e}")

        return False





def criar_documento_caso(

    titulo: str,

    clientes_ids: List[str],

    clientes_nomes: List[str],

    responsaveis_ids: List[str],

    responsaveis_dados: List[Dict],

    nucleo: str,

    prioridade: str,

    status: str

) -> Dict:

    agora = datetime.now()

    

    return {

        'titulo': titulo,

        'clientes': clientes_ids,

        'clientes_nomes': clientes_nomes,

        'responsaveis': responsaveis_ids,

        'responsaveis_dados': responsaveis_dados,

        'nucleo': nucleo or 'Generalista',

        'prioridade': prioridade or PRIORIDADE_PADRAO,

        'status': status or 'Em andamento',

        'categoria': CATEGORIA_PADRAO,

        'estado': ESTADO_PADRAO,

        'descricao': 'Importado via migração',

        'created_at': agora,

        'updated_at': agora,

    }





# =============================================================================

# FUNÇÃO PRINCIPAL DE MIGRAÇÃO

# =============================================================================



def executar_migracao(arquivo_excel: str, dry_run: bool = False):

    print("=" * 70)

    print("MIGRAÇÃO DE CASOS - VISÃO GERAL DO ESCRITÓRIO")

    print("=" * 70)

    print(f"Arquivo: {arquivo_excel}")

    print(f"Coleção Firebase: {COLECAO_CASOS}")

    print(f"Modo: {'SIMULAÇÃO (dry-run)' if dry_run else 'EXECUÇÃO REAL'}")

    print("=" * 70)

    print()

    

    if not os.path.exists(arquivo_excel):

        print(f"❌ Erro: Arquivo não encontrado: {arquivo_excel}")

        return

    

    print("📖 Lendo planilha Excel...")

    try:

        df = pd.read_excel(arquivo_excel, sheet_name='CASOS')

        print(f"   ✅ {len(df)} registros encontrados na aba CASOS")

    except Exception as e:

        print(f"❌ Erro ao ler planilha: {e}")

        return

    

    df = df.dropna(subset=['TÍTULO DO CASO'])

    print(f"   📊 {len(df)} registros válidos após remover vazios")

    print()

    

    print("🔌 Conectando ao Firebase...")

    try:

        db = get_db()

        print("   ✅ Conectado com sucesso")

    except Exception as e:

        print(f"❌ Erro ao conectar ao Firebase: {e}")

        return

    

    cache_clientes = {}

    cache_responsaveis = {}

    

    print()

    print("👥 Pré-carregando responsáveis...")

    for nome, variacoes in MAPEAMENTO_RESPONSAVEIS.items():

        resp_id = buscar_responsavel_por_nome(db, nome)

        if resp_id:

            print(f"   ✅ {nome} -> {resp_id}")

            cache_responsaveis[nome] = resp_id

        else:

            print(f"   ⚠️  {nome} -> NÃO ENCONTRADO")

    

    print()

    print("📊 Estatísticas da planilha:")

    print(f"   - Núcleos: {df['NÚCLEO'].dropna().unique().tolist()}")

    print(f"   - Responsáveis: {df['RESPONSÁVEL'].dropna().unique().tolist()}")

    print(f"   - Prioridades: {df['PRIORIDADE'].dropna().unique().tolist()}")

    print(f"   - Status: {df['STATUS'].dropna().unique().tolist()}")

    print()

    

    total = len(df)

    importados = 0

    ja_existentes = 0

    erros = 0

    clientes_nao_encontrados = set()

    

    print("🔄 Iniciando processamento...")

    print("-" * 70)

    

    for idx, row in df.iterrows():

        numero = idx + 1

        titulo = str(row['TÍTULO DO CASO']).strip() if pd.notna(row['TÍTULO DO CASO']) else ''

        

        if not titulo:

            print(f"[{numero:3d}/{total}] ⏭️  Linha vazia - IGNORADA")

            continue

        

        try:

            if verificar_caso_existente(db, titulo):

                print(f"[{numero:3d}/{total}] ⏭️  {titulo[:50]}... - JÁ EXISTE")

                ja_existentes += 1

                continue

            

            clientes_str = row.get('CLIENTES', '')

            clientes_ids, clientes_nomes, nao_encontrados = processar_clientes(

                db, clientes_str, cache_clientes

            )

            

            for nome in nao_encontrados:

                clientes_nao_encontrados.add(nome)

            

            responsavel_nome = str(row.get('RESPONSÁVEL', '')).strip() if pd.notna(row.get('RESPONSÁVEL')) else ''

            responsaveis_ids = []

            responsaveis_dados = []

            

            if responsavel_nome and responsavel_nome in cache_responsaveis:

                resp_id = cache_responsaveis[responsavel_nome]

                responsaveis_ids = [resp_id]

                responsaveis_dados = [{

                    'usuario_id': resp_id,

                    'nome': responsavel_nome,

                    'email': ''

                }]

            

            nucleo = str(row.get('NÚCLEO', 'Generalista')).strip() if pd.notna(row.get('NÚCLEO')) else 'Generalista'

            prioridade = str(row.get('PRIORIDADE', PRIORIDADE_PADRAO)).strip() if pd.notna(row.get('PRIORIDADE')) else PRIORIDADE_PADRAO

            status = str(row.get('STATUS', 'Em andamento')).strip() if pd.notna(row.get('STATUS')) else 'Em andamento'

            

            documento = criar_documento_caso(

                titulo=titulo,

                clientes_ids=clientes_ids,

                clientes_nomes=clientes_nomes,

                responsaveis_ids=responsaveis_ids,

                responsaveis_dados=responsaveis_dados,

                nucleo=nucleo,

                prioridade=prioridade,

                status=status

            )

            

            clientes_info = f"({len(clientes_ids)} cliente(s))" if clientes_ids else "(sem clientes)"

            

            if dry_run:

                print(f"[{numero:3d}/{total}] 🔍 {titulo[:40]}... {clientes_info} - SERIA IMPORTADO")

                importados += 1

            else:

                db.collection(COLECAO_CASOS).add(documento)

                print(f"[{numero:3d}/{total}] ✅ {titulo[:40]}... {clientes_info} - IMPORTADO")

                importados += 1

        

        except Exception as e:

            print(f"[{numero:3d}/{total}] ❌ {titulo[:40]}... - ERRO: {e}")

            erros += 1

    

    print()

    print("=" * 70)

    print("RELATÓRIO FINAL")

    print("=" * 70)

    print(f"Total de registros na planilha:  {total}")

    print(f"Casos importados:                {importados}")

    print(f"Casos já existentes:             {ja_existentes}")

    print(f"Erros encontrados:               {erros}")

    print("=" * 70)

    

    if clientes_nao_encontrados:

        print()

        print("⚠️  CLIENTES NÃO ENCONTRADOS NA COLEÇÃO vg_pessoas:")

        print("-" * 70)

        for nome in sorted(clientes_nao_encontrados):

            print(f"   • {nome}")

        print("-" * 70)

        print(f"   Total: {len(clientes_nao_encontrados)} clientes não encontrados")

        print()

        print("   💡 DICA: Execute primeiro o script de migração de clientes")

        print("      para cadastrar esses clientes antes de importar os casos.")

    

    if dry_run:

        print()

        print("⚠️  MODO SIMULAÇÃO - Nenhum dado foi salvo no Firebase")

        print("    Execute sem --dry-run para salvar os dados")

    else:

        print()

        print("✅ Migração concluída!")





def main():

    parser = argparse.ArgumentParser(

        description='Migra casos da planilha Excel para o Firebase'

    )

    parser.add_argument(

        '--dry-run', '-d',

        action='store_true',

        help='Simular migração (não salva dados)'

    )

    parser.add_argument(

        '--arquivo', '-a',

        type=str,

        default='NOVO-MIGRACAO-V1.xlsx',

        help='Caminho para o arquivo Excel'

    )

    

    args = parser.parse_args()

    

    arquivo = args.arquivo

    if not os.path.isabs(arquivo):

        if not os.path.exists(arquivo):

            script_dir = os.path.dirname(os.path.abspath(__file__))

            arquivo_script = os.path.join(script_dir, arquivo)

            if os.path.exists(arquivo_script):

                arquivo = arquivo_script

            else:

                root_dir = os.path.dirname(script_dir)

                arquivo_root = os.path.join(root_dir, arquivo)

                if os.path.exists(arquivo_root):

                    arquivo = arquivo_root

    

    executar_migracao(arquivo_excel=arquivo, dry_run=args.dry_run)





if __name__ == '__main__':

    main()

