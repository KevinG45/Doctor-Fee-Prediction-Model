"""
Simple HTTP-based spider for Practo doctors (without Playwright dependency)
This is a lightweight alternative that uses regular HTTP requests.
"""

import scrapy
from urllib.parse import urlencode
import json
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


class PractoDoctorsSimpleSpider(scrapy.Spider):
    name = "practo_doctors_simple"
    allowed_domains = ["practo.com"]
    
    # Configuration
    cities = CITIES
    specialities = SPECIALITIES
    
    def __init__(self, city=None, speciality=None, *args, **kwargs):
        super(PractoDoctorsSimpleSpider, self).__init__(*args, **kwargs)
        
        # Allow filtering by specific city or speciality
        if city:
            self.cities = [city.title()]
        if speciality:
            self.specialities = [speciality.title()]
    
    def start_requests(self):
        """Generate initial requests for all city-speciality combinations"""
        
        for city in self.cities:
            for speciality in self.specialities:
                # Build the search URL for Practo
                search_query = f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]'
                url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
                
                yield scrapy.Request(
                    url=url,
                    meta={
                        "city": city,
                        "speciality": speciality,
                        "page": 1,
                    },
                    callback=self.parse_doctors_listing,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                )
    
    def parse_doctors_listing(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        page = response.meta.get('page', 1)
        
        # Extract doctor profile links using CSS selectors
        doctor_links = response.css('div.listing-card a::attr(href), .info-card a::attr(href), div.u-border-general--bottom a[href*="/doctor/"]::attr(href)').getall()
        
        # Filter for valid doctor profile URLs
        valid_links = []
        for link in doctor_links:
            if link and '/doctor/' in link:
                if not link.startswith('http'):
                    link = response.urljoin(link)
                valid_links.append(link)
        
        # Remove duplicates
        valid_links = list(set(valid_links))
        
        self.logger.info(f"Found {len(valid_links)} doctors for {speciality} in {city} (page {page})")
        
        # Follow doctor profile URLs
        for profile_url in valid_links:
            yield scrapy.Request(
                url=profile_url,
                meta={
                    "city": city,
                    "speciality": speciality,
                },
                callback=self.parse_doctor_profile,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
        
        # Look for pagination - try to follow next page
        next_page_url = None
        
        # Try different pagination selectors
        pagination_selectors = [
            'a.next::attr(href)',
            'a[aria-label="Next"]::attr(href)',
            '.pagination a.next::attr(href)',
            '.pagination li.next a::attr(href)',
            'a:contains("Next")::attr(href)',
        ]
        
        for selector in pagination_selectors:
            next_page_url = response.css(selector).get()
            if next_page_url:
                break
        
        # Also try looking for page numbers
        if not next_page_url:
            # Look for direct page links
            page_links = response.css('.pagination a::attr(href)').getall()
            current_page = page
            for link in page_links:
                if f'page={current_page + 1}' in link or f'&p={current_page + 1}' in link:
                    next_page_url = link
                    break
        
        # If we found a next page and haven't reached our limit, follow it
        if next_page_url and page < 20:  # Limit to 20 pages per speciality
            if not next_page_url.startswith('http'):
                next_page_url = response.urljoin(next_page_url)
            
            yield scrapy.Request(
                url=next_page_url,
                meta={
                    "city": city,
                    "speciality": speciality,
                    "page": page + 1,
                },
                callback=self.parse_doctors_listing,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
    
    def parse_doctor_profile(self, response):
        """Parse individual doctor profile page"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        try:
            item = DoctorItem()
            
            # Extract doctor information using CSS selectors
            item['city'] = city
            item['speciality'] = speciality
            item['profile_url'] = response.url
            
            # Name - try multiple selectors
            name = None
            name_selectors = [
                'h1.c-profile__title::text',
                'h1.doctor-name::text',
                '.profile-title h1::text',
                'h1::text',
                '.doctor-info h1::text'
            ]
            
            for selector in name_selectors:
                name = response.css(selector).get()
                if name:
                    name = name.strip()
                    break
            
            item['name'] = name or ""
            
            # Degree/Qualification
            degree = None
            degree_selectors = [
                'p.c-profile__details::text',
                '.doctor-qualification::text',
                '.profile-details .qualification::text',
                '.doctor-degree::text'
            ]
            
            for selector in degree_selectors:
                degree = response.css(selector).get()
                if degree:
                    degree = degree.strip()
                    break
            
            item['degree'] = degree or ""
            
            # Years of experience
            experience = None
            experience_text = response.css('*::text').getall()
            for text in experience_text:
                if text and ('year' in text.lower() and 'experience' in text.lower()) or ('years' in text.lower()):
                    # Extract number of years
                    numbers = re.findall(r'\d+', text)
                    if numbers and any(char.isdigit() for char in text):
                        experience = text.strip()
                        break
            
            item['year_of_experience'] = experience or ""
            
            # Location
            location = None
            location_selectors = [
                'h4.c-profile--clinic__location::text',
                '.clinic-location::text',
                '.doctor-location::text',
                '.practice-address::text'
            ]
            
            for selector in location_selectors:
                location = response.css(selector).get()
                if location:
                    location = location.strip()
                    break
            
            item['location'] = location or ""
            
            # DP Score (rating)
            dp_score = None
            score_selectors = [
                'span.u-green-text.u-bold.u-large-font::text',
                '.doctor-rating::text',
                '.rating-score::text',
                '.dp-score::text'
            ]
            
            for selector in score_selectors:
                dp_score = response.css(selector).get()
                if dp_score:
                    dp_score = dp_score.strip()
                    break
            
            item['dp_score'] = dp_score or ""
            
            # Number of patient votes
            votes = None
            votes_text = response.css('*::text').getall()
            for text in votes_text:
                if text and ('vote' in text.lower() or 'review' in text.lower()):
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        votes = text.strip()
                        break
            
            item['npv'] = votes or "0"
            
            # Consultation fee
            fee = None
            fee_selectors = [
                'span.u-strike::text',
                '.consultation-fee::text',
                '.fee-amount::text',
                'div.u-f-right.u-large-font.u-bold::text'
            ]
            
            for selector in fee_selectors:
                fee = response.css(selector).get()
                if fee:
                    fee = fee.strip()
                    break
            
            # If no fee found, look for any text with rupee symbol or fee-related keywords
            if not fee:
                all_text = response.css('*::text').getall()
                for text in all_text:
                    if text and ('₹' in text or 'fee' in text.lower() or 'consultation' in text.lower()):
                        numbers = re.findall(r'₹?\s*\d+', text)
                        if numbers:
                            fee = text.strip()
                            break
            
            item['consultation_fee'] = fee or ""
            
            # Google map link
            google_map_link = None
            map_links = response.css('a[href*="google.com/maps"]::attr(href), iframe[src*="google.com/maps"]::attr(src)').getall()
            if map_links:
                google_map_link = map_links[0]
            
            item['google_map_link'] = google_map_link or ""
            
            # Only yield if we have essential data
            if item.get('name') and (item.get('consultation_fee') or item.get('speciality')):
                yield item
            else:
                self.logger.warning(f"Skipping incomplete profile: {response.url} - Name: {item.get('name')}, Fee: {item.get('consultation_fee')}")
                
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")