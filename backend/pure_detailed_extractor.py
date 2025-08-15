#!/usr/bin/env python3
"""
PURE DETAILED EXTRACTOR - Extractor detallado para Pure Universidad de la Sabana
Extrae información completa de unidades, investigadores y producción científica
"""

import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re

try:
    from scrapfly import ScrapflyClient, ScrapeConfig, ScrapeApiResponse
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DetailedExtractionConfig:
    """Configuración para extracción detallada"""
    api_key: str = "scp-live-f7567d8f742e4c7dbf2fe70ba11e98f7"
    base_url: str = "https://pure.unisabana.edu.co"
    max_researchers_per_page: int = 20
    max_publications_per_researcher: int = 50
    delay_between_requests: float = 2.0
    session_name: str = "pure_detailed_session"

class PureDetailedExtractor:
    """Extractor detallado para Pure Universidad de la Sabana"""
    
    def __init__(self, config: DetailedExtractionConfig):
        self.config = config
        self.client = None
        self.extracted_data = {
            "research_units": [],
            "researchers": [],
            "publications": [],
            "projects": [],
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "total_requests": 0,
                "successful_requests": 0,
                "total_cost": 0
            }
        }

    def setup_client(self) -> bool:
        """Configurar cliente ScrapFly"""
        try:
            if not SCRAPFLY_AVAILABLE:
                logger.error("ScrapFly SDK no disponible")
                return False
            
            self.client = ScrapflyClient(key=self.config.api_key)
            logger.info("🚀 Cliente ScrapFly configurado para extracción detallada")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando ScrapFly: {e}")
            return False

    def scrape_with_scrapfly(self, url: str) -> Optional[str]:
        """Hacer scraping usando ScrapFly con configuración optimizada"""
        try:
            logger.info(f"🌐 Extrayendo: {url}")
            
            scrape_config = ScrapeConfig(
                url=url,
                tags=["player", "project:default"],
                asp=True,
                render_js=True,
                session=self.config.session_name
            )
            
            self.extracted_data["metadata"]["total_requests"] += 1
            result: ScrapeApiResponse = self.client.scrape(scrape_config)
            
            if result.success:
                self.extracted_data["metadata"]["successful_requests"] += 1
                self.extracted_data["metadata"]["total_cost"] += getattr(result, 'cost', 1)
                return result.content
            else:
                logger.warning(f"❌ Error scraping {url}: {result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error en ScrapFly para {url}: {e}")
            return None

    def extract_research_units(self) -> List[Dict[str, Any]]:
        """Extraer información detallada de unidades de investigación"""
        logger.info("🏛️ EXTRAYENDO UNIDADES DE INVESTIGACIÓN")
        units = []
        
        # URLs de unidades organizacionales
        unit_urls = [
            f"{self.config.base_url}/es/organisations/",
            f"{self.config.base_url}/es/organisations/?page=1",
            f"{self.config.base_url}/es/organisations/?page=2"
        ]
        
        for url in unit_urls:
            content = self.scrape_with_scrapfly(url)
            if not content:
                continue
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Buscar tarjetas de unidades
            unit_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                term in x.lower() for term in ['organisation', 'unit', 'department', 'faculty']
            ))
            
            for card in unit_cards:
                unit = self.extract_unit_details(card)
                if unit and unit not in units:
                    units.append(unit)
            
            time.sleep(self.config.delay_between_requests)
        
        # Extraer detalles individuales de cada unidad
        for unit in units:
            if unit.get('profile_url'):
                self.extract_unit_profile(unit)
        
        self.extracted_data["research_units"] = units
        logger.info(f"✅ {len(units)} unidades de investigación extraídas")
        return units

    def extract_unit_details(self, card_soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extraer detalles de una unidad desde su tarjeta"""
        try:
            unit = {}
            
            # Nombre de la unidad
            name_elem = card_soup.find(['h1', 'h2', 'h3', 'a'], class_=lambda x: x and 'name' in x.lower()) or \
                       card_soup.find('a', href=lambda x: x and '/organisations/' in x)
            
            if name_elem:
                unit['name'] = name_elem.get_text().strip()
                if name_elem.get('href'):
                    unit['profile_url'] = f"{self.config.base_url}{name_elem['href']}" if name_elem['href'].startswith('/') else name_elem['href']
            
            # Tipo de unidad
            type_elem = card_soup.find(['span', 'div'], class_=lambda x: x and 'type' in x.lower())
            if type_elem:
                unit['type'] = type_elem.get_text().strip()
            
            # Descripción
            desc_elem = card_soup.find(['p', 'div'], class_=lambda x: x and 'description' in x.lower())
            if desc_elem:
                unit['description'] = desc_elem.get_text().strip()
            
            # ID único basado en URL
            if unit.get('profile_url'):
                unit['unit_id'] = unit['profile_url'].split('/')[-2] if unit['profile_url'].endswith('/') else unit['profile_url'].split('/')[-1]
            
            return unit if unit.get('name') else None
            
        except Exception as e:
            logger.debug(f"Error extrayendo unidad: {e}")
            return None

    def extract_unit_profile(self, unit: Dict[str, Any]):
        """Extraer información detallada del perfil de una unidad"""
        try:
            profile_url = unit.get('profile_url')
            if not profile_url:
                return
            
            content = self.scrape_with_scrapfly(profile_url)
            if not content:
                return
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Información adicional de la unidad
            unit['detailed_info'] = {
                'members_count': 0,
                'publications_count': 0,
                'projects_count': 0,
                'contact_info': {},
                'research_areas': []
            }
            
            # Contar miembros
            members_section = soup.find(['section', 'div'], class_=lambda x: x and 'member' in x.lower())
            if members_section:
                member_links = members_section.find_all('a', href=lambda x: x and '/persons/' in x)
                unit['detailed_info']['members_count'] = len(member_links)
                unit['members'] = [{'name': link.get_text().strip(), 'url': link['href']} for link in member_links[:10]]
            
            # Información de contacto
            contact_info = {}
            email_elem = soup.find('a', href=lambda x: x and 'mailto:' in x)
            if email_elem:
                contact_info['email'] = email_elem['href'].replace('mailto:', '')
            
            phone_elem = soup.find(string=re.compile(r'\+?\d{1,4}[-.\s]?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}'))
            if phone_elem:
                contact_info['phone'] = phone_elem.strip()
            
            unit['detailed_info']['contact_info'] = contact_info
            
            # Áreas de investigación
            research_areas = []
            keywords = soup.find_all(['span', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['keyword', 'research-area', 'topic']
            ))
            for keyword in keywords:
                area = keyword.get_text().strip()
                if area and area not in research_areas:
                    research_areas.append(area)
            
            unit['detailed_info']['research_areas'] = research_areas[:10]
            
            time.sleep(self.config.delay_between_requests)
            
        except Exception as e:
            logger.debug(f"Error extrayendo perfil de unidad {unit.get('name')}: {e}")

    def extract_researchers_detailed(self) -> List[Dict[str, Any]]:
        """Extraer información detallada de investigadores"""
        logger.info("👥 EXTRAYENDO INVESTIGADORES DETALLADOS")
        researchers = []
        
        # URLs de investigadores con paginación
        researcher_urls = [
            f"{self.config.base_url}/es/persons/",
            f"{self.config.base_url}/es/persons/?page=1",
            f"{self.config.base_url}/es/persons/?page=2",
            f"{self.config.base_url}/es/persons/?page=3"
        ]
        
        for url in researcher_urls:
            content = self.scrape_with_scrapfly(url)
            if not content:
                continue
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Buscar tarjetas de investigadores
            researcher_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                term in x.lower() for term in ['person', 'researcher', 'profile']
            ))
            
            for card in researcher_cards:
                researcher = self.extract_researcher_details(card)
                if researcher and researcher not in researchers:
                    researchers.append(researcher)
            
            time.sleep(self.config.delay_between_requests)
        
        # Extraer detalles individuales de cada investigador
        for i, researcher in enumerate(researchers[:20]):  # Limitar a 20 para no exceder costos
            if researcher.get('profile_url'):
                logger.info(f"📄 Extrayendo perfil {i+1}/{min(len(researchers), 20)}: {researcher['name']}")
                self.extract_researcher_profile(researcher)
        
        self.extracted_data["researchers"] = researchers
        logger.info(f"✅ {len(researchers)} investigadores extraídos")
        return researchers

    def extract_researcher_details(self, card_soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extraer detalles de un investigador desde su tarjeta"""
        try:
            researcher = {}
            
            # Nombre del investigador
            name_elem = card_soup.find(['h1', 'h2', 'h3', 'a'], class_=lambda x: x and 'name' in x.lower()) or \
                       card_soup.find('a', href=lambda x: x and '/persons/' in x)
            
            if name_elem:
                researcher['name'] = name_elem.get_text().strip()
                if name_elem.get('href'):
                    researcher['profile_url'] = f"{self.config.base_url}{name_elem['href']}" if name_elem['href'].startswith('/') else name_elem['href']
            
            # Posición/Título
            position_elem = card_soup.find(['p', 'div', 'span'], class_=lambda x: x and any(
                term in x.lower() for term in ['position', 'title', 'role', 'job']
            ))
            if position_elem:
                researcher['position'] = position_elem.get_text().strip()
            
            # Departamento/Unidad
            dept_elem = card_soup.find(['p', 'div', 'span'], class_=lambda x: x and any(
                term in x.lower() for term in ['department', 'faculty', 'organization', 'unit']
            ))
            if dept_elem:
                researcher['department'] = dept_elem.get_text().strip()
            
            # ID único basado en URL
            if researcher.get('profile_url'):
                researcher['researcher_id'] = researcher['profile_url'].split('/')[-2] if researcher['profile_url'].endswith('/') else researcher['profile_url'].split('/')[-1]
            
            return researcher if researcher.get('name') else None
            
        except Exception as e:
            logger.debug(f"Error extrayendo investigador: {e}")
            return None

    def extract_researcher_profile(self, researcher: Dict[str, Any]):
        """Extraer información detallada del perfil de un investigador"""
        try:
            profile_url = researcher.get('profile_url')
            if not profile_url:
                return
            
            content = self.scrape_with_scrapfly(profile_url)
            if not content:
                return
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Información detallada del investigador
            researcher['detailed_info'] = {
                'email': '',
                'orcid': '',
                'biography': '',
                'research_areas': [],
                'publications_count': 0,
                'recent_publications': [],
                'collaborations': [],
                'projects': []
            }
            
            # Email
            email_elem = soup.find('a', href=lambda x: x and 'mailto:' in x)
            if email_elem:
                researcher['detailed_info']['email'] = email_elem['href'].replace('mailto:', '')
            
            # ORCID
            orcid_elem = soup.find('a', href=lambda x: x and 'orcid.org' in x)
            if orcid_elem:
                researcher['detailed_info']['orcid'] = orcid_elem['href']
            
            # Biografía
            bio_elem = soup.find(['div', 'p'], class_=lambda x: x and any(
                term in x.lower() for term in ['biography', 'bio', 'about', 'description']
            ))
            if bio_elem:
                researcher['detailed_info']['biography'] = bio_elem.get_text().strip()
            
            # Áreas de investigación
            research_areas = []
            keywords = soup.find_all(['span', 'div'], class_=lambda x: x and any(
                term in x.lower() for term in ['keyword', 'research-area', 'topic', 'subject']
            ))
            for keyword in keywords:
                area = keyword.get_text().strip()
                if area and area not in research_areas:
                    research_areas.append(area)
            
            researcher['detailed_info']['research_areas'] = research_areas[:10]
            
            # Publicaciones recientes
            publications = []
            pub_section = soup.find(['section', 'div'], class_=lambda x: x and 'publication' in x.lower())
            if pub_section:
                pub_links = pub_section.find_all('a', href=lambda x: x and '/publications/' in x)
                for pub_link in pub_links[:5]:  # Últimas 5 publicaciones
                    publications.append({
                        'title': pub_link.get_text().strip(),
                        'url': pub_link['href']
                    })
            
            researcher['detailed_info']['recent_publications'] = publications
            researcher['detailed_info']['publications_count'] = len(pub_links) if pub_section and pub_links else 0
            
            time.sleep(self.config.delay_between_requests)
            
        except Exception as e:
            logger.debug(f"Error extrayendo perfil de investigador {researcher.get('name')}: {e}")

    def extract_scientific_production(self) -> List[Dict[str, Any]]:
        """Extraer producción científica detallada"""
        logger.info("📚 EXTRAYENDO PRODUCCIÓN CIENTÍFICA")
        publications = []
        
        # URLs de publicaciones
        publication_urls = [
            f"{self.config.base_url}/es/publications/",
            f"{self.config.base_url}/es/publications/?page=1",
            f"{self.config.base_url}/es/publications/?page=2"
        ]
        
        for url in publication_urls:
            content = self.scrape_with_scrapfly(url)
            if not content:
                continue
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Buscar publicaciones
            publication_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                term in x.lower() for term in ['publication', 'result', 'research-output']
            ))
            
            for card in publication_cards:
                publication = self.extract_publication_details(card)
                if publication and publication not in publications:
                    publications.append(publication)
            
            time.sleep(self.config.delay_between_requests)
        
        self.extracted_data["publications"] = publications
        logger.info(f"✅ {len(publications)} publicaciones extraídas")
        return publications

    def extract_publication_details(self, card_soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extraer detalles de una publicación"""
        try:
            publication = {}
            
            # Título
            title_elem = card_soup.find(['h1', 'h2', 'h3', 'a'])
            if title_elem:
                publication['title'] = title_elem.get_text().strip()
                if title_elem.get('href'):
                    publication['url'] = f"{self.config.base_url}{title_elem['href']}" if title_elem['href'].startswith('/') else title_elem['href']
            
            # Autores
            authors_elem = card_soup.find(['p', 'div', 'span'], class_=lambda x: x and 'author' in x.lower())
            if authors_elem:
                publication['authors'] = authors_elem.get_text().strip()
            
            # Año
            year_elem = card_soup.find(['span', 'div'], string=re.compile(r'20\d{2}'))
            if year_elem:
                publication['year'] = year_elem.get_text().strip()
            
            # Tipo de publicación
            type_elem = card_soup.find(['span', 'div'], class_=lambda x: x and 'type' in x.lower())
            if type_elem:
                publication['type'] = type_elem.get_text().strip()
            
            # DOI
            doi_elem = card_soup.find('a', href=lambda x: x and 'doi.org' in x)
            if doi_elem:
                publication['doi'] = doi_elem['href']
            
            return publication if publication.get('title') else None
            
        except Exception as e:
            logger.debug(f"Error extrayendo publicación: {e}")
            return None

    def cross_reference_data(self):
        """Cruzar información entre investigadores, unidades y publicaciones"""
        logger.info("🔗 CRUZANDO REFERENCIAS DE DATOS")
        
        # Mapear investigadores por unidad
        units_map = {unit.get('unit_id'): unit for unit in self.extracted_data['research_units']}
        researchers_map = {r.get('researcher_id'): r for r in self.extracted_data['researchers']}
        
        # Agregar información cruzada
        for researcher in self.extracted_data['researchers']:
            dept_name = researcher.get('department', '')
            
            # Buscar unidad correspondiente
            for unit in self.extracted_data['research_units']:
                if dept_name.lower() in unit.get('name', '').lower():
                    researcher['unit_info'] = {
                        'unit_id': unit.get('unit_id'),
                        'unit_name': unit.get('name'),
                        'unit_type': unit.get('type')
                    }
                    break
        
        # Agregar estadísticas de unidades
        for unit in self.extracted_data['research_units']:
            unit_researchers = [r for r in self.extracted_data['researchers'] 
                              if r.get('unit_info', {}).get('unit_id') == unit.get('unit_id')]
            unit['statistics'] = {
                'researchers_count': len(unit_researchers),
                'total_publications': sum(r.get('detailed_info', {}).get('publications_count', 0) for r in unit_researchers)
            }

    def generate_knowledge_base(self) -> Dict[str, Any]:
        """Generar base de conocimiento estructurada"""
        logger.info("🧠 GENERANDO BASE DE CONOCIMIENTO")
        
        knowledge_base = {
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "total_requests": self.extracted_data["metadata"]["total_requests"],
                "successful_requests": self.extracted_data["metadata"]["successful_requests"],
                "total_cost": self.extracted_data["metadata"]["total_cost"],
                "summary": {
                    "research_units": len(self.extracted_data["research_units"]),
                    "researchers": len(self.extracted_data["researchers"]),
                    "publications": len(self.extracted_data["publications"])
                }
            },
            "research_units": self.extracted_data["research_units"],
            "researchers": self.extracted_data["researchers"],
            "scientific_production": self.extracted_data["publications"],
            "relationships": {
                "researcher_unit_mapping": {},
                "unit_statistics": {},
                "research_areas": {}
            }
        }
        
        # Generar mapeos de relaciones
        for researcher in self.extracted_data["researchers"]:
            if researcher.get('unit_info'):
                unit_id = researcher['unit_info']['unit_id']
                if unit_id not in knowledge_base["relationships"]["researcher_unit_mapping"]:
                    knowledge_base["relationships"]["researcher_unit_mapping"][unit_id] = []
                knowledge_base["relationships"]["researcher_unit_mapping"][unit_id].append(researcher['researcher_id'])
        
        return knowledge_base

    def extract_complete_data(self) -> Dict[str, Any]:
        """Ejecutar extracción completa de datos"""
        logger.info("🚀 INICIANDO EXTRACCIÓN COMPLETA DE PURE UNIVERSIDAD DE LA SABANA")
        
        start_time = time.time()
        
        try:
            # 1. Extraer unidades de investigación
            self.extract_research_units()
            
            # 2. Extraer investigadores detallados
            self.extract_researchers_detailed()
            
            # 3. Extraer producción científica
            self.extract_scientific_production()
            
            # 4. Cruzar referencias
            self.cross_reference_data()
            
            # 5. Generar base de conocimiento
            knowledge_base = self.generate_knowledge_base()
            
            end_time = time.time()
            
            logger.info(f"⏱️ Extracción completada en {end_time - start_time:.1f} segundos")
            logger.info(f"💰 Costo total: {knowledge_base['metadata']['total_cost']} créditos")
            logger.info(f"📊 Datos extraídos:")
            logger.info(f"  🏛️ Unidades: {knowledge_base['metadata']['summary']['research_units']}")
            logger.info(f"  👥 Investigadores: {knowledge_base['metadata']['summary']['researchers']}")
            logger.info(f"  📚 Publicaciones: {knowledge_base['metadata']['summary']['publications']}")
            
            return knowledge_base
            
        except Exception as e:
            logger.error(f"Error en extracción completa: {e}")
            return {}

def main():
    """Función principal"""
    config = DetailedExtractionConfig()
    extractor = PureDetailedExtractor(config)
    
    try:
        if not extractor.setup_client():
            logger.error("❌ No se pudo configurar ScrapFly")
            return
        
        # Ejecutar extracción completa
        knowledge_base = extractor.extract_complete_data()
        
        if knowledge_base:
            # Guardar base de conocimiento
            output_file = f"scraped_data/pure_knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("scraped_data", exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Base de conocimiento guardada en: {output_file}")
            logger.info("🎉 ¡EXTRACCIÓN COMPLETA EXITOSA!")
        
    except Exception as e:
        logger.error(f"Error en ejecución: {e}")

if __name__ == "__main__":
    if not SCRAPFLY_AVAILABLE:
        print("❌ ScrapFly SDK no disponible. Instalar con: pip install scrapfly-sdk")
    else:
        main()
