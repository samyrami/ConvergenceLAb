from __future__ import annotations

import logging
import os
import asyncio
import json
from typing import Optional, Dict, List, Any
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
logger = logging.getLogger("convergence-lab-agent-with-pure")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Verify required environment variables
required_env_vars = ['OPENAI_API_KEY', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

class PureDataLoader:
    """Cargador integrado de datos de Pure Universidad de la Sabana"""
    
    def __init__(self):
        self.pure_data = {}
        self.units_index = {}
        self.categories_index = {}
        self.loaded = False
        self.load_pure_data()
    
    def load_pure_data(self):
        """Cargar datos de Pure desde archivos disponibles"""
        try:
            # Intentar cargar contexto híbrido primero
            hybrid_path = "scraped_data/pure_hybrid_context.json"
            if os.path.exists(hybrid_path):
                with open(hybrid_path, 'r', encoding='utf-8') as f:
                    self.pure_data = json.load(f)
                logger.info("✅ Contexto híbrido de Pure cargado")
            else:
                # Buscar archivos de knowledge base
                data_dir = "scraped_data"
                if os.path.exists(data_dir):
                    kb_files = [f for f in os.listdir(data_dir) if f.startswith('pure_knowledge_base_') and f.endswith('.json')]
                    if kb_files:
                        latest_file = max(kb_files)
                        kb_path = os.path.join(data_dir, latest_file)
                        with open(kb_path, 'r', encoding='utf-8') as f:
                            kb_data = json.load(f)
                        
                        # Convertir a formato estándar
                        self.pure_data = {
                            "research_units": kb_data.get('research_units', []),
                            "researchers": kb_data.get('researchers', []),
                            "publications": kb_data.get('scientific_production', [])
                        }
                        logger.info(f"✅ Knowledge base de Pure cargado: {latest_file}")
            
            self.create_indices()
            self.loaded = True
            
        except Exception as e:
            logger.error(f"Error cargando datos de Pure: {e}")
            self.loaded = False
    
    def create_indices(self):
        """Crear índices para búsqueda rápida"""
        try:
            # Índice de unidades
            for unit in self.pure_data.get('research_units', []):
                name = unit.get('name', '').lower()
                self.units_index[name] = unit
                
                # Agregar palabras clave del nombre
                words = name.split()
                for word in words:
                    if len(word) > 3:
                        if word not in self.units_index:
                            self.units_index[word] = []
                        if isinstance(self.units_index[word], list):
                            self.units_index[word].append(unit)
                        else:
                            self.units_index[word] = [self.units_index[word], unit]
            
            # Índice por categorías
            categories = {
                "medicina": [],
                "biomédica": [],
                "ingeniería": [],
                "comunicación": [],
                "economía": [],
                "derecho": [],
                "educación": [],
                "psicología": []
            }
            
            for unit in self.pure_data.get('research_units', []):
                name = unit.get('name', '').lower()
                for category, units_list in categories.items():
                    if category in name:
                        units_list.append(unit)
            
            self.categories_index = categories
            
        except Exception as e:
            logger.error(f"Error creando índices: {e}")
    
    def search_units(self, query: str) -> List[Dict[str, Any]]:
        """Buscar unidades de investigación"""
        if not self.loaded:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda exacta
            if query_lower in self.units_index:
                unit = self.units_index[query_lower]
                if isinstance(unit, dict):
                    results.append(unit)
                elif isinstance(unit, list):
                    results.extend(unit)
            
            # Búsqueda por palabras clave
            words = query_lower.split()
            for word in words:
                if word in self.units_index:
                    matches = self.units_index[word]
                    if isinstance(matches, dict):
                        if matches not in results:
                            results.append(matches)
                    elif isinstance(matches, list):
                        for match in matches:
                            if match not in results:
                                results.append(match)
            
            # Búsqueda parcial
            if not results:
                for unit in self.pure_data.get('research_units', []):
                    name = unit.get('name', '').lower()
                    if query_lower in name:
                        results.append(unit)
            
            return results[:10]
            
        except Exception as e:
            logger.error(f"Error buscando unidades: {e}")
            return []
    
    def get_units_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Obtener unidades por categoría"""
        if not self.loaded:
            return []
        
        category_lower = category.lower()
        return self.categories_index.get(category_lower, [])
    
    def get_minciencias_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de categorías MinCiencias"""
        if not self.loaded:
            return {}
        
        stats = {"A": 0, "B": 0, "sin_categoria": 0, "total": 0}
        
        for unit in self.pure_data.get('research_units', []):
            category = unit.get('category', '')
            if 'Categoría A' in category:
                stats["A"] += 1
            elif 'Categoría B' in category:
                stats["B"] += 1
            else:
                stats["sin_categoria"] += 1
            stats["total"] += 1
        
        return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen general de Pure"""
        if not self.loaded:
            return {"available": False}
        
        return {
            "available": True,
            "total_units": len(self.pure_data.get('research_units', [])),
            "total_researchers": len(self.pure_data.get('researchers', [])),
            "total_publications": len(self.pure_data.get('publications', [])),
            "minciencias_stats": self.get_minciencias_stats()
        }

class GovLabAssistantWithPure(Agent):
    def __init__(self) -> None:
        # Cargar datos de Pure
        self.pure_loader = PureDataLoader()
        
        # Crear el prompt del sistema que incluye información de Pure
        pure_context = self.generate_pure_context()
        
        super().__init__(instructions=f""" 
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

{pure_context}

---

## 🎯 MI PERSONALIDAD Y ESTILO

Soy **amigable, cercano y motivador**, pero siempre mantengo un enfoque **académico y profesional**. Mi objetivo es:

- **Facilitar la exploración** de ideas y oportunidades de colaboración
- **Conectar disciplinas** y mostrar cómo diferentes saberes pueden converger
- **Impulsar la acción** hacia la materialización de proyectos con impacto
- **Democratizar la innovación** haciendo accesibles tecnologías complejas

## 🗣️ Mi comunicación es:
- **Clara y accesible** (evito jerga innecesaria)
- **Inspiradora y orientada a la acción**
- **Contextualizada** a la Universidad de La Sabana
- **Colaborativa** (invito al diálogo y la co-creación)

## 🚀 DIRECTRICES CLAVE

1. **Siempre inicio** las conversaciones invitando a explorar las posibilidades del Convergence Lab
2. **Conecto** las consultas con oportunidades de innovación, investigación o colaboración interdisciplinar
3. **Muestro ejemplos concretos** de cómo el Lab puede potenciar proyectos
4. **Invito a la acción**: visitar el Lab, participar en actividades, explorar colaboraciones
5. **Uso las funciones de Pure** para proporcionar información específica sobre investigación universitaria cuando sea relevante

---

**¡Estoy aquí para ayudarte a materializar esas ideas que pueden transformar el mundo desde la Universidad de La Sabana!** 🌟
""")
    
    def generate_pure_context(self) -> str:
        """Generar contexto de Pure para el prompt del sistema"""
        if not self.pure_loader.loaded:
            return """## 🔬 PURE UNIVERSIDAD DE LA SABANA
*Base de conocimiento de investigación no disponible actualmente*"""
        
        summary = self.pure_loader.get_summary()
        minciencias = summary.get('minciencias_stats', {})
        
        # Obtener ejemplos de unidades por categoría
        medicina_units = self.pure_loader.get_units_by_category("medicina")[:3]
        ingenieria_units = self.pure_loader.get_units_by_category("ingeniería")[:3]
        comunicacion_units = self.pure_loader.get_units_by_category("comunicación")[:3]
        
        context = f"""## 🔬 PURE UNIVERSIDAD DE LA SABANA - BASE DE CONOCIMIENTO DE INVESTIGACIÓN

Tienes acceso completo a la base de datos Pure de Universidad de la Sabana con información actualizada sobre investigación institucional.

### 📊 ESTADÍSTICAS GENERALES:
- **{summary['total_units']} unidades de investigación** mapeadas
- **{summary['total_researchers']} investigadores** registrados  
- **{summary['total_publications']} publicaciones** científicas
- **{minciencias['total']} grupos** clasificados

### 🏆 CLASIFICACIÓN MINCIENCIAS:
- **Categoría A:** {minciencias['A']} grupos de excelencia
- **Categoría B:** {minciencias['B']} grupos consolidados  
- **Sin categoría:** {minciencias['sin_categoria']} grupos

### 🔬 PRINCIPALES ÁREAS DE INVESTIGACIÓN:

**MEDICINA Y CIENCIAS DE LA SALUD:**"""
        
        for unit in medicina_units:
            context += f"\n- {unit.get('name', 'N/A')}"
        
        context += f"\n\n**INGENIERÍA Y TECNOLOGÍA:**"
        for unit in ingenieria_units:
            context += f"\n- {unit.get('name', 'N/A')}"
        
        context += f"\n\n**COMUNICACIÓN Y MEDIOS:**"
        for unit in comunicacion_units:
            context += f"\n- {unit.get('name', 'N/A')}"
        
        context += f"""

### 🔍 FUNCIONES DISPONIBLES:
- `buscar_unidades_investigacion(query)`: Buscar grupos por nombre/área
- `obtener_estadisticas_minciencias()`: Clasificación completa
- `buscar_por_area(area)`: Unidades por disciplina específica
- `obtener_resumen_pure()`: Panorama general institucional

**INSTRUCCIONES PARA USO DE PURE:**
1. Utiliza las funciones cuando los usuarios pregunten sobre investigación, grupos, facultades o áreas específicas
2. Conecta la información de Pure con oportunidades del Convergence Lab
3. Sugiere colaboraciones interdisciplinarias basadas en los grupos de investigación
4. Cita siempre "Pure Universidad de la Sabana" como fuente de información"""
        
        return context

class PureAssistantSession(AgentSession):
    """Sesión del agente con funcionalidades de Pure integradas"""
    
    def __init__(self, chat_ctx: llm.ChatContext, fnc_ctx: llm.FunctionContext, pure_loader: PureDataLoader):
        super().__init__(chat_ctx, fnc_ctx)
        self.pure_loader = pure_loader
        
        # Registrar funciones de Pure si están disponibles
        if self.pure_loader.loaded:
            self.register_pure_functions()

    def register_pure_functions(self):
        """Registrar funciones de Pure en el contexto del agente"""
        
        @self.fnc_ctx.ai_callable(
            description="Buscar unidades de investigación en Pure Universidad de la Sabana por nombre, área o especialidad"
        )
        async def buscar_unidades_investigacion(query: str) -> str:
            """Buscar unidades de investigación en Pure Universidad de la Sabana"""
            try:
                results = self.pure_loader.search_units(query)
                
                if not results:
                    return f"No se encontraron unidades de investigación para '{query}' en Pure Universidad de la Sabana."
                
                response = f"🔍 **Unidades de investigación encontradas para '{query}':**\n\n"
                
                for i, unit in enumerate(results[:5], 1):
                    name = unit.get('name', 'N/A')
                    category = unit.get('category', 'Sin categoría')
                    unit_type = unit.get('type', 'Unidad organizativa')
                    
                    response += f"**{i}. {name}**\n"
                    response += f"   📂 Tipo: {unit_type}\n"
                    if 'Categoría' in category:
                        response += f"   🏆 {category}\n"
                    
                    response += "\n"
                
                if len(results) > 5:
                    response += f"... y {len(results) - 5} unidades adicionales encontradas.\n\n"
                
                response += "💡 **¿Te interesa colaborar con alguna de estas unidades?** El Convergence Lab puede facilitar conexiones interdisciplinarias para proyectos innovadores."
                
                return response
                
            except Exception as e:
                logger.error(f"Error buscando unidades: {e}")
                return f"Error al buscar unidades de investigación para '{query}'."

        @self.fnc_ctx.ai_callable(
            description="Obtener estadísticas completas de categorías MinCiencias de Universidad de la Sabana"
        )
        async def obtener_estadisticas_minciencias() -> str:
            """Obtener estadísticas de categorías MinCiencias"""
            try:
                stats = self.pure_loader.get_minciencias_stats()
                
                response = "🏆 **Clasificación MinCiencias - Universidad de la Sabana:**\n\n"
                response += f"📊 **CATEGORÍA A (Excelencia):** {stats['A']} grupos\n"
                response += f"📊 **CATEGORÍA B (Consolidados):** {stats['B']} grupos\n"
                response += f"📊 **SIN CATEGORÍA:** {stats['sin_categoria']} grupos\n"
                response += f"📊 **TOTAL GRUPOS:** {stats['total']} unidades de investigación\n\n"
                
                # Mostrar algunos grupos de Categoría A si existen
                category_a_units = []
                for unit in self.pure_loader.pure_data.get('research_units', []):
                    if 'Categoría A' in unit.get('category', ''):
                        category_a_units.append(unit['name'])
                
                if category_a_units:
                    response += "🌟 **Grupos de Categoría A destacados:**\n"
                    for unit_name in category_a_units[:3]:
                        response += f"   • {unit_name}\n"
                    response += "\n"
                
                response += "💡 **El Convergence Lab puede ayudarte a conectar con estos grupos de investigación para proyectos colaborativos de alto impacto.**"
                
                return response
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas MinCiencias: {e}")
                return "Error al obtener estadísticas de categorías MinCiencias."

        @self.fnc_ctx.ai_callable(
            description="Buscar unidades de investigación por área específica (medicina, ingeniería, comunicación, etc.)"
        )
        async def buscar_por_area(area: str) -> str:
            """Buscar unidades por área específica"""
            try:
                units = self.pure_loader.get_units_by_category(area.lower())
                
                if not units:
                    # Intentar búsqueda general
                    units = self.pure_loader.search_units(area)
                
                if not units:
                    return f"No se encontraron unidades en el área de '{area}' en Pure Universidad de la Sabana."
                
                response = f"🔬 **Unidades de investigación en {area.title()}:**\n\n"
                
                for i, unit in enumerate(units[:8], 1):
                    name = unit.get('name', 'N/A')
                    category = unit.get('category', 'Sin categoría')
                    
                    response += f"**{i}. {name}**\n"
                    if 'Categoría' in category:
                        response += f"   🏆 {category}\n"
                    response += "\n"
                
                if len(units) > 8:
                    response += f"... y {len(units) - 8} unidades adicionales en esta área.\n\n"
                
                response += f"🚀 **¿Tienes una idea para {area}?** En el Convergence Lab podemos ayudarte a desarrollar proyectos interdisciplinarios conectando con estos grupos de investigación."
                
                return response
                
            except Exception as e:
                logger.error(f"Error buscando por área: {e}")
                return f"Error al buscar unidades en el área de '{area}'."

        @self.fnc_ctx.ai_callable(
            description="Obtener resumen general de Pure Universidad de la Sabana con todas las estadísticas"
        )
        async def obtener_resumen_pure() -> str:
            """Obtener resumen general de Pure Universidad de la Sabana"""
            try:
                summary = self.pure_loader.get_summary()
                
                if not summary.get('available', False):
                    return "La información de Pure Universidad de la Sabana no está disponible en este momento."
                
                minciencias = summary.get('minciencias_stats', {})
                
                response = "📋 **Resumen General - Pure Universidad de la Sabana:**\n\n"
                
                response += f"🏛️ **Total de unidades de investigación:** {summary['total_units']}\n"
                response += f"👥 **Investigadores registrados:** {summary['total_researchers']}\n"
                response += f"📚 **Publicaciones científicas:** {summary['total_publications']}\n\n"
                
                response += f"🏆 **Distribución MinCiencias:**\n"
                response += f"   • Categoría A: {minciencias.get('A', 0)} grupos de excelencia\n"
                response += f"   • Categoría B: {minciencias.get('B', 0)} grupos consolidados\n"
                response += f"   • Sin categoría: {minciencias.get('sin_categoria', 0)} grupos\n\n"
                
                # Destacar principales áreas
                main_areas = ["medicina", "ingeniería", "comunicación", "economía", "derecho"]
                response += f"🔬 **Principales áreas de investigación disponibles:**\n"
                for area in main_areas:
                    area_units = self.pure_loader.get_units_by_category(area)
                    if area_units:
                        response += f"   • {area.title()}: {len(area_units)} unidades\n"
                
                response += f"\n✅ **Estado:** Operacional y actualizado\n"
                response += f"💡 **El Convergence Lab está conectado con toda esta red de investigación para potenciar tus proyectos interdisciplinarios.**"
                
                return response
                
            except Exception as e:
                logger.error(f"Error obteniendo resumen: {e}")
                return "Error al obtener resumen general de Pure Universidad de la Sabana."

        logger.info("✅ Funciones de Pure integradas en el agente")

async def entrypoint(ctx: JobContext):
    """Punto de entrada del agente con Pure integrado"""
    logger.info("🚀 Starting Convergence Lab Agent with Pure Integration")
    
    # Create function context
    fnc_ctx = llm.FunctionContext()
    
    # Create the agent
    agent = GovLabAssistantWithPure()
    
    # Create chat context
    chat_ctx = llm.ChatContext().append(
        role="system",
        text=agent.instructions,
    )

    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Create specialized session with Pure integration
    session = PureAssistantSession(chat_ctx, fnc_ctx, agent.pure_loader)
    
    # Start the agent
    actual_agent = Agent(ctx.room, session)
    
    logger.info("🎯 Convergence Lab Agent with Pure started successfully")
    if agent.pure_loader.loaded:
        logger.info(f"📊 {agent.pure_loader.get_summary()['total_units']} unidades de investigación disponibles")
    
    await actual_agent.start(ctx.room, session)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=None,
        ),
    )
