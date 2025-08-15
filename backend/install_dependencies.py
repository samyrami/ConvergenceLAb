#!/usr/bin/env python3
"""
SCRIPT DE INSTALACIÓN DE DEPENDENCIAS
Verifica e instala todas las dependencias necesarias para el agente
"""

import subprocess
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_package(package):
    """Instalar un paquete usando pip"""
    try:
        logger.info(f"Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error instalando {package}: {e}")
        return False

def verify_import(module_name, package_name=None):
    """Verificar que un módulo se pueda importar"""
    try:
        __import__(module_name)
        logger.info(f"✅ {module_name} se puede importar correctamente")
        return True
    except ImportError as e:
        logger.error(f"❌ No se puede importar {module_name}: {e}")
        if package_name:
            logger.info(f"Intentando instalar {package_name}...")
            return install_package(package_name)
        return False

def main():
    """Función principal de instalación"""
    logger.info("🚀 INICIANDO INSTALACIÓN DE DEPENDENCIAS PARA CONVERGENCE LAB AGENT")
    logger.info("=" * 70)
    
    # Lista de dependencias críticas
    critical_dependencies = [
        ("livekit", "livekit>=0.12.0"),
        ("livekit.agents", "livekit-agents>=0.8.0"),
        ("livekit.plugins.openai", "livekit-plugins-openai>=0.7.0"),
        ("livekit.plugins.silero", "livekit-plugins-silero>=0.7.0"),
        ("openai", "openai>=1.0.0"),
        ("dotenv", "python-dotenv>=1.0.0"),
        ("scrapfly", "scrapfly-sdk>=0.8.23"),
        ("bs4", "beautifulsoup4>=4.12.0"),
        ("requests", "requests>=2.31.0"),
    ]
    
    # Opcional pero recomendadas
    optional_dependencies = [
        ("numpy", "numpy>=1.24.0"),
        ("scipy", "scipy>=1.10.0"),
        ("loguru", "loguru>=0.7.0"),
    ]
    
    logger.info("📦 VERIFICANDO DEPENDENCIAS CRÍTICAS...")
    critical_success = True
    
    for module, package in critical_dependencies:
        if not verify_import(module, package):
            critical_success = False
    
    logger.info("\n📦 VERIFICANDO DEPENDENCIAS OPCIONALES...")
    for module, package in optional_dependencies:
        verify_import(module, package)
    
    logger.info("\n" + "=" * 70)
    
    if critical_success:
        logger.info("🎉 TODAS LAS DEPENDENCIAS CRÍTICAS ESTÁN DISPONIBLES")
        logger.info("✅ Tu agente está listo para ejecutarse")
        
        # Probar importación del agente
        try:
            logger.info("\n🧪 PROBANDO IMPORTACIÓN DEL AGENTE...")
            from agent import GovLabAssistant, PureDataLoader
            logger.info("✅ Agent.py se puede importar correctamente")
            
            # Verificar Pure
            pure_loader = PureDataLoader()
            if pure_loader.loaded:
                logger.info("✅ Pure integration funcionando")
            else:
                logger.warning("⚠️ Pure data no disponible (pero el agente funcionará)")
            
        except Exception as e:
            logger.error(f"❌ Error importando agent.py: {e}")
            critical_success = False
    
    if critical_success:
        logger.info("\n🚀 TODO LISTO PARA EJECUTAR:")
        logger.info("   python agent.py")
    else:
        logger.error("\n❌ HAY PROBLEMAS CON DEPENDENCIAS CRÍTICAS")
        logger.error("   Revisa los errores arriba e instala manualmente si es necesario")
    
    return critical_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
