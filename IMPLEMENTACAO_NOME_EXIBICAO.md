# Implementação da Regra Centralizada de "Nome de Exibição"

## 📋 Resumo da Implementação

Foi implementada uma regra centralizada para garantir que **TODAS** as pessoas (clientes, PJ, PF, órgãos públicos, outros envolvidos) sempre exibam o "nome de exibição" de forma consistente em todos os módulos do sistema.

## 🎯 Objetivos Alcançados

✅ **Campo Unificado**: Adicionado campo `nome_exibicao` como padrão  
✅ **Função Centralizada**: Criada `get_display_name_by_id()` com cache thread-safe  
✅ **Aplicação Universal**: Implementado em casos, processos e pessoas  
✅ **Script de Backfill**: Criado para popular dados existentes  
✅ **Compatibilidade**: Mantidos campos antigos durante transição  

---

## 🔧 Mudanças Técnicas Implementadas

### 1. **Função Centralizada (core.py)**

#### Novas Funções:
- `get_display_name_by_id(person_id, person_type)` - Função principal com cache
- `invalidate_display_name_cache(person_id)` - Gerenciamento de cache
- `get_display_name(item)` - Atualizada com nova prioridade

#### Prioridade de Exibição:
1. `nickname` (se existir e não vazio)
2. `nome_exibicao` (campo padronizado)
3. `display_name` (compatibilidade)
4. `full_name` (fallback)
5. `name` (compatibilidade com dados antigos)

#### Cache Thread-Safe:
- **TTL**: 5 minutos
- **Invalidação**: Automática ao salvar/deletar pessoas
- **Performance**: Evita consultas repetidas ao Firestore

### 2. **Modelos de Dados (models.py)**

#### Campos Adicionados:
```python
# Em Cliente e ParteContraria
nome_exibicao: str    # Campo obrigatório para exibição
display_name: str     # Mantido para compatibilidade
```

#### Colunas de Tabela:
- Atualizadas para usar `nome_exibicao` como campo principal
- Label: "Nome de Exibição"

### 3. **Funções de Salvamento**

#### Garantias Implementadas:
- `nome_exibicao` sempre preenchido (obrigatório)
- Fallback automático: `display_name` → `full_name` → `name` → "Sem nome"
- Sincronização com `display_name` para compatibilidade
- Invalidação automática do cache

### 4. **Aplicação nos Módulos**

#### **Módulo de Casos:**
- **ui_components.py**: Cards de casos usam função centralizada
- **utils.py**: `get_short_name_helper()` migrada para `get_display_name()`

#### **Módulo de Processos:**
- **utils.py**: `get_short_name()` migrada para função centralizada
- **processos_page.py**: `_get_priority_name()` atualizada
- **acesso_processos_page.py**: `_get_priority_name()` atualizada
- **simple_modal.py**: Dropdowns usam regra centralizada

#### **Módulo de Pessoas:**
- **business_logic.py**: `prepare_*_row_data()` incluem `nome_exibicao`
- **ui_dialogs.py**: Formulários salvam em ambos os campos
- **ui_components.py**: Input com tooltip explicativo

---

## 📦 Script de Backfill

### **Localização**: `scripts/backfill_display_names.py`

### **Funcionalidades**:
- ✅ Modo simulação (`--dry-run`)
- ✅ Modo verboso (`--verbose`) 
- ✅ Relatório detalhado de mudanças
- ✅ Tratamento de erros robusto
- ✅ Validação de dados antes da atualização

### **Uso**:
```bash
# Simulação (recomendado primeiro)
python3 scripts/backfill_display_names.py --dry-run --verbose

# Execução real
python3 scripts/backfill_display_names.py
```

### **Resultado do Teste**:
- **12 registros** processados (9 clientes + 3 outros envolvidos)
- **100% sucesso** na simulação
- **Fontes**: 10 de `display_name`, 2 de `full_name`

---

## 🔄 Compatibilidade e Transição

### **Estratégia de Migração**:
1. **Fase 1**: Implementação com dupla gravação (`nome_exibicao` + `display_name`)
2. **Fase 2**: Backfill de dados existentes
3. **Fase 3**: Uso universal da função centralizada
4. **Fase 4**: (Futuro) Remoção gradual de campos antigos

### **Campos Mantidos**:
- `display_name` - Compatibilidade durante transição
- `name` - Compatibilidade com dados legados
- `full_name` - Campo principal de nome completo

---

## 🎨 Benefícios da Implementação

### **Consistência Visual**:
- ✅ Mesmo nome exibido em **todos** os módulos
- ✅ Cards de casos mostram nomes padronizados
- ✅ Tabelas de processos com exibição uniforme
- ✅ Formulários e modais consistentes

### **Performance**:
- ✅ Cache thread-safe reduz consultas ao Firestore
- ✅ Invalidação inteligente apenas quando necessário
- ✅ Busca otimizada por tipo de pessoa

### **Manutenibilidade**:
- ✅ Ponto único de verdade para nomes de exibição
- ✅ Função reutilizável em todo o projeto
- ✅ Fácil atualização de regras de prioridade
- ✅ Tratamento centralizado de erros

### **Experiência do Usuário**:
- ✅ Nomes familiares (apelidos/siglas) sempre visíveis
- ✅ Tooltips informativos em formulários
- ✅ Identificação rápida de pessoas em listas
- ✅ Consistência entre diferentes telas

---

## 🧪 Validação e Testes

### **Testes Realizados**:
- ✅ Script de backfill em modo simulação
- ✅ Verificação de linting em todos os arquivos
- ✅ Validação de compatibilidade com dados existentes
- ✅ Teste de prioridade de campos

### **Cenários Cobertos**:
- ✅ Pessoas com `nickname` definido
- ✅ Pessoas apenas com `display_name`
- ✅ Pessoas apenas com `full_name`
- ✅ Pessoas com dados legados (`name`)
- ✅ Casos extremos (campos vazios)

---

## 📚 Próximos Passos Recomendados

### **Imediatos**:
1. **Executar backfill** em produção: `python3 scripts/backfill_display_names.py`
2. **Testar interface** para verificar exibição correta
3. **Validar performance** do cache em uso real

### **Médio Prazo**:
1. **Monitorar logs** para identificar possíveis problemas
2. **Coletar feedback** dos usuários sobre consistência
3. **Otimizar cache** se necessário (ajustar TTL)

### **Longo Prazo**:
1. **Considerar remoção** de campos de compatibilidade
2. **Expandir funcionalidade** para outros módulos se necessário
3. **Documentar padrões** para novos desenvolvimentos

---

## 🔍 Arquivos Modificados

### **Core**:
- `mini_erp/core.py` - Funções centralizadas e cache

### **Modelos**:
- `mini_erp/pages/pessoas/models.py` - Definições de tipos

### **Módulo Casos**:
- `mini_erp/pages/casos/ui_components.py` - Cards de casos
- `mini_erp/pages/casos/utils.py` - Função auxiliar

### **Módulo Processos**:
- `mini_erp/pages/processos/utils.py` - Função de nomes
- `mini_erp/pages/processos/processos_page.py` - Tabela principal
- `mini_erp/pages/processos/acesso_processos_page.py` - Tabela de acesso
- `mini_erp/pages/processos/simple_modal.py` - Modal de criação

### **Módulo Pessoas**:
- `mini_erp/pages/pessoas/business_logic.py` - Preparação de dados
- `mini_erp/pages/pessoas/ui_dialogs.py` - Formulários
- `mini_erp/pages/pessoas/ui_components.py` - Componentes

### **Scripts**:
- `scripts/backfill_display_names.py` - Script de migração

---

## ✅ Conclusão

A implementação da regra centralizada de "Nome de Exibição" foi **concluída com sucesso**, garantindo:

- **Consistência** total na exibição de nomes
- **Performance** otimizada com cache inteligente  
- **Compatibilidade** com dados existentes
- **Facilidade** de manutenção futura

O sistema agora possui um **ponto único de verdade** para exibição de nomes de pessoas, eliminando inconsistências e melhorando significativamente a experiência do usuário.





