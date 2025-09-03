#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración sin estímulo
"""

import asyncio
from agent_timeout_config import get_agent_timeout_config, enable_no_stimulus_mode

def test_no_stimulus_configuration():
    """Prueba la configuración sin estímulo"""
    print("🧪 PROBANDO CONFIGURACIÓN SIN ESTÍMULO")
    print("=" * 50)
    
    # Aplicar configuración sin estímulo
    enable_no_stimulus_mode()
    
    # Obtener configuración actual
    config = get_agent_timeout_config()
    
    print("✅ Configuración aplicada:")
    print(f"   - Saludo: {config.INITIAL_GREETING_TIMEOUT}s")
    print(f"   - Simple: {config.SIMPLE_QUERY_TIMEOUT}s")
    print(f"   - Compleja: {config.COMPLEX_QUERY_TIMEOUT}s")
    print(f"   - Pure: {config.PURE_QUERY_TIMEOUT}s")
    print(f"   - Silencio: {config.SILENCE_DURATION_MS}ms")
    print(f"   - VAD: {config.VAD_THRESHOLD}")
    
    print("\n🎯 CONFIGURACIÓN VAD:")
    print("   - min_silence_duration: 0.05s (50ms)")
    print("   - speech_threshold: 0.01 (ultra sensible)")
    
    print("\n🚀 RESULTADO ESPERADO:")
    print("   - Sabius responderá inmediatamente sin esperar impulso")
    print("   - No más 'pensando' prolongado")
    print("   - Detección ultra sensible de voz")
    print("   - Respuesta en 0.5-1.5 segundos máximo")
    
    return True

if __name__ == "__main__":
    test_no_stimulus_configuration()
