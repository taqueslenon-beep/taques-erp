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
    """
    # Preparar dados com cores individuais se fornecidas
    if colors and len(colors) == len(values):
        chart_data = [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(values, colors)]
    else:
        chart_data = values
    
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
            'label': {
                'show': show_label,
                'position': 'right' if horizontal else label_position,
                'fontWeight': 'bold',
                'fontSize': label_font_size
            }
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
    legend_position: str = 'left',
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
    if center is None:
        center = ['65%', '50%'] if show_legend else ['50%', '50%']
    
    formatter = '{b}\n{c} ({d}%)' if show_percentage else '{b}: {c}'
    
    config = {
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: {c} ({d}%)'
        },
        'series': [{
            'name': series_name,
            'type': 'pie',
            'radius': ['40%', '70%'] if donut else '70%',
            'center': center,
            'avoidLabelOverlap': False,
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
                'formatter': formatter
            },
            'labelLine': {'show': True},
            'data': data
        }]
    }
    
    if show_legend:
        config['legend'] = {
            'orient': 'vertical',
            'left': legend_position,
            'top': 'center',
            'fontSize': 13
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


