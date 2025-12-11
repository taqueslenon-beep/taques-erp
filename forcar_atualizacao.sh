#!/bin/bash
# Script para forçar atualização do painel

echo "🧹 Limpando cache do Python..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Cache limpo!"
echo ""
echo "📝 Próximos passos:"
echo "1. Pare o servidor (Ctrl+C no terminal onde está rodando)"
echo "2. Execute: python3 iniciar.py"
echo "3. No navegador: Cmd+Shift+R (Mac) ou Ctrl+Shift+R (Windows/Linux)"
echo ""








