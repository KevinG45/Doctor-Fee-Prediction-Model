"""
Improved Web Scraping Script for Practo Doctor Data
This version fixes the deprecated pandas.append() method and adds better error handling.
"""

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
from datetime import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImprovedPractoScraper:
    """Improved Practo scraper with better error handling and modern pandas usage"""
    
    def __init__(self):
        self.data = []
        self.cities = ['Bangalore', 'Delhi', 'Mumbai']
        self.specialities = [
            'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
            'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
            'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
            'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
            'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
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
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Successfully initialized Chrome driver")
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def scroll_page(self, driver):
        """Scroll page to load all content"""
        try:
            scroll_pause_time = 2
            screen_height = driver.execute_script("return window.screen.height;")
            scroll_count = 1

            while True:
                driver.execute_script(f"window.scrollTo(0, {screen_height}*{scroll_count});")
                scroll_count += 1
                time.sleep(scroll_pause_time)
                
                scroll_height = driver.execute_script("return document.body.scrollHeight;")
                if (screen_height * scroll_count) > scroll_height:
                    break
                    
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def extract_doctor_data(self, soup, city, speciality):
        """Extract doctor data from page soup"""
        doctors_data = []
        
        try:
            postings = soup.find_all('div', class_='u-border-general--bottom')
            logger.info(f"Found {len(postings)} doctor postings for {speciality} in {city}")
            
            for post in postings:
                try:
                    # Get doctor profile link
                    link_elem = post.find('div', class_='listing-doctor-card')
                    if not link_elem:
                        continue
                        
                    link = link_elem.find('a')
                    if not link or not link.get('href'):
                        continue
                        
                    profile_url = 'https://www.practo.com' + link.get('href')
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
        """Scrape individual doctor profile"""
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(profile_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # Extract data with safe fallbacks
            data = {
                'Name': self.safe_extract_text(soup, 'h1', 'c-profile__title u-bold u-d-inlineblock'),
                'Speciality': speciality,
                'Degree': self.safe_extract_text(soup, 'p', 'c-profile__details'),
                'Year_of_experience': self.extract_experience(soup),
                'Location': self.safe_extract_text(soup, 'h4', 'c-profile--clinic__location'),
                'City': city,
                'dp_score': self.safe_extract_text(soup, 'span', 'u-green-text u-bold u-large-font'),
                'npv': self.safe_extract_text(soup, 'span', 'u-smallest-font u-grey_3-text'),
                'consultation_fee': self.extract_consultation_fee(soup),
                'google_map_link': self.extract_google_map_link(soup),
                'profile_url': profile_url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Clean the data
            data = self.clean_data(data)
            
            # Only return if essential fields are present
            if data['Name'] and data['consultation_fee']:
                logger.info(f"Successfully scraped: {data['Name']}")
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
    
    def safe_extract_text(self, soup, tag, class_name):
        """Safely extract text from soup element with multiple fallback selectors"""
        # Try original selector first
        try:
            element = soup.find(tag, class_=class_name)
            if element and element.text.strip():
                return element.text.strip()
        except:
            pass
        
        # For location field, try additional selectors
        if 'location' in class_name.lower():
            location_selectors = [
                ('h4', 'c-profile--clinic__location'),  # Original
                ('div', 'c-profile--clinic__location'),  # Without h4
                ('span', None),  # Search all spans
                ('div', None),   # Search all divs
                ('p', None),     # Search all paragraphs
            ]
            
            for sel_tag, sel_class in location_selectors:
                try:
                    if sel_class:
                        element = soup.find(sel_tag, class_=sel_class)
                    else:
                        # Search all elements of this tag for location-related content
                        elements = soup.find_all(sel_tag)
                        for elem in elements:
                            text = elem.text.strip()
                            if text and any(keyword in text.lower() for keyword in ['bangalore', 'delhi', 'mumbai', 'road', 'area', 'nagar', 'cross']):
                                if len(text) < 100:  # Reasonable length for location
                                    return text
                        continue
                    
                    if element and element.text.strip():
                        return element.text.strip()
                except:
                    continue
        
        # For votes/npv field, try additional selectors
        if 'grey_3-text' in class_name or 'votes' in class_name.lower():
            votes_selectors = [
                ('span', 'u-smallest-font u-grey_3-text'),  # Original
                ('span', None),  # Search all spans
                ('div', None),   # Search all divs
            ]
            
            for sel_tag, sel_class in votes_selectors:
                try:
                    if sel_class:
                        element = soup.find(sel_tag, class_=sel_class)
                        if element and element.text.strip():
                            return element.text.strip()
                    else:
                        # Search all elements for vote-related content
                        elements = soup.find_all(sel_tag)
                        for elem in elements:
                            text = elem.text.strip()
                            if text and any(keyword in text.lower() for keyword in ['votes', 'reviews', 'patients', 'feedback']):
                                if any(char.isdigit() for char in text):
                                    return text
                except:
                    continue
        
        return ""
    
    def extract_experience(self, soup):
        """Extract years of experience with multiple fallback selectors"""
        experience_selectors = [
            ('div', 'c-profile__details'),  # Original approach
            ('*', '*[class*="experience"]'),  # Any element with experience in class
            ('*', '*[class*="years"]'),  # Any element with years in class
            ('span', None),  # All spans to search for text
            ('div', None),  # All divs to search for text
            ('h2', None),  # All h2 to search for text
        ]
        
        # Try specific CSS selectors first
        try:
            elements = soup.find('div', class_='c-profile__details')
            if elements:
                h2_elements = elements.find_all('h2')
                if h2_elements:
                    text = h2_elements[-1].text.strip()
                    if text and ("years" in text.lower() or "experience" in text.lower()):
                        return text
        except:
            pass
        
        # Try alternative selectors
        for tag, class_attr in experience_selectors:
            try:
                if class_attr and class_attr.startswith('*['):
                    # Skip complex selectors for BeautifulSoup
                    continue
                    
                elements = soup.find_all(tag, class_=class_attr) if class_attr else soup.find_all(tag)
                for elem in elements:
                    text = elem.text.strip()
                    if text and ("years" in text.lower() or "experience" in text.lower()):
                        # Check if it contains a number
                        if any(char.isdigit() for char in text):
                            return text
            except:
                continue
        
        # Text-based search as last resort
        try:
            all_text_elements = soup.find_all(text=True)
            for text in all_text_elements:
                text = str(text).strip()
                if text and ("years" in text.lower() or "experience" in text.lower()):
                    if any(char.isdigit() for char in text) and len(text) < 50:  # Reasonable length
                        return text
        except:
            pass
            
        return ""
    
    def extract_consultation_fee(self, soup):
        """Extract consultation fee with fallback options"""
        try:
            # Try striked price first
            fee_elem = soup.find('span', class_='u-strike')
            if fee_elem:
                return fee_elem.text.strip()
            
            # Try alternative selector
            fee_elem = soup.find('div', class_='u-f-right u-large-font u-bold u-valign--middle u-lheight-normal')
            if fee_elem:
                return fee_elem.text.strip()
                
        except:
            pass
        return ""
    
    def extract_google_map_link(self, soup):
        """Extract Google Maps link with multiple fallback selectors"""
        google_map_link = ""
        
        # Try iframe with Google Maps source
        try:
            iframe = soup.find('iframe', src=lambda x: x and 'google.com/maps' in x)
            if iframe:
                return iframe.get('src', '')
        except:
            pass
        
        # Try anchor link to Google Maps
        try:
            anchor = soup.find('a', href=lambda x: x and 'google.com/maps' in x)
            if anchor:
                return anchor.get('href', '')
        except:
            pass
        
        # Try alternative Google Maps patterns
        try:
            iframe = soup.find('iframe', src=lambda x: x and 'maps.google' in x)
            if iframe:
                return iframe.get('src', '')
        except:
            pass
        
        # Try data attributes
        try:
            for attr in ['data-src', 'data-href']:
                element = soup.find(attrs={attr: lambda x: x and 'google.com/maps' in x}) if soup.find(attrs={attr: True}) else None
                if element:
                    return element.get(attr, '')
        except:
            pass
        
        # Look for elements with coordinates in data attributes
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
                # Remove extra whitespace and newlines
                cleaned[key] = re.sub(r'\\s+', ' ', value).strip()
            else:
                cleaned[key] = value
                
        return cleaned
    
    def scrape_all_data(self, max_doctors_per_speciality=None):
        """Main method to scrape all doctor data"""
        logger.info("Starting Practo doctor data scraping...")
        
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
                    time.sleep(3)
                    
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
                    time.sleep(2)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"Error scraping {speciality} in {city}: {e}")
                    if 'driver' in locals():
                        driver.quit()
                    continue
        
        logger.info(f"Scraping completed. Total doctors scraped: {total_doctors}")
        return self.data
    
    def save_to_csv(self, filename=None):
        """Save scraped data to CSV using modern pandas"""
        if not self.data:
            logger.warning("No data to save")
            return
        
        # Create DataFrame using pd.concat instead of deprecated append
        df = pd.DataFrame(self.data)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/improved_practo_data_{timestamp}.csv'
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Data saved to {filename}")
        
        # Print summary
        print(f"\\nScraping Summary:")
        print(f"Total doctors scraped: {len(df)}")
        print(f"Cities covered: {df['City'].nunique()}")
        print(f"Specialities covered: {df['Speciality'].nunique()}")
        print(f"Data saved to: {filename}")
        
        return filename


def main():
    """Main function to run the scraper"""
    try:
        scraper = ImprovedPractoScraper()
        
        # Run scraping (limit for testing)
        scraper.scrape_all_data(max_doctors_per_speciality=5)
        
        # Save data
        scraper.save_to_csv()
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")


if __name__ == "__main__":
    main()