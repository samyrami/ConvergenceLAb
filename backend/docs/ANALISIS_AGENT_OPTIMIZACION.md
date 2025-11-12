# 📊 Análisis y Optimización de `agent.py`
## Universidad de La Sabana - Convergence Lab

---

## 🔴 **ERRORES CRÍTICOS IDENTIFICADOS**

### 1. **Datos Masivos Embebidos en Código (4000+ líneas)**

**Ubicación:** Líneas 348-4334

**Problema:**
- Tienes aproximadamente **4000 líneas** de datos de investigación (productos, profesores, unidades) **hardcodeadas** directamente en el archivo Python
- Estos datos se cargan en **cada inicialización** del agente
- Consumen ~**8,000-12,000 tokens** del prompt del sistema
- Imposibilita el mantenimiento y actualización eficiente

**Impacto:**
```
❌ Ventana de contexto mal utilizada
❌ Costo de tokens innecesario en cada llamada
❌ Tiempo de inicialización lento
❌ Código difícil de mantener
❌ Duplicación de información
```

**Solución:**
```python
# ❌ MAL - Datos embebidos (tu código actual)
context = """
Nombre de unidad organizativa:Inalde Business School | Grupos de investigación:...
Nombre de unidad organizativa:Clínica Universidad de La Sabana | Grupos de investigación:...
[... 4000 líneas más ...]
"""

# ✅ BIEN - Carga desde archivo JSON
def load_research_data():
    with open('scraped_data/research_database.json', 'r') as f:
        return json.load(f)
```

---

### 2. **Contexto Duplicado**

**Ubicación:** Líneas 251-309 y 4344-4402

**Problema:**
- El método `generate_pure_context()` está definido **DOS VECES**
- Contenido similar pero no idéntico
- Genera confusión y desperdicio de memoria

**Solución:**
```python
# Mantener solo UNA definición optimizada
def generate_pure_context_summary(self) -> str:
    """RESUMEN compacto de Pure (no datos completos)"""
    # Solo estadísticas generales
    # Datos detallados se cargan bajo demanda
```

---

### 3. **No se Usa el ContextManager Eficientemente**

**Ubicación:** Líneas 221-222

**Problema:**
```python
# Importas estas clases pero NO las usas correctamente
self.context_manager = ContextManager()
self.prompt_builder = DynamicPromptBuilder(self.context_manager)

# Los 4000+ líneas de datos se cargan directamente al prompt
# en lugar de usar el context_manager
```

**Solución:**
Ver `agent_optimized.py` - líneas 259-271

---

## ⚠️ **PROBLEMAS DE OPTIMIZACIÓN**

### 1. **Ventana de Contexto Ineficiente**

**Estimación de tokens en tu versión actual:**
```
Prompt base (DynamicPromptBuilder):    ~2,500 tokens
Datos embebidos (4000 líneas):         ~10,000 tokens
Pure context completo:                 ~1,500 tokens
Protocolo y desarrollador:             ~300 tokens
----------------------------------------
TOTAL PROMPT INICIAL:                  ~14,300 tokens ❌
```

**Estimación de tokens en versión optimizada:**
```
Prompt base (DynamicPromptBuilder):    ~2,500 tokens
Pure context RESUMEN:                  ~400 tokens
Protocolo y desarrollador:             ~300 tokens
----------------------------------------
TOTAL PROMPT INICIAL:                  ~3,200 tokens ✅
```

**Ahorro:** ~11,000 tokens (77% de reducción)

---

### 2. **Gestión Limitada del Historial de Conversación**

**Tu código actual (línea 4465-4474):**
```python
async def on_user_turn_completed(self, chat_ctx, new_message):
    chat_ctx = chat_ctx.copy()
    if len(chat_ctx.items) > 15:
        chat_ctx.items = chat_ctx.items[-15:]  # Solo mantiene últimos 15
    await self.update_chat_ctx(chat_ctx)
```

**Problema:**
- Solo mantiene 15 mensajes
- No hay estrategia de resumen
- Conversaciones largas pierden contexto importante

**Solución Mejorada:**
```python
async def on_user_turn_completed(self, chat_ctx, new_message):
    chat_ctx = chat_ctx.copy()
    
    if len(chat_ctx.items) > 20:
        # Mantener últimos 15 mensajes
        recent_items = chat_ctx.items[-15:]
        
        # TODO: Implementar resumen de mensajes antiguos
        # old_items = chat_ctx.items[:-15]
        # summary = await self._summarize_old_messages(old_items)
        # Agregar resumen al inicio
        
        chat_ctx.items = recent_items
    
    await self.update_chat_ctx(chat_ctx)
```

---

### 3. **Método `enrich_context_for_query` No se Usa**

**Problema:**
```python
# El método existe (línea 4336-4342) pero NO se invoca
# durante el flujo de conversación
def enrich_context_for_query(self, user_message: str) -> str:
    relevant_context = self.context_manager.get_relevant_context(...)
    return f"\n\n## Contexto Adicional Relevante\n{relevant_context}"
```

**Solución:**
Debes **inyectar este contexto dinámicamente** en las respuestas del agente cuando detectes keywords relevantes.

---

## ✅ **SOLUCIONES IMPLEMENTADAS EN `agent_optimized.py`**

### 1. **Eliminación de Datos Embebidos**
```python
# ✅ Solo se carga RESUMEN en el prompt inicial
def generate_pure_context_summary(self) -> str:
    """Solo estadísticas generales"""
    return f"""
    ### 📊 ESTADÍSTICAS GENERALES:
    - {total_units} unidades de investigación
    - {total_researchers} investigadores
    [...]
    """
```

### 2. **Carga Dinámica de Contexto**
```python
# ✅ Datos detallados se cargan SOLO cuando son relevantes
def get_detailed_pure_context_for_query(self, query: str) -> str:
    """Cargar contexto DETALLADO solo si la query lo requiere"""
    if 'investigación' in query or 'grupo' in query:
        # Cargar solo unidades relevantes (5-10)
        units = self.pure_loader.search_units(query)[:5]
        return format_units_context(units)
    return ""
```

### 3. **Enriquecimiento Contextual Mejorado**
```python
def enrich_context_for_query(self, user_message: str) -> str:
    relevant_context = self.context_manager.get_relevant_context(...)
    
    # ✅ Agregar contexto Pure específico si es relevante
    if any(keyword in user_message.lower() 
           for keyword in ['investigación', 'grupo', 'pure']):
        pure_context = self.get_detailed_pure_context_for_query(user_message)
        relevant_context = f"{relevant_context}\n\n{pure_context}"
    
    return relevant_context
```

---

## 📋 **RECOMENDACIONES DE IMPLEMENTACIÓN**

### Paso 1: Migrar Datos a JSON
```bash
# Crear archivo con todos los datos de investigación
backend/scraped_data/research_database.json
```

### Paso 2: Actualizar Loader
```python
class ResearchDataLoader:
    def __init__(self):
        self.data = self.load_from_json()
        self.create_indices()  # Índices para búsqueda rápida
    
    def search(self, query: str, max_results=5):
        # Búsqueda eficiente en datos indexados
        pass
```

### Paso 3: Inyectar Contexto Dinámicamente
```python
# En el flujo de conversación del agente
async def on_message_received(self, message: str):
    # 1. Analizar si necesita contexto adicional
    if self.requires_research_context(message):
        additional_context = self.get_detailed_context(message)
        # 2. Inyectar en el chat context
        enriched_message = f"{message}\n\n{additional_context}"
    
    # 3. Procesar con el LLM
    response = await self.generate_response(enriched_message)
```

---

## 🎯 **BENEFICIOS ESPERADOS**

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|---------|
| **Tokens iniciales** | ~14,300 | ~3,200 | **77% ↓** |
| **Tiempo de inicialización** | ~3-5 seg | ~0.5-1 seg | **80% ↓** |
| **Costo por sesión** | $0.15-0.20 | $0.03-0.05 | **75% ↓** |
| **Mantenibilidad** | Baja | Alta | ✅ |
| **Escalabilidad** | Limitada | Alta | ✅ |

---

## 🚀 **PRÓXIMOS PASOS**

### Inmediato (Alta Prioridad)
1. ✅ **Usar `agent_optimized.py`** como referencia
2. ✅ **Migrar datos a JSON** externo
3. ✅ **Implementar carga bajo demanda** de contexto

### Corto Plazo
4. ⚠️ **Implementar resumen de conversaciones largas**
5. ⚠️ **Agregar caché** para búsquedas frecuentes
6. ⚠️ **Monitoreo de uso de tokens** en producción

### Mediano Plazo
7. 💡 **Vector database** para búsqueda semántica eficiente
8. 💡 **RAG (Retrieval Augmented Generation)** completo
9. 💡 **Fine-tuning** con datos específicos del Convergence Lab

---

## 📚 **RECURSOS ADICIONALES**

### Documentación LiveKit
- [Managing Context Windows](https://docs.livekit.io/agents/context-management)
- [Optimizing Token Usage](https://docs.livekit.io/agents/best-practices)

### OpenAI Best Practices
- [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Token Management](https://platform.openai.com/docs/guides/production-best-practices)

---

## 👨‍💻 **Contacto**

**Samuel Esteban Ramírez**  
Desarrollador Principal - Convergence Lab  
Universidad de La Sabana  
LinkedIn: [samuel-ramirez-developer](https://www.linkedin.com/in/samuel-ramirez-developer/)

---

**Fecha de Análisis:** 2025-11-11  
**Versión:** 1.0  
**Estado:** ✅ Completado
