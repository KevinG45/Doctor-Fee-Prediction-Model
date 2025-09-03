"""
Configuration file for Practo scraper
Redesigned to comply with robots.txt and navigate naturally through the site
"""

# Base URL configuration for natural site navigation
BASE_URL = "https://www.practo.com"
BANGALORE_URL = f"{BASE_URL}/bangalore"

# Scraping configuration - Focus on Bangalore as requested
CITY = "Bangalore"  # Single city focus as per requirements

# Common speciality URL patterns found on Practo Bangalore
# These should be discovered dynamically from the main page
COMMON_SPECIALITIES = [
    # Primary care
    'general-physician', 'dentist', 'gynecologist-obstetrician', 
    'pediatrician', 'dermatologist',
    
    # Specialists
    'cardiologist', 'neurologist', 'orthopedist', 'ophthalmologist', 
    'ent-specialist', 'urologist', 'gastroenterologist', 'pulmonologist',
    
    # Mental health and wellness
    'psychiatrist', 'psychologist', 'physiotherapist',
    
    # Surgery specialists
    'general-surgeon', 'plastic-surgeon', 'neurosurgeon',
    
    # Other specialists
    'endocrinologist', 'nephrologist', 'rheumatologist', 'oncologist',
    'radiologist', 'pathologist', 'anesthesiologist'
]

# Output configuration
OUTPUT_DIR = 'data'
CSV_FILENAME = f'{CITY.lower()}_doctors_data.csv'

# Scraping configuration
REQUEST_DELAY = 2
MAX_DOCTORS_PER_SPECIALITY = None  # No artificial limits
MAX_PAGES_PER_SPECIALITY = 50      # Prevent infinite loops
SCROLL_PAUSE_TIME = 2              # Seconds to wait between scrolls
MAX_SCROLL_ATTEMPTS = 10           # Maximum scroll attempts per page

# Browser configuration for Playwright
BROWSER_CONFIG = {
    'headless': True,
    'timeout': 30000,
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Robots.txt compliance settings
ROBOTS_TXT_COMPLIANCE = True
RESPECT_ROBOTS_TXT = True

# Selectors for the new navigation approach
SELECTORS = {
    'specialty_links': 'a[href*="/bangalore/"][href*="-doctors"]',
    'doctor_profile_links': 'a[href*="/doctor/"]',
    'doctor_name': 'h1[data-qa-id="doctor_name"], h1.c-profile__title',
    'doctor_specialty': '[data-qa-id="doctor_specialization"], .c-profile__subtitle',
    'consultation_fee': '[data-qa-id="consultation_fee"], .fee-container',
    'experience': '[data-qa-id="doctor_experience"], .experience',
    'rating': '[data-qa-id="doctor_rating"], .rating',
    'location': '[data-qa-id="doctor_location"], .location',
    'google_map_link': 'a[href*="maps.google.com"], a[href*="goo.gl/maps"], a[href*="google.com/maps"], .map-link, [data-qa-id="map_link"]'
}