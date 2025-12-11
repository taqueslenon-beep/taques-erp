# Correção de Bug - Upload de Foto do Perfil

## Data
2024-12-19

## Erro Identificado
- **Mensagem**: `object of type 'coroutine' has no len()`
- **Local**: Funcionalidade de alterar foto do perfil em `/configuracoes`
- **Arquivo**: `mini_erp/pages/configuracoes.py` (linha 365)

## Causa
A função `file_upload.read()` do NiceGUI é assíncrona e retorna uma coroutine. O código estava chamando-a sem `await`, resultando em uma coroutine sendo armazenada em `img_bytes`. Ao tentar validar o tamanho com `len(img_bytes)`, o Python lançava o erro porque não é possível obter o tamanho de uma coroutine.

## Código Antes (ERRADO)
```python
img_bytes = file_upload.read()  # Retorna coroutine, não bytes

# Validação de tamanho (5MB)
if len(img_bytes) > 5 * 1024 * 1024:  # ❌ ERRO: len() em coroutine
    ...
```

## Código Depois (CORRETO)
```python
img_bytes = await file_upload.read()  # ✅ Aguarda e retorna bytes reais

# Validação de tamanho (5MB)
if len(img_bytes) > 5 * 1024 * 1024:  # ✅ Funciona corretamente
    ...
```

## Correção Aplicada
Adicionado `await` antes de `file_upload.read()` na linha 365 do arquivo `mini_erp/pages/configuracoes.py`.

**Linha corrigida:**
```362:365:mini_erp/pages/configuracoes.py
                                # Lê os bytes do arquivo
                                # FileUpload é um objeto file-like com método read() assíncrono
                                # SmallFileUpload não tem seek(), então lemos diretamente
                                img_bytes = await file_upload.read()
```

## Verificações Realizadas
- ✅ Função `handle_upload` já estava marcada como `async def` (linha 342)
- ✅ Handler do evento de upload suporta async
- ✅ Todas as operações assíncronas no fluxo têm `await` apropriado
- ✅ Nenhum erro de lint encontrado

## Teste Recomendado
1. Acessar página de Configurações
2. Tentar fazer upload de uma imagem para o perfil
3. Verificar se a validação de tamanho funciona corretamente
4. Confirmar que o upload é processado sem erros

## Observações
- A função `handle_upload` já era assíncrona (`async def`), então apenas foi necessário adicionar o `await`
- O comentário no código foi atualizado para mencionar que o método `read()` é assíncrono




