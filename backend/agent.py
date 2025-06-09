from __future__ import annotations

import logging
import os
import asyncio
from typing import Optional
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AgentSession,
    Agent,
    llm,
    RoomInputOptions,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents._exceptions import APIConnectionError
from livekit.plugins import openai, silero

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

# Configure logging
logger = logging.getLogger("convergence-lab-agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Verify required environment variables
required_env_vars = ['OPENAI_API_KEY', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

class GovLabAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=""" 
# 🧠 Prompt del sistema — César, Asistente de IA del Convergence Lab

**Eres César**, la asistente de IA conversacional con voz en tiempo real del Convergence Lab de la Universidad de La Sabana.  
Tu propósito es explicar y guiar a estudiantes, docentes, investigadores y aliados sobre las capacidades del Convergence Lab como espacio de innovación interdisciplinar, co-creación y articulación universitaria para generar impacto tangible.

---

## 🧭 MISIÓN Y PROPÓSITO

### Definición del Convergence Lab
Un laboratorio vivo que impulsa la convergencia entre saberes, tecnologías emergentes y actores del ecosistema universitario, para transformar ideas en soluciones reales con impacto social, educativo y científico. Es un entorno de exploración, diálogo y co-creación interdisciplinar, donde la innovación se vive, se construye y se comparte.

### Propósito fundamental
Fomentar la innovación interdisciplinar y la co-creación con propósito, integrando tecnologías avanzadas, metodologías participativas y alianzas estratégicas para convertir la investigación en transformación.

---

## ✨ ¿Qué hace único al Convergence Lab?

1. **Exploración interdisciplinar**: articulamos saberes y disciplinas para resolver retos complejos en colaboración.  
2. **Tecnología accesible y ética**: promovemos el uso creativo de IA, analítica avanzada, computación cuántica, realidad aumentada y más.  
3. **Co-creación con propósito**: conectamos con comunidades, sectores públicos y empresas para generar soluciones útiles y replicables.  
4. **Agenda viva**: talleres, bootcamps, retos y experiencias inmersivas para potenciar la investigación y el emprendimiento.  
5. **Ecosistema articulado**:
   - Dirección de Innovación y Emprendimiento (Centro de Emprendimiento, Oficina de Transferencia, Ambientes de Innovación)
   - Dirección de Proyección Social
   - Dirección General de Investigación
   - Dirección de Alumni Sabana
   - Apoyo itinerante: Biblioteca, Relaciones Internacionales, Unisabana Hub

---

## 🏢 Espacios Disponibles

- Salas de conversación abierta  
- Zonas de trabajo individual abiertas  
- Salas privadas para trabajo individual o grupal  
- Salas de juntas (incluye una sala tipo cine)  
- Cartelería digital para divulgación de resultados, convocatorias, prototipos y más

---

## 🔓 ¿Quiénes pueden acceder y cómo?

**Pueden acceder**:
- Profesores de planta  
- Estudiantes de posgrado  
- Grupos de investigación registrados  

**Acceso a espacios**:
- **Espacios abiertos**: sin necesidad de reserva  
- **Salas privadas o de juntas**: reserva desde la App Unisabana (como en el Living Lab)  

**Soporte en sitio**: equipo de estudiantes PAT y miembros del Ecosistema de Innovación disponibles en el primer piso.

---

## 📍 Ubicación y contacto

📌 Edificio Ad Portas, Eje 17, Piso 3  
📧 convergence.lab@unisabana.edu.co  
📧 living.labsabana@unisabana.edu.co

---

## 🗺️ FUNCIONALIDADES DEL ASISTENTE

César debe ser capaz de:

- **Informar sobre el Convergence Lab**: definición, espacios, servicios, agenda, usuarios.  
- **Guiar en la reserva de espacios** (instrucciones App Unisabana).  
- **Brindar información institucional**:
  - Historia, cifras, acreditaciones
  - Proyecto Educativo Institucional (misión, visión, propósito formativo)
- **Asistir en la búsqueda de investigación**:
  - Consulta de temas vía base de datos PURE  
  - Sugerencia de grupos, docentes, publicaciones  
- **Detectar temas fuera de alcance** y redirigir la conversación con cortesía

---

## 🔄 Protocolo de respuesta de César

1. Identificar la necesidad específica del usuario  
2. Guiar hacia espacios, servicios o recursos del Lab  
3. Explicar beneficios tangibles o articulaciones posibles  
4. Referenciar unidades del ecosistema que pueden apoyar  
5. Invitar a interactuar y experimentar la innovación  

---

## 🏅 Beneficios clave a comunicar

- Espacio para experimentar e innovar en comunidad  
- Apoyo institucional en todas las fases del proceso creativo  
- Inspiración para transformar la investigación en soluciones reales  
- Tecnología emergente al servicio de la academia  
- Integración de capacidades internas y externas de la universidad


""")

    async def on_user_turn_completed(
        self,
        chat_ctx: llm.ChatContext,
        new_message: llm.ChatMessage
    ) -> None:
        # Keep the most recent 15 items in the chat context.
        chat_ctx = chat_ctx.copy()
        if len(chat_ctx.items) > 15:
            chat_ctx.items = chat_ctx.items[-15:]
        await self.update_chat_ctx(chat_ctx)

async def create_realtime_model_with_retry(max_retries: int = 3) -> openai.realtime.RealtimeModel:
    """Create a realtime model with connection retry logic."""
    for attempt in range(max_retries):
        try:
            model = openai.realtime.RealtimeModel(
                voice="ash",
                model="gpt-4o-realtime-preview",
                temperature=0.6,
            )
            logger.info(f"Realtime model created successfully on attempt {attempt + 1}")
            return model
        except Exception as e:
            logger.warning(f"Failed to create realtime model on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Failed to create realtime model after all retries")
                raise

async def start_agent_session_with_recovery(ctx: JobContext, max_retries: int = 3) -> None:
    """Start agent session with automatic recovery on connection failures."""
    
    for attempt in range(max_retries):
        session: Optional[AgentSession] = None
        try:
            logger.info(f"Starting agent session attempt {attempt + 1}")
            
            # Create the realtime model with retry logic
            model = await create_realtime_model_with_retry()
            
            # Create the AgentSession with VAD
            session = AgentSession(
                llm=model,
                vad=silero.VAD.load(),
            )
            
            # Create and start the agent
            agent = GovLabAssistant()
            await session.start(
                room=ctx.room,
                agent=agent,
            )
            
            # Generate initial greeting with timeout handling
            try:
                await asyncio.wait_for(
                    session.generate_reply(
                        instructions="Saluda brevemente al usuario e introduce el ConvergenceLab"
                    ),
                    timeout=10.0  # 10 second timeout
                )
                logger.info("Initial greeting generated successfully")
            except asyncio.TimeoutError:
                logger.warning("Initial greeting timed out, but session is active")
            except Exception as e:
                logger.warning(f"Failed to generate initial greeting: {e}, but session is active")
            
            logger.info("Agent session started successfully")
            
            # Keep the session alive and monitor for connection issues
            await monitor_session_health(session, ctx)
            
        except APIConnectionError as e:
            logger.error(f"API Connection error on attempt {attempt + 1}: {e}")
            if session:
                try:
                    await session.stop()
                except Exception:
                    pass  # Ignore cleanup errors
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Failed to maintain stable connection after all retries")
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
            if session:
                try:
                    await session.stop()
                except Exception:
                    pass
            raise

async def monitor_session_health(session: AgentSession, ctx: JobContext) -> None:
    """Monitor session health and attempt recovery if needed."""
    health_check_interval = 30  # Check every 30 seconds
    
    while True:
        try:
            await asyncio.sleep(health_check_interval)
            
            # Check if room is still connected
            if ctx.room.connection_state == rtc.ConnectionState.CONN_DISCONNECTED:
                logger.warning("Room disconnected, attempting to reconnect...")
                await ctx.connect()
                
            # Add more health checks as needed
            logger.debug("Session health check passed")
            
        except asyncio.CancelledError:
            logger.info("Session monitoring cancelled")
            break
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # You might want to trigger a reconnection here
            break

async def entrypoint(ctx: JobContext):
    """Main entrypoint with enhanced error handling and recovery."""
    try:
        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect()
        
        logger.info("Initializing agent session with recovery...")
        await start_agent_session_with_recovery(ctx)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Critical error in entrypoint: {e}", exc_info=True)
        
        # Attempt graceful fallback - you could implement a basic text-only mode here
        logger.info("Attempting graceful fallback...")
        # Add fallback logic if needed
        
        raise

if __name__ == "__main__":
    try:
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
            )
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
