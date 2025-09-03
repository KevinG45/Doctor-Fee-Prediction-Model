# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re
import pandas as pd
import os
from datetime import datetime
import logging


class ValidationPipeline:
    """Pipeline to validate scraped items"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Skip only if name is missing (essential field)
        if not adapter.get('name') or not adapter.get('name').strip():
            raise DropItem(f"Missing name in {item}")
            
        # Skip if profile_url is missing (prevents duplicates and identifies unique doctors)
        if not adapter.get('profile_url'):
            raise DropItem(f"Missing profile_url in {item}")
            
        # Don't drop items just because consultation fee is missing - that's what we're trying to fix
        # Instead, set a default value or flag for missing fees
        if not adapter.get('consultation_fee'):
            if hasattr(spider, 'logger') and spider.logger:
                spider.logger.warning(f"Missing consultation fee for {adapter.get('name')} - keeping item anyway")
            adapter['consultation_fee'] = ""  # Set empty string instead of dropping
            
        return item


class CleaningPipeline:
    """Pipeline to clean and normalize scraped data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean name
        if adapter.get('name'):
            adapter['name'] = self.clean_text(adapter['name'])
        
        # Clean and normalize degree
        if adapter.get('degree'):
            adapter['degree'] = self.clean_text(adapter['degree'])
            # Extract the main degree
            adapter['degree'] = self.extract_main_degree(adapter['degree'])
        
        # Clean and extract year of experience 
        if adapter.get('year_of_experience'):
            adapter['year_of_experience'] = self.extract_experience_years(adapter['year_of_experience'])
        
        # Clean and validate location
        if adapter.get('location'):
            cleaned_location = self.clean_text(adapter['location'])
            if self.is_valid_location(cleaned_location):
                adapter['location'] = cleaned_location
            else:
                # If location is garbage, try to extract from google_map_link or fall back to city
                adapter['location'] = self.recover_location_from_map_link(
                    adapter.get('google_map_link'), 
                    adapter.get('city', '')
                )
        
        # Clean and convert dp_score to float
        if adapter.get('dp_score'):
            adapter['dp_score'] = self.clean_score(adapter['dp_score'])
        
        # Clean and extract number from npv (votes)
        if adapter.get('npv'):
            adapter['npv'] = self.extract_votes_count(adapter['npv'])
        
        # Clean and extract consultation fee
        if adapter.get('consultation_fee'):
            adapter['consultation_fee'] = self.extract_fee_amount(adapter['consultation_fee'])
        
        # Clean and validate Google Maps link
        if adapter.get('google_map_link'):
            adapter['google_map_link'] = self.clean_map_link(adapter['google_map_link'])
        
        # Add timestamp
        adapter['scraped_at'] = datetime.now().isoformat()
        
        return item
    
    def clean_text(self, text):
        """Clean text by removing extra whitespace and special characters"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', str(text)).strip()
        return text
    
    def extract_main_degree(self, degree_text):
        """Extract the main degree from degree text"""
        if not degree_text:
            return ""
        
        # Common degrees patterns
        degree_patterns = [
            r'\b(MBBS|MD|MS|BDS|MDS|BAMS|BHMS|BUMS|DNB|DM|MCh|PhD|DSc)\b',
            r'\b(Bachelor|Master|Doctor)\s+of\s+\w+',
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, degree_text, re.IGNORECASE)
            if match:
                return match.group()
        
        # If no pattern matches, return first word that looks like a degree
        words = degree_text.split()
        for word in words:
            if len(word) >= 3 and word.isalpha():
                return word
        
        return degree_text[:50]  # Truncate if too long
    
    def extract_experience_years(self, experience_text):
        """Extract number of years from experience text"""
        if not experience_text:
            return 0
        
        exp_str = str(experience_text).strip()
        
        # Look for clear experience patterns first
        experience_patterns = [
            r'(\d+)(?:\+)?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',  # "5 years of experience"
            r'(?:experience|exp)[\s:]*(\d+)(?:\+)?\s*(?:years?|yrs?)',  # "experience: 5 years"
            r'(\d+)(?:\+)?\s*(?:years?|yrs?)',  # "5 years" (more general)
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, exp_str, re.IGNORECASE)
            if match:
                years = int(match.group(1))
                # Reasonable experience range (0-60 years)
                if 0 <= years <= 60:
                    return years
        
        # If no explicit experience pattern, look for standalone numbers
        # but be more cautious about what qualifies as experience
        if re.search(r'\b(?:experience|exp|years?|yrs?)\b', exp_str, re.IGNORECASE):
            numbers = re.findall(r'\d+', exp_str)
            for num_str in numbers:
                try:
                    num = int(num_str)
                    # Must be reasonable experience range and not a year
                    if 0 <= num <= 60 and not (1900 <= num <= 2024):
                        return num
                except ValueError:
                    continue
        
        return 0
    
    def clean_score(self, score_text):
        """Extract and clean rating score"""
        if not score_text:
            return 0.0
        
        # Extract decimal number
        pattern = r'(\d+\.?\d*)'
        match = re.search(pattern, str(score_text))
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0
    
    def extract_votes_count(self, votes_text):
        """Extract number of votes/reviews"""
        if not votes_text:
            return 0
        
        # Look for patterns like "(123 votes)", "123 patient stories"
        pattern = r'(\d+)(?:\s*(?:votes?|patient|stories|reviews?))?'
        match = re.search(pattern, str(votes_text), re.IGNORECASE)
        
        if match:
            return int(match.group(1))
        
        return 0
    
    def extract_fee_amount(self, fee_text):
        """Extract consultation fee amount"""
        if not fee_text:
            return 0
        
        fee_str = str(fee_text).strip()
        
        # First check if this looks like a year (common confusion with experience)
        if re.match(r'^(19|20)\d{2}$', fee_str):
            # This is likely a year, not a fee
            return 0
        
        # Check for common fee patterns
        fee_patterns = [
            r'[₹$]\s*([0-9,]+)',  # ₹500 or $500 format
            r'([0-9,]+)\s*[₹$]',  # 500₹ format
            r'([0-9,]+)\s*(?:rupees?|rs\.?)',  # 500 rupees format
            r'(?:fee|cost|price)[\s:]*[₹$]?\s*([0-9,]+)',  # fee: 500 format
            r'consultation[\s:]*[₹$]?\s*([0-9,]+)',  # consultation: 500 format
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, fee_str, re.IGNORECASE)
            if match:
                fee_num_str = match.group(1).replace(',', '')
                try:
                    fee_amount = int(fee_num_str)
                    # Reasonable fee range validation (₹50 to ₹10,000)
                    if 50 <= fee_amount <= 10000:
                        return fee_amount
                except ValueError:
                    continue
        
        # Fallback: extract any number that looks like a fee
        numbers = re.findall(r'\d+', fee_str)
        for num_str in numbers:
            try:
                num = int(num_str)
                # Must be in reasonable fee range and not look like a year
                if 50 <= num <= 10000 and not (1900 <= num <= 2024):
                    return num
            except ValueError:
                continue
        
        return 0
    
    def clean_map_link(self, map_link):
        """Clean and validate Google Maps link"""
        if not map_link:
            return ""
        
        map_str = str(map_link).strip()
        
        # Check if it's a valid Google Maps URL
        valid_domains = ['maps.google.com', 'google.com/maps', 'goo.gl/maps']
        if any(domain in map_str for domain in valid_domains):
            # Remove any extra parameters that might cause issues
            if '?' in map_str and '&' in map_str:
                # Keep only essential parameters
                essential_params = ['q', 'll', 'place_id']
                url_parts = map_str.split('?')
                if len(url_parts) == 2:
                    base_url, params = url_parts
                    param_pairs = params.split('&')
                    filtered_params = []
                    for param in param_pairs:
                        if any(essential in param for essential in essential_params):
                            filtered_params.append(param)
                    if filtered_params:
                        return f"{base_url}?{'&'.join(filtered_params)}"
                    else:
                        return base_url
            return map_str
        
        # If not a valid Google Maps link, return empty
        return ""
    
    def is_valid_location(self, location):
        """Check if a location is valid and not HTML garbage"""
        if not location or not location.strip():
            return False
        
        location = location.strip()
        
        # Check for HTML tag patterns (common garbage)
        html_patterns = [
            r'^a,abbr,acronym,address,applet,article',  # Common garbage pattern
            r'[a-z]+,[a-z]+,[a-z]+,[a-z]+',  # Multiple comma-separated lowercase words
            r'^(a|abbr|acronym|address|applet|article|aside|audio|b|big|blockquote)$',  # Single HTML tags
        ]
        
        for pattern in html_patterns:
            if re.search(pattern, location, re.IGNORECASE):
                return False
        
        # Check if it's suspiciously long (garbage data tends to be very long)
        if len(location) > 200:
            return False
            
        # Check if it contains too many commas (likely tag list)
        if location.count(',') > 5:
            return False
        
        # Check if it looks like HTML tags
        if '<' in location or '>' in location:
            return False
        
        return True
    
    def recover_location_from_map_link(self, map_link, city):
        """Try to recover location information from Google Maps link"""
        if not map_link:
            return city or "Location Unknown"
        
        # Try multiple coordinate extraction patterns
        coord_patterns = [
            r'maps/place/(-?\d+\.?\d*),(-?\d+\.?\d*)',  # Original pattern
            r'@(-?\d+\.?\d*),(-?\d+\.?\d*)',            # @lat,lng format
            r'll=(-?\d+\.?\d*),(-?\d+\.?\d*)',          # ll=lat,lng format
            r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)',           # q=lat,lng format
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, str(map_link))
            if match:
                try:
                    lat, lng = float(match.group(1)), float(match.group(2))
                    # Return city with coordinates info
                    return f"{city} ({lat:.3f}, {lng:.3f})"
                except ValueError:
                    continue
        
        # Try to extract place name from URL
        place_patterns = [
            r'maps/place/([^/@]+)',  # Place name after maps/place/
            r'q=([^&@]+)',           # Query parameter
        ]
        
        for pattern in place_patterns:
            match = re.search(pattern, str(map_link))
            if match:
                place_name = match.group(1).replace('+', ' ').replace('%20', ' ')
                if place_name and len(place_name) > 3:
                    return place_name.title()
        
        # If extraction fails, fall back to city
        return city or "Location Unknown"


class CsvExportPipeline:
    """Pipeline to export data to CSV"""
    
    def __init__(self):
        self.items = []
        
    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item
    
    def close_spider(self, spider):
        if self.items:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.items)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/practo_doctors_{timestamp}.csv'
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            spider.logger.info(f'Saved {len(self.items)} items to {filename}')
            
            # Also save to a standard filename for easy access
            df.to_csv('data/latest_doctors_data.csv', index=False, encoding='utf-8')
            spider.logger.info(f'Also saved to data/latest_doctors_data.csv')


from scrapy.exceptions import DropItem
import sqlite3
import os


class DeduplicationPipeline:
    """Pipeline to prevent duplicate doctors based on name and profile URL"""
    
    def __init__(self):
        self.seen_urls = set()
        self.seen_names_cities = set()  # Track name+city combinations
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        profile_url = adapter.get('profile_url', '')
        name = adapter.get('name', '').strip().lower()
        city = adapter.get('city', '').strip().lower()
        
        # Check URL-based duplicates (most reliable)
        if profile_url in self.seen_urls:
            raise DropItem(f"Duplicate URL found: {profile_url}")
        
        # Check name+city combination for additional deduplication
        name_city_key = f"{name}|{city}"
        if name_city_key in self.seen_names_cities:
            spider.logger.warning(f"Potential duplicate doctor found: {name} in {city}")
            # Don't drop, but log for review
        
        # Add to seen sets
        self.seen_urls.add(profile_url)
        self.seen_names_cities.add(name_city_key)
        
        return item


class DatabasePipeline:
    """Pipeline to save data to SQLite database"""
    
    def __init__(self):
        self.db_path = 'data/doctors_database.db'
        
    def open_spider(self, spider):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Connect to database
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        
        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                speciality TEXT,
                degree TEXT,
                year_of_experience TEXT,
                location TEXT,
                city TEXT,
                dp_score TEXT,
                npv TEXT,
                consultation_fee TEXT,
                profile_url TEXT UNIQUE,
                google_map_link TEXT,
                scraped_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
        spider.logger.info(f"Database initialized: {self.db_path}")
    
    def close_spider(self, spider):
        # Get count of records
        self.cursor.execute("SELECT COUNT(*) FROM doctors")
        count = self.cursor.fetchone()[0]
        
        self.connection.close()
        spider.logger.info(f"Database closed. Total records: {count}")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            # Insert or replace record (avoid duplicates based on profile_url)
            self.cursor.execute('''
                INSERT OR REPLACE INTO doctors (
                    name, speciality, degree, year_of_experience, location, city,
                    dp_score, npv, consultation_fee, profile_url, google_map_link, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('name', ''),
                adapter.get('speciality', ''),
                adapter.get('degree', ''),
                adapter.get('year_of_experience', ''),
                adapter.get('location', ''),
                adapter.get('city', ''),
                adapter.get('dp_score', ''),
                adapter.get('npv', ''),
                adapter.get('consultation_fee', ''),
                adapter.get('profile_url', ''),
                adapter.get('google_map_link', ''),
                adapter.get('scraped_at', '')
            ))
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            spider.logger.error(f"Database error: {e}")
            
        return item
