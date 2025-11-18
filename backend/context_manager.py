"""
Sistema de Gestión de Contexto Optimizado para Sabius
Carga dinámica de contexto según relevancia de la consulta
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("context-manager")


class ContextManager:
    """Gestor inteligente de contexto para el agente"""
    
    def __init__(self, context_dir: str = "scraped_data/context", knowledge_base_dir: str = "knowledge_base"):
        self.context_dir = Path(context_dir)
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.contexts = {}
        self.keywords_map = {}
        self.load_all_contexts()
        self.load_knowledge_base()  # Cargar datos de knowledge_base
        
    def load_all_contexts(self):
        """Carga todos los contextos disponibles y crea índice de keywords"""
        if not self.context_dir.exists():
            logger.warning(f"Context directory not found: {self.context_dir}")
            return
            
        for context_file in self.context_dir.glob("*.json"):
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    context_name = context_file.stem
                    self.contexts[context_name] = data
                    
                    # Crear índice de keywords
                    if 'keywords' in data:
                        for keyword in data['keywords']:
                            if keyword not in self.keywords_map:
                                self.keywords_map[keyword] = []
                            self.keywords_map[keyword].append(context_name)
                    
                logger.info(f"✅ Contexto cargado: {context_name}")
            except Exception as e:
                logger.error(f"Error cargando {context_file}: {e}")
    
    def load_knowledge_base(self):
        """Carga datos de faculty_professors.json y research_publications.json"""
        if not self.knowledge_base_dir.exists():
            logger.warning(f"Knowledge base directory not found: {self.knowledge_base_dir}")
            return
        
        # Cargar faculty_professors.json
        faculty_file = self.knowledge_base_dir / "faculty_professors.json"
        if faculty_file.exists():
            try:
                with open(faculty_file, 'r', encoding='utf-8') as f:
                    faculty_data = json.load(f)
                self.contexts['faculty_professors'] = {
                    'title': 'Profesores y Facultad',
                    'keywords': ['profesor', 'faculty', 'docente', 'académico', 'investigador', 'enfermería', 'enfermeria', 'enfermero', 'enfermera', 'catedra', 'cátedra', 'magister', 'maestría', 'doctorado', 'doctor', 'maestro', 'teacher', 'instructor'],
                    'content': self._format_faculty_data(faculty_data)
                }
                # Indexar keywords de faculty
                for keyword in self.contexts['faculty_professors']['keywords']:
                    if keyword not in self.keywords_map:
                        self.keywords_map[keyword] = []
                    self.keywords_map[keyword].append('faculty_professors')
                logger.info("✅ Datos de faculty_professors cargados")
            except Exception as e:
                logger.error(f"Error cargando faculty_professors.json: {e}")
        
        # Cargar research_publications.json
        research_file = self.knowledge_base_dir / "research_publications.json"
        if research_file.exists():
            try:
                with open(research_file, 'r', encoding='utf-8') as f:
                    research_data = json.load(f)
                self.contexts['research_publications'] = {
                    'title': 'Publicaciones e Investigación',
                    'keywords': ['publicación', 'research', 'investigación', 'artículo', 'estudio', 'investigador', 'revista', 'paper', 'tesis', 'grupo', 'unidad', 'producto', 'producción', 'científico', 'cientifico', 'journal', 'publicado', 'publicada'],
                    'content': self._format_research_data(research_data),
                    '_raw_data': research_data  # Guardar datos originales para búsqueda
                }
                # Indexar keywords de research
                for keyword in self.contexts['research_publications']['keywords']:
                    if keyword not in self.keywords_map:
                        self.keywords_map[keyword] = []
                    self.keywords_map[keyword].append('research_publications')
                logger.info("✅ Datos de research_publications cargados")
            except Exception as e:
                logger.error(f"Error cargando research_publications.json: {e}")
    
    def _format_faculty_data(self, faculty_data: Dict[str, Any]) -> str:
        """Formatea los datos de faculty para incluirlos como contexto con todos los campos disponibles"""
        lines = []
        
        # Extraer metadata si existe
        if isinstance(faculty_data, dict) and 'metadata' in faculty_data:
            metadata = faculty_data.get('metadata', {})
            total = metadata.get('total', 0)
            description = metadata.get('description', 'Profesores de Universidad de La Sabana')
            department = metadata.get('department', 'N/A')
            lines.append(f"📚 {description}")
            lines.append(f"Departamento: {department}")
            lines.append(f"Total de profesores: {total}\n")
            
            # Extraer profesores del array
            professors = faculty_data.get('professors', [])
            if isinstance(professors, list):
                for prof in professors[:30]:  # Mostrar primeros 30
                    if isinstance(prof, dict):
                        nombre = prof.get('nombre', 'Sin nombre')
                        titulo = prof.get('titulo', 'N/A')
                        posicion = prof.get('posicion', prof.get('escalafon_puesto', 'N/A'))
                        categoria_minciencias = prof.get('categoria_minciencias', '')
                        facultad = prof.get('facultad')
                        tipo_dedicacion = prof.get('tipo_dedicacion')
                        pais = prof.get('pais', '')
                        pregrado = prof.get('pregrado', '')
                        
                        lines.append(f"- {nombre}")
                        lines.append(f"  Título: {titulo}")
                        if posicion and posicion != 'N/A':
                            lines.append(f"  Posición: {posicion}")
                        if facultad:
                            lines.append(f"  Facultad: {facultad}")
                        if tipo_dedicacion:
                            lines.append(f"  Dedicación: {tipo_dedicacion}")
                        if categoria_minciencias:
                            lines.append(f"  MinCiencias: {categoria_minciencias}")
                        
                        # Información de productividad académica si existe
                        # horas_investigacion = horas dedicadas a investigación durante el semestre
                        horas_investigacion = prof.get('horas_investigacion', 0)
                        total_productos = prof.get('total_productos', 0)
                        if horas_investigacion > 0 or total_productos > 0:
                            lines.append(f"  📊 Investigación: {horas_investigacion}h (semestre) | {total_productos} productos")
                            
                            # Detallar publicaciones si existen
                            art_intl = prof.get('articulos_internacionales_indexados', 0)
                            art_natl = prof.get('articulos_nacionales_indexados', 0)
                            libros = prof.get('libros_capitulos_investigacion', 0)
                            patentes = prof.get('patentes_disenos_software', 0)
                            if art_intl > 0 or art_natl > 0 or libros > 0 or patentes > 0:
                                details = []
                                if art_intl > 0:
                                    details.append(f"{art_intl} artículos internacionales")
                                if art_natl > 0:
                                    details.append(f"{art_natl} artículos nacionales")
                                if libros > 0:
                                    details.append(f"{libros} libros/capítulos")
                                if patentes > 0:
                                    details.append(f"{patentes} patentes/software")
                        if details:
                                    lines.append(f"    └ {' | '.join(details)}")
                        
                        # Incluir otra_informacion si existe
                        otra_info = prof.get('otra_informacion', '').strip()
                        if otra_info:
                            lines.append(f"  📤 {otra_info}")
                        
                        lines.append("")
        elif isinstance(faculty_data, list):
            lines.append(f"Total de profesores registrados: {len(faculty_data)}\n")
            for prof in faculty_data[:30]:
                if isinstance(prof, dict):
                    nombre = prof.get('nombre', prof.get('name', 'Sin nombre'))
                    titulo = prof.get('titulo', 'N/A')
                    posicion = prof.get('posicion', prof.get('escalafon_puesto', prof.get('categoria_institucional', 'N/A')))
                    lines.append(f"- {nombre}")
                    lines.append(f"  Título: {titulo}")
                    if posicion and posicion != 'N/A':
                        lines.append(f"  Posición: {posicion}")
                    lines.append("")
        
        return "\n".join(lines) if lines else "No hay datos de profesores disponibles."
    
    def _format_research_data(self, research_data: Dict[str, Any]) -> str:
        """Formatea los datos de investigación para incluirlos como contexto con búsqueda mejorada"""
        lines = []
        
        # Extraer metadata
        if isinstance(research_data, dict):
            metadata = research_data.get('metadata', {})
            total_pubs = metadata.get('total', 0)
            units = metadata.get('units', 0)
            groups = metadata.get('groups', 0)
            description = metadata.get('description', 'Productos de investigación')
            
            lines.append(f"📰 {description}")
            lines.append(f"Total: {total_pubs} publicaciones | {units} unidades | {groups} grupos de investigación\n")
            
            # Crear índice de publicaciones para búsqueda rápida
            lines.append("=== PUBLICACIONES POR GRUPO Y UNIDAD ===")
            
            # Extraer publicaciones por unidad
            by_unit = research_data.get('by_unit', {})
            if isinstance(by_unit, dict):
                for unit_name, publications in list(by_unit.items())[:10]:  # Mostrar hasta 10 unidades
                    if isinstance(publications, list):
                        # Agrupar por grupo de investigación
                        groups_dict = {}
                        for pub in publications:
                            if isinstance(pub, dict):
                                grupo = pub.get('grupo', 'Sin grupo')
                                if grupo not in groups_dict:
                                    groups_dict[grupo] = []
                                groups_dict[grupo].append(pub)
                        
                        lines.append(f"\n🏢 UNIDAD: {unit_name}")
                        
                        for grupo_name, grupo_pubs in groups_dict.items():
                            lines.append(f"  📊 Grupo: {grupo_name}")
                            # Mostrar primeras 5 publicaciones del grupo
                            for pub in grupo_pubs[:5]:
                                titulo = pub.get('titulo', 'Sin título')
                                revista = pub.get('revista', 'N/A')
                                lines.append(f"    ✓ {titulo}")
                                lines.append(f"      Revista: {revista}")
        elif isinstance(research_data, list):
            lines.append(f"Total de publicaciones: {len(research_data)}\n")
            for pub in research_data[:30]:
                if isinstance(pub, dict):
                    titulo = pub.get('titulo', pub.get('title', 'Sin título'))
                    revista = pub.get('revista', pub.get('journal', 'N/A'))
                    grupo = pub.get('grupo', 'N/A')
                    lines.append(f"- {titulo}")
                    lines.append(f"  Revista: {revista} | Grupo: {grupo}")
        
        return "\n".join(lines) if lines else "No hay datos de publicaciones disponibles."
    
    def search_publications(self, query: str) -> str:
        """Busca publicaciones por título, tema o grupo de investigación"""
        if 'research_publications' not in self.contexts:
            return "No hay datos de publicaciones disponibles."
        
        research_data = self.contexts['research_publications'].get('_raw_data', {})
        if not research_data:
            return "No se puede buscar en publicaciones."
        
        query_lower = query.lower()
        results = []
        
        by_unit = research_data.get('by_unit', {})
        if isinstance(by_unit, dict):
            for unit_name, publications in by_unit.items():
                if isinstance(publications, list):
                    for pub in publications:
                        if isinstance(pub, dict):
                            titulo = pub.get('titulo', '').lower()
                            grupo = pub.get('grupo', '').lower()
                            revista = pub.get('revista', '').lower()
                            unidad = pub.get('unidad', '').lower()
                            
                            # Buscar en título, grupo, revista
                            if (query_lower in titulo or 
                                query_lower in grupo or 
                                query_lower in revista or
                                query_lower in unidad):
                                results.append(pub)
        
        if not results:
            return f"No se encontraron publicaciones relacionadas con '{query}'."
        
        # Formatear resultados
        lines = [f"🔍 Resultados para '{query}' ({len(results)} encontrados):\n"]
        for pub in results[:10]:  # Mostrar máximo 10
            unidad = pub.get('unidad', 'N/A')
            grupo = pub.get('grupo', 'N/A')
            titulo = pub.get('titulo', 'Sin título')
            revista = pub.get('revista', 'N/A')
            
            lines.append(f"📄 {titulo}")
            lines.append(f"   Unidad: {unidad}")
            lines.append(f"   Grupo: {grupo}")
            lines.append(f"   Revista: {revista}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_relevant_context(self, query: str, max_sections: int = 3) -> str:
        """
        Identifica y retorna solo el contexto relevante para la consulta
        Busca inteligentemente en publicaciones, artículos, grupos, etc.
        
        Args:
            query: Consulta del usuario
            max_sections: Número máximo de secciones a incluir
            
        Returns:
            String con el contexto relevante formateado
        """
        query_lower = query.lower()
        relevant_contexts = []
        scores = {}
        
        # Primero: Buscar si es una consulta sobre publicaciones/artículos
        publication_keywords = ['publicación', 'artículo', 'revista', 'paper', 'estudio', 
                               'investigación', 'grupo', 'grupo de investigación', 'tema']
        is_publication_query = any(kw in query_lower for kw in publication_keywords)
        
        if is_publication_query and 'research_publications' in self.contexts:
            # Si es una consulta sobre publicaciones, buscar en el contenido
            search_result = self.search_publications(query)
            if "No se encontraron" not in search_result:
                return search_result
        
        # Segundo: Scoring por keywords normal
        for keyword, context_names in self.keywords_map.items():
            if keyword in query_lower:
                for context_name in context_names:
                    scores[context_name] = scores.get(context_name, 0) + 1
        
        # Ordenar por relevancia
        sorted_contexts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Construir contexto relevante
        context_parts = []
        for context_name, score in sorted_contexts[:max_sections]:
            if context_name in self.contexts:
                context_data = self.contexts[context_name]
                context_parts.append(self._format_context(context_name, context_data))
        
        # Si no hay contexto específico, incluir el core
        if not context_parts and 'core' in self.contexts:
            context_parts.append(self._format_context('core', self.contexts['core']))
        
        return "\n\n".join(context_parts)
    
    def _format_context(self, name: str, data: Dict[str, Any]) -> str:
        """Formatea un contexto para incluirlo en el prompt"""
        formatted = f"## {data.get('title', name.upper())}\n\n"
        
        if 'content' in data:
            formatted += data['content']
        
        return formatted
    
    def get_core_context(self) -> str:
        """Retorna el contexto core siempre presente"""
        if 'core' in self.contexts:
            return self._format_context('core', self.contexts['core'])
        return ""
    
    def get_context_by_name(self, context_name: str) -> Optional[str]:
        """Obtiene un contexto específico por nombre"""
        if context_name in self.contexts:
            return self._format_context(context_name, self.contexts[context_name])
        return None
    
    def list_available_contexts(self) -> List[str]:
        """Lista todos los contextos disponibles"""
        return list(self.contexts.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas sobre los contextos cargados"""
        total_size = sum(
            len(json.dumps(ctx)) for ctx in self.contexts.values()
        )
        
        return {
            "total_contexts": len(self.contexts),
            "total_keywords": len(self.keywords_map),
            "estimated_total_tokens": total_size // 4,  # Aproximación
            "available_contexts": list(self.contexts.keys())
        }


class DynamicPromptBuilder:
    """Constructor de prompts dinámicos con contexto optimizado"""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        self.base_prompt = self._load_base_prompt()
    
    def _load_base_prompt(self) -> str:
        """Carga el prompt base con reglas ESTRICTAS para bloquear alucinaciones"""
        return """# 🧠 Sabius – Asistente del Convergence Lab

## INSTRUCCIONES OPERACIONALES:

1. Responde ÚNICAMENTE con información del contexto proporcionado
2. NO inventes, supongas ni uses información externa
3. Sé conciso y responde directamente a la pregunta
4. NO menciones que respondes "basado en contexto"
5. Si no tienes información, di claramente: "No encuentro esa información"

## ESTILO DE RESPUESTA:
- Responde de forma natural y directa
- No hagas aclaraciones sobre tus fuentes
- Si es una pregunta sobre un tema disponible, proporciona la información
- Mantén respuestas breves y al punto

## Contacto:
📍 Edificio Ad Portas, Eje 17, Piso 3
📧 convergence.lab@unisabana.edu.co

---

## INFORMACIÓN DISPONIBLE:
"""
    
    def build_prompt(self, query: str = "", include_pure: bool = True) -> str:
        """
        Construye un prompt optimizado con contexto OBLIGATORIO relevante
        NUNCA devuelve un prompt sin contexto específico.
        
        Args:
            query: Consulta del usuario para determinar contexto relevante
            include_pure: Si incluir información de Pure
            
        Returns:
            Prompt completo con contexto obligatorio
        """
        parts = [self.base_prompt]
        
        # Siempre incluir contexto core (OBLIGATORIO)
        core = self.context_manager.get_core_context()
        if core:
            parts.append(core)
        else:
            parts.append("""## Información Base del ConvergenceLab
Ubicación: Edificio Ad Portas, Eje 17, Piso 3
Contacto: convergence.lab@unisabana.edu.co
Universidad: Universidad de La Sabana""")
        
        # Agregar contexto relevante según la consulta (OBLIGATORIO)
        if query:
            relevant = self.context_manager.get_relevant_context(query, max_sections=3)
            if relevant:
                parts.append("\n--- CONTEXTO ESPECÍFICO PARA ESTA PREGUNTA ---\n")
                parts.append(relevant)
            else:
                # Si no hay contexto específico, al menos incluir listado de temas disponibles
                available = self.context_manager.list_available_contexts()
                parts.append(f"\n⚠️ Contexto relevante no encontrado. Temas disponibles: {', '.join(available)}")
        else:
            # Si no hay query, incluir resumen de todos los contextos
            available = self.context_manager.list_available_contexts()
            all_contexts = [self._format_context(ctx_name, self.context_manager.contexts[ctx_name]) 
                           for ctx_name in available if ctx_name in self.context_manager.contexts]
            if all_contexts:
                parts.append("\n--- TODOS LOS CONTEXTOS DISPONIBLES ---\n")
                parts.extend(all_contexts)
        
        prompt = "\n".join(parts)
        
        return prompt
    
    def _format_context(self, name: str, data: Dict[str, Any]) -> str:
        """Formatea un contexto para incluirlo en el prompt"""
        formatted = f"\n### [{name.upper()}]\n{data.get('title', name.upper())}\n\n"
        if 'content' in data:
            formatted += data['content']
        return formatted
    
    def get_prompt_stats(self, prompt: str) -> Dict[str, int]:
        """Retorna estadísticas del prompt generado"""
        return {
            "characters": len(prompt),
            "estimated_tokens": len(prompt) // 4,
            "lines": prompt.count('\n')
        }
