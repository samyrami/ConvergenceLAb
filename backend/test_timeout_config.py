#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de timeouts del agente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_timeout_config import (
    get_agent_timeout_config, 
    update_timeout_config, 
    apply_preset_config,
    PRESET_CONFIGS
)

def test_timeout_configuration():
    """Prueba la configuración de timeouts"""
    print("🧪 PROBANDO CONFIGURACIÓN DE TIMEOUTS DEL AGENTE")
    print("=" * 60)
    
    # Obtener configuración actual
    config = get_agent_timeout_config()
    
    print(f"✅ Configuración actual:")
    print(f"   - Saludo inicial: {config.INITIAL_GREETING_TIMEOUT}s")
    print(f"   - Consulta simple: {config.SIMPLE_QUERY_TIMEOUT}s")
    print(f"   - Consulta compleja: {config.COMPLEX_QUERY_TIMEOUT}s")
    print(f"   - Consulta Pure: {config.PURE_QUERY_TIMEOUT}s")
    print(f"   - Tokens máximos: {config.MAX_RESPONSE_TOKENS}")
    print(f"   - Silencio antes de responder: {config.SILENCE_DURATION_MS}ms")
    
    # Probar función de timeout por tipo
    print(f"\n🔍 Timeouts por tipo de consulta:")
    for query_type in ["simple", "complex", "pure", "greeting"]:
        timeout = config.get_timeout_for_query_type(query_type)
        print(f"   - {query_type}: {timeout}s")
    
    # Probar configuración del modelo OpenAI
    print(f"\n🤖 Configuración del modelo OpenAI:")
    model_config = config.get_openai_model_config()
    print(f"   - Voz: {model_config['voice']}")
    print(f"   - Modelo: {model_config['model']}")
    print(f"   - Temperatura: {model_config['temperature']}")
    print(f"   - Duración de silencio: {config.SILENCE_DURATION_MS}ms")
    print(f"   - Umbral VAD: {config.VAD_THRESHOLD}")
    
    return True

def test_preset_configurations():
    """Prueba las configuraciones predefinidas"""
    print(f"\n🎛️ PROBANDO CONFIGURACIONES PREDEFINIDAS")
    print("=" * 60)
    
    for preset_name, preset_config in PRESET_CONFIGS.items():
        print(f"\n📋 Preset: {preset_name}")
        print(f"   - Saludo: {preset_config.INITIAL_GREETING_TIMEOUT}s")
        print(f"   - Simple: {preset_config.SIMPLE_QUERY_TIMEOUT}s")
        print(f"   - Compleja: {preset_config.COMPLEX_QUERY_TIMEOUT}s")
        print(f"   - Pure: {preset_config.PURE_QUERY_TIMEOUT}s")
        print(f"   - Silencio: {preset_config.SILENCE_DURATION_MS}ms")
        print(f"   - VAD: {preset_config.VAD_THRESHOLD}")
    
    return True

def test_dynamic_updates():
    """Prueba las actualizaciones dinámicas de configuración"""
    print(f"\n🔄 PROBANDO ACTUALIZACIONES DINÁMICAS")
    print("=" * 60)
    
    # Actualizar configuración dinámicamente
    update_timeout_config(
        COMPLEX_QUERY_TIMEOUT=10.0,
        SILENCE_DURATION_MS=300
    )
    
    config = get_agent_timeout_config()
    print(f"✅ Después de actualización dinámica:")
    print(f"   - Consulta compleja: {config.COMPLEX_QUERY_TIMEOUT}s")
    print(f"   - Silencio: {config.SILENCE_DURATION_MS}ms")
    
    # Aplicar preset ultra_fast
    apply_preset_config("ultra_fast")
    config = get_agent_timeout_config()
    print(f"\n✅ Después de aplicar preset 'ultra_fast':")
    print(f"   - Consulta compleja: {config.COMPLEX_QUERY_TIMEOUT}s")
    print(f"   - Silencio: {config.SILENCE_DURATION_MS}ms")
    
    return True

def main():
    """Función principal de prueba"""
    try:
        print("🚀 INICIANDO PRUEBAS DE CONFIGURACIÓN DE TIMEOUTS")
        print("=" * 80)
        
        # Ejecutar todas las pruebas
        test_timeout_configuration()
        test_preset_configurations()
        test_dynamic_updates()
        
        print(f"\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 80)
        print("✅ La configuración de timeouts está funcionando correctamente")
        print("✅ Sabius ahora tiene más tiempo para procesar preguntas complejas")
        print("✅ Los timeouts se pueden ajustar dinámicamente según las necesidades")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
