# Como Fazer Mudanças Aparecerem no Front-End

## Problema

Quando você faz modificações no código, elas não aparecem automaticamente no navegador.

## Solução Rápida

### 1. Use o Servidor com Auto-Reload

**Sempre inicie o servidor usando:**

```bash
python3 iniciar.py
```

Ou diretamente:

```bash
python3 dev_server.py
```

O `iniciar.py` agora detecta automaticamente o `dev_server.py` e usa ele, que tem auto-reload habilitado.

### 2. Se Mudanças Não Aparecerem

**No navegador, pressione:**

- **F5** - Recarrega a página
- **Ctrl+Shift+R** (Windows/Linux) ou **Cmd+Shift+R** (Mac) - Hard refresh (limpa cache)

### 3. Verifique se o Servidor Detectou a Mudança

No terminal onde o servidor está rodando, você deve ver:

```
📝 Mudança detectada: mini_erp/pages/processos/processos_page.py
🔄 Reiniciando servidor...
```

Se não aparecer essa mensagem, o servidor pode não estar usando o `dev_server.py`.

## Como Verificar

### Verificar se está usando dev_server:

No terminal, quando iniciar o servidor, você deve ver:

```
🔄 Modo desenvolvimento: Auto-reload habilitado
   Mudanças em arquivos .py serão detectadas automaticamente
   A página recarregará sozinha quando você salvar arquivos
```

### Se não aparecer essa mensagem:

1. Pare o servidor (Ctrl+C)
2. Inicie novamente com: `python3 iniciar.py`
3. Ou diretamente: `python3 dev_server.py`

## Dicas

### Mudanças em Arquivos Python (.py)

- ✅ **Detectadas automaticamente** pelo `dev_server.py`
- ✅ Servidor reinicia sozinho
- ⚠️ Pode precisar pressionar **F5** no navegador

### Mudanças em Arquivos Estáticos (CSS, JS, imagens)

- ❌ **NÃO são detectadas automaticamente**
- ✅ Sempre pressione **F5** ou **Ctrl+Shift+R** no navegador

### Mudanças em Templates/HTML

- ✅ Se estiver em arquivo `.py` (NiceGUI), funciona como arquivo Python
- ⚠️ Pode precisar refresh manual no navegador

## Troubleshooting

### Problema: Mudanças não aparecem mesmo após F5

**Solução:**
1. Pare o servidor (Ctrl+C)
2. Limpe cache do navegador (Ctrl+Shift+Delete)
3. Reinicie o servidor: `python3 iniciar.py`
4. Abra navegador em modo anônimo/privado para testar

### Problema: Servidor não detecta mudanças

**Verifique:**
1. Está usando `dev_server.py`? (veja mensagem no terminal)
2. Arquivo salvo? (Cmd+S ou Ctrl+S)
3. Arquivo é `.py`? (outros tipos não são monitorados)
4. Arquivo está em `mini_erp/`? (fora do projeto não é monitorado)

### Problema: Servidor reinicia mas página não atualiza

**Solução:**
- Pressione **F5** no navegador
- Ou **Ctrl+Shift+R** para hard refresh
- NiceGUI às vezes precisa de refresh manual após restart

## Modo de Desenvolvimento vs Produção

### Desenvolvimento (com auto-reload)
```bash
python3 iniciar.py  # ou python3 dev_server.py
```

### Produção (sem auto-reload)
```bash
python3 -m mini_erp.main
```

## Resumo

1. ✅ Use `python3 iniciar.py` para desenvolvimento
2. ✅ Salve arquivos (Cmd+S / Ctrl+S)
3. ✅ Aguarde mensagem "Mudança detectada" no terminal
4. ✅ Pressione **F5** no navegador se necessário
5. ✅ Use **Ctrl+Shift+R** se F5 não funcionar

---

**Última atualização**: 2024-12-XX



