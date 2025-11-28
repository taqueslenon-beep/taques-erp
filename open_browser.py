#!/usr/bin/env python3
"""
Script para abrir o navegador na porta correta do servidor TAQUES ERP.
Detecta automaticamente qual porta está em uso (8081-8090) e abre o navegador.
"""
import socket
import webbrowser
import sys

def find_active_port():
    """Encontra a porta ativa do servidor (8081-8090)."""
    base_port = 8081
    max_ports = 10
    
    for i in range(max_ports):
        port = base_port + i
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:  # Porta está em uso e respondendo
                return port
        except Exception:
            continue
    
    return None

def main():
    port = find_active_port()
    
    if port:
        url = f'http://localhost:{port}'
        print(f'✅ Servidor encontrado na porta {port}')
    else:
        # Se não encontrou, tenta a porta padrão (8081)
        # O navegador vai mostrar erro se não estiver rodando, mas pelo menos abre
        port = 8081
        url = f'http://localhost:{port}'
        print(f'⚠️  Servidor não detectado. Tentando porta padrão {port}...')
        print('💡 Se não abrir, inicie o servidor com: python3 -m mini_erp.main')
    
    print(f'🌐 Abrindo navegador em {url}...')
    webbrowser.open(url)

if __name__ == '__main__':
    main()

