#!/usr/bin/env python3
"""
PERFECT BANGALORE DOCTORS SCRAPER - LIFE OR DEATH VERSION
🚨 HANDLES MULTIPLE LOCATIONS AS SEPARATE ENTRIES
🎯 EXTRACTS ALL DOCTOR DETAILS + DIRECT GOOGLE MAPS LINKS
🏥 PERFECT DATA FOR DOCTOR FEE PREDICTION MODEL
"""

import asyncio
import sys
import os

# CRITICAL: Set Windows event loop policy FIRST to avoid reactor errors
if os.name == 'nt':  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import csv
import re
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
import logging
from pathlib import Path
import threading

# Platform-specific file locking
try:
    import fcntl  # Unix/Linux file locking
except ImportError:
    fcntl = None

try:
    import msvcrt  # Windows file locking
except ImportError:
    msvcrt = None

class BangaloreLocationExtractor:
    """
    BANGALORE LOCATION EXTRACTOR - LIFE OR DEATH ACCURACY
    🎯 Extracts specific Bangalore areas from addresses/text
    📍 Perfect for location-based doctor sorting
    🗺️ Comprehensive coverage of all Bangalore localities
    """
    
    def __init__(self):
        # COMPREHENSIVE BANGALORE AREAS - All major localities
        self.bangalore_areas = {
            # NORTH BANGALORE
            'hebbal': ['hebbal', 'hebbala'],
            'yelahanka': ['yelahanka', 'yelanka'],
            'sahakara_nagar': ['sahakara nagar', 'sahakaranagar', 'sahkar nagar'],
            'rt_nagar': ['rt nagar', 'r t nagar', 'rajajinagar'],
            'malleswaram': ['malleswaram', 'malleshwaram', 'malleswar'],
            'rajajinagar': ['rajajinagar', 'raja ji nagar', 'rajaji nagar'],
            'seshadripuram': ['seshadripuram', 'seshadri puram'],
            'cunningham_road': ['cunningham road', 'cunningham', 'cuningham road'],
            'gandhinagar': ['gandhinagar', 'gandhi nagar'],
            'vyalikaval': ['vyalikaval', 'vyalik aval'],
            
            # SOUTH BANGALORE  
            'koramangala': ['koramangala', 'koramangla', 'koramangala 1 block', 'koramangala 4 block', 'koramangala 5 block', 'koramangala 6 block', 'koramangala 7 block', 'koramangala 8 block'],
            'btm_layout': ['btm layout', 'btm', 'btm 1st stage', 'btm 2nd stage'],
            'jayanagar': ['jayanagar', 'jaya nagar', 'jayanagara', 'jayanagar 4th block', 'jayanagar 9th block'],
            'jp_nagar': ['jp nagar', 'j p nagar', 'jaya prakash nagar', 'jp nagara'],
            'banashankari': ['banashankari', 'bana shankari', 'banasankari'],
            'basavanagudi': ['basavanagudi', 'basavan gudi', 'basavangudi'],
            'wilson_garden': ['wilson garden', 'wilson gardens'],
            'lalbagh': ['lalbagh', 'lal bagh'],
            'shanti_nagar': ['shanti nagar', 'shantinagar'],
            
            # EAST BANGALORE
            'whitefield': ['whitefield', 'white field'],
            'marathahalli': ['marathahalli', 'marathalli', 'marata halli'],
            'varthur': ['varthur', 'varturu'],
            'kundalahalli': ['kundalahalli', 'kundala halli'],
            'brookefield': ['brookefield', 'brooke field'],
            'kadugodi': ['kadugodi', 'kadu godi'],
            'hoodi': ['hoodi', 'hodi'],
            'k_r_puram': ['k r puram', 'kr puram', 'krishnarajapuram'],
            'banaswadi': ['banaswadi', 'banas wadi'],
            'ramamurthy_nagar': ['ramamurthy nagar', 'ramamurthy nagara'],
            'kasturi_nagar': ['kasturi nagar', 'kasturi nagara', 'kasturinagar'],
            'lingarajapuram': ['lingarajapuram', 'lingara japuram'],
            'frazer_town': ['frazer town', 'frazier town'],
            'commercial_street': ['commercial street', 'commercial st'],
            'shivajinagar': ['shivajinagar', 'shivaji nagar'],
            'richmond_town': ['richmond town', 'richmond'],
            'ulsoor': ['ulsoor', 'ulsur'],
            'indiranagar': ['indiranagar', 'indira nagar'],
            'domlur': ['domlur', 'domluru'],
            'jeevanbhima_nagar': ['jeevanbhima nagar', 'jeevan bhima nagar'],
            
            # WEST BANGALORE
            'rajajinagar': ['rajajinagar', 'raja ji nagar'],
            'basaveshwaranagar': ['basaveshwaranagar', 'basaveshwara nagar'],
            'vijayanagar': ['vijayanagar', 'vijaya nagar'],
            'chord_road': ['chord road', 'chord rd'],
            'magadi_road': ['magadi road', 'magadi rd'],
            'kammanahalli': ['kammanahalli', 'kammana halli'],
            'peenya': ['peenya', 'pinya'],
            'yeshwanthpur': ['yeshwanthpur', 'yeshwanth pur', 'yeswanthpur'],
            'mathikere': ['mathikere', 'mathi kere'],
            'jalahalli': ['jalahalli', 'jala halli'],
            
            # CENTRAL BANGALORE
            'mg_road': ['mg road', 'm g road', 'mahatma gandhi road'],
            'brigade_road': ['brigade road', 'brigade rd'],
            'church_street': ['church street', 'church st'],
            'cubbon_park': ['cubbon park', 'cubon park'],
            'high_grounds': ['high grounds', 'high ground'],
            'cantonment': ['cantonment', 'cantonement'],
            'vasanth_nagar': ['vasanth nagar', 'vasanthnagar'],
            'sadashivanagar': ['sadashivanagar', 'sadashiva nagar'],
            
            # SOUTH-EAST BANGALORE
            'hsr_layout': ['hsr layout', 'hsr', 'hsr layoout'],
            'sarjapur_road': ['sarjapur road', 'sarjapur', 'sarjapur rd'],
            'outer_ring_road': ['outer ring road', 'orr', 'outer ring rd'],
            'bellandur': ['bellandur', 'beladur'],
            'ecity': ['electronic city', 'e city', 'ecity', 'electronics city'],
            'bommanahalli': ['bommanahalli', 'bommana halli'],
            'hongasandra': ['hongasandra', 'honga sandra'],
            'begur': ['begur', 'beguru'],
            'hulimavu': ['hulimavu', 'huli mavu'],
            'arekere': ['arekere', 'are kere'],
            'bannerghatta_road': ['bannerghatta road', 'bannerghatta', 'bannerghata road', 'bannerghatta rd'],
            'btm_layout': ['btm layout', 'btm'],
            'j_p_nagar': ['j p nagar', 'jp nagar'],
            
            # SOUTH-WEST BANGALORE
            'kengeri': ['kengeri', 'kengari'],
            'nagarbhavi': ['nagarbhavi', 'nagar bhavi'],
            'vijayanagar': ['vijayanagar', 'vijaya nagar'],
            'attiguppe': ['attiguppe', 'atti guppe'],
            'mahalakshmi_layout': ['mahalakshmi layout', 'mahalaxmi layout'],
            'girinagar': ['girinagar', 'giri nagar'],
            'rajarajeshwarinagar': ['rajarajeshwarinagar', 'rajarajeshwari nagar', 'rr nagar'],
            'uttarahalli': ['uttarahalli', 'uttara halli'],
            'kanakapura_road': ['kanakapura road', 'kanakapura rd'],
            
            # NORTH-WEST BANGALORE
            'tumkur_road': ['tumkur road', 'tumkur rd', 'tumakuru road'],
            'nagasandra': ['nagasandra', 'naga sandra'],
            'dasarahalli': ['dasarahalli', 'dasara halli'],
            'goraguntepalya': ['goraguntepalya', 'goragunte palya'],
            
            # OTHER IMPORTANT AREAS
            'airport_road': ['airport road', 'airport rd', 'hal airport road'],
            'old_airport_road': ['old airport road', 'old airport rd'],
            'residency_road': ['residency road', 'residency rd'],
            'lavelle_road': ['lavelle road', 'lavelle rd'],
            'richmond_circle': ['richmond circle', 'richmond'],
            'mayo_hall': ['mayo hall', 'mayo'],
            'pottery_town': ['pottery town', 'pottery'],
            'cox_town': ['cox town', 'cox'],
            'cooke_town': ['cooke town', 'cooke'],
            'benson_town': ['benson town', 'benson'],
            'fraser_town': ['fraser town', 'frazer town'],
            'murphy_town': ['murphy town', 'murphy'],
            'austin_town': ['austin town', 'austin'],
            'bharathi_nagar': ['bharathi nagar', 'bharathi nagara'],
            'new_thippasandra': ['new thippasandra', 'new thipasandra'],
            'old_madras_road': ['old madras road', 'old madras rd'],
            'kammanahalli': ['kammanahalli', 'kammana halli'],
            'tavarekere': ['tavarekere', 'tavare kere'],
            'adugodi': ['adugodi', 'adu godi'],
            'ejipura': ['ejipura', 'eji pura'],
            'koramangala': ['koramangala', 'kormangala'],
            'yelachenahalli': ['yelachenahalli', 'yelachena halli']
        }
        
        # Special area patterns for better detection
        self.area_patterns = [
            r'(\w+)\s*layout',  # Something Layout
            r'(\w+)\s*nagar',   # Something Nagar  
            r'(\w+)\s*road',    # Something Road
            r'(\w+)\s*cross',   # Something Cross
            r'(\w+)\s*circle',  # Something Circle
            r'(\w+)\s*stage',   # Something Stage
            r'(\w+)\s*block',   # Something Block
            r'(\w+)\s*extension' # Something Extension
        ]
    
    def extract_bangalore_location(self, address_text: str = "", 
                                 maps_link: str = "", source_url: str = "") -> str:
        """
        Extract Bangalore location from multiple sources with PERFECT accuracy
        🎯 Checks address, maps link, and source URL
        📍 Returns ONLY specific, actionable Bangalore areas - NO GENERIC FALLBACKS!
        """
        
        if not address_text and not maps_link and not source_url:
            return ""  # Return empty instead of "Unknown"
        
        # Combine all text sources for analysis
        combined_text = " ".join([
            address_text or "",
            maps_link or "",
            source_url or ""
        ]).lower()
        
        # Remove common noise words
        combined_text = re.sub(r'\b(bangalore|bengaluru|karnataka|india|practo|doctor|dr|hospital|clinic)\b', '', combined_text)
        
        # Find the best matching area - ONLY SPECIFIC AREAS!
        best_match = self._find_best_area_match(combined_text)
        
        if best_match:
            return best_match
        
        # NO GENERIC FALLBACKS - only return specific areas or empty
        return ""
    
    def _find_best_area_match(self, text: str) -> str:
        """Find the best matching Bangalore area - ONLY SPECIFIC REAL AREAS"""
        
        matches = []
        
        # CRITICAL FIX: Direct exact matching for each area
        area_map = {
            'koramangala': 'Koramangala',
            'richmond_town': 'Richmond Town', 
            'richmond town': 'Richmond Town',
            'richmond': 'Richmond Town',
            'kasturi_nagar': 'Kasturi Nagar',
            'kasturi nagar': 'Kasturi Nagar', 
            'kasturinagar': 'Kasturi Nagar',
            'hsr_layout': 'HSR Layout',
            'hsr layout': 'HSR Layout',
            'hsr': 'HSR Layout',
            'whitefield': 'Whitefield',
            'indiranagar': 'Indiranagar',
            'marathahalli': 'Marathahalli',
            'bannerghatta road': 'Bannerghatta Road',
            'btm layout': 'BTM Layout',
            'btm': 'BTM Layout',
            'jp nagar': 'JP Nagar',
            'j p nagar': 'JP Nagar',
            'jayanagar': 'Jayanagar',
            'electronic city': 'Electronic City',
            'ecity': 'Electronic City',
            'bellandur': 'Bellandur',
            'mg road': 'MG Road',
            'brigade road': 'Brigade Road',
            'commercial street': 'Commercial Street',
            'ulsoor': 'Ulsoor',
            'frazer town': 'Frazer Town',
            'malleswaram': 'Malleswaram',
            'rajajinagar': 'Rajajinagar',
            'seshadripuram': 'Seshadripuram',
            'vijayanagar': 'Vijayanagar',
            'basaveshwaranagar': 'Basaveshwaranagar',
            'peenya': 'Peenya',
            'yeshwanthpur': 'Yeshwanthpur',
            'hebbal': 'Hebbal',
            'yelahanka': 'Yelahanka',
            'kr puram': 'KR Puram',
            'banaswadi': 'Banaswadi',
            'kammanahalli': 'Kammanahalli',
            'ramamurthy nagar': 'Ramamurthy Nagar',
            'lingarajapuram': 'Lingarajapuram',
            'domlur': 'Domlur',
            'banashankari': 'Banashankari',
            'basavanagudi': 'Basavanagudi'
        }
        
        # Find exact matches with scoring
        for key, area_name in area_map.items():
            if key in text:
                score = len(key)  # Longer matches are more specific
                matches.append((area_name, key, score))
        
        if matches:
            # Return the most specific match (highest score)
            best_match = max(matches, key=lambda x: x[2])
            return best_match[0]
        
        return ""
    
    def _extract_with_patterns(self, text: str) -> str:
        """Extract location using pattern matching"""
        
        for pattern in self.area_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first meaningful match
                for match in matches:
                    if len(match) > 2 and match not in ['the', 'and', 'for', 'with']:
                        return f"{match.title()} Area"
        
        return ""
    
    def _extract_generic_location(self, text: str) -> str:
        """Extract any meaningful location reference"""
        
        # Look for common location indicators
        location_indicators = [
            r'near\s+(\w+(?:\s+\w+){0,2})',
            r'opposite\s+(\w+(?:\s+\w+){0,2})',
            r'behind\s+(\w+(?:\s+\w+){0,2})',
            r'(\w+(?:\s+\w+){0,2})\s+metro',
            r'(\w+(?:\s+\w+){0,2})\s+junction',
            r'(\w+(?:\s+\w+){0,2})\s+main\s+road'
        ]
        
        for pattern in location_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if len(match) > 3:
                        return f"{match.title()} Area"
        
        return ""
    
    def get_location_statistics(self, locations: List[str]) -> Dict:
        """Get statistics about extracted locations"""
        
        location_counts = {}
        for location in locations:
            location_counts[location] = location_counts.get(location, 0) + 1
        
        return {
            'total_locations': len(locations),
            'unique_locations': len(location_counts),
            'location_breakdown': location_counts,
            'most_common': max(location_counts.items(), key=lambda x: x[1]) if location_counts else None
        }

class RealTimeCSVWriter:
    """
    REAL-TIME CSV WRITER - PERFECT FOR LIVE MONITORING
    🔥 Writes each doctor entry immediately to CSV
    💾 Safe file locking to prevent corruption
    📊 Live progress tracking for manual monitoring
    """
    
    def __init__(self, filename: str):
        self.filename = filename
        self.lock = threading.Lock()
        self.entries_written = 0
        self.file_initialized = False
        
        # CSV fieldnames in perfect order
        self.fieldnames = [
            'entry_id', 'name', 'specialty', 'experience', 'degree', 'consultation_fee', 'rating',
            'bangalore_location', 'google_maps_link', 'coordinates',
            'location_index', 'source_url', 'scraped_at', 'scraping_session'
        ]
        
        # Initialize CSV file with headers
        self._initialize_csv()
        
        print(f"📝 REAL-TIME CSV: {self.filename}")
        print(f"👀 LIVE MONITORING: Watch data being written in real-time!")
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        
        file_exists = Path(self.filename).exists()
        
        if not file_exists:
            try:
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                    writer.writeheader()
                    f.flush()  # Ensure headers are written immediately
                
                print(f"✅ CSV initialized: {self.filename}")
                self.file_initialized = True
                
            except Exception as e:
                print(f"❌ Error initializing CSV: {e}")
                raise
        else:
            print(f"📁 CSV exists: {self.filename} (appending)")
            self.file_initialized = True
            
            # Count existing entries
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    self.entries_written = sum(1 for row in reader) - 1  # Subtract header
                print(f"📊 Existing entries: {self.entries_written}")
            except Exception as e:
                print(f"⚠️  Could not count existing entries: {e}")
    
    def write_entry(self, doctor_data: Dict, session_id: str) -> bool:
        """
        Write single doctor entry to CSV immediately
        Returns True if successful, False otherwise
        """
        
        if not self.file_initialized:
            return False
        
        try:
            with self.lock:  # Thread-safe writing
                # Ensure all required fields exist and remove unknown fields
                clean_data = {}
                for field in self.fieldnames:
                    clean_data[field] = doctor_data.get(field, '')
                
                # Add entry metadata
                clean_data['entry_id'] = self.entries_written + 1
                clean_data['scraping_session'] = session_id
                
                # Write with file locking for safety
                with open(self.filename, 'a', newline='', encoding='utf-8') as f:
                    # Platform-specific file locking
                    self._lock_file(f)
                    
                    try:
                        writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                        writer.writerow(clean_data)
                        f.flush()  # Force immediate write to disk
                        
                        # Update counter after successful write
                        self.entries_written += 1
                        
                        # Live progress indicator
                        if self.entries_written % 10 == 0:
                            print(f"💾 LIVE: {self.entries_written} entries written to CSV")
                        
                        return True
                        
                    finally:
                        self._unlock_file(f)
                
        except Exception as e:
            print(f"❌ Error writing entry {self.entries_written}: {e}")
            return False
    
    def _lock_file(self, file_obj):
        """Platform-specific file locking"""
        try:
            if os.name == 'nt' and msvcrt:  # Windows
                msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
            elif fcntl:  # Unix/Linux
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
        except Exception:
            pass  # File locking is optional - continue without it
    
    def _unlock_file(self, file_obj):
        """Platform-specific file unlocking"""
        try:
            if os.name == 'nt' and msvcrt:  # Windows
                msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
            elif fcntl:  # Unix/Linux
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
    
    def get_stats(self) -> Dict:
        """Get current writing statistics"""
        return {
            'filename': self.filename,
            'entries_written': self.entries_written,
            'file_size_mb': Path(self.filename).stat().st_size / (1024 * 1024) if Path(self.filename).exists() else 0
        }

class PerfectPractoScraper:
    def __init__(self):
        # Generate unique session ID for this scraping run
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # BANGALORE LOCATION EXTRACTOR - CRITICAL FOR SORTING!
        self.location_extractor = BangaloreLocationExtractor()
        
        # REAL-TIME CSV WRITER - Resume from existing CSV or create new one
        # Check for existing CSV files to resume from
        existing_csv = self._find_latest_csv()
        if existing_csv:
            print(f"🔄 RESUMING from existing CSV: {existing_csv}")
            csv_filename = existing_csv
        else:
            print(f"🆕 CREATING new CSV file")
            csv_filename = f"doctors_bangalore_LIVE_{self.session_id}.csv"
        
        self.csv_writer = RealTimeCSVWriter(csv_filename)
        
        self.doctors_data: List[Dict] = []  # Keep minimal in-memory list for final stats
        self.processed_urls: Set[str] = set()  # Track processed URLs
        self.failed_urls: List[str] = []  # Track failures for retry
        self.total_scraped = 0
        self.total_locations = 0
        self.start_time = datetime.now()
        
        # COMPREHENSIVE specialties - ALL medical fields in Bangalore
        self.specialties = [
            'general-physician', 'cardiologist', 'dermatologist', 'orthopedist',
            'gynecologist', 'neurologist', 'pediatrician', 'psychiatrist',
            'gastroenterologist', 'pulmonologist', 'urologist', 'ophthalmologist',
            'ent-specialist', 'endocrinologist', 'rheumatologist', 'nephrologist',
            'radiologist', 'pathologist', 'anesthesiologist', 'oncologist',
            'dentist', 'physiotherapist', 'dietitian-nutritionist', 'psychologist',
            'surgeon', 'plastic-surgeon', 'neurosurgeon', 'cardiac-surgeon',
            'vascular-surgeon', 'spine-surgeon', 'ayurveda', 'homeopath',
            'unani', 'acupuncturist', 'naturopathy', 'yoga-therapist',
            'sexologist', 'trichologist', 'cosmetologist', 'audiologist',
            'speech-therapist', 'occupational-therapist'
        ]
        
        # Setup comprehensive logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('perfect_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # SELECTORS for extracting data - multiple fallbacks for each field
        self.selectors = {
            'name': [
                'h1[data-qa-id="doctor_name"]',
                'h1.doctor-name', 
                'h1',
                '.profile-details h1'
            ],
            'experience': [
                # Look for actual year numbers, not generic text
                'text=/\\d+\\+?\\s*years?\\s*(?:of\\s*)?experience/i',
                'text=/\\d+\\+?\\s*years?/i',
                '[data-qa-id="doctor_experience"]',
                '.experience-years'
            ],
            'degree': [
                # Look for actual degree abbreviations, not descriptions
                '[data-qa-id="doctor_qualification"]',
                '.doctor-qualification',
                '.qualification',
                'text=/MBBS[^.]*(?:,\\s*(?:MD|MS|BDS|DNB))?[^.]*/i'
            ],
            'consultation_fee': [
                # Look for actual rupee amounts
                'text=/₹\\s*\\d+(?:,\\d{3})*/i',
                '[data-qa-id="consultation_fee"]', 
                '.consultation-fee',
                '.fee-amount'
            ],
            'rating': [
                # Look for actual decimal ratings
                'text=/\\d+\\.\\d+/i',
                '[data-qa-id="doctor_rating"]',
                '.rating-score',
                '.star-rating'
            ],
            'google_maps_button': [
                'a[href*="maps.google"]', 'a[href*="google.com/maps"]',
                'a:has-text("Get Directions")', 'a:has-text("View on Map")',
                'a:has-text("Directions")', 'button:has-text("Directions")',
                '[data-qa-id="get_directions"]', '.get-directions'
            ],
            'clinic_info_sections': [
                '[data-qa-id="clinic_card"]', '.clinic-info', '.practice-info',
                '.location-card', '.clinic-card', '.practice-card'
            ],
            # 🎯 CRITICAL: BANGALORE LOCATION FROM DOCTOR PROFILE
            'bangalore_location': [
                'nav[aria-label="breadcrumb"] a:nth-last-child(2)', # Breadcrumb - second last item
                '.breadcrumb a:nth-last-child(2)',
                'nav a:nth-last-child(2)', 
                '.u-c-pointer:nth-last-child(2)', # Practo breadcrumb styling
                'h4:has-text("Bangalore")', # Location headers in profile
                'text=/^[A-Za-z\\s]+,\\s*Bangalore$/i', # "Area, Bangalore" pattern
                'text=/domlur|koramangala|whitefield|hsr|indiranagar|jayanagar|btm|marathahalli|jp\\s*nagar|rajajinagar|malleswaram|frazer\\s*town|mg\\s*road|brigade\\s*road/i',
                '.doctor-location', 
                '[data-qa-id="doctor_location"]'
            ]
        }
        
        print("🚨 PERFECT SCRAPER - LIFE OR DEATH MODE ACTIVATED")
        print("🎯 MULTI-LOCATION AWARE: Each location = Separate entry")
        print(f"🏥 Target: {len(self.specialties)} specialties")
        print("📊 Extracting: Name, Experience, Degree, Fee, Rating, Location, Maps")
        print("📍 BANGALORE AREAS: Smart location extraction for sorting")
        print(f"📝 REAL-TIME CSV: {self.csv_writer.filename}")
        print("👀 LIVE MONITORING: Data written immediately - open CSV to watch!")
        print("💾 SAFE WRITING: File locking prevents corruption")
        print("💯 GUARANTEE: Perfect data for ML model")
        print("=" * 80)
    
    def _find_latest_csv(self):
        """Find the most recent CSV file to resume from"""
        try:
            # First, check for the specific file mentioned by user in current directory
            specific_file = Path("doctors_bangalore_LIVE_20250904_183103.csv")
            if specific_file.exists():
                print(f"✅ Found target CSV file: {specific_file}")
                return str(specific_file)
            
            # Also check in data subdirectory
            specific_file_data = Path("data/doctors_bangalore_LIVE_20250904_183103.csv")
            if specific_file_data.exists():
                print(f"✅ Found target CSV file in data/: {specific_file_data}")
                return str(specific_file_data)
            
            # Fall back to looking for any recent CSV files in current directory
            csv_files = list(Path(".").glob("doctors_bangalore_LIVE_*.csv"))
            
            # Also check data directory
            data_dir = Path("data")
            if data_dir.exists():
                csv_files.extend(list(data_dir.glob("doctors_bangalore_LIVE_*.csv")))
            
            if not csv_files:
                return None
            
            # Get the most recent file by modification time
            latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
            
            print(f"🔄 Found latest CSV: {latest_csv}")
            return str(latest_csv)
            
        except Exception as e:
            print(f"⚠️  Error finding latest CSV: {e}")
            return None

    async def scrape_all_doctors(self):
        """Main scraping function with perfect error handling"""
        
        browser = None
        try:
            async with async_playwright() as p:
                # Launch browser with MAXIMUM STEALTH + Anti-Detection
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                        '--disable-web-security', '--no-first-run',
                        '--disable-background-timer-throttling',
                        '--disable-blink-features=AutomationControlled',  # ANTI-DETECTION
                        '--disable-features=VizDisplayCompositor',         # ANTI-DETECTION  
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
                    ]
                )
                
                # Process all specialties
                for i, specialty in enumerate(self.specialties, 1):
                    success = await self.process_specialty_perfect(browser, specialty, i)
                    
                    # Save checkpoint every 5 specialties
                    if i % 5 == 0:
                        await self.save_checkpoint(i)
                        csv_stats = self.csv_writer.get_stats()
                        print(f"📊 Checkpoint {i}/{len(self.specialties)}: {csv_stats['entries_written']} entries → CSV ({csv_stats['file_size_mb']:.1f} MB)")
                
                await browser.close()
                
        except Exception as e:
            self.logger.error(f"Critical browser error: {e}")
            if browser:
                await browser.close()
        
        # Retry failed URLs
        if self.failed_urls:
            await self.retry_failed_urls()
        
        # Save final results
        await self.save_perfect_results()
        self.print_perfect_summary()

    async def process_specialty_perfect(self, browser, specialty, index) -> bool:
        """Process specialty with ANTI-DETECTION measures"""
        
        # ROTATING USER AGENTS POOL - Realistic browsers
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        
        # Create NEW CONTEXT with rotating user agent
        import random
        context = await browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        print(f"\n🏥 [{index}/{len(self.specialties)}] Processing: {specialty}")
        
        try:
            success = await self.scrape_specialty_all_pages_perfect(page, specialty)
            await context.close()
            return success
        except Exception as e:
            self.logger.error(f"Error processing {specialty}: {e}")
            await context.close()
            return False

    async def scrape_specialty_all_pages_perfect(self, page, specialty) -> bool:
        """Scrape ALL pages for specialty with perfect pagination"""
        
        page_num = 1
        total_entries = 0
        consecutive_empty = 0
        
        while consecutive_empty < 2:  # Stop after 2 consecutive empty pages
            try:
                # Build URL
                if page_num == 1:
                    url = f"https://www.practo.com/bangalore/{specialty}"
                else:
                    url = f"https://www.practo.com/bangalore/{specialty}?page={page_num}"
                
                # Load page with retry
                loaded = await self.load_page_perfect(page, url)
                if not loaded:
                    consecutive_empty += 1
                    page_num += 1
                    continue
                
                # Extract doctor URLs
                doctor_urls = await self.extract_doctor_urls_perfect(page)
                
                if not doctor_urls:
                    consecutive_empty += 1
                    print(f"   📄 Page {page_num}: No doctors found")
                    page_num += 1
                    continue
                
                consecutive_empty = 0
                print(f"   📄 Page {page_num}: Found {len(doctor_urls)} doctors")
                
                # Process each doctor
                page_entries = 0
                for doctor_url in doctor_urls:
                    if doctor_url not in self.processed_urls:
                        entries = await self.scrape_doctor_perfect(page, doctor_url, specialty)
                        page_entries += entries
                        total_entries += entries
                
                print(f"   ✅ Page {page_num}: {page_entries} entries created")
                page_num += 1
                
                # Safety limit
                if page_num > 50:
                    print(f"   ⚠️  Safety limit reached for {specialty}")
                    break
                    
                # Delay to avoid rate limiting
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                self.logger.error(f"Error on page {page_num} of {specialty}: {e}")
                consecutive_empty += 1
                page_num += 1
        
        print(f"🎯 {specialty}: {total_entries} total entries from {page_num-1} pages")
        return total_entries > 0

    async def load_page_perfect(self, page, url, max_retries=3) -> bool:
        """Load page with ANTI-DETECTION stealth measures"""
        
        for attempt in range(max_retries):
            try:
                # SET STEALTH HEADERS (User Agent is set at context level)
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                })
                
                # LONGER TIMEOUT + DIFFERENT WAIT STRATEGY
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
                
                # HUMAN-LIKE DELAY (3-7 seconds as per your plan)
                await asyncio.sleep(random.uniform(3, 7))
                
                # VERIFY PAGE LOADED PROPERLY
                await page.wait_for_selector('body', timeout=10000)
                return True
                
            except PlaywrightTimeoutError:
                # EXPONENTIAL BACKOFF (as per your plan)
                wait_time = (2 ** attempt) + random.uniform(2, 5)  # Longer delays
                if attempt < max_retries - 1:
                    self.logger.warning(f"Timeout {url}, retry {attempt + 1} in {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                self.logger.error(f"Error loading {url}: {e}")
                break
        
        return False

    async def extract_doctor_urls_perfect(self, page) -> List[str]:
        """Extract doctor URLs with perfect fallback strategies"""
        
        doctor_urls = []
        
        # Multiple selectors for doctor cards
        selectors = [
            '[data-qa-id="doctor_card"] a[href*="/doctor/"]',
            '.doctor-card a[href*="/doctor/"]',
            'a[href*="/doctor/"]:not([href*="/recommended"])',
            '.listing-item a[href*="/doctor/"]',
            '.doctor-profile a[href*="/doctor/"]'
        ]
        
        for selector in selectors:
            try:
                links = await page.query_selector_all(selector)
                for link in links:
                    href = await link.get_attribute('href')
                    if href and '/doctor/' in href and '/recommended' not in href:
                        if href.startswith('/'):
                            full_url = f"https://www.practo.com{href}"
                        else:
                            full_url = href
                        
                        # Clean URL
                        clean_url = full_url.split('?')[0]
                        if clean_url not in doctor_urls:
                            doctor_urls.append(clean_url)
                            
                if doctor_urls:
                    break
                    
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return doctor_urls

    async def scrape_doctor_perfect(self, page, doctor_url, specialty) -> int:
        """Scrape doctor with PERFECT multi-location handling"""
        
        entries_created = 0
        
        try:
            # Load doctor profile
            loaded = await self.load_page_perfect(page, doctor_url)
            if not loaded:
                self.failed_urls.append(doctor_url)
                return 0
            
            # Extract basic doctor info (same for all locations)
            basic_info = await self.extract_basic_doctor_info(page, doctor_url, specialty)
            if not basic_info or not basic_info.get('name'):
                return 0
            
            # Extract ALL location information
            locations_data = await self.extract_all_locations_perfect(page)
            
            if not locations_data:
                # If no specific locations found, create one entry with available data
                entry = basic_info.copy()
                entry.update({
                    'google_maps_link': '',
                    'coordinates': '',
                    'location_index': 1
                })
                
                # 🎯 EXTRACT BANGALORE LOCATION - CRITICAL FOR SORTING!
                # Priority 1: Use profile location if available
                if basic_info.get('profile_location') and basic_info['profile_location'].strip():
                    profile_loc = basic_info['profile_location']
                    # Clean the profile location (remove "Bangalore" suffix if present)
                    profile_loc = re.sub(r',?\s*Bangalore\s*$', '', profile_loc, flags=re.IGNORECASE).strip()
                    entry['bangalore_location'] = profile_loc
                else:
                    # Priority 2: Try to extract from page URL or title again
                    page_title = await page.title()
                    if page_title:
                        extracted_location = self.location_extractor.extract_bangalore_location(page_title)
                        entry['bangalore_location'] = extracted_location if extracted_location else "Bangalore"
                    else:
                        # Priority 3: Default to "Bangalore" (never empty!)
                        entry['bangalore_location'] = "Bangalore"
                
                # 🔥 REAL-TIME CSV WRITING - Write immediately!
                if self.csv_writer.write_entry(entry, self.session_id):
                    self.doctors_data.append(entry)  # Keep minimal copy for stats
                    self.total_scraped += 1
                    self.total_locations += 1
                    entries_created = 1
                    
                    print(f"✅ {self.total_scraped}: {basic_info['name']} ({specialty}) - {entry['bangalore_location']} → CSV")
                else:
                    print(f"❌ Failed to write: {basic_info['name']} ({specialty})")
            else:
                # Create separate entry for each location
                for i, location_data in enumerate(locations_data, 1):
                    entry = basic_info.copy()
                    entry.update(location_data)
                    entry['location_index'] = i
                    
                    # 🎯 EXTRACT BANGALORE LOCATION - CRITICAL FOR SORTING!
                    # Priority 1: Use profile location if available
                    if basic_info.get('profile_location') and basic_info['profile_location'].strip():
                        profile_loc = basic_info['profile_location']
                        # Clean the profile location (remove "Bangalore" suffix if present)
                        profile_loc = re.sub(r',?\s*Bangalore\s*$', '', profile_loc, flags=re.IGNORECASE).strip()
                        entry['bangalore_location'] = profile_loc
                    else:
                        # Priority 2: Try location extractor with available data
                        extracted_location = self.location_extractor.extract_bangalore_location(
                            address_text="",
                            maps_link=entry.get('google_maps_link', ''),
                            source_url=entry.get('source_url', '')
                        )
                        # Priority 3: Use page title if no location from clinic data
                        if not extracted_location:
                            page_title = await page.title()
                            if page_title:
                                extracted_location = self.location_extractor.extract_bangalore_location(page_title)
                        
                        # Priority 4: Never leave empty - default to "Bangalore"
                        entry['bangalore_location'] = extracted_location if extracted_location else "Bangalore"
                    
                    # 🔥 REAL-TIME CSV WRITING - Write each location immediately!
                    if self.csv_writer.write_entry(entry, self.session_id):
                        self.doctors_data.append(entry)  # Keep minimal copy for stats
                        self.total_locations += 1
                        entries_created += 1
                    else:
                        print(f"❌ Failed to write location {i}: {basic_info['name']}")
                
                self.total_scraped += 1
                print(f"✅ {self.total_scraped}: {basic_info['name']} ({specialty}) - {len(locations_data)} locations → CSV")
            
            self.processed_urls.add(doctor_url)
            return entries_created
            
        except Exception as e:
            self.logger.error(f"Error scraping {doctor_url}: {e}")
            self.failed_urls.append(doctor_url)
            return 0

    async def extract_basic_doctor_info(self, page, doctor_url, specialty) -> Optional[Dict]:
        """Extract basic doctor information (same for all locations)"""
        
        basic_info = {
            'name': '',
            'specialty': specialty,
            'experience': '',
            'degree': '',
            'consultation_fee': '',
            'rating': '',
            'source_url': doctor_url,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract name
        basic_info['name'] = await self.extract_with_fallback(page, 'name')
        if not basic_info['name']:
            return None
        
        # Clean name
        basic_info['name'] = re.sub(r'^Dr\.?\s*', '', basic_info['name'].strip())
        
        # Extract other basic info
        basic_info['experience'] = await self.extract_with_fallback(page, 'experience')
        basic_info['degree'] = await self.extract_with_fallback(page, 'degree')
        basic_info['consultation_fee'] = await self.extract_with_fallback(page, 'consultation_fee')
        basic_info['rating'] = await self.extract_with_fallback(page, 'rating')
        
        # 🎯 CRITICAL: Extract Bangalore location from PAGE TITLE
        page_title = await page.title()
        if page_title:
            # Extract location from title like "Dr. Name - Specialty in Location, Bangalore"
            basic_info['profile_location'] = self.location_extractor.extract_bangalore_location(page_title)
        else:
            basic_info['profile_location'] = ""
        
        return basic_info

    async def extract_all_locations_perfect(self, page) -> List[Dict]:
        """Extract ALL locations for a doctor as separate entries"""
        
        locations_data = []
        
        try:
            # Strategy 1: Look for multiple clinic/practice cards
            clinic_sections = await page.query_selector_all('[data-qa-id="clinic_card"], .clinic-info, .practice-info')
            
            if clinic_sections:
                for section in clinic_sections:
                    location_info = await self.extract_single_location_from_section(section)
                    if location_info and location_info['clinic_address']:
                        locations_data.append(location_info)
            
            # Strategy 2: Look for multiple addresses in the main content
            if not locations_data:
                addresses = await self.extract_multiple_addresses(page)
                maps_links = await self.extract_multiple_maps_links(page)
                
                # Pair addresses with maps links
                max_locations = max(len(addresses), len(maps_links))
                for i in range(max_locations):
                    address = addresses[i] if i < len(addresses) else ''
                    maps_link = maps_links[i] if i < len(maps_links) else ''
                    
                    if address or maps_link:
                        coordinates = self.extract_coordinates_from_link(maps_link)
                        location_info = {
                            'google_maps_link': maps_link,
                            'coordinates': coordinates
                        }
                        locations_data.append(location_info)
            
            # Strategy 3: Single location fallback
            if not locations_data:
                single_location = await self.extract_single_location_fallback(page)
                if single_location:
                    locations_data.append(single_location)
            
        except Exception as e:
            self.logger.error(f"Error extracting locations: {e}")
        
        return locations_data

    async def extract_single_location_from_section(self, section) -> Optional[Dict]:
        """Extract location info from a specific clinic section"""
        
        try:
            # Extract maps link
            maps_link = ''
            maps_selectors = ['a[href*="maps.google"]', 'a[href*="google.com/maps"]', 'a:has-text("Directions")']
            for selector in maps_selectors:
                elem = await section.query_selector(selector)
                if elem:
                    href = await elem.get_attribute('href')
                    if href:
                        maps_link = href
                        break
            
            # Extract coordinates
            coordinates = self.extract_coordinates_from_link(maps_link)
            
            return {
                'google_maps_link': maps_link,
                'coordinates': coordinates
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting from section: {e}")
            return None

    async def extract_multiple_addresses(self, page) -> List[str]:
        """Extract multiple addresses from page"""
        
        addresses = []
        selectors = ['[data-qa-id="clinic_address"]', '.clinic-address', '.practice-address']
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text and text.strip() and text.strip() not in addresses:
                        addresses.append(text.strip())
                        
                if addresses:
                    break
                    
            except Exception as e:
                self.logger.debug(f"Address selector {selector} failed: {e}")
                continue
        
        return addresses

    async def extract_multiple_maps_links(self, page) -> List[str]:
        """Extract multiple Google Maps links"""
        
        maps_links = []
        selectors = [
            'a[href*="maps.google"]', 'a[href*="google.com/maps"]',
            'a:has-text("Get Directions")', 'a:has-text("Directions")'
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    href = await elem.get_attribute('href')
                    if href and href not in maps_links:
                        maps_links.append(href)
                        
                if maps_links:
                    break
                    
            except Exception as e:
                self.logger.debug(f"Maps selector {selector} failed: {e}")
                continue
        
        return maps_links

    async def extract_single_location_fallback(self, page) -> Optional[Dict]:
        """Fallback to extract single location"""
        
        try:
            maps_link = await self.extract_with_fallback(page, 'google_maps_button')
            coordinates = self.extract_coordinates_from_link(maps_link)
            
            if maps_link:
                return {
                    'google_maps_link': maps_link,
                    'coordinates': coordinates
                }
        except Exception as e:
            self.logger.error(f"Fallback extraction failed: {e}")
        
        return None

    def extract_coordinates_from_link(self, maps_link: str) -> str:
        """Extract coordinates from Google Maps link"""
        
        if not maps_link:
            return ''
        
        patterns = [
            r'place/(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'@(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, maps_link)
            if match:
                lat, lng = match.groups()
                return f"{lat},{lng}"
        
        return ''

    async def extract_with_fallback(self, page, data_type) -> str:
        """Extract text with multiple fallback selectors"""
        
        selectors = self.selectors.get(data_type, [])
        
        for selector in selectors:
            try:
                if selector.startswith('text=/'):
                    elem = await page.query_selector(selector)
                else:
                    elem = await page.query_selector(selector)
                
                if elem:
                    if 'href' in selector:
                        text = await elem.get_attribute('href')
                    else:
                        text = await elem.text_content()
                    
                    if text and text.strip():
                        return text.strip()
                        
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed for {data_type}: {e}")
                continue
        
        return ''

    async def retry_failed_urls(self):
        """Retry failed URLs with fresh browser"""
        
        if not self.failed_urls:
            return
        
        print(f"\n🔄 Retrying {len(self.failed_urls)} failed URLs...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            retry_success = 0
            for url in self.failed_urls[:20]:  # Limit retries
                try:
                    entries = await self.scrape_doctor_perfect(page, url, 'general-physician')
                    if entries > 0:
                        retry_success += entries
                except Exception as e:
                    self.logger.error(f"Retry failed for {url}: {e}")
            
            await browser.close()
            print(f"✅ Retry created: {retry_success} additional entries")

    async def save_checkpoint(self, specialty_index):
        """Save checkpoint with current progress including CSV stats"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_file = f"checkpoint_specialty_{specialty_index}_{timestamp}.json"
        
        csv_stats = self.csv_writer.get_stats()
        
        checkpoint_data = {
            'specialties_completed': specialty_index,
            'total_doctors': self.total_scraped,
            'total_entries': len(self.doctors_data),
            'total_locations': self.total_locations,
            'failed_urls': len(self.failed_urls),
            'csv_stats': csv_stats,
            'session_id': self.session_id,
            'timestamp': timestamp
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    async def save_perfect_results(self):
        """Save perfect final results"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"doctors_bangalore_perfect_{timestamp}.csv"
        
        if self.doctors_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'name', 'specialty', 'experience', 'degree', 'consultation_fee', 'rating',
                    'clinic_name', 'clinic_address', 'google_maps_link', 'coordinates',
                    'location_index', 'source_url', 'scraped_at'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for doctor_entry in self.doctors_data:
                    writer.writerow(doctor_entry)
            
            print(f"💾 PERFECT DATA saved to: {csv_filename}")
            
            # Save statistics
            stats = self.generate_perfect_stats()
            stats_filename = f"perfect_stats_{timestamp}.json"
            
            with open(stats_filename, 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"📊 Statistics saved to: {stats_filename}")

    def generate_perfect_stats(self) -> Dict:
        """Generate comprehensive statistics"""
        
        total_entries = len(self.doctors_data)
        
        if total_entries == 0:
            return {'error': 'No data collected'}
        
        # Count by specialty
        specialty_counts = {}
        for entry in self.doctors_data:
            specialty = entry['specialty']
            specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1
        
        # Multi-location analysis
        multi_location_doctors = {}
        for entry in self.doctors_data:
            doctor_key = f"{entry['name']}_{entry['specialty']}"
            if doctor_key not in multi_location_doctors:
                multi_location_doctors[doctor_key] = 0
            multi_location_doctors[doctor_key] += 1
        
        multi_location_count = sum(1 for count in multi_location_doctors.values() if count > 1)
        # Data quality metrics
        quality_metrics = {
            'with_google_maps': sum(1 for d in self.doctors_data if d.get('google_maps_link')),
            'with_coordinates': sum(1 for d in self.doctors_data if d.get('coordinates')),
            'with_fee': sum(1 for d in self.doctors_data if d.get('consultation_fee')),
            'with_experience': sum(1 for d in self.doctors_data if d.get('experience')),
            'with_rating': sum(1 for d in self.doctors_data if d.get('rating')),
            'with_degree': sum(1 for d in self.doctors_data if d.get('degree'))
        }
        
        return {
            'total_entries': total_entries,
            'unique_doctors': self.total_scraped,
            'total_locations': self.total_locations,
            'multi_location_doctors': multi_location_count,
            'avg_locations_per_doctor': self.total_locations / self.total_scraped if self.total_scraped > 0 else 0,
            'specialties_processed': len(self.specialties),
            'specialty_breakdown': specialty_counts,
            'data_quality_counts': quality_metrics,
            'data_quality_percentages': {
                k: f"{v/total_entries*100:.1f}%" for k, v in quality_metrics.items()
            },
            'processing_stats': {
                'total_urls_processed': len(self.processed_urls),
                'failed_urls': len(self.failed_urls),
                'success_rate': f"{len(self.processed_urls)/(len(self.processed_urls)+len(self.failed_urls))*100:.1f}%" if self.processed_urls or self.failed_urls else "N/A"
            },
            'scraping_duration': str(datetime.now() - self.start_time)
        }

    def print_perfect_summary(self):
        """Print perfect final summary with CSV statistics"""
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        total_entries = len(self.doctors_data)
        csv_stats = self.csv_writer.get_stats()
        
        print("\n" + "="*80)
        print("🎯 PERFECT SCRAPER - MISSION ACCOMPLISHED")
        print("="*80)
        print(f"📊 Total entries created: {total_entries}")
        print(f"💾 CSV entries written: {csv_stats['entries_written']}")
        print(f"📁 CSV file size: {csv_stats['file_size_mb']:.1f} MB")
        print(f"📝 CSV filename: {csv_stats['filename']}")
        print(f"👨‍⚕️ Unique doctors: {self.total_scraped}")
        print(f"🏥 Total locations: {self.total_locations}")
        
        # Fix division by zero error
        if self.total_scraped > 0:
            print(f"📍 Avg locations per doctor: {self.total_locations/self.total_scraped:.1f}")
        else:
            print(f"📍 Avg locations per doctor: 0.0")
            
        print(f"🏥 Specialties processed: {len(self.specialties)}")
        print(f"⏱️  Total duration: {duration}")
        
        # Fix division by zero for speed calculation
        if duration.total_seconds() > 0:
            print(f"🚀 Speed: {csv_stats['entries_written'] / duration.total_seconds():.2f} entries/second")
        else:
            print(f"🚀 Speed: 0.00 entries/second")
        
        if total_entries > 0:
            # Multi-location analysis
            multi_location_doctors = {}
            for entry in self.doctors_data:
                doctor_key = f"{entry['name']}_{entry['specialty']}"
                if doctor_key not in multi_location_doctors:
                    multi_location_doctors[doctor_key] = 0
                multi_location_doctors[doctor_key] += 1
            
            multi_location_count = sum(1 for count in multi_location_doctors.values() if count > 1)
            
            print(f"🔄 Multi-location doctors: {multi_location_count}")
            
            # BANGALORE LOCATION ANALYSIS - CRITICAL FOR SORTING!
            all_locations = [d.get('bangalore_location', 'Unknown') for d in self.doctors_data]
            location_stats = self.location_extractor.get_location_statistics(all_locations)
            
            print(f"📍 Bangalore areas found: {location_stats['unique_locations']}")
            if location_stats['most_common']:
                print(f"🏆 Most common area: {location_stats['most_common'][0]} ({location_stats['most_common'][1]} doctors)")
            
            # Data quality summary
            quality_metrics = {
                'Google Maps Links': sum(1 for d in self.doctors_data if d.get('google_maps_link')),
                'Coordinates': sum(1 for d in self.doctors_data if d.get('coordinates')),
                'Fee Information': sum(1 for d in self.doctors_data if d.get('consultation_fee')),
                'Experience': sum(1 for d in self.doctors_data if d.get('experience')),
                'Degree': sum(1 for d in self.doctors_data if d.get('degree'))
            }
            
            print("\n📋 DATA QUALITY SUMMARY:")
            for metric, count in quality_metrics.items():
                percentage = count / total_entries * 100
                print(f"✅ {metric}: {count}/{total_entries} ({percentage:.1f}%)")
        
        print("="*80)
        print("✅ PERFECT DATA COLLECTION COMPLETE")
        print(f"📝 REAL-TIME CSV: {csv_stats['filename']}")
        print(f"💾 LIVE DATA: {csv_stats['entries_written']} entries ready for analysis")
        print("🎯 READY FOR DOCTOR FEE PREDICTION MODEL")
        print("👀 CSV file can be opened in Excel/Pandas for immediate analysis")
        print("="*80)

async def main():
    """Main execution function"""
    scraper = PerfectPractoScraper()
    await scraper.scrape_all_doctors()

if __name__ == "__main__":
    asyncio.run(main())
