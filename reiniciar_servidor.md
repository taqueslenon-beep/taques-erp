# 🔄 REINICIAR SERVIDOR

O código está correto, mas o servidor precisa ser REINICIADO para carregar as mudanças.

## Passos:

1. **PARE o servidor atual:**
   - Vá no terminal onde o servidor está rodando
   - Pressione `Ctrl + C`

2. **INICIE novamente:**
   ```bash
   python3 -m mini_erp.main
   ```
   Ou se usar outro script:
   ```bash
   python3 dev_server.py
   ```

3. **No navegador:**
   - Acesse: http://localhost:8081/inteligencia
   - Faça hard refresh: Cmd+Shift+R (Mac) ou Ctrl+F5 (Windows)

## Verificação:

Se você vê o card "Riscos Penais - Carlos" com o badge "3 ações penais", 
o código está correto! Se ainda aparece "Em desenvolvimento", o servidor 
não foi reiniciado.

