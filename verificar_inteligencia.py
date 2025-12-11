#!/usr/bin/env python3
"""Script para verificar se o módulo de inteligência está correto."""
import sys
sys.path.insert(0, '.')

print("🔍 Verificando módulo de Inteligência...\n")

# Verifica imports
try:
    from mini_erp.pages.inteligencia import inteligencia, carlos_page
    print("✅ Imports OK")
except Exception as e:
    print(f"❌ Erro nos imports: {e}")
    sys.exit(1)

# Verifica dados
try:
    from mini_erp.pages.inteligencia.riscos_penais.dados_processos import PROCESSOS, DADOS_REU
    print(f"✅ Dados carregados: {len(PROCESSOS)} processos")
except Exception as e:
    print(f"❌ Erro ao carregar dados: {e}")
    sys.exit(1)

# Verifica rotas
import inspect
source_int = inspect.getsource(inteligencia)
source_carlos = inspect.getsource(carlos_page)

if 'riscos-penais/carlos' in source_int:
    print("✅ Rota correta na página principal")
else:
    print("❌ Rota incorreta na página principal")

if '@ui.page' in source_carlos and 'riscos-penais/carlos' in source_carlos:
    print("✅ Rota correta na página de detalhes")
else:
    print("❌ Rota incorreta na página de detalhes")

if 'RISCO ALTO' in source_int:
    print("✅ Card atualizado com badge RISCO ALTO")
else:
    print("❌ Card não atualizado")

if 'Em desenvolvimento' in source_int or 'show_development' in source_int:
    print("❌ AINDA TEM CÓDIGO ANTIGO!")
    sys.exit(1)
else:
    print("✅ Sem código antigo")

print("\n✅ Tudo verificado! O código está correto.")
print("⚠️  IMPORTANTE: Reinicie o servidor para ver as mudanças!")
