# Instruções de Teste - Acompanhamento de Terceiros (Fase 1)

## Pré-requisitos

1. **Ambiente Python configurado**

   ```bash
   python --version  # Deve ser 3.8+
   ```

2. **Dependências instaladas**

   ```bash
   pip install -r requirements.txt
   ```

3. **Firebase configurado**

   - Arquivo `firebase-credentials.json` presente
   - Ou variáveis de ambiente configuradas
   - Conexão com Firestore funcionando

4. **Servidor rodando**
   ```bash
   python iniciar.py
   # ou
   python dev_server.py
   ```

---

## Testes Manuais

### Teste 1: Verificar Botão na Página de Processos

**Objetivo:** Confirmar que o botão aparece corretamente.

**Passos:**

1. Acesse: `http://localhost:8080/processos`
2. Faça login se necessário
3. Verifique se o botão **"+ Novo Acompanhamento de Terceiro"** aparece:
   - Localização: Ao lado de "+ Novo Processo Futuro"
   - Ícone: Link (cadeia)
   - Cor: Verde escuro (primary)

**Resultado Esperado:**

- ✅ Botão visível e clicável
- ✅ Ao clicar, mostra notificação informativa

**Erros Comuns:**

- ❌ Botão não aparece → Verificar se o código foi aplicado corretamente
- ❌ Erro ao clicar → Verificar console do navegador

---

### Teste 2: Verificar Card no Painel

**Objetivo:** Confirmar que o card contador aparece e mostra o número correto.

**Passos:**

1. Acesse: `http://localhost:8080/`
2. Faça login se necessário
3. Na aba **"Totais"** (selecionada por padrão)
4. Role até a seção **"PROCESSOS"**
5. Verifique se o card **"Acompanhamentos de Terceiros"** aparece:
   - Localização: ANTES de "Processos Previstos"
   - Cor da borda: Laranja/âmbar (#f59e0b)
   - Número: 0 (se não houver acompanhamentos)

**Resultado Esperado:**

- ✅ Card visível com título correto
- ✅ Número exibido (mesmo que 0)
- ✅ Card clicável (mostra notificação ao clicar)

**Erros Comuns:**

- ❌ Card não aparece → Verificar código em `tab_visualizations.py`
- ❌ Número mostra "–" → Erro ao contar no banco, verificar logs

---

### Teste 3: Criar Acompanhamento (via Console Python)

**Objetivo:** Testar a função de criação diretamente.

**Passos:**

1. Abra o console Python no terminal:

   ```bash
   python
   ```

2. Execute o seguinte código:

   ```python
   import sys
   sys.path.append('.')

   from mini_erp.pages.processos.database import criar_acompanhamento, contar_acompanhamentos_ativos

   # Dados de teste
   dados_teste = {
       "client_id": "test-cliente-001",  # Use um ID de cliente existente
       "third_party_name": "Terceiro Teste",
       "process_title": "Processo de Teste - Acompanhamento",
       "process_number": "1234567-89.2023.4.05.0000",
       "monitoring_type": "Processo Judicial",
       "start_date": "15/01/2025",
       "status": "ativo",
       "observations": "Acompanhamento criado para teste"
   }

   # Criar acompanhamento
   try:
       doc_id = criar_acompanhamento(dados_teste)
       print(f"✅ Acompanhamento criado com ID: {doc_id}")

       # Verificar contagem
       total = contar_acompanhamentos_ativos()
       print(f"✅ Total de acompanhamentos ativos: {total}")
   except Exception as e:
       print(f"❌ Erro: {e}")
       import traceback
       traceback.print_exc()
   ```

3. Verifique no Firebase Console:
   - Acesse: https://console.firebase.google.com
   - Navegue até: Firestore Database
   - Verifique a coleção `third_party_monitoring`
   - Deve conter o documento criado

**Resultado Esperado:**

- ✅ Função retorna ID do documento
- ✅ Documento aparece no Firestore
- ✅ Contagem atualiza corretamente

**Erros Comuns:**

- ❌ `client_id` não encontrado → Use um ID de cliente existente
- ❌ Erro de conexão → Verificar credenciais do Firebase

---

### Teste 4: Contar Acompanhamentos Ativos

**Objetivo:** Verificar se a contagem funciona corretamente.

**Passos:**

1. No console Python, execute:

   ```python
   from mini_erp.pages.processos.database import contar_acompanhamentos_ativos

   total = contar_acompanhamentos_ativos()
   print(f"Total de acompanhamentos ativos: {total}")
   ```

2. Crie alguns acompanhamentos de teste com status diferentes:

   ```python
   # Ativo
   criar_acompanhamento({..., "status": "ativo"})

   # Concluído (não deve contar)
   criar_acompanhamento({..., "status": "concluído"})

   # Suspenso (não deve contar)
   criar_acompanhamento({..., "status": "suspenso"})
   ```

3. Verifique se a contagem considera apenas status `ativo`

**Resultado Esperado:**

- ✅ Conta apenas acompanhamentos com status `ativo`
- ✅ Ignora `concluído` e `suspenso`

---

### Teste 5: Verificar Atualização do Card no Painel

**Objetivo:** Confirmar que o card atualiza após criar acompanhamento.

**Passos:**

1. Acesse o Painel (`http://localhost:8080/`)
2. Anote o número no card "Acompanhamentos de Terceiros"
3. Crie um novo acompanhamento ativo (via console Python)
4. Recarregue a página do Painel (F5)
5. Verifique se o número no card aumentou

**Resultado Esperado:**

- ✅ Número atualiza após criar acompanhamento
- ✅ Número diminui ao deletar acompanhamento

---

## Testes Automatizados (Estrutura Futura)

### Estrutura de Testes Unitários

Crie um arquivo `tests/test_third_party_monitoring.py`:

```python
import unittest
from mini_erp.pages.processos.database import (
    criar_acompanhamento,
    contar_acompanhamentos_ativos,
    deletar_acompanhamento,
    obter_acompanhamento_por_id
)

class TestThirdPartyMonitoring(unittest.TestCase):

    def setUp(self):
        """Prepara dados de teste."""
        self.dados_teste = {
            "client_id": "test-cliente-001",
            "third_party_name": "Terceiro Teste",
            "process_title": "Processo de Teste",
            "monitoring_type": "Processo Judicial",
            "start_date": "15/01/2025",
            "status": "ativo"
        }

    def test_criar_acompanhamento(self):
        """Testa criação de acompanhamento."""
        doc_id = criar_acompanhamento(self.dados_teste)
        self.assertIsNotNone(doc_id)

        # Limpeza
        deletar_acompanhamento(doc_id)

    def test_contar_ativos(self):
        """Testa contagem de acompanhamentos ativos."""
        # Criar acompanhamento ativo
        doc_id = criar_acompanhamento(self.dados_teste)

        total_antes = contar_acompanhamentos_ativos()
        self.assertGreaterEqual(total_antes, 1)

        # Limpeza
        deletar_acompanhamento(doc_id)

    def test_obter_por_id(self):
        """Testa busca por ID."""
        doc_id = criar_acompanhamento(self.dados_teste)
        acompanhamento = obter_acompanhamento_por_id(doc_id)

        self.assertIsNotNone(acompanhamento)
        self.assertEqual(acompanhamento['process_title'], "Processo de Teste")

        # Limpeza
        deletar_acompanhamento(doc_id)

if __name__ == '__main__':
    unittest.main()
```

**Para executar:**

```bash
python -m pytest tests/test_third_party_monitoring.py -v
```

---

## Checklist de Validação

Antes de considerar a Fase 1 completa, verifique:

### Funcionalidade

- [ ] Botão aparece na página de Processos
- [ ] Card aparece no Painel
- [ ] Número no card é atualizado corretamente
- [ ] Funções CRUD funcionam sem erros

### Interface

- [ ] Botão com estilo consistente
- [ ] Card com cor laranja/âmbar
- [ ] Responsivo em diferentes tamanhos de tela

### Banco de Dados

- [ ] Coleção `third_party_monitoring` criada no Firestore
- [ ] Documentos salvos com todos os campos
- [ ] Timestamps (`created_at`, `updated_at`) gerados automaticamente

### Erros

- [ ] Mensagens de erro em português
- [ ] Tratamento de erros de conexão
- [ ] Validação de campos obrigatórios

---

## Limpeza Após Testes

### Deletar Dados de Teste

Execute no console Python:

```python
from mini_erp.pages.processos.database import obter_todos_acompanhamentos, deletar_acompanhamento

# Listar todos
todos = obter_todos_acompanhamentos()

# Deletar apenas os de teste
for acomp in todos:
    if "teste" in acomp.get('process_title', '').lower() or \
       "test" in acomp.get('process_title', '').lower():
        deletar_acompanhamento(acomp['_id'])
        print(f"✅ Deletado: {acomp['process_title']}")
```

---

## Troubleshooting

### Problema: Card mostra "–" ao invés de número

**Causa:** Erro ao contar no banco.

**Solução:**

1. Verificar logs do servidor
2. Verificar conexão com Firebase
3. Verificar se a coleção existe no Firestore

### Problema: Botão não aparece

**Causa:** Código não foi aplicado ou cache do navegador.

**Solução:**

1. Limpar cache do navegador (Ctrl+Shift+R)
2. Verificar se o código está em `processos_page.py`
3. Reiniciar servidor

### Problema: Erro ao criar acompanhamento

**Causa:** Credenciais do Firebase ou campos inválidos.

**Solução:**

1. Verificar `firebase-credentials.json`
2. Verificar campos obrigatórios preenchidos
3. Verificar logs detalhados no console

---

**Última atualização:** 2025-01-XX  
**Versão:** 1.0.0 (Fase 1)


