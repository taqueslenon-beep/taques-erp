"""
ui_components.py - Componentes de interface NiceGUI para o módulo de Processos.

Este módulo contém:
- Slots de tabela customizados (templates Vue)
- Colunas de tabela para visualização de acesso
"""

from typing import List, Dict, Any


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
# SLOT DE CÉLULA PARA ÁREA
# =============================================================================

BODY_SLOT_AREA = '''
    <q-td :props="props">
        <q-badge 
            v-if="props.value && props.value !== '-'"
            :style="props.value === 'Administrativo' ? 'background-color: #d1d5db; color: #1f2937; border: 1px solid #9ca3af;' : 
                    props.value === 'Criminal' ? 'background-color: #fecaca; color: #7f1d1d; border: 1px solid #f87171;' : 
                    (props.value === 'Cível' || props.value === 'Civil') ? 'background-color: #bfdbfe; color: #1e3a8a; border: 1px solid #60a5fa;' : 
                    props.value === 'Tributário' ? 'background-color: #ddd6fe; color: #4c1d95; border: 1px solid #a78bfa;' : 
                    (props.value === 'Técnico/projetos' || props.value === 'Projeto/Técnicos') ? 'background-color: #bbf7d0; color: #14532d; border: 1px solid #4ade80;' : 
                    'background-color: #e5e7eb; color: #374151; border: 1px solid #9ca3af;'"
            class="px-2 py-1"
            style="font-weight: 600; font-size: 12px; border-radius: 4px;"
        >
            {{ props.value }}
        </q-badge>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''


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
    <q-td :props="props">
        <a 
            v-if="props.row.link" 
            :href="props.row.link" 
            target="_blank" 
            class="text-blue-600 hover:text-blue-800 hover:underline"
        >
            {{ props.value }}
        </a>
        <span v-else class="text-gray-600">{{ props.value }}</span>
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
    <q-td :props="props" style="white-space: normal; vertical-align: top;">
        <div v-if="props.row.cases_list && props.row.cases_list.length > 0" class="flex flex-col gap-0.5">
            <div v-for="(caso, index) in props.row.cases_list" :key="index" class="text-xs text-gray-700 leading-tight">
                {{ caso }}
            </div>
        </div>
        <span v-else class="text-gray-400">-</span>
    </q-td>
'''

BODY_SLOT_STATUS = '''
    <q-td :props="props">
        <q-badge 
            :style="props.value === 'Em andamento' ? 'background-color: #eab308; color: #111827;' : 
                    props.value === 'Concluído' ? 'background-color: #166534; color: #ffffff;' : 
                    props.value === 'Concluído com pendências' ? 'background-color: #4d7c0f; color: #ffffff;' : 
                    props.value === 'Em monitoramento' ? 'background-color: #ea580c; color: #ffffff;' : 
                    'background-color: #9ca3af; color: #111827;'"
            class="text-white px-3 py-1"
            style="border: 1px solid rgba(0,0,0,0.1);"
        >
            {{ props.value }}
        </q-badge>
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
    <q-td :props="props" style="white-space: normal; vertical-align: top;">
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


