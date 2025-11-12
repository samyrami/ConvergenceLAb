"""
Knowledge Base Loader - Utilidad para cargar y consultar la base de conocimiento
del Convergence Lab Agent.

Autor: Samuel Esteban Ramírez
Fecha: 2024-11-11
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class KnowledgeBaseLoader:
    """Cargador y buscador de la base de conocimiento en formato JSON"""
    
    def __init__(self, kb_path: Optional[str] = None):
        """
        Inicializa el loader
        
        Args:
            kb_path: Ruta al directorio de la base de conocimiento.
                    Si no se provee, usa el directorio actual.
        """
        self.kb_path = Path(kb_path) if kb_path else Path(__file__).parent
        self._institutional_data = None
        self._professors_data = None
        self._publications_data = None
        self._search_index = None
        self._stats = None
    
    def load_institutional_context(self) -> Dict[str, Any]:
        """Carga el contexto institucional completo"""
        if self._institutional_data is None:
            file_path = self.kb_path / "institutional_context.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._institutional_data = json.load(f)
            else:
                self._institutional_data = {}
        return self._institutional_data
    
    def load_professors(self) -> List[Dict[str, Any]]:
        """Carga datos de profesores"""
        if self._professors_data is None:
            file_path = self.kb_path / "faculty_professors.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._professors_data = data.get('professors', [])
            else:
                self._professors_data = []
        return self._professors_data
    
    def load_publications(self) -> Dict[str, Any]:
        """Carga datos de publicaciones"""
        if self._publications_data is None:
            file_path = self.kb_path / "research_publications.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._publications_data = json.load(f)
            else:
                self._publications_data = {"by_unit": {}, "by_group": {}}
        return self._publications_data
    
    def load_search_index(self) -> Dict[str, List[int]]:
        """Carga el índice de búsqueda"""
        if self._search_index is None:
            file_path = self.kb_path / "research_search_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._search_index = json.load(f)
            else:
                self._search_index = {}
        return self._search_index
    
    def get_institutional_summary(self) -> str:
        """
        Genera un resumen COMPACTO del contexto institucional
        para usar en el prompt inicial del agente.
        """
        data = self.load_institutional_context()
        
        if not data:
            return "## Universidad de La Sabana\n*Contexto institucional no disponible*"
        
        unisabana = data.get('universidad_sabana', {})
        cifras = unisabana.get('cifras_2024', {})
        
        summary = f"""## 🎓 Universidad de La Sabana - Contexto Institucional

### Modelo U3G
Universidad de Tercera Generación que integra docencia, investigación e impacto social real.

### Cifras 2024
- **{cifras.get('estudiantes', {}).get('total', 'N/A')} estudiantes** ({cifras.get('estudiantes', {}).get('pregrado', 'N/A')} pregrado, {cifras.get('estudiantes', {}).get('posgrado', 'N/A')} posgrado)
- **{cifras.get('profesores', {}).get('total', 'N/A')} profesores**
- **{cifras.get('graduados', 'N/A')} graduados**

### Centros Estratégicos
- **UCTS**: Centro de Ciencia Traslacional
- **Unisabana HUB**: 127 proyectos, 17.462 personas impactadas
- **GovLab**: IA para gobierno y analítica aplicada

### Reconocimientos
- Acreditación Alta Calidad por 10 años
- 4ª universidad privada del país (QS Ranking)
- Top 5 nacional en Saber Pro

**NOTA:** Tienes acceso a base de conocimiento completa sobre profesores, grupos de investigación y publicaciones. Consulta cuando el usuario pregunte sobre investigación específica."""
        
        return summary
    
    def search_professors(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca profesores por nombre, área o grupo
        
        Args:
            query: Término de búsqueda
            limit: Máximo número de resultados
        """
        professors = self.load_professors()
        query_lower = query.lower()
        
        results = []
        for prof in professors:
            # Buscar en nombre
            if query_lower in prof.get('nombre', '').lower():
                results.append(prof)
                continue
            
            # Buscar en título/área
            if query_lower in prof.get('titulo', '').lower():
                results.append(prof)
                continue
            
            # Buscar en grupo
            if 'grupo_url' in prof and query_lower in prof['grupo_url'].lower():
                results.append(prof)
                continue
        
        return results[:limit]
    
    def search_publications(self, query: str, unit: Optional[str] = None, 
                          group: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca publicaciones por tema, unidad o grupo
        
        Args:
            query: Término de búsqueda
            unit: Filtrar por unidad organizativa
            group: Filtrar por grupo de investigación
            limit: Máximo número de resultados
        """
        pub_data = self.load_publications()
        query_lower = query.lower()
        
        # Determinar dónde buscar
        search_pool = []
        
        if unit:
            search_pool = pub_data.get('by_unit', {}).get(unit, [])
        elif group:
            search_pool = pub_data.get('by_group', {}).get(group, [])
        else:
            # Buscar en todas
            for pubs in pub_data.get('by_unit', {}).values():
                search_pool.extend(pubs)
        
        # Filtrar por query
        results = []
        for pub in search_pool:
            titulo = pub.get('titulo', '').lower()
            grupo = pub.get('grupo', '').lower()
            
            if query_lower in titulo or query_lower in grupo:
                results.append(pub)
        
        return results[:limit]
    
    def get_publications_by_unit(self, unit: str) -> List[Dict[str, Any]]:
        """Obtiene todas las publicaciones de una unidad específica"""
        pub_data = self.load_publications()
        return pub_data.get('by_unit', {}).get(unit, [])
    
    def get_publications_by_group(self, group: str) -> List[Dict[str, Any]]:
        """Obtiene todas las publicaciones de un grupo específico"""
        pub_data = self.load_publications()
        return pub_data.get('by_group', {}).get(group, [])
    
    def get_research_areas(self) -> List[str]:
        """Obtiene lista de áreas de investigación disponibles"""
        institutional = self.load_institutional_context()
        unisabana = institutional.get('universidad_sabana', {})
        investigacion = unisabana.get('investigacion_innovacion', {})
        return investigacion.get('focos', [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de conocimiento"""
        if self._stats is None:
            file_path = self.kb_path / "knowledge_base_stats.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._stats = json.load(f)
            else:
                # Generar estadísticas básicas
                self._stats = {
                    "professors": {"total": len(self.load_professors())},
                    "publications": {
                        "total": sum(len(pubs) for pubs in self.load_publications().get('by_unit', {}).values())
                    }
                }
        return self._stats
    
    def format_professors(self, professors: List[Dict[str, Any]]) -> str:
        """Formatea lista de profesores para inyectar en contexto"""
        if not professors:
            return ""
        
        formatted = "\n### Profesores Relevantes:\n\n"
        for prof in professors:
            formatted += f"- **{prof.get('nombre', 'N/A')}**\n"
            if 'titulo' in prof:
                formatted += f"  - Título: {prof['titulo']}\n"
            if 'categoria_minciencias' in prof and prof['categoria_minciencias']:
                formatted += f"  - Categoría MinCiencias: {prof['categoria_minciencias']}\n"
            formatted += "\n"
        
        return formatted
    
    def format_publications(self, publications: List[Dict[str, Any]]) -> str:
        """Formatea lista de publicaciones para inyectar en contexto"""
        if not publications:
            return ""
        
        formatted = "\n### Publicaciones Relevantes:\n\n"
        for pub in publications[:10]:  # Limitar a 10
            formatted += f"- **{pub.get('titulo', 'N/A')}**\n"
            if 'revista' in pub:
                formatted += f"  - Revista: {pub['revista']}\n"
            if 'grupo' in pub:
                formatted += f"  - Grupo: {pub['grupo']}\n"
            formatted += "\n"
        
        return formatted
    
    def get_ai_professors(self) -> List[Dict[str, Any]]:
        """Obtiene lista de profesores que trabajan con IA (predefinida en contexto institucional)"""
        institutional = self.load_institutional_context()
        unisabana = institutional.get('universidad_sabana', {})
        return unisabana.get('profesores_ia', [])
    
    def get_research_groups_ia(self) -> List[Dict[str, Any]]:
        """Obtiene grupos de investigación relacionados con IA"""
        institutional = self.load_institutional_context()
        unisabana = institutional.get('universidad_sabana', {})
        return unisabana.get('grupos_investigacion_ia', [])
    
    def get_strategic_centers(self) -> Dict[str, Any]:
        """Obtiene información de centros estratégicos"""
        institutional = self.load_institutional_context()
        unisabana = institutional.get('universidad_sabana', {})
        return unisabana.get('centros_estrategicos', {})
    
    def get_entrepreneurship_cases(self) -> List[Dict[str, Any]]:
        """Obtiene casos de éxito de emprendimiento"""
        institutional = self.load_institutional_context()
        centro = institutional.get('centro_emprendimiento', {})
        return centro.get('casos_exito', [])
    
    def search_entrepreneurship_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca un caso de éxito específico por nombre"""
        cases = self.get_entrepreneurship_cases()
        name_lower = name.lower()
        
        for case in cases:
            if name_lower in case.get('nombre', '').lower():
                return case
        
        return None


# Ejemplo de uso
if __name__ == "__main__":
    print("="*50)
    print("📚 Knowledge Base Loader - Prueba")
    print("="*50)
    print()
    
    kb = KnowledgeBaseLoader()
    
    # Probar carga de resumen
    print("1. Resumen institucional:")
    print(kb.get_institutional_summary())
    print()
    
    # Probar estadísticas
    print("2. Estadísticas:")
    stats = kb.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print()
    
    # Probar búsqueda de profesores IA
    print("3. Profesores de IA:")
    ai_profs = kb.get_ai_professors()
    print(f"   Total: {len(ai_profs)}")
    for prof in ai_profs[:3]:
        print(f"   - {prof.get('nombre')}")
    print()
    
    # Probar búsqueda de casos de éxito
    print("4. Casos de éxito:")
    cases = kb.get_entrepreneurship_cases()
    print(f"   Total: {len(cases)}")
    for case in cases:
        print(f"   - {case.get('nombre')} ({case.get('empresa')})")
    print()
    
    print("✅ Prueba completada")
