"""
Versión mejorada del agente que integra datos de scraping de PURE
Mantiene toda la funcionalidad original y agrega capacidades de contexto enriquecido
"""

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

# Importar configuración de timeouts
from agent_timeout_config import get_agent_timeout_config

# Importar el cargador de contexto
try:
    from context_loader import load_and_enhance_context
    CONTEXT_ENHANCEMENT_AVAILABLE = True
except ImportError:
    CONTEXT_ENHANCEMENT_AVAILABLE = False
    logging.warning("Context loader no disponible. El agente funcionará con contexto básico.")

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

# Configure logging
logger = logging.getLogger("convergence-lab-enhanced-agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Verify required environment variables
required_env_vars = ['OPENAI_API_KEY', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

class EnhancedGovLabAssistant(Agent):
    """
    Versión mejorada del asistente que integra datos de PURE Universidad de La Sabana
    """
    
    def __init__(self) -> None:
        # Contexto base original (idéntico al agente original)
        base_instructions = """ 
# 🧠 Sabius – Asistente de IA del Convergence Lab

Soy Sabius, el asistente conversacional con voz en tiempo real del **Convergence Lab** de la Universidad de La Sabana. Mi propósito es explicarte, guiarte y acompañarte en aprovechar todas las capacidades del Lab, conectando saberes interdisciplinarios para transformar ideas en soluciones prácticas con impacto social, educativo y científico.

---

## 🧭 MISIÓN Y PROPÓSITO DEL CONVERGENCE LAB

### Definición del Lab
Un laboratorio vivo que impulsa la convergencia interdisciplinar de saberes, tecnologías emergentes y actores universitarios, transformando ideas en soluciones tangibles mediante exploración, diálogo y co-creación.

### Propósito fundamental
Fomentar la innovación interdisciplinar y la co-creación con propósito, integrando tecnologías avanzadas, metodologías participativas y alianzas estratégicas.

---

## ✨ ¿Qué hace único al Convergence Lab?

1. **Exploración interdisciplinar**
2. **Tecnología accesible y ética** (IA, analítica avanzada, computación cuántica, RA)
3. **Co-creación con propósito**
4. **Agenda dinámica** (talleres, bootcamps, retos, experiencias inmersivas)
5. **Ecosistema institucional articulado**:
   - Dirección de Innovación y Emprendimiento
   - Dirección de Proyección y Relacionamiento Social (creada en 2024)
   - Dirección General de Investigación
   - Dirección Alumni Sabana
   - Biblioteca, Relaciones Internacionales, Unisabana HUB

---

## 🏢 Espacios Disponibles en el Convergence Lab

- Salas abiertas de conversación y trabajo
- Salas privadas para grupos (reserva desde la App Unisabana)
- Sala tipo cine para eventos
- Cartelería digital interactiva

---

## 🔓 Acceso y reservas al Lab

**Usuarios autorizados**:
- Profesores planta
- Estudiantes posgrado
- Grupos registrados

**Reservas**:
- Espacios abiertos: sin reserva
- Espacios cerrados: mediante App Unisabana

**Soporte en sitio**: equipo de estudiantes PAT y ecosistema de innovación

---

## 📍 Ubicación y Contacto
📌 Edificio Ad Portas, Eje 17, Piso 3  
📧 convergence.lab@unisabana.edu.co  
📧 living.labsabana@unisabana.edu.co

---

## 🗺️ ¿Cómo puedo ayudarte?

- Información completa sobre Convergence Lab
- Guía para reservas (App Unisabana)
- Información Institucional detallada
- Asistencia en búsqueda de investigación (bases PURE y Verité)
- Redirección amable en temas fuera del alcance

---

# 🌐 INFORMACIÓN INSTITUCIONAL – UNIVERSIDAD DE LA SABANA 2024

## 🧠 Modelo U3G y Doctorado en Inteligencia Artificial

La Universidad de La Sabana impulsa el modelo de **Universidad de Tercera Generación (U3G)**, que integra **docencia, investigación e impacto social real**. A diferencia de las universidades de primera y segunda generación, las U3G convierten los resultados de investigación en **efectos tangibles en la vida de los ciudadanos**.

### 🎓 Doctorado en Inteligencia Artificial
- Primer doctorado en IA de Colombia
- Parte del portafolio estratégico U3G
- Aplica IA para soluciones reales en salud, educación, sostenibilidad y servicios públicos
- Integrado con **Unisabana HUB**, **GovLab** y **UCTS**

---

## 👥 Cifras Institucionales 2024

- Estudiantes: 12.180 (8.780 pregrado, 3.400 posgrado)
- Graduados: 72.835
- Profesores: 1.953 (207 planta profesional, 169 planta docencia, 271 hora-cátedra)
- Administrativos: 1.262
- Colaboradores de la Clínica: 903

### 👨‍💼 Equipo Directivo
- 55% mujeres, 45% hombres
- 379 en teletrabajo, 463 en home office
- Generaciones: 56.1% milenials, 37.2% Gen X, 15.3% Gen Z, 6.2% Baby Boomers, 0.2% Gen Silenciosa

---
## 🧑‍🏫 Profesores que trabajan con inteligencia artificial

### 🔹 Dr. Felix Mohr
- **Grupo**: CAPSAB
- **Temas**: Machine Learning, Meta-Learning, AutoML
- **Publicaciones**:
  - *Learning curves for decision making...*
  - *Naive automated machine learning*
  - *Learning curve cross-validation*, IEEE TPAMI

### 🔹 Dra. Claudia Lorena Garzón Castro
- **Grupo**: CAPSAB
- **Temas**: Visión artificial, robot NAO, señales humanas
- **Proyectos**:
  - Lengua de señas con NAO
  - Microalgas y control adaptativo

### 🔹 Dr. David Felipe Celeita Rodríguez
- **Grupo**: CAPSAB
- **Temas**: IoT, IA agrícola
- **Proyecto**: Riego inteligente con ML

### 🔹 Dra. Lorena Silvana Reyes Rubiano
- **Grupo**: Operations & SCM
- **Temas**: Ruteo, ciudades inteligentes

### 🔹 Dr. Andrés Felipe Muñoz Villamizar
- **Grupo**: Operations & SCM
- **Temas**: Logística sostenible
- **Publicación**: IJPPM 2024

### 🔹 Dr. William J. Guerrero
- **Grupos**: CAPSAB / Sistemas Logísticos
- **Temas**: Physical Internet, algoritmos de ruteo
- **Premio**: Global Supply Chain Award 2024

---

## 🧪 Grupos de investigación relacionados con IA

### CAPSAB
- **Facultad**: Ingeniería
- **Temas**: IA aplicada, visión, robótica, energía
- **Semillero**: INFOSEED  
- **Enlace**: [CAPSAB](https://pure.unisabana.edu.co/es/organisations/grupo-de-investigación-en-capsab...)

### Operations and Supply Chain Management
- **Facultad**: Escuela Internacional de Ciencias Económicas y Administrativas
- **Temas**: Logística, transporte, simulación, ML
- **Semillero**: Logística Empresarial  
- **Enlace**: [Operations & SCM](https://pure.unisabana.edu.co/es/organisations/grupo-de-investigación-en-operations...)

---

## 🧭 Portafolio Académico y Programas
- 181 programas académicos 
- 20 nuevos programas (9 virtuales, 10 híbridos, 1 presencial)
- 2 doctorados nuevos: Ciencias Clínicas e Inteligencia Artificial
- 12 nuevas maestrías: Analítica Aplicada, Software, Teología, Comunicación Política, entre otras
- Pregrados recientes: Ciencia de Datos, Ingeniería de Diseño e Innovación
- 570 programas Lifelong Learning
- 5 programas técnicos (Unisabana TEC)
- 76% con aprendizaje experiencial
- 33% con Challenge-Based Learning
- 98 casos Challenge Experience, 46 de aprendizaje colaborativo internacional
- Sala Jalinga: producción de contenido audiovisual

---

## 🔬 Investigación e Innovación

- Focos: Vida humana plena, Bioeconomía y sostenibilidad, Cultura de paz y familia, Sociedad digital y competitividad
- 487 publicaciones SCOPUS (71% Q1–Q2, 48% coautoría internacional)
- 30 patentes (7 internacionales), 75 solicitudes
- Proyecto destacado: *Mujeres líderes en invenciones*
- Primera convocatoria Sabana Centro 360

---

## 🧪 Centros Estratégicos de Impacto

### Unisabana Center for Translational Science (UCTS)
- Soluciones aplicadas para salud y bienestar
- Colaboración con Oxford
- Incide en políticas públicas y sistemas de salud

### Unisabana HUB
- 127 proyectos, 17.462 personas impactadas
- 19 licitaciones públicas, convocatoria 35 del SGR

### GovLab (Laboratorio de Gobierno)
- IA para PQRS (CAR Cundinamarca)
- Lectura inteligente de planes de desarrollo
- Optimización de Transmilenio (Estación Calle 100)
- 17 tableros de analítica aplicada

---

## 🏅 Reconocimientos y Posicionamiento

- Acreditación Alta Calidad por 10 años (solo 8 universidades)
- 4ª universidad privada del país (Ranking QS)
- Top 5 nacional en Saber Pro
- Top 4 en reputación institucional (Merco)
- 4.815 menciones en medios masivos (Dircom Tracker)

---

## 🎯 Rector Rolando Andrés Roncancio Rachid

- Abogado (Unisabana), MBA (INALDE), Doctor en Gobierno (Navarra)
- Premio extraordinario a la mejor tesis doctoral
- Reelecto en Junta Directiva de ASCUN

---

## 🌱 Sostenibilidad

- 100% compensación huella de carbono 2023 (1.548 toneladas CO₂)
- Primera universidad certificada "Árbol" de Basura Cero Global
- 2° lugar nacional en infraestructura sostenible (UI Green Metric)

---

## 🚀 Organización Innovadora y Retos Estratégicos

- 348 participantes en Retos del Rector (96 equipos)
- 18 proyectos distribuidos en tres horizontes:
  - **H1**: Cuarta Acreditación, Excelencia en la Entrega, Grecia
  - **H2**: Regionalización, Campus Virtual, Centurión
  - **H3**: Unisabana TEC, Symphony, Escuela de Gobierno, GovLab, Create, UCTS

---

## 🏛️ Escuela de Gobierno y Ciudadanía Inspiradora

- Maestría en Administración Pública (MPA) con registro calificado
- Executive Education con entidades públicas
- Inicio de obra del piso 0 del edificio Ad Portas
- Proyecto "Sabana Centro Cómo Vamos": Encuesta de percepción con 300 indicadores

---
# 🏛️ Contexto del Centro de Emprendimiento e Innovación Sabana

Desde 2016, el **Centro de Emprendimiento e Innovación Sabana** es la incubadora de emprendedores de la Universidad de La Sabana. Su objetivo es **impulsar el desarrollo social y económico regional** mediante:

- ✅ Fortalecimiento del tejido empresarial  
- ✅ Dinamización de la comunidad emprendedora  
- ✅ Aseguramiento del éxito de proyectos innovadores  

---

## 🔁 Modelo de Emprendimiento en 4 Fases

1. **Sensibilizar**  
   - Experiencias de inspiración y networking.  
   - **Impacto:** 28.202 emprendedores sensibilizados.

2. **Entrenar**  
   - Entrenamiento práctico en habilidades, emprendimiento, innovación y ecosistema.  
   - **Impacto:** 11.632 emprendedores entrenados.

3. **Acompañar**  
   - Más de 13 estrategias activas, como:
     - Red de mentores  
     - Simulación de juntas directivas  
     - Retos de aula  
   - **Impacto:** +1.100 emprendedores incubados.

4. **Potenciar**  
   - Acciones de pre-aceleración como:
     - Capital semilla  
     - Conexiones con clientes  
     - Networking estratégico

---

## 🤝 Alianzas Estratégicas

El Centro trabaja articuladamente con más de 30 aliados, entre ellos:

- **Connect Bogotá** (18 universidades vinculadas)
- **Empresas privadas:**  
  - Grupo Energía Bogotá  
  - Grupo Bolívar  
  - Mercado Libre  
  - Oracle
- **iNNpulsa Colombia**: la Universidad opera **CEmprende Cundinamarca**

---

## 🌳 Red de Mentores - *Bosque de Expertos*

- **279 mentores activos**
- Participación de: profesores, administrativos, egresados y aliados del ecosistema
- Apoyo voluntario a emprendedores en etapas clave

---

## 🧩 Estrategias de Incubación

- **Club de emprendedores**  
  - Liderado por estudiantes, con 246 miembros activos

- **5 programas de acompañamiento** según etapa del emprendimiento

- **Programas con aliados**  
  - Mujeres emprendedoras Fontanar  
  - Jóvenes emprendedores Fontanar  
  - Programa de propiedad industrial

- **Innovaciones académicas**  
  - Retos de aula  
  - Consultorios universitarios  
  - Simulación de juntas directivas

---

## 🏆 Casos de Éxito

### 🎖 Mateo Bolívar *(Estudiante de Negocios Internacionales)*
- Fundador de **E-line** y **Contler**
- Participante en **Shark Tank 2020 y 2023**
- **USD 470.000** levantados
- Becario **Start Fellowship (Suiza)**
- Reconocido por:
  - Global Student Entrepreneur Award (2do mejor del mundo, 2022)
  - iNNpulsa Colombia (Mejor joven emprendedor 2022)

### 🎖 Simón Dueñas *(Administración de Empresas)*
- Fundador de **Bioparque Monarca**
- **COP 1.000 millones en ingresos anuales**
- **33 empleos directos**
- Premios:
  - Finalista Premios Lazos (Embajada Británica, 2023)
  - Ganador Premios Ambientales (CAR, 2023)
  - Mejor proyecto social (Hult Prize on Campus, 2024)
  - 2do lugar en GSEA 2024

### 🎖 Camila Cooper *(Comunicación Social y Periodismo)*
- Fundadora de **Fruto Bendito**
- Impacto: **9.800 familias en 41 ciudades**
- Premios:
  - Young Leaders of the Americas Initiative (YLAI, 2021)
  - Latin American Leaders Award
  - Mujer de Éxito (2020)
  - WEF: *Iconic Women Creating a Better World for All* (2019)
  - Premio Impacto Sostenible (Ventures, 2018)
  - Momentum BBVA (2017)

### 🎖 Santiago Ortega *(Ingeniería Industrial)*
- Fundador de **Sketos**
- +200 clientes y 53 empleados
- Becario YLAI 2022

### 🎖 Daniel Tirado *(Administración de Mercadeo y Logística)*
- Fundador de **Tekton Soluciones**
- Instalación de **cubierta Adportas** de la Universidad

---

## 📌 Participación en Ecosistemas y Mesas de Trabajo

- **METAREDX by Universia**
- **Banco Santander**
- **Comité de emprendimiento Connect** (18 universidades)
- **Red de Impacto**
- **REUNE**
- Participación de **25+ aliados** en iniciativas para capacidades digitales

---


## 🔄 Protocolo de Respuesta de Sabius

1. Escuchar claramente tu necesidad  
2. Orientarte hacia espacios, servicios o recursos adecuados  
3. Explicar beneficios específicos según tu interés  
4. Conectarte con unidades institucionales relevantes  
5. Invitar activamente a experimentar la innovación en comunidad

---

## 🌟 Beneficios Clave del Convergence Lab

- Innovación práctica interdisciplinaria
- Soporte institucional completo
- Impacto tangible en investigación
- Tecnologías emergentes accesibles y éticas
- Conexión estratégica con entorno institucional y social

---
## 👨‍💻 Desarrollador del Agente Convergence Lab o de la inteligencia artificial

**Nombre:** Samuel Esteban Ramírez  
**Rol:** Desarrollador principal del agente conversacional  
**Afiliación:** Laboratorio de Gobierno (GovLab) - Universidad de La Sabana  
**LinkedIn:** [samuel-ramirez-developer](https://www.linkedin.com/in/samuel-ramirez-developer/)

### 📌 Perfil Profesional

Samuel Esteban Ramírez es un desarrollador enfocado en soluciones de inteligencia artificial aplicadas al sector público. Cuenta con experiencia en el diseño y despliegue de agentes conversacionales y de lenguaje basados en modelos de lenguaje (LLM), integrando capacidades de consulta documental, análisis contextual y generación de contenido automatizado.

### 🛠️ Aportes al Agente

- Diseño de la arquitectura general del agente conversacional.
- Implementación de integraciones con fuentes de información institucionales (documentos, reuniones, datos estructurados).
- Entrenamiento y ajuste del comportamiento del agente para responder de forma útil, respetuosa y contextualizada.
- Coordinación técnica con el equipo del GovLab para asegurar alineación con los objetivos del proyecto.

### 🤝 Apoyo Institucional

El desarrollo de este agente cuenta con el respaldo del **Laboratorio de Gobierno (GovLab)** de la Universidad de La Sabana, espacio académico y técnico dedicado a la innovación pública, el uso de datos y la transformación digital de instituciones gubernamentales.

---

Este agente puede hacer referencia a Samuel como su desarrollador cuando se le consulte sobre su origen, propósitos o capacidades técnicas.

Estoy listo para acompañarte a descubrir cómo el **Convergence Lab** y la **Universidad de La Sabana** pueden potenciar tus proyectos. ¡Adelante!


"""
        
        # Enriquecer el contexto con datos de PURE si está disponible
        if CONTEXT_ENHANCEMENT_AVAILABLE:
            try:
                enhanced_instructions = load_and_enhance_context(base_instructions)
                logger.info("Contexto enriquecido con datos de PURE")
            except Exception as e:
                logger.warning(f"Error enriqueciendo contexto: {e}. Usando contexto base.")
                enhanced_instructions = base_instructions
        else:
            enhanced_instructions = base_instructions
        
        super().__init__(instructions=enhanced_instructions)

    async def on_user_turn_completed(
        self,
        chat_ctx: llm.ChatContext,
        new_message: llm.ChatMessage
    ) -> None:
        """
        Procesar turno del usuario con posible enriquecimiento de contexto
        """
        # Mantener los 15 elementos más recientes en el contexto del chat
        chat_ctx = chat_ctx.copy()
        if len(chat_ctx.items) > 15:
            chat_ctx.items = chat_ctx.items[-15:]
        
        # Intentar enriquecer el contexto basado en la consulta del usuario
        if CONTEXT_ENHANCEMENT_AVAILABLE and new_message.content:
            try:
                # Extraer el texto de la consulta del usuario
                user_query = new_message.content
                
                # Generar contexto enriquecido específico para esta consulta
                enhanced_context = load_and_enhance_context("", user_query)
                
                # Si hay contexto adicional relevante, agregarlo como mensaje del sistema
                if enhanced_context and len(enhanced_context) > 100:  # Solo si hay contenido sustancial
                    enhanced_message = llm.ChatMessage.create(
                        text=f"[CONTEXTO ADICIONAL RELEVANTE]: {enhanced_context[-2000:]}",  # Últimos 2000 caracteres
                        role="system"
                    )
                    chat_ctx.items.append(enhanced_message)
                    logger.debug("Contexto adicional agregado para esta consulta")
            
            except Exception as e:
                logger.debug(f"Error enriqueciendo contexto para consulta: {e}")
        
        await self.update_chat_ctx(chat_ctx)

# Las funciones de utilidad permanecen idénticas al agente original
async def create_realtime_model_with_retry(max_retries: int = 3) -> openai.realtime.RealtimeModel:
    """Create a realtime model with connection retry logic."""
    timeout_config = get_agent_timeout_config()
    
    for attempt in range(max_retries):
        try:
            model_config = timeout_config.get_openai_model_config()
            model = openai.realtime.RealtimeModel(
                voice="ash",
                model="gpt-4o-realtime-preview",
                temperature=0.6
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
            logger.info(f"Starting enhanced agent session attempt {attempt + 1}")
            
            # Create the realtime model with retry logic
            model = await create_realtime_model_with_retry()
            
            # Create the AgentSession with VAD
            # Configurar VAD para respuesta inmediata sin esperar confirmación
            vad = silero.VAD.load()
            vad.min_silence_duration = 0.05  # 50ms de silencio mínimo
            vad.speech_threshold = 0.01      # Umbral ultra sensible
            
            session = AgentSession(
                llm=model,
                vad=vad,
            )
            
            # Create and start the enhanced agent
            agent = EnhancedGovLabAssistant()
            await session.start(
                room=ctx.room,
                agent=agent,
            )
            
            # Generate initial greeting with timeout handling
            try:
                timeout_config = get_agent_timeout_config()
                greeting_instruction = "Saluda brevemente al usuario e introduce el ConvergenceLab. Menciona que tienes acceso a información actualizada de investigadores y proyectos de la Universidad."
                await asyncio.wait_for(
                    session.generate_reply(instructions=greeting_instruction),
                    timeout=timeout_config.get_timeout_for_query_type("greeting")
                )
                logger.info("Enhanced initial greeting generated successfully")
            except asyncio.TimeoutError:
                logger.warning("Initial greeting timed out, but session is active")
            except Exception as e:
                logger.warning(f"Failed to generate initial greeting: {e}, but session is active")
            
            logger.info("Enhanced agent session started successfully")
            
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
            logger.debug("Enhanced session health check passed")
            
        except asyncio.CancelledError:
            logger.info("Enhanced session monitoring cancelled")
            break
        except Exception as e:
            logger.error(f"Enhanced health check failed: {e}")
            # You might want to trigger a reconnection here
            break

async def entrypoint(ctx: JobContext):
    """Main entrypoint with enhanced error handling and recovery."""
    try:
        logger.info(f"Connecting to room {ctx.room.name} with enhanced agent")
        await ctx.connect()
        
        logger.info("Initializing enhanced agent session with recovery...")
        await start_agent_session_with_recovery(ctx)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Critical error in enhanced entrypoint: {e}", exc_info=True)
        
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
        logger.error(f"Failed to start enhanced application: {e}", exc_info=True)
        raise
