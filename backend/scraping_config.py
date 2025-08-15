"""
Configuración para el sistema de web scraping de PURE Universidad de La Sabana
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ScrapingConfig:
    """Configuración para el scraper de PURE"""
    
    # URLs base
    BASE_URL: str = "https://pure.unisabana.edu.co"
    
    # Configuración de delays y timeouts (aumentar delays para evitar detección)
    REQUEST_DELAY: float = 3.0  # Delay base entre peticiones
    RANDOM_DELAY: bool = True  # Activar delays aleatorios
    MIN_DELAY: float = 2.0     # Delay mínimo
    MAX_DELAY: float = 5.0     # Delay máximo
    TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0  # Factor de backoff para reintentos
    
    # Configuración de Selenium (habilitar por defecto)
    USE_SELENIUM: bool = True  # Cambiar a True por defecto
    HEADLESS: bool = False  # Cambiar a False para debugging
    
    # Límites de scraping
    MAX_PAGES: int = 100  # Máximo número de páginas a procesar
    MAX_CONCURRENT_REQUESTS: int = 3  # Máximo número de peticiones concurrentes
    
    # Patrones de URL relevantes
    RELEVANT_URL_PATTERNS: List[str] = None
    
    # Selectores CSS para diferentes tipos de contenido
    SELECTORS: Dict[str, Dict[str, str]] = None
    
    # Directorios de salida
    OUTPUT_DIR: str = "scraped_data"
    CONTEXT_FILE: str = "pure_context.json"
    
    def __post_init__(self):
        """Inicializar valores por defecto después de la creación"""
        if self.RELEVANT_URL_PATTERNS is None:
            self.RELEVANT_URL_PATTERNS = [
                '/persons/', '/person/',
                '/research-outputs/', '/publications/', '/publication/',
                '/projects/', '/project/',
                '/organisations/', '/organization/',
                '/activities/', '/activity/',
                '/datasets/', '/dataset/',
                '/patents/', '/patent/'
            ]
        
        if self.SELECTORS is None:
            self.SELECTORS = {
                'researcher': {
                    'name': 'h1, .name, .full-name, .researcher-name, [class*="name"]',
                    'email': 'a[href^="mailto:"]',
                    'orcid': 'a[href*="orcid.org"]',
                    'position': '.position, .title, .job-title, .academic-position',
                    'affiliation': '.affiliation, .department, .organization, .faculty',
                    'research_areas': '.research-area, .keyword, .topic, .subject',
                    'biography': '.biography, .bio, .description, .about',
                    'publications': 'a[href*="/research-outputs/"], a[href*="/publications/"]'
                },
                'publication': {
                    'title': 'h1, .title, .publication-title',
                    'authors': '.author, .authors, .contributor',
                    'journal': '.journal, .source, .publication-source',
                    'abstract': '.abstract, .summary, .description',
                    'publication_type': '.publication-type, .type, .category',
                    'doi': 'a[href*="doi.org"]'
                },
                'project': {
                    'title': 'h1, .title, .project-title',
                    'principal_investigator': '.principal-investigator, .pi, .leader',
                    'funding': '.funding, .sponsor, .grant',
                    'description': '.description, .abstract, .summary',
                    'participants': '.participant, .member, .researcher',
                    'dates': '.date, .period, .duration'
                },
                'organization': {
                    'name': 'h1, .name, .organization-name',
                    'description': '.description, .about, .overview',
                    'contact': '.contact, .email, .phone',
                    'members': 'a[href*="/persons/"], a[href*="/person/"]'
                }
            }

# Configuración por defecto
DEFAULT_CONFIG = ScrapingConfig()

# Mejorar headers para evitar detección de bot - Usar headers más realistas
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Cache-Control': 'max-age=0',
    'DNT': '1'
}

# Headers adicionales para rotación
ADDITIONAL_HEADERS_POOL = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
    }
]

# Mejorar configuración de Selenium para evitar detección
SELENIUM_OPTIONS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--disable-extensions',
    '--disable-blink-features=AutomationControlled',
    '--disable-web-security',
    '--allow-running-insecure-content',
    '--disable-features=VizDisplayCompositor',
    '--disable-automation',
    '--disable-infobars',
    '--disable-plugins',
    '--disable-save-password-bubble',
    '--disable-translate',
    '--disable-default-apps',
    '--no-first-run',
    '--no-default-browser-check',
    '--ignore-certificate-errors',
    '--ignore-ssl-errors',
    '--ignore-certificate-errors-spki-list',
    '--disable-logging',
    '--disable-extensions-file-access-check',
    '--disable-plugins-discovery',
    '--disable-password-generation',
    '--disable-background-networking'
]

# Lista de proxies para rotación (opcional - agregar proxies válidos si los tienes)
PROXY_POOL = [
    # Agregar proxies válidos aquí si los tienes
    # 'http://proxy1:port',
    # 'http://proxy2:port',
]

def get_config() -> ScrapingConfig:
    """Obtener configuración con posibles overrides desde variables de entorno"""
    config = ScrapingConfig()
    
    # Override desde variables de entorno si existen
    if os.getenv('PURE_BASE_URL'):
        config.BASE_URL = os.getenv('PURE_BASE_URL')
    
    if os.getenv('SCRAPING_DELAY'):
        config.REQUEST_DELAY = float(os.getenv('SCRAPING_DELAY'))
    
    if os.getenv('SCRAPING_MAX_PAGES'):
        config.MAX_PAGES = int(os.getenv('SCRAPING_MAX_PAGES'))
    
    if os.getenv('USE_SELENIUM'):
        config.USE_SELENIUM = os.getenv('USE_SELENIUM').lower() == 'true'
    
    if os.getenv('SCRAPING_OUTPUT_DIR'):
        config.OUTPUT_DIR = os.getenv('SCRAPING_OUTPUT_DIR')
    
    return config
