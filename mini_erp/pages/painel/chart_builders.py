"""
Builders de configuração de gráficos EChart.
Funções genéricas e reutilizáveis para criar especificações de gráficos.
"""
from typing import List, Dict, Any, Optional


def build_bar_chart_config(
    categories: List[str],
    values: List[int],
    colors: Optional[List[str]] = None,
    series_name: str = 'Quantidade',
    horizontal: bool = False,
    bar_width: str = '60%',
    label_font_size: int = 14,
    rotate_labels: int = 0,
    show_label: bool = True,
    label_position: str = 'top',
    show_percentage: bool = False,
) -> Dict[str, Any]:
    """
    Cria configuração para gráfico de barras.
    
    Args:
        categories: Lista de categorias (eixo X ou Y)
        values: Lista de valores
        colors: Lista de cores (opcional, uma por barra)
        series_name: Nome da série
        horizontal: Se True, barras horizontais
        bar_width: Largura das barras
        label_font_size: Tamanho da fonte do label
        rotate_labels: Rotação dos labels do eixo
        show_label: Mostrar valores nas barras
        label_position: Posição do label ('top', 'right', etc)
        show_percentage: Se True, mostra porcentagem junto com o valor
    """
    # Calcula porcentagens se necessário
    total = sum(values) if show_percentage and values else 0
    percentages = [(v / total * 100) if total > 0 else 0 for v in values] if show_percentage else None
    
    # Preparar dados com cores individuais se fornecidas
    if colors and len(colors) == len(values):
        chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
    else:
        chart_data = values
    
    # Configura formatter de label com porcentagem se necessário
    label_config = {
        'show': show_label,
        'position': 'right' if horizontal else label_position,
        'fontWeight': 'bold',
        'fontSize': label_font_size
    }
    
    if show_percentage and percentages and total > 0:
        # Prepara dados com labels formatados já calculados
        # Formatação de porcentagens:
        # - Se >= 1%: arredondar para inteiro (ex: "47 (90%)")
        # - Se < 1% e > 0%: 1 casa decimal (ex: "1 (0.5%)")
        # - Se = 0: mostrar "0 (0%)"
        def formatar_label_com_percentual(valor, percentual):
            """Formata label com porcentagem seguindo regras específicas"""
            if percentual == 0:
                return f'{valor} (0%)'
            elif percentual >= 1:
                return f'{valor} ({percentual:.0f}%)'
            else:
                return f'{valor} ({percentual:.1f}%)'
        
        formatted_data = []
        data_list = chart_data if isinstance(chart_data, list) else [{'value': v} for v in values]
        for i, item in enumerate(data_list):
            if isinstance(item, dict):
                val = item.get('value', values[i] if i < len(values) else 0)
                formatted_item = item.copy()
                formatted_item['label'] = {
                    'show': True,
                    'formatter': formatar_label_com_percentual(val, percentages[i])
                }
                formatted_data.append(formatted_item)
            else:
                val = item if isinstance(item, (int, float)) else values[i] if i < len(values) else 0
                formatted_data.append({
                    'value': val,
                    'label': {
                        'show': True,
                        'formatter': formatar_label_com_percentual(val, percentages[i])
                    }
                })
        chart_data = formatted_data
        label_config['show'] = False  # Desabilita label da série, já está nos dados
    else:
        label_config['formatter'] = '{c}'
    
    # Configuração base
    config = {
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {
            'left': '3%',
            'right': '10%' if horizontal else '4%',
            'bottom': '3%',
            'top': '3%',
            'containLabel': True
        },
        'series': [{
            'name': series_name,
            'type': 'bar',
            'data': chart_data,
            'barWidth': bar_width,
            'label': label_config
        }]
    }
    
    if horizontal:
        config['xAxis'] = {
            'type': 'value',
            'minInterval': 1
        }
        config['yAxis'] = {
            'type': 'category',
            'data': list(reversed(categories)),
            'axisLabel': {'fontSize': 11}
        }
        config['series'][0]['data'] = list(reversed(chart_data)) if isinstance(chart_data, list) else chart_data
    else:
        config['xAxis'] = {
            'type': 'category',
            'data': categories,
            'axisLabel': {
                'interval': 0,
                'rotate': rotate_labels,
                'fontSize': 11 if rotate_labels else 12,
                'fontWeight': 'bold' if not rotate_labels else 'normal'
            }
        }
        config['yAxis'] = {
            'type': 'value',
            'minInterval': 1
        }
    
    return config


def build_pie_chart_config(
    data: List[Dict[str, Any]],
    series_name: str = 'Dados',
    show_legend: bool = True,
    legend_position: str = 'bottom',
    donut: bool = True,
    center: List[str] = None,
    label_font_size: int = 13,
    show_percentage: bool = True,
) -> Dict[str, Any]:
    """
    Cria configuração para gráfico de pizza/donut.
    
    Args:
        data: Lista de dicts com 'value', 'name' e opcionalmente 'itemStyle'
        series_name: Nome da série
        show_legend: Mostrar legenda
        legend_position: Posição da legenda ('left', 'right', 'top', 'bottom')
        donut: Se True, cria gráfico donut (com furo no meio)
        center: Posição do centro ['x%', 'y%']
        label_font_size: Tamanho da fonte do label
        show_percentage: Mostrar percentual no label
    """
    # Se legenda está abaixo ou acima, centraliza o gráfico verticalmente mais alto
    # Se legenda está lateral, ajusta horizontalmente
    if center is None:
        if show_legend and legend_position in ['bottom', 'top']:
            center = ['50%', '45%']  # Centralizado horizontalmente, um pouco acima do centro
        elif show_legend and legend_position in ['left', 'right']:
            center = ['65%', '50%'] if legend_position == 'left' else ['35%', '50%']
        else:
            center = ['50%', '50%']
    
    formatter = '{b}\n{c} ({d}%)' if show_percentage else '{b}: {c}'
    
    config = {
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: {c} ({d}%)'
        },
        'series': [{
            'name': series_name,
            'type': 'pie',
            # Reduzir radius para dar mais espaço aos labels externos
            'radius': ['35%', '60%'] if donut else '60%',
            'center': center,
            'avoidLabelOverlap': True,  # Evitar sobreposição de labels
            'itemStyle': {
                'borderRadius': 10,
                'borderColor': '#fff',
                'borderWidth': 2
            },
            'label': {
                'show': True,
                'position': 'outside',
                'fontSize': label_font_size,
                'fontWeight': 'bold',
                'formatter': formatter,
                'distanceToLabelLine': 5,
                'rich': {
                    'name': {
                        'fontSize': label_font_size,
                        'fontWeight': 'bold',
                        'lineHeight': 20
                    },
                    'value': {
                        'fontSize': label_font_size - 1,
                        'fontWeight': 'normal'
                    }
                }
            },
            'labelLine': {
                'show': True,
                'length': 15,
                'length2': 10,
                'smooth': 0.2
            },
            'emphasis': {
                'label': {
                    'show': True,
                    'fontSize': label_font_size + 2,
                    'fontWeight': 'bold'
                }
            },
            'data': data
        }]
    }
    
    if show_legend:
        if legend_position in ['bottom', 'top']:
            # Legenda horizontal abaixo ou acima
            config['legend'] = {
                'orient': 'horizontal',
                'left': 'center',
                'bottom': '5%' if legend_position == 'bottom' else None,
                'top': '5%' if legend_position == 'top' else None,
                'fontSize': 12,
                'itemGap': 20,
                'itemWidth': 14,
                'itemHeight': 14
            }
        else:
            # Legenda vertical lateral
            config['legend'] = {
                'orient': 'vertical',
                'left': legend_position,
                'top': 'center',
                'fontSize': 13,
                'itemGap': 12
            }
    
    return config


def build_line_chart_config(
    years: List[str],
    series_data: List[Dict[str, Any]],
    show_area: bool = True,
) -> Dict[str, Any]:
    """
    Cria configuração para gráfico de linhas (evolução temporal).
    
    Args:
        years: Lista de anos/períodos
        series_data: Lista de séries (cada uma com 'name', 'data', 'color')
        show_area: Mostrar área preenchida sob a linha
    """
    series = []
    for s in series_data:
        color = s.get('color', '#455A64')
        serie_config = {
            'name': s['name'],
            'type': 'line',
            'data': s['data'],
            'smooth': True,
            'lineStyle': {'color': color, 'width': 3},
            'itemStyle': {'color': color},
            'emphasis': {'focus': 'series'}
        }
        
        if show_area:
            serie_config['areaStyle'] = {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': color + '40'},
                        {'offset': 1, 'color': color + '10'}
                    ]
                }
            }
        
        series.append(serie_config)
    
    return {
        'tooltip': {
            'trigger': 'axis',
            'backgroundColor': 'rgba(255, 255, 255, 0.95)',
            'borderColor': '#ddd',
            'borderWidth': 1,
            'textStyle': {'color': '#333'},
            'axisPointer': {
                'type': 'cross',
                'lineStyle': {'color': '#999', 'type': 'dashed'}
            }
        },
        'legend': {
            'data': [s['name'] for s in series_data],
            'top': '3%',
            'left': 'center',
            'textStyle': {'fontSize': 14, 'color': '#333'}
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '10%',
            'top': '15%',
            'containLabel': True,
            'backgroundColor': '#f8f9fa'
        },
        'xAxis': {
            'type': 'category',
            'data': years,
            'boundaryGap': False,
            'axisLine': {'lineStyle': {'color': '#e0e0e0'}},
            'axisLabel': {
                'fontSize': 12,
                'color': '#333',
                'fontWeight': '500'
            },
            'name': 'Ano',
            'nameLocation': 'middle',
            'nameGap': 35,
            'nameTextStyle': {
                'fontSize': 13,
                'fontWeight': 'bold',
                'color': '#555'
            }
        },
        'yAxis': {
            'type': 'value',
            'minInterval': 1,
            'axisLine': {'lineStyle': {'color': '#e0e0e0'}},
            'splitLine': {'lineStyle': {'color': '#e0e0e0', 'type': 'dashed'}},
            'axisLabel': {
                'fontSize': 12,
                'color': '#333'
            },
            'name': 'Quantidade',
            'nameLocation': 'middle',
            'nameGap': 50,
            'nameTextStyle': {
                'fontSize': 13,
                'fontWeight': 'bold',
                'color': '#555'
            }
        },
        'series': series
    }


def build_heatmap_config(
    data: List[List[Any]],
    x_categories: List[str],
    y_categories: List[str],
    max_value: int,
    tooltip_formatter: str,
    colors: List[str] = None,
) -> Dict[str, Any]:
    """
    Cria configuração para mapa de calor.
    
    Args:
        data: Dados no formato [[x, y, value], ...]
        x_categories: Categorias do eixo X
        y_categories: Categorias do eixo Y
        max_value: Valor máximo para a escala
        tooltip_formatter: Função JS para formatar tooltip
        colors: Lista de cores para o gradiente
    """
    if colors is None:
        colors = ['#e0f2fe', '#0ea5e9', '#0284c7', '#0369a1', '#075985', '#0c4a6e']
    
    height = max(400, len(y_categories) * 40)
    
    return {
        'tooltip': {
            'position': 'top',
            'formatter': tooltip_formatter
        },
        'grid': {
            'height': f'{height}px',
            'top': '10%',
            'left': '15%',
            'right': '10%'
        },
        'xAxis': {
            'type': 'category',
            'data': x_categories,
            'splitArea': {'show': True},
            'axisLabel': {
                'rotate': 45,
                'fontSize': 11
            }
        },
        'yAxis': {
            'type': 'category',
            'data': y_categories,
            'splitArea': {'show': True},
            'axisLabel': {
                'fontSize': 11
            }
        },
        'visualMap': {
            'min': 0,
            'max': max_value,
            'calculable': True,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': '5%',
            'inRange': {
                'color': colors
            },
            'text': ['Alto', 'Baixo'],
            'textStyle': {'color': '#000'}
        },
        'series': [{
            'name': 'Problemas',
            'type': 'heatmap',
            'data': data,
            'label': {
                'show': True,
                'fontSize': 11,
                'fontWeight': 'bold',
                'color': '#000'
            },
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 10,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    }


def build_simple_pie_config(
    data: List[Dict[str, Any]],
    series_name: str = 'Dados',
) -> Dict[str, Any]:
    """
    Cria configuração simples para gráfico de pizza (sem legenda lateral).
    Usado para gráficos compactos.
    """
    return {
        'tooltip': {'trigger': 'item'},
        'series': [{
            'name': series_name,
            'type': 'pie',
            'radius': ['40%', '70%'],
            'center': ['50%', '50%'],
            'avoidLabelOverlap': False,
            'itemStyle': {
                'borderRadius': 10,
                'borderColor': '#fff',
                'borderWidth': 2
            },
            'label': {
                'show': True,
                'position': 'outside',
                'fontSize': 14,
                'fontWeight': 'bold',
                'formatter': '{b}: {c}'
            },
            'labelLine': {'show': True},
            'data': data
        }]
    }


def build_stacked_bar_chart_config(
    categories: List[str],
    series_data: List[Dict[str, Any]],
    show_labels: bool = True,
    label_font_size: int = 11,
) -> Dict[str, Any]:
    """
    Cria configuração para gráfico de barras verticais empilhadas.
    
    Args:
        categories: Lista de categorias (eixo X) - meses, por exemplo
        series_data: Lista de séries, cada uma com 'name', 'data' (valores) e 'color'
        show_labels: Mostrar valores nas barras
        label_font_size: Tamanho da fonte dos labels
    
    Returns:
        Dicionário com configuração EChart para barras empilhadas
    """
    series = []
    for idx, serie in enumerate(series_data):
        is_last = idx == len(series_data) - 1  # Última série (topo da pilha)
        item_style = {
            'color': serie.get('color', '#3B82F6')
        }
        # Aplica bordas arredondadas apenas na última série (topo)
        if is_last:
            item_style['borderRadius'] = [0, 4, 4, 0]
        
        serie_config = {
            'name': serie.get('name', ''),
            'type': 'bar',
            'stack': 'total',  # Empilha as barras
            'data': serie.get('data', []),
            'itemStyle': item_style,
            'label': {
                'show': show_labels,
                'position': 'inside',  # Labels dentro da barra
                'fontSize': label_font_size,
                'fontWeight': 'bold',
                'color': '#000' if serie.get('color') in ['#67E8F9', '#22D3EE'] else '#fff'  # Contraste para legibilidade
            }
        }
        series.append(serie_config)
    
    return {
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '3%',
            'top': '3%',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': categories,
            'axisLabel': {
                'fontSize': 11,
                'fontWeight': 'bold'
            }
        },
        'yAxis': {
            'type': 'value',
            'minInterval': 1
        },
        'legend': {
            'show': False  # Não mostrar legenda para gráfico empilhado simples
        },
        'series': series
    }










