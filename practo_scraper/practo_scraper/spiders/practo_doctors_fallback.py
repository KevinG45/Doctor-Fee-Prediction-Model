import scrapy
import requests
import time
import re
from practo_scraper.items import DoctorItem
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from config import CITIES, SPECIALITIES
except ImportError:
    # Fallback if config import fails
    CITIES = ['Bangalore', 'Delhi', 'Mumbai']
    SPECIALITIES = [
        'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
        'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
        'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
        'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
        'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
    ]


class PractoDoctorsFallbackSpider(scrapy.Spider):
    name = "practo_doctors_fallback"
    allowed_domains = ["practo.com"]
    
    # Configuration
    cities = CITIES
    specialities = SPECIALITIES
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        # Disable Playwright for this spider
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
    }
    
    def start_requests(self):
        """Generate initial requests for all city-speciality combinations"""
        
        for city in self.cities:
            for speciality in self.specialities:
                # Build the search URL for Practo
                search_query = f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]'
                url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
                
                yield scrapy.Request(
                    url=url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    },
                    meta={
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctors_listing,
                    errback=self.handle_error,
                )
    
    def parse_doctors_listing(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        # Extract doctor profile links from the HTML
        doctor_links = response.css('div.u-border-general--bottom a[href*="/doctor/"]::attr(href)').getall()
        
        if not doctor_links:
            # Try alternative selectors if the main one doesn't work
            doctor_links = response.css('a[href*="/doctor/"]::attr(href)').getall()
        
        self.logger.info(f"Found {len(doctor_links)} doctors for {speciality} in {city}")
        
        # Process each doctor profile link
        for link in doctor_links[:10]:  # Limit to first 10 for testing
            if link:
                if link.startswith('/'):
                    profile_url = response.urljoin(link)
                else:
                    profile_url = link
                
                yield scrapy.Request(
                    url=profile_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Referer': response.url,
                    },
                    meta={
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctor_profile,
                    errback=self.handle_error,
                )
        
        # Look for pagination - try to find next page links
        next_page_links = response.css('a[href*="page="]:contains("Next"), a[href*="page="]:contains("→"), .pagination a:last-child::attr(href)').getall()
        
        for next_link in next_page_links:
            if next_link and 'page=' in next_link:
                next_page_url = response.urljoin(next_link)
                self.logger.info(f"Following pagination to: {next_page_url}")
                yield scrapy.Request(
                    url=next_page_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Referer': response.url,
                    },
                    meta={
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctors_listing,
                )
                break  # Only follow one pagination link to avoid loops
    
    def parse_doctor_profile(self, response):
        """Parse individual doctor profile page"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        try:
            item = DoctorItem()
            
            # Extract doctor information
            item['city'] = city
            item['speciality'] = speciality
            item['profile_url'] = response.url
            
            # Name - try multiple selectors
            name_selectors = [
                'h1.c-profile__title::text',
                'h1[class*="profile"]::text',
                'h1[class*="doctor"]::text',
                '.doctor-name::text',
                '.profile-title::text',
                'h1::text'
            ]
            
            name = None
            for selector in name_selectors:
                name = response.css(selector).get()
                if name:
                    name = name.strip()
                    break
            
            item['name'] = name or ""
            
            # Degree - try multiple selectors
            degree_selectors = [
                'p.c-profile__details::text',
                '.doctor-degree::text',
                '.qualification::text',
                '.profile-details::text',
                '.degree::text'
            ]
            
            degree = None
            for selector in degree_selectors:
                degree = response.css(selector).get()
                if degree:
                    degree = degree.strip()
                    break
            
            item['degree'] = degree or ""
            
            # Years of experience - extract from text
            page_text = response.text
            experience_patterns = [
                r'(\d+)\s*years?\s*(?:of\s*)?experience',
                r'experience[:\s]*(\d+)\s*years?',
                r'(\d+)\s*yrs?\s*exp',
            ]
            
            experience = ""
            for pattern in experience_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    experience = f"{match.group(1)} years"
                    break
            
            item['year_of_experience'] = experience
            
            # Location - try multiple selectors
            location_selectors = [
                'h4.c-profile--clinic__location::text',
                '.clinic-location::text',
                '.location::text',
                '.address::text',
                '[class*="location"]::text'
            ]
            
            location = None
            for selector in location_selectors:
                location = response.css(selector).get()
                if location and location.strip() and len(location.strip()) < 200:
                    # Validate it's not HTML garbage
                    if not re.search(r'^[a-z,]+$', location.strip().lower()):
                        location = location.strip()
                        break
            
            item['location'] = location or ""
            
            # DP Score (rating) - try multiple selectors
            score_selectors = [
                'span.u-green-text.u-bold.u-large-font::text',
                '.rating::text',
                '.score::text',
                '[class*="rating"]::text'
            ]
            
            score = None
            for selector in score_selectors:
                score = response.css(selector).get()
                if score:
                    score = score.strip()
                    break
            
            item['dp_score'] = score or ""
            
            # Number of patient votes
            votes_text = ""
            votes_patterns = [
                r'(\d+)\s*(?:patient\s*)?(?:reviews?|votes?)',
                r'(?:reviews?|votes?)[:\s]*(\d+)',
                r'(\d+)\s*feedbacks?'
            ]
            
            for pattern in votes_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    votes_text = match.group(1)
                    break
            
            item['npv'] = votes_text or "0"
            
            # Consultation fee - extract from text
            fee_patterns = [
                r'₹\s*(\d+(?:,\d+)*)',
                r'(?:consultation|fee|cost)[:\s]*₹?\s*(\d+(?:,\d+)*)',
                r'(\d+)\s*rupees?',
                r'rs\.?\s*(\d+(?:,\d+)*)'
            ]
            
            consultation_fee = ""
            for pattern in fee_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    fee_value = match.group(1)
                    # Validate it's not a year
                    if not re.match(r'^(19|20)\d{2}$', fee_value.replace(',', '')):
                        consultation_fee = f"₹{fee_value}"
                        break
            
            item['consultation_fee'] = consultation_fee
            
            # Google Map link - extract from text
            map_link = ""
            map_patterns = [
                r'https?://(?:www\.)?(?:maps\.)?google\.com/maps[^\s"\'<>]+',
                r'https?://goo\.gl/maps/[^\s"\'<>]+',
                r'https?://maps\.app\.goo\.gl/[^\s"\'<>]+'
            ]
            
            for pattern in map_patterns:
                match = re.search(pattern, page_text)
                if match:
                    map_link = match.group(0)
                    break
            
            item['google_map_link'] = map_link
            
            # Always yield if we have a name and profile URL
            if item.get('name') and item.get('profile_url'):
                yield item
            else:
                self.logger.warning(f"Skipping incomplete profile (missing name or URL): {response.url}")
                
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")