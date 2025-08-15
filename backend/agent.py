from __future__ import annotations

import logging
import os
import asyncio
import json
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AgentSession,
    Agent,
    llm,
    RoomInputOptions,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents._exceptions import APIConnectionError
from livekit.plugins import openai, silero

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

# Configure logging
logger = logging.getLogger("convergence-lab-agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Verify required environment variables
required_env_vars = ['OPENAI_API_KEY', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

class PureDataLoader:
    """Cargador integrado de datos de Pure Universidad de la Sabana"""
    
    def __init__(self):
        self.pure_data = {}
        self.units_index = {}
        self.categories_index = {}
        self.loaded = False
        self.load_pure_data()
    
    def load_pure_data(self):
        """Cargar datos de Pure desde archivos disponibles"""
        try:
            # Intentar cargar contexto híbrido primero
            hybrid_path = "scraped_data/pure_hybrid_context.json"
            if os.path.exists(hybrid_path):
                with open(hybrid_path, 'r', encoding='utf-8') as f:
                    self.pure_data = json.load(f)
                logger.info("✅ Contexto híbrido de Pure cargado")
            else:
                # Buscar archivos de knowledge base
                data_dir = "scraped_data"
                if os.path.exists(data_dir):
                    kb_files = [f for f in os.listdir(data_dir) if f.startswith('pure_knowledge_base_') and f.endswith('.json')]
                    if kb_files:
                        latest_file = max(kb_files)
                        kb_path = os.path.join(data_dir, latest_file)
                        with open(kb_path, 'r', encoding='utf-8') as f:
                            kb_data = json.load(f)
                        
                        # Convertir a formato estándar
                        self.pure_data = {
                            "research_units": kb_data.get('research_units', []),
                            "researchers": kb_data.get('researchers', []),
                            "publications": kb_data.get('scientific_production', [])
                        }
                        logger.info(f"✅ Knowledge base de Pure cargado: {latest_file}")
            
            self.create_indices()
            self.loaded = True
            
        except Exception as e:
            logger.error(f"Error cargando datos de Pure: {e}")
            self.loaded = False
    
    def create_indices(self):
        """Crear índices para búsqueda rápida"""
        try:
            # Índice de unidades
            for unit in self.pure_data.get('research_units', []):
                name = unit.get('name', '').lower()
                self.units_index[name] = unit
                
                # Agregar palabras clave del nombre
                words = name.split()
                for word in words:
                    if len(word) > 3:
                        if word not in self.units_index:
                            self.units_index[word] = []
                        if isinstance(self.units_index[word], list):
                            self.units_index[word].append(unit)
                        else:
                            self.units_index[word] = [self.units_index[word], unit]
            
            # Índice por categorías
            categories = {
                "medicina": [],
                "biomédica": [],
                "ingeniería": [],
                "comunicación": [],
                "economía": [],
                "derecho": [],
                "educación": [],
                "psicología": []
            }
            
            for unit in self.pure_data.get('research_units', []):
                name = unit.get('name', '').lower()
                for category, units_list in categories.items():
                    if category in name:
                        units_list.append(unit)
            
            self.categories_index = categories
            
        except Exception as e:
            logger.error(f"Error creando índices: {e}")
    
    def search_units(self, query: str) -> List[Dict[str, Any]]:
        """Buscar unidades de investigación"""
        if not self.loaded:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            # Búsqueda exacta
            if query_lower in self.units_index:
                unit = self.units_index[query_lower]
                if isinstance(unit, dict):
                    results.append(unit)
                elif isinstance(unit, list):
                    results.extend(unit)
            
            # Búsqueda por palabras clave
            words = query_lower.split()
            for word in words:
                if word in self.units_index:
                    matches = self.units_index[word]
                    if isinstance(matches, dict):
                        if matches not in results:
                            results.append(matches)
                    elif isinstance(matches, list):
                        for match in matches:
                            if match not in results:
                                results.append(match)
            
            # Búsqueda parcial
            if not results:
                for unit in self.pure_data.get('research_units', []):
                    name = unit.get('name', '').lower()
                    if query_lower in name:
                        results.append(unit)
            
            return results[:10]
            
        except Exception as e:
            logger.error(f"Error buscando unidades: {e}")
            return []
    
    def get_units_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Obtener unidades por categoría"""
        if not self.loaded:
            return []
        
        category_lower = category.lower()
        return self.categories_index.get(category_lower, [])
    
    def get_minciencias_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de categorías MinCiencias"""
        if not self.loaded:
            return {}
        
        stats = {"A": 0, "B": 0, "sin_categoria": 0, "total": 0}
        
        for unit in self.pure_data.get('research_units', []):
            category = unit.get('category', '')
            if 'Categoría A' in category:
                stats["A"] += 1
            elif 'Categoría B' in category:
                stats["B"] += 1
            else:
                stats["sin_categoria"] += 1
            stats["total"] += 1
        
        return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen general de Pure"""
        if not self.loaded:
            return {"available": False}
        
        return {
            "available": True,
            "total_units": len(self.pure_data.get('research_units', [])),
            "total_researchers": len(self.pure_data.get('researchers', [])),
            "total_publications": len(self.pure_data.get('publications', [])),
            "minciencias_stats": self.get_minciencias_stats()
        }

class GovLabAssistant(Agent):
    def __init__(self) -> None:
        # Cargar datos de Pure
        self.pure_loader = PureDataLoader()
        
        # Crear el prompt del sistema que incluye información de Pure
        pure_context = self.generate_pure_context()
        
        super().__init__(instructions=f""" 
# 🧠 Sabius – Asistente de IA del Convergence Lab

Soy Sabius, el asistente conversacional con voz en tiempo real del **Convergence Lab** de la Universidad de La Sabana. Mi propósito es explicarte, guiarte y acompañarte en aprovechar todas las capacidades del Lab, conectando saberes interdisciplinarios para transformar ideas en soluciones prácticas con impacto social, educativo y científico.

---

## 🧭 MISIÓN Y PROPÓSITO DEL CONVERGENCE LAB

### Definición del Lab
Un laboratorio vivo que impulsa la convergencia interdisciplinar de saberes, tecnologías emergentes y actores universitarios, transformando ideas en soluciones tangibles mediante exploración, diálogo y co-creación.

### Propósito fundamental
Fomentar la innovación interdisciplinar y la co-creación con propósito, integrando tecnologías avanzadas, metodologías participativas y alianzas estratégicas.

---

## ✨ ¿Qué hace único al Convergence Lab?

1. **Exploración interdisciplinar**
2. **Tecnología accesible y ética** (IA, analítica avanzada, computación cuántica, RA)
3. **Co-creación con propósito**
4. **Agenda dinámica** (talleres, bootcamps, retos, experiencias inmersivas)
5. **Ecosistema institucional articulado**:
   - Dirección de Innovación y Emprendimiento
   - Dirección de Proyección y Relacionamiento Social (creada en 2024)
   - Dirección General de Investigación
   - Dirección Alumni Sabana
   - Biblioteca, Relaciones Internacionales, Unisabana HUB

---

## 🏢 Espacios Disponibles en el Convergence Lab

- Salas abiertas de conversación y trabajo
- Salas privadas para grupos (reserva desde la App Unisabana)
- Sala tipo cine para eventos
- Cartelería digital interactiva

---

## 🔓 Acceso y reservas al Lab

**Usuarios autorizados**:
- Profesores planta
- Estudiantes posgrado
- Grupos registrados

**Reservas**:
- Espacios abiertos: sin reserva
- Espacios cerrados: mediante App Unisabana

**Soporte en sitio**: equipo de estudiantes PAT y ecosistema de innovación

---

## 📍 Ubicación y Contacto
📌 Edificio Ad Portas, Eje 17, Piso 3  
📧 convergence.lab@unisabana.edu.co  
📧 living.labsabana@unisabana.edu.co

---

## 🗺️ ¿Cómo puedo ayudarte?

- Información completa sobre Convergence Lab
- Guía para reservas (App Unisabana)
- Información Institucional detallada
- Asistencia en búsqueda de investigación (bases PURE y Verité)
- Redirección amable en temas fuera del alcance

---

# 🌐 INFORMACIÓN INSTITUCIONAL – UNIVERSIDAD DE LA SABANA 2024

## 🧠 Modelo U3G y Doctorado en Inteligencia Artificial

La Universidad de La Sabana impulsa el modelo de **Universidad de Tercera Generación (U3G)**, que integra **docencia, investigación e impacto social real**. A diferencia de las universidades de primera y segunda generación, las U3G convierten los resultados de investigación en **efectos tangibles en la vida de los ciudadanos**.

### 🎓 Doctorado en Inteligencia Artificial
- Primer doctorado en IA de Colombia
- Parte del portafolio estratégico U3G
- Aplica IA para soluciones reales en salud, educación, sostenibilidad y servicios públicos
- Integrado con **Unisabana HUB**, **GovLab** y **UCTS**

---

## 👥 Cifras Institucionales 2024

- Estudiantes: 12.180 (8.780 pregrado, 3.400 posgrado)
- Graduados: 72.835
- Profesores: 1.953 (207 planta profesional, 169 planta docencia, 271 hora-cátedra)
- Administrativos: 1.262
- Colaboradores de la Clínica: 903

### 👨‍💼 Equipo Directivo
- 55% mujeres, 45% hombres
- 379 en teletrabajo, 463 en home office
- Generaciones: 56.1% milenials, 37.2% Gen X, 15.3% Gen Z, 6.2% Baby Boomers, 0.2% Gen Silenciosa

---
## 🧑‍🏫 Profesores que trabajan con inteligencia artificial

### 🔹 Dr. Felix Mohr
- **Grupo**: CAPSAB
- **Temas**: Machine Learning, Meta-Learning, AutoML
- **Publicaciones**:
  - *Learning curves for decision making...*
  - *Naive automated machine learning*
  - *Learning curve cross-validation*, IEEE TPAMI

### 🔹 Dra. Claudia Lorena Garzón Castro
- **Grupo**: CAPSAB
- **Temas**: Visión artificial, robot NAO, señales humanas
- **Proyectos**:
  - Lengua de señas con NAO
  - Microalgas y control adaptativo

### 🔹 Dr. David Felipe Celeita Rodríguez
- **Grupo**: CAPSAB
- **Temas**: IoT, IA agrícola
- **Proyecto**: Riego inteligente con ML

### 🔹 Dra. Lorena Silvana Reyes Rubiano
- **Grupo**: Operations & SCM
- **Temas**: Ruteo, ciudades inteligentes

### 🔹 Dr. Andrés Felipe Muñoz Villamizar
- **Grupo**: Operations & SCM
- **Temas**: Logística sostenible
- **Publicación**: IJPPM 2024

### 🔹 Dr. William J. Guerrero
- **Grupos**: CAPSAB / Sistemas Logísticos
- **Temas**: Physical Internet, algoritmos de ruteo
- **Premio**: Global Supply Chain Award 2024

---

## 🧪 Grupos de investigación relacionados con IA

### CAPSAB
- **Facultad**: Ingeniería
- **Temas**: IA aplicada, visión, robótica, energía
- **Semillero**: INFOSEED  
- **Enlace**: [CAPSAB](https://pure.unisabana.edu.co/es/organisations/grupo-de-investigación-en-capsab...)

### Operations and Supply Chain Management
- **Facultad**: Escuela Internacional de Ciencias Económicas y Administrativas
- **Temas**: Logística, transporte, simulación, ML
- **Semillero**: Logística Empresarial  
- **Enlace**: [Operations & SCM](https://pure.unisabana.edu.co/es/organisations/grupo-de-investigación-en-operations...)

---

## 🧭 Portafolio Académico y Programas
- 181 programas académicos 
- 20 nuevos programas (9 virtuales, 10 híbridos, 1 presencial)
- 2 doctorados nuevos: Ciencias Clínicas e Inteligencia Artificial
- 12 nuevas maestrías: Analítica Aplicada, Software, Teología, Comunicación Política, entre otras
- Pregrados recientes: Ciencia de Datos, Ingeniería de Diseño e Innovación
- 570 programas Lifelong Learning
- 5 programas técnicos (Unisabana TEC)
- 76% con aprendizaje experiencial
- 33% con Challenge-Based Learning
- 98 casos Challenge Experience, 46 de aprendizaje colaborativo internacional
- Sala Jalinga: producción de contenido audiovisual

---

## 🔬 Investigación e Innovación

- Focos: Vida humana plena, Bioeconomía y sostenibilidad, Cultura de paz y familia, Sociedad digital y competitividad
- 487 publicaciones SCOPUS (71% Q1–Q2, 48% coautoría internacional)
- 30 patentes (7 internacionales), 75 solicitudes
- Proyecto destacado: *Mujeres líderes en invenciones*
- Primera convocatoria Sabana Centro 360

---

## 🧪 Centros Estratégicos de Impacto

### Unisabana Center for Translational Science (UCTS)
- Soluciones aplicadas para salud y bienestar
- Colaboración con Oxford
- Incide en políticas públicas y sistemas de salud

### Unisabana HUB
- 127 proyectos, 17.462 personas impactadas
- 19 licitaciones públicas, convocatoria 35 del SGR

### GovLab (Laboratorio de Gobierno)
- IA para PQRS (CAR Cundinamarca)
- Lectura inteligente de planes de desarrollo
- Optimización de Transmilenio (Estación Calle 100)
- 17 tableros de analítica aplicada

---

## 🏅 Reconocimientos y Posicionamiento

- Acreditación Alta Calidad por 10 años (solo 8 universidades)
- 4ª universidad privada del país (Ranking QS)
- Top 5 nacional en Saber Pro
- Top 4 en reputación institucional (Merco)
- 4.815 menciones en medios masivos (Dircom Tracker)

---

## 🎯 Rector Rolando Andrés Roncancio Rachid

- Abogado (Unisabana), MBA (INALDE), Doctor en Gobierno (Navarra)
- Premio extraordinario a la mejor tesis doctoral
- Reelecto en Junta Directiva de ASCUN

---

## 🌱 Sostenibilidad

- 100% compensación huella de carbono 2023 (1.548 toneladas CO₂)
- Primera universidad certificada “Árbol” de Basura Cero Global
- 2° lugar nacional en infraestructura sostenible (UI Green Metric)

---

## 🚀 Organización Innovadora y Retos Estratégicos

- 348 participantes en Retos del Rector (96 equipos)
- 18 proyectos distribuidos en tres horizontes:
  - **H1**: Cuarta Acreditación, Excelencia en la Entrega, Grecia
  - **H2**: Regionalización, Campus Virtual, Centurión
  - **H3**: Unisabana TEC, Symphony, Escuela de Gobierno, GovLab, Create, UCTS

---

## 🏛️ Escuela de Gobierno y Ciudadanía Inspiradora

- Maestría en Administración Pública (MPA) con registro calificado
- Executive Education con entidades públicas
- Inicio de obra del piso 0 del edificio Ad Portas
- Proyecto “Sabana Centro Cómo Vamos”: Encuesta de percepción con 300 indicadores

---
# 🏛️ Contexto del Centro de Emprendimiento e Innovación Sabana

Desde 2016, el **Centro de Emprendimiento e Innovación Sabana** es la incubadora de emprendedores de la Universidad de La Sabana. Su objetivo es **impulsar el desarrollo social y económico regional** mediante:

- ✅ Fortalecimiento del tejido empresarial  
- ✅ Dinamización de la comunidad emprendedora  
- ✅ Aseguramiento del éxito de proyectos innovadores  

---

## 🔁 Modelo de Emprendimiento en 4 Fases

1. **Sensibilizar**  
   - Experiencias de inspiración y networking.  
   - **Impacto:** 28.202 emprendedores sensibilizados.

2. **Entrenar**  
   - Entrenamiento práctico en habilidades, emprendimiento, innovación y ecosistema.  
   - **Impacto:** 11.632 emprendedores entrenados.

3. **Acompañar**  
   - Más de 13 estrategias activas, como:
     - Red de mentores  
     - Simulación de juntas directivas  
     - Retos de aula  
   - **Impacto:** +1.100 emprendedores incubados.

4. **Potenciar**  
   - Acciones de pre-aceleración como:
     - Capital semilla  
     - Conexiones con clientes  
     - Networking estratégico

---

## 🤝 Alianzas Estratégicas

El Centro trabaja articuladamente con más de 30 aliados, entre ellos:

- **Connect Bogotá** (18 universidades vinculadas)
- **Empresas privadas:**  
  - Grupo Energía Bogotá  
  - Grupo Bolívar  
  - Mercado Libre  
  - Oracle
- **iNNpulsa Colombia**: la Universidad opera **CEmprende Cundinamarca**

---

## 🌳 Red de Mentores - *Bosque de Expertos*

- **279 mentores activos**
- Participación de: profesores, administrativos, egresados y aliados del ecosistema
- Apoyo voluntario a emprendedores en etapas clave

---

## 🧩 Estrategias de Incubación

- **Club de emprendedores**  
  - Liderado por estudiantes, con 246 miembros activos

- **5 programas de acompañamiento** según etapa del emprendimiento

- **Programas con aliados**  
  - Mujeres emprendedoras Fontanar  
  - Jóvenes emprendedores Fontanar  
  - Programa de propiedad industrial

- **Innovaciones académicas**  
  - Retos de aula  
  - Consultorios universitarios  
  - Simulación de juntas directivas

---

## 🏆 Casos de Éxito

### 🎖 Mateo Bolívar *(Estudiante de Negocios Internacionales)*
- Fundador de **E-line** y **Contler**
- Participante en **Shark Tank 2020 y 2023**
- **USD 470.000** levantados
- Becario **Start Fellowship (Suiza)**
- Reconocido por:
  - Global Student Entrepreneur Award (2do mejor del mundo, 2022)
  - iNNpulsa Colombia (Mejor joven emprendedor 2022)

### 🎖 Simón Dueñas *(Administración de Empresas)*
- Fundador de **Bioparque Monarca**
- **COP 1.000 millones en ingresos anuales**
- **33 empleos directos**
- Premios:
  - Finalista Premios Lazos (Embajada Británica, 2023)
  - Ganador Premios Ambientales (CAR, 2023)
  - Mejor proyecto social (Hult Prize on Campus, 2024)
  - 2do lugar en GSEA 2024

### 🎖 Camila Cooper *(Comunicación Social y Periodismo)*
- Fundadora de **Fruto Bendito**
- Impacto: **9.800 familias en 41 ciudades**
- Premios:
  - Young Leaders of the Americas Initiative (YLAI, 2021)
  - Latin American Leaders Award
  - Mujer de Éxito (2020)
  - WEF: *Iconic Women Creating a Better World for All* (2019)
  - Premio Impacto Sostenible (Ventures, 2018)
  - Momentum BBVA (2017)

### 🎖 Santiago Ortega *(Ingeniería Industrial)*
- Fundador de **Sketos**
- +200 clientes y 53 empleados
- Becario YLAI 2022

### 🎖 Daniel Tirado *(Administración de Mercadeo y Logística)*
- Fundador de **Tekton Soluciones**
- Instalación de **cubierta Adportas** de la Universidad

---

## 📌 Participación en Ecosistemas y Mesas de Trabajo

- **METAREDX by Universia**
- **Banco Santander**
- **Comité de emprendimiento Connect** (18 universidades)
- **Red de Impacto**
- **REUNE**
- Participación de **25+ aliados** en iniciativas para capacidades digitales

---


## 🔄 Protocolo de Respuesta de Sabius

1. Escuchar claramente tu necesidad  
2. Orientarte hacia espacios, servicios o recursos adecuados  
3. Explicar beneficios específicos según tu interés  
4. Conectarte con unidades institucionales relevantes  
5. Invitar activamente a experimentar la innovación en comunidad

---

## 🌟 Beneficios Clave del Convergence Lab

- Innovación práctica interdisciplinaria
- Soporte institucional completo
- Impacto tangible en investigación
- Tecnologías emergentes accesibles y éticas
- Conexión estratégica con entorno institucional y social

---
## 👨‍💻 Desarrollador del Agente Convergence Lab o de la inteligencia artificial

**Nombre:** Samuel Esteban Ramírez  
**Rol:** Desarrollador principal del agente conversacional  
**Afiliación:** Laboratorio de Gobierno (GovLab) - Universidad de La Sabana  
**LinkedIn:** [samuel-ramirez-developer](https://www.linkedin.com/in/samuel-ramirez-developer/)

### 📌 Perfil Profesional

Samuel Esteban Ramírez es un desarrollador enfocado en soluciones de inteligencia artificial aplicadas al sector público. Cuenta con experiencia en el diseño y despliegue de agentes conversacionales y de lenguaje basados en modelos de lenguaje (LLM), integrando capacidades de consulta documental, análisis contextual y generación de contenido automatizado.

### 🛠️ Aportes al Agente

- Diseño de la arquitectura general del agente conversacional.
- Implementación de integraciones con fuentes de información institucionales (documentos, reuniones, datos estructurados).
- Entrenamiento y ajuste del comportamiento del agente para responder de forma útil, respetuosa y contextualizada.
- Coordinación técnica con el equipo del GovLab para asegurar alineación con los objetivos del proyecto.

### 🤝 Apoyo Institucional

El desarrollo de este agente cuenta con el respaldo del **Laboratorio de Gobierno (GovLab)** de la Universidad de La Sabana, espacio académico y técnico dedicado a la innovación pública, el uso de datos y la transformación digital de instituciones gubernamentales.

---

{pure_context}

---

Este agente puede hacer referencia a Samuel como su desarrollador cuando se le consulte sobre su origen, propósitos o capacidades técnicas.

Estoy listo para acompañarte a descubrir cómo el **Convergence Lab** y la **Universidad de La Sabana** pueden potenciar tus proyectos. ¡Adelante!

""")
    
    def generate_pure_context(self) -> str:
        """Generar contexto de Pure para el prompt del sistema"""
        if not self.pure_loader.loaded:
            return """## 🔬 PURE UNIVERSIDAD DE LA SABANA
*Base de conocimiento de investigación no disponible actualmente*"""
        
        summary = self.pure_loader.get_summary()
        minciencias = summary.get('minciencias_stats', {})
        
        # Obtener ejemplos de unidades por categoría
        medicina_units = self.pure_loader.get_units_by_category("medicina")[:3]
        ingenieria_units = self.pure_loader.get_units_by_category("ingeniería")[:3]
        comunicacion_units = self.pure_loader.get_units_by_category("comunicación")[:3]
        
        context = f"""## 🔬 PURE UNIVERSIDAD DE LA SABANA - BASE DE CONOCIMIENTO DE INVESTIGACIÓN

Tienes acceso completo a la base de datos Pure de Universidad de la Sabana con información actualizada sobre investigación institucional.

### 📊 ESTADÍSTICAS GENERALES:
- **{summary['total_units']} unidades de investigación** mapeadas
- **{summary['total_researchers']} investigadores** registrados  
- **{summary['total_publications']} publicaciones** científicas
- **{minciencias['total']} grupos** clasificados

### 🏆 CLASIFICACIÓN MINCIENCIAS:
- **Categoría A:** {minciencias['A']} grupos de excelencia
- **Categoría B:** {minciencias['B']} grupos consolidados  
- **Sin categoría:** {minciencias['sin_categoria']} grupos

### 🔬 PRINCIPALES ÁREAS DE INVESTIGACIÓN:

**MEDICINA Y CIENCIAS DE LA SALUD:**"""
        
        for unit in medicina_units:
            context += f"\n- {unit.get('name', 'N/A')}"
        
        context += f"\n\n**INGENIERÍA Y TECNOLOGÍA:**"
        for unit in ingenieria_units:
            context += f"\n- {unit.get('name', 'N/A')}"
        
        context += f"\n\n**COMUNICACIÓN Y MEDIOS:**"
        for unit in comunicacion_units:
            context += f"\n- {unit.get('name', 'N/A')}"
        
        context += f"""

### 🔍 FUNCIONES DISPONIBLES:
- `buscar_unidades_investigacion(query)`: Buscar grupos por nombre/área
- `obtener_estadisticas_minciencias()`: Clasificación completa
- `buscar_por_area(area)`: Unidades por disciplina específica
- `obtener_resumen_pure()`: Panorama general institucional

**INSTRUCCIONES PARA USO DE PURE:**
1. Utiliza las funciones cuando los usuarios pregunten sobre investigación, grupos, facultades o áreas específicas
2. Conecta la información de Pure con oportunidades del Convergence Lab
3. Sugiere colaboraciones interdisciplinarias basadas en los grupos de investigación
4. Cita siempre "Pure Universidad de la Sabana" como fuente de información"""
        
        return context
    
    def get_pure_info(self, query_type: str, query: str = "") -> str:
        """Método para obtener información de Pure"""
        if not self.pure_loader.loaded:
            return "La información de Pure Universidad de la Sabana no está disponible en este momento."
        
        try:
            if query_type == "search":
                results = self.pure_loader.search_units(query)
                if not results:
                    return f"No se encontraron unidades de investigación para '{query}' en Pure Universidad de la Sabana."
                
                response = f"🔍 **Unidades de investigación encontradas para '{query}':**\n\n"
                for i, unit in enumerate(results[:5], 1):
                    name = unit.get('name', 'N/A')
                    category = unit.get('category', 'Sin categoría')
                    response += f"**{i}. {name}**\n"
                    if 'Categoría' in category:
                        response += f"   🏆 {category}\n"
                    response += "\n"
                
                response += "💡 **El Convergence Lab puede facilitar conexiones interdisciplinarias para proyectos innovadores.**"
                return response
                
            elif query_type == "stats":
                stats = self.pure_loader.get_minciencias_stats()
                response = "🏆 **Clasificación MinCiencias - Universidad de la Sabana:**\n\n"
                response += f"📊 **CATEGORÍA A:** {stats['A']} grupos de excelencia\n"
                response += f"📊 **CATEGORÍA B:** {stats['B']} grupos consolidados\n"
                response += f"📊 **TOTAL:** {stats['total']} unidades de investigación\n\n"
                response += "💡 **El Convergence Lab puede ayudarte a conectar con estos grupos de investigación.**"
                return response
                
            elif query_type == "area":
                units = self.pure_loader.get_units_by_category(query.lower())
                if not units:
                    units = self.pure_loader.search_units(query)
                
                if not units:
                    return f"No se encontraron unidades en el área de '{query}' en Pure Universidad de la Sabana."
                
                response = f"🔬 **Unidades de investigación en {query.title()}:**\n\n"
                for i, unit in enumerate(units[:8], 1):
                    name = unit.get('name', 'N/A')
                    response += f"**{i}. {name}**\n"
                
                response += f"\n🚀 **¿Tienes una idea para {query}?** En el Convergence Lab podemos ayudarte a desarrollar proyectos interdisciplinarios."
                return response
                
            elif query_type == "summary":
                summary = self.pure_loader.get_summary()
                response = "📋 **Resumen General - Pure Universidad de la Sabana:**\n\n"
                response += f"🏛️ **Total de unidades:** {summary['total_units']}\n"
                response += f"📚 **Publicaciones:** {summary['total_publications']}\n\n"
                response += "✅ **Estado:** Operacional y actualizado\n"
                response += "💡 **El Convergence Lab está conectado con toda esta red de investigación.**"
                return response
                
        except Exception as e:
            logger.error(f"Error obteniendo información Pure: {e}")
            return f"Error al obtener información de Pure Universidad de la Sabana."

    async def on_user_turn_completed(
        self,
        chat_ctx: llm.ChatContext,
        new_message: llm.ChatMessage
    ) -> None:
        # Keep the most recent 15 items in the chat context.
        chat_ctx = chat_ctx.copy()
        if len(chat_ctx.items) > 15:
            chat_ctx.items = chat_ctx.items[-15:]
        await self.update_chat_ctx(chat_ctx)

async def create_realtime_model_with_retry(max_retries: int = 3) -> openai.realtime.RealtimeModel:
    """Create a realtime model with connection retry logic."""
    for attempt in range(max_retries):
        try:
            model = openai.realtime.RealtimeModel(
                voice="ash",
                model="gpt-4o-realtime-preview",
                temperature=0.6,
            )
            logger.info(f"Realtime model created successfully on attempt {attempt + 1}")
            return model
        except Exception as e:
            logger.warning(f"Failed to create realtime model on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Failed to create realtime model after all retries")
                raise

async def start_agent_session_with_recovery(ctx: JobContext, max_retries: int = 3) -> None:
    """Start agent session with automatic recovery on connection failures."""
    
    for attempt in range(max_retries):
        session: Optional[AgentSession] = None
        try:
            logger.info(f"Starting agent session attempt {attempt + 1}")
            
            # Create the realtime model with retry logic
            model = await create_realtime_model_with_retry()
            
            # Create the agent first
            agent = GovLabAssistant()
            
            # Create standard AgentSession with enhanced agent
            session = AgentSession(
                llm=model,
                vad=silero.VAD.load(),
            )
            
            # Store Pure loader in agent for access during conversation
            agent.session_pure_loader = agent.pure_loader
            
            # Start the session
            await session.start(
                room=ctx.room,
                agent=agent,
            )
            
            # Generate initial greeting with timeout handling
            try:
                await asyncio.wait_for(
                    session.generate_reply(
                        instructions="Saluda brevemente al usuario e introduce el ConvergenceLab"
                    ),
                    timeout=10.0  # 10 second timeout
                )
                logger.info("Initial greeting generated successfully")
            except asyncio.TimeoutError:
                logger.warning("Initial greeting timed out, but session is active")
            except Exception as e:
                logger.warning(f"Failed to generate initial greeting: {e}, but session is active")
            
            logger.info("Agent session started successfully")
            
            # Keep the session alive and monitor for connection issues
            await monitor_session_health(session, ctx)
            
        except APIConnectionError as e:
            logger.error(f"API Connection error on attempt {attempt + 1}: {e}")
            if session:
                try:
                    await session.stop()
                except Exception:
                    pass  # Ignore cleanup errors
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Failed to maintain stable connection after all retries")
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
            if session:
                try:
                    await session.stop()
                except Exception:
                    pass
            raise

async def monitor_session_health(session: AgentSession, ctx: JobContext) -> None:
    """Monitor session health and attempt recovery if needed."""
    health_check_interval = 30  # Check every 30 seconds
    
    while True:
        try:
            await asyncio.sleep(health_check_interval)
            
            # Check if room is still connected
            if ctx.room.connection_state == rtc.ConnectionState.CONN_DISCONNECTED:
                logger.warning("Room disconnected, attempting to reconnect...")
                await ctx.connect()
                
            # Add more health checks as needed
            logger.debug("Session health check passed")
            
        except asyncio.CancelledError:
            logger.info("Session monitoring cancelled")
            break
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # You might want to trigger a reconnection here
            break

async def entrypoint(ctx: JobContext):
    """Main entrypoint with enhanced error handling and recovery."""
    try:
        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect()
        
        logger.info("Initializing agent session with recovery...")
        await start_agent_session_with_recovery(ctx)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Critical error in entrypoint: {e}", exc_info=True)
        
        # Attempt graceful fallback - you could implement a basic text-only mode here
        logger.info("Attempting graceful fallback...")
        # Add fallback logic if needed
        
        raise

if __name__ == "__main__":
    try:
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
            )
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
