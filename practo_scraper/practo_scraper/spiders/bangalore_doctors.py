"""
Bangalore Doctors Spider - Robots.txt Compliant Implementation

This spider navigates naturally through the Practo website starting from
https://www.practo.com/bangalore and follows the site structure to discover
specialities and doctors, respecting the robots.txt guidelines.

Navigation Flow:
1. Start at /bangalore main page
2. Discover specialty pages (e.g., /bangalore/cardiologist-doctors)
3. Navigate through each specialty to find doctors
4. Extract individual doctor profile data

This approach avoids search URLs which are disallowed by robots.txt.
"""

import scrapy
from scrapy_playwright.page import PageMethod
import re
import asyncio
from urllib.parse import urljoin, urlparse
from practo_scraper.items import DoctorItem
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from config import (
        BASE_URL, BANGALORE_URL, CITY, COMMON_SPECIALITIES, 
        BROWSER_CONFIG, SELECTORS, SCROLL_PAUSE_TIME, MAX_SCROLL_ATTEMPTS
    )
except ImportError:
    # Fallback configuration
    BASE_URL = "https://www.practo.com"
    BANGALORE_URL = f"{BASE_URL}/bangalore"
    CITY = "Bangalore"
    COMMON_SPECIALITIES = ['general-physician', 'dentist', 'cardiologist']
    SELECTORS = {
        'specialty_links': 'a[href*="/bangalore/"][href*="-doctors"]',
        'doctor_profile_links': 'a[href*="/doctor/"]',
        'doctor_name': 'h1[data-qa-id="doctor_name"], h1.c-profile__title',
        'google_map_link': 'a[href*="maps.google.com"], a[href*="goo.gl/maps"], a[href*="google.com/maps"]'
    }


class BangaloreDoctorsSpider(scrapy.Spider):
    name = "bangalore_doctors"
    allowed_domains = ["practo.com"]
    start_urls = [BANGALORE_URL]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,  # Respect robots.txt
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    }
    
    def start_requests(self):
        """Start by requesting the main Bangalore page"""
        yield scrapy.Request(
            url=BANGALORE_URL,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod("wait_for_timeout", 3000),
                ],
            },
            callback=self.parse_bangalore_main,
            errback=self.handle_error,
        )
    
    async def parse_bangalore_main(self, response):
        """
        Parse the main Bangalore page to discover specialty pages
        """
        page = response.meta["playwright_page"]
        
        try:
            self.logger.info(f"Parsing Bangalore main page: {response.url}")
            
            # Wait for page to load completely
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Look for specialty links on the page
            specialty_links = await page.query_selector_all(SELECTORS['specialty_links'])
            
            discovered_specialties = []
            for link in specialty_links:
                href = await link.get_attribute('href')
                if href and '/bangalore/' in href and '-doctors' in href:
                    full_url = urljoin(BASE_URL, href)
                    discovered_specialties.append(full_url)
            
            self.logger.info(f"Discovered {len(discovered_specialties)} specialty pages from main page")
            
            # If we didn't find enough specialty links, try common ones
            if len(discovered_specialties) < 5:
                self.logger.info("Using common specialty patterns as fallback")
                for specialty in COMMON_SPECIALITIES:
                    specialty_url = f"{BASE_URL}/bangalore/{specialty}-doctors"
                    discovered_specialties.append(specialty_url)
            
            # Remove duplicates
            discovered_specialties = list(set(discovered_specialties))
            
            # Generate requests for each specialty page
            for specialty_url in discovered_specialties:
                yield scrapy.Request(
                    url=specialty_url,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("wait_for_timeout", 2000),
                        ],
                        "specialty_url": specialty_url,
                    },
                    callback=self.parse_specialty_page,
                    errback=self.handle_error,
                )
                
        except Exception as e:
            self.logger.error(f"Error parsing Bangalore main page: {str(e)}")
        finally:
            await page.close()
    
    async def parse_specialty_page(self, response):
        """
        Parse a specialty page (e.g., /bangalore/cardiologist-doctors) 
        to find doctor profile links
        """
        page = response.meta["playwright_page"]
        specialty_url = response.meta["specialty_url"]
        
        try:
            # Extract specialty name from URL
            specialty_name = self.extract_specialty_from_url(specialty_url)
            self.logger.info(f"Parsing specialty page: {specialty_name} - {response.url}")
            
            # Scroll to load all doctors on the page
            await self.scroll_to_load_all_doctors(page)
            
            # Find all doctor profile links
            doctor_links = await page.query_selector_all(SELECTORS['doctor_profile_links'])
            
            self.logger.info(f"Found {len(doctor_links)} doctor profiles for {specialty_name}")
            
            # Generate requests for each doctor profile
            for link in doctor_links:
                href = await link.get_attribute('href')
                if href and '/doctor/' in href:
                    profile_url = urljoin(BASE_URL, href)
                    
                    yield scrapy.Request(
                        url=profile_url,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "playwright_page_methods": [
                                PageMethod("wait_for_load_state", "domcontentloaded"),
                                PageMethod("wait_for_timeout", 2000),
                            ],
                            "specialty": specialty_name,
                            "city": CITY,
                        },
                        callback=self.parse_doctor_profile,
                        errback=self.handle_error,
                    )
            
            # Check for pagination and handle next pages
            await self.handle_pagination(page, specialty_url, specialty_name)
                    
        except Exception as e:
            self.logger.error(f"Error parsing specialty page {specialty_url}: {str(e)}")
        finally:
            await page.close()
    
    async def parse_doctor_profile(self, response):
        """
        Extract doctor information from individual profile page
        """
        page = response.meta["playwright_page"]
        specialty = response.meta["specialty"]
        city = response.meta["city"]
        
        try:
            self.logger.info(f"Parsing doctor profile: {response.url}")
            
            # Wait for profile content to load
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Extract doctor information
            item = DoctorItem()
            
            # Doctor name
            name_element = await page.query_selector(SELECTORS['doctor_name'])
            item['name'] = await name_element.inner_text() if name_element else "N/A"
            
            # Specialty
            specialty_element = await page.query_selector(SELECTORS['doctor_specialty'])
            item['speciality'] = await specialty_element.inner_text() if specialty_element else specialty
            
            # Consultation fee
            fee_element = await page.query_selector(SELECTORS['consultation_fee'])
            fee_text = await fee_element.inner_text() if fee_element else "N/A"
            item['consultation_fee'] = self.extract_fee(fee_text)
            
            # Experience
            exp_element = await page.query_selector(SELECTORS['experience'])
            exp_text = await exp_element.inner_text() if exp_element else "N/A"
            item['year_of_experience'] = self.extract_experience(exp_text)
            
            # Rating
            rating_element = await page.query_selector(SELECTORS['rating'])
            rating_text = await rating_element.inner_text() if rating_element else "N/A"
            item['dp_score'] = self.extract_rating(rating_text)
            
            # Location
            location_element = await page.query_selector(SELECTORS['location'])
            item['location'] = await location_element.inner_text() if location_element else city
            
            # Google Maps link extraction
            map_element = await page.query_selector(SELECTORS['google_map_link'])
            if map_element:
                map_href = await map_element.get_attribute('href')
                item['google_map_link'] = map_href if map_href else ""
                self.logger.info(f"Found Google Maps link for {item['name']}: {map_href}")
            else:
                # Try alternative approaches to find map links
                item['google_map_link'] = await self.find_map_link_alternative(page)
            
            # Additional fields
            item['city'] = city
            item['profile_url'] = response.url
            
            # Only yield if we have essential information
            if item['name'] != "N/A" and item['name'].strip():
                yield item
                self.logger.info(f"Extracted doctor: {item['name']} - {item['speciality']}")
            else:
                self.logger.warning(f"Skipping incomplete profile: {response.url}")
                
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
        finally:
            await page.close()
    
    async def scroll_to_load_all_doctors(self, page):
        """
        Scroll down the page to load all doctors (for infinite scroll pages)
        """
        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < MAX_SCROLL_ATTEMPTS:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(SCROLL_PAUSE_TIME * 1000)
            
            # Check if new content loaded
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # Try to click "Load More" button if available
                load_more_btn = await page.query_selector('button[data-qa-id="load_more"], .load-more-btn, button:has-text("Load More")')
                if load_more_btn:
                    await load_more_btn.click()
                    await page.wait_for_timeout(3000)
                    new_height = await page.evaluate("document.body.scrollHeight")
                
                if new_height == last_height:
                    break  # No more content to load
            
            last_height = new_height
            scroll_attempts += 1
        
        self.logger.info(f"Completed scrolling after {scroll_attempts} attempts")
    
    async def handle_pagination(self, page, base_url, specialty_name):
        """
        Handle pagination for specialty pages
        """
        try:
            # Look for next page or pagination links
            next_page_selectors = [
                'a[data-qa-id="next_page"]',
                '.pagination a[aria-label="Next"]',
                '.pagination .next',
                'a:has-text("Next")'
            ]
            
            for selector in next_page_selectors:
                next_link = await page.query_selector(selector)
                if next_link:
                    href = await next_link.get_attribute('href')
                    if href:
                        next_url = urljoin(BASE_URL, href)
                        self.logger.info(f"Found next page for {specialty_name}: {next_url}")
                        
                        yield scrapy.Request(
                            url=next_url,
                            meta={
                                "playwright": True,
                                "playwright_include_page": True,
                                "playwright_page_methods": [
                                    PageMethod("wait_for_load_state", "domcontentloaded"),
                                    PageMethod("wait_for_timeout", 2000),
                                ],
                                "specialty_url": next_url,
                            },
                            callback=self.parse_specialty_page,
                            errback=self.handle_error,
                        )
                        break
        except Exception as e:
            self.logger.error(f"Error handling pagination: {str(e)}")
    
    async def find_map_link_alternative(self, page):
        """
        Alternative method to find Google Maps links if primary selector fails
        """
        try:
            # Try to find any links containing map-related keywords
            map_selectors = [
                'a[href*="maps"]',
                'a[href*="directions"]',
                'a[title*="map"]',
                'a[title*="Map"]',
                '.map-container a',
                '.location-map a'
            ]
            
            for selector in map_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    href = await element.get_attribute('href')
                    if href and ('maps.google.com' in href or 'goo.gl/maps' in href or 'google.com/maps' in href):
                        self.logger.info(f"Found map link via alternative method: {href}")
                        return href
            
            return ""
        except Exception as e:
            self.logger.error(f"Error in alternative map link search: {str(e)}")
            return ""

    def extract_specialty_from_url(self, url):
        """Extract specialty name from URL"""
        try:
            path = urlparse(url).path
            # Extract from pattern like /bangalore/cardiologist-doctors
            parts = path.split('/')
            for part in parts:
                if '-doctors' in part:
                    return part.replace('-doctors', '').replace('-', ' ').title()
            return "Unknown"
        except:
            return "Unknown"
    
    def extract_fee(self, fee_text):
        """Extract consultation fee from text"""
        try:
            # Look for currency symbols and numbers
            fee_match = re.search(r'[₹$]\s*(\d+)', fee_text)
            if fee_match:
                return fee_match.group(1)
            
            # Look for just numbers
            number_match = re.search(r'\b(\d+)\b', fee_text)
            if number_match:
                return number_match.group(1)
                
            return "N/A"
        except:
            return "N/A"
    
    def extract_experience(self, exp_text):
        """Extract years of experience from text"""
        try:
            # Look for patterns like "5 years", "10+ years"
            exp_match = re.search(r'(\d+)\+?\s*years?', exp_text, re.IGNORECASE)
            if exp_match:
                return exp_match.group(1)
            return "N/A"
        except:
            return "N/A"
    
    def extract_rating(self, rating_text):
        """Extract rating from text"""
        try:
            # Look for decimal ratings like "4.5", "4.8"
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                return rating_match.group(1)
            return "N/A"
        except:
            return "N/A"
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
    
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")