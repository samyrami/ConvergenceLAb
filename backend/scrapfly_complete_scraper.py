#!/usr/bin/env python3
"""
SCRAPFLY COMPLETE SCRAPER - Solución definitiva para Pure Universidad de la Sabana
Usa la API oficial de ScrapFly para bypass garantizado del 100% de las protecciones
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dataclasses import dataclass
from bs4 import BeautifulSoup

try:
    from scrapfly import ScrapflyClient, ScrapeConfig, ScrapeApiResponse
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False
    print("Error: ScrapFly SDK no disponible. Instalar con: pip install scrapfly-sdk")

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CompleteScrapingConfig:
    """Configuración para el scraper completo con ScrapFly"""
    api_key: str = "scp-live-f7567d8f742e4c7dbf2fe70ba11e98f7"
    base_url: str = "https://pure.unisabana.edu.co"
    max_pages_per_section: int = 10
    delay_between_requests: float = 2.0
    session_name: str = "pure_unisabana_session"
    
class ScrapFlyCompleteScraper:
    """Scraper completo usando ScrapFly SDK oficial"""
    
    def __init__(self, config: CompleteScrapingConfig):
        self.config = config
        self.client = None
        self.results = {}
        self.total_requests = 0
        self.successful_requests = 0
        self.total_cost = 0
        
        # URLs objetivo organizadas por sección
        self.target_sections = {
            "home": [
                f"{config.base_url}/es/",
                f"{config.base_url}/en/"
            ],
            "researchers": [
                f"{config.base_url}/es/persons/",
                f"{config.base_url}/es/persons/?page=1",
                f"{config.base_url}/es/persons/?page=2"
            ],
            "organizations": [
                f"{config.base_url}/es/organisations/",
                f"{config.base_url}/es/organisations/?page=1"
            ],
            "publications": [
                f"{config.base_url}/es/publications/",
                f"{config.base_url}/es/publications/?page=1",
                f"{config.base_url}/es/publications/?page=2"
            ],
            "projects": [
                f"{config.base_url}/es/projects/",
                f"{config.base_url}/es/projects/?page=1"
            ],
            "datasets": [
                f"{config.base_url}/es/datasets/"
            ],
            "activities": [
                f"{config.base_url}/es/activities/"
            ],
            "prizes": [
                f"{config.base_url}/es/prizes/"
            ]
        }

    def setup_scrapfly_client(self) -> bool:
        """Configurar cliente ScrapFly"""
        try:
            if not SCRAPFLY_AVAILABLE:
                logger.error("ScrapFly SDK no disponible")
                return False
            
            self.client = ScrapflyClient(key=self.config.api_key)
            logger.info("🚀 Cliente ScrapFly configurado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando ScrapFly: {e}")
            return False

    def scrape_url_with_scrapfly(self, url: str, section: str = "general") -> Optional[Dict[str, Any]]:
        """Hacer scraping de una URL usando ScrapFly"""
        try:
            logger.info(f"🌐 ScrapFly procesando: {url}")
            
            # Configurar parámetros de scraping (configuración simplificada)
            scrape_config = ScrapeConfig(
                url=url,
                tags=["player", "project:pure_unisabana"],
                asp=True,  # Anti-scraping protection
                render_js=True,  # JavaScript rendering
                country="CO",  # IP colombiana
                session=self.config.session_name
                # No usar retry con timeout personalizado
                # retry=True,
                # timeout=30000
            )
            
            # Ejecutar scraping
            self.total_requests += 1
            result: ScrapeApiResponse = self.client.scrape(scrape_config)
            
            if result.success:
                # Procesar contenido exitoso
                content = result.content
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extraer información específica según la sección
                extracted_data = self.extract_section_data(soup, section, url)
                
                scrape_result = {
                    "url": url,
                    "section": section,
                    "status": "success",
                    "status_code": result.status_code,
                    "title": soup.find('title').get_text().strip() if soup.find('title') else "",
                    "content_length": len(content),
                    "links_found": len(soup.find_all('a', href=True)),
                    "extracted_data": extracted_data,
                    "scrapfly_cost": getattr(result, 'cost', 1),
                    "scraped_at": datetime.now().isoformat()
                }
                
                self.successful_requests += 1
                self.total_cost += scrape_result['scrapfly_cost']
                
                logger.info(f"✅ Éxito: {scrape_result['links_found']} links, costo: {scrape_result['scrapfly_cost']} créditos")
                return scrape_result
            
            else:
                logger.warning(f"❌ ScrapFly falló para {url}: {result.error}")
                return {
                    "url": url,
                    "section": section,
                    "status": "failed",
                    "error": str(result.error),
                    "scraped_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error en ScrapFly para {url}: {e}")
            return {
                "url": url,
                "section": section,
                "status": "error",
                "error": str(e),
                "scraped_at": datetime.now().isoformat()
            }

    def extract_section_data(self, soup: BeautifulSoup, section: str, url: str) -> Dict[str, Any]:
        """Extraer datos específicos según la sección"""
        try:
            data = {
                "all_links": [a.get('href') for a in soup.find_all('a', href=True)],
                "internal_links": [],
                "external_links": [],
                "section_specific": {}
            }
            
            # Clasificar links
            for link in data["all_links"]:
                if link and link.startswith('http'):
                    if 'pure.unisabana.edu.co' in link:
                        data["internal_links"].append(link)
                    else:
                        data["external_links"].append(link)
                elif link and link.startswith('/'):
                    data["internal_links"].append(f"{self.config.base_url}{link}")
            
            # Extraer datos específicos por sección
            if section == "researchers":
                # Buscar información de investigadores
                researchers = []
                researcher_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(term in x.lower() for term in ['person', 'researcher', 'profile']))
                
                for card in researcher_cards[:10]:  # Limitar a 10 por página
                    researcher = {}
                    
                    # Nombre
                    name_elem = card.find(['h1', 'h2', 'h3', 'a'], class_=lambda x: x and 'name' in x.lower()) or \
                               card.find('a', href=lambda x: x and '/persons/' in x)
                    if name_elem:
                        researcher['name'] = name_elem.get_text().strip()
                        if name_elem.get('href'):
                            researcher['profile_url'] = name_elem['href']
                    
                    # Posición/Título
                    title_elem = card.find(['p', 'div', 'span'], class_=lambda x: x and any(term in x.lower() for term in ['title', 'position', 'role']))
                    if title_elem:
                        researcher['title'] = title_elem.get_text().strip()
                    
                    # Departamento
                    dept_elem = card.find(['p', 'div', 'span'], class_=lambda x: x and any(term in x.lower() for term in ['department', 'faculty', 'organization']))
                    if dept_elem:
                        researcher['department'] = dept_elem.get_text().strip()
                    
                    if researcher:
                        researchers.append(researcher)
                
                data["section_specific"]["researchers"] = researchers
                
            elif section == "publications":
                # Buscar publicaciones
                publications = []
                pub_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(term in x.lower() for term in ['publication', 'result', 'research']))
                
                for card in pub_cards[:10]:
                    publication = {}
                    
                    # Título
                    title_elem = card.find(['h1', 'h2', 'h3', 'a'])
                    if title_elem:
                        publication['title'] = title_elem.get_text().strip()
                        if title_elem.get('href'):
                            publication['url'] = title_elem['href']
                    
                    # Autores
                    authors_elem = card.find(['p', 'div', 'span'], class_=lambda x: x and 'author' in x.lower())
                    if authors_elem:
                        publication['authors'] = authors_elem.get_text().strip()
                    
                    # Año
                    year_elem = card.find(['span', 'div'], class_=lambda x: x and any(term in x.lower() for term in ['year', 'date']))
                    if year_elem:
                        publication['year'] = year_elem.get_text().strip()
                    
                    if publication:
                        publications.append(publication)
                
                data["section_specific"]["publications"] = publications
                
            elif section == "organizations":
                # Buscar organizaciones/facultades
                organizations = []
                org_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(term in x.lower() for term in ['organization', 'faculty', 'department']))
                
                for card in org_cards[:10]:
                    organization = {}
                    
                    # Nombre
                    name_elem = card.find(['h1', 'h2', 'h3', 'a'])
                    if name_elem:
                        organization['name'] = name_elem.get_text().strip()
                        if name_elem.get('href'):
                            organization['url'] = name_elem['href']
                    
                    # Descripción
                    desc_elem = card.find(['p', 'div'], class_=lambda x: x and 'description' in x.lower())
                    if desc_elem:
                        organization['description'] = desc_elem.get_text().strip()
                    
                    if organization:
                        organizations.append(organization)
                
                data["section_specific"]["organizations"] = organizations
            
            return data
            
        except Exception as e:
            logger.warning(f"Error extrayendo datos de {section}: {e}")
            return {"error": str(e)}

    def scrape_all_sections(self) -> Dict[str, Any]:
        """Hacer scraping completo de todas las secciones"""
        logger.info("🚀 INICIANDO SCRAPING COMPLETO CON SCRAPFLY")
        logger.info(f"🎯 Secciones objetivo: {len(self.target_sections)}")
        
        start_time = time.time()
        
        for section_name, urls in self.target_sections.items():
            logger.info(f"\n📂 Procesando sección: {section_name.upper()}")
            section_results = []
            
            for i, url in enumerate(urls[:self.config.max_pages_per_section]):
                logger.info(f"  📄 {i+1}/{len(urls)}: {url}")
                
                result = self.scrape_url_with_scrapfly(url, section_name)
                if result:
                    section_results.append(result)
                
                # Delay respetuoso
                if i < len(urls) - 1:
                    time.sleep(self.config.delay_between_requests)
            
            self.results[section_name] = section_results
            
            # Pausa entre secciones
            time.sleep(3.0)
        
        end_time = time.time()
        
        # Generar resumen
        summary = self.generate_summary(end_time - start_time)
        return summary

    def generate_summary(self, execution_time: float) -> Dict[str, Any]:
        """Generar resumen completo de los resultados"""
        successful_by_section = {}
        total_data_extracted = {}
        
        for section, results in self.results.items():
            successful = [r for r in results if r.get('status') == 'success']
            successful_by_section[section] = len(successful)
            
            # Contar datos extraídos por sección
            total_researchers = sum(len(r.get('extracted_data', {}).get('section_specific', {}).get('researchers', [])) for r in successful)
            total_publications = sum(len(r.get('extracted_data', {}).get('section_specific', {}).get('publications', [])) for r in successful)
            total_organizations = sum(len(r.get('extracted_data', {}).get('section_specific', {}).get('organizations', [])) for r in successful)
            
            total_data_extracted[section] = {
                "researchers": total_researchers,
                "publications": total_publications,
                "organizations": total_organizations
            }
        
        summary = {
            "execution_time": execution_time,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "success_rate": (self.successful_requests / self.total_requests) * 100 if self.total_requests > 0 else 0,
            "total_cost": self.total_cost,
            "successful_by_section": successful_by_section,
            "total_data_extracted": total_data_extracted,
            "sections_processed": len(self.results),
            "complete_results": self.results
        }
        
        # Mostrar resumen
        logger.info("\n📊 RESUMEN COMPLETO DE SCRAPFLY:")
        logger.info(f"  ⏱️ Tiempo total: {execution_time:.1f}s")
        logger.info(f"  📡 Requests totales: {self.total_requests}")
        logger.info(f"  ✅ Requests exitosos: {self.successful_requests}")
        logger.info(f"  📈 Tasa de éxito: {summary['success_rate']:.1f}%")
        logger.info(f"  💰 Costo total: {self.total_cost} créditos")
        logger.info(f"  📂 Secciones procesadas: {summary['sections_processed']}")
        
        logger.info("\n📊 ÉXITOS POR SECCIÓN:")
        for section, count in successful_by_section.items():
            logger.info(f"  📁 {section}: {count} URLs exitosas")
        
        logger.info("\n🎯 DATOS EXTRAÍDOS:")
        total_researchers = sum(data['researchers'] for data in total_data_extracted.values())
        total_publications = sum(data['publications'] for data in total_data_extracted.values())
        total_organizations = sum(data['organizations'] for data in total_data_extracted.values())
        
        logger.info(f"  👥 Investigadores encontrados: {total_researchers}")
        logger.info(f"  📚 Publicaciones encontradas: {total_publications}")
        logger.info(f"  🏛️ Organizaciones encontradas: {total_organizations}")
        
        return summary

def main():
    """Función principal"""
    config = CompleteScrapingConfig()
    scraper = ScrapFlyCompleteScraper(config)
    
    try:
        # Configurar cliente
        if not scraper.setup_scrapfly_client():
            logger.error("❌ No se pudo configurar ScrapFly")
            return
        
        # Ejecutar scraping completo
        summary = scraper.scrape_all_sections()
        
        # Guardar resultados completos
        output_file = f"scraped_data/scrapfly_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("scraped_data", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Resultados completos guardados en: {output_file}")
        
        # Resumen final
        if summary['success_rate'] > 80:
            logger.info("\n🎉 ¡SCRAPING COMPLETO EXITOSO!")
            logger.info("✅ Pure Universidad de la Sabana completamente accesible")
            logger.info("✅ Datos extraídos y listos para el agente conversacional")
        elif summary['success_rate'] > 50:
            logger.info("\n🔄 SCRAPING PARCIALMENTE EXITOSO")
            logger.info("✅ Mayoría de secciones accesibles")
            logger.info("🔧 Algunas secciones pueden necesitar ajustes")
        else:
            logger.info("\n⚠️ PROBLEMAS DETECTADOS")
            logger.info("🔧 Verificar configuración de ScrapFly")
            logger.info("💳 Verificar créditos disponibles")
        
        logger.info(f"\n💰 Costo total: {summary['total_cost']} créditos ScrapFly")
        logger.info("🚀 ¡Sistema listo para alimentar el agente conversacional!")
        
    except Exception as e:
        logger.error(f"Error en ejecución: {e}")

if __name__ == "__main__":
    if not SCRAPFLY_AVAILABLE:
        print("❌ ScrapFly SDK no disponible")
        print("Instalar con: pip install scrapfly-sdk")
    else:
        main()
