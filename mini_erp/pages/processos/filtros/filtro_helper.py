"""
filtro_helper.py - Funções auxiliares para criar e validar filtros.

Contém função genérica para criar dropdowns de filtro com validação.
"""

from typing import List, Dict, Any, Callable, Optional
from nicegui import ui


def criar_dropdown_filtro(
    label: str,
    opcoes: List[str],
    estado_dict: Dict[str, str],
    refresh_callback: Optional[Callable] = None,
    width_class: str = 'min-w-[140px]',
    valor_inicial: str = '',
    on_change_callback: Optional[Callable] = None
) -> Any:
    """
    Cria dropdown de filtro com validação de opções.
    
    Valida e sanitiza opções antes de passar para ui.select
    para prevenir erros de ValueError.
    
    Args:
        label: Rótulo do filtro
        opcoes: Lista de opções para o dropdown
        estado_dict: Dicionário de estado {'value': '...'}
        refresh_callback: Função chamada para atualizar tabela
        width_class: Classes CSS para largura
        valor_inicial: Valor inicial do filtro
        on_change_callback: Callback adicional ao mudar valor
    
    Returns:
        Componente ui.select criado
    """
    try:
        # Validação: garante que opcoes é uma lista
        if not isinstance(opcoes, list):
            print(f"[FILTER_DROPDOWN] ⚠️  Opções não são lista para '{label}': {type(opcoes)}")
            opcoes = ['']
        
        # Sanitização: remove valores inválidos
        valid_options = []
        for opt in opcoes:
            try:
                # Converte para string e valida
                if opt is None:
                    continue
                
                opt_str = str(opt).strip()
                
                # Ignora strings vazias (exceto a primeira que é permitida)
                if not opt_str and len(valid_options) > 0:
                    continue
                
                # Validação adicional: verifica se não é número float problemático
                try:
                    float_val = float(opt_str)
                    if opt_str.replace('.', '').replace('-', '').replace(' ', '').isdigit():
                        print(f"[FILTER_DROPDOWN] ⚠️  Valor numérico puro em '{label}': '{opt_str}'")
                except (ValueError, TypeError):
                    pass
                
                # Adiciona opção válida
                valid_options.append(opt_str if opt_str else '')
                
            except Exception as opt_exc:
                print(f"[FILTER_DROPDOWN] ⚠️  Opção inválida ignorada em '{label}': '{opt}' - {opt_exc}")
                continue
        
        # Garante que há pelo menos uma opção vazia
        if not valid_options or (valid_options and valid_options[0] != ''):
            valid_options = [''] + valid_options
        
        # Valida valor_inicial
        if valor_inicial and valor_inicial not in valid_options:
            print(f"[FILTER_DROPDOWN] ⚠️  Valor inicial '{valor_inicial}' não está nas opções válidas para '{label}', usando ''")
            valor_inicial = ''
        
        print(f"[FILTER_DROPDOWN] Criando dropdown '{label}' com {len(valid_options)} opções válidas")
        
        # Cria select com opções validadas
        select = ui.select(valid_options, label=label, value=valor_inicial).props('clearable dense outlined').classes(width_class)
        
        # Estilo discreto e minimalista
        select.style('font-size: 12px; border-color: #d1d5db;')
        select.classes('filter-select')
        
        # Callback para atualizar filtro quando valor mudar
        def on_filter_change():
            try:
                estado_dict['value'] = select.value if select.value else ''
                if on_change_callback:
                    on_change_callback()
                if refresh_callback:
                    refresh_callback()
            except Exception as change_exc:
                print(f"[FILTER_DROPDOWN] ⚠️  Erro no callback de mudança para '{label}': {change_exc}")
        
        # Registrar callback
        select.on('update:model-value', on_filter_change)
        return select
        
    except Exception as exc:
        print(f"[FILTER_DROPDOWN] ❌ Erro crítico ao criar dropdown '{label}': {exc}")
        import traceback
        traceback.print_exc()
        # Retorna select vazio em caso de erro
        try:
            return ui.select([''], label=label, value='').props('clearable dense outlined').classes(width_class)
        except:
            return None

