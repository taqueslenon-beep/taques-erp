"""
ui_components.py - Componentes de interface NiceGUI para o módulo de Processos.

Este módulo contém:
- Slots de tabela customizados (templates Vue)
- Colunas de tabela para visualização de acesso
- CSS padrão para cores alternadas nas tabelas
"""

from typing import List, Dict, Any
from mini_erp.constants import AREA_COLORS_BACKGROUND, AREA_COLORS_TEXT, AREA_COLORS_BORDER


# =============================================================================
# CSS PADRÃO PARA TABELAS DE PROCESSOS - CORES ALTERNADAS
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
    /* Garante que números com e sem link tenham exatamente a mesma aparência visual */
    .process-number-text,
    .process-number-link {
        font-size: 11px !important;
        font-weight: normal !important;
        color: #374151 !important;
        line-height: 1.4 !important;
        text-decoration: none !important;
        font-family: inherit !important;
    }
    /* Links mantêm mesma aparência, mas cursor muda no hover */
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
    /* LINHA LILÁS/ROXA PASTEL PARA PROCESSOS FUTURO/PREVISTO */
    .q-table tbody tr[data-status="Futuro/Previsto"],
    .q-table tbody tr.future-process-row {
        background-color: #F3E5F5 !important;
        border-left: 4px solid #9B59B6 !important;
    }
    .q-table tbody tr[data-status="Futuro/Previsto"]:hover,
    .q-table tbody tr.future-process-row:hover {
        background-color: #E1BEE7 !important;
    }
    /* LINHA AZUL CLARO PARA ACOMPANHAMENTOS DE TERCEIROS */
    .q-table tbody tr[data-type="third_party_monitoring"],
    .q-table tbody tr.third-party-monitoring-row {
        background-color: #E8F1FF !important;
        border-left: 4px solid #4A90E2 !important;
    }
    .q-table tbody tr[data-type="third_party_monitoring"]:hover,
    .q-table tbody tr.third-party-monitoring-row:hover {
        background-color: #D4E7FF !important;
    }
</style>
'''


# =============================================================================
# DEFINIÇÕES DE COLUNAS PARA TABELA DE ACESSO
# =============================================================================

ACCESS_TABLE_COLUMNS = [
    {'name': 'area', 'label': 'Área', 'field': 'area', 'align': 'left', 'sortable': True, 'style': 'width: 100px;'},
    {'name': 'title', 'label': 'Título', 'field': 'title', 'align': 'left', 'sortable': True},
    {'name': 'number', 'label': 'Número', 'field': 'number', 'align': 'left', 'sortable': True, 'style': 'width: 150px;'},
    {'name': 'system', 'label': 'Sistema', 'field': 'system', 'align': 'left', 'sortable': True, 'style': 'width: 200px;'},
    {'name': 'access_lawyer', 'label': 'Acesso aos Processos', 'field': 'access_lawyer', 'align': 'center', 'style': 'width: 150px;'},
    {'name': 'access_technicians', 'label': '', 'field': 'access_technicians', 'align': 'center', 'style': 'width: 150px;'},
    {'name': 'access_client', 'label': '', 'field': 'access_client', 'align': 'center', 'style': 'width: 150px;'},
]


# =============================================================================
# SLOTS DE CABEÇALHO PARA TABELA DE ACESSO
# =============================================================================

HEADER_SLOT_ACCESS_LAWYER = '''
    <q-th :props="props" style="background-color: #f3f4f6; text-align: center;">
        <div style="font-weight: 600; font-size: 12px; padding: 8px;">
            Acesso aos Processos
        </div>
    </q-th>
'''

HEADER_SLOT_ACCESS_TECHNICIANS = '''
    <q-th :props="props" style="background-color: #f3f4f6; text-align: center;">
        <div style="font-weight: 600; font-size: 12px; padding: 8px;">
            Advogado
        </div>
    </q-th>
'''

HEADER_SLOT_ACCESS_CLIENT = '''
    <q-th :props="props" style="background-color: #f3f4f6; text-align: center;">
        <div style="font-weight: 600; font-size: 12px; padding: 8px;">
            Cliente
        </div>
    </q-th>
'''


# =============================================================================
# SLOTS DE CÉLULA PARA ACESSO - ADVOGADO
# =============================================================================

BODY_SLOT_ACCESS_LAWYER = '''
    <q-td :props="props" 
          :style="{
              backgroundColor: (props.row.lawyer_granted ? '#dcfce7' : 
                               props.row.lawyer_requested ? '#dbeafe' : '#fee2e2'),
              borderLeft: '3px solid ' + (props.row.lawyer_granted ? '#22c55e' : 
                                         props.row.lawyer_requested ? '#3b82f6' : '#ef4444')
          }">
        <div style="display: flex; flex-direction: column; gap: 8px; padding: 8px; align-items: center; position: relative;">
            <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 11px; color: #6b7280;">Solicitado:</span>
                <q-checkbox 
                    :model-value="props.row.lawyer_requested"
                    @update:model-value="(val) => $parent.$emit('updateAccess', {idx: props.row.idx, type: 'lawyer', field: 'requested', value: val})"
                    size="xs"
                />
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 11px; color: #6b7280;">Concedido:</span>
                <q-checkbox 
                    :model-value="props.row.lawyer_granted"
                    @update:model-value="(val) => $parent.$emit('updateAccess', {idx: props.row.idx, type: 'lawyer', field: 'granted', value: val})"
                    size="xs"
                />
            </div>
            <q-btn 
                flat 
                dense 
                round 
                size="xs" 
                icon="comment"
                :color="props.row.lawyer_comment ? 'primary' : 'grey-6'"
                @click="$parent.$emit('openComment', {idx: props.row.idx, type: 'lawyer', comment: props.row.lawyer_comment || ''})"
                style="position: absolute; top: 4px; right: 4px;"
            >
                <q-badge v-if="props.row.lawyer_comment" color="primary" floating rounded />
            </q-btn>
        </div>
    </q-td>
'''


# =============================================================================
# SLOTS DE CÉLULA PARA ACESSO - TÉCNICOS
# =============================================================================

BODY_SLOT_ACCESS_TECHNICIANS = '''
    <q-td :props="props" 
          :style="{
              backgroundColor: (props.row.technicians_granted ? '#dcfce7' : 
                               props.row.technicians_requested ? '#dbeafe' : '#fee2e2'),
              borderLeft: '3px solid ' + (props.row.technicians_granted ? '#22c55e' : 
                                         props.row.technicians_requested ? '#3b82f6' : '#ef4444')
          }">
        <div style="display: flex; flex-direction: column; gap: 8px; padding: 8px; align-items: center; position: relative;">
            <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 11px; color: #6b7280;">Solicitado:</span>
                <q-checkbox 
                    :model-value="props.row.technicians_requested"
                    @update:model-value="(val) => $parent.$emit('updateAccess', {idx: props.row.idx, type: 'technicians', field: 'requested', value: val})"
                    size="xs"
                />
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 11px; color: #6b7280;">Concedido:</span>
                <q-checkbox 
                    :model-value="props.row.technicians_granted"
                    @update:model-value="(val) => $parent.$emit('updateAccess', {idx: props.row.idx, type: 'technicians', field: 'granted', value: val})"
                    size="xs"
                />
            </div>
            <q-btn 
                flat 
                dense 
                round 
                size="xs" 
                icon="comment"
                :color="props.row.technicians_comment ? 'primary' : 'grey-6'"
                @click="$parent.$emit('openComment', {idx: props.row.idx, type: 'technicians', comment: props.row.technicians_comment || ''})"
                style="position: absolute; top: 4px; right: 4px;"
            >
                <q-badge v-if="props.row.technicians_comment" color="primary" floating rounded />
            </q-btn>
        </div>
    </q-td>
'''


# =============================================================================
# SLOTS DE CÉLULA PARA ACESSO - CLIENTE
# =============================================================================

BODY_SLOT_ACCESS_CLIENT = '''
    <q-td :props="props" 
          :style="{
              backgroundColor: (props.row.client_granted ? '#dcfce7' : 
                               props.row.client_requested ? '#dbeafe' : '#fee2e2'),
              borderLeft: '3px solid ' + (props.row.client_granted ? '#22c55e' : 
                                         props.row.client_requested ? '#3b82f6' : '#ef4444')
          }">
        <div style="display: flex; flex-direction: column; gap: 8px; padding: 8px; align-items: center; position: relative;">
            <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 11px; color: #6b7280;">Solicitado:</span>
                <q-checkbox 
                    :model-value="props.row.client_requested"
                    @update:model-value="(val) => $parent.$emit('updateAccess', {idx: props.row.idx, type: 'client', field: 'requested', value: val})"
                    size="xs"
                />
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 11px; color: #6b7280;">Concedido:</span>
                <q-checkbox 
                    :model-value="props.row.client_granted"
                    @update:model-value="(val) => $parent.$emit('updateAccess', {idx: props.row.idx, type: 'client', field: 'granted', value: val})"
                    size="xs"
                />
            </div>
            <q-btn 
                flat 
                dense 
                round 
                size="xs" 
                icon="comment"
                :color="props.row.client_comment ? 'primary' : 'grey-6'"
                @click="$parent.$emit('openComment', {idx: props.row.idx, type: 'client', comment: props.row.client_comment || ''})"
                style="position: absolute; top: 4px; right: 4px;"
            >
                <q-badge v-if="props.row.client_comment" color="primary" floating rounded />
            </q-btn>
        </div>
    </q-td>
'''


# =============================================================================
# FUNÇÃO PARA GERAR SLOT DE ÁREA COM CORES DINÂMICAS
# =============================================================================

def _generate_area_slot() -> str:
    """
    Gera o slot de área com cores centralizadas.
    Importa cores de mini_erp.constants para garantir consistência.
    """
    # Mapear áreas para seus estilos
    area_styles = []
    for area in ['Administrativo', 'Criminal', 'Cível', 'Civil', 'Tributário', 'Técnico/projetos', 'Projeto/Técnicos']:
        bg = AREA_COLORS_BACKGROUND.get(area, '#e5e7eb')
        text = AREA_COLORS_TEXT.get(area, '#374151')
        border = AREA_COLORS_BORDER.get(area, '#9ca3af')
        
        # Para variações de nome (Civil/Cível)
        conditions = [f"props.value === '{area}'"]
        if area == 'Cível':
            conditions.append("props.value === 'Civil'")
        elif area == 'Técnico/projetos':
            conditions.append("props.value === 'Projeto/Técnicos'")
        
        condition = ' || '.join([f"({c})" for c in conditions]) if len(conditions) > 1 else conditions[0]
        style_str = f"'background-color: {bg}; color: {text}; border: 1px solid {border};'"
        
        if area_styles:
            area_styles.append(f"{condition} ? {style_str} : ")
        else:
            area_styles.append(f"{condition} ? {style_str} : ")
    
    # Estilo padrão
    default_style = f"'background-color: {AREA_COLORS_BACKGROUND.get('Outros', '#e5e7eb')}; color: {AREA_COLORS_TEXT.get('Outros', '#374151')}; border: 1px solid {AREA_COLORS_BORDER.get('Outros', '#9ca3af')};'"
    
    return f'''
    <q-td :props="props" style="vertical-align: middle;">
        <q-badge 
            v-if="props.value && props.value !== '-'"
            :style="props.value === 'Administrativo' ? 'background-color: {AREA_COLORS_BACKGROUND['Administrativo']}; color: {AREA_COLORS_TEXT['Administrativo']}; border: 1px solid {AREA_COLORS_BORDER['Administrativo']};' : 
                    props.value === 'Criminal' ? 'background-color: {AREA_COLORS_BACKGROUND['Criminal']}; color: {AREA_COLORS_TEXT['Criminal']}; border: 1px solid {AREA_COLORS_BORDER['Criminal']};' : 
                    (props.value === 'Cível' || props.value === 'Civil') ? 'background-color: {AREA_COLORS_BACKGROUND['Cível']}; color: {AREA_COLORS_TEXT['Cível']}; border: 1px solid {AREA_COLORS_BORDER['Cível']};' : 
                    props.value === 'Tributário' ? 'background-color: {AREA_COLORS_BACKGROUND['Tributário']}; color: {AREA_COLORS_TEXT['Tributário']}; border: 1px solid {AREA_COLORS_BORDER['Tributário']};' : 
                    (props.value === 'Técnico/projetos' || props.value === 'Projeto/Técnicos') ? 'background-color: {AREA_COLORS_BACKGROUND['Técnico/projetos']}; color: {AREA_COLORS_TEXT['Técnico/projetos']}; border: 1px solid {AREA_COLORS_BORDER['Técnico/projetos']};' : 
                    'background-color: {AREA_COLORS_BACKGROUND.get('Outros', '#e5e7eb')}; color: {AREA_COLORS_TEXT.get('Outros', '#374151')}; border: 1px solid {AREA_COLORS_BORDER.get('Outros', '#9ca3af')};'"
            class="px-2 py-1"
            style="font-weight: 600; font-size: 12px; border-radius: 4px;"
        >
            {{{{ props.value }}}}
        </q-badge>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

# =============================================================================
# SLOT DE CÉLULA PARA ÁREA
# =============================================================================

BODY_SLOT_AREA = _generate_area_slot()


# =============================================================================
# SLOTS PARA TABELA DE PROCESSOS PRINCIPAL
# =============================================================================

BODY_SLOT_TITLE = '''
    <q-td :props="props">
        <span 
            class="text-primary cursor-pointer hover:underline font-medium"
            @click="$parent.$emit('titleClick', props.row.idx)"
        >
            {{ props.value }}
        </span>
    </q-td>
'''

BODY_SLOT_NUMBER = '''
    <q-td :props="props" style="vertical-align: middle; padding: 6px 10px;">
        <div style="display: flex; align-items: center; gap: 4px;">
            <a 
                v-if="props.row.link && props.value" 
                :href="props.row.link" 
                target="_blank" 
                class="process-number-link"
                style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; text-decoration: none; font-family: inherit;">
                {{ props.value }}
            </a>
            <span v-else-if="props.value" 
                  class="process-number-text"
                  style="font-size: 11px; font-weight: normal; color: #374151; line-height: 1.4; font-family: inherit;">
                {{ props.value }}
            </span>
            <span v-else class="text-gray-400" style="font-size: 11px;">—</span>
            <q-btn 
                v-if="props.value"
                flat dense round 
                icon="content_copy" 
                size="xs" 
                color="grey"
                class="ml-1"
                @click.stop="$parent.$emit('copyNumber', props.value)"
            >
                <q-tooltip>Copiar número</q-tooltip>
            </q-btn>
        </div>
    </q-td>
'''

BODY_SLOT_NUCLEO = '''
    <q-td :props="props">
        <q-badge 
            v-if="props.value && props.value !== '-'"
            style="background-color: #223631;"
            class="text-white px-2 py-1"
        >
            {{ props.value }}
        </q-badge>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

BODY_SLOT_CASES = '''
    <q-td :props="props" style="white-space: normal; vertical-align: middle;">
        <div v-if="props.row.cases_list && props.row.cases_list.length > 0" class="flex flex-col gap-0.5">
            <div v-for="(caso, index) in props.row.cases_list" :key="index" class="text-xs text-gray-700 leading-tight">
                {{ caso }}
            </div>
        </div>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

BODY_SLOT_STATUS = '''
    <q-td :props="props" style="vertical-align: middle;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <q-badge 
                :style="props.value === 'Em andamento' ? 'background-color: #fde047; color: #000000;' : 
                        props.value === 'Concluído' ? 'background-color: #4ade80; color: #000000;' : 
                        props.value === 'Concluído com pendências' ? 'background-color: #a3e635; color: #000000;' : 
                        props.value === 'Em monitoramento' ? 'background-color: #fdba74; color: #000000;' : 
                        props.value === 'Futuro/Previsto' ? 'background-color: #e9d5ff; color: #6b21a8;' : 
                        'background-color: #d1d5db; color: #000000;'"
                class="px-3 py-1"
                style="border: 1px solid rgba(0,0,0,0.1);"
            >
                {{ props.value }}
            </q-badge>
            <q-icon v-if="props.value === 'Futuro/Previsto'" name="auto_awesome" size="18px" style="color: #9333ea;"></q-icon>
        </div>
    </q-td>
'''

BODY_SLOT_LINK = '''
    <q-td :props="props">
        <a v-if="props.value" :href="props.value" target="_blank" class="text-blue-600 hover:text-blue-800">
            <q-icon name="open_in_new" size="sm" />
        </a>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

BODY_SLOT_CLIENTS = '''
    <q-td :props="props" style="white-space: normal; vertical-align: middle;">
        <div v-if="props.row.short_clients_list && props.row.short_clients_list.length > 0" class="flex flex-col gap-0.5">
            <div v-for="(client, index) in props.row.short_clients_list" :key="index" class="text-xs text-gray-700 leading-tight">
                {{ client }}
            </div>
        </div>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''


# =============================================================================
# FUNÇÕES AUXILIARES PARA APLICAR SLOTS
# =============================================================================

def apply_access_table_slots(table) -> None:
    """
    Aplica todos os slots necessários para a tabela de acesso.
    
    Args:
        table: Componente ui.table do NiceGUI
    """
    # Headers
    table.add_slot('header-cell-access_lawyer', HEADER_SLOT_ACCESS_LAWYER)
    table.add_slot('header-cell-access_technicians', HEADER_SLOT_ACCESS_TECHNICIANS)
    table.add_slot('header-cell-access_client', HEADER_SLOT_ACCESS_CLIENT)
    
    # Body cells
    table.add_slot('body-cell-access_lawyer', BODY_SLOT_ACCESS_LAWYER)
    table.add_slot('body-cell-access_technicians', BODY_SLOT_ACCESS_TECHNICIANS)
    table.add_slot('body-cell-access_client', BODY_SLOT_ACCESS_CLIENT)
    table.add_slot('body-cell-area', BODY_SLOT_AREA)


def apply_processes_table_slots(table, selected_columns: Dict[str, bool]) -> None:
    """
    Aplica slots para a tabela de processos baseado nas colunas selecionadas.
    
    Args:
        table: Componente ui.table do NiceGUI
        selected_columns: Dicionário com colunas visíveis
    """
    if selected_columns.get('title'):
        table.add_slot('body-cell-title', BODY_SLOT_TITLE)
    
    if selected_columns.get('number'):
        table.add_slot('body-cell-number', BODY_SLOT_NUMBER)
    
    if selected_columns.get('nucleo'):
        table.add_slot('body-cell-nucleo', BODY_SLOT_NUCLEO)
    
    if selected_columns.get('area'):
        table.add_slot('body-cell-area', BODY_SLOT_AREA)
    
    if selected_columns.get('cases'):
        table.add_slot('body-cell-cases', BODY_SLOT_CASES)
    
    if selected_columns.get('status'):
        table.add_slot('body-cell-status', BODY_SLOT_STATUS)
    
    if selected_columns.get('link'):
        table.add_slot('body-cell-link', BODY_SLOT_LINK)
    
    if selected_columns.get('clients'):
        table.add_slot('body-cell-clients', BODY_SLOT_CLIENTS)


