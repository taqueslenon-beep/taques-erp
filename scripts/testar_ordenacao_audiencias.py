#!/usr/bin/env python3
"""
Script de Teste - Ordenação de Audiências
Valida que as audiências estão ordenadas das mais próximas para as mais distantes
"""

import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mini_erp.pages.audiencias.database import listar_audiencias

def testar_ordenacao():
    """Testa ordenação de audiências"""
    print("=" * 80)
    print("🧪 TESTE - ORDENAÇÃO DE AUDIÊNCIAS")
    print("=" * 80)
    
    print("\n📞 Buscando audiências...")
    audiencias = listar_audiencias()
    
    print(f"✅ Total de audiências: {len(audiencias)}")
    
    if not audiencias:
        print("\n⚠️  Nenhuma audiência encontrada no sistema.")
        return True
    
    # Verificar ordenação
    print("\n" + "=" * 80)
    print("📋 AUDIÊNCIAS EM ORDEM (DO PRESENTE PARA O FUTURO):")
    print("=" * 80)
    
    data_atual = datetime.now()
    audiencias_passadas = 0
    audiencias_futuras = 0
    
    datas_anteriores = []
    ordenacao_correta = True
    
    for i, audiencia in enumerate(audiencias, 1):
        data_hora = audiencia.get('data_hora')
        titulo = audiencia.get('titulo', '[SEM TÍTULO]')
        
        if data_hora:
            dt = datetime.fromtimestamp(data_hora)
            data_str = dt.strftime('%d/%m/%Y %H:%M')
            
            # Verificar se está no passado ou futuro
            if dt < data_atual:
                status_tempo = "🔴 PASSADA"
                audiencias_passadas += 1
            else:
                status_tempo = "🟢 FUTURA"
                audiencias_futuras += 1
            
            # Verificar ordenação crescente
            if datas_anteriores and data_hora < datas_anteriores[-1]:
                ordenacao_correta = False
                print(f"   {i:2d}. {data_str} - {titulo[:40]} {status_tempo} ❌ FORA DE ORDEM!")
            else:
                print(f"   {i:2d}. {data_str} - {titulo[:40]} {status_tempo}")
            
            datas_anteriores.append(data_hora)
        else:
            print(f"   {i:2d}. [SEM DATA] - {titulo[:40]} ⚠️")
    
    # Relatório
    print("\n" + "=" * 80)
    print("📊 ESTATÍSTICAS:")
    print("=" * 80)
    print(f"   Total: {len(audiencias)}")
    print(f"   Passadas: {audiencias_passadas}")
    print(f"   Futuras: {audiencias_futuras}")
    print(f"   Sem data: {len(audiencias) - audiencias_passadas - audiencias_futuras}")
    
    print("\n" + "=" * 80)
    print("🔍 VALIDAÇÃO DA ORDENAÇÃO:")
    print("=" * 80)
    
    if ordenacao_correta:
        print("   ✅ SUCESSO! Audiências estão em ordem cronológica crescente.")
        print("   ✅ As mais próximas aparecem primeiro.")
    else:
        print("   ❌ ERRO! Audiências NÃO estão em ordem cronológica.")
    
    # Mostrar próximas 3 audiências futuras
    print("\n" + "=" * 80)
    print("📅 PRÓXIMAS 3 AUDIÊNCIAS A ACONTECER:")
    print("=" * 80)
    
    futuras = [a for a in audiencias if a.get('data_hora', 0) >= data_atual.timestamp()]
    
    if futuras:
        for i, audiencia in enumerate(futuras[:3], 1):
            data_hora = audiencia.get('data_hora')
            titulo = audiencia.get('titulo', '[SEM TÍTULO]')
            if data_hora:
                dt = datetime.fromtimestamp(data_hora)
                data_str = dt.strftime('%d/%m/%Y às %H:%M')
                dias_ate = (dt - data_atual).days
                
                if dias_ate == 0:
                    quando = "HOJE"
                elif dias_ate == 1:
                    quando = "AMANHÃ"
                elif dias_ate < 0:
                    quando = f"há {abs(dias_ate)} dia(s)"
                else:
                    quando = f"em {dias_ate} dia(s)"
                
                print(f"   {i}. {titulo}")
                print(f"      📅 {data_str} ({quando})")
    else:
        print("   Nenhuma audiência futura agendada.")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 80)
    
    return ordenacao_correta


if __name__ == '__main__':
    resultado = testar_ordenacao()
    sys.exit(0 if resultado else 1)
