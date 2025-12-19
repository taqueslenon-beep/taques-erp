"""
Componentes de tabela para a página de processos (Visão Geral).
Contém CSS, slots Vue e funções de conversão de dados.
"""
from datetime import datetime
from typing import Dict, Any, List
from mini_erp.models.prioridade import PRIORIDADE_PADRAO, get_cor_por_prioridade

# =============================================================================
# CSS PADRÃO PARA TABELAS DE PROCESSOS
# =============================================================================

TABELA_PROCESSOS_CSS = '''
<style>
    /* CSS Padrão para Tabelas de Processos - Cores Alternadas */
    .q-table {
        border-collapse: collapse;
        border: 1px solid #e0e0e0;
    }
    .q-table thead th {
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 8px 10px !important;
        text-align: center !important;
        background-color: #f5f5f5 !important;
        border-bottom: 2px solid #d0d0d0 !important;
        border-right: 1px solid #e0e0e0 !important;
        vertical-align: middle !important;
        white-space: normal !important;
        line-height: 1.3 !important;
    }
    .q-table thead th:last-child {
        border-right: none !important;
    }
    .q-table tbody td {
        font-size: 11px !important;
        padding: 6px 10px !important;
        border-bottom: 1px solid #e8e8e8 !important;
        border-right: 1px solid #e8e8e8 !important;
        vertical-align: middle !important;
    }
    .q-table tbody td:last-child {
        border-right: none !important;
    }
    /* CORES ALTERNADAS - Par: cinza claro, Ímpar: branco */
    .q-table tbody tr:nth-child(even) {
        background-color: #fafafa !important;
    }
    .q-table tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    /* Hover suave */
    .q-table tbody tr:hover {
        background-color: #f0f7ff !important;
    }
    .q-table tbody tr:last-child td {
        border-bottom: 1px solid #e8e8e8 !important;
    }
    /* PADRONIZAÇÃO DE FONTE - COLUNA "NÚMERO" */
    .process-number-text,
    .process-number-link {
        font-size: 11px !important;
        font-weight: normal !important;
        color: #374151 !important;
        line-height: 1.4 !important;
        text-decoration: none !important;
        font-family: inherit !important;
    }
    .process-number-link:hover {
        color: #374151 !important;
        text-decoration: none !important;
        cursor: pointer !important;
    }
    .process-number-link:active,
    .process-number-link:visited {
        color: #374151 !important;
        text-decoration: none !important;
    }
</style>
'''

# =============================================================================
# SLOTS VUE PARA TABELA
# =============================================================================

BODY_SLOT_AREA = '''
    <q-td :props="props" style="vertical-align: middle;">
        <q-badge 
            v-if="props.value && props.value !== '-'"
            :style="props.value === 'Cível' ? 'background-color: #dbeafe; color: #1e40af; border: 1px solid #3b82f6;' : 
                    props.value === 'Criminal' ? 'background-color: #fee2e2; color: #991b1b; border: 1px solid #ef4444;' : 
                    props.value === 'Trabalhista' ? 'background-color: #fef3c7; color: #92400e; border: 1px solid #f59e0b;' : 
                    props.value === 'Tributário' ? 'background-color: #ddd6fe; color: #5b21b6; border: 1px solid #8b5cf6;' : 
                    props.value === 'Ambiental' ? 'background-color: #d1fae5; color: #065f46; border: 1px solid #10b981;' : 
                    props.value === 'Administrativo' ? 'background-color: #f3f4f6; color: #374151; border: 1px solid #9ca3af;' : 
                    'background-color: #e5e7eb; color: #374151; border: 1px solid #9ca3af;'"
            class="px-2 py-1"
            style="font-weight: 600; font-size: 12px; border-radius: 4px;"
        >
            {{ props.value }}
        </q-badge>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

BODY_SLOT_STATUS = '''
    <q-td :props="props" style="vertical-align: middle;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <q-badge 
                :style="props.value === 'Em andamento' ? 'background-color: #fbbf24; color: #1f2937;' : 
                        props.value === 'Concluído' ? 'background-color: #059669; color: white;' : 
                        props.value === 'Em monitoramento' ? 'background-color: #f97316; color: white;' : 
                        'background-color: #d1d5db; color: #000000;'"
                class="px-3 py-1"
                style="border: 1px solid rgba(0,0,0,0.1);"
            >
                {{ props.value }}
            </q-badge>
        </div>
    </q-td>
'''

BODY_SLOT_NUCLEO = '''
    <q-td :props="props" style="vertical-align: middle;">
        <q-badge 
            v-if="props.value && props.value !== '-'"
            :style="props.value === 'Ambiental' ? 'background-color: #223631; color: white;' : 
                    props.value === 'Cobranças' ? 'background-color: #f59e0b; color: white;' : 
                    props.value === 'Generalista' ? 'background-color: #6366f1; color: white;' : 
                    'background-color: #e5e7eb; color: #374151;'"
            class="px-2 py-1"
            style="font-weight: 600; font-size: 11px; border-radius: 4px;"
        >
            {{ props.value }}
        </q-badge>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

# =============================================================================
# COLUNAS DA TABELA
# =============================================================================

COLUMNS = [
    {'name': 'acoes', 'label': '', 'field': 'acoes', 'align': 'center', 'sortable': False, 'style': 'width: 50px; min-width: 50px;'},
    {'name': 'data_abertura', 'label': 'Data', 'field': 'data_abertura_sort', 'align': 'center', 'sortable': True, 'style': 'width: 90px; min-width: 90px;'},
    {'name': 'nucleo', 'label': 'Núcleo', 'field': 'nucleo', 'align': 'center', 'sortable': True, 'style': 'width: 100px;'},
    {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True, 'style': 'width: 120px; max-width: 120px;'},
    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True, 'style': 'width: 280px; max-width: 280px;'},
    {'name': 'cases', 'label': 'Casos', 'field': 'cases', 'align': 'left', 'style': 'width: 180px; min-width: 180px;'},
    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 180px;'},
    {'name': 'clients', 'label': 'Clientes', 'field': 'clients', 'align': 'left', 'style': 'width: 120px; max-width: 120px;'},
    {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True, 'style': 'width: 140px;'},
]

# Slot para coluna de ações (botão editar)
BODY_SLOT_ACOES = '''
    <q-td :props="props" style="vertical-align: middle; text-align: center; padding: 4px;">
        <q-btn 
            flat 
            round 
            dense 
            icon="edit" 
            color="primary" 
            size="sm"
            @click="$parent.$emit('edit', props.row)"
        >
            <q-tooltip>Editar</q-tooltip>
        </q-btn>
    </q-td>
'''


# =============================================================================
# FUNÇÕES DE CONVERSÃO
# =============================================================================

def converter_processo_para_row(processo: dict) -> dict:
    """
    Converte processo do formato vg_processos para formato esperado pela tabela.
    
    Args:
        processo: Dicionário do processo no formato vg_processos
        
    Returns:
        Dicionário no formato esperado pela tabela
    """
    # Processa data de abertura
    data_abertura_raw = processo.get('data_abertura') or ''
    data_abertura_display = ''
    data_abertura_sort = ''
    
    if data_abertura_raw:
        try:
            # Tenta converter timestamps ISO para formato DD/MM/AAAA
            if isinstance(data_abertura_raw, str) and 'T' in data_abertura_raw:
                # É um timestamp ISO
                dt = datetime.fromisoformat(data_abertura_raw.replace('Z', '+00:00'))
                data_abertura_display = dt.strftime('%d/%m/%Y')
                data_abertura_sort = dt.strftime('%Y/%m/%d')
            else:
                data_abertura_raw = str(data_abertura_raw).strip()
                
                # Formato: AAAA (apenas ano)
                if len(data_abertura_raw) == 4 and data_abertura_raw.isdigit():
                    data_abertura_display = data_abertura_raw
                    data_abertura_sort = f"{data_abertura_raw}/00/00"
                # Formato: MM/AAAA (mês e ano)
                elif len(data_abertura_raw) == 7 and '/' in data_abertura_raw:
                    partes = data_abertura_raw.split('/')
                    if len(partes) == 2:
                        data_abertura_display = data_abertura_raw
                        data_abertura_sort = f"{partes[1]}/{partes[0]}/00"
                # Formato: DD/MM/AAAA (completa)
                elif len(data_abertura_raw) == 10 and data_abertura_raw.count('/') == 2:
                    partes = data_abertura_raw.split('/')
                    if len(partes) == 3:
                        data_abertura_display = data_abertura_raw
                        data_abertura_sort = f"{partes[2]}/{partes[1]}/{partes[0]}"
                else:
                    data_abertura_display = data_abertura_raw
        except Exception:
            data_abertura_display = str(data_abertura_raw)
    
    # Extrai clientes (formato esperado: lista de strings)
    clientes_nomes = processo.get('clientes_nomes', [])
    if not isinstance(clientes_nomes, list):
        clientes_nomes = [str(clientes_nomes)] if clientes_nomes else []
    clients_list = [str(c).upper() for c in clientes_nomes if c]
    
    # Extrai casos vinculados
    caso_titulo = processo.get('caso_titulo', '')
    cases_list = [caso_titulo] if caso_titulo else []
    
    # Mapeia parte contrária
    parte_contraria = processo.get('parte_contraria', '')
    opposing_list = [parte_contraria.upper()] if parte_contraria else []
    
    # Migra status antigos para novos
    status_raw = processo.get('status', 'Em andamento')
    status_mapeamento = {
        'Ativo': 'Em andamento',
        'Suspenso': 'Em monitoramento',
        'Arquivado': 'Concluído',
        'Baixado': 'Concluído',
        'Encerrado': 'Concluído',
    }
    status_final = status_mapeamento.get(status_raw, status_raw)
    if status_final not in ['Em andamento', 'Concluído', 'Em monitoramento']:
        status_final = 'Em andamento'
    
    return {
        '_id': processo.get('_id', ''),
        'data_abertura': data_abertura_display,
        'data_abertura_sort': data_abertura_sort,
        'nucleo': processo.get('nucleo', 'Ambiental'),
        'title': processo.get('titulo', 'Sem título'),
        'title_raw': processo.get('titulo', 'Sem título'),
        'number': processo.get('numero', ''),
        'clients_list': clients_list,
        'cases_list': cases_list,
        'system': processo.get('sistema_processual', ''),
        'status': status_final,
        'area': processo.get('area', ''),
        'link': processo.get('link', ''),
        'prioridade': processo.get('prioridade', PRIORIDADE_PADRAO),
        'is_third_party_monitoring': False,
        'is_desdobramento': False,
    }



