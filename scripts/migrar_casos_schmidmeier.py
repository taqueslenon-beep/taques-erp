"""
Script de migração de casos do workspace Schmidmeier para Visão Geral.

Migra casos da coleção "cases" (Schmidmeier) para "vg_casos" (Visão Geral).
Mantém sincronização entre ambos os workspaces.
"""
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mini_erp.firebase_config import get_db
from mini_erp.pages.visao_geral.casos.database import (
    criar_caso,
    listar_casos,
    excluir_caso,
    buscar_caso
)
from mini_erp.pages.visao_geral.pessoas.database_grupo import buscar_grupo_por_nome
from mini_erp.pages.visao_geral.pessoas.database import listar_pessoas, listar_pessoas_colecao_people
from mini_erp.pages.visao_geral.casos.models import criar_caso_vazio, PRIORIDADE_PADRAO


# Diretório para salvar mapeamentos
MAPEAMENTOS_DIR = Path(__file__).parent.parent / 'migracoes'
MAPEAMENTOS_DIR.mkdir(exist_ok=True)


def buscar_casos_schmidmeier() -> List[Dict[str, Any]]:
    """
    Busca todos os casos da coleção 'cases' (Schmidmeier).
    
    Returns:
        Lista de casos do Schmidmeier
    """
    try:
        db = get_db()
        if not db:
            print("❌ Erro: Conexão com Firebase não disponível")
            return []
        
        docs = db.collection('cases').stream()
        casos = []
        
        for doc in docs:
            caso = doc.to_dict()
            caso['_id'] = doc.id
            casos.append(caso)
        
        print(f"✅ Encontrados {len(casos)} casos no Schmidmeier")
        return casos
        
    except Exception as e:
        print(f"❌ Erro ao buscar casos do Schmidmeier: {e}")
        import traceback
        traceback.print_exc()
        return []


def filtrar_casos_para_migrar(casos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtra casos que devem ser migrados:
    - Todos os casos com case_type = 'Antigo'
    - 2 casos específicos novos: "2-5-bituva-impedir-regeneracao-2025" e "2-6-contagem-nova-autuacao-2025"
    
    Args:
        casos: Lista de todos os casos do Schmidmeier
        
    Returns:
        Lista de casos filtrados para migração
    """
    casos_antigos = [c for c in casos if c.get('case_type') == 'Antigo']
    
    slugs_especificos = [
        '2-5-bituva-impedir-regeneracao-2025',
        '2-6-contagem-nova-autuacao-2025'
    ]
    casos_especificos = [
        c for c in casos 
        if c.get('slug') in slugs_especificos
    ]
    
    # Combina e remove duplicatas
    todos_casos = {c.get('slug'): c for c in casos_antigos + casos_especificos}.values()
    
    print(f"📋 Casos filtrados para migração: {len(todos_casos)}")
    print(f"   - Casos Antigos: {len(casos_antigos)}")
    print(f"   - Casos específicos: {len(casos_especificos)}")
    
    return list(todos_casos)


def converter_clientes_nomes_para_ids(
    clientes_nomes: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Converte lista de nomes de clientes para IDs e nomes na Visão Geral.
    
    Args:
        clientes_nomes: Lista de nomes de clientes (strings)
        
    Returns:
        Tupla (lista_ids, lista_nomes) - IDs e nomes encontrados
    """
    if not clientes_nomes:
        return [], []
    
    pessoas = listar_pessoas()
    pessoas_people = listar_pessoas_colecao_people()
    
    # Combina ambas as listas
    todas_pessoas = pessoas + pessoas_people
    
    ids_encontrados = []
    nomes_encontrados = []
    nomes_nao_encontrados = []
    
    for nome_cliente in clientes_nomes:
        if not nome_cliente or not nome_cliente.strip():
            continue
        
        nome_limpo = nome_cliente.strip()
        encontrado = False
        
        # Busca por full_name, nome_exibicao, name, display_name
        for pessoa in todas_pessoas:
            nome_pessoa = (
                pessoa.get('full_name', '') or
                pessoa.get('nome_exibicao', '') or
                pessoa.get('name', '') or
                pessoa.get('display_name', '') or
                ''
            ).strip()
            
            if nome_pessoa.lower() == nome_limpo.lower():
                pessoa_id = pessoa.get('_id', '')
                if pessoa_id and pessoa_id not in ids_encontrados:
                    ids_encontrados.append(pessoa_id)
                    nomes_encontrados.append(nome_pessoa)
                    encontrado = True
                    break
        
        if not encontrado:
            nomes_nao_encontrados.append(nome_limpo)
    
    if nomes_nao_encontrados:
        print(f"⚠️  Clientes não encontrados: {', '.join(nomes_nao_encontrados)}")
    
    return ids_encontrados, nomes_encontrados


def mapear_caso_schmidmeier_para_visao_geral(
    caso_schmidmeier: Dict[str, Any],
    grupo_id: str,
    grupo_nome: str
) -> Dict[str, Any]:
    """
    Mapeia um caso do formato Schmidmeier para formato Visão Geral.
    
    Args:
        caso_schmidmeier: Caso no formato Schmidmeier
        grupo_id: ID do grupo Schmidmeier
        grupo_nome: Nome do grupo Schmidmeier
        
    Returns:
        Caso no formato Visão Geral
    """
    # Cria estrutura base
    caso_vg = criar_caso_vazio()
    
    # Mapeamento de campos básicos
    caso_vg['titulo'] = caso_schmidmeier.get('title', '') or caso_schmidmeier.get('name', '')
    caso_vg['status'] = caso_schmidmeier.get('status', 'Em andamento')
    caso_vg['estado'] = caso_schmidmeier.get('state', 'Santa Catarina')
    caso_vg['categoria'] = caso_schmidmeier.get('category', 'Contencioso')
    caso_vg['descricao'] = caso_schmidmeier.get('observations', '') or caso_schmidmeier.get('description', '')
    
    # Campos fixos
    caso_vg['nucleo'] = 'Ambiental'  # Todos os casos do Schmidmeier são ambientais
    caso_vg['prioridade'] = PRIORIDADE_PADRAO  # P4 por padrão
    
    # Campos de grupo
    caso_vg['grupo_id'] = grupo_id
    caso_vg['grupo_nome'] = grupo_nome
    
    # Campo de referência
    caso_vg['slug_original'] = caso_schmidmeier.get('slug', '')
    
    # Campos estratégicos
    caso_vg['objetivos'] = caso_schmidmeier.get('objectives', '')
    caso_vg['proximas_acoes'] = caso_schmidmeier.get('next_actions', '')
    caso_vg['consideracoes_legais'] = caso_schmidmeier.get('legal_considerations', '')
    caso_vg['consideracoes_tecnicas'] = caso_schmidmeier.get('technical_considerations', '')
    caso_vg['observacoes_estrategia'] = caso_schmidmeier.get('strategy_observations', '')
    caso_vg['teses'] = caso_schmidmeier.get('theses', []) or []
    
    # Campos de responsáveis (mantém formato original)
    caso_vg['responsaveis'] = caso_schmidmeier.get('responsaveis', []) or []
    
    # Campos de parte contrária
    caso_vg['parte_contraria'] = caso_schmidmeier.get('parte_contraria', '')
    caso_vg['parte_contraria_nome'] = caso_schmidmeier.get('parte_contraria_nome', '')
    
    # Campos SWOT
    caso_vg['swot_forcas'] = caso_schmidmeier.get('swot_s', []) or []
    caso_vg['swot_fraquezas'] = caso_schmidmeier.get('swot_w', []) or []
    caso_vg['swot_oportunidades'] = caso_schmidmeier.get('swot_o', []) or []
    caso_vg['swot_ameacas'] = caso_schmidmeier.get('swot_t', []) or []
    
    # Campos de mapas e cálculos
    caso_vg['mapas'] = caso_schmidmeier.get('maps', []) or []
    caso_vg['notas_mapas'] = caso_schmidmeier.get('map_notes', '')
    caso_vg['calculos'] = caso_schmidmeier.get('calculations', []) or []
    
    # Campos de links
    caso_vg['links'] = caso_schmidmeier.get('links', []) or []
    
    # Campos de processos
    caso_vg['processos_ids'] = caso_schmidmeier.get('process_ids', []) or []
    caso_vg['processos_titulos'] = caso_schmidmeier.get('processes', []) or []
    
    # Conversão de clientes (nomes → IDs)
    clientes_nomes_originais = caso_schmidmeier.get('clients', []) or []
    if isinstance(clientes_nomes_originais, str):
        clientes_nomes_originais = [clientes_nomes_originais]
    
    clientes_ids, clientes_nomes = converter_clientes_nomes_para_ids(clientes_nomes_originais)
    caso_vg['clientes'] = clientes_ids
    caso_vg['clientes_nomes'] = clientes_nomes
    
    return caso_vg


def verificar_duplicata_por_titulo(titulo: str) -> Optional[str]:
    """
    Verifica se já existe um caso com o mesmo título na Visão Geral.
    
    Args:
        titulo: Título do caso a verificar
        
    Returns:
        ID do caso duplicado ou None
    """
    if not titulo:
        return None
    
    casos_existentes = listar_casos()
    for caso in casos_existentes:
        if caso.get('titulo', '').strip().lower() == titulo.strip().lower():
            return caso.get('_id')
    
    return None


def salvar_mapeamento(
    mapeamento: Dict[str, str],
    nome_arquivo: str = None
) -> str:
    """
    Salva mapeamento slug → novo_id em arquivo JSON.
    
    Args:
        mapeamento: Dicionário com mapeamento slug → novo_id
        nome_arquivo: Nome do arquivo (opcional, gera automaticamente se None)
        
    Returns:
        Caminho do arquivo salvo
    """
    if nome_arquivo is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f'mapeamento_casos_{timestamp}.json'
    
    caminho_arquivo = MAPEAMENTOS_DIR / nome_arquivo
    
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(mapeamento, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Mapeamento salvo em: {caminho_arquivo}")
    return str(caminho_arquivo)


def carregar_mapeamento(caminho_arquivo: str) -> Dict[str, str]:
    """
    Carrega mapeamento de arquivo JSON.
    
    Args:
        caminho_arquivo: Caminho do arquivo de mapeamento
        
    Returns:
        Dicionário com mapeamento slug → novo_id
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        return {}


def migrar_casos_schmidmeier(
    lista_casos: List[Dict[str, Any]] = None,
    dry_run: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Migra casos do Schmidmeier para Visão Geral.
    
    Args:
        lista_casos: Lista de casos a migrar (se None, busca automaticamente)
        dry_run: Se True, apenas simula sem salvar
        
    Returns:
        Tupla (sucesso: bool, resultado: dict)
    """
    resultado = {
        'sucesso': False,
        'casos_migrados': 0,
        'casos_duplicados': 0,
        'casos_com_erro': 0,
        'mapeamento': {},
        'erros': []
    }
    
    try:
        # Busca grupo Schmidmeier
        grupo = buscar_grupo_por_nome('Schmidmeier')
        if not grupo:
            resultado['erros'].append('Grupo "Schmidmeier" não encontrado. Execute inicializar_grupo_schmidmeier() primeiro.')
            print("❌ Grupo 'Schmidmeier' não encontrado")
            return False, resultado
        
        grupo_id = grupo._id
        grupo_nome = grupo.nome
        print(f"✅ Grupo encontrado: {grupo_nome} (ID: {grupo_id})")
        
        # Busca casos se não fornecidos
        if lista_casos is None:
            todos_casos = buscar_casos_schmidmeier()
            lista_casos = filtrar_casos_para_migrar(todos_casos)
        
        if not lista_casos:
            print("⚠️  Nenhum caso encontrado para migrar")
            resultado['erros'].append('Nenhum caso encontrado para migrar')
            return False, resultado
        
        print(f"\n🚀 Iniciando migração de {len(lista_casos)} casos...")
        if dry_run:
            print("🔍 MODO DRY RUN - Nenhum dado será salvo\n")
        
        # Processa cada caso
        for idx, caso_schmidmeier in enumerate(lista_casos, 1):
            slug = caso_schmidmeier.get('slug', '')
            titulo = caso_schmidmeier.get('title', '') or caso_schmidmeier.get('name', '')
            
            print(f"\n[{idx}/{len(lista_casos)}] Processando: {titulo}")
            
            # Verifica duplicata
            caso_duplicado_id = verificar_duplicata_por_titulo(titulo)
            if caso_duplicado_id:
                print(f"⚠️  Duplicata encontrada (ID: {caso_duplicado_id}) - Pulando")
                resultado['casos_duplicados'] += 1
                continue
            
            try:
                # Mapeia caso
                caso_vg = mapear_caso_schmidmeier_para_visao_geral(
                    caso_schmidmeier,
                    grupo_id,
                    grupo_nome
                )
                
                if dry_run:
                    print(f"   [DRY RUN] Seria criado: {caso_vg['titulo']}")
                    resultado['casos_migrados'] += 1
                    resultado['mapeamento'][slug] = '[DRY_RUN_ID]'
                else:
                    # Cria caso na Visão Geral
                    novo_id = criar_caso(caso_vg)
                    if novo_id:
                        print(f"   ✅ Migrado com sucesso (ID: {novo_id})")
                        resultado['casos_migrados'] += 1
                        resultado['mapeamento'][slug] = novo_id
                    else:
                        print(f"   ❌ Erro ao criar caso")
                        resultado['casos_com_erro'] += 1
                        resultado['erros'].append(f"Erro ao criar caso: {titulo}")
            
            except Exception as e:
                print(f"   ❌ Erro ao processar caso: {e}")
                import traceback
                traceback.print_exc()
                resultado['casos_com_erro'] += 1
                resultado['erros'].append(f"Erro ao processar {titulo}: {str(e)}")
        
        # Salva mapeamento
        if resultado['mapeamento'] and not dry_run:
            salvar_mapeamento(resultado['mapeamento'])
        
        resultado['sucesso'] = True
        print(f"\n✅ Migração concluída!")
        print(f"   - Migrados: {resultado['casos_migrados']}")
        print(f"   - Duplicados: {resultado['casos_duplicados']}")
        print(f"   - Erros: {resultado['casos_com_erro']}")
        
        return True, resultado
        
    except Exception as e:
        print(f"❌ Erro geral na migração: {e}")
        import traceback
        traceback.print_exc()
        resultado['erros'].append(f"Erro geral: {str(e)}")
        return False, resultado


def rollback_migracao(caminho_mapeamento: str) -> bool:
    """
    Desfaz migração removendo casos criados.
    
    Args:
        caminho_mapeamento: Caminho do arquivo de mapeamento
        
    Returns:
        True se rollback bem-sucedido
    """
    try:
        mapeamento = carregar_mapeamento(caminho_mapeamento)
        if not mapeamento:
            print("❌ Mapeamento vazio ou inválido")
            return False
        
        print(f"🔄 Iniciando rollback de {len(mapeamento)} casos...")
        
        casos_removidos = 0
        erros = 0
        
        for slug, caso_id in mapeamento.items():
            if caso_id == '[DRY_RUN_ID]':
                continue
            
            try:
                if excluir_caso(caso_id):
                    print(f"   ✅ Removido: {slug} (ID: {caso_id})")
                    casos_removidos += 1
                else:
                    print(f"   ⚠️  Não encontrado: {slug} (ID: {caso_id})")
                    erros += 1
            except Exception as e:
                print(f"   ❌ Erro ao remover {slug}: {e}")
                erros += 1
        
        print(f"\n✅ Rollback concluído!")
        print(f"   - Removidos: {casos_removidos}")
        print(f"   - Erros: {erros}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no rollback: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Exemplo de uso
    print("=" * 60)
    print("SCRIPT DE MIGRAÇÃO DE CASOS - SCHMIDMEIER → VISÃO GERAL")
    print("=" * 60)
    
    # Primeiro, testa em modo dry_run
    print("\n🔍 Testando em modo DRY RUN...")
    sucesso, resultado = migrar_casos_schmidmeier(dry_run=True)
    
    if sucesso and resultado['casos_migrados'] > 0:
        resposta = input(f"\n❓ Migrar {resultado['casos_migrados']} casos? (s/N): ")
        if resposta.lower() == 's':
            print("\n🚀 Executando migração real...")
            sucesso, resultado = migrar_casos_schmidmeier(dry_run=False)
        else:
            print("❌ Migração cancelada pelo usuário")
    else:
        print("⚠️  Nenhum caso para migrar ou erro na verificação")



