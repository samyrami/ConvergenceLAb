"""
Script para extraer y convertir los datos de investigación embebidos en agent.py
a archivos JSON estructurados y consultables.

Autor: Samuel Esteban Ramírez
Fecha: 2024-11-11
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def parse_professor_data(line: str) -> Dict[str, Any]:
    """Parsea una línea de datos de profesor"""
    parts = line.split(" | ")
    professor = {}
    
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # Mapear nombres de campos
            field_map = {
                "Profesor": "nombre",
                "Título obtenido": "titulo",
                "País de obtención": "pais",
                "Título de pregrado": "pregrado",
                "Categoría institucional": "categoria_institucional",
                "Categoría Minciencias": "categoria_minciencias",
                "Grupo de investigación": "grupo_url"
            }
            
            mapped_key = field_map.get(key, key.lower().replace(" ", "_"))
            professor[mapped_key] = value
    
    return professor

def parse_publication_data(line: str) -> Dict[str, Any]:
    """Parsea una línea de producto de investigación"""
    parts = line.split(" | ")
    publication = {}
    
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # Mapear nombres de campos
            field_map = {
                "Nombre de unidad organizativa": "unidad",
                "Grupos de investigación": "grupo",
                "Libros y cap": "libros_capitulos",
                "Título": "titulo",
                "Título.1": "revista"
            }
            
            mapped_key = field_map.get(key, key.lower().replace(" ", "_"))
            publication[mapped_key] = value
    
    return publication

def extract_from_agent_py():
    """Extrae datos del agent.py original"""
    print("🔍 Leyendo agent.py...")
    
    # Intentar múltiples rutas
    agent_file = Path("../agent.py")
    if not agent_file.exists():
        # Intentar desde el directorio actual
        script_dir = Path(__file__).parent
        agent_file = script_dir.parent / "agent.py"
    
    if not agent_file.exists():
        print(f"❌ No se encontró agent.py en {agent_file.absolute()}")
        return None, None
    
    print(f"   Ubicación: {agent_file.absolute()}")
    
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraer secciones
    professors = []
    publications = []
    
    # Buscar sección de profesores (línea 642-652)
    professor_pattern = r'Profesor:([^\n]+)'
    professor_matches = re.findall(professor_pattern, content)
    
    print(f"✅ Encontrados {len(professor_matches)} profesores")
    
    for match in professor_matches:
        prof = parse_professor_data("Profesor:" + match)
        if prof.get('nombre'):
            professors.append(prof)
    
    # Buscar sección de publicaciones (línea 670+)
    publication_pattern = r'Nombre de unidad organizativa:([^\n]+)'
    publication_matches = re.findall(publication_pattern, content)
    
    print(f"✅ Encontradas {len(publication_matches)} publicaciones")
    
    for match in publication_matches[:1000]:  # Limitar para prueba
        pub = parse_publication_data("Nombre de unidad organizativa:" + match)
        if pub.get('titulo'):
            publications.append(pub)
    
    return professors, publications

def organize_by_unit(publications: List[Dict]) -> Dict[str, List[Dict]]:
    """Organiza publicaciones por unidad organizativa"""
    by_unit = defaultdict(list)
    
    for pub in publications:
        unit = pub.get('unidad', 'Sin clasificar')
        by_unit[unit].append(pub)
    
    return dict(by_unit)

def organize_by_research_group(publications: List[Dict]) -> Dict[str, List[Dict]]:
    """Organiza publicaciones por grupo de investigación"""
    by_group = defaultdict(list)
    
    for pub in publications:
        group = pub.get('grupo', 'Sin grupo')
        by_group[group].append(pub)
    
    return dict(by_group)

def create_search_index(data: List[Dict], fields: List[str]) -> Dict[str, List[int]]:
    """Crea índice de búsqueda por palabras clave"""
    index = defaultdict(list)
    
    for idx, item in enumerate(data):
        for field in fields:
            value = item.get(field, '')
            if value:
                # Tokenizar y indexar
                words = re.findall(r'\w+', value.lower())
                for word in words:
                    if len(word) > 3:  # Palabras de más de 3 caracteres
                        if idx not in index[word]:
                            index[word].append(idx)
    
    return dict(index)

def main():
    """Función principal"""
    print("="*50)
    print("📚 Extractor de Datos de Investigación")
    print("Universidad de La Sabana - Convergence Lab")
    print("="*50)
    print()
    
    # Extraer datos
    professors, publications = extract_from_agent_py()
    
    if not professors and not publications:
        print("❌ No se pudieron extraer datos")
        return
    
    # Crear directorio si no existe
    kb_dir = Path(".")
    kb_dir.mkdir(exist_ok=True)
    
    # 1. Guardar profesores
    if professors:
        professors_file = kb_dir / "faculty_professors.json"
        professors_data = {
            "metadata": {
                "total": len(professors),
                "description": "Profesores de Universidad de La Sabana",
                "last_updated": "2024-11-11"
            },
            "professors": professors
        }
        
        with open(professors_file, 'w', encoding='utf-8') as f:
            json.dump(professors_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Guardados {len(professors)} profesores en {professors_file}")
    
    # 2. Guardar publicaciones
    if publications:
        publications_file = kb_dir / "research_publications.json"
        
        # Organizar por unidad y grupo
        by_unit = organize_by_unit(publications)
        by_group = organize_by_research_group(publications)
        
        # Crear índice de búsqueda
        search_index = create_search_index(publications, ['titulo', 'grupo', 'unidad'])
        
        publications_data = {
            "metadata": {
                "total": len(publications),
                "units": len(by_unit),
                "groups": len(by_group),
                "description": "Productos de investigación Universidad de La Sabana (1980-2024)",
                "last_updated": "2024-11-11"
            },
            "by_unit": by_unit,
            "by_group": by_group,
            "search_index": {
                "total_keywords": len(search_index),
                "note": "Use keywords para buscar publicaciones por índice"
            }
        }
        
        with open(publications_file, 'w', encoding='utf-8') as f:
            json.dump(publications_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Guardadas {len(publications)} publicaciones en {publications_file}")
        print(f"   - {len(by_unit)} unidades organizativas")
        print(f"   - {len(by_group)} grupos de investigación")
        print(f"   - {len(search_index)} keywords en índice")
        
        # Guardar índice de búsqueda por separado
        index_file = kb_dir / "research_search_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Índice de búsqueda en {index_file}")
    
    # 3. Crear resumen estadístico
    stats = {
        "metadata": {
            "generated": "2024-11-11",
            "description": "Estadísticas de la base de conocimiento"
        },
        "professors": {
            "total": len(professors),
            "by_category": {}
        },
        "publications": {
            "total": len(publications),
            "by_unit": {unit: len(pubs) for unit, pubs in by_unit.items()},
            "by_group": {group: len(pubs) for group, pubs in by_group.items()}
        }
    }
    
    stats_file = kb_dir / "knowledge_base_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Estadísticas en {stats_file}")
    print()
    print("="*50)
    print("✅ COMPLETADO - Base de conocimiento generada")
    print("="*50)

if __name__ == "__main__":
    main()
