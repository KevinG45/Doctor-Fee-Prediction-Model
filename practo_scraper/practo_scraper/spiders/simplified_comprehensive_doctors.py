"""
Simplified Comprehensive Bangalore Doctors Spider
Works without Playwright - uses standard Scrapy HTTP downloader

This version implements the same two-level scraping strategy and field extraction
but without browser automation, making it more reliable in environments where
Playwright installation fails.
"""

import scrapy
import re
import random
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
import json

# Import enhanced configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from enhanced_config import (
        COMPREHENSIVE_SPECIALTIES, TARGET_CITY, generate_search_url,
        EXTRACTION_SELECTORS, get_random_user_agent,
        get_download_delay, get_timestamp, DATA_VALIDATION_RULES,
        OUTPUT_CONFIG, MONITORING_CONFIG
    )
except ImportError:
    # Fallback configuration
    COMPREHENSIVE_SPECIALTIES = ["Cardiologist", "Dermatologist", "Dentist", "Gynecologist", "Orthopedist"]
    TARGET_CITY = "Bangalore"
    
    def generate_search_url(specialty, city="Bangalore"):
        query_json = f'[{{"word":"{specialty}","autocompleted":true,"category":"subspeciality"}}]'
        from urllib.parse import quote
        encoded_query = quote(query_json)
        return f"https://www.practo.com/search/doctors?results_type=doctor&q={encoded_query}&city={city}"
    
    def get_random_user_agent():
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        return random.choice(agents)
    
    MONITORING_CONFIG = {'expected_total_doctors': 4500, 'progress_log_interval': 10}

from practo_scraper.items import DoctorItem


class SimplifiedComprehensiveDoctorsSpider(scrapy.Spider):
    name = "simplified_comprehensive_doctors"
    allowed_domains = ["practo.com"]
    
    # Custom settings for respectful scraping
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Following problem statement approach
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,  # Sequential processing as specified
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
        }
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_doctors = 0
        self.failed_extractions = 0
        self.specialties_processed = 0
        self.start_time = datetime.now()
        
        # Statistics tracking
        self.stats = {
            'doctors_per_specialty': {},
            'pages_per_specialty': {},
            'extraction_success_rate': 0,
            'total_pages_processed': 0
        }
        
        # Get specialties to process (allow filtering for testing)
        specialties_arg = kwargs.get('specialties')
        if specialties_arg:
            self.specialties_to_process = [s.strip() for s in specialties_arg.split(',')]
        else:
            self.specialties_to_process = COMPREHENSIVE_SPECIALTIES[:5]  # Limit for testing
        
        self.logger.info(f"Starting simplified scraping for {len(self.specialties_to_process)} specialties: {self.specialties_to_process}")
    
    def start_requests(self):
        """
        Generate initial requests for specialty listing pages
        """
        for specialty in self.specialties_to_process:
            search_url = generate_search_url(specialty, TARGET_CITY)
            
            yield scrapy.Request(
                url=search_url,
                headers={'User-Agent': get_random_user_agent()},
                meta={
                    'specialty': specialty,
                    'city': TARGET_CITY,
                    'page_number': 1,
                    'level': 'listing',  # Level 1: Specialty listing
                },
                callback=self.parse_listing_page,
                errback=self.handle_error,
                dont_filter=False
            )
    
    def parse_listing_page(self, response):
        """
        Level 1: Parse specialty listing pages to extract doctor profile URLs
        """
        specialty = response.meta['specialty']
        page_number = response.meta['page_number']
        
        self.logger.info(f"Processing {specialty} - Page {page_number}: {response.url}")
        
        # Extract doctor profile URLs using multiple selectors
        doctor_urls = self.extract_doctor_urls(response)
        
        if doctor_urls:
            self.logger.info(f"Found {len(doctor_urls)} doctors on {specialty} page {page_number}")
            
            # Update statistics
            if specialty not in self.stats['doctors_per_specialty']:
                self.stats['doctors_per_specialty'][specialty] = 0
                self.stats['pages_per_specialty'][specialty] = 0
            
            self.stats['doctors_per_specialty'][specialty] += len(doctor_urls)
            self.stats['pages_per_specialty'][specialty] += 1
            self.stats['total_pages_processed'] += 1
            
            # Generate Level 2 requests for individual doctor profiles
            for doctor_url in doctor_urls:
                yield scrapy.Request(
                    url=doctor_url,
                    headers={'User-Agent': get_random_user_agent()},
                    meta={
                        'specialty': specialty,
                        'city': TARGET_CITY,
                        'level': 'profile',  # Level 2: Individual profile
                    },
                    callback=self.parse_doctor_profile,
                    errback=self.handle_error,
                    dont_filter=False
                )
            
            # Handle pagination (simplified - just try first few pages)
            if page_number <= 3:  # Limit pages for testing
                next_page_url = self.get_next_page_url(response, specialty, page_number)
                if next_page_url:
                    yield scrapy.Request(
                        url=next_page_url,
                        headers={'User-Agent': get_random_user_agent()},
                        meta={
                            'specialty': specialty,
                            'city': TARGET_CITY,
                            'page_number': page_number + 1,
                            'level': 'listing',
                        },
                        callback=self.parse_listing_page,
                        errback=self.handle_error,
                        dont_filter=False
                    )
        else:
            self.logger.warning(f"No doctors found on {specialty} page {page_number}")
            self.logger.debug(f"Response preview: {response.text[:500]}")
    
    def parse_doctor_profile(self, response):
        """
        Level 2: Extract complete doctor information from individual profiles
        """
        specialty = response.meta['specialty']
        city = response.meta['city']
        
        try:
            # Create doctor item
            item = DoctorItem()
            
            # Field 1: name - multiple selectors
            item['name'] = self.extract_text_field(response, [
                'h1[data-qa-id="doctor_name"]::text',
                'h1.c-profile__title::text',
                '.doctor-name h1::text',
                'h1::text',
                '.profile-name::text'
            ], "N/A")
            
            # Field 2: speciality (inherit from search)
            item['speciality'] = specialty
            
            # Field 3: degree
            item['degree'] = self.extract_text_field(response, [
                '[data-qa-id="doctor_qualification"]::text',
                '.qualification-text::text',
                '.doctor-qualification::text',
                '.qualifications::text',
                '.degree::text'
            ], "Not Specified")
            
            # Field 4: year_of_experience
            experience_text = self.extract_text_field(response, [
                '[data-qa-id="doctor_experience"]::text',
                '.experience-text::text',
                '.years-experience::text',
                '*:contains("Years Experience")',
                '*:contains("experience")'
            ], "0")
            item['year_of_experience'] = self.extract_experience_years(experience_text)
            
            # Field 5: location
            item['location'] = self.extract_text_field(response, [
                '[data-qa-id="doctor_location"]::text',
                '.clinic-name::text',
                '.hospital-name::text',
                '.practice-name::text',
                '.location::text'
            ], city)
            
            # Field 6: city (hardcoded as per requirement)
            item['city'] = city
            
            # Field 7: dp_score (rating)
            rating_text = self.extract_text_field(response, [
                '[data-qa-id="doctor_rating"]::text',
                '.rating-percent::text',
                '.doctor-rating::text',
                '.rating-value::text',
                '*:contains("%")'
            ], "0.0")
            item['dp_score'] = self.extract_rating_score(rating_text)
            
            # Field 8: npv (patient stories)
            patient_text = self.extract_text_field(response, [
                '[data-qa-id="patient_stories"]::text',
                '.patient-stories::text',
                '.patient-feedback-count::text',
                '*:contains("Patient Stories")',
                '*:contains("patient")'
            ], "0")
            item['npv'] = self.extract_patient_count(patient_text)
            
            # Field 9: consultation_fee
            fee_text = self.extract_text_field(response, [
                '[data-qa-id="consultation_fee"]::text',
                '.fee-amount::text',
                '.consultation-fee::text',
                '*:contains("₹")',
                '*:contains("fee")'
            ], "0")
            item['consultation_fee'] = self.extract_consultation_fee(fee_text)
            
            # Field 10: profile_url
            item['profile_url'] = response.url
            
            # Field 11: scraped_at
            item['scraped_at'] = datetime.now().isoformat()
            
            # Validate and yield item if it meets quality standards
            if self.validate_doctor_item(item):
                self.scraped_doctors += 1
                
                # Progress logging
                if self.scraped_doctors % MONITORING_CONFIG.get('progress_log_interval', 10) == 0:
                    self.log_progress()
                
                yield item
                
                self.logger.info(f"✅ Extracted: {item['name']} - {specialty}")
            else:
                self.failed_extractions += 1
                self.logger.warning(f"❌ Failed validation: {response.url}")
                
        except Exception as e:
            self.failed_extractions += 1
            self.logger.error(f"❌ Error extracting profile {response.url}: {str(e)}")
    
    def extract_doctor_urls(self, response):
        """Extract doctor profile URLs from listing page"""
        doctor_urls = []
        
        # Multiple selectors to find doctor profile links
        selectors = [
            'a[href*="/doctor/"]::attr(href)',
            'a[href*="/bangalore/doctor/"]::attr(href)',
            '.doctor-card a[href*="/doctor/"]::attr(href)',
            '[data-qa-id="doctor_card"] a[href*="/doctor/"]::attr(href)',
            '.listing-item a[href*="/doctor/"]::attr(href)',
            'a[href*="/practo.com/doctor/"]::attr(href)'
        ]
        
        for selector in selectors:
            links = response.css(selector).getall()
            for href in links:
                if href and '/doctor/' in href:
                    full_url = urljoin(response.url, href)
                    if full_url not in doctor_urls:
                        doctor_urls.append(full_url)
        
        # Also try extracting from any anchor tags
        all_links = response.css('a::attr(href)').getall()
        for href in all_links:
            if href and '/doctor/' in href and 'practo.com' in (response.url + href):
                full_url = urljoin(response.url, href)
                if full_url not in doctor_urls:
                    doctor_urls.append(full_url)
        
        return doctor_urls[:20]  # Limit for testing
    
    def get_next_page_url(self, response, specialty, current_page):
        """Handle numbered pagination"""
        
        # Look for next page in pagination
        next_selectors = [
            f'a[href*="page={current_page + 1}"]::attr(href)',
            'a:contains("Next")::attr(href)',
            '.pagination .next::attr(href)',
            'a[aria-label="Next"]::attr(href)'
        ]
        
        for selector in next_selectors:
            next_href = response.css(selector).get()
            if next_href:
                return urljoin(response.url, next_href)
        
        # Construct next page URL manually
        if current_page < 5:  # Limit to prevent infinite loops
            current_url = response.url
            if 'page=' in current_url:
                next_url = re.sub(r'page=\d+', f'page={current_page + 1}', current_url)
            else:
                separator = '&' if '?' in current_url else '?'
                next_url = f"{current_url}{separator}page={current_page + 1}"
            
            return next_url
        
        return None
    
    def extract_text_field(self, response, selectors, default=""):
        """Extract text using multiple fallback selectors"""
        
        for selector in selectors:
            try:
                if '::text' in selector:
                    result = response.css(selector).get()
                elif ':contains(' in selector:
                    # Handle text content extraction
                    elements = response.css(selector.split(':contains(')[0])
                    for element in elements:
                        text = element.css('::text').get()
                        if text and selector.split(':contains(')[1].replace(')', '').replace('"', '') in text:
                            result = text
                            break
                    else:
                        continue
                else:
                    result = response.css(selector + '::text').get()
                
                if result and result.strip():
                    return result.strip()
                        
            except Exception as e:
                self.logger.debug(f"Selector failed: {selector} - {e}")
                continue
        
        return default
    
    def extract_experience_years(self, text):
        """Extract years of experience from text"""
        if not text or text == "N/A":
            return 0
        
        # Pattern: "37 Years Experience Overall"
        match = re.search(r'(\d+)\s*(?:Years?|Year)\s*(?:Experience|Exp)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern: just numbers followed by year-related words
        match = re.search(r'(\d+)\s*(?:years?|yrs?)', text, re.IGNORECASE)
        if match:
            years = int(match.group(1))
            if 0 <= years <= 60:  # Reasonable range
                return years
        
        return 0
    
    def extract_rating_score(self, text):
        """Extract rating score from text"""
        if not text or text == "N/A":
            return 0.0
        
        # Pattern: "98%" -> convert to 5-point scale
        match = re.search(r'(\d+)%', text)
        if match:
            percentage = int(match.group(1))
            return round((percentage / 100) * 5.0, 1)
        
        # Pattern: direct decimal rating "4.5"
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            return float(match.group(1))
        
        return 0.0
    
    def extract_patient_count(self, text):
        """Extract patient count from text"""
        if not text or text == "N/A":
            return 0
        
        # Pattern: "63 Patient Stories"
        match = re.search(r'(\d+)\s*Patient', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern: just numbers
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        
        return 0
    
    def extract_consultation_fee(self, text):
        """Extract consultation fee from text"""
        if not text or text == "N/A":
            return 0
        
        # Pattern: "₹1000"
        match = re.search(r'₹\s*(\d+)', text)
        if match:
            return int(match.group(1))
        
        # Pattern: just numbers in reasonable fee range
        match = re.search(r'(\d+)', text)
        if match:
            fee = int(match.group(1))
            if 50 <= fee <= 10000:  # Reasonable fee range
                return fee
        
        return 0
    
    def validate_doctor_item(self, item):
        """Validate doctor item against quality rules"""
        
        # Required field validation
        if not item.get('name') or item['name'] == "N/A" or len(item['name'].strip()) < 3:
            return False
        
        # Don't fail validation for missing optional data - just ensure reasonable defaults
        try:
            fee = int(item.get('consultation_fee', 0))
            if fee < 0 or fee > 10000:
                item['consultation_fee'] = 0
                
            experience = int(item.get('year_of_experience', 0))
            if experience < 0 or experience > 50:
                item['year_of_experience'] = 0
                
            rating = float(item.get('dp_score', 0))
            if rating < 0 or rating > 5.0:
                item['dp_score'] = 0.0
                
        except (ValueError, TypeError):
            # Set defaults for invalid numeric values
            item['consultation_fee'] = 0
            item['year_of_experience'] = 0
            item['dp_score'] = 0.0
        
        return True
    
    def log_progress(self):
        """Log detailed progress information"""
        elapsed_time = datetime.now() - self.start_time
        
        if self.scraped_doctors > 0:
            success_rate = (self.scraped_doctors / (self.scraped_doctors + self.failed_extractions)) * 100
            
            self.logger.info(f"PROGRESS: {self.scraped_doctors} doctors extracted ({success_rate:.1f}% success)")
            self.logger.info(f"ELAPSED: {elapsed_time} - Failures: {self.failed_extractions}")
            self.logger.info(f"SPECIALTIES: {len(self.stats['doctors_per_specialty'])} processed")
    
    def handle_error(self, failure):
        """Enhanced error handling with retry logic"""
        request = failure.request
        self.logger.error(f"❌ Request failed: {request.url} - {failure.value}")
        
        # Simple retry with different user agent
        retry_count = request.meta.get('retry_count', 0)
        if retry_count < 2:
            new_request = request.copy()
            new_request.meta['retry_count'] = retry_count + 1
            new_request.headers['User-Agent'] = get_random_user_agent()
            
            return new_request
    
    def closed(self, reason):
        """Final statistics and cleanup"""
        elapsed_time = datetime.now() - self.start_time
        
        self.logger.info("="*60)
        self.logger.info("SIMPLIFIED COMPREHENSIVE SCRAPING COMPLETED")
        self.logger.info("="*60)
        self.logger.info(f"Total doctors scraped: {self.scraped_doctors}")
        self.logger.info(f"Failed extractions: {self.failed_extractions}")
        self.logger.info(f"Total elapsed time: {elapsed_time}")
        self.logger.info(f"Specialties processed: {len(self.stats['doctors_per_specialty'])}")
        
        if self.scraped_doctors > 0:
            success_rate = (self.scraped_doctors / (self.scraped_doctors + self.failed_extractions)) * 100
            self.logger.info(f"Overall success rate: {success_rate:.1f}%")
        
        # Log specialty breakdown
        self.logger.info("\nSpecialty breakdown:")
        for specialty, count in self.stats['doctors_per_specialty'].items():
            pages = self.stats['pages_per_specialty'].get(specialty, 0)
            self.logger.info(f"  {specialty}: {count} doctors ({pages} pages)")
        
        if self.scraped_doctors >= 10:
            self.logger.info("✅ SUCCESS: Proof of concept working!")
        elif self.scraped_doctors >= 1:
            self.logger.info("✅ PARTIAL SUCCESS: Some data extracted")
        else:
            self.logger.warning("⚠️ NEEDS DEBUGGING: No doctors extracted")