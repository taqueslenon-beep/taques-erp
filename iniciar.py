#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAQUES ERP - Script de Inicialização
=====================================
Inicia o servidor TAQUES ERP automaticamente.
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
import socket

# Configuração
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PORTA_PADRAO = 8081
HOST = '127.0.0.1'


def verificar_porta(porta):
    """Verifica se a porta está disponível"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((HOST, porta))
        sock.close()
        return result != 0  # True se disponível (não conseguiu conectar)
    except:
        return True


def encontrar_porta_disponivel():
    """Encontra a primeira porta disponível a partir da porta padrão"""
    porta = PORTA_PADRAO
    max_porta = 65535  # Porta máxima do sistema
    while porta <= max_porta:
        if verificar_porta(porta):
            return porta
        porta += 1
    return None


def servidor_pronto(porta, max_tentativas=30):
    """Verifica se o servidor está respondendo"""
    import urllib.request
    url = f'http://{HOST}:{porta}'
    for i in range(max_tentativas):
        try:
            req = urllib.request.urlopen(url, timeout=1)
            if req.getcode() == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def abrir_navegador(porta):
    """Aguarda o servidor iniciar e abre o navegador"""
    print(f'⏳ Aguardando servidor ficar pronto...')
    if servidor_pronto(porta):
        url = f'http://{HOST}:{porta}'
        try:
            webbrowser.open(url)
            print(f'\n✅ Servidor pronto! Navegador aberto em: {url}\n')
        except Exception as e:
            print(f'\n⚠️  Erro ao abrir navegador: {e}')
            print(f'   Abra manualmente: {url}\n')
    else:
        url = f'http://{HOST}:{porta}'
        print(f'\n⚠️  Servidor pode não estar pronto ainda.')
        print(f'   Tente acessar manualmente: {url}\n')


def main():
    """Inicia o servidor TAQUES ERP"""
    print('=' * 60)
    print('🚀 INICIANDO TAQUES ERP')
    print('=' * 60)
    
    # Encontra porta disponível
    porta = encontrar_porta_disponivel()
    if not porta:
        print(f'\n❌ Erro: Nenhuma porta disponível a partir de {PORTA_PADRAO}')
        print(f'   Encerre outros processos ou tente novamente.')
        sys.exit(1)
    
    if porta != PORTA_PADRAO:
        print(f'\n⚠️  Porta {PORTA_PADRAO} ocupada. Usando porta {porta}.')
    
    print(f'\n📡 Servidor iniciando em http://{HOST}:{porta}')
    print(f'⏳ Aguarde 2-3 segundos...')
    
    # Mudar para pasta do projeto
    os.chdir(PASTA_PROJETO)
    
    # Iniciar thread para abrir navegador
    thread = threading.Thread(target=lambda: abrir_navegador(porta), daemon=True)
    thread.start()
    
    # Define variável de ambiente para a porta
    os.environ['APP_PORT'] = str(porta)
    
    # Rodar o servidor
    # CONFIGURADO: Modo manual (sem auto-reload) - use scripts/reiniciar_servidor.sh para reiniciar
    # Para habilitar auto-reload, defina ENABLE_AUTO_RELOAD=true ou use dev_server.py diretamente
    usar_auto_reload = os.environ.get('ENABLE_AUTO_RELOAD', '').lower() == 'true'
    dev_server_path = os.path.join(PASTA_PROJETO, 'dev_server.py')
    
    if usar_auto_reload and os.path.exists(dev_server_path):
        print(f'\n🔄 Modo desenvolvimento: Auto-reload habilitado')
        print(f'   Mudanças em arquivos .py serão detectadas automaticamente')
        print(f'   A página recarregará sozinha quando você salvar arquivos\n')
        cmd = [sys.executable, 'dev_server.py']
    else:
        # Modo manual: usa main.py diretamente ou dev_server.py sem watchfiles
        if os.path.exists(dev_server_path):
            print(f'\n🔄 Modo manual: Auto-reload desabilitado')
            print(f'   Use scripts/reiniciar_servidor.sh para reiniciar o servidor')
            print(f'   Ou defina ENABLE_AUTO_RELOAD=true para habilitar auto-reload\n')
            # Define flag para desabilitar watchfiles no dev_server.py
            os.environ['DISABLE_AUTO_RELOAD'] = 'true'
            cmd = [sys.executable, 'dev_server.py']
        else:
            print(f'\n⚠️  dev_server.py não encontrado. Usando modo sem auto-reload.')
            cmd = [sys.executable, '-m', 'mini_erp.main']
    
    try:
        subprocess.run(cmd, cwd=PASTA_PROJETO)
        
    except KeyboardInterrupt:
        print('\n\n⛔ Servidor interrompido pelo usuário')
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ Erro ao iniciar servidor: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
