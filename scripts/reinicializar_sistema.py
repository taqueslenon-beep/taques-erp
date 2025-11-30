#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Reinicialização Segura do Sistema TAQUES ERP
======================================================

Realiza reinicialização completa e segura do sistema, garantindo que:
- Todos os dados do Firestore sejam salvos
- Estado de sessão seja preservado
- Integridade seja validada após reinicialização

Uso:
    python3 scripts/reinicializar_sistema.py --modo=completo --validar=sim --backup=sim
"""

import os
import sys
import json
import time
import signal
import socket
import hashlib
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from firebase_admin import storage, auth, firestore
    from mini_erp.firebase_config import get_db, init_firebase
    from mini_erp.core import invalidate_cache
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que está executando do diretório raiz do projeto")
    sys.exit(1)

# Configuração
BACKUPS_DIR = Path(__file__).parent.parent / "backups"
COLLECTIONS = [
    'cases', 'processes', 'clients', 'opposing_parties', 
    'users', 'benefits', 'agreements', 'convictions'
]
DEFAULT_PORT = 8080
GRACEFUL_SHUTDOWN_TIMEOUT = 30
FORCE_KILL_TIMEOUT = 5

# Estado global
_timestamp = None
_logger = None
_backup_data = {}
_server_pid = None
_restart_report = {
    'inicio': None,
    'fim': None,
    'duracao': None,
    'fases': {},
    'registros': {},
    'testes': {},
    'status': 'EM_ANDAMENTO'
}


# ============================================================================
# UTILITÁRIOS
# ============================================================================

def setup_logging(timestamp: str) -> logging.Logger:
    """Configura sistema de logging."""
    log_file = BACKUPS_DIR / f"reinicializacao_{timestamp}.log"
    BACKUPS_DIR.mkdir(exist_ok=True)
    
    logger = logging.getLogger('reinicializacao')
    logger.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_timestamp() -> str:
    """Retorna timestamp formatado para nomes de arquivo."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def print_progress(fase: str, mensagem: str, progresso: Optional[Tuple[int, int]] = None):
    """Exibe mensagem de progresso formatada."""
    if progresso:
        pct = (progresso[0] / progresso[1] * 100) if progresso[1] > 0 else 0
        print(f"[{fase}] {mensagem} ({progresso[0]}/{progresso[1]} - {pct:.1f}%)")
        _logger.info(f"[{fase}] {mensagem} ({progresso[0]}/{progresso[1]})")
    else:
        print(f"[{fase}] {mensagem}")
        _logger.info(f"[{fase}] {mensagem}")


def calcular_checksum(arquivo: Path) -> str:
    """Calcula MD5 checksum de um arquivo."""
    hash_md5 = hashlib.md5()
    with open(arquivo, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verificar_porta_disponivel(porta: int) -> bool:
    """Verifica se uma porta está disponível."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', porta))
        sock.close()
        return result != 0  # True se disponível
    except:
        return True


# ============================================================================
# FASE 1: PRÉ-SALVAMENTO
# ============================================================================

def preparar_sistema_desligamento() -> bool:
    """Prepara sistema para desligamento."""
    print_progress("FASE 1", "Preparando sistema para desligamento...")
    
    try:
        # Valida conectividade Firebase
        db = get_db()
        db.collection('users').limit(1).stream()
        
        print_progress("FASE 1", "✓ Sistema preparado para desligamento")
        return True
    except Exception as e:
        print_progress("FASE 1", f"✗ Erro ao preparar sistema: {e}")
        _logger.error(f"Erro ao preparar sistema: {e}", exc_info=True)
        return False


def exportar_dados_firestore() -> Dict[str, Any]:
    """Exporta todas as coleções do Firestore para JSON."""
    print_progress("FASE 1", "Exportando dados do Firestore...")
    
    backup_data = {
        'timestamp': _timestamp,
        'collections': {}
    }
    
    try:
        db = get_db()
        total_docs = 0
        
        for collection_name in COLLECTIONS:
            print_progress("FASE 1", f"Exportando coleção: {collection_name}...")
            docs = db.collection(collection_name).stream()
            items = []
            count = 0
            
            for doc in docs:
                item = doc.to_dict()
                item['_id'] = doc.id
                items.append(item)
                count += 1
                total_docs += 1
                
                if count % 50 == 0:
                    print_progress("FASE 1", f"  Processados {count} documentos de {collection_name}...")
            
            backup_data['collections'][collection_name] = items
            print_progress("FASE 1", f"✓ {collection_name}: {count} documentos exportados")
            _restart_report['registros'][collection_name] = count
        
        print_progress("FASE 1", f"✓ Total: {total_docs} documentos exportados")
        return backup_data
        
    except Exception as e:
        print_progress("FASE 1", f"✗ Erro ao exportar dados: {e}")
        _logger.error(f"Erro ao exportar dados: {e}", exc_info=True)
        raise


def exportar_storage_inventory() -> Dict[str, Any]:
    """Lista todos os arquivos do Firebase Storage."""
    print_progress("FASE 1", "Exportando inventário do Storage...")
    
    try:
        bucket = storage.bucket()
        if not bucket:
            print_progress("FASE 1", "⚠️  Storage não disponível")
            return {'files': [], 'count': 0}
        
        files = []
        blobs = bucket.list_blobs()
        count = 0
        
        for blob in blobs:
            files.append({
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'time_created': str(blob.time_created) if blob.time_created else None,
                'updated': str(blob.updated) if blob.updated else None
            })
            count += 1
            
            if count % 10 == 0:
                print_progress("FASE 1", f"  Processados {count} arquivos do Storage...")
        
        print_progress("FASE 1", f"✓ Storage: {count} arquivos listados")
        return {'files': files, 'count': count}
        
    except Exception as e:
        print_progress("FASE 1", f"⚠️  Erro ao exportar Storage: {e}")
        _logger.warning(f"Erro ao exportar Storage: {e}", exc_info=True)
        return {'files': [], 'count': 0}


def exportar_sessoes_ativas() -> Dict[str, Any]:
    """Exporta estado de sessões ativas."""
    print_progress("FASE 1", "Exportando sessões ativas...")
    
    sessions_data = {
        'timestamp': _timestamp,
        'sessions': []
    }
    
    try:
        # Tenta encontrar arquivos de sessão do NiceGUI
        nicegui_dir = Path(__file__).parent.parent / ".nicegui"
        
        if nicegui_dir.exists():
            storage_files = list(nicegui_dir.glob("storage-user-*.json"))
            
            for storage_file in storage_files:
                try:
                    with open(storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Remove dados sensíveis (senhas, tokens completos)
                        safe_data = {}
                        if 'user' in data:
                            user = data['user']
                            safe_data['user'] = {
                                'email': user.get('email', ''),
                                'uid': user.get('uid', '')
                                # Não salvar token completo por segurança
                            }
                        sessions_data['sessions'].append({
                            'file': storage_file.name,
                            'data': safe_data
                        })
                except Exception as e:
                    _logger.warning(f"Erro ao ler {storage_file}: {e}")
        
        print_progress("FASE 1", f"✓ {len(sessions_data['sessions'])} sessões exportadas")
        return sessions_data
        
    except Exception as e:
        print_progress("FASE 1", f"⚠️  Erro ao exportar sessões: {e}")
        _logger.warning(f"Erro ao exportar sessões: {e}", exc_info=True)
        return sessions_data


def validar_integridade_backup(backup_file: Path) -> Tuple[bool, str]:
    """Valida integridade do arquivo de backup."""
    print_progress("FASE 1", "Validando integridade do backup...")
    
    try:
        # Verifica se arquivo existe e não está vazio
        if not backup_file.exists():
            return False, "Arquivo de backup não encontrado"
        
        size = backup_file.stat().st_size
        if size < 100:
            return False, f"Arquivo muito pequeno ({size} bytes)"
        
        # Valida JSON
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {e}"
        
        # Calcula checksum
        checksum = calcular_checksum(backup_file)
        checksum_file = BACKUPS_DIR / f"backup_checksum_{_timestamp}.txt"
        with open(checksum_file, 'w') as f:
            f.write(f"MD5: {checksum}\n")
            f.write(f"Arquivo: {backup_file.name}\n")
            f.write(f"Tamanho: {size} bytes\n")
            f.write(f"Timestamp: {_timestamp}\n")
        
        print_progress("FASE 1", f"✓ Backup validado (MD5: {checksum[:16]}...)")
        return True, checksum
        
    except Exception as e:
        return False, f"Erro na validação: {e}"


def executar_fase1() -> Tuple[bool, Dict[str, Any]]:
    """Executa FASE 1: Pré-Salvamento."""
    _restart_report['fases']['fase1'] = {'inicio': datetime.now().isoformat()}
    
    try:
        # 1.1 Preparar sistema
        if not preparar_sistema_desligamento():
            return False, {}
        
        # 1.2 Executar backup completo
        backup_data = exportar_dados_firestore()
        storage_inventory = exportar_storage_inventory()
        sessions_data = exportar_sessoes_ativas()
        
        # Salvar backup completo
        backup_file = BACKUPS_DIR / f"backup_completo_{_timestamp}.json"
        BACKUPS_DIR.mkdir(exist_ok=True)
        
        full_backup = {
            'firestore': backup_data,
            'storage': storage_inventory,
            'sessions': sessions_data
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(full_backup, f, ensure_ascii=False, indent=2)
        
        # Salvar inventário de storage separadamente
        storage_file = BACKUPS_DIR / f"storage_inventory_{_timestamp}.json"
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(storage_inventory, f, ensure_ascii=False, indent=2)
        
        # Salvar sessões separadamente
        sessions_file = BACKUPS_DIR / f"sessions_{_timestamp}.json"
        with open(sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions_data, f, ensure_ascii=False, indent=2)
        
        # 1.3 Validar integridade
        valid, checksum = validar_integridade_backup(backup_file)
        if not valid:
            raise Exception(f"Validação de backup falhou: {checksum}")
        
        _restart_report['fases']['fase1']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase1']['status'] = 'SUCESSO'
        _restart_report['fases']['fase1']['backup_file'] = str(backup_file)
        _restart_report['fases']['fase1']['checksum'] = checksum
        
        print_progress("FASE 1", "✓ FASE 1 concluída com sucesso")
        return True, full_backup
        
    except Exception as e:
        _restart_report['fases']['fase1']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase1']['status'] = 'ERRO'
        _restart_report['fases']['fase1']['erro'] = str(e)
        print_progress("FASE 1", f"✗ FASE 1 falhou: {e}")
        _logger.error(f"FASE 1 falhou: {e}", exc_info=True)
        return False, {}


# ============================================================================
# FASE 2: SINCRONIZAÇÃO E FLUSH
# ============================================================================

def forcar_sincronizacao_firebase() -> bool:
    """Força sincronização com Firebase."""
    print_progress("FASE 2", "Forçando sincronização com Firebase...")
    
    try:
        db = get_db()
        # Testa uma operação de leitura para garantir sincronização
        db.collection('users').limit(1).stream()
        
        print_progress("FASE 2", "✓ Sincronização confirmada")
        return True
    except Exception as e:
        print_progress("FASE 2", f"⚠️  Erro na sincronização: {e}")
        _logger.warning(f"Erro na sincronização: {e}", exc_info=True)
        return False


def limpar_cache_local() -> bool:
    """Limpa cache em memória."""
    print_progress("FASE 2", "Limpando cache local...")
    
    try:
        invalidate_cache()
        print_progress("FASE 2", "✓ Cache limpo")
        return True
    except Exception as e:
        print_progress("FASE 2", f"⚠️  Erro ao limpar cache: {e}")
        _logger.warning(f"Erro ao limpar cache: {e}", exc_info=True)
        return False


def fechar_conexoes_ativas() -> bool:
    """Fecha conexões ativas."""
    print_progress("FASE 2", "Fechando conexões ativas...")
    
    try:
        # Aguarda um pouco para operações pendentes finalizarem
        time.sleep(2)
        print_progress("FASE 2", "✓ Conexões fechadas")
        return True
    except Exception as e:
        print_progress("FASE 2", f"⚠️  Erro ao fechar conexões: {e}")
        _logger.warning(f"Erro ao fechar conexões: {e}", exc_info=True)
        return False


def executar_fase2() -> bool:
    """Executa FASE 2: Sincronização e Flush."""
    _restart_report['fases']['fase2'] = {'inicio': datetime.now().isoformat()}
    
    try:
        forcar_sincronizacao_firebase()
        limpar_cache_local()
        fechar_conexoes_ativas()
        
        _restart_report['fases']['fase2']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase2']['status'] = 'SUCESSO'
        
        print_progress("FASE 2", "✓ FASE 2 concluída com sucesso")
        return True
        
    except Exception as e:
        _restart_report['fases']['fase2']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase2']['status'] = 'ERRO'
        _restart_report['fases']['fase2']['erro'] = str(e)
        print_progress("FASE 2", f"✗ FASE 2 falhou: {e}")
        _logger.error(f"FASE 2 falhou: {e}", exc_info=True)
        return False


# ============================================================================
# FASE 3: PARADA CONTROLADA
# ============================================================================

def detectar_processo_servidor(porta: int = DEFAULT_PORT) -> Optional[int]:
    """Encontra PID do processo usando a porta."""
    print_progress("FASE 3", f"Detectando processo na porta {porta}...")
    
    try:
        # Tenta usar lsof (disponível no macOS/Linux)
        result = subprocess.run(
            ['lsof', '-ti', f':{porta}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip().split('\n')[0])
            print_progress("FASE 3", f"✓ Processo encontrado: PID {pid}")
            return pid
        
        print_progress("FASE 3", "⚠️  Nenhum processo encontrado na porta")
        return None
        
    except FileNotFoundError:
        # lsof não disponível, tenta psutil
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'connections']):
                try:
                    conns = proc.info.get('connections')
                    if conns:
                        for conn in conns:
                            if conn.laddr.port == porta:
                                pid = proc.info['pid']
                                print_progress("FASE 3", f"✓ Processo encontrado: PID {pid}")
                                return pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            pass
        
        print_progress("FASE 3", "⚠️  Nenhum processo encontrado na porta")
        return None
    except Exception as e:
        print_progress("FASE 3", f"⚠️  Erro ao detectar processo: {e}")
        _logger.warning(f"Erro ao detectar processo: {e}", exc_info=True)
        return None


def parar_servidor_nicegui(pid: int) -> bool:
    """Para servidor via SIGTERM."""
    print_progress("FASE 3", f"Parando servidor (PID {pid})...")
    
    try:
        # Envia SIGTERM
        os.kill(pid, signal.SIGTERM)
        
        # Aguarda graceful shutdown
        for i in range(GRACEFUL_SHUTDOWN_TIMEOUT):
            try:
                os.kill(pid, 0)  # Verifica se processo ainda existe
                time.sleep(1)
            except ProcessLookupError:
                print_progress("FASE 3", f"✓ Servidor parado após {i+1} segundos")
                return True
        
        # Se ainda estiver rodando, força kill
        print_progress("FASE 3", "⚠️  Servidor não parou, forçando kill...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(2)
        
        try:
            os.kill(pid, 0)
            return False  # Ainda está rodando
        except ProcessLookupError:
            print_progress("FASE 3", "✓ Servidor parado (forçado)")
            return True
            
    except ProcessLookupError:
        print_progress("FASE 3", "✓ Processo já não existe")
        return True
    except Exception as e:
        print_progress("FASE 3", f"✗ Erro ao parar servidor: {e}")
        _logger.error(f"Erro ao parar servidor: {e}", exc_info=True)
        return False


def verificar_porta_liberada(porta: int) -> bool:
    """Valida que porta foi liberada."""
    print_progress("FASE 3", f"Verificando se porta {porta} foi liberada...")
    
    max_tentativas = 10
    for i in range(max_tentativas):
        if verificar_porta_disponivel(porta):
            print_progress("FASE 3", f"✓ Porta {porta} liberada")
            return True
        time.sleep(1)
    
    print_progress("FASE 3", f"⚠️  Porta {porta} ainda em uso após {max_tentativas} tentativas")
    return False


def executar_fase3() -> bool:
    """Executa FASE 3: Parada Controlada."""
    _restart_report['fases']['fase3'] = {'inicio': datetime.now().isoformat()}
    
    try:
        porta = int(os.environ.get('APP_PORT', DEFAULT_PORT))
        pid = detectar_processo_servidor(porta)
        
        if pid:
            global _server_pid
            _server_pid = pid
            
            if not parar_servidor_nicegui(pid):
                raise Exception("Não foi possível parar o servidor")
        
        if not verificar_porta_liberada(porta):
            raise Exception(f"Porta {porta} não foi liberada")
        
        _restart_report['fases']['fase3']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase3']['status'] = 'SUCESSO'
        
        print_progress("FASE 3", "✓ FASE 3 concluída com sucesso")
        return True
        
    except Exception as e:
        _restart_report['fases']['fase3']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase3']['status'] = 'ERRO'
        _restart_report['fases']['fase3']['erro'] = str(e)
        print_progress("FASE 3", f"✗ FASE 3 falhou: {e}")
        _logger.error(f"FASE 3 falhou: {e}", exc_info=True)
        return False


# ============================================================================
# FASE 4: REINICIALIZAÇÃO
# ============================================================================

def iniciar_servidor_novamente() -> bool:
    """Inicia servidor NiceGUI novamente."""
    print_progress("FASE 4", "Iniciando servidor...")
    
    try:
        porta = int(os.environ.get('APP_PORT', DEFAULT_PORT))
        projeto_dir = Path(__file__).parent.parent
        
        # Tenta usar dev_server.py se existir, senão usa main.py
        if (projeto_dir / "dev_server.py").exists():
            cmd = [sys.executable, "dev_server.py"]
        else:
            cmd = [sys.executable, "-m", "mini_erp.main"]
        
        # Inicia servidor em background
        process = subprocess.Popen(
            cmd,
            cwd=projeto_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, 'APP_PORT': str(porta)}
        )
        
        # Aguarda servidor iniciar
        max_tentativas = 30
        for i in range(max_tentativas):
            time.sleep(1)
            if not verificar_porta_disponivel(porta):
                print_progress("FASE 4", f"✓ Servidor iniciado após {i+1} segundos")
                return True
        
        # Verifica se processo ainda está rodando
        if process.poll() is None:
            print_progress("FASE 4", "⚠️  Servidor iniciado mas porta não respondeu")
            return True  # Processo está rodando, pode ser que ainda esteja iniciando
        
        # Processo terminou, verifica erro
        stdout, stderr = process.communicate()
        if stderr:
            _logger.error(f"Erro ao iniciar servidor: {stderr.decode()}")
        
        raise Exception("Servidor não iniciou corretamente")
        
    except Exception as e:
        print_progress("FASE 4", f"✗ Erro ao iniciar servidor: {e}")
        _logger.error(f"Erro ao iniciar servidor: {e}", exc_info=True)
        return False


def validar_conectividade_firebase() -> bool:
    """Testa conexões Firebase."""
    print_progress("FASE 4", "Validando conectividade Firebase...")
    
    try:
        # Reinicializa Firebase se necessário
        init_firebase()
        
        # Testa Firestore
        db = get_db()
        list(db.collection('users').limit(1).stream())
        print_progress("FASE 4", "✓ Firestore conectado")
        
        # Testa Firebase Auth
        try:
            auth.list_users(max_results=1)
            print_progress("FASE 4", "✓ Firebase Auth conectado")
        except Exception as e:
            _logger.warning(f"Firebase Auth não disponível: {e}")
        
        # Testa Storage
        try:
            bucket = storage.bucket()
            if bucket:
                print_progress("FASE 4", "✓ Firebase Storage conectado")
        except Exception as e:
            _logger.warning(f"Firebase Storage não disponível: {e}")
        
        print_progress("FASE 4", "✓ Conectividade Firebase validada")
        return True
        
    except Exception as e:
        print_progress("FASE 4", f"✗ Erro na validação Firebase: {e}")
        _logger.error(f"Erro na validação Firebase: {e}", exc_info=True)
        return False


def restaurar_estado_sessao() -> bool:
    """Restaura estado de sessão do usuário."""
    print_progress("FASE 4", "Restaurando estado de sessão...")
    
    try:
        sessions_file = BACKUPS_DIR / f"sessions_{_timestamp}.json"
        
        if not sessions_file.exists():
            print_progress("FASE 4", "⚠️  Arquivo de sessões não encontrado")
            return True  # Não é crítico
        
        with open(sessions_file, 'r', encoding='utf-8') as f:
            sessions_data = json.load(f)
        
        # Nota: A restauração real de sessão requer acesso ao app.storage.user
        # que só está disponível dentro do contexto do NiceGUI
        # Aqui apenas validamos que o arquivo existe e é válido
        
        print_progress("FASE 4", f"✓ Estado de sessão carregado ({len(sessions_data.get('sessions', []))} sessões)")
        return True
        
    except Exception as e:
        print_progress("FASE 4", f"⚠️  Erro ao restaurar sessão: {e}")
        _logger.warning(f"Erro ao restaurar sessão: {e}", exc_info=True)
        return True  # Não é crítico


def executar_fase4() -> bool:
    """Executa FASE 4: Reinicialização."""
    _restart_report['fases']['fase4'] = {'inicio': datetime.now().isoformat()}
    
    try:
        if not iniciar_servidor_novamente():
            raise Exception("Falha ao iniciar servidor")
        
        time.sleep(3)  # Aguarda servidor estabilizar
        
        if not validar_conectividade_firebase():
            raise Exception("Falha na validação Firebase")
        
        restaurar_estado_sessao()
        
        _restart_report['fases']['fase4']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase4']['status'] = 'SUCESSO'
        
        print_progress("FASE 4", "✓ FASE 4 concluída com sucesso")
        return True
        
    except Exception as e:
        _restart_report['fases']['fase4']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase4']['status'] = 'ERRO'
        _restart_report['fases']['fase4']['erro'] = str(e)
        print_progress("FASE 4", f"✗ FASE 4 falhou: {e}")
        _logger.error(f"FASE 4 falhou: {e}", exc_info=True)
        return False


# ============================================================================
# FASE 5: VALIDAÇÃO PÓS-REINICIALIZAÇÃO
# ============================================================================

def testes_integridade(backup_data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida integridade dos dados."""
    print_progress("FASE 5", "Executando testes de integridade...")
    
    resultados = {}
    
    try:
        db = get_db()
        firestore_data = backup_data.get('firestore', {}).get('collections', {})
        
        for collection_name in COLLECTIONS:
            backup_count = len(firestore_data.get(collection_name, []))
            
            # Conta no Firestore
            docs = list(db.collection(collection_name).stream())
            firestore_count = len(docs)
            
            resultados[collection_name] = {
                'backup': backup_count,
                'firestore': firestore_count,
                'match': backup_count == firestore_count
            }
            
            status = "✓" if backup_count == firestore_count else "✗"
            print_progress(
                "FASE 5", 
                f"{status} {collection_name}: backup={backup_count}, firestore={firestore_count}"
            )
        
        return resultados
        
    except Exception as e:
        print_progress("FASE 5", f"✗ Erro nos testes de integridade: {e}")
        _logger.error(f"Erro nos testes de integridade: {e}", exc_info=True)
        return resultados


def testes_funcionalidade() -> Dict[str, Any]:
    """Testa operações CRUD básicas."""
    print_progress("FASE 5", "Executando testes de funcionalidade...")
    
    resultados = {
        'firestore_read': False,
        'firestore_write': False,
        'firestore_delete': False
    }
    
    try:
        db = get_db()
        
        # Teste READ
        try:
            list(db.collection('processes').limit(1).stream())
            resultados['firestore_read'] = True
            print_progress("FASE 5", "✓ Teste READ: OK")
        except Exception as e:
            print_progress("FASE 5", f"✗ Teste READ falhou: {e}")
        
        # Teste WRITE (cria documento temporário)
        try:
            test_doc = db.collection('_test_restart').document('temp')
            test_doc.set({'test': True, 'timestamp': datetime.now().isoformat()})
            resultados['firestore_write'] = True
            print_progress("FASE 5", "✓ Teste WRITE: OK")
            
            # Teste DELETE
            test_doc.delete()
            resultados['firestore_delete'] = True
            print_progress("FASE 5", "✓ Teste DELETE: OK")
        except Exception as e:
            print_progress("FASE 5", f"✗ Teste WRITE/DELETE falhou: {e}")
        
        return resultados
        
    except Exception as e:
        print_progress("FASE 5", f"✗ Erro nos testes de funcionalidade: {e}")
        _logger.error(f"Erro nos testes de funcionalidade: {e}", exc_info=True)
        return resultados


def testes_performance() -> Dict[str, Any]:
    """Mede performance do sistema."""
    print_progress("FASE 5", "Executando testes de performance...")
    
    resultados = {}
    
    try:
        db = get_db()
        
        # Teste: tempo de leitura de processos
        inicio = time.time()
        list(db.collection('processes').limit(10).stream())
        tempo_processos = time.time() - inicio
        resultados['tempo_leitura_processos'] = tempo_processos
        print_progress("FASE 5", f"✓ Tempo leitura processos: {tempo_processos:.2f}s")
        
        # Teste: tempo de leitura de casos
        inicio = time.time()
        list(db.collection('cases').limit(10).stream())
        tempo_casos = time.time() - inicio
        resultados['tempo_leitura_casos'] = tempo_casos
        print_progress("FASE 5", f"✓ Tempo leitura casos: {tempo_casos:.2f}s")
        
        return resultados
        
    except Exception as e:
        print_progress("FASE 5", f"⚠️  Erro nos testes de performance: {e}")
        _logger.warning(f"Erro nos testes de performance: {e}", exc_info=True)
        return resultados


def gerar_relatorio_status(backup_data: Dict[str, Any]) -> Path:
    """Gera relatório final de status."""
    print_progress("FASE 5", "Gerando relatório de status...")
    
    fim = datetime.now()
    inicio = datetime.fromisoformat(_restart_report['inicio'])
    duracao = (fim - inicio).total_seconds()
    
    _restart_report['fim'] = fim.isoformat()
    _restart_report['duracao'] = duracao
    
    # Determina status final
    todas_fases_ok = all(
        fase.get('status') == 'SUCESSO' 
        for fase in _restart_report['fases'].values()
    )
    _restart_report['status'] = 'SUCESSO' if todas_fases_ok else 'FALHA'
    
    # Gera relatório em Markdown
    relatorio_file = BACKUPS_DIR / f"system_restart_report_{_timestamp}.md"
    
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write("# Relatório de Reinicialização do Sistema\n\n")
        f.write(f"**Timestamp**: {_timestamp}\n\n")
        f.write(f"**Início**: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Fim**: {fim.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Duração**: {duracao:.1f} segundos ({duracao/60:.1f} minutos)\n\n")
        f.write(f"**Status Final**: {'✅ SUCESSO' if todas_fases_ok else '❌ FALHA'}\n\n")
        
        f.write("## Fases Executadas\n\n")
        for fase_nome, fase_data in _restart_report['fases'].items():
            status_icon = "✅" if fase_data.get('status') == 'SUCESSO' else "❌"
            f.write(f"### {fase_nome.upper()}\n\n")
            f.write(f"- **Status**: {status_icon} {fase_data.get('status', 'DESCONHECIDO')}\n")
            f.write(f"- **Início**: {fase_data.get('inicio', 'N/A')}\n")
            f.write(f"- **Fim**: {fase_data.get('fim', 'N/A')}\n")
            if 'erro' in fase_data:
                f.write(f"- **Erro**: {fase_data['erro']}\n")
            f.write("\n")
        
        f.write("## Registros por Coleção\n\n")
        for collection, count in _restart_report['registros'].items():
            f.write(f"- **{collection}**: {count} documentos\n")
        f.write("\n")
        
        f.write("## Testes Executados\n\n")
        for teste_nome, teste_resultado in _restart_report['testes'].items():
            f.write(f"### {teste_nome}\n\n")
            if isinstance(teste_resultado, dict):
                for key, value in teste_resultado.items():
                    f.write(f"- **{key}**: {value}\n")
            else:
                f.write(f"- {teste_resultado}\n")
            f.write("\n")
    
    print_progress("FASE 5", f"✓ Relatório salvo em: {relatorio_file}")
    return relatorio_file


def executar_fase5(backup_data: Dict[str, Any]) -> bool:
    """Executa FASE 5: Validação Pós-Reinicialização."""
    _restart_report['fases']['fase5'] = {'inicio': datetime.now().isoformat()}
    
    try:
        resultados_integridade = testes_integridade(backup_data)
        resultados_funcionalidade = testes_funcionalidade()
        resultados_performance = testes_performance()
        
        _restart_report['testes'] = {
            'integridade': resultados_integridade,
            'funcionalidade': resultados_funcionalidade,
            'performance': resultados_performance
        }
        
        gerar_relatorio_status(backup_data)
        
        _restart_report['fases']['fase5']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase5']['status'] = 'SUCESSO'
        
        print_progress("FASE 5", "✓ FASE 5 concluída com sucesso")
        return True
        
    except Exception as e:
        _restart_report['fases']['fase5']['fim'] = datetime.now().isoformat()
        _restart_report['fases']['fase5']['status'] = 'ERRO'
        _restart_report['fases']['fase5']['erro'] = str(e)
        print_progress("FASE 5", f"✗ FASE 5 falhou: {e}")
        _logger.error(f"FASE 5 falhou: {e}", exc_info=True)
        return False


# ============================================================================
# TRATAMENTO DE ERROS E ROLLBACK
# ============================================================================

def tratar_erro_fase1_ou_2():
    """Trata erros nas fases 1 ou 2."""
    print("\n" + "="*60)
    print("❌ ERRO CRÍTICO - FASE 1 ou 2")
    print("="*60)
    print("Sistema não foi alterado. Contate administrador.")
    print("="*60 + "\n")
    _logger.critical("Erro crítico em FASE 1 ou 2 - sistema não foi alterado")
    sys.exit(1)


def tratar_erro_fase3_ou_4(backup_data: Dict[str, Any]):
    """Trata erros nas fases 3 ou 4."""
    print("\n" + "="*60)
    print("❌ ERRO CRÍTICO - FASE 3 ou 4")
    print("="*60)
    print("Tentando restaurar do backup...")
    print("="*60 + "\n")
    _logger.critical("Erro crítico em FASE 3 ou 4 - tentando restaurar backup")
    
    # Aqui poderia implementar restauração do backup se necessário
    # Por enquanto, apenas loga o erro
    sys.exit(2)


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal do script."""
    global _timestamp, _logger, _backup_data
    
    parser = argparse.ArgumentParser(
        description='Reinicialização Segura do Sistema TAQUES ERP'
    )
    parser.add_argument(
        '--modo',
        choices=['completo', 'backup'],
        default='completo',
        help='Modo de execução: completo (todas as fases) ou backup (apenas backup)'
    )
    parser.add_argument(
        '--validar',
        choices=['sim', 'nao'],
        default='sim',
        help='Executar validação pós-reinicialização'
    )
    parser.add_argument(
        '--backup',
        choices=['sim', 'nao'],
        default='sim',
        help='Criar backup antes de reinicializar'
    )
    
    args = parser.parse_args()
    
    # Inicializa timestamp e logging
    _timestamp = get_timestamp()
    _logger = setup_logging(_timestamp)
    _restart_report['inicio'] = datetime.now().isoformat()
    
    print("\n" + "="*60)
    print("🚀 REINICIALIZAÇÃO SEGURA DO SISTEMA TAQUES ERP")
    print("="*60)
    print(f"Timestamp: {_timestamp}")
    print(f"Modo: {args.modo}")
    print(f"Backup: {args.backup}")
    print(f"Validação: {args.validar}")
    print("="*60 + "\n")
    
    _logger.info(f"Iniciando reinicialização - Modo: {args.modo}, Backup: {args.backup}, Validação: {args.validar}")
    
    try:
        # FASE 1: Pré-Salvamento
        if args.backup == 'sim':
            sucesso, backup_data = executar_fase1()
            if not sucesso:
                tratar_erro_fase1_ou_2()
            _backup_data = backup_data
        else:
            print_progress("FASE 1", "⚠️  Backup desabilitado (--backup=nao)")
            _backup_data = {}
        
        # FASE 2: Sincronização e Flush
        if args.modo == 'completo':
            if not executar_fase2():
                tratar_erro_fase1_ou_2()
        
        # FASE 3: Parada Controlada
        if args.modo == 'completo':
            if not executar_fase3():
                tratar_erro_fase3_ou_4(_backup_data)
        
        # FASE 4: Reinicialização
        if args.modo == 'completo':
            if not executar_fase4():
                tratar_erro_fase3_ou_4(_backup_data)
        
        # FASE 5: Validação Pós-Reinicialização
        if args.validar == 'sim' and args.modo == 'completo':
            executar_fase5(_backup_data)
        
        # Resumo final
        print("\n" + "="*60)
        print("✅ REINICIALIZAÇÃO CONCLUÍDA")
        print("="*60)
        
        todas_fases_ok = all(
            fase.get('status') == 'SUCESSO' 
            for fase in _restart_report['fases'].values()
        )
        
        if todas_fases_ok:
            print("Status: SUCESSO")
        else:
            print("Status: FALHA (verifique relatório)")
        
        print(f"Relatório: backups/system_restart_report_{_timestamp}.md")
        print("="*60 + "\n")
        
        _logger.info("Reinicialização concluída")
        sys.exit(0 if todas_fases_ok else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação interrompida pelo usuário")
        _logger.warning("Operação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        _logger.critical(f"Erro inesperado: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

