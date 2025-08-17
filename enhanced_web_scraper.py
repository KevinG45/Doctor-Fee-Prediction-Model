#!/usr/bin/env python3
"""
Enhanced Web Scraping Script for Practo Doctor Data
Fixes all identified issues:
1. Empty location and experience fields
2. Missing Google Maps data
3. Duplicate records
4. Improved error handling
5. Better data extraction with multiple fallback selectors
"""

import pandas as pd
import time
import logging
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedPractoScraper:
    """Enhanced Practo scraper with comprehensive data extraction and deduplication"""
    
    def __init__(self):
        self.data = []
        self.seen_doctors = set()  # For deduplication
        self.cities = ['Bangalore']  # Focus on Bangalore
        self.specialities = [
            'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
            'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
            'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
            'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
            'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist',
            'General Physician', 'ENT Specialist', 'Radiologist', 'Pathologist',
            'Anesthesiologist', 'Emergency Medicine Physician', 'Geriatrician',
            'Plastic Surgeon', 'Vascular Surgeon', 'Thoracic Surgeon',
            'Endocrinologist', 'Nephrologist', 'Oncologist', 'Homeopath',
            'Ayurveda', 'Unani', 'Sexologist', 'Cosmetologist'
        ]
        
    def setup_driver(self):
        """Set up Chrome driver with proper options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Successfully initialized Chrome driver")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def generate_doctor_id(self, name, city, speciality):
        """Generate unique ID for deduplication"""
        unique_string = f"{name.lower().strip()}-{city.lower()}-{speciality.lower()}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def scroll_page(self, driver, max_scrolls=10):
        """Enhanced page scrolling to load all content"""
        try:
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            
            while scroll_count < max_scrolls:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Check for "Load More" or "View More" buttons
                try:
                    load_more_buttons = driver.find_elements(By.XPATH, 
                        "//button[contains(text(), 'Load') or contains(text(), 'View') or contains(text(), 'Show')]")
                    if load_more_buttons:
                        for button in load_more_buttons:
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    driver.execute_script("arguments[0].click();", button)
                                    time.sleep(2)
                                    logger.info("Clicked load more button")
                            except:
                                pass
                except:
                    pass
                
                # Calculate new scroll height and compare with last height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_count += 1
                
            logger.info(f"Scrolled {scroll_count} times to load content")
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def extract_doctor_links(self, soup, base_url="https://www.practo.com"):
        """Extract all doctor profile links from search results"""
        links = []
        
        # Multiple selectors for doctor links
        link_selectors = [
            'a[href*="/doctor/"]',
            'a[data-qa-id="doctor_name"]',
            '.listing-item a',
            '.doctor-card a',
            '.info-section a'
        ]
        
        for selector in link_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href and '/doctor/' in href:
                        full_url = urljoin(base_url, href)
                        if full_url not in links:
                            links.append(full_url)
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        logger.info(f"Found {len(links)} doctor profile links")
        return links
    
    def extract_doctor_data(self, soup, city, speciality):
        """Extract doctor data from listing page (basic info only)"""
        doctors_data = []
        
        try:
            # Multiple selectors for doctor cards
            card_selectors = [
                '.listing-item',
                '.doctor-card',
                '.info-section',
                '[data-qa-id="doctor_card"]'
            ]
            
            doctor_cards = []
            for selector in card_selectors:
                cards = soup.select(selector)
                if cards:
                    doctor_cards = cards
                    break
            
            if not doctor_cards:
                logger.warning("No doctor cards found on page")
                return doctors_data
            
            for card in doctor_cards:
                try:
                    # Extract profile link
                    link_elem = card.find('a', href=lambda x: x and '/doctor/' in x)
                    if not link_elem:
                        continue
                    
                    profile_url = 'https://www.practo.com' + link_elem.get('href')
                    
                    # Extract basic info from card
                    doctor_data = self.scrape_doctor_profile(profile_url, city, speciality)
                    if doctor_data:
                        doctors_data.append(doctor_data)
                        
                except Exception as e:
                    logger.warning(f"Error extracting doctor data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in extract_doctor_data: {e}")
            
        return doctors_data
    
    def scrape_doctor_profile(self, profile_url, city, speciality):
        """Enhanced individual doctor profile scraping"""
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(profile_url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Extract comprehensive data
            data = {
                'name': self.extract_doctor_name(soup),
                'speciality': speciality,
                'degree': self.extract_degree(soup),
                'year_of_experience': self.extract_experience(soup),
                'location': self.extract_location(soup),
                'city': city,
                'dp_score': self.extract_rating(soup),
                'npv': self.extract_votes(soup),
                'consultation_fee': self.extract_consultation_fee(soup),
                'google_map_link': self.extract_google_map_link(soup),
                'profile_url': profile_url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Clean the data
            data = self.clean_data(data)
            
            # Generate unique ID for deduplication
            doctor_id = self.generate_doctor_id(data['name'], data['city'], data['speciality'])
            
            # Check for duplicates
            if doctor_id in self.seen_doctors:
                logger.info(f"Skipping duplicate doctor: {data['name']}")
                return None
            
            # Only return if essential fields are present
            if data['name'] and (data['consultation_fee'] or data['location']):
                self.seen_doctors.add(doctor_id)
                logger.info(f"Successfully scraped: {data['name']} - {data['location']}")
                return data
            else:
                logger.warning(f"Incomplete data for profile: {profile_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def extract_doctor_name(self, soup):
        """Extract doctor name with multiple fallback selectors"""
        name_selectors = [
            'h1.c-profile__title',
            'h1[data-qa-id="doctor_name"]',
            '.doctor-name h1',
            '.profile-title h1',
            'h1',
            '.doctor-name',
            '.profile-name'
        ]
        
        for selector in name_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    name = element.text.strip()
                    # Clean up the name
                    name = re.sub(r'\s+', ' ', name)
                    return name
            except:
                continue
        
        return ""
    
    def extract_degree(self, soup):
        """Extract doctor degree with multiple selectors"""
        degree_selectors = [
            '.c-profile__details p',
            '.degree',
            '.qualification',
            '[data-qa-id="doctor_degree"]',
            '.doctor-qualifications'
        ]
        
        for selector in degree_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.text.strip()
                    # Look for degree patterns
                    if any(degree in text.upper() for degree in ['MBBS', 'BDS', 'MD', 'MS', 'BHMS', 'BAMS']):
                        return text
            except:
                continue
        
        return ""
    
    def extract_experience(self, soup):
        """Enhanced experience extraction with multiple patterns"""
        experience_patterns = [
            r'(\d+)\s*years?\s*of\s*experience',
            r'(\d+)\s*years?\s*experience',
            r'(\d+)\s*yrs?\s*experience',
            r'experience:?\s*(\d+)\s*years?',
            r'(\d+)\+?\s*years?'
        ]
        
        # Try specific selectors first
        experience_selectors = [
            '.c-profile__details h2',
            '[data-qa-id="doctor_experience"]',
            '.experience',
            '.years-experience',
            '.doctor-experience'
        ]
        
        for selector in experience_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.text.strip().lower()
                    for pattern in experience_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            return f"{match.group(1)} years"
            except:
                continue
        
        # Search in all text content
        try:
            page_text = soup.get_text().lower()
            for pattern in experience_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return f"{match.group(1)} years"
        except:
            pass
        
        return ""
    
    def extract_location(self, soup):
        """Enhanced location extraction with multiple strategies"""
        location_selectors = [
            '.c-profile--clinic__location',
            '[data-qa-id="doctor_location"]',
            '.clinic-location',
            '.location',
            '.address',
            '.clinic-address'
        ]
        
        # Try specific selectors
        for selector in location_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    location = element.text.strip()
                    if len(location) > 5 and len(location) < 200:  # Reasonable length
                        return location
            except:
                continue
        
        # Search for Bangalore-specific locations
        location_keywords = [
            'koramangala', 'indiranagar', 'whitefield', 'electronic city', 'jp nagar',
            'btm layout', 'jayanagar', 'rajajinagar', 'malleshwaram', 'basavanagudi',
            'marathahalli', 'hebbal', 'bannerghatta', 'ulsoor', 'richmond town',
            'mg road', 'brigade road', 'cunningham road', 'commercial street',
            'vijayanagar', 'yeshwanthpur', 'peenya', 'rt nagar', 'hsr layout',
            'sarjapur', 'bellandur', 'domlur', 'frazer town', 'banaswadi'
        ]
        
        try:
            all_text = soup.get_text().lower()
            for keyword in location_keywords:
                if keyword in all_text:
                    # Find the context around the keyword
                    context_start = max(0, all_text.find(keyword) - 50)
                    context_end = min(len(all_text), all_text.find(keyword) + 50)
                    context = all_text[context_start:context_end]
                    
                    # Extract a reasonable location string
                    lines = context.split('\n')
                    for line in lines:
                        if keyword in line and len(line.strip()) > 5 and len(line.strip()) < 100:
                            return line.strip().title()
        except:
            pass
        
        return ""
    
    def extract_rating(self, soup):
        """Extract doctor rating/score"""
        rating_selectors = [
            '.u-green-text.u-bold',
            '[data-qa-id="doctor_score"]',
            '.rating',
            '.score',
            '.doctor-rating'
        ]
        
        for selector in rating_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    rating_text = element.text.strip()
                    # Extract number
                    rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                    if rating_match:
                        return float(rating_match.group(1))
            except:
                continue
        
        return ""
    
    def extract_votes(self, soup):
        """Extract number of patient votes/reviews"""
        votes_selectors = [
            '.u-smallest-font.u-grey_3-text',
            '[data-qa-id="doctor_votes"]',
            '.votes',
            '.reviews-count',
            '.patient-count'
        ]
        
        for selector in votes_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    votes_text = element.text.strip()
                    # Extract number
                    votes_match = re.search(r'(\d+)', votes_text)
                    if votes_match:
                        return int(votes_match.group(1))
            except:
                continue
        
        return 0
    
    def extract_consultation_fee(self, soup):
        """Enhanced consultation fee extraction"""
        fee_selectors = [
            '.u-strike',
            '[data-qa-id="consultation_fee"]',
            '.fee',
            '.consultation-fee',
            '.price'
        ]
        
        for selector in fee_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    fee_text = element.text.strip()
                    # Extract number
                    fee_match = re.search(r'₹?(\d+)', fee_text)
                    if fee_match:
                        return int(fee_match.group(1))
            except:
                continue
        
        # Search in all text for fee patterns
        try:
            page_text = soup.get_text()
            fee_patterns = [
                r'₹\s*(\d+)',
                r'fee:?\s*₹?\s*(\d+)',
                r'consultation:?\s*₹?\s*(\d+)',
                r'charges?:?\s*₹?\s*(\d+)'
            ]
            
            for pattern in fee_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    fee = int(match.group(1))
                    if 100 <= fee <= 5000:  # Reasonable fee range
                        return fee
        except:
            pass
        
        return ""
    
    def extract_google_map_link(self, soup):
        """Enhanced Google Maps link extraction"""
        # Direct iframe search
        try:
            iframe = soup.find('iframe', src=lambda x: x and 'google.com/maps' in x)
            if iframe:
                return iframe.get('src', '')
        except:
            pass
        
        # Direct link search
        try:
            anchor = soup.find('a', href=lambda x: x and 'google.com/maps' in x)
            if anchor:
                return anchor.get('href', '')
        except:
            pass
        
        # Look for map-related buttons or links
        map_keywords = ['map', 'location', 'directions', 'navigate']
        
        try:
            for keyword in map_keywords:
                elements = soup.find_all('a', string=lambda text: text and keyword.lower() in text.lower())
                for element in elements:
                    href = element.get('href', '')
                    if 'google.com/maps' in href or 'maps.google' in href:
                        return href
        except:
            pass
        
        # Look for coordinates in data attributes
        try:
            lat_elem = soup.find(attrs={'data-lat': True})
            lng_elem = soup.find(attrs={'data-lng': True})
            if lat_elem and lng_elem:
                lat = lat_elem.get('data-lat')
                lng = lng_elem.get('data-lng')
                if lat and lng:
                    return f"https://www.google.com/maps?q={lat},{lng}"
        except:
            pass
        
        return ""
    
    def clean_data(self, data):
        """Clean and normalize extracted data"""
        cleaned = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Clean whitespace and normalize
                cleaned_value = ' '.join(value.split())
                # Remove special characters for some fields
                if key in ['name', 'degree']:
                    cleaned_value = re.sub(r'[^\w\s.-]', '', cleaned_value)
                cleaned[key] = cleaned_value
            else:
                cleaned[key] = value
        
        return cleaned
    
    def scrape_all_data(self, max_doctors_per_speciality=None):
        """Main method to scrape all doctor data"""
        logger.info("Starting enhanced Practo doctor data scraping...")
        
        total_doctors = 0
        
        for city in self.cities:
            for speciality in self.specialities:
                try:
                    logger.info(f"Scraping {speciality} in {city}")
                    
                    # Build search URL
                    search_query = f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]'
                    url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
                    
                    driver = self.setup_driver()
                    driver.get(url)
                    time.sleep(5)
                    
                    # Scroll to load all doctors
                    self.scroll_page(driver)
                    
                    # Extract data
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    doctors_data = self.extract_doctor_data(soup, city, speciality)
                    
                    # Add to main data list
                    if max_doctors_per_speciality:
                        doctors_data = doctors_data[:max_doctors_per_speciality]
                    
                    self.data.extend(doctors_data)
                    total_doctors += len(doctors_data)
                    
                    logger.info(f"Scraped {len(doctors_data)} doctors for {speciality} in {city}")
                    
                    driver.quit()
                    time.sleep(3)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"Error scraping {speciality} in {city}: {e}")
                    if 'driver' in locals():
                        driver.quit()
                    continue
        
        logger.info(f"Scraping completed. Total doctors scraped: {total_doctors}")
        logger.info(f"Unique doctors (after deduplication): {len(self.seen_doctors)}")
        return self.data
    
    def save_to_csv(self, filename=None):
        """Save scraped data to CSV using modern pandas"""
        if not self.data:
            logger.warning("No data to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bangalore_doctors_enhanced_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(self.data)
            
            # Remove any remaining duplicates based on name + location
            df = df.drop_duplicates(subset=['name', 'location', 'speciality'], keep='first')
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Data saved to {filename}")
            logger.info(f"Total records: {len(df)}")
            
            # Data quality report
            self.generate_quality_report(df)
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def generate_quality_report(self, df):
        """Generate data quality report"""
        logger.info("\n=== DATA QUALITY REPORT ===")
        logger.info(f"Total records: {len(df)}")
        
        for column in df.columns:
            empty_count = df[column].isna().sum() + (df[column] == '').sum()
            filled_percentage = ((len(df) - empty_count) / len(df)) * 100
            logger.info(f"{column}: {filled_percentage:.1f}% filled ({len(df) - empty_count}/{len(df)})")
        
        # Check for Google Maps data
        maps_count = df['google_map_link'].apply(lambda x: bool(x and x.strip())).sum()
        logger.info(f"Google Maps links: {maps_count} ({(maps_count/len(df)*100):.1f}%)")


def main():
    """Main function to run the enhanced scraper"""
    try:
        scraper = EnhancedPractoScraper()
        
        # For testing, limit to small sample
        logger.info("Starting enhanced scraping with deduplication...")
        scraper.scrape_all_data(max_doctors_per_speciality=10)
        
        # Save data
        scraper.save_to_csv()
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")


if __name__ == "__main__":
    main()