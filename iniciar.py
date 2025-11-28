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
PORTA_PADRAO = 8080
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
    while porta < PORTA_PADRAO + 10:
        if verificar_porta(porta):
            return porta
        porta += 1
    return None


def abrir_navegador(porta):
    """Aguarda o servidor iniciar e abre o navegador"""
    time.sleep(3)
    url = f'http://{HOST}:{porta}'
    try:
        webbrowser.open(url)
        print(f'\n✅ Navegador aberto em: {url}\n')
    except Exception as e:
        print(f'\n⚠️  Erro ao abrir navegador: {e}')
        print(f'   Abra manualmente: {url}\n')


def main():
    """Inicia o servidor TAQUES ERP"""
    print('=' * 60)
    print('🚀 INICIANDO TAQUES ERP')
    print('=' * 60)
    
    # Encontra porta disponível
    porta = encontrar_porta_disponivel()
    if not porta:
        print(f'\n❌ Erro: Nenhuma porta disponível entre {PORTA_PADRAO} e {PORTA_PADRAO + 9}')
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
    try:
        subprocess.run([
            sys.executable,
            '-m',
            'mini_erp.main'
        ], cwd=PASTA_PROJETO)
        
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


