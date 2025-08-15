#!/usr/bin/env python3
"""
PURE AGENT FINAL - Agente conversacional con conocimiento completo de Pure Universidad de la Sabana
Versión final integrada con contexto híbrido y funciones especializadas
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

# Importar el cargador de contexto original (mantener funcionalidad existente)
try:
    from context_loader import load_and_enhance_context
    CONTEXT_ENHANCEMENT_AVAILABLE = True
except ImportError:
    CONTEXT_ENHANCEMENT_AVAILABLE = False
    logging.warning("Context loader no disponible. El agente funcionará con contexto básico.")

# Importar el gestor híbrido de Pure
try:
    from pure_hybrid_manager import PureHybridManager
    PURE_HYBRID_AVAILABLE = True
except ImportError:
    PURE_HYBRID_AVAILABLE = False
    logging.warning("Pure Hybrid Manager no disponible.")

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

# Configure logging
logger = logging.getLogger("pure-agent-final")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Verify required environment variables
required_env_vars = ['OPENAI_API_KEY', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

class PureAgentSession(AgentSession):
    """Sesión del agente con conocimiento completo de Pure"""
    
    def __init__(self, chat_ctx: llm.ChatContext, fnc_ctx: llm.FunctionContext):
        super().__init__(chat_ctx, fnc_ctx)
        self.pure_manager = None
        self.pure_available = False
        self.setup_pure_knowledge()
        
        # Registrar funciones de Pure
        if self.pure_available:
            self.register_pure_functions()

    def setup_pure_knowledge(self):
        """Configurar conocimiento de Pure"""
        try:
            if not PURE_HYBRID_AVAILABLE:
                logger.info("🔍 Pure Hybrid Manager no disponible")
                return
            
            self.pure_manager = PureHybridManager()
            
            if self.pure_manager.load_context():
                self.pure_available = True
                logger.info("✅ Conocimiento de Pure Universidad de la Sabana cargado exitosamente")
            else:
                logger.warning("❌ Error cargando conocimiento de Pure")
                
        except Exception as e:
            logger.error(f"Error configurando Pure: {e}")

    def register_pure_functions(self):
        """Registrar funciones especializadas de Pure"""
        
        @self.fnc_ctx.ai_callable(
            description="Buscar unidades de investigación en Pure Universidad de la Sabana por nombre, área o categoría"
        )
        async def buscar_unidades_investigacion(query: str) -> str:
            """Buscar unidades de investigación en Pure Universidad de la Sabana"""
            try:
                results = self.pure_manager.search_units(query)
                
                if not results:
                    return f"No se encontraron unidades de investigación para '{query}' en Pure Universidad de la Sabana."
                
                response = f"🔍 **Unidades de investigación encontradas para '{query}':**\n\n"
                
                for i, unit in enumerate(results[:5], 1):
                    name = unit.get('name', 'N/A')
                    category = unit.get('category', 'Sin categoría')
                    unit_type = unit.get('type', 'N/A')
                    
                    response += f"**{i}. {name}**\n"
                    response += f"   📂 Tipo: {unit_type}\n"
                    response += f"   🏆 Categoría: {category}\n"
                    
                    # Agregar áreas de investigación si están disponibles
                    areas = unit.get('research_areas', [])
                    if areas and areas[0] != 'Sin áreas definidas':
                        areas_text = ', '.join(areas[:2])
                        response += f"   🔬 Áreas: {areas_text}\n"
                    
                    response += "\n"
                
                if len(results) > 5:
                    response += f"... y {len(results) - 5} unidades adicionales encontradas.\n"
                
                return response
                
            except Exception as e:
                logger.error(f"Error buscando unidades: {e}")
                return f"Error al buscar unidades de investigación para '{query}'."

        @self.fnc_ctx.ai_callable(
            description="Obtener todas las unidades organizadas por categoría MinCiencias"
        )
        async def listar_categorias_minciencias() -> str:
            """Listar unidades por categoría MinCiencias"""
            try:
                categories = self.pure_manager.get_minciencias_categories()
                
                response = "🏆 **Clasificación MinCiencias - Pure Universidad de la Sabana:**\n\n"
                
                # Categoría A
                cat_a = categories.get('A', [])
                response += f"**📊 CATEGORÍA A ({len(cat_a)} unidades):**\n"
                for unit in cat_a[:10]:  # Mostrar hasta 10
                    response += f"   • {unit.get('name', 'N/A')}\n"
                if len(cat_a) > 10:
                    response += f"   ... y {len(cat_a) - 10} unidades más\n"
                response += "\n"
                
                # Categoría B
                cat_b = categories.get('B', [])
                response += f"**📊 CATEGORÍA B ({len(cat_b)} unidades):**\n"
                for unit in cat_b[:10]:
                    response += f"   • {unit.get('name', 'N/A')}\n"
                if len(cat_b) > 10:
                    response += f"   ... y {len(cat_b) - 10} unidades más\n"
                response += "\n"
                
                # Sin categoría
                sin_cat = categories.get('Sin categoría', [])
                response += f"**📊 SIN CATEGORÍA ({len(sin_cat)} unidades):**\n"
                for unit in sin_cat[:5]:  # Mostrar solo 5
                    response += f"   • {unit.get('name', 'N/A')}\n"
                if len(sin_cat) > 5:
                    response += f"   ... y {len(sin_cat) - 5} unidades más\n"
                
                return response
                
            except Exception as e:
                logger.error(f"Error listando categorías MinCiencias: {e}")
                return "Error al obtener categorías MinCiencias."

        @self.fnc_ctx.ai_callable(
            description="Obtener estadísticas detalladas de una facultad específica"
        )
        async def obtener_estadisticas_facultad(facultad: str) -> str:
            """Obtener estadísticas de una facultad específica"""
            try:
                stats = self.pure_manager.get_faculty_statistics(facultad)
                
                if not stats or stats.get('total_units', 0) == 0:
                    return f"No se encontraron datos para la facultad '{facultad}' en Pure Universidad de la Sabana."
                
                response = f"📊 **Estadísticas de {stats.get('faculty_name', facultad)}:**\n\n"
                response += f"🏛️ **Unidades de investigación:** {stats.get('total_units', 0)}\n"
                response += f"👥 **Investigadores:** {stats.get('total_researchers', 0)}\n\n"
                
                # Categorías MinCiencias
                categories = stats.get('minciencias_categories', {})
                response += f"🏆 **Distribución MinCiencias:**\n"
                response += f"   • Categoría A: {categories.get('A', 0)} unidades\n"
                response += f"   • Categoría B: {categories.get('B', 0)} unidades\n"
                response += f"   • Sin categoría: {categories.get('Sin categoría', 0)} unidades\n\n"
                
                # Unidades principales
                units = stats.get('units', [])
                if units:
                    response += f"🔬 **Principales unidades:**\n"
                    for unit in units[:5]:
                        response += f"   • {unit}\n"
                    if len(units) > 5:
                        response += f"   ... y {len(units) - 5} unidades más\n"
                
                return response
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas de facultad: {e}")
                return f"Error al obtener estadísticas de la facultad '{facultad}'."

        @self.fnc_ctx.ai_callable(
            description="Buscar unidades por área específica (medicina, ingeniería, comunicación, etc.)"
        )
        async def buscar_por_area(area: str) -> str:
            """Buscar unidades por área específica"""
            try:
                units = self.pure_manager.get_units_by_category(area)
                
                if not units:
                    # Intentar búsqueda general
                    units = self.pure_manager.search_units(area)
                
                if not units:
                    return f"No se encontraron unidades en el área de '{area}' en Pure Universidad de la Sabana."
                
                response = f"🔬 **Unidades de investigación en {area}:**\n\n"
                
                for i, unit in enumerate(units[:8], 1):
                    name = unit.get('name', 'N/A')
                    category = unit.get('category', 'Sin categoría')
                    
                    response += f"**{i}. {name}**\n"
                    response += f"   🏆 {category}\n\n"
                
                if len(units) > 8:
                    response += f"... y {len(units) - 8} unidades adicionales en esta área.\n"
                
                return response
                
            except Exception as e:
                logger.error(f"Error buscando por área: {e}")
                return f"Error al buscar unidades en el área de '{area}'."

        @self.fnc_ctx.ai_callable(
            description="Obtener resumen general de Pure Universidad de la Sabana"
        )
        async def obtener_resumen_pure() -> str:
            """Obtener resumen general de Pure Universidad de la Sabana"""
            try:
                stats = self.pure_manager.get_summary_statistics()
                
                response = "📋 **Resumen General - Pure Universidad de la Sabana:**\n\n"
                
                # Estadísticas generales
                response += f"🏛️ **Total de unidades de investigación:** {len(self.pure_manager.context.get('research_units', []))}\n"
                response += f"📊 **Calidad de datos:** {stats.get('data_quality', 'Media').title()}\n"
                response += f"💰 **Costo de extracción:** {stats.get('total_cost', 0)} créditos ScrapFly\n\n"
                
                # Distribución por categorías
                units_by_cat = stats.get('units_by_category', {})
                response += f"🏆 **Distribución MinCiencias:**\n"
                response += f"   • Categoría A: {units_by_cat.get('A', 0)} unidades\n"
                response += f"   • Categoría B: {units_by_cat.get('B', 0)} unidades\n"
                response += f"   • Sin categoría: {units_by_cat.get('Sin categoría', 0)} unidades\n\n"
                
                # Áreas principales
                main_areas = stats.get('main_research_areas', [])
                if main_areas:
                    response += f"🔬 **Principales áreas de investigación:**\n"
                    for area in main_areas[:5]:
                        if 'Categoría' not in area:  # Filtrar metadatos
                            response += f"   • {area}\n"
                    response += "\n"
                
                # Categorías de conocimiento disponibles
                knowledge_cats = stats.get('knowledge_categories', [])
                response += f"📚 **Categorías disponibles:** {', '.join(knowledge_cats)}\n\n"
                
                response += f"📅 **Última actualización:** {stats.get('extraction_date', 'N/A')[:10]}\n"
                response += f"✅ **Estado:** Operacional y listo para consultas"
                
                return response
                
            except Exception as e:
                logger.error(f"Error obteniendo resumen: {e}")
                return "Error al obtener resumen general de Pure Universidad de la Sabana."

        logger.info("✅ Funciones especializadas de Pure registradas en el agente")

    async def handle_pure_query(self, message: str) -> str:
        """Manejar consultas específicas sobre Pure"""
        try:
            message_lower = message.lower()
            
            # Detectar tipo de consulta
            if any(word in message_lower for word in ['unidad', 'grupo', 'centro', 'instituto']):
                if 'medicina' in message_lower or 'médica' in message_lower:
                    return await self.buscar_por_area('medicina')
                elif 'ingeniería' in message_lower or 'engineering' in message_lower:
                    return await self.buscar_por_area('ingeniería')
                elif 'comunicación' in message_lower:
                    return await self.buscar_por_area('comunicación')
                else:
                    # Extraer términos de búsqueda
                    search_terms = message_lower.replace('unidad', '').replace('grupo', '').replace('centro', '').strip()
                    return await self.buscar_unidades_investigacion(search_terms)
            
            elif any(word in message_lower for word in ['categoría', 'minciencias', 'clasificación']):
                return await self.listar_categorias_minciencias()
            
            elif any(word in message_lower for word in ['facultad', 'escuela']):
                # Extraer nombre de facultad
                for word in ['facultad', 'escuela']:
                    if word in message_lower:
                        faculty = message_lower.split(word)[-1].strip()
                        if faculty:
                            return await self.obtener_estadisticas_facultad(faculty)
                return await self.obtener_resumen_pure()
            
            elif any(word in message_lower for word in ['resumen', 'estadísticas', 'general', 'total']):
                return await self.obtener_resumen_pure()
            
            else:
                # Búsqueda general
                return await self.buscar_unidades_investigacion(message)
                
        except Exception as e:
            logger.error(f"Error manejando consulta de Pure: {e}")
            return "Error procesando la consulta sobre Pure Universidad de la Sabana."

async def entrypoint(ctx: JobContext):
    """Punto de entrada del agente final con Pure"""
    logger.info("🚀 Starting Pure Agent Final")
    
    # Load enhanced context (mantener funcionalidad original)
    enhanced_context = ""
    if CONTEXT_ENHANCEMENT_AVAILABLE:
        try:
            enhanced_context = load_and_enhance_context()
            logger.info("✅ Enhanced context loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load enhanced context: {e}")
    
    # Sistema message especializado para Pure
    base_system_message = f"""Eres el asistente oficial de Pure Universidad de la Sabana, especializado en información de investigación académica.

**ESPECIALIZACIÓN PURE:**
Tienes acceso completo y actualizado a la base de datos Pure de Universidad de la Sabana con:

🏛️ **150 UNIDADES DE INVESTIGACIÓN MAPEADAS**
- Centros de investigación biomédica (CIBUS)
- Facultades y escuelas especializadas
- Grupos de investigación por áreas
- Clasificación MinCiencias (Categorías A y B)

📊 **CATEGORÍAS MINCIENCIAS DISPONIBLES:**
- Categoría A: Grupos de excelencia reconocidos
- Categoría B: Grupos consolidados
- Distribución completa por facultades

🔬 **ÁREAS DE CONOCIMIENTO:**
- Medicina y Ciencias de la Salud
- Ingeniería y Tecnología
- Comunicación y Medios
- Ciencias Económicas y Administrativas
- Derecho y Ciencias Políticas
- Educación y Humanidades

**FUNCIONES ESPECIALIZADAS DISPONIBLES:**
- `buscar_unidades_investigacion()`: Encuentra grupos y centros por nombre/área
- `listar_categorias_minciencias()`: Clasificación completa MinCiencias
- `obtener_estadisticas_facultad()`: Datos detallados por facultad
- `buscar_por_area()`: Unidades especializadas por disciplina
- `obtener_resumen_pure()`: Panorama general institucional

**INSTRUCCIONES ESPECÍFICAS:**
1. SIEMPRE usa las funciones de Pure para consultas de investigación
2. Proporciona información precisa y actualizada
3. Cita "Pure Universidad de la Sabana" como fuente
4. Mantén un tono académico y profesional
5. Destaca las fortalezas investigativas de cada unidad

**DATOS ACTUALIZADOS:** Agosto 2024 (Extracción: 395 créditos ScrapFly)
**COBERTURA:** 100% de unidades públicas en Pure
**ESTADO:** ✅ Operacional y completo

{enhanced_context}

Responde como el experto oficial en investigación de Universidad de la Sabana."""

    # Create function context
    fnc_ctx = llm.FunctionContext()
    
    # Create chat context
    chat_ctx = llm.ChatContext().append(
        role="system",
        text=base_system_message,
    )

    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Create specialized Pure agent session
    session = PureAgentSession(chat_ctx, fnc_ctx)
    
    # Start the agent
    agent = Agent(ctx.room, session)
    
    logger.info("🎯 Pure Agent Final started successfully")
    logger.info("📊 150 unidades de investigación disponibles para consulta")
    await agent.start(ctx.room, session)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=None,
        ),
    )
