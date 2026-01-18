#!/usr/bin/env python3
"""
Script de Debug - Ordem das Audiências
Verifica os timestamps reais e a ordenação
"""

import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mini_erp.firebase_config import get_db

def debug_audiencias():
    """Debug das audiências no Firebase"""
    print("=" * 80)
    print("🔍 DEBUG - ORDEM DAS AUDIÊNCIAS")
    print("=" * 80)
    
    db = get_db()
    
    # Buscar todas as audiências direto do Firebase
    print("\n📊 Buscando audiências do Firebase...")
    docs = db.collection('audiencias').stream()
    
    audiencias = []
    for doc in docs:
        audiencia = doc.to_dict()
        audiencia['_id'] = doc.id
        audiencias.append(audiencia)
    
    print(f"✅ Total: {len(audiencias)} audiência(s)")
    
    # Mostrar ANTES da ordenação
    print("\n" + "=" * 80)
    print("📋 AUDIÊNCIAS ANTES DA ORDENAÇÃO (ordem do Firebase):")
    print("=" * 80)
    
    for i, aud in enumerate(audiencias, 1):
        titulo = aud.get('titulo', '[SEM TÍTULO]')
        data_hora_inicio = aud.get('data_hora_inicio')
        
        if data_hora_inicio:
            dt = datetime.fromtimestamp(data_hora_inicio)
            data_str = dt.strftime('%d/%m/%Y %H:%M')
            timestamp_str = f"timestamp={data_hora_inicio}"
        else:
            data_str = "[SEM DATA]"
            timestamp_str = "timestamp=None"
        
        print(f"{i}. {titulo[:50]}")
        print(f"   Data: {data_str} ({timestamp_str})")
    
    # Aplicar ordenação
    print("\n" + "=" * 80)
    print("🔧 APLICANDO ORDENAÇÃO: key=lambda x: x.get('data_hora_inicio', float('inf'))")
    print("=" * 80)
    
    audiencias.sort(key=lambda x: x.get('data_hora_inicio', float('inf')))
    
    # Mostrar DEPOIS da ordenação
    print("\n" + "=" * 80)
    print("📋 AUDIÊNCIAS DEPOIS DA ORDENAÇÃO (próximas primeiro):")
    print("=" * 80)
    
    hoje = datetime.now()
    
    for i, aud in enumerate(audiencias, 1):
        titulo = aud.get('titulo', '[SEM TÍTULO]')
        data_hora_inicio = aud.get('data_hora_inicio')
        
        if data_hora_inicio:
            dt = datetime.fromtimestamp(data_hora_inicio)
            data_str = dt.strftime('%d/%m/%Y %H:%M')
            timestamp_str = f"timestamp={data_hora_inicio}"
            
            # Calcular dias até
            dias = (dt - hoje).days
            if dias < 0:
                quando = f"(há {abs(dias)} dias)"
            elif dias == 0:
                quando = "(HOJE)"
            elif dias == 1:
                quando = "(AMANHÃ)"
            else:
                quando = f"(em {dias} dias)"
            
            status = quando
        else:
            data_str = "[SEM DATA]"
            timestamp_str = "timestamp=None"
            status = ""
        
        print(f"{i}. {titulo[:50]}")
        print(f"   Data: {data_str} {status}")
        print(f"   {timestamp_str}")
    
    # Verificar audiências específicas
    print("\n" + "=" * 80)
    print("🔎 BUSCANDO AUDIÊNCIAS ESPECÍFICAS:")
    print("=" * 80)
    
    alvos = ['edilson', 'ricardo', 'marcos', 'hiroaki', 'nagano']
    
    for alvo in alvos:
        for aud in audiencias:
            titulo = aud.get('titulo', '').lower()
            clientes = aud.get('clientes_ids', [])
            
            if alvo in titulo:
                data_hora_inicio = aud.get('data_hora_inicio')
                if data_hora_inicio:
                    dt = datetime.fromtimestamp(data_hora_inicio)
                    data_str = dt.strftime('%d/%m/%Y %H:%M')
                else:
                    data_str = "[SEM DATA]"
                
                print(f"\n   '{alvo}' encontrado em: {aud.get('titulo')}")
                print(f"   Data: {data_str}")
                print(f"   Timestamp: {data_hora_inicio}")
                break
    
    print("\n" + "=" * 80)
    print("✅ DEBUG CONCLUÍDO")
    print("=" * 80)


if __name__ == '__main__':
    debug_audiencias()
