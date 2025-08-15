#!/usr/bin/env python3
"""
PURE KNOWLEDGE MANAGER - Gestor de conocimiento para Pure Universidad de la Sabana
Integra la información extraída con el agente conversacional sin alterar el contexto existente
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeManagerConfig:
    """Configuración para el gestor de conocimiento"""
    knowledge_base_path: str = "scraped_data/pure_knowledge_base_latest.json"
    context_output_path: str = "scraped_data/pure_agent_context.json"
    enable_caching: bool = True
    max_context_size: int = 50000  # Caracteres máximos para contexto

class PureKnowledgeManager:
    """Gestor de conocimiento para Pure Universidad de la Sabana"""
    
    def __init__(self, config: KnowledgeManagerConfig):
        self.config = config
        self.knowledge_base = {}
        self.search_index = {}
        self.agent_context = {}
        
    def load_knowledge_base(self, file_path: Optional[str] = None) -> bool:
        """Cargar base de conocimiento desde archivo"""
        try:
            kb_path = file_path or self.config.knowledge_base_path
            
            if not os.path.exists(kb_path):
                logger.warning(f"Base de conocimiento no encontrada: {kb_path}")
                return False
            
            with open(kb_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            
            logger.info(f"✅ Base de conocimiento cargada desde: {kb_path}")
            logger.info(f"📊 Datos disponibles:")
            logger.info(f"  🏛️ Unidades: {len(self.knowledge_base.get('research_units', []))}")
            logger.info(f"  👥 Investigadores: {len(self.knowledge_base.get('researchers', []))}")
            logger.info(f"  📚 Publicaciones: {len(self.knowledge_base.get('scientific_production', []))}")
            
            # Crear índice de búsqueda
            self.create_search_index()
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando base de conocimiento: {e}")
            return False

    def create_search_index(self):
        """Crear índice de búsqueda para acceso rápido"""
        try:
            self.search_index = {
                'researchers_by_name': {},
                'researchers_by_unit': {},
                'researchers_by_area': {},
                'units_by_name': {},
                'units_by_type': {},
                'publications_by_author': {},
                'publications_by_year': {},
                'keywords': set()
            }
            
            # Indexar investigadores
            for researcher in self.knowledge_base.get('researchers', []):
                name = researcher.get('name', '').lower()
                self.search_index['researchers_by_name'][name] = researcher
                
                # Por unidad
                unit_name = researcher.get('department', '').lower()
                if unit_name:
                    if unit_name not in self.search_index['researchers_by_unit']:
                        self.search_index['researchers_by_unit'][unit_name] = []
                    self.search_index['researchers_by_unit'][unit_name].append(researcher)
                
                # Por área de investigación
                areas = researcher.get('detailed_info', {}).get('research_areas', [])
                for area in areas:
                    area_lower = area.lower()
                    if area_lower not in self.search_index['researchers_by_area']:
                        self.search_index['researchers_by_area'][area_lower] = []
                    self.search_index['researchers_by_area'][area_lower].append(researcher)
                    self.search_index['keywords'].add(area_lower)
            
            # Indexar unidades
            for unit in self.knowledge_base.get('research_units', []):
                name = unit.get('name', '').lower()
                self.search_index['units_by_name'][name] = unit
                
                unit_type = unit.get('type', '').lower()
                if unit_type:
                    if unit_type not in self.search_index['units_by_type']:
                        self.search_index['units_by_type'][unit_type] = []
                    self.search_index['units_by_type'][unit_type].append(unit)
            
            # Indexar publicaciones
            for pub in self.knowledge_base.get('scientific_production', []):
                authors = pub.get('authors', '').lower()
                year = pub.get('year', '')
                
                if authors:
                    if authors not in self.search_index['publications_by_author']:
                        self.search_index['publications_by_author'][authors] = []
                    self.search_index['publications_by_author'][authors].append(pub)
                
                if year:
                    if year not in self.search_index['publications_by_year']:
                        self.search_index['publications_by_year'][year] = []
                    self.search_index['publications_by_year'][year].append(pub)
            
            logger.info("🔍 Índice de búsqueda creado exitosamente")
            
        except Exception as e:
            logger.error(f"Error creando índice de búsqueda: {e}")

    def search_researchers(self, query: str) -> List[Dict[str, Any]]:
        """Buscar investigadores por nombre, área o unidad"""
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda por nombre exacto
            if query_lower in self.search_index['researchers_by_name']:
                results.append(self.search_index['researchers_by_name'][query_lower])
            
            # Búsqueda por nombre parcial
            for name, researcher in self.search_index['researchers_by_name'].items():
                if query_lower in name and researcher not in results:
                    results.append(researcher)
            
            # Búsqueda por área de investigación
            if query_lower in self.search_index['researchers_by_area']:
                for researcher in self.search_index['researchers_by_area'][query_lower]:
                    if researcher not in results:
                        results.append(researcher)
            
            # Búsqueda por unidad
            for unit_name, researchers in self.search_index['researchers_by_unit'].items():
                if query_lower in unit_name:
                    for researcher in researchers:
                        if researcher not in results:
                            results.append(researcher)
            
            return results[:10]  # Limitar a 10 resultados
            
        except Exception as e:
            logger.error(f"Error buscando investigadores: {e}")
            return []

    def search_units(self, query: str) -> List[Dict[str, Any]]:
        """Buscar unidades de investigación"""
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda por nombre exacto
            if query_lower in self.search_index['units_by_name']:
                results.append(self.search_index['units_by_name'][query_lower])
            
            # Búsqueda por nombre parcial
            for name, unit in self.search_index['units_by_name'].items():
                if query_lower in name and unit not in results:
                    results.append(unit)
            
            # Búsqueda por tipo
            for unit_type, units in self.search_index['units_by_type'].items():
                if query_lower in unit_type:
                    for unit in units:
                        if unit not in results:
                            results.append(unit)
            
            return results[:5]  # Limitar a 5 resultados
            
        except Exception as e:
            logger.error(f"Error buscando unidades: {e}")
            return []

    def search_publications(self, query: str, year: Optional[str] = None) -> List[Dict[str, Any]]:
        """Buscar publicaciones por autor o año"""
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda por año específico
            if year and year in self.search_index['publications_by_year']:
                year_pubs = self.search_index['publications_by_year'][year]
                for pub in year_pubs:
                    if query_lower in pub.get('title', '').lower() or query_lower in pub.get('authors', '').lower():
                        results.append(pub)
            
            # Búsqueda general por autor
            for authors, pubs in self.search_index['publications_by_author'].items():
                if query_lower in authors:
                    for pub in pubs:
                        if pub not in results:
                            results.append(pub)
            
            # Búsqueda por título
            for pub in self.knowledge_base.get('scientific_production', []):
                title = pub.get('title', '').lower()
                if query_lower in title and pub not in results:
                    results.append(pub)
            
            return results[:10]  # Limitar a 10 resultados
            
        except Exception as e:
            logger.error(f"Error buscando publicaciones: {e}")
            return []

    def get_researcher_details(self, researcher_name: str) -> Optional[Dict[str, Any]]:
        """Obtener detalles completos de un investigador"""
        try:
            researchers = self.search_researchers(researcher_name)
            if researchers:
                researcher = researchers[0]  # Tomar el primer resultado
                
                # Enriquecer con información adicional
                enriched = researcher.copy()
                
                # Agregar publicaciones relacionadas
                enriched['related_publications'] = self.search_publications(researcher_name)
                
                # Agregar información de la unidad
                unit_name = researcher.get('department', '')
                if unit_name:
                    units = self.search_units(unit_name)
                    if units:
                        enriched['unit_details'] = units[0]
                
                return enriched
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de investigador: {e}")
            return None

    def get_unit_summary(self, unit_name: str) -> Optional[Dict[str, Any]]:
        """Obtener resumen completo de una unidad"""
        try:
            units = self.search_units(unit_name)
            if units:
                unit = units[0]
                
                # Enriquecer con estadísticas
                enriched = unit.copy()
                
                # Obtener investigadores de la unidad
                unit_researchers = self.search_index['researchers_by_unit'].get(unit_name.lower(), [])
                enriched['researchers'] = unit_researchers
                
                # Calcular estadísticas
                total_publications = 0
                research_areas = set()
                
                for researcher in unit_researchers:
                    pub_count = researcher.get('detailed_info', {}).get('publications_count', 0)
                    total_publications += pub_count
                    
                    areas = researcher.get('detailed_info', {}).get('research_areas', [])
                    research_areas.update(areas)
                
                enriched['statistics'] = {
                    'total_researchers': len(unit_researchers),
                    'total_publications': total_publications,
                    'research_areas': list(research_areas)
                }
                
                return enriched
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de unidad: {e}")
            return None

    def generate_agent_context(self) -> Dict[str, Any]:
        """Generar contexto estructurado para el agente conversacional"""
        try:
            context = {
                "pure_knowledge_base": {
                    "metadata": {
                        "last_updated": datetime.now().isoformat(),
                        "source": "Pure Universidad de la Sabana",
                        "description": "Base de conocimiento completa de investigación universitaria"
                    },
                    "summary": {
                        "total_units": len(self.knowledge_base.get('research_units', [])),
                        "total_researchers": len(self.knowledge_base.get('researchers', [])),
                        "total_publications": len(self.knowledge_base.get('scientific_production', [])),
                        "available_search_functions": [
                            "search_researchers",
                            "search_units", 
                            "search_publications",
                            "get_researcher_details",
                            "get_unit_summary"
                        ]
                    },
                    "sample_data": {
                        "top_units": [unit.get('name') for unit in self.knowledge_base.get('research_units', [])[:5]],
                        "sample_researchers": [r.get('name') for r in self.knowledge_base.get('researchers', [])[:5]],
                        "research_areas": list(self.search_index['keywords'])[:20]
                    }
                }
            }
            
            # Comprimir contexto si es muy grande
            context_str = json.dumps(context, ensure_ascii=False)
            if len(context_str) > self.config.max_context_size:
                # Reducir datos de muestra
                context["pure_knowledge_base"]["sample_data"]["top_units"] = context["pure_knowledge_base"]["sample_data"]["top_units"][:3]
                context["pure_knowledge_base"]["sample_data"]["sample_researchers"] = context["pure_knowledge_base"]["sample_data"]["sample_researchers"][:3]
                context["pure_knowledge_base"]["sample_data"]["research_areas"] = context["pure_knowledge_base"]["sample_data"]["research_areas"][:10]
            
            self.agent_context = context
            return context
            
        except Exception as e:
            logger.error(f"Error generando contexto del agente: {e}")
            return {}

    def save_agent_context(self, output_path: Optional[str] = None) -> bool:
        """Guardar contexto del agente en archivo"""
        try:
            output_file = output_path or self.config.context_output_path
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.agent_context, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Contexto del agente guardado en: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando contexto del agente: {e}")
            return False

    def get_knowledge_functions(self) -> Dict[str, callable]:
        """Obtener funciones de conocimiento para integrar con el agente"""
        return {
            'search_researchers': self.search_researchers,
            'search_units': self.search_units,
            'search_publications': self.search_publications,
            'get_researcher_details': self.get_researcher_details,
            'get_unit_summary': self.get_unit_summary
        }

    def query_knowledge(self, query_type: str, query: str, **kwargs) -> Dict[str, Any]:
        """Interfaz unificada para consultas al conocimiento"""
        try:
            if query_type == "researcher":
                results = self.search_researchers(query)
                return {"type": "researchers", "results": results, "count": len(results)}
            
            elif query_type == "unit":
                results = self.search_units(query)
                return {"type": "units", "results": results, "count": len(results)}
            
            elif query_type == "publication":
                year = kwargs.get('year')
                results = self.search_publications(query, year)
                return {"type": "publications", "results": results, "count": len(results)}
            
            elif query_type == "researcher_details":
                result = self.get_researcher_details(query)
                return {"type": "researcher_details", "result": result}
            
            elif query_type == "unit_summary":
                result = self.get_unit_summary(query)
                return {"type": "unit_summary", "result": result}
            
            else:
                return {"error": f"Tipo de consulta no válido: {query_type}"}
                
        except Exception as e:
            logger.error(f"Error en consulta de conocimiento: {e}")
            return {"error": str(e)}

def main():
    """Función principal para probar el gestor de conocimiento"""
    config = KnowledgeManagerConfig()
    manager = PureKnowledgeManager(config)
    
    # Buscar el archivo de conocimiento más reciente
    data_dir = "scraped_data"
    kb_files = [f for f in os.listdir(data_dir) if f.startswith('pure_knowledge_base_') and f.endswith('.json')]
    
    if not kb_files:
        logger.error("❌ No se encontraron archivos de base de conocimiento")
        logger.info("🔧 Ejecutar primero: python pure_detailed_extractor.py")
        return
    
    # Usar el archivo más reciente
    latest_file = max(kb_files)
    kb_path = os.path.join(data_dir, latest_file)
    
    logger.info(f"📂 Usando base de conocimiento: {latest_file}")
    
    if manager.load_knowledge_base(kb_path):
        # Generar contexto para el agente
        context = manager.generate_agent_context()
        
        if context:
            manager.save_agent_context()
            logger.info("✅ Gestor de conocimiento configurado exitosamente")
            
            # Pruebas de funcionalidad
            logger.info("\n🧪 PRUEBAS DE FUNCIONALIDAD:")
            
            # Buscar investigadores
            researchers = manager.search_researchers("profesor")
            logger.info(f"👥 Investigadores encontrados: {len(researchers)}")
            
            # Buscar unidades
            units = manager.search_units("facultad")
            logger.info(f"🏛️ Unidades encontradas: {len(units)}")
            
            # Buscar publicaciones
            publications = manager.search_publications("investigación")
            logger.info(f"📚 Publicaciones encontradas: {len(publications)}")
            
            logger.info("\n🎉 GESTOR DE CONOCIMIENTO LISTO PARA INTEGRACIÓN CON AGENTE")
        
    else:
        logger.error("❌ Error cargando base de conocimiento")

if __name__ == "__main__":
    main()
