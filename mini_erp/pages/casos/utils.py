"""
Módulo de funções utilitárias para o módulo de Casos.

Contém funções auxiliares como formatação de nomes, 
geração de HTML para bandeiras e exportação para PDF.
"""

from datetime import datetime
import io

from nicegui import ui

from .models import (
    STATE_FLAG_URLS,
    MONTH_OPTIONS,
    CASE_TYPE_OPTIONS
)

# Importação opcional do reportlab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def get_short_name_helper(full_name: str, source_list: list) -> str:
    """
    Retorna sigla/apelido ou primeiro nome - função auxiliar global.
    
    Args:
        full_name: Nome completo da pessoa/entidade
        source_list: Lista de dicionários contendo informações das pessoas/entidades
        
    Returns:
        Sigla, apelido ou primeiro nome
    """
    for item in source_list:
        item_name = item.get('name') or item.get('full_name', '')
        if item_name == full_name:
            # Prioridade: nickname > alias > primeiro nome
            if item.get('nickname'):
                return item['nickname']
            if item.get('alias'):
                return item['alias']
            # Se não tem apelido, retorna primeiro nome
            return full_name.split()[0] if full_name else full_name
    # Se não encontrou na lista, retorna primeiro nome
    return full_name.split()[0] if full_name else full_name


def get_state_flag_html(state: str, size: int = 16) -> str:
    """
    Retorna HTML da bandeira do estado como imagem.
    
    Args:
        state: Nome do estado (ex: 'Paraná', 'Santa Catarina')
        size: Tamanho da imagem em pixels
        
    Returns:
        String HTML com a tag <img> ou string vazia se estado não encontrado
    """
    url = STATE_FLAG_URLS.get(state)
    if url:
        return f'<img src="{url}" width="{size}" height="{int(size * 0.7)}" style="border-radius: 2px; box-shadow: 0 1px 2px rgba(0,0,0,0.15);" alt="{state}"/>'
    return ''


def format_option_for_search(item: dict) -> str:
    """
    Formata opção para busca: inclui nome e sigla/apelido.
    
    Args:
        item: Dicionário com dados do cliente/pessoa
        
    Returns:
        String formatada como "Nome (Apelido)" ou apenas "Nome"
    """
    name = item.get('name', '')
    nickname = item.get('nickname', '')
    if nickname and nickname != name:
        return f"{name} ({nickname})"
    return name


def get_option_value(formatted_option: str, source_list: list) -> str:
    """
    Extrai o nome completo de uma opção formatada.
    
    Args:
        formatted_option: String formatada como "Nome (Apelido)"
        source_list: Lista de dicionários (não usado, mantido para compatibilidade)
        
    Returns:
        Nome completo sem a parte entre parênteses
    """
    # Remove a parte entre parênteses se existir
    if '(' in formatted_option:
        return formatted_option.split(' (')[0]
    return formatted_option


def export_cases_to_pdf(get_cases_list_func, get_case_sort_key_func, get_case_type_func, primary_color: str):
    """
    Exporta todos os casos para um arquivo PDF.
    
    Args:
        get_cases_list_func: Função que retorna lista de casos
        get_case_sort_key_func: Função que retorna chave de ordenação
        get_case_type_func: Função que retorna tipo do caso
        primary_color: Cor primária para o tema do PDF
    """
    if not REPORTLAB_AVAILABLE:
        ui.notify('Biblioteca reportlab não está instalada. Execute: pip install reportlab', type='negative')
        return
    
    cases_list = get_cases_list_func()
    if not cases_list:
        ui.notify('Nenhum caso para exportar.', type='warning')
        return
    
    try:
        # Criar buffer em memória para o PDF
        buffer = io.BytesIO()
        
        # Criar documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(primary_color),
            spaceAfter=30,
            alignment=1  # Centralizado
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(primary_color),
            spaceAfter=12,
            spaceBefore=12
        )
        normal_style = styles['Normal']
        
        # Título do documento
        story.append(Paragraph('Relatório de Casos', title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Data de geração
        data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
        story.append(Paragraph(f'Gerado em: {data_geracao}', normal_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Total de casos
        story.append(Paragraph(f'Total de casos: {len(cases_list)}', normal_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Ordenar casos por ano, mês e nome
        sorted_cases = sorted(cases_list, key=get_case_sort_key_func, reverse=True)
        
        # Agrupar por tipo
        casos_antigos = [c for c in sorted_cases if get_case_type_func(c) == 'Antigo']
        casos_novos = [c for c in sorted_cases if get_case_type_func(c) == 'Novo']
        casos_futuros = [c for c in sorted_cases if get_case_type_func(c) == 'Futuro']
        
        def add_cases_to_pdf(casos, emoji, titulo):
            """Adiciona uma seção de casos ao PDF."""
            if casos:
                story.append(Paragraph(f'{emoji} {titulo}', heading_style))
                for case in casos:
                    story.append(Spacer(1, 0.3*cm))
                    story.append(Paragraph(f"<b>{case.get('title', 'Sem título')}</b>", normal_style))
                    
                    info_lines = []
                    if case.get('number'):
                        info_lines.append(f"<b>Número:</b> {case.get('number')}")
                    if case.get('year') and case.get('month'):
                        month_idx = case.get('month', 1) - 1
                        if 0 <= month_idx < len(MONTH_OPTIONS):
                            month_name = MONTH_OPTIONS[month_idx]['label']
                            info_lines.append(f"<b>Data:</b> {month_name}/{case.get('year')}")
                    if case.get('category'):
                        info_lines.append(f"<b>Categoria:</b> {case.get('category')}")
                    if case.get('status'):
                        info_lines.append(f"<b>Status:</b> {case.get('status')}")
                    if case.get('state'):
                        info_lines.append(f"<b>Estado:</b> {case.get('state')}")
                    if case.get('clients'):
                        clients_str = ', '.join(case.get('clients', []))
                        info_lines.append(f"<b>Clientes:</b> {clients_str}")
                    
                    if info_lines:
                        story.append(Paragraph('<br/>'.join(info_lines), normal_style))
                    
                    story.append(Spacer(1, 0.2*cm))
                story.append(Spacer(1, 0.5*cm))
        
        # Adicionar cada tipo de caso
        add_cases_to_pdf(casos_antigos, '🔴', 'Casos Antigos')
        add_cases_to_pdf(casos_novos, '🔥', 'Casos Novos')
        add_cases_to_pdf(casos_futuros, '🔮', 'Casos Futuros')
        
        # Construir PDF
        doc.build(story)
        
        # Obter bytes do PDF
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Criar nome do arquivo
        filename = f'casos_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        # Fazer download do PDF
        ui.download(pdf_bytes, filename=filename, media_type='application/pdf')
        ui.notify(f'PDF exportado com sucesso! ({len(cases_list)} casos)', type='positive')
        
    except Exception as e:
        ui.notify(f'Erro ao exportar PDF: {str(e)}', type='negative')


