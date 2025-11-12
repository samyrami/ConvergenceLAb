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

# Importar configuración de timeouts
from agent_timeout_config import get_agent_timeout_config

# Importar sistema de gestión de contexto optimizado
from context_manager import ContextManager, DynamicPromptBuilder

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
                logger.info("OK - Contexto hibrido de Pure cargado")
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
                        logger.info(f"OK - Knowledge base de Pure cargado: {latest_file}")
            
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
                "biomedica": [],
                "ingenieria": [],
                "comunicacion": [],
                "economia": [],
                "derecho": [],
                "educacion": [],
                "psicologia": []
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
            if 'Categoria A' in category:
                stats["A"] += 1
            elif 'Categoria B' in category:
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

class GovLabAssistant(Agent):
    def __init__(self) -> None:
        # Cargar datos de Pure
        self.pure_loader = PureDataLoader()
        
        # Inicializar sistema de gestión de contexto optimizado
        self.context_manager = ContextManager()
        self.prompt_builder = DynamicPromptBuilder(self.context_manager)
        
        # Log de estadísticas de contexto
        ctx_stats = self.context_manager.get_statistics()
        logger.info(f"Contextos cargados: {ctx_stats['total_contexts']}")
        logger.info(f"Keywords indexados: {ctx_stats['total_keywords']}")
        logger.info(f"Tokens estimados (total): ~{ctx_stats['estimated_total_tokens']}")
        
        # Crear el prompt base SIN query (se hará dinámicamente por cada mensaje)
        base_prompt = self.prompt_builder.build_prompt(query="")
        
        # Log estadísticas del prompt final
        prompt_stats = self.prompt_builder.get_prompt_stats(base_prompt)
        logger.info(f"Prompt base: ~{prompt_stats['estimated_tokens']} tokens")
        logger.info(f"⚠️ MODO CONTEXTO FORZADO ACTIVADO: El agente SOLO responderá con información del contexto.")
        
        super().__init__(instructions=base_prompt)

    async def on_user_turn_completed(
        self,
        chat_ctx: llm.ChatContext,
        new_message: llm.ChatMessage
    ) -> None:
        # NUEVO: Reconstruir prompt dinámicamente con la query del usuario
        try:
            user_query = new_message.content
            if user_query:
                dynamic_prompt = self.prompt_builder.build_prompt(query=user_query)
                await self.update_instructions(dynamic_prompt)
                logger.info(f"📋 Prompt actualizado dinámicamente para: '{user_query[:50]}...'")
        except Exception as e:
            logger.warning(f"Error actualizando prompt dinámicamente: {e}")
        
        # Keep the most recent 15 items in the chat context.
        chat_ctx = chat_ctx.copy()
        if len(chat_ctx.items) > 15:
            chat_ctx.items = chat_ctx.items[-15:]
        await self.update_chat_ctx(chat_ctx)

async def create_realtime_model_with_retry(max_retries: int = 3) -> openai.realtime.RealtimeModel:
    """Create a realtime model with connection retry logic."""
    timeout_config = get_agent_timeout_config()
    
    for attempt in range(max_retries):
        try:
            model_config = timeout_config.get_openai_model_config()
            model = openai.realtime.RealtimeModel(
                voice="ash",
                model="gpt-4o-realtime-preview",
                temperature=0.3  # ULTRA BAJO para NO alucinar (era 0.6)
            )
            logger.info(f"Realtime model created successfully on attempt {attempt + 1} [temperature=0.3]")
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
            
            # Create the agent first
            agent = GovLabAssistant()
            
            # Create standard AgentSession with enhanced agent
            vad = silero.VAD.load()
            
            session = AgentSession(
                llm=model,
                vad=vad,
            )
            
            # Start the session
            await session.start(
                room=ctx.room,
                agent=agent,
            )
            
            # Generate initial greeting with timeout handling
            try:
                timeout_config = get_agent_timeout_config()
                await asyncio.wait_for(
                    session.generate_reply(
                        instructions="Saluda brevemente al usuario e introduce el ConvergenceLab"
                    ),
                    timeout=timeout_config.get_timeout_for_query_type("greeting")
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
