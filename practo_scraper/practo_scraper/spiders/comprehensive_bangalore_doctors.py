"""
Enhanced Bangalore Doctors Spider - Comprehensive Implementation
Following the detailed execution plan from the problem statement

Two-Level Scraping Strategy:
Level 1: Specialty Listing Pages (extract doctor profile URLs)
Level 2: Individual Doctor Profiles (extract complete data)

This spider follows the exact URL patterns and field extraction requirements
specified in the comprehensive execution plan.
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
        EXTRACTION_SELECTORS, PAGINATION_SELECTORS, get_random_user_agent,
        get_download_delay, get_timestamp, DATA_VALIDATION_RULES,
        OUTPUT_CONFIG, MONITORING_CONFIG
    )
except ImportError:
    # Fallback configuration
    COMPREHENSIVE_SPECIALTIES = ["Cardiologist", "Dermatologist", "Dentist", "Gynecologist"]
    TARGET_CITY = "Bangalore"
    
    def generate_search_url(specialty, city="Bangalore"):
        query_json = f'[{{"word":"{specialty}","autocompleted":true,"category":"subspeciality"}}]'
        from urllib.parse import quote
        encoded_query = quote(query_json)
        return f"https://www.practo.com/search/doctors?results_type=doctor&q={encoded_query}&city={city}"

from practo_scraper.items import DoctorItem


class ComprehensiveBangaloreDoctorsSpider(scrapy.Spider):
    name = "comprehensive_bangalore_doctors"
    allowed_domains = ["practo.com"]
    
    # Custom settings for anti-detection and respectful scraping
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
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 3600,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
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
        
        self.logger.info(f"Starting comprehensive scraping for {len(COMPREHENSIVE_SPECIALTIES)} specialties")
        self.logger.info(f"Target: {MONITORING_CONFIG.get('expected_total_doctors', 4500)} doctors")
    
    def start_requests(self):
        """
        Phase 2: Generate initial requests for specialty listing pages
        Following the exact URL pattern from problem statement
        """
        for specialty in COMPREHENSIVE_SPECIALTIES:
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
        
        Handles:
        - Doctor profile URL extraction
        - Numbered pagination
        - Progress monitoring
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
            
            # Handle pagination (numbered pages)
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
    
    def parse_doctor_profile(self, response):
        """
        Level 2: Extract complete doctor information from individual profiles
        
        Extracts all 11 required fields as specified in problem statement:
        1. name, 2. speciality, 3. degree, 4. year_of_experience,
        5. location, 6. city, 7. dp_score, 8. npv, 9. consultation_fee,
        10. profile_url, 11. scraped_at
        """
        specialty = response.meta['specialty']
        city = response.meta['city']
        
        try:
            # Create doctor item
            item = DoctorItem()
            
            # Field 1: name
            item['name'] = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['name'], 
                default="N/A", field_name="name"
            )
            
            # Field 2: speciality (inherit from search)
            item['speciality'] = specialty
            
            # Field 3: degree
            item['degree'] = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['degree'],
                default="Not Specified", field_name="degree"
            )
            
            # Field 4: year_of_experience
            experience_text = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['experience'],
                default="0", field_name="experience"
            )
            item['year_of_experience'] = self.extract_experience_years(experience_text)
            
            # Field 5: location
            item['location'] = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['location'],
                default=city, field_name="location"
            )
            
            # Field 6: city (hardcoded as per requirement)
            item['city'] = city
            
            # Field 7: dp_score (rating)
            rating_text = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['rating'],
                default="0.0", field_name="rating"
            )
            item['dp_score'] = self.extract_rating_score(rating_text)
            
            # Field 8: npv (patient stories)
            patient_text = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['patient_stories'],
                default="0", field_name="patient_stories"
            )
            item['npv'] = self.extract_patient_count(patient_text)
            
            # Field 9: consultation_fee
            fee_text = self.extract_field_with_fallbacks(
                response, EXTRACTION_SELECTORS['consultation_fee'],
                default="0", field_name="consultation_fee"
            )
            item['consultation_fee'] = self.extract_consultation_fee(fee_text)
            
            # Field 10: profile_url
            item['profile_url'] = response.url
            
            # Field 11: scraped_at
            item['scraped_at'] = datetime.now().isoformat()
            
            # Validate and yield item if it meets quality standards
            if self.validate_doctor_item(item):
                self.scraped_doctors += 1
                
                # Progress logging
                if self.scraped_doctors % MONITORING_CONFIG.get('progress_log_interval', 50) == 0:
                    self.log_progress()
                
                yield item
                
                self.logger.info(f"Successfully extracted: {item['name']} - {specialty}")
            else:
                self.failed_extractions += 1
                self.logger.warning(f"Failed validation for profile: {response.url}")
                
        except Exception as e:
            self.failed_extractions += 1
            self.logger.error(f"Error extracting doctor profile {response.url}: {str(e)}")
    
    def extract_doctor_urls(self, response):
        """Extract doctor profile URLs from listing page"""
        doctor_urls = []
        
        # Multiple selectors to find doctor profile links
        selectors = [
            'a[href*="/doctor/"]',
            'a[href*="/bangalore/doctor/"]',
            '.doctor-card a[href*="/doctor/"]',
            '[data-qa-id="doctor_card"] a[href*="/doctor/"]',
            '.listing-item a[href*="/doctor/"]'
        ]
        
        for selector in selectors:
            links = response.css(selector)
            for link in links:
                href = link.attrib.get('href')
                if href and '/doctor/' in href:
                    full_url = urljoin(response.url, href)
                    if full_url not in doctor_urls:
                        doctor_urls.append(full_url)
        
        return doctor_urls
    
    def get_next_page_url(self, response, specialty, current_page):
        """Handle numbered pagination as specified in problem statement"""
        
        # Look for numbered pagination links
        next_page_selectors = [
            f'a[href*="page={current_page + 1}"]',
            f'a:contains("{current_page + 1}")',
            '.pagination a[data-page="{}"]'.format(current_page + 1),
            '.page-link:contains("Next")',
            'a[aria-label="Next"]'
        ]
        
        for selector in next_page_selectors:
            next_link = response.css(selector).get()
            if next_link:
                href = response.css(selector).attrib.get('href')
                if href:
                    return urljoin(response.url, href)
        
        # Alternative: construct next page URL manually
        if current_page < 20:  # Limit to prevent infinite loops
            current_url = response.url
            if 'page=' in current_url:
                # Replace existing page parameter
                next_url = re.sub(r'page=\d+', f'page={current_page + 1}', current_url)
            else:
                # Add page parameter
                separator = '&' if '?' in current_url else '?'
                next_url = f"{current_url}{separator}page={current_page + 1}"
            
            return next_url
        
        return None
    
    def extract_field_with_fallbacks(self, response, selectors, default="N/A", field_name=""):
        """Extract field using multiple fallback selectors"""
        
        for selector in selectors:
            try:
                # Try CSS selector first
                result = response.css(selector + '::text').get()
                if result and result.strip():
                    return result.strip()
                
                # Try with inner text
                result = response.css(selector).get()
                if result:
                    text = re.sub(r'<[^>]+>', '', result).strip()
                    if text:
                        return text
                        
            except Exception as e:
                self.logger.debug(f"Selector failed for {field_name}: {selector} - {e}")
                continue
        
        return default
    
    def extract_experience_years(self, text):
        """Extract years of experience from text"""
        if not text or text == "N/A":
            return 0
        
        # Pattern: "37 Years Experience Overall"
        match = re.search(r'(\d+)\s*(?:Years?|Year)\s*Experience', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Pattern: just numbers
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        
        return 0
    
    def extract_rating_score(self, text):
        """Extract rating score from text (convert percentage to 5-point scale)"""
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
        
        # Pattern: just numbers
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        
        return 0
    
    def validate_doctor_item(self, item):
        """Validate doctor item against quality rules"""
        
        # Required field validation
        if not item.get('name') or item['name'] == "N/A" or len(item['name'].strip()) < 3:
            return False
        
        # Numeric field validation
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
        total_expected = MONITORING_CONFIG.get('expected_total_doctors', 4500)
        
        if self.scraped_doctors > 0:
            success_rate = (self.scraped_doctors / (self.scraped_doctors + self.failed_extractions)) * 100
            
            # Calculate ETA
            rate_per_second = self.scraped_doctors / elapsed_time.total_seconds()
            remaining_doctors = total_expected - self.scraped_doctors
            eta_seconds = remaining_doctors / rate_per_second if rate_per_second > 0 else 0
            eta_hours = eta_seconds / 3600
            
            self.logger.info(f"PROGRESS: {self.scraped_doctors}/{total_expected} doctors ({(self.scraped_doctors/total_expected)*100:.1f}%)")
            self.logger.info(f"SUCCESS RATE: {success_rate:.1f}% - Failed extractions: {self.failed_extractions}")
            self.logger.info(f"ELAPSED TIME: {elapsed_time} - ETA: {eta_hours:.1f} hours")
            self.logger.info(f"SPECIALTIES: {len(self.stats['doctors_per_specialty'])} processed")
    
    def handle_error(self, failure):
        """Enhanced error handling with retry logic"""
        request = failure.request
        self.logger.error(f"Request failed: {request.url} - {failure.value}")
        
        # Implement exponential backoff for retries
        retry_count = request.meta.get('retry_count', 0)
        if retry_count < 3:
            delay = (2 ** retry_count) * random.uniform(1, 3)
            self.logger.info(f"Retrying in {delay:.1f} seconds (attempt {retry_count + 1})")
            
            # Create new request with increased retry count
            new_request = request.copy()
            new_request.meta['retry_count'] = retry_count + 1
            new_request.headers['User-Agent'] = get_random_user_agent()
            
            return new_request
    
    def closed(self, reason):
        """Final statistics and cleanup"""
        elapsed_time = datetime.now() - self.start_time
        
        self.logger.info("="*60)
        self.logger.info("COMPREHENSIVE SCRAPING COMPLETED")
        self.logger.info("="*60)
        self.logger.info(f"Total doctors scraped: {self.scraped_doctors}")
        self.logger.info(f"Failed extractions: {self.failed_extractions}")
        self.logger.info(f"Total elapsed time: {elapsed_time}")
        self.logger.info(f"Specialties processed: {len(self.stats['doctors_per_specialty'])}")
        self.logger.info(f"Pages processed: {self.stats['total_pages_processed']}")
        
        if self.scraped_doctors > 0:
            success_rate = (self.scraped_doctors / (self.scraped_doctors + self.failed_extractions)) * 100
            self.logger.info(f"Overall success rate: {success_rate:.1f}%")
        
        # Log specialty breakdown
        self.logger.info("\nSpecialty breakdown:")
        for specialty, count in self.stats['doctors_per_specialty'].items():
            pages = self.stats['pages_per_specialty'].get(specialty, 0)
            self.logger.info(f"  {specialty}: {count} doctors ({pages} pages)")
        
        target = MONITORING_CONFIG.get('expected_total_doctors', 4500)
        minimum = MONITORING_CONFIG.get('min_acceptable_doctors', 2000)
        
        if self.scraped_doctors >= target:
            self.logger.info(f"✅ SUCCESS: Exceeded target of {target} doctors!")
        elif self.scraped_doctors >= minimum:
            self.logger.info(f"✅ ACCEPTABLE: Met minimum of {minimum} doctors")
        else:
            self.logger.warning(f"⚠️  BELOW TARGET: Only {self.scraped_doctors} doctors (target: {target})")