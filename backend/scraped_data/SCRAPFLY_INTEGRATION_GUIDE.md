
# 🚀 GUÍA DE INTEGRACIÓN CON SCRAPFLY

## 1. Registro y Configuración

### Paso 1: Crear cuenta en ScrapFly
- Visitar: https://scrapfly.io/
- Registrarse con email
- Verificar cuenta

### Paso 2: Obtener API Key
- Dashboard → API Keys
- Crear nueva API key
- Copiar la clave generada

### Paso 3: Configurar en el scraper
```python
config = ScrapFlyConfig(
    api_key="TU_API_KEY_AQUI",
    base_url="https://pure.unisabana.edu.co",
    country="CO",  # IP colombiana
    asp=True,      # Anti-scraping protection
    render_js=True # JavaScript rendering
)
```

## 2. Precios de ScrapFly

### Plan Starter ($29/mes)
- 10,000 requests incluidas
- Bypass automático de Cloudflare
- JavaScript rendering
- Proxies residenciales
- ✅ Perfecto para Pure Universidad de la Sabana

### Plan Pro ($99/mes)
- 50,000 requests
- Todas las funciones premium
- Soporte prioritario

## 3. Código de Implementación

```python
import requests

def scrape_with_scrapfly(url, api_key):
    api_url = "https://api.scrapfly.io/scrape"
    params = {
        'key': api_key,
        'url': url,
        'asp': 'true',          # Bypass anti-bot
        'render_js': 'true',    # Ejecutar JavaScript
        'country': 'CO',        # IP colombiana
        'session': 'pure_session'  # Mantener sesión
    }
    
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['result']['content']
    return None

# Uso
html = scrape_with_scrapfly(
    'https://pure.unisabana.edu.co/es/persons/', 
    'TU_API_KEY'
)
```

## 4. Ventajas de ScrapFly

✅ **99.9% Success Rate** - Bypass garantizado
✅ **Cloudflare Bypass** - Automático
✅ **JavaScript Rendering** - SPA support
✅ **Proxies Residenciales** - IPs reales
✅ **Rate Limiting** - Automático
✅ **No Mantenimiento** - Infraestructura gestionada

## 5. ROI (Retorno de Inversión)

### Comparación de Costos:
- **Desarrollo interno**: 40+ horas ingeniero ($2000+)
- **Proxies residenciales**: $150/mes mínimo
- **Mantenimiento**: 5 horas/mes ($500/mes)
- **ScrapFly**: $29/mes todo incluido

### Beneficios:
- ⏰ Implementación inmediata (1 hora)
- 🛡️ Bypass garantizado
- 📈 Escalabilidad automática
- 🔧 Sin mantenimiento

## 6. Implementación Recomendada

### Para Pure Universidad de la Sabana:
1. **Suscribirse** al plan Starter ($29/mes)
2. **Configurar** el scraper con la API key
3. **Ejecutar** scraping de todas las secciones
4. **Extraer** datos de investigadores y publicaciones
5. **Procesar** datos para el agente conversacional

### Tiempo estimado: 2-3 horas
### Costo mensual: $29
### Success rate esperado: 99%

## 7. Código de Prueba

Ejecutar este scraper con tu API key:
```bash
python scrapfly_professional_scraper.py
```

¡ScrapFly es la solución más efectiva para burlar las protecciones de Pure Universidad de la Sabana!
