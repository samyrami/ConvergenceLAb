"""
ENHANCED AGENT WITH PURE KNOWLEDGE - Agente mejorado con conocimiento de Pure Universidad de la Sabana
Integra toda la información extraída sin alterar la funcionalidad existente
"""

from __future__ import annotations

import logging
import os
import asyncio
import json
from typing import Optional, Dict, Any, List
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

# Importar el cargador de contexto original
try:
    from context_loader import load_and_enhance_context
    CONTEXT_ENHANCEMENT_AVAILABLE = True
except ImportError:
    CONTEXT_ENHANCEMENT_AVAILABLE = False
    logging.warning("Context loader no disponible. El agente funcionará con contexto básico.")

# Importar el gestor de conocimiento de Pure
try:
    from pure_knowledge_manager import PureKnowledgeManager, KnowledgeManagerConfig
    PURE_KNOWLEDGE_AVAILABLE = True
except ImportError:
    PURE_KNOWLEDGE_AVAILABLE = False
    logging.warning("Pure Knowledge Manager no disponible. El agente funcionará sin conocimiento de Pure.")

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

# Configure logging
logger = logging.getLogger("convergence-lab-pure-agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Verify required environment variables
required_env_vars = ['OPENAI_API_KEY', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

class PureKnowledgeIntegration:
    """Integración del conocimiento de Pure con el agente"""
    
    def __init__(self):
        self.knowledge_manager = None
        self.knowledge_available = False
        self.setup_knowledge_manager()
    
    def setup_knowledge_manager(self):
        """Configurar el gestor de conocimiento de Pure"""
        try:
            if not PURE_KNOWLEDGE_AVAILABLE:
                logger.info("🔍 Pure Knowledge Manager no disponible")
                return
            
                    # Buscar archivos de conocimiento (priorizar contexto híbrido)
        data_dir = "scraped_data"
        if not os.path.exists(data_dir):
            logger.info("📂 Directorio scraped_data no encontrado")
            return
        
        # Intentar usar el contexto híbrido primero
        hybrid_path = os.path.join(data_dir, "pure_hybrid_context.json")
        if os.path.exists(hybrid_path):
            kb_path = hybrid_path
            logger.info("🔧 Usando contexto híbrido de Pure")
        else:
            # Fallback a archivos de knowledge base
            kb_files = [f for f in os.listdir(data_dir) if f.startswith('pure_knowledge_base_') and f.endswith('.json')]
            
            if not kb_files:
                logger.info("📊 No se encontraron bases de conocimiento de Pure")
                return
            
            # Usar el archivo más reciente
            latest_file = max(kb_files)
            kb_path = os.path.join(data_dir, latest_file)
            
            config = KnowledgeManagerConfig(knowledge_base_path=kb_path)
            self.knowledge_manager = PureKnowledgeManager(config)
            
            if self.knowledge_manager.load_knowledge_base():
                self.knowledge_available = True
                logger.info(f"✅ Conocimiento de Pure cargado desde: {latest_file}")
            else:
                logger.warning("❌ Error cargando conocimiento de Pure")
                
        except Exception as e:
            logger.error(f"Error configurando conocimiento de Pure: {e}")

    def search_pure_knowledge(self, query: str, query_type: str = "general") -> Dict[str, Any]:
        """Buscar información en la base de conocimiento de Pure"""
        if not self.knowledge_available or not self.knowledge_manager:
            return {"available": False, "message": "Conocimiento de Pure no disponible"}
        
        try:
            # Determinar tipo de búsqueda según la consulta
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['investigador', 'profesor', 'researcher', 'académico']):
                results = self.knowledge_manager.query_knowledge("researcher", query)
            elif any(word in query_lower for word in ['unidad', 'facultad', 'departamento', 'unit', 'faculty']):
                results = self.knowledge_manager.query_knowledge("unit", query)
            elif any(word in query_lower for word in ['publicación', 'artículo', 'publication', 'paper']):
                results = self.knowledge_manager.query_knowledge("publication", query)
            else:
                # Búsqueda general en todas las categorías
                researcher_results = self.knowledge_manager.search_researchers(query)
                unit_results = self.knowledge_manager.search_units(query)
                publication_results = self.knowledge_manager.search_publications(query)
                
                results = {
                    "type": "general",
                    "researchers": researcher_results[:3],
                    "units": unit_results[:2],
                    "publications": publication_results[:3],
                    "total_found": len(researcher_results) + len(unit_results) + len(publication_results)
                }
            
            results["available"] = True
            return results
            
        except Exception as e:
            logger.error(f"Error buscando en conocimiento de Pure: {e}")
            return {"available": False, "error": str(e)}

class EnhancedAgentSession(AgentSession):
    """Sesión del agente mejorada con conocimiento de Pure"""
    
    def __init__(self, chat_ctx: llm.ChatContext, fnc_ctx: llm.FunctionContext):
        super().__init__(chat_ctx, fnc_ctx)
        self.pure_knowledge = PureKnowledgeIntegration()
        
        # Registrar funciones de Pure si están disponibles
        if self.pure_knowledge.knowledge_available:
            self.register_pure_functions()

    def register_pure_functions(self):
        """Registrar funciones de conocimiento de Pure en el contexto"""
        @self.fnc_ctx.ai_callable(
            description="Buscar información sobre investigadores de Pure Universidad de la Sabana"
        )
        async def buscar_investigadores(query: str) -> str:
            """Buscar investigadores en Pure Universidad de la Sabana"""
            results = self.pure_knowledge.search_pure_knowledge(query, "researcher")
            
            if not results.get("available", False):
                return "Lo siento, la información de Pure Universidad de la Sabana no está disponible en este momento."
            
            if results.get("type") == "researchers" and results.get("results"):
                response = "🔍 Investigadores encontrados en Pure Universidad de la Sabana:\n\n"
                for researcher in results["results"][:3]:
                    name = researcher.get("name", "N/A")
                    position = researcher.get("position", "N/A")
                    department = researcher.get("department", "N/A")
                    
                    response += f"👤 **{name}**\n"
                    response += f"   📋 Cargo: {position}\n"
                    response += f"   🏛️ Unidad: {department}\n\n"
                    
                    # Agregar áreas de investigación si están disponibles
                    areas = researcher.get("detailed_info", {}).get("research_areas", [])
                    if areas:
                        response += f"   🔬 Áreas: {', '.join(areas[:3])}\n\n"
                
                return response
            else:
                return f"No se encontraron investigadores con el término '{query}' en Pure Universidad de la Sabana."

        @self.fnc_ctx.ai_callable(
            description="Buscar información sobre unidades de investigación de Pure Universidad de la Sabana"
        )
        async def buscar_unidades(query: str) -> str:
            """Buscar unidades de investigación en Pure Universidad de la Sabana"""
            results = self.pure_knowledge.search_pure_knowledge(query, "unit")
            
            if not results.get("available", False):
                return "Lo siento, la información de Pure Universidad de la Sabana no está disponible en este momento."
            
            if results.get("type") == "units" and results.get("results"):
                response = "🔍 Unidades encontradas en Pure Universidad de la Sabana:\n\n"
                for unit in results["results"][:3]:
                    name = unit.get("name", "N/A")
                    unit_type = unit.get("type", "N/A")
                    description = unit.get("description", "")
                    
                    response += f"🏛️ **{name}**\n"
                    response += f"   📂 Tipo: {unit_type}\n"
                    if description:
                        response += f"   📝 Descripción: {description[:200]}...\n"
                    
                    # Agregar estadísticas si están disponibles
                    stats = unit.get("statistics", {})
                    if stats:
                        response += f"   👥 Investigadores: {stats.get('researchers_count', 0)}\n"
                        response += f"   📚 Publicaciones: {stats.get('total_publications', 0)}\n"
                    
                    response += "\n"
                
                return response
            else:
                return f"No se encontraron unidades con el término '{query}' en Pure Universidad de la Sabana."

        @self.fnc_ctx.ai_callable(
            description="Buscar publicaciones científicas de Pure Universidad de la Sabana"
        )
        async def buscar_publicaciones(query: str, year: Optional[str] = None) -> str:
            """Buscar publicaciones científicas en Pure Universidad de la Sabana"""
            kwargs = {"year": year} if year else {}
            results = self.pure_knowledge.search_pure_knowledge(query, "publication")
            
            if not results.get("available", False):
                return "Lo siento, la información de Pure Universidad de la Sabana no está disponible en este momento."
            
            if results.get("type") == "publications" and results.get("results"):
                response = "🔍 Publicaciones encontradas en Pure Universidad de la Sabana:\n\n"
                for pub in results["results"][:3]:
                    title = pub.get("title", "N/A")
                    authors = pub.get("authors", "N/A")
                    year = pub.get("year", "N/A")
                    pub_type = pub.get("type", "N/A")
                    
                    response += f"📚 **{title}**\n"
                    response += f"   ✍️ Autores: {authors}\n"
                    response += f"   📅 Año: {year}\n"
                    response += f"   📂 Tipo: {pub_type}\n"
                    
                    if pub.get("doi"):
                        response += f"   🔗 DOI: {pub['doi']}\n"
                    
                    response += "\n"
                
                return response
            else:
                return f"No se encontraron publicaciones con el término '{query}' en Pure Universidad de la Sabana."

        @self.fnc_ctx.ai_callable(
            description="Obtener información detallada de un investigador específico de Pure Universidad de la Sabana"
        )
        async def obtener_detalles_investigador(nombre: str) -> str:
            """Obtener información detallada de un investigador específico"""
            if not self.pure_knowledge.knowledge_available:
                return "Lo siento, la información de Pure Universidad de la Sabana no está disponible en este momento."
            
            try:
                researcher = self.pure_knowledge.knowledge_manager.get_researcher_details(nombre)
                
                if not researcher:
                    return f"No se encontró información detallada para el investigador '{nombre}' en Pure Universidad de la Sabana."
                
                response = f"👤 **Información detallada de {researcher.get('name', 'N/A')}**\n\n"
                
                # Información básica
                response += f"📋 **Información básica:**\n"
                response += f"   • Cargo: {researcher.get('position', 'N/A')}\n"
                response += f"   • Unidad: {researcher.get('department', 'N/A')}\n"
                
                detailed_info = researcher.get('detailed_info', {})
                
                # Contacto
                if detailed_info.get('email'):
                    response += f"   • Email: {detailed_info['email']}\n"
                
                if detailed_info.get('orcid'):
                    response += f"   • ORCID: {detailed_info['orcid']}\n"
                
                # Áreas de investigación
                areas = detailed_info.get('research_areas', [])
                if areas:
                    response += f"\n🔬 **Áreas de investigación:**\n"
                    for area in areas[:5]:
                        response += f"   • {area}\n"
                
                # Publicaciones
                pub_count = detailed_info.get('publications_count', 0)
                if pub_count > 0:
                    response += f"\n📚 **Producción científica:**\n"
                    response += f"   • Total de publicaciones: {pub_count}\n"
                    
                    recent_pubs = detailed_info.get('recent_publications', [])
                    if recent_pubs:
                        response += f"   • Publicaciones recientes:\n"
                        for pub in recent_pubs[:3]:
                            response += f"     - {pub.get('title', 'N/A')}\n"
                
                # Biografía
                biography = detailed_info.get('biography', '')
                if biography:
                    response += f"\n📝 **Biografía:**\n{biography[:300]}...\n"
                
                return response
                
            except Exception as e:
                logger.error(f"Error obteniendo detalles del investigador: {e}")
                return f"Error al obtener información detallada del investigador '{nombre}'."

        logger.info("✅ Funciones de Pure Universidad de la Sabana registradas en el agente")

    async def ask_pure_question(self, question: str) -> str:
        """Hacer una pregunta específica sobre Pure Universidad de la Sabana"""
        try:
            # Búsqueda general en la base de conocimiento
            results = self.pure_knowledge.search_pure_knowledge(question)
            
            if not results.get("available", False):
                return "La información de Pure Universidad de la Sabana no está disponible en este momento."
            
            if results.get("type") == "general":
                response = "🔍 **Información encontrada en Pure Universidad de la Sabana:**\n\n"
                
                # Investigadores
                researchers = results.get("researchers", [])
                if researchers:
                    response += "👥 **Investigadores relevantes:**\n"
                    for r in researchers:
                        response += f"   • {r.get('name', 'N/A')} - {r.get('department', 'N/A')}\n"
                    response += "\n"
                
                # Unidades
                units = results.get("units", [])
                if units:
                    response += "🏛️ **Unidades relevantes:**\n"
                    for u in units:
                        response += f"   • {u.get('name', 'N/A')}\n"
                    response += "\n"
                
                # Publicaciones
                publications = results.get("publications", [])
                if publications:
                    response += "📚 **Publicaciones relevantes:**\n"
                    for p in publications:
                        response += f"   • {p.get('title', 'N/A')} ({p.get('year', 'N/A')})\n"
                    response += "\n"
                
                if results.get("total_found", 0) == 0:
                    response += "No se encontraron resultados específicos para tu consulta."
                
                return response
            
            return "Se encontró información, pero no se pudo procesar adecuadamente."
            
        except Exception as e:
            logger.error(f"Error procesando pregunta sobre Pure: {e}")
            return "Error procesando la consulta sobre Pure Universidad de la Sabana."

# El resto del código del agente se mantiene igual que en enhanced_agent.py
# Solo se agrega la integración con Pure sin alterar la funcionalidad existente

async def request_fnc(req: llm.FunctionCallRequest) -> None:
    """Handle function calls with Pure knowledge integration"""
    logger.info(f"Function call request: {req.call_info.function_info.name}")
    
    if req.call_info.function_info.name == "buscar_investigadores":
        query = req.call_info.arguments.get("query", "")
        # Esta función ya está registrada en el contexto
        
    elif req.call_info.function_info.name == "buscar_unidades":
        query = req.call_info.arguments.get("query", "")
        # Esta función ya está registrada en el contexto
        
    elif req.call_info.function_info.name == "buscar_publicaciones":
        query = req.call_info.arguments.get("query", "")
        year = req.call_info.arguments.get("year")
        # Esta función ya está registrada en el contexto

async def entrypoint(ctx: JobContext):
    """Enhanced entrypoint with Pure knowledge integration"""
    logger.info("🚀 Starting Enhanced Agent with Pure Knowledge")
    
    # Load enhanced context (original functionality)
    enhanced_context = ""
    if CONTEXT_ENHANCEMENT_AVAILABLE:
        try:
            enhanced_context = load_and_enhance_context()
            logger.info("✅ Enhanced context loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load enhanced context: {e}")
    
    # Base system message with Pure knowledge integration
    base_system_message = f"""Eres un asistente especializado en investigación de la Universidad de la Sabana, con acceso completo a la base de datos Pure de la universidad.

**CAPACIDADES PRINCIPALES:**

1. **Información General Universitaria:** Puedes responder preguntas generales sobre la Universidad de la Sabana, sus programas, historia, y servicios.

2. **Base de Conocimiento Pure:** Tienes acceso completo a la información de investigación de Pure Universidad de la Sabana, incluyendo:
   - 👥 Investigadores y profesores
   - 🏛️ Unidades y facultades de investigación  
   - 📚 Publicaciones científicas
   - 🔬 Proyectos de investigación
   - 📊 Producción científica

**FUNCIONES DISPONIBLES:**
- `buscar_investigadores(query)`: Buscar investigadores por nombre, área o unidad
- `buscar_unidades(query)`: Buscar unidades de investigación
- `buscar_publicaciones(query, year)`: Buscar publicaciones científicas
- `obtener_detalles_investigador(nombre)`: Información detallada de un investigador

**INSTRUCCIONES:**
- Utiliza las funciones de Pure para responder preguntas específicas sobre investigación
- Proporciona información precisa y detallada
- Si no encuentras información específica en Pure, indícalo claramente
- Mantén un tono académico y profesional
- Siempre cita la fuente de información (Pure Universidad de la Sabana)

{enhanced_context}

Responde de manera útil, precisa y profesional. Utiliza las funciones de Pure cuando sea relevante para la consulta del usuario."""

    # Create function context with Pure integration
    fnc_ctx = llm.FunctionContext()
    
    # Create chat context
    chat_ctx = llm.ChatContext().append(
        role="system",
        text=base_system_message,
    )

    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Create enhanced agent session with Pure knowledge
    session = EnhancedAgentSession(chat_ctx, fnc_ctx)
    
    # Start the agent
    agent = Agent(ctx.room, session)
    
    logger.info("🎯 Enhanced Agent with Pure Knowledge started successfully")
    await agent.start(ctx.room, session)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=None,
        ),
    )
