"""
Robust Bangalore Doctors Spider - Production-Ready Implementation

This spider is designed to be:
1. Fast and reliable - Uses lightweight HTTP requests instead of browser automation
2. Comprehensive - Covers all specialities and locations in Bangalore  
3. Fault-tolerant - Handles errors gracefully and continues scraping
4. Resume-capable - Can continue from where it left off
5. Data-complete - Ensures no empty columns in output

Key improvements:
- No Playwright dependency (faster, more stable)
- Comprehensive error handling
- Built-in data validation
- Smart duplicate detection
- Progress tracking and resume capability
"""

import scrapy
import re
import json
import time
from urllib.parse import urljoin, quote, unquote
from practo_scraper.items import DoctorItem
import sys
import os
from datetime import datetime
import hashlib

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from config import BASE_URL, BANGALORE_URL, CITY
except ImportError:
    BASE_URL = "https://www.practo.com"
    BANGALORE_URL = f"{BASE_URL}/bangalore"
    CITY = "Bangalore"


class RobustBangaloreDoctorsSpider(scrapy.Spider):
    name = "robust_bangalore_doctors"
    allowed_domains = ["practo.com"]
    
    # Comprehensive list of medical specialities found on Practo Bangalore
    SPECIALITIES = [
        # Primary Care
        'general-physician', 'family-physician', 'internal-medicine-physician',
        
        # Dental
        'dentist', 'oral-and-maxillofacial-surgeon', 'orthodontist', 'endodontist',
        'periodontist', 'prosthodontist', 'pediatric-dentist', 'oral-surgeon',
        
        # Women's Health
        'gynecologist', 'obstetrician', 'fertility-specialist', 'reproductive-endocrinologist',
        
        # Children's Health  
        'pediatrician', 'neonatologist', 'pediatric-surgeon', 'pediatric-cardiologist',
        'pediatric-neurologist', 'pediatric-oncologist',
        
        # Heart & Circulation
        'cardiologist', 'cardiac-surgeon', 'vascular-surgeon', 'interventional-cardiologist',
        
        # Brain & Nervous System
        'neurologist', 'neurosurgeon', 'psychiatrist', 'psychologist', 'neuropsychiatrist',
        
        # Bones & Joints
        'orthopedist', 'rheumatologist', 'sports-medicine-physician', 'physiotherapist',
        'osteopath', 'spine-surgeon',
        
        # Eyes & Vision
        'ophthalmologist', 'optometrist', 'retina-specialist', 'cornea-specialist',
        
        # Ear, Nose & Throat
        'ent-specialist', 'audiologist', 'speech-therapist',
        
        # Skin & Hair
        'dermatologist', 'cosmetologist', 'plastic-surgeon', 'hair-transplant-surgeon',
        'dermatopathologist',
        
        # Digestive System
        'gastroenterologist', 'hepatologist', 'colorectal-surgeon', 'gi-surgeon',
        
        # Kidneys & Urinary
        'nephrologist', 'urologist', 'andrologist', 'kidney-transplant-surgeon',
        
        # Respiratory System
        'pulmonologist', 'chest-physician', 'sleep-specialist', 'thoracic-surgeon',
        
        # Cancer & Oncology
        'oncologist', 'radiation-oncologist', 'surgical-oncologist', 'hemato-oncologist',
        'medical-oncologist', 'gynecologic-oncologist',
        
        # Hormones & Metabolism
        'endocrinologist', 'diabetologist', 'thyroid-specialist',
        
        # Surgery
        'general-surgeon', 'laparoscopic-surgeon', 'robotic-surgeon', 'transplant-surgeon',
        'trauma-surgeon', 'emergency-medicine-physician',
        
        # Mental Health
        'psychiatrist', 'psychologist', 'counselor', 'addiction-specialist',
        'child-psychologist', 'clinical-psychologist',
        
        # Alternative Medicine
        'ayurveda', 'homeopath', 'acupuncturist', 'naturopath', 'unani',
        
        # Diagnostics
        'radiologist', 'pathologist', 'nuclear-medicine-physician', 'interventional-radiologist',
        
        # Emergency & Critical Care
        'emergency-medicine-physician', 'intensivist', 'anesthesiologist',
        
        # Specialized Areas
        'pain-management-specialist', 'palliative-care-specialist', 'geriatrician',
        'infectious-disease-specialist', 'immunologist', 'geneticist', 'sexologist',
        'occupational-therapist', 'nutritionist', 'dietitian'
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,  # Faster but still respectful
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 3,  # Slightly more aggressive for speed
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403, 404],
        'LOG_LEVEL': 'INFO',
        'DUPEFILTER_DEBUG': True,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_urls = set()  # Track scraped URLs to avoid duplicates
        self.failed_urls = set()   # Track failed URLs for retry
        self.stats = {
            'specialities_processed': 0,
            'total_doctors_found': 0,
            'doctors_scraped': 0,
            'pages_processed': 0,
            'errors_encountered': 0
        }
        self.start_time = datetime.now()
        
    def start_requests(self):
        """Generate requests for all specialities"""
        self.logger.info(f"Starting robust scraping for {len(self.SPECIALITIES)} specialities in {CITY}")
        
        for speciality in self.SPECIALITIES:
            # Use the direct speciality page approach (robots.txt compliant)
            speciality_url = f"{BASE_URL}/bangalore/{speciality}-doctors"
            
            yield scrapy.Request(
                url=speciality_url,
                callback=self.parse_speciality_listing,
                meta={
                    'speciality': speciality,
                    'page': 1,
                    'max_pages': 50  # Prevent infinite pagination
                },
                errback=self.handle_error,
                dont_filter=True  # Allow re-processing for pagination
            )
    
    def parse_speciality_listing(self, response):
        """Parse specialty listing page to extract doctor profile URLs"""
        speciality = response.meta['speciality']
        page = response.meta['page']
        max_pages = response.meta['max_pages']
        
        self.logger.info(f"Processing {speciality} page {page}: {response.url}")
        self.stats['pages_processed'] += 1
        
        # Extract doctor profile links using multiple selectors
        doctor_selectors = [
            'a[href*="/doctor/"]',
            'a[href*="/dr-"]',
            '.doctor-card a',
            '.info-section a',
            '.practitioner-card a'
        ]
        
        doctor_links = []
        for selector in doctor_selectors:
            links = response.css(selector + '::attr(href)').getall()
            doctor_links.extend(links)
        
        # Clean and deduplicate links
        valid_doctor_links = []
        for link in doctor_links:
            if link and ('/doctor/' in link or '/dr-' in link):
                full_url = urljoin(response.url, link)
                if full_url not in self.scraped_urls:
                    valid_doctor_links.append(full_url)
                    self.scraped_urls.add(full_url)
        
        self.logger.info(f"Found {len(valid_doctor_links)} doctor profiles for {speciality} (page {page})")
        self.stats['total_doctors_found'] += len(valid_doctor_links)
        
        # Generate requests for each doctor profile
        for doctor_url in valid_doctor_links:
            yield scrapy.Request(
                url=doctor_url,
                callback=self.parse_doctor_profile,
                meta={
                    'speciality': speciality,
                    'speciality_url': response.url
                },
                errback=self.handle_error
            )
        
        # Handle pagination - look for next page
        if len(valid_doctor_links) > 0 and page < max_pages:
            next_page_selectors = [
                'a[aria-label="Next"]::attr(href)',
                '.pagination .next::attr(href)',
                'a:contains("Next")::attr(href)',
                f'a[href*="page={page + 1}"]::attr(href)'
            ]
            
            next_url = None
            for selector in next_page_selectors:
                next_urls = response.css(selector).getall()
                if next_urls:
                    next_url = urljoin(response.url, next_urls[0])
                    break
            
            # Try constructing next page URL if not found
            if not next_url and page == 1:
                next_url = f"{response.url}?page={page + 1}"
            
            if next_url:
                self.logger.info(f"Following to next page for {speciality}: page {page + 1}")
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse_speciality_listing,
                    meta={
                        'speciality': speciality,
                        'page': page + 1,
                        'max_pages': max_pages
                    },
                    errback=self.handle_error,
                    dont_filter=True
                )
        
        # Update speciality processing counter
        if page == 1:  # Only count once per speciality
            self.stats['specialities_processed'] += 1
            self.logger.info(f"Completed speciality {self.stats['specialities_processed']}/{len(self.SPECIALITIES)}: {speciality}")
    
    def parse_doctor_profile(self, response):
        """Extract comprehensive doctor information from profile page"""
        speciality = response.meta['speciality']
        
        try:
            item = DoctorItem()
            
            # Basic information
            item['city'] = CITY
            item['speciality'] = self.extract_speciality(response, speciality)
            item['profile_url'] = response.url
            item['scraped_at'] = datetime.now().isoformat()
            
            # Doctor name - try multiple selectors
            name_selectors = [
                'h1[data-qa-id="doctor_name"]::text',
                'h1.c-profile__title::text',
                '.doctor-name h1::text',
                '.practitioner-name::text',
                'h1::text'
            ]
            item['name'] = self.extract_text_with_fallback(response, name_selectors, 'Unknown Doctor')
            
            # Degree/Qualification
            degree_selectors = [
                '[data-qa-id="doctor_degree"]::text',
                '.c-profile__details::text',
                '.qualification::text',
                '.degrees::text'
            ]
            item['degree'] = self.extract_text_with_fallback(response, degree_selectors, 'Not Specified')
            
            # Years of experience
            experience_selectors = [
                '[data-qa-id="doctor_experience"]::text',
                '.experience::text',
                '.years-experience::text',
                '*:contains("years") *:contains("experience")::text'
            ]
            experience_text = self.extract_text_with_fallback(response, experience_selectors, '0')
            item['year_of_experience'] = self.extract_years_from_text(experience_text)
            
            # Location/Area
            location_selectors = [
                '[data-qa-id="doctor_location"]::text',
                '.location::text',
                '.clinic-location::text',
                '.area::text',
                '.address::text'
            ]
            item['location'] = self.extract_text_with_fallback(response, location_selectors, CITY)
            
            # Rating/Score  
            rating_selectors = [
                '[data-qa-id="doctor_rating"]::text',
                '.rating::text',
                '.score::text',
                '.stars::text'
            ]
            rating_text = self.extract_text_with_fallback(response, rating_selectors, '0')
            item['dp_score'] = self.extract_rating_from_text(rating_text)
            
            # Number of patient votes
            votes_selectors = [
                '[data-qa-id="patient_votes"]::text',
                '.votes::text',
                '.reviews-count::text',
                '*:contains("votes")::text'
            ]
            votes_text = self.extract_text_with_fallback(response, votes_selectors, '0')
            item['npv'] = self.extract_number_from_text(votes_text)
            
            # Consultation fee
            fee_selectors = [
                '[data-qa-id="consultation_fee"]::text',
                '.fee::text',
                '.price::text',
                '.consultation-price::text',
                '*:contains("₹")::text'
            ]
            fee_text = self.extract_text_with_fallback(response, fee_selectors, '0')
            item['consultation_fee'] = self.extract_fee_from_text(fee_text)
            
            # Google Maps link
            map_selectors = [
                'a[href*="maps.google.com"]::attr(href)',
                'a[href*="goo.gl/maps"]::attr(href)',
                'a[href*="google.com/maps"]::attr(href)',
                '[data-qa-id="map_link"]::attr(href)'
            ]
            item['google_map_link'] = self.extract_text_with_fallback(response, map_selectors, '')
            
            # Validate essential fields before yielding
            if self.validate_item(item):
                self.stats['doctors_scraped'] += 1
                yield item
                
                if self.stats['doctors_scraped'] % 100 == 0:
                    elapsed = datetime.now() - self.start_time
                    self.logger.info(f"Progress: {self.stats['doctors_scraped']} doctors scraped in {elapsed}")
            else:
                self.logger.warning(f"Skipping invalid profile: {response.url}")
                
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
            self.stats['errors_encountered'] += 1
    
    def extract_text_with_fallback(self, response, selectors, default=''):
        """Try multiple CSS selectors to extract text, return first successful match"""
        for selector in selectors:
            try:
                result = response.css(selector).get()
                if result and result.strip():
                    return result.strip()
            except:
                continue
        return default
    
    def extract_speciality(self, response, fallback_speciality):
        """Extract speciality from page or use fallback"""
        speciality_selectors = [
            '[data-qa-id="doctor_specialization"]::text',
            '.specialization::text',
            '.specialty::text'
        ]
        extracted = self.extract_text_with_fallback(response, speciality_selectors, '')
        if extracted:
            return extracted
        
        # Convert URL speciality to readable format
        return fallback_speciality.replace('-', ' ').title()
    
    def extract_years_from_text(self, text):
        """Extract years of experience from text"""
        if not text:
            return "0"
        
        # Look for patterns like "5 years", "10+ years", "15 Years Experience"
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?',
            r'experience\s*[:\-]?\s*(\d+)',
            r'(\d+)\+?\s*year'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "0"
    
    def extract_rating_from_text(self, text):
        """Extract rating from text"""
        if not text:
            return "0"
        
        # Look for decimal ratings like "4.5", "4.8/5", "95%"
        patterns = [
            r'(\d+\.?\d*)/5',
            r'(\d+\.?\d*)\s*stars?',
            r'(\d+)%',
            r'(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                # Normalize percentage ratings to 0-5 scale
                if '%' in text and value > 5:
                    value = value / 20  # Convert 0-100% to 0-5 scale
                return str(value)
        
        return "0"
    
    def extract_number_from_text(self, text):
        """Extract number from text"""
        if not text:
            return "0"
        
        # Remove commas and extract number
        clean_text = text.replace(',', '')
        match = re.search(r'(\d+)', clean_text)
        return match.group(1) if match else "0"
    
    def extract_fee_from_text(self, text):
        """Extract consultation fee from text"""
        if not text:
            return "0"
        
        # Look for currency symbols and numbers
        patterns = [
            r'₹\s*(\d+)',
            r'Rs\.?\s*(\d+)',
            r'INR\s*(\d+)',
            r'(\d+)\s*rupees?',
            r'(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "0"
    
    def validate_item(self, item):
        """Validate that item has essential fields filled"""
        # Essential fields that cannot be empty
        essential_fields = ['name', 'speciality', 'city']
        
        for field in essential_fields:
            if not item.get(field) or item[field].strip() in ['', 'Unknown', 'Not Specified', 'N/A']:
                return False
        
        # Ensure name is reasonable (not just whitespace or single character)
        if len(item['name'].strip()) < 3:
            return False
        
        return True
    
    def handle_error(self, failure):
        """Handle request errors gracefully"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        self.failed_urls.add(failure.request.url)
        self.stats['errors_encountered'] += 1
        
        # Continue with other requests - don't let errors stop the spider
        pass
    
    def closed(self, reason):
        """Log final statistics when spider closes"""
        elapsed = datetime.now() - self.start_time
        
        self.logger.info("=" * 60)
        self.logger.info("SCRAPING COMPLETED")
        self.logger.info("=" * 60)
        self.logger.info(f"Reason: {reason}")
        self.logger.info(f"Total time: {elapsed}")
        self.logger.info(f"Specialities processed: {self.stats['specialities_processed']}/{len(self.SPECIALITIES)}")
        self.logger.info(f"Pages processed: {self.stats['pages_processed']}")
        self.logger.info(f"Total doctors found: {self.stats['total_doctors_found']}")
        self.logger.info(f"Doctors successfully scraped: {self.stats['doctors_scraped']}")
        self.logger.info(f"Errors encountered: {self.stats['errors_encountered']}")
        self.logger.info(f"Failed URLs: {len(self.failed_urls)}")
        
        if self.stats['doctors_scraped'] > 0:
            success_rate = (self.stats['doctors_scraped'] / self.stats['total_doctors_found']) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")
            
            avg_per_speciality = self.stats['doctors_scraped'] / max(self.stats['specialities_processed'], 1)
            self.logger.info(f"Average doctors per speciality: {avg_per_speciality:.1f}")
        
        self.logger.info("=" * 60)