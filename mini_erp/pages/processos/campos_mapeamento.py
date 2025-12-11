"""
Mapeamento completo de campos do módulo de processos.

Este arquivo documenta TODOS os campos do formulário de processos,
suas características e onde são utilizados.
"""

# =============================================================================
# MAPEAMENTO COMPLETO DE CAMPOS
# =============================================================================

CAMPOS_PROCESSO = {
    # ========== ABA: DADOS BÁSICOS ==========
    'title': {
        'tipo': 'input',
        'obrigatorio': True,
        'aba': 'dados_basicos',
        'label': 'Título do Processo',
        'variavel': 'title_input',
        'salvamento': 'build_process_data(title=...)',
        'carregamento': 'title_input.value = p.get("title", "")',
        'observacoes': 'Campo obrigatório, usado como identificador principal'
    },
    'number': {
        'tipo': 'input',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Número do Processo',
        'variavel': 'number_input',
        'salvamento': 'build_process_data(number=...)',
        'carregamento': 'number_input.value = p.get("number", "")',
        'observacoes': 'Número oficial do processo no tribunal'
    },
    'link': {
        'tipo': 'input',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Link do Processo',
        'variavel': 'link_input',
        'salvamento': 'build_process_data(link=...)',
        'carregamento': 'link_input.value = p.get("link", "")',
        'observacoes': 'URL para acessar o processo no sistema do tribunal'
    },
    'process_type': {
        'tipo': 'select',
        'obrigatorio': True,
        'aba': 'dados_basicos',
        'label': 'Tipo de processo',
        'variavel': 'type_select',
        'opcoes': 'PROCESS_TYPE_OPTIONS',
        'valor_padrao': 'Existente',
        'salvamento': 'build_process_data(process_type=...)',
        'carregamento': 'type_select.value = p.get("process_type", "Existente")',
        'observacoes': 'Classificação: Novo (ainda não existe) ou Existente (já em andamento)'
    },
    'data_abertura': {
        'tipo': 'input',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Data de Abertura',
        'variavel': 'data_abertura_input',
        'formatos': ['DD/MM/AAAA', 'MM/AAAA', 'AAAA'],
        'salvamento': 'build_process_data(data_abertura=...)',
        'carregamento': 'data_abertura_input.value = p.get("data_abertura", "")',
        'observacoes': 'Aceita 3 formatos de precisão: data completa, mês/ano ou apenas ano'
    },
    'clients': {
        'tipo': 'multi_select',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Clientes',
        'variavel': 'state["selected_clients"]',
        'salvamento': 'build_process_data(clients=...)',
        'carregamento': 'state["selected_clients"] = list(p.get("clients", []))',
        'observacoes': 'Lista de clientes (pessoas ou empresas que você representa)'
    },
    'opposing_parties': {
        'tipo': 'multi_select',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Parte Contrária',
        'variavel': 'state["selected_opposing"]',
        'salvamento': 'build_process_data(opposing_parties=...)',
        'carregamento': 'state["selected_opposing"] = [get_short_name(...)]',
        'observacoes': 'Pessoa, empresa ou órgão do lado oposto do processo'
    },
    'other_parties': {
        'tipo': 'multi_select',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Outros Envolvidos',
        'variavel': 'state["selected_others"]',
        'salvamento': 'build_process_data(other_parties=...)',
        'carregamento': 'state["selected_others"] = [get_short_name(...)]',
        'observacoes': 'Terceiros interessados, assistentes, litisconsortes, etc'
    },
    'parent_ids': {
        'tipo': 'multi_select',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Processos Pais',
        'variavel': 'state["parent_ids"]',
        'salvamento': 'build_process_data(parent_ids=...)',
        'carregamento': 'state["parent_ids"] = list(p.get("parent_ids", []))',
        'observacoes': 'Lista de IDs dos processos pais (vínculos hierárquicos)'
    },
    'cases': {
        'tipo': 'multi_select',
        'obrigatorio': False,
        'aba': 'dados_basicos',
        'label': 'Casos Vinculados',
        'variavel': 'state["selected_cases"]',
        'salvamento': 'build_process_data(cases=...)',
        'carregamento': 'state["selected_cases"] = list(p.get("cases", []))',
        'observacoes': 'Casos do escritório relacionados a este processo'
    },
    
    # ========== ABA: DADOS JURÍDICOS ==========
    'system': {
        'tipo': 'select',
        'obrigatorio': False,
        'aba': 'dados_juridicos',
        'label': 'Sistema Processual',
        'variavel': 'system_select',
        'opcoes': 'SYSTEM_OPTIONS',
        'salvamento': 'build_process_data(system=...)',
        'carregamento': 'system_select.value = p.get("system")',
        'observacoes': 'Sistema processual (SEI, PJe, etc)'
    },
    'nucleo': {
        'tipo': 'select',
        'obrigatorio': False,
        'aba': 'dados_juridicos',
        'label': 'Núcleo',
        'variavel': 'nucleo_select',
        'opcoes': 'NUCLEO_OPTIONS',
        'valor_padrao': 'Ambiental',
        'salvamento': 'build_process_data(nucleo=...)',
        'carregamento': 'nucleo_select.value = p.get("nucleo", "Ambiental")',
        'observacoes': 'Núcleo do escritório responsável'
    },
    'area': {
        'tipo': 'select',
        'obrigatorio': False,
        'aba': 'dados_juridicos',
        'label': 'Área',
        'variavel': 'area_select',
        'opcoes': 'AREA_OPTIONS',
        'salvamento': 'build_process_data(area=...)',
        'carregamento': 'area_select.value = p.get("area")',
        'observacoes': 'Área do direito'
    },
    'status': {
        'tipo': 'select',
        'obrigatorio': True,
        'aba': 'dados_juridicos',
        'label': 'Status',
        'variavel': 'status_select',
        'opcoes': 'STATUS_OPTIONS',
        'valor_padrao': 'Em andamento',
        'salvamento': 'build_process_data(status=...)',
        'carregamento': 'status_select.value = p.get("status", "Em andamento")',
        'observacoes': 'Status do processo (obrigatório)'
    },
    'result': {
        'tipo': 'select',
        'obrigatorio': False,
        'aba': 'dados_juridicos',
        'label': 'Resultado do processo',
        'variavel': 'result_select',
        'opcoes': 'RESULT_OPTIONS',
        'condicional': 'should_show_result_field(status)',
        'salvamento': 'build_process_data(result=...)',
        'carregamento': 'result_select.value = p.get("result")',
        'observacoes': 'Apenas visível quando status é finalizado'
    },
    'envolve_dano_app': {
        'tipo': 'switch',
        'obrigatorio': False,
        'aba': 'dados_juridicos',
        'label': 'Envolve Dano em APP?',
        'variavel': 'envolve_dano_app_switch',
        'valor_padrao': False,
        'salvamento': 'build_process_data(envolve_dano_app=...)',
        'carregamento': 'envolve_dano_app_switch.value = p.get("envolve_dano_app", False)',
        'observacoes': 'Marque se o processo envolve dano em APP conforme Código Florestal'
    },
    'area_total_discutida': {
        'tipo': 'number',
        'obrigatorio': False,
        'aba': 'dados_juridicos',
        'label': 'Área Total Discutida (ha)',
        'variavel': 'area_total_discutida_input',
        'formato': 'float',
        'salvamento': 'build_process_data(area_total_discutida=...)',
        'carregamento': 'area_total_discutida_input.value = p.get("area_total_discutida")',
        'observacoes': 'Área total discutida no processo em hectares'
    },
    
    # ========== ABA: RELATÓRIO ==========
    'relatory_facts': {
        'tipo': 'editor',
        'obrigatorio': False,
        'aba': 'relatorio',
        'label': 'Resumo dos Fatos',
        'variavel': 'relatory_facts_input',
        'auto_save': True,
        'salvamento': 'build_process_data(relatory_facts=...)',
        'carregamento': 'relatory_facts_input.value = p.get("relatory_facts", "")',
        'observacoes': 'Editor de texto rico (ui.editor) - campo de texto longo'
    },
    'relatory_timeline': {
        'tipo': 'editor',
        'obrigatorio': False,
        'aba': 'relatorio',
        'label': 'Histórico / Linha do Tempo',
        'variavel': 'relatory_timeline_input',
        'auto_save': True,
        'salvamento': 'build_process_data(relatory_timeline=...)',
        'carregamento': 'relatory_timeline_input.value = p.get("relatory_timeline", "")',
        'observacoes': 'Editor de texto rico (ui.editor) - campo de texto longo'
    },
    'relatory_documents': {
        'tipo': 'editor',
        'obrigatorio': False,
        'aba': 'relatorio',
        'label': 'Documentos Relevantes',
        'variavel': 'relatory_documents_input',
        'auto_save': True,
        'salvamento': 'build_process_data(relatory_documents=...)',
        'carregamento': 'relatory_timeline_input.value = p.get("relatory_documents", "")',
        'observacoes': 'Editor de texto rico (ui.editor) - campo de texto longo'
    },
    
    # ========== ABA: ESTRATÉGIA ==========
    'strategy_objectives': {
        'tipo': 'editor',
        'obrigatorio': False,
        'aba': 'estrategia',
        'label': 'Objetivos',
        'variavel': 'objectives_input',
        'auto_save': True,
        'salvamento': 'build_process_data(strategy_objectives=...)',
        'carregamento': 'objectives_input.value = p.get("strategy_objectives", "")',
        'observacoes': 'Editor de texto rico (ui.editor) - campo de texto longo'
    },
    'legal_thesis': {
        'tipo': 'editor',
        'obrigatorio': False,
        'aba': 'estrategia',
        'label': 'Teses a serem trabalhadas',
        'variavel': 'thesis_input',
        'auto_save': True,
        'salvamento': 'build_process_data(legal_thesis=...)',
        'carregamento': 'thesis_input.value = p.get("legal_thesis", "")',
        'observacoes': 'Editor de texto rico (ui.editor) - campo de texto longo'
    },
    'strategy_observations': {
        'tipo': 'editor',
        'obrigatorio': False,
        'aba': 'estrategia',
        'label': 'Observações',
        'variavel': 'observations_input',
        'auto_save': True,
        'salvamento': 'build_process_data(strategy_observations=...)',
        'carregamento': 'observations_input.value = p.get("strategy_observations", "")',
        'observacoes': 'Editor de texto rico (ui.editor) - campo de texto longo'
    },
    
    # ========== ABA: CENÁRIOS ==========
    'scenarios': {
        'tipo': 'lista',
        'obrigatorio': False,
        'aba': 'cenarios',
        'label': 'Cenários',
        'variavel': 'state["scenarios"]',
        'estrutura': {
            'title': 'str',
            'type': 'str',
            'status': 'str',
            'impact': 'str',
            'chance': 'str',
            'obs': 'str'
        },
        'salvamento': 'build_process_data(scenarios=...)',
        'carregamento': 'state["scenarios"] = list(p.get("scenarios", []))',
        'observacoes': 'Lista de cenários possíveis (array de objetos)'
    },
    
    # ========== ABA: PROTOCOLOS ==========
    'protocols': {
        'tipo': 'lista',
        'obrigatorio': False,
        'aba': 'protocolos',
        'label': 'Protocolos',
        'variavel': 'state["protocols"]',
        'estrutura': {
            'title': 'str',
            'date': 'str',
            'number': 'str',
            'system': 'str',
            'observations': 'str'
        },
        'salvamento': 'build_process_data(protocols=...)',
        'carregamento': 'state["protocols"] = list(p.get("protocols", []))',
        'observacoes': 'Lista de protocolos (array de objetos) - também pode ser vinculado externamente'
    },
    
    # ========== ABA: SENHAS DE ACESSO ==========
    # NOTA: Senhas são salvas em subcoleção 'senhas_processo' do processo
    # Não são campos diretos do processo, mas sim documentos filhos
    
    # ========== ABA: SLACK ==========
    # NOTA: Integração Slack ainda não implementada
    
    # ========== CAMPOS DE ACESSO (Dummy - mantidos para compatibilidade) ==========
    'access_lawyer_requested': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_lawyer_requested',
        'salvamento': 'build_process_data(access_lawyer_requested=...)',
        'carregamento': 'access_lawyer_requested.value = p.get("access_lawyer_requested", False)',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_lawyer_granted': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_lawyer_granted',
        'salvamento': 'build_process_data(access_lawyer=...)',
        'carregamento': 'access_lawyer_granted.value = p.get("access_lawyer_granted", False)',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_technicians_requested': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_technicians_requested',
        'salvamento': 'build_process_data(access_technicians_requested=...)',
        'carregamento': 'access_technicians_requested.value = p.get("access_technicians_requested", False)',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_technicians_granted': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_technicians_granted',
        'salvamento': 'build_process_data(access_technicians=...)',
        'carregamento': 'access_technicians_granted.value = p.get("access_technicians_granted", False)',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_client_requested': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_client_requested',
        'salvamento': 'build_process_data(access_client_requested=...)',
        'carregamento': 'access_client_requested.value = p.get("access_client_requested", False)',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_client_granted': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_client_granted',
        'salvamento': 'build_process_data(access_client=...)',
        'carregamento': 'access_client_granted.value = p.get("access_client_granted", False)',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_lawyer_comment': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_lawyer_comment',
        'salvamento': 'build_process_data(access_lawyer_comment=...)',
        'carregamento': 'access_lawyer_comment.value = p.get("access_lawyer_comment", "")',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_technicians_comment': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_technicians_comment',
        'salvamento': 'build_process_data(access_technicians_comment=...)',
        'carregamento': 'access_technicians_comment.value = p.get("access_technicians_comment", "")',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    'access_client_comment': {
        'tipo': 'dummy',
        'obrigatorio': False,
        'aba': 'acesso',
        'variavel': 'access_client_comment',
        'salvamento': 'build_process_data(access_client_comment=...)',
        'carregamento': 'access_client_comment.value = p.get("access_client_comment", "")',
        'observacoes': 'Campo dummy mantido para compatibilidade'
    },
    
    # ========== METADADOS (gerados automaticamente) ==========
    'created_at': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'Firestore',
        'observacoes': 'Timestamp de criação (gerado automaticamente)'
    },
    'updated_at': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'Firestore',
        'observacoes': 'Timestamp de atualização (gerado automaticamente)'
    },
    'created_by': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'Sistema',
        'observacoes': 'ID do usuário que criou (pode ser implementado)'
    },
    'title_searchable': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'save_process()',
        'observacoes': 'Campo de busca em minúsculas (gerado automaticamente)'
    },
    'depth': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'save_process()',
        'observacoes': 'Profundidade na hierarquia (calculado automaticamente)'
    },
    'parent_id': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'save_process()',
        'observacoes': 'Compatibilidade: primeiro parent_id (mantido para funções legadas)'
    },
    'state': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'save_process()',
        'observacoes': 'Estado herdado do primeiro caso vinculado (se houver)'
    },
    'case_ids': {
        'tipo': 'auto',
        'obrigatorio': False,
        'gerado_por': 'save_process()',
        'observacoes': 'Array de slugs dos casos (gerado automaticamente a partir de cases)'
    },
}


# =============================================================================
# CAMPOS COM AUTO-SAVE
# =============================================================================

CAMPOS_AUTO_SAVE = [
    'relatory_facts',
    'relatory_timeline',
    'relatory_documents',
    'strategy_objectives',
    'legal_thesis',
    'strategy_observations',
]


# =============================================================================
# CAMPOS OBRIGATÓRIOS
# =============================================================================

CAMPOS_OBRIGATORIOS = [
    'title',
    'status',
    'process_type',
]


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_all_fields() -> list:
    """Retorna lista de todos os campos mapeados."""
    return list(CAMPOS_PROCESSO.keys())


def get_fields_by_aba(aba: str) -> list:
    """Retorna lista de campos de uma aba específica."""
    return [campo for campo, info in CAMPOS_PROCESSO.items() if info.get('aba') == aba]


def get_fields_by_type(tipo: str) -> list:
    """Retorna lista de campos de um tipo específico."""
    return [campo for campo, info in CAMPOS_PROCESSO.items() if info.get('tipo') == tipo]


def get_required_fields() -> list:
    """Retorna lista de campos obrigatórios."""
    return CAMPOS_OBRIGATORIOS


def get_auto_save_fields() -> list:
    """Retorna lista de campos com auto-save."""
    return CAMPOS_AUTO_SAVE


def validate_field_exists(campo: str) -> bool:
    """Verifica se um campo está mapeado."""
    return campo in CAMPOS_PROCESSO


def get_field_info(campo: str) -> dict:
    """Retorna informações de um campo específico."""
    return CAMPOS_PROCESSO.get(campo, {})

