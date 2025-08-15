"""
Cargador de contexto adicional para integrar datos de scraping con el agente
Diseñado para no interferir con el agente principal
"""

import json
import os
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContextData:
    """Estructura para datos de contexto"""
    source: str
    content_type: str
    title: str
    summary: str
    full_data: Dict
    relevance_score: float = 0.0

class PureContextLoader:
    """
    Cargador de contexto que integra datos de scraping de PURE
    con el contexto existente del agente
    """
    
    def __init__(self, context_dir: str = "scraped_data"):
        """Inicializar el cargador de contexto"""
        self.context_dir = context_dir
        self.loaded_contexts: Dict[str, Dict] = {}
        self.processed_data: List[ContextData] = []
        
        logger.info(f"ContextLoader inicializado con directorio: {context_dir}")
    
    def load_pure_context(self, filename: str = "pure_context.json") -> Optional[Dict]:
        """Cargar contexto desde archivo de scraping de PURE"""
        filepath = os.path.join(self.context_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Archivo de contexto no encontrado: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.loaded_contexts['pure'] = data
            logger.info(f"Contexto PURE cargado exitosamente desde {filepath}")
            
            # Procesar datos para crear resúmenes útiles
            self._process_pure_data(data)
            
            return data
        
        except Exception as e:
            logger.error(f"Error cargando contexto PURE: {e}")
            return None
    
    def _process_pure_data(self, data: Dict) -> None:
        """Procesar datos de PURE para crear resúmenes y contexto útil"""
        logger.info("Procesando datos de PURE para contexto del agente...")
        
        # Procesar investigadores
        if 'researchers' in data:
            for researcher in data['researchers']:
                context_item = self._create_researcher_context(researcher)
                if context_item:
                    self.processed_data.append(context_item)
        
        # Procesar publicaciones
        if 'publications' in data:
            for publication in data['publications']:
                context_item = self._create_publication_context(publication)
                if context_item:
                    self.processed_data.append(context_item)
        
        # Procesar proyectos
        if 'projects' in data:
            for project in data['projects']:
                context_item = self._create_project_context(project)
                if context_item:
                    self.processed_data.append(context_item)
        
        # Procesar organizaciones
        if 'organizations' in data:
            for organization in data['organizations']:
                context_item = self._create_organization_context(organization)
                if context_item:
                    self.processed_data.append(context_item)
        
        logger.info(f"Procesados {len(self.processed_data)} elementos de contexto")
    
    def _create_researcher_context(self, researcher_data: Dict) -> Optional[ContextData]:
        """Crear contexto para un investigador"""
        try:
            data = researcher_data.get('data', {})
            title = researcher_data.get('title', 'Investigador sin nombre')
            
            # Crear resumen del investigador
            summary_parts = []
            
            if 'name' in data:
                summary_parts.append(f"Nombre: {data['name']}")
            
            if 'position' in data:
                summary_parts.append(f"Posición: {data['position']}")
            
            if 'affiliation' in data:
                summary_parts.append(f"Afiliación: {data['affiliation']}")
            
            if 'research_areas' in data and isinstance(data['research_areas'], list):
                areas = ', '.join(data['research_areas'][:3])  # Primeras 3 áreas
                summary_parts.append(f"Áreas de investigación: {areas}")
            
            if 'email' in data:
                summary_parts.append(f"Email: {data['email']}")
            
            # Información sobre publicaciones recientes
            if 'recent_publications' in data and isinstance(data['recent_publications'], list):
                pub_count = len(data['recent_publications'])
                summary_parts.append(f"Publicaciones recientes: {pub_count}")
            
            summary = ". ".join(summary_parts)
            
            return ContextData(
                source="PURE Universidad de La Sabana",
                content_type="researcher",
                title=title,
                summary=summary,
                full_data=researcher_data,
                relevance_score=self._calculate_researcher_relevance(data)
            )
        
        except Exception as e:
            logger.debug(f"Error procesando investigador: {e}")
            return None
    
    def _create_publication_context(self, publication_data: Dict) -> Optional[ContextData]:
        """Crear contexto para una publicación"""
        try:
            data = publication_data.get('data', {})
            title = publication_data.get('title', 'Publicación sin título')
            
            # Crear resumen de la publicación
            summary_parts = []
            
            if 'title' in data:
                summary_parts.append(f"Título: {data['title']}")
            
            if 'authors' in data and isinstance(data['authors'], list):
                authors = ', '.join(data['authors'][:3])  # Primeros 3 autores
                if len(data['authors']) > 3:
                    authors += f" y {len(data['authors']) - 3} más"
                summary_parts.append(f"Autores: {authors}")
            
            if 'year' in data:
                summary_parts.append(f"Año: {data['year']}")
            
            if 'journal' in data:
                summary_parts.append(f"Revista: {data['journal']}")
            
            if 'publication_type' in data:
                summary_parts.append(f"Tipo: {data['publication_type']}")
            
            if 'abstract' in data:
                abstract_preview = data['abstract'][:200] + "..." if len(data['abstract']) > 200 else data['abstract']
                summary_parts.append(f"Resumen: {abstract_preview}")
            
            summary = ". ".join(summary_parts)
            
            return ContextData(
                source="PURE Universidad de La Sabana",
                content_type="publication",
                title=title,
                summary=summary,
                full_data=publication_data,
                relevance_score=self._calculate_publication_relevance(data)
            )
        
        except Exception as e:
            logger.debug(f"Error procesando publicación: {e}")
            return None
    
    def _create_project_context(self, project_data: Dict) -> Optional[ContextData]:
        """Crear contexto para un proyecto"""
        try:
            data = project_data.get('data', {})
            title = project_data.get('title', 'Proyecto sin título')
            
            # Crear resumen del proyecto
            summary_parts = []
            
            if 'title' in data:
                summary_parts.append(f"Título: {data['title']}")
            
            if 'principal_investigator' in data:
                summary_parts.append(f"Investigador principal: {data['principal_investigator']}")
            
            if 'funding' in data:
                summary_parts.append(f"Financiamiento: {data['funding']}")
            
            if 'participants' in data and isinstance(data['participants'], list):
                participant_count = len(data['participants'])
                summary_parts.append(f"Participantes: {participant_count}")
            
            if 'dates' in data and isinstance(data['dates'], list):
                dates_str = ', '.join(data['dates'][:2])  # Primeras 2 fechas
                summary_parts.append(f"Fechas: {dates_str}")
            
            if 'description' in data:
                desc_preview = data['description'][:200] + "..." if len(data['description']) > 200 else data['description']
                summary_parts.append(f"Descripción: {desc_preview}")
            
            summary = ". ".join(summary_parts)
            
            return ContextData(
                source="PURE Universidad de La Sabana",
                content_type="project",
                title=title,
                summary=summary,
                full_data=project_data,
                relevance_score=self._calculate_project_relevance(data)
            )
        
        except Exception as e:
            logger.debug(f"Error procesando proyecto: {e}")
            return None
    
    def _create_organization_context(self, org_data: Dict) -> Optional[ContextData]:
        """Crear contexto para una organización"""
        try:
            data = org_data.get('data', {})
            title = org_data.get('title', 'Organización sin nombre')
            
            # Crear resumen de la organización
            summary_parts = []
            
            if 'name' in data:
                summary_parts.append(f"Nombre: {data['name']}")
            
            if 'description' in data:
                desc_preview = data['description'][:200] + "..." if len(data['description']) > 200 else data['description']
                summary_parts.append(f"Descripción: {desc_preview}")
            
            if 'members' in data and isinstance(data['members'], list):
                member_count = len(data['members'])
                summary_parts.append(f"Miembros: {member_count}")
            
            if 'contact' in data and isinstance(data['contact'], dict):
                contact_info = []
                if 'email' in data['contact']:
                    contact_info.append(f"Email: {data['contact']['email']}")
                if 'phone' in data['contact']:
                    contact_info.append(f"Teléfono: {data['contact']['phone']}")
                if contact_info:
                    summary_parts.append(f"Contacto: {', '.join(contact_info)}")
            
            summary = ". ".join(summary_parts)
            
            return ContextData(
                source="PURE Universidad de La Sabana",
                content_type="organization",
                title=title,
                summary=summary,
                full_data=org_data,
                relevance_score=self._calculate_organization_relevance(data)
            )
        
        except Exception as e:
            logger.debug(f"Error procesando organización: {e}")
            return None
    
    def _calculate_researcher_relevance(self, data: Dict) -> float:
        """Calcular score de relevancia para un investigador"""
        score = 0.0
        
        # Factores de relevancia
        if 'name' in data:
            score += 1.0
        
        if 'research_areas' in data and isinstance(data['research_areas'], list):
            score += min(len(data['research_areas']) * 0.2, 1.0)
        
        if 'recent_publications' in data and isinstance(data['recent_publications'], list):
            score += min(len(data['recent_publications']) * 0.1, 1.0)
        
        if 'orcid' in data:
            score += 0.5
        
        if 'biography' in data:
            score += 0.3
        
        # Normalizar entre 0 y 1
        return min(score / 3.8, 1.0)
    
    def _calculate_publication_relevance(self, data: Dict) -> float:
        """Calcular score de relevancia para una publicación"""
        score = 0.0
        
        if 'title' in data:
            score += 1.0
        
        if 'authors' in data and isinstance(data['authors'], list):
            score += min(len(data['authors']) * 0.1, 0.5)
        
        if 'year' in data:
            # Más reciente = más relevante
            current_year = datetime.now().year
            if isinstance(data['year'], int):
                year_diff = current_year - data['year']
                score += max(0, (10 - year_diff) / 10) * 0.5
        
        if 'abstract' in data:
            score += 0.5
        
        if 'doi' in data:
            score += 0.3
        
        # Normalizar entre 0 y 1
        return min(score / 2.8, 1.0)
    
    def _calculate_project_relevance(self, data: Dict) -> float:
        """Calcular score de relevancia para un proyecto"""
        score = 0.0
        
        if 'title' in data:
            score += 1.0
        
        if 'principal_investigator' in data:
            score += 0.5
        
        if 'participants' in data and isinstance(data['participants'], list):
            score += min(len(data['participants']) * 0.1, 0.5)
        
        if 'description' in data:
            score += 0.5
        
        if 'funding' in data:
            score += 0.3
        
        # Normalizar entre 0 y 1
        return min(score / 2.8, 1.0)
    
    def _calculate_organization_relevance(self, data: Dict) -> float:
        """Calcular score de relevancia para una organización"""
        score = 0.0
        
        if 'name' in data:
            score += 1.0
        
        if 'description' in data:
            score += 0.5
        
        if 'members' in data and isinstance(data['members'], list):
            score += min(len(data['members']) * 0.05, 0.5)
        
        if 'contact' in data:
            score += 0.3
        
        # Normalizar entre 0 y 1
        return min(score / 2.3, 1.0)
    
    def get_context_for_query(self, query: str, max_results: int = 10) -> List[ContextData]:
        """Obtener contexto relevante para una consulta específica"""
        query_lower = query.lower()
        relevant_contexts = []
        
        for context in self.processed_data:
            relevance_score = 0.0
            
            # Buscar coincidencias en título
            if any(word in context.title.lower() for word in query_lower.split()):
                relevance_score += 0.3
            
            # Buscar coincidencias en resumen
            if any(word in context.summary.lower() for word in query_lower.split()):
                relevance_score += 0.2
            
            # Buscar coincidencias específicas por tipo de contenido
            if context.content_type == "researcher":
                # Buscar en nombres de investigadores
                full_data = context.full_data.get('data', {})
                if 'name' in full_data and any(word in full_data['name'].lower() for word in query_lower.split()):
                    relevance_score += 0.4
                
                # Buscar en áreas de investigación
                if 'research_areas' in full_data and isinstance(full_data['research_areas'], list):
                    for area in full_data['research_areas']:
                        if any(word in area.lower() for word in query_lower.split()):
                            relevance_score += 0.3
                            break
            
            elif context.content_type == "publication":
                # Buscar en autores
                full_data = context.full_data.get('data', {})
                if 'authors' in full_data and isinstance(full_data['authors'], list):
                    for author in full_data['authors']:
                        if any(word in author.lower() for word in query_lower.split()):
                            relevance_score += 0.3
                            break
            
            # Agregar score base de relevancia del contexto
            relevance_score += context.relevance_score * 0.1
            
            if relevance_score > 0.1:  # Umbral mínimo de relevancia
                context.relevance_score = relevance_score
                relevant_contexts.append(context)
        
        # Ordenar por relevancia y limitar resultados
        relevant_contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_contexts[:max_results]
    
    def generate_enhanced_context(self, base_context: str = "", query: str = "") -> str:
        """Generar contexto enriquecido combinando contexto base con datos de PURE"""
        if not self.processed_data:
            logger.warning("No hay datos de PURE cargados para enriquecer el contexto")
            return base_context
        
        enhanced_context = base_context
        
        if query:
            # Obtener contexto relevante para la consulta específica
            relevant_contexts = self.get_context_for_query(query, max_results=5)
            
            if relevant_contexts:
                enhanced_context += "\n\n=== INFORMACIÓN ADICIONAL DE PURE UNIVERSIDAD DE LA SABANA ===\n"
                
                for i, context in enumerate(relevant_contexts, 1):
                    enhanced_context += f"\n{i}. {context.title} ({context.content_type.title()})\n"
                    enhanced_context += f"   {context.summary}\n"
                    
                    # Agregar URL si está disponible
                    if 'url' in context.full_data:
                        enhanced_context += f"   URL: {context.full_data['url']}\n"
        else:
            # Agregar resumen general de datos disponibles
            summary = self.get_general_summary()
            if summary:
                enhanced_context += "\n\n=== DATOS DISPONIBLES DE PURE UNIVERSIDAD DE LA SABANA ===\n"
                enhanced_context += summary
        
        return enhanced_context
    
    def get_general_summary(self) -> str:
        """Obtener resumen general de todos los datos cargados"""
        if not self.processed_data:
            return ""
        
        # Contar por tipo
        type_counts = {}
        for context in self.processed_data:
            type_counts[context.content_type] = type_counts.get(context.content_type, 0) + 1
        
        summary_parts = []
        
        if 'researcher' in type_counts:
            summary_parts.append(f"- {type_counts['researcher']} investigadores registrados")
        
        if 'publication' in type_counts:
            summary_parts.append(f"- {type_counts['publication']} publicaciones académicas")
        
        if 'project' in type_counts:
            summary_parts.append(f"- {type_counts['project']} proyectos de investigación")
        
        if 'organization' in type_counts:
            summary_parts.append(f"- {type_counts['organization']} organizaciones/departamentos")
        
        # Agregar algunos ejemplos destacados
        top_researchers = [c for c in self.processed_data if c.content_type == 'researcher']
        top_researchers.sort(key=lambda x: x.relevance_score, reverse=True)
        
        if top_researchers:
            summary_parts.append(f"\nInvestigadores destacados incluyen: {', '.join([c.title for c in top_researchers[:3]])}")
        
        # Información sobre actualización
        if 'pure' in self.loaded_contexts and 'metadata' in self.loaded_contexts['pure']:
            metadata = self.loaded_contexts['pure']['metadata']
            if 'scraped_at' in metadata:
                summary_parts.append(f"\nÚltima actualización de datos: {metadata['scraped_at']}")
        
        return "\n".join(summary_parts)
    
    def save_processed_context(self, filename: str = "processed_context.json") -> str:
        """Guardar contexto procesado para uso futuro"""
        filepath = os.path.join(self.context_dir, filename)
        
        processed_data_dict = []
        for context in self.processed_data:
            context_dict = {
                'source': context.source,
                'content_type': context.content_type,
                'title': context.title,
                'summary': context.summary,
                'relevance_score': context.relevance_score,
                'full_data': context.full_data
            }
            processed_data_dict.append(context_dict)
        
        output_data = {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'total_items': len(processed_data_dict),
                'context_loader_version': '1.0'
            },
            'processed_contexts': processed_data_dict
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Contexto procesado guardado en: {filepath}")
        return filepath

# Función de utilidad para integración fácil con el agente principal
def load_and_enhance_context(base_context: str = "", query: str = "", context_dir: str = "scraped_data") -> str:
    """
    Función de utilidad para cargar y enriquecer contexto fácilmente
    Esta función puede ser importada y usada en el agente principal
    """
    try:
        loader = PureContextLoader(context_dir)
        
        # Intentar cargar contexto de PURE
        pure_data = loader.load_pure_context()
        
        if pure_data:
            enhanced_context = loader.generate_enhanced_context(base_context, query)
            return enhanced_context
        else:
            logger.info("No se encontró contexto de PURE, usando contexto base")
            return base_context
    
    except Exception as e:
        logger.error(f"Error enriqueciendo contexto: {e}")
        return base_context

def main():
    """Función principal para pruebas"""
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("=== PRUEBA DEL CARGADOR DE CONTEXTO ===")
    
    # Crear cargador
    loader = PureContextLoader()
    
    # Cargar contexto de PURE
    pure_data = loader.load_pure_context()
    
    if pure_data:
        # Generar resumen
        summary = loader.get_general_summary()
        logger.info(f"Resumen general:\n{summary}")
        
        # Probar búsqueda por consulta
        test_query = "inteligencia artificial"
        relevant_contexts = loader.get_context_for_query(test_query)
        logger.info(f"\nContextos relevantes para '{test_query}': {len(relevant_contexts)}")
        
        # Generar contexto enriquecido
        enhanced = loader.generate_enhanced_context("Contexto base del agente", test_query)
        logger.info(f"\nContexto enriquecido generado (longitud: {len(enhanced)} caracteres)")
        
        # Guardar contexto procesado
        loader.save_processed_context()
    
    else:
        logger.warning("No se pudo cargar contexto de PURE")

if __name__ == "__main__":
    main()
