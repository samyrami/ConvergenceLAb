# 🚀 Sistema de Optimización de Contexto para Sabius

## 📋 Resumen

Sistema de gestión de contexto optimizado que **reduce el uso de tokens en ~96%** (de ~15,000 a ~581 tokens base) sin comprometer la funcionalidad del agente.

## 🎯 Problema Solucionado

**Antes:**
- System prompt de ~15,000+ tokens embebido directamente en `agent.py`
- Toda la información institucional cargada en cada interacción
- Alto consumo de ventana de contexto
- Difícil de mantener y actualizar

**Después:**
- System prompt base de ~581 tokens
- Contexto cargado dinámicamente según relevancia de la consulta
- Reducción de 96.1% en tokens base
- Sistema modular y fácil de mantener

## 🏗️ Arquitectura

### Componentes

```
backend/
├── context_manager.py          # Gestor inteligente de contexto
├── scraped_data/
│   └── context/               # Contextos modulares en JSON
│       ├── core.json          # Siempre presente (~400 tokens)
│       ├── institucional.json # Carga bajo demanda
│       ├── investigacion_ia.json
│       └── emprendimiento.json
└── agent.py                   # Agente optimizado
```

### Flujo de Trabajo

```
Usuario hace pregunta
    ↓
ContextManager analiza keywords
    ↓
Identifica contextos relevantes (max 2-3 secciones)
    ↓
DynamicPromptBuilder construye prompt optimizado
    ↓
Agente responde con contexto mínimo necesario
```

## 📊 Resultados de Optimización

### Métricas de Tokens

| Escenario | Tokens | Reducción |
|-----------|--------|-----------|
| **Prompt original** | ~15,000 | - |
| **Prompt base optimizado** | ~581 | **96.1%** |
| **Con 1 contexto adicional** | ~910 | 93.9% |
| **Con 2 contextos adicionales** | ~1,240 | 91.7% |

### Beneficios

✅ **Eficiencia**: 96% menos tokens por consulta  
✅ **Velocidad**: Respuestas más rápidas  
✅ **Costos**: Reducción significativa en costos de API  
✅ **Mantenibilidad**: Contextos separados y fáciles de actualizar  
✅ **Escalabilidad**: Agregar nuevos contextos sin impactar rendimiento base

## 🔧 Uso

### Agregar Nuevo Contexto

1. Crear archivo JSON en `scraped_data/context/`:

```json
{
  "title": "Título del Contexto",
  "keywords": ["palabra1", "palabra2", "palabra3"],
  "content": "Contenido del contexto en markdown..."
}
```

2. El ContextManager lo cargará automáticamente al iniciar

### Keywords Strategy

El sistema usa keywords para identificar contexto relevante:

- **core**: convergence, lab, laboratorio, reserva, espacios
- **emprendimiento**: emprendimiento, startup, incubadora, mentor
- **investigacion_ia**: investigación, ia, inteligencia artificial, pure
- **institucional**: universidad, sabana, cifras, programas

## 🧪 Testing

Ejecutar tests de validación:

```bash
cd backend
python test_context_optimization.py
```

Tests incluyen:
1. ✅ Inicialización del Context Manager
2. ✅ Constructor de prompts dinámicos
3. ✅ Relevancia de contexto por consulta
4. ✅ Cálculo de ahorro de tokens

## 📈 Comparación: Antes vs Después

### Antes (System Prompt Monolítico)

```python
# agent.py líneas 220-4280 (~4000 líneas de prompt)
super().__init__(instructions=f"""
# Todo el contexto institucional embebido aquí...
# ~15,000 tokens siempre presentes
""")
```

### Después (Context Manager Dinámico)

```python
# agent.py optimizado
self.context_manager = ContextManager()
self.prompt_builder = DynamicPromptBuilder(self.context_manager)

# Prompt base: ~581 tokens
# Contexto adicional: solo lo relevante
optimized_prompt = self.prompt_builder.build_prompt(user_query)
```

## 🔄 Actualizaciones Futuras

### Mejoras Planificadas

1. **Búsqueda Semántica Real**
   - Integrar embeddings para matching más preciso
   - Usar FAISS o ChromaDB para búsqueda vectorial

2. **Caché de Contexto**
   - Cachear contextos frecuentemente usados
   - Reducir latencia en consultas repetidas

3. **Contexto por Sesión**
   - Mantener contexto relevante durante toda la conversación
   - Enriquecer dinámicamente según el flujo del diálogo

4. **Analytics**
   - Tracking de contextos más usados
   - Optimización basada en patrones de uso

## 📝 Mantenimiento

### Actualizar Contextos

Editar directamente los archivos JSON en `scraped_data/context/`:

```bash
# Editar contexto institucional
nano scraped_data/context/institucional.json

# El cambio se refleja en el siguiente reinicio del agente
```

### Monitoreo

El sistema registra estadísticas al iniciar:

```
📊 Contextos cargados: 4
📊 Keywords indexados: 27
📊 Tokens estimados (total): ~1808
✅ Prompt optimizado: ~581 tokens (antes: ~15000+ tokens)
```

## ⚠️ Consideraciones

- **No eliminar `core.json`**: Es el contexto esencial siempre presente
- **Keywords precisos**: Usar palabras clave representativas para mejor matching
- **Balance contenido**: Mantener contextos concisos pero completos
- **Testing**: Validar cambios con `test_context_optimization.py`

## 🤝 Contribución

Para agregar nuevos contextos:

1. Identificar información que debe ser modular
2. Crear archivo JSON con estructura estándar
3. Definir keywords relevantes
4. Probar con queries esperadas
5. Validar con tests

## 📚 Referencias

- **Context Manager**: `context_manager.py`
- **Tests**: `test_context_optimization.py`
- **Contextos**: `scraped_data/context/*.json`

---

**Desarrollado por:** Samuel Esteban Ramírez  
**GovLab - Universidad de La Sabana**  
**Fecha:** Noviembre 2025
