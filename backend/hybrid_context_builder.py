#!/usr/bin/env python3
"""
HYBRID CONTEXT BUILDER - Constructor de contexto híbrido
Combina datos existentes de Pure con nueva información extraída y datos de investigadores/publicaciones
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HybridContextConfig:
    """Configuración para el constructor de contexto híbrido"""
    existing_data_path: str = "scraped_data/scrapfly_complete_20250814_210110.json"
    new_units_data_path: str = "scraped_data/pure_knowledge_base_20250814_213019.json"
    output_path: str = "scraped_data/pure_hybrid_context.json"
    enable_researcher_extraction: bool = True
    max_context_size: int = 100000

class HybridContextBuilder:
    """Constructor de contexto híbrido para Pure Universidad de la Sabana"""
    
    def __init__(self, config: HybridContextConfig):
        self.config = config
        self.existing_data = {}
        self.new_units_data = {}
        self.hybrid_context = {}
        
    def load_existing_data(self) -> bool:
        """Cargar datos existentes exitosos"""
        try:
            if not os.path.exists(self.config.existing_data_path):
                logger.warning(f"Datos existentes no encontrados: {self.config.existing_data_path}")
                return False
            
            with open(self.config.existing_data_path, 'r', encoding='utf-8') as f:
                self.existing_data = json.load(f)
            
            logger.info(f"✅ Datos existentes cargados desde: {self.config.existing_data_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando datos existentes: {e}")
            return False

    def load_new_units_data(self) -> bool:
        """Cargar nueva información de unidades"""
        try:
            if not os.path.exists(self.config.new_units_data_path):
                logger.warning(f"Nuevos datos de unidades no encontrados: {self.config.new_units_data_path}")
                return False
            
            with open(self.config.new_units_data_path, 'r', encoding='utf-8') as f:
                self.new_units_data = json.load(f)
            
            logger.info(f"✅ Nuevos datos de unidades cargados: {len(self.new_units_data.get('research_units', []))} unidades")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando nuevos datos de unidades: {e}")
            return False

    def extract_researchers_from_existing_data(self) -> List[Dict[str, Any]]:
        """Extraer información de investigadores de datos existentes"""
        researchers = []
        
        try:
            # Buscar en datos exitosos anteriores
            sections_data = self.existing_data.get('sections_data', {})
            
            for section_name, section_data in sections_data.items():
                section_content = section_data.get('content', '')
                
                # Buscar patrones de investigadores en el contenido
                researchers_found = self.extract_researcher_patterns(section_content, section_name)
                researchers.extend(researchers_found)
            
            # Remover duplicados
            unique_researchers = []
            seen_names = set()
            
            for researcher in researchers:
                name = researcher.get('name', '').strip().lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_researchers.append(researcher)
            
            logger.info(f"📊 Investigadores extraídos de datos existentes: {len(unique_researchers)}")
            return unique_researchers
            
        except Exception as e:
            logger.error(f"Error extrayendo investigadores: {e}")
            return []

    def extract_researcher_patterns(self, content: str, section_name: str) -> List[Dict[str, Any]]:
        """Extraer patrones de investigadores del contenido"""
        researchers = []
        
        try:
            import re
            
            # Patrones para encontrar investigadores
            patterns = [
                r'Dr\.?\s+([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+)',
                r'Dra\.?\s+([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+)',
                r'Profesor(?:a)?\s+([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+)',
                r'Investigador(?:a)?\s+([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+)',
                r'([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+),?\s+PhD',
                r'([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+),?\s+Mg\.',
                r'([A-Z][a-záéíóúü]+(?:\s+[A-Z][a-záéíóúü]+)+),?\s+M\.Sc\.',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    name = match.strip()
                    if len(name.split()) >= 2:  # Al menos nombre y apellido
                        researcher = {
                            'name': name,
                            'source_section': section_name,
                            'department': self.infer_department(section_name),
                            'extraction_method': 'pattern_matching',
                            'found_in': 'existing_data'
                        }
                        researchers.append(researcher)
            
            return researchers
            
        except Exception as e:
            logger.debug(f"Error en extracción de patrones: {e}")
            return []

    def infer_department(self, section_name: str) -> str:
        """Inferir departamento basado en el nombre de la sección"""
        section_lower = section_name.lower()
        
        dept_mappings = {
            'medicina': 'Facultad de Medicina',
            'enfermeria': 'Facultad de Enfermería y Rehabilitación',
            'ingenieria': 'Facultad de Ingeniería',
            'comunicacion': 'Facultad de Comunicación',
            'economia': 'Escuela Internacional de Ciencias Económicas y Administrativas',
            'administracion': 'Escuela Internacional de Ciencias Económicas y Administrativas',
            'derecho': 'Facultad de Derecho y Ciencias Políticas',
            'psicologia': 'Facultad de Psicología',
            'educacion': 'Facultad de Educación',
            'filosofia': 'Facultad de Filosofía y Ciencias Humanas'
        }
        
        for keyword, department in dept_mappings.items():
            if keyword in section_lower:
                return department
        
        return 'Universidad de la Sabana'

    def extract_publications_from_existing_data(self) -> List[Dict[str, Any]]:
        """Extraer información de publicaciones de datos existentes"""
        publications = []
        
        try:
            sections_data = self.existing_data.get('sections_data', {})
            
            for section_name, section_data in sections_data.items():
                section_content = section_data.get('content', '')
                
                # Buscar patrones de publicaciones
                publications_found = self.extract_publication_patterns(section_content, section_name)
                publications.extend(publications_found)
            
            logger.info(f"📚 Publicaciones extraídas de datos existentes: {len(publications)}")
            return publications
            
        except Exception as e:
            logger.error(f"Error extrayendo publicaciones: {e}")
            return []

    def extract_publication_patterns(self, content: str, section_name: str) -> List[Dict[str, Any]]:
        """Extraer patrones de publicaciones del contenido"""
        publications = []
        
        try:
            import re
            
            # Patrones para encontrar publicaciones
            patterns = [
                r'(?:doi:|DOI:)\s*(10\.\d+/[^\s]+)',
                r'(?:Journal|Revista|Conference|Conferencia):\s*([^.\n]+)',
                r'(?:Published|Publicado|Appeared)(?:\s+in)?\s*([^.\n]+)',
                r'"([^"]+)"(?:\s*\(\d{4}\))',  # Títulos entre comillas con año
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    title = match.strip()
                    if len(title) > 10:  # Filtrar títulos muy cortos
                        publication = {
                            'title': title,
                            'source_section': section_name,
                            'extraction_method': 'pattern_matching',
                            'found_in': 'existing_data',
                            'year': self.extract_year_from_context(content, title)
                        }
                        publications.append(publication)
            
            return publications
            
        except Exception as e:
            logger.debug(f"Error en extracción de publicaciones: {e}")
            return []

    def extract_year_from_context(self, content: str, title: str) -> str:
        """Extraer año del contexto alrededor del título"""
        try:
            import re
            
            # Buscar años cerca del título
            title_pos = content.find(title)
            if title_pos != -1:
                context = content[max(0, title_pos-100):title_pos+len(title)+100]
                year_pattern = r'\b(20\d{2})\b'
                years = re.findall(year_pattern, context)
                if years:
                    return years[0]
            
            return 'N/A'
            
        except Exception as e:
            return 'N/A'

    def clean_research_units(self) -> List[Dict[str, Any]]:
        """Limpiar y estructurar información de unidades de investigación"""
        clean_units = []
        
        try:
            raw_units = self.new_units_data.get('research_units', [])
            
            for unit in raw_units:
                # Filtrar unidades con nombres válidos
                name = unit.get('name', '').strip()
                if not name or len(name) < 5 or 'Universidad' in name and '(1)' in name:
                    continue
                
                clean_unit = {
                    'name': name,
                    'unit_id': unit.get('unit_id', ''),
                    'type': unit.get('type', '').replace('Unidad organizativa:', '').strip(),
                    'profile_url': unit.get('profile_url', ''),
                    'research_areas': self.extract_clean_research_areas(unit),
                    'category': self.extract_category(unit),
                    'status': 'active'
                }
                
                clean_units.append(clean_unit)
            
            logger.info(f"🏛️ Unidades limpias procesadas: {len(clean_units)}")
            return clean_units
            
        except Exception as e:
            logger.error(f"Error limpiando unidades: {e}")
            return []

    def extract_clean_research_areas(self, unit: Dict[str, Any]) -> List[str]:
        """Extraer áreas de investigación limpias"""
        try:
            areas = unit.get('detailed_info', {}).get('research_areas', [])
            clean_areas = []
            
            for area in areas:
                if isinstance(area, str) and len(area) > 10:
                    # Limpiar texto de categorías
                    if 'Categoría MinCiencias' in area:
                        # Extraer solo las categorías relevantes
                        import re
                        categories = re.findall(r'Categoría ([AB])', area)
                        if categories:
                            clean_areas.append(f"Categoría MinCiencias: {categories[0]}")
                    else:
                        clean_areas.append(area[:100])  # Limitar longitud
            
            return clean_areas
            
        except Exception as e:
            return []

    def extract_category(self, unit: Dict[str, Any]) -> str:
        """Extraer categoría de la unidad"""
        try:
            areas = unit.get('detailed_info', {}).get('research_areas', [])
            for area in areas:
                if 'Categoría MinCiencias2022' in str(area):
                    import re
                    match = re.search(r'2022:\s*Categoría\s*([AB])', str(area))
                    if match:
                        return f"MinCiencias Categoría {match.group(1)}"
            return 'Sin categoría'
            
        except Exception as e:
            return 'Sin categoría'

    def build_hybrid_context(self) -> Dict[str, Any]:
        """Construir contexto híbrido completo"""
        logger.info("🔧 CONSTRUYENDO CONTEXTO HÍBRIDO")
        
        # Extraer información de diferentes fuentes
        researchers = self.extract_researchers_from_existing_data()
        publications = self.extract_publications_from_existing_data()
        clean_units = self.clean_research_units()
        
        # Crear contexto estructurado
        context = {
            "metadata": {
                "created_date": datetime.now().isoformat(),
                "source_files": [
                    self.config.existing_data_path,
                    self.config.new_units_data_path
                ],
                "extraction_method": "hybrid_combination",
                "total_cost": self.existing_data.get('metadata', {}).get('total_cost', 0) + 
                             self.new_units_data.get('metadata', {}).get('total_cost', 0),
                "summary": {
                    "research_units": len(clean_units),
                    "researchers": len(researchers),
                    "publications": len(publications),
                    "data_quality": "high" if len(researchers) > 10 else "medium"
                }
            },
            "research_units": clean_units,
            "researchers": researchers,
            "publications": publications,
            "knowledge_categories": {
                "biomedical_research": [u for u in clean_units if 'biomédic' in u['name'].lower() or 'CIBUS' in u['name']],
                "communication": [u for u in clean_units if 'comunicación' in u['name'].lower()],
                "engineering": [u for u in clean_units if 'ingenier' in u['name'].lower()],
                "medicine": [u for u in clean_units if 'medicina' in u['name'].lower() or 'clínica' in u['name'].lower()],
                "business": [u for u in clean_units if 'econom' in u['name'].lower() or 'admin' in u['name'].lower()],
                "law": [u for u in clean_units if 'derecho' in u['name'].lower()],
                "education": [u for u in clean_units if 'educación' in u['name'].lower()]
            },
            "search_capabilities": {
                "can_search_researchers": True,
                "can_search_units": True,
                "can_search_publications": True,
                "can_provide_details": True,
                "supported_queries": [
                    "investigadores por área",
                    "unidades de investigación",
                    "publicaciones científicas",
                    "grupos de investigación",
                    "categorías MinCiencias"
                ]
            }
        }
        
        self.hybrid_context = context
        return context

    def save_hybrid_context(self) -> bool:
        """Guardar contexto híbrido"""
        try:
            os.makedirs(os.path.dirname(self.config.output_path), exist_ok=True)
            
            with open(self.config.output_path, 'w', encoding='utf-8') as f:
                json.dump(self.hybrid_context, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Contexto híbrido guardado en: {self.config.output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando contexto híbrido: {e}")
            return False

    def create_agent_integration_guide(self) -> str:
        """Crear guía de integración para el agente"""
        guide = f"""
# 🤖 GUÍA DE INTEGRACIÓN - PURE KNOWLEDGE BASE

## 📊 RESUMEN DE DATOS DISPONIBLES

### 🏛️ **Unidades de Investigación**: {len(self.hybrid_context.get('research_units', []))}
- Centros de investigación biomédica
- Facultades y escuelas
- Grupos de investigación especializados
- Categorías MinCiencias (A y B)

### 👥 **Investigadores**: {len(self.hybrid_context.get('researchers', []))}
- Profesores investigadores
- Doctores y especialistas
- Perfiles académicos completos

### 📚 **Publicaciones**: {len(self.hybrid_context.get('publications', []))}
- Artículos científicos
- Conferencias y ponencias
- Producción académica

## 🔧 FUNCIONES DISPONIBLES PARA EL AGENTE

### 1. `buscar_unidades(query: str)`
Busca unidades de investigación por nombre, área o categoría.

### 2. `buscar_investigadores(query: str)`
Encuentra investigadores por nombre, departamento o área de especialización.

### 3. `buscar_publicaciones(query: str, year: str = None)`
Localiza publicaciones científicas por título, autor o año.

### 4. `obtener_estadisticas_facultad(facultad: str)`
Proporciona estadísticas completas de una facultad específica.

### 5. `listar_categorias_minciencias()`
Lista todas las unidades organizadas por categoría MinCiencias.

## 🎯 CASOS DE USO COMUNES

1. **"¿Qué investigadores hay en el área de medicina?"**
   → Usar `buscar_investigadores("medicina")`

2. **"¿Cuáles son los grupos de investigación en ingeniería?"**
   → Usar `buscar_unidades("ingeniería")`

3. **"¿Qué publicaciones recientes hay sobre biomedicina?"**
   → Usar `buscar_publicaciones("biomedicina", "2024")`

4. **"¿Cuántos grupos tiene categoría A en MinCiencias?"**
   → Usar `listar_categorias_minciencias()`

## 📈 CALIDAD DE DATOS
- **Estado**: ✅ Operacional
- **Cobertura**: {len(self.hybrid_context.get('research_units', []))} unidades mapeadas
- **Actualización**: {datetime.now().strftime('%Y-%m-%d')}
- **Confiabilidad**: Alta (datos de Pure oficial)

## 🚀 PRÓXIMOS PASOS
1. Integrar funciones en el agente conversacional
2. Probar consultas comunes
3. Expandir con más datos de investigadores
4. Automatizar actualizaciones periódicas
"""
        
        guide_path = "scraped_data/PURE_AGENT_INTEGRATION_GUIDE.md"
        try:
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(guide)
            logger.info(f"📖 Guía de integración creada: {guide_path}")
        except Exception as e:
            logger.error(f"Error creando guía: {e}")
        
        return guide

def main():
    """Función principal"""
    config = HybridContextConfig()
    builder = HybridContextBuilder(config)
    
    logger.info("🚀 INICIANDO CONSTRUCCIÓN DE CONTEXTO HÍBRIDO")
    
    try:
        # Cargar datos
        existing_loaded = builder.load_existing_data()
        units_loaded = builder.load_new_units_data()
        
        if not existing_loaded and not units_loaded:
            logger.error("❌ No se pudieron cargar datos de ninguna fuente")
            return
        
        # Construir contexto híbrido
        context = builder.build_hybrid_context()
        
        if context:
            # Guardar contexto
            if builder.save_hybrid_context():
                # Crear guía de integración
                builder.create_agent_integration_guide()
                
                logger.info("\n" + "="*60)
                logger.info("🎉 CONTEXTO HÍBRIDO CREADO EXITOSAMENTE")
                logger.info(f"🏛️ Unidades: {context['metadata']['summary']['research_units']}")
                logger.info(f"👥 Investigadores: {context['metadata']['summary']['researchers']}")
                logger.info(f"📚 Publicaciones: {context['metadata']['summary']['publications']}")
                logger.info(f"💰 Costo total: {context['metadata']['total_cost']} créditos")
                logger.info("✅ Listo para integración con agente")
                logger.info("="*60)
            else:
                logger.error("❌ Error guardando contexto híbrido")
        else:
            logger.error("❌ Error construyendo contexto híbrido")
            
    except Exception as e:
        logger.error(f"Error en construcción híbrida: {e}")

if __name__ == "__main__":
    main()
