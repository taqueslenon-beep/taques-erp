"""
Script de validação e auditoria do módulo de processos.

Este script verifica se todos os campos estão sendo salvos e carregados corretamente.
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
from .campos_mapeamento import (
    CAMPOS_PROCESSO,
    get_all_fields,
    get_fields_by_aba,
    get_required_fields,
    get_auto_save_fields
)
from .database import get_all_processes
from .business_logic import build_process_data


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO
# =============================================================================

def validar_campo_salvamento(campo: str, processo: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida se um campo está presente no processo salvo.
    
    Args:
        campo: Nome do campo
        processo: Dicionário do processo
    
    Returns:
        Tupla (valido, mensagem)
    """
    info = CAMPOS_PROCESSO.get(campo)
    if not info:
        return False, f"Campo {campo} não está mapeado"
    
    # Campos auto-gerados não precisam estar no processo original
    if info.get('tipo') == 'auto':
        return True, "Campo auto-gerado"
    
    # Campos dummy não precisam estar no processo
    if info.get('tipo') == 'dummy':
        return True, "Campo dummy (compatibilidade)"
    
    # Verifica se campo está presente
    if campo not in processo:
        # Verifica se é opcional
        if not info.get('obrigatorio', False):
            return True, "Campo opcional ausente (OK)"
        else:
            return False, f"Campo obrigatório {campo} ausente"
    
    return True, "Campo presente"


def validar_campo_carregamento(campo: str, processo: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida se um campo pode ser carregado do processo.
    
    Args:
        campo: Nome do campo
        processo: Dicionário do processo
    
    Returns:
        Tupla (valido, mensagem)
    """
    info = CAMPOS_PROCESSO.get(campo)
    if not info:
        return False, f"Campo {campo} não está mapeado"
    
    # Campos auto-gerados são gerados no salvamento
    if info.get('tipo') == 'auto':
        return True, "Campo auto-gerado (será gerado no salvamento)"
    
    # Campos dummy não precisam estar no processo
    if info.get('tipo') == 'dummy':
        return True, "Campo dummy (compatibilidade)"
    
    # Verifica se campo está presente ou tem valor padrão
    if campo not in processo:
        if info.get('valor_padrao') is not None:
            return True, f"Campo ausente, mas tem valor padrão: {info.get('valor_padrao')}"
        elif not info.get('obrigatorio', False):
            return True, "Campo opcional ausente (OK)"
        else:
            return False, f"Campo obrigatório {campo} ausente"
    
    return True, "Campo presente e pode ser carregado"


def auditar_processo(processo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audita um processo individual.
    
    Args:
        processo: Dicionário do processo
    
    Returns:
        Dicionário com resultados da auditoria
    """
    processo_id = processo.get('_id', 'SEM_ID')
    titulo = processo.get('title', 'Sem título')
    
    campos_salvamento_ok = []
    campos_salvamento_erro = []
    campos_carregamento_ok = []
    campos_carregamento_erro = []
    
    todos_campos = get_all_fields()
    
    for campo in todos_campos:
        # Valida salvamento
        valido_save, msg_save = validar_campo_salvamento(campo, processo)
        if valido_save:
            campos_salvamento_ok.append((campo, msg_save))
        else:
            campos_salvamento_erro.append((campo, msg_save))
        
        # Valida carregamento
        valido_load, msg_load = validar_campo_carregamento(campo, processo)
        if valido_load:
            campos_carregamento_ok.append((campo, msg_load))
        else:
            campos_carregamento_erro.append((campo, msg_load))
    
    return {
        'processo_id': processo_id,
        'titulo': titulo,
        'total_campos': len(todos_campos),
        'campos_salvamento_ok': len(campos_salvamento_ok),
        'campos_salvamento_erro': len(campos_salvamento_erro),
        'campos_carregamento_ok': len(campos_carregamento_ok),
        'campos_carregamento_erro': len(campos_carregamento_erro),
        'erros_salvamento': campos_salvamento_erro,
        'erros_carregamento': campos_carregamento_erro,
        'campos_presentes': list(processo.keys()),
        'total_campos_presentes': len(processo)
    }


def auditar_todos_processos() -> Dict[str, Any]:
    """
    Audita todos os processos do sistema.
    
    Returns:
        Dicionário com resultados da auditoria completa
    """
    processos = get_all_processes()
    
    auditorias = []
    total_erros_salvamento = 0
    total_erros_carregamento = 0
    
    for processo in processos:
        auditoria = auditar_processo(processo)
        auditorias.append(auditoria)
        total_erros_salvamento += len(auditoria['erros_salvamento'])
        total_erros_carregamento += len(auditoria['erros_carregamento'])
    
    # Agrupa erros por tipo
    erros_por_campo = {}
    for auditoria in auditorias:
        for campo, msg in auditoria['erros_salvamento']:
            if campo not in erros_por_campo:
                erros_por_campo[campo] = {'salvamento': [], 'carregamento': []}
            erros_por_campo[campo]['salvamento'].append({
                'processo_id': auditoria['processo_id'],
                'titulo': auditoria['titulo'],
                'mensagem': msg
            })
        
        for campo, msg in auditoria['erros_carregamento']:
            if campo not in erros_por_campo:
                erros_por_campo[campo] = {'salvamento': [], 'carregamento': []}
            erros_por_campo[campo]['carregamento'].append({
                'processo_id': auditoria['processo_id'],
                'titulo': auditoria['titulo'],
                'mensagem': msg
            })
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_processos': len(processos),
        'total_campos_mapeados': len(get_all_fields()),
        'total_erros_salvamento': total_erros_salvamento,
        'total_erros_carregamento': total_erros_carregamento,
        'auditorias': auditorias,
        'erros_por_campo': erros_por_campo,
        'campos_obrigatorios': get_required_fields(),
        'campos_auto_save': get_auto_save_fields()
    }


def gerar_relatorio_auditoria() -> str:
    """
    Gera relatório completo de auditoria em formato texto.
    
    Returns:
        String com relatório formatado
    """
    resultado = auditar_todos_processos()
    
    relatorio = []
    relatorio.append("=" * 80)
    relatorio.append("RELATÓRIO DE AUDITORIA - MÓDULO DE PROCESSOS")
    relatorio.append("=" * 80)
    relatorio.append(f"Data: {resultado['timestamp']}")
    relatorio.append("")
    
    relatorio.append("RESUMO GERAL")
    relatorio.append("-" * 80)
    relatorio.append(f"Total de processos auditados: {resultado['total_processos']}")
    relatorio.append(f"Total de campos mapeados: {resultado['total_campos_mapeados']}")
    relatorio.append(f"Total de erros de salvamento: {resultado['total_erros_salvamento']}")
    relatorio.append(f"Total de erros de carregamento: {resultado['total_erros_carregamento']}")
    relatorio.append("")
    
    relatorio.append("CAMPOS OBRIGATÓRIOS")
    relatorio.append("-" * 80)
    for campo in resultado['campos_obrigatorios']:
        info = CAMPOS_PROCESSO.get(campo, {})
        relatorio.append(f"  ✓ {campo} ({info.get('label', 'N/A')})")
    relatorio.append("")
    
    relatorio.append("CAMPOS COM AUTO-SAVE")
    relatorio.append("-" * 80)
    for campo in resultado['campos_auto_save']:
        info = CAMPOS_PROCESSO.get(campo, {})
        relatorio.append(f"  ✓ {campo} ({info.get('label', 'N/A')})")
    relatorio.append("")
    
    if resultado['erros_por_campo']:
        relatorio.append("PROBLEMAS ENCONTRADOS")
        relatorio.append("-" * 80)
        for campo, erros in resultado['erros_por_campo'].items():
            if erros['salvamento'] or erros['carregamento']:
                relatorio.append(f"\n  Campo: {campo}")
                if erros['salvamento']:
                    relatorio.append(f"    Erros de salvamento: {len(erros['salvamento'])}")
                    for erro in erros['salvamento'][:3]:  # Mostra apenas os 3 primeiros
                        relatorio.append(f"      - {erro['titulo']}: {erro['mensagem']}")
                if erros['carregamento']:
                    relatorio.append(f"    Erros de carregamento: {len(erros['carregamento'])}")
                    for erro in erros['carregamento'][:3]:  # Mostra apenas os 3 primeiros
                        relatorio.append(f"      - {erro['titulo']}: {erro['mensagem']}")
        relatorio.append("")
    else:
        relatorio.append("PROBLEMAS ENCONTRADOS")
        relatorio.append("-" * 80)
        relatorio.append("  Nenhum problema encontrado! ✓")
        relatorio.append("")
    
    relatorio.append("MAPEAMENTO DE CAMPOS POR ABA")
    relatorio.append("-" * 80)
    abas = ['dados_basicos', 'dados_juridicos', 'relatorio', 'estrategia', 'cenarios', 'protocolos']
    for aba in abas:
        campos_aba = get_fields_by_aba(aba)
        relatorio.append(f"\n  {aba.upper().replace('_', ' ')}: {len(campos_aba)} campos")
        for campo in campos_aba[:5]:  # Mostra apenas os 5 primeiros
            info = CAMPOS_PROCESSO.get(campo, {})
            obrigatorio = " *" if info.get('obrigatorio') else ""
            relatorio.append(f"    - {campo}{obrigatorio}")
        if len(campos_aba) > 5:
            relatorio.append(f"    ... e mais {len(campos_aba) - 5} campos")
    relatorio.append("")
    
    relatorio.append("=" * 80)
    relatorio.append("FIM DO RELATÓRIO")
    relatorio.append("=" * 80)
    
    return "\n".join(relatorio)


if __name__ == '__main__':
    # Executa auditoria e imprime relatório
    relatorio = gerar_relatorio_auditoria()
    print(relatorio)
    
    # Salva relatório em arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_relatorio = f'RELATORIO_AUDITORIA_PROCESSOS_{timestamp}.txt'
    with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    print(f"\nRelatório salvo em: {arquivo_relatorio}")

