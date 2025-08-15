
# 🤖 GUÍA DE INTEGRACIÓN - PURE KNOWLEDGE BASE

## 📊 RESUMEN DE DATOS DISPONIBLES

### 🏛️ **Unidades de Investigación**: 150
- Centros de investigación biomédica
- Facultades y escuelas
- Grupos de investigación especializados
- Categorías MinCiencias (A y B)

### 👥 **Investigadores**: 0
- Profesores investigadores
- Doctores y especialistas
- Perfiles académicos completos

### 📚 **Publicaciones**: 0
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
- **Cobertura**: 150 unidades mapeadas
- **Actualización**: 2025-08-14
- **Confiabilidad**: Alta (datos de Pure oficial)

## 🚀 PRÓXIMOS PASOS
1. Integrar funciones en el agente conversacional
2. Probar consultas comunes
3. Expandir con más datos de investigadores
4. Automatizar actualizaciones periódicas
