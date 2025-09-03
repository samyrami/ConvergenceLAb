"""
Configuración centralizada de timeouts para el agente Sabius
Permite ajustar fácilmente los tiempos de respuesta para diferentes tipos de consultas
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentTimeoutConfig:
    """Configuración de timeouts para el agente conversacional"""
    
    # Timeouts para respuestas del agente (optimizados para respuestas rápidas)
    INITIAL_GREETING_TIMEOUT: float = 15.0  # Tiempo para saludo inicial (reducido)
    SIMPLE_QUERY_TIMEOUT: float = 10.0      # Tiempo para consultas simples (reducido)
    COMPLEX_QUERY_TIMEOUT: float = 25.0     # Tiempo para consultas complejas (reducido)
    PURE_QUERY_TIMEOUT: float = 20.0        # Tiempo para consultas de Pure (reducido)
    
    # Configuraciones del modelo OpenAI (optimizadas para respuestas rápidas)
    MAX_RESPONSE_TOKENS: int = 2048         # Máximo tokens de respuesta (reducido)
    SILENCE_DURATION_MS: int = 1000         # Tiempo de silencio antes de responder (reducido)
    VAD_THRESHOLD: float = 0.3              # Umbral de detección de voz (más sensible)
    
    # Configuraciones de reintentos
    MAX_RETRIES: int = 3                    # Máximo número de reintentos
    RETRY_BACKOFF_FACTOR: float = 2.0       # Factor de backoff exponencial
    
    # Configuraciones de monitoreo de sesión
    SESSION_HEALTH_CHECK_INTERVAL: float = 30.0  # Intervalo de verificación de salud
    CONNECTION_TIMEOUT: float = 10.0              # Timeout de conexión
    
    def get_timeout_for_query_type(self, query_type: str = "simple") -> float:
        """Obtiene el timeout apropiado según el tipo de consulta"""
        timeout_map = {
            "simple": self.SIMPLE_QUERY_TIMEOUT,
            "complex": self.COMPLEX_QUERY_TIMEOUT,
            "pure": self.PURE_QUERY_TIMEOUT,
            "greeting": self.INITIAL_GREETING_TIMEOUT
        }
        return timeout_map.get(query_type, self.SIMPLE_QUERY_TIMEOUT)
    
    def get_openai_model_config(self) -> dict:
        """Obtiene la configuración del modelo OpenAI optimizada para respuestas complejas"""
        return {
            # Configuración mínima - solo parámetros básicos disponibles
            "voice": "ash",
            "model": "gpt-4o-realtime-preview", 
            "temperature": 0.6
        }

# Instancia global de configuración - Configurada para respuestas sin estímulo
AGENT_TIMEOUT_CONFIG = AgentTimeoutConfig(
    INITIAL_GREETING_TIMEOUT=0.5,  # Mínimo absoluto
    SIMPLE_QUERY_TIMEOUT=0.5,      # Mínimo absoluto
    COMPLEX_QUERY_TIMEOUT=1.5,     # Mínimo para complejas
    PURE_QUERY_TIMEOUT=1.0,        # Mínimo para Pure
    SILENCE_DURATION_MS=5,         # Respuesta inmediata
    VAD_THRESHOLD=0.001            # Ultra ultra sensible
)

# Función de utilidad para obtener configuración
def get_agent_timeout_config() -> AgentTimeoutConfig:
    """Obtiene la configuración global de timeouts del agente"""
    return AGENT_TIMEOUT_CONFIG

# Función para actualizar configuración dinámicamente
def update_timeout_config(**kwargs) -> None:
    """Actualiza la configuración de timeouts dinámicamente"""
    global AGENT_TIMEOUT_CONFIG
    for key, value in kwargs.items():
        if hasattr(AGENT_TIMEOUT_CONFIG, key):
            setattr(AGENT_TIMEOUT_CONFIG, key, value)
        else:
            print(f"Warning: Unknown configuration key '{key}'")

# Configuraciones predefinidas para diferentes escenarios
PRESET_CONFIGS = {
    "no_stimulus": AgentTimeoutConfig(
        INITIAL_GREETING_TIMEOUT=0.5,  # Mínimo absoluto
        SIMPLE_QUERY_TIMEOUT=0.5,      # Mínimo absoluto
        COMPLEX_QUERY_TIMEOUT=1.5,     # Mínimo para complejas
        PURE_QUERY_TIMEOUT=1.0,        # Mínimo para Pure
        SILENCE_DURATION_MS=5,         # Respuesta inmediata
        VAD_THRESHOLD=0.001            # Ultra ultra sensible
    ),
    "instant": AgentTimeoutConfig(
        INITIAL_GREETING_TIMEOUT=1.0,
        SIMPLE_QUERY_TIMEOUT=1.0,
        COMPLEX_QUERY_TIMEOUT=3.0,
        PURE_QUERY_TIMEOUT=2.0,
        SILENCE_DURATION_MS=10,  # Respuesta instantánea
        VAD_THRESHOLD=0.01  # Ultra sensible
    ),
    "ultra_fast": AgentTimeoutConfig(
        INITIAL_GREETING_TIMEOUT=5.0,
        SIMPLE_QUERY_TIMEOUT=3.0,
        COMPLEX_QUERY_TIMEOUT=10.0,
        PURE_QUERY_TIMEOUT=8.0,
        SILENCE_DURATION_MS=100,
        VAD_THRESHOLD=0.1
    ),
    "fast": AgentTimeoutConfig(
        INITIAL_GREETING_TIMEOUT=8.0,
        SIMPLE_QUERY_TIMEOUT=5.0,
        COMPLEX_QUERY_TIMEOUT=15.0,
        PURE_QUERY_TIMEOUT=12.0,
        SILENCE_DURATION_MS=300,
        VAD_THRESHOLD=0.15
    ),
    "balanced": AgentTimeoutConfig(
        INITIAL_GREETING_TIMEOUT=15.0,
        SIMPLE_QUERY_TIMEOUT=10.0,
        COMPLEX_QUERY_TIMEOUT=25.0,
        PURE_QUERY_TIMEOUT=20.0,
        SILENCE_DURATION_MS=500,
        VAD_THRESHOLD=0.2
    ),
    "thorough": AgentTimeoutConfig(
        INITIAL_GREETING_TIMEOUT=30.0,
        SIMPLE_QUERY_TIMEOUT=20.0,
        COMPLEX_QUERY_TIMEOUT=60.0,
        PURE_QUERY_TIMEOUT=45.0,
        SILENCE_DURATION_MS=2000,
        MAX_RESPONSE_TOKENS=4096
    )
}

def apply_preset_config(preset_name: str) -> None:
    """Aplica una configuración predefinida"""
    global AGENT_TIMEOUT_CONFIG
    if preset_name in PRESET_CONFIGS:
        AGENT_TIMEOUT_CONFIG = PRESET_CONFIGS[preset_name]
        print(f"Applied preset configuration: {preset_name}")
    else:
        print(f"Unknown preset: {preset_name}. Available presets: {list(PRESET_CONFIGS.keys())}")

def enable_no_stimulus_mode() -> None:
    """Habilita el modo sin estímulo para respuestas inmediatas"""
    global AGENT_TIMEOUT_CONFIG
    AGENT_TIMEOUT_CONFIG = PRESET_CONFIGS["no_stimulus"]
    print("🚀 Modo sin estímulo activado - Sabius responderá inmediatamente")

def enable_instant_mode() -> None:
    """Habilita el modo instantáneo para respuestas rápidas"""
    global AGENT_TIMEOUT_CONFIG
    AGENT_TIMEOUT_CONFIG = PRESET_CONFIGS["instant"]
    print("⚡ Modo instantáneo activado - Sabius responderá muy rápido")
