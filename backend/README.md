# 🤖 Sabius - Agente Conversacional ConvergenceLab

## 📋 Descripción General

Sabius es un asistente de IA impulsado por **OpenAI GPT-4o Realtime** que proporciona información actualizada sobre:
- **Profesores y facultad** de Enfermería (Universidad de La Sabana)
- **Publicaciones de investigación** (1980-2024)
- **Grupos de investigación** y sus productos académicos

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.local.example .env.local
# Editar .env.local con tus claves:
# - OPENAI_API_KEY
# - LIVEKIT_API_KEY
# - LIVEKIT_API_SECRET
# - LIVEKIT_URL

# 3. Ejecutar el agente
python agent.py dev
```

## 📊 Estructura de Datos

### 1. 📚 Faculty Professors JSON
**Archivo:** `knowledge_base/faculty_professors.json`

```json
{
  "metadata": {
    "total": 11,
    "description": "Profesores de Universidad de La Sabana en Enfermería",
    "department": "Facultad de Enfermería y Rehabilitación"
  },
  "professors": [
    {
      "nombre": "CARVAJAL CARRASCAL GLORIA",
      "titulo": "Doctora en Enfermería",
      "pais": "COLOMBIA",
      "pregrado": "Enfermera",
      "escalafon_puesto": "Asociado",
      "categoria_minciencias": "Asociado (I)"
    }
  ]
}
```

**Campos:**
- `nombre`: Nombre completo del profesor
- `titulo`: Máximo nivel académico alcanzado
- `pais`: País de origen o procedencia
- `pregrado`: Carrera base o licenciatura
- `escalafon_puesto`: Escalafón o posición en la universidad
- `categoria_minciencias`: Categoría según MinCiencias de Colombia

**Ejemplo de consulta esperada:**
- "¿Quiénes son los profesores de Enfermería?"
- "¿Cuál es el escalafón de Gloria Carvajal?"
- "Dime sobre los doctores en Enfermería"

### 2. 📰 Research Publications JSON
**Archivo:** `knowledge_base/research_publications.json`

```json
{
  "metadata": {
    "total": 1000,
    "units": 7,
    "groups": 19,
    "description": "Productos de investigación Universidad de La Sabana (1980-2024)"
  },
  "by_unit": {
    "Inalde Business School": [
      {
        "unidad": "Inalde Business School",
        "grupo": "Grupo de Investigación en Empresa, competitividad y Marketing",
        "titulo": "Shortage of perioperative supplies and drugs: Theory and practical implications",
        "revista": "Revista Colombiana de Anestesiología"
      }
    ]
  }
}
```

**Campos:**
- `unidad`: Unidad o facultad a la que pertenece la investigación
- `grupo`: Grupo de investigación responsable
- `titulo`: Título del artículo o publicación
- `revista`: Revista o medio donde fue publicado

**Estructura esperada en respuestas:**
Cuando preguntes sobre publicaciones, el agente responderá así:

"La **Inalde Business School** con el grupo de **Empresa, competitividad y Marketing** publicaron **'Shortage of perioperative supplies and drugs: Theory and practical implications'** en la revista **Revista Colombiana de Anestesiología**."

**Ejemplos de consultas esperadas:**
- "¿Qué publicaciones tiene Inalde Business School?"
- "¿Cuáles son los artículos del grupo de Empresa y Competitividad?"
- "Dime sobre investigaciones de la Clínica Universidad de La Sabana"

## 🧠 Cómo Funciona el Agente

### Arquitectura

```
┌─────────────────────────┐
│   Usuario (Voice/Text)   │
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  OpenAI GPT-4o Realtime (Temp: 0.4) │ ◄─── Temperatura BAJA para consistencia
└──────────────────────────┬───────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   Context Manager (DynamicPromptBuilder) │
│  - Carga faculty_professors.json     │
│  - Carga research_publications.json  │
│  - Identifica contexto relevante     │
└──────────────────────────┬───────────┘
             │
             ▼
┌──────────────────────────────────────┐
│    Respuesta Directa (Sin prefijos)  │
│    "La facultad X publicó..."|      │
│    "El profesor Y tiene..."|        │
└──────────────────────────────────────┘
```

### Parámetros Clave

- **Temperatura:** 0.4 (Baja para respuestas consistentes y precisas)
- **Contexto:** Obligatorio para cada respuesta
- **Modo respuesta:** Directo, sin aclaraciones sobre "basado en contexto"
- **Alucinaciones:** Bloqueadas - solo responde información disponible

## 📝 Patrones de Respuesta

### ✅ Respuestas Correctas

**Consulta:** "¿Quiénes son los profesores de Enfermería?"
**Respuesta:**
```
En la Facultad de Enfermería tenemos 11 profesores:
- CARVAJAL CARRASCAL GLORIA (Doctora, Asociado)
- FUENTES RAMÍREZ ALEJANDRA (Doctora, Asistente)
- GUEVARA LOZANO MARYORY (Magíster, Asistente)
...
```

**Consulta:** "¿Qué publicó el grupo de Empresa y Competitividad?"
**Respuesta:**
```
El grupo de Investigación en Empresa, competitividad y Marketing de Inalde Business School publicó:
- "Shortage of perioperative supplies and drugs..." en Revista Colombiana de Anestesiología
- "Comportamiento y experiencia de consumo..." en Revista de Investigaciones
...
```

### ❌ Patrones Prohibidos

El agente **NO** responderá así:
- ❌ "Basándome en el contexto, ..."
- ❌ "Según la información disponible, ..."
- ❌ "Suponiendo que, ..."
- ❌ "Probablemente, ..."
- ❌ "Posiblemente, ..."

## 🔧 Configuración Técnica

### Archivos Clave

- `agent.py` - Agente principal con PureDataLoader
- `context_manager.py` - Gestor de contextos dinámicos
- `agent_timeout_config.py` - Configuración de timeouts
- `knowledge_base/faculty_professors.json` - Base de datos de profesores
- `knowledge_base/research_publications.json` - Base de datos de publicaciones

### Flujo de Carga de Datos

1. **Inicialización:** El agente carga ambos JSONs al iniciarse
2. **Indexación:** Se crean índices de keywords para búsqueda rápida
3. **Consulta:** Cuando el usuario pregunta, se busca el contexto relevante
4. **Respuesta:** Se construye la respuesta dinámicamente

## 🎯 Próximos Pasos

1. ✅ Temperatura ajustada a 0.4
2. ✅ Instrucciones de respuesta directa activadas
3. ✅ JSONs de faculty y publicaciones optimizados
4. 🔄 Pruebas completas del agente
5. 📊 Dashboard de estadísticas

## 📧 Contacto

**Convergence Lab**
- 📍 Edificio Ad Portas, Eje 17, Piso 3
- 📧 convergence.lab@unisabana.edu.co
- 🏫 Universidad de La Sabana
