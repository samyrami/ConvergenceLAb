#!/usr/bin/env python3
"""
PURE HYBRID MANAGER - Gestor específico para contexto híbrido de Pure
Maneja búsquedas y consultas en el contexto híbrido combinado
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PureHybridManager:
    """Gestor especializado para contexto híbrido de Pure"""
    
    def __init__(self, context_path: str = "scraped_data/pure_hybrid_context.json"):
        self.context_path = context_path
        self.context = {}
        self.units_index = {}
        self.researchers_index = {}
        self.categories_index = {}
        self.loaded = False
        
    def load_context(self) -> bool:
        """Cargar contexto híbrido"""
        try:
            if not os.path.exists(self.context_path):
                logger.warning(f"Contexto híbrido no encontrado: {self.context_path}")
                return False
            
            with open(self.context_path, 'r', encoding='utf-8') as f:
                self.context = json.load(f)
            
            # Crear índices para búsqueda rápida
            self.create_search_indices()
            
            self.loaded = True
            logger.info(f"✅ Contexto híbrido cargado exitosamente")
            logger.info(f"📊 Datos disponibles:")
            logger.info(f"  🏛️ Unidades: {len(self.context.get('research_units', []))}")
            logger.info(f"  👥 Investigadores: {len(self.context.get('researchers', []))}")
            logger.info(f"  📚 Publicaciones: {len(self.context.get('publications', []))}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando contexto híbrido: {e}")
            return False

    def create_search_indices(self):
        """Crear índices de búsqueda"""
        try:
            # Índice de unidades
            for unit in self.context.get('research_units', []):
                name = unit.get('name', '').lower()
                self.units_index[name] = unit
                
                # Índice por palabras clave
                keywords = name.split()
                for keyword in keywords:
                    if len(keyword) > 3:  # Filtrar palabras muy cortas
                        if keyword not in self.units_index:
                            self.units_index[keyword] = []
                        if isinstance(self.units_index[keyword], list):
                            self.units_index[keyword].append(unit)
                        else:
                            self.units_index[keyword] = [self.units_index[keyword], unit]
            
            # Índice de investigadores
            for researcher in self.context.get('researchers', []):
                name = researcher.get('name', '').lower()
                self.researchers_index[name] = researcher
            
            # Índice de categorías
            categories = self.context.get('knowledge_categories', {})
            for category, units in categories.items():
                self.categories_index[category] = units
            
            logger.info("🔍 Índices de búsqueda creados")
            
        except Exception as e:
            logger.error(f"Error creando índices: {e}")

    def search_units(self, query: str) -> List[Dict[str, Any]]:
        """Buscar unidades de investigación"""
        if not self.loaded:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda exacta por nombre
            if query_lower in self.units_index:
                unit = self.units_index[query_lower]
                if isinstance(unit, dict):
                    results.append(unit)
                elif isinstance(unit, list):
                    results.extend(unit)
            
            # Búsqueda por palabras clave
            query_words = query_lower.split()
            for word in query_words:
                if word in self.units_index:
                    matches = self.units_index[word]
                    if isinstance(matches, dict):
                        if matches not in results:
                            results.append(matches)
                    elif isinstance(matches, list):
                        for match in matches:
                            if match not in results:
                                results.append(match)
            
            # Búsqueda parcial en nombres
            if not results:
                for unit in self.context.get('research_units', []):
                    name = unit.get('name', '').lower()
                    if query_lower in name:
                        results.append(unit)
            
            return results[:10]  # Limitar a 10 resultados
            
        except Exception as e:
            logger.error(f"Error buscando unidades: {e}")
            return []

    def search_researchers(self, query: str) -> List[Dict[str, Any]]:
        """Buscar investigadores"""
        if not self.loaded:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda exacta
            if query_lower in self.researchers_index:
                results.append(self.researchers_index[query_lower])
            
            # Búsqueda parcial
            for researcher in self.context.get('researchers', []):
                name = researcher.get('name', '').lower()
                department = researcher.get('department', '').lower()
                
                if query_lower in name or query_lower in department:
                    if researcher not in results:
                        results.append(researcher)
            
            return results[:10]
            
        except Exception as e:
            logger.error(f"Error buscando investigadores: {e}")
            return []

    def search_publications(self, query: str, year: Optional[str] = None) -> List[Dict[str, Any]]:
        """Buscar publicaciones"""
        if not self.loaded:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            for publication in self.context.get('publications', []):
                title = publication.get('title', '').lower()
                pub_year = publication.get('year', '')
                
                # Filtrar por año si se especifica
                if year and pub_year != year:
                    continue
                
                if query_lower in title:
                    results.append(publication)
            
            return results[:10]
            
        except Exception as e:
            logger.error(f"Error buscando publicaciones: {e}")
            return []

    def get_units_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Obtener unidades por categoría"""
        if not self.loaded:
            return []
        
        try:
            category_lower = category.lower()
            
            # Buscar en categorías predefinidas
            for cat_name, units in self.categories_index.items():
                if category_lower in cat_name.lower():
                    return units
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo categoría: {e}")
            return []

    def get_minciencias_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Obtener unidades organizadas por categoría MinCiencias"""
        if not self.loaded:
            return {}
        
        try:
            categories = {"A": [], "B": [], "Sin categoría": []}
            
            for unit in self.context.get('research_units', []):
                category = unit.get('category', 'Sin categoría')
                
                if 'Categoría A' in category:
                    categories["A"].append(unit)
                elif 'Categoría B' in category:
                    categories["B"].append(unit)
                else:
                    categories["Sin categoría"].append(unit)
            
            return categories
            
        except Exception as e:
            logger.error(f"Error obteniendo categorías MinCiencias: {e}")
            return {}

    def get_faculty_statistics(self, faculty_name: str) -> Dict[str, Any]:
        """Obtener estadísticas de una facultad"""
        if not self.loaded:
            return {}
        
        try:
            faculty_lower = faculty_name.lower()
            faculty_units = []
            faculty_researchers = []
            
            # Buscar unidades de la facultad
            for unit in self.context.get('research_units', []):
                unit_name = unit.get('name', '').lower()
                if faculty_lower in unit_name:
                    faculty_units.append(unit)
            
            # Buscar investigadores de la facultad
            for researcher in self.context.get('researchers', []):
                dept = researcher.get('department', '').lower()
                if faculty_lower in dept:
                    faculty_researchers.append(researcher)
            
            statistics = {
                'faculty_name': faculty_name,
                'total_units': len(faculty_units),
                'total_researchers': len(faculty_researchers),
                'units': [unit['name'] for unit in faculty_units],
                'main_research_areas': self.extract_research_areas(faculty_units),
                'minciencias_categories': self.get_faculty_categories(faculty_units)
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de facultad: {e}")
            return {}

    def extract_research_areas(self, units: List[Dict[str, Any]]) -> List[str]:
        """Extraer áreas de investigación de una lista de unidades"""
        areas = set()
        
        for unit in units:
            unit_areas = unit.get('research_areas', [])
            for area in unit_areas:
                if len(area) > 5:  # Filtrar áreas muy cortas
                    areas.add(area)
        
        return list(areas)[:10]  # Limitar a 10 áreas principales

    def get_faculty_categories(self, units: List[Dict[str, Any]]) -> Dict[str, int]:
        """Obtener distribución de categorías MinCiencias por facultad"""
        categories = {"A": 0, "B": 0, "Sin categoría": 0}
        
        for unit in units:
            category = unit.get('category', 'Sin categoría')
            
            if 'Categoría A' in category:
                categories["A"] += 1
            elif 'Categoría B' in category:
                categories["B"] += 1
            else:
                categories["Sin categoría"] += 1
        
        return categories

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales del contexto"""
        if not self.loaded:
            return {}
        
        try:
            metadata = self.context.get('metadata', {})
            
            # Distribución por categorías
            minciencias_dist = self.get_minciencias_categories()
            
            # Áreas principales
            all_units = self.context.get('research_units', [])
            main_areas = self.extract_research_areas(all_units)
            
            statistics = {
                'extraction_date': metadata.get('created_date', ''),
                'total_cost': metadata.get('total_cost', 0),
                'data_quality': metadata.get('summary', {}).get('data_quality', 'unknown'),
                'units_by_category': {
                    'A': len(minciencias_dist.get('A', [])),
                    'B': len(minciencias_dist.get('B', [])),
                    'Sin categoría': len(minciencias_dist.get('Sin categoría', []))
                },
                'main_research_areas': main_areas,
                'knowledge_categories': list(self.categories_index.keys()),
                'search_capabilities': self.context.get('search_capabilities', {})
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas generales: {e}")
            return {}

    def query_knowledge(self, query_type: str, query: str, **kwargs) -> Dict[str, Any]:
        """Interfaz unificada para consultas"""
        try:
            if query_type == "units":
                results = self.search_units(query)
                return {"type": "units", "results": results, "count": len(results)}
            
            elif query_type == "researchers":
                results = self.search_researchers(query)
                return {"type": "researchers", "results": results, "count": len(results)}
            
            elif query_type == "publications":
                year = kwargs.get('year')
                results = self.search_publications(query, year)
                return {"type": "publications", "results": results, "count": len(results)}
            
            elif query_type == "category":
                results = self.get_units_by_category(query)
                return {"type": "category", "results": results, "count": len(results)}
            
            elif query_type == "minciencias":
                results = self.get_minciencias_categories()
                return {"type": "minciencias", "results": results}
            
            elif query_type == "faculty_stats":
                results = self.get_faculty_statistics(query)
                return {"type": "faculty_stats", "results": results}
            
            elif query_type == "summary":
                results = self.get_summary_statistics()
                return {"type": "summary", "results": results}
            
            else:
                return {"error": f"Tipo de consulta no válido: {query_type}"}
                
        except Exception as e:
            logger.error(f"Error en consulta: {e}")
            return {"error": str(e)}

def main():
    """Función principal para probar el gestor híbrido"""
    manager = PureHybridManager()
    
    if manager.load_context():
        logger.info("\n🧪 PRUEBAS DE FUNCIONALIDAD:")
        
        # Prueba búsqueda de unidades
        units = manager.search_units("biomédica")
        logger.info(f"🏛️ Unidades biomédicas: {len(units)}")
        
        # Prueba categorías MinCiencias
        categories = manager.get_minciencias_categories()
        logger.info(f"📊 Categorías MinCiencias: A={len(categories.get('A', []))}, B={len(categories.get('B', []))}")
        
        # Prueba estadísticas generales
        stats = manager.get_summary_statistics()
        logger.info(f"📈 Calidad de datos: {stats.get('data_quality', 'unknown')}")
        
        logger.info("\n✅ GESTOR HÍBRIDO LISTO PARA USO")
    else:
        logger.error("❌ Error cargando contexto híbrido")

if __name__ == "__main__":
    main()
