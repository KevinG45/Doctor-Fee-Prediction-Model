"""
Enhanced Configuration for Comprehensive Bangalore Doctors Scraping Project
Following the detailed execution plan requirements
"""

import random
from datetime import datetime

# Base URL configuration (following problem statement specs)
BASE_URL = "https://www.practo.com"

# Target city (focusing on Bangalore as specified)
TARGET_CITY = "Bangalore"

# Comprehensive specialty list (37 specialties as mentioned in problem statement)
COMPREHENSIVE_SPECIALTIES = [
    # Primary care specialties
    "Cardiologist", "Dermatologist", "Dentist", "Gynecologist", "Orthopedist", 
    "Pediatrician", "Neurologist", "Ophthalmologist", "Psychiatrist",
    
    # Secondary specialties
    "General Physician", "ENT Specialist", "Gastroenterologist", "Pulmonologist", 
    "Urologist", "Oncologist",
    
    # Alternative medicine
    "Ayurveda", "Homeopath", "Unani", "Naturopathy",
    
    # Surgery specialists
    "General Surgeon", "Plastic Surgeon", "Neurosurgeon", "Cardiac Surgeon",
    "Orthopedic Surgeon",
    
    # Additional specialists
    "Endocrinologist", "Nephrologist", "Rheumatologist", "Radiologist",
    "Pathologist", "Anesthesiologist", "Emergency Medicine", "Physiotherapist",
    "Psychologist", "Dietitian/Nutritionist", "Infertility Specialist",
    "Bariatric Surgeon", "Vascular Surgeon", "Thoracic Surgeon",
    "Neurosurgeon", "Chiropractor"
]

# Anti-detection configuration (Phase 1 requirements)
USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
]

VIEWPORT_RESOLUTIONS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 720},
]

# Request headers configuration
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

# Timing strategy (respectful rate limiting)
DOWNLOAD_DELAYS = {
    "listing_pages": (2, 5),    # 2-5 seconds for listing pages
    "profile_pages": (3, 7),    # 3-7 seconds for profile pages
}

# Session management
SESSION_ROTATION_REQUESTS = 100  # New session every 100 requests

# URL generation function following problem statement specs
def generate_search_url(specialty, city=TARGET_CITY):
    """
    Generate search URL following exact pattern from problem statement:
    https://www.practo.com/search/doctors?results_type=doctor&q=[{"word":"SPECIALTY","autocompleted":true,"category":"subspeciality"}]&city=Bangalore
    """
    import urllib.parse
    
    query_json = f'[{{"word":"{specialty}","autocompleted":true,"category":"subspeciality"}}]'
    encoded_query = urllib.parse.quote(query_json)
    
    return f"{BASE_URL}/search/doctors?results_type=doctor&q={encoded_query}&city={city}"

# Data extraction selectors (11 required fields)
EXTRACTION_SELECTORS = {
    # Field 1: name
    "name": [
        "h1[data-qa-id='doctor_name']",
        "h1.c-profile__title",
        ".doctor-name h1",
        "h1",
    ],
    
    # Field 3: degree  
    "degree": [
        "[data-qa-id='doctor_qualification']",
        ".qualification-text",
        ".doctor-qualification",
        ".qualifications",
    ],
    
    # Field 4: year_of_experience
    "experience": [
        "[data-qa-id='doctor_experience']",
        ".experience-text",
        ".years-experience", 
        "*[text()*='Years Experience' i]",
    ],
    
    # Field 5: location
    "location": [
        "[data-qa-id='doctor_location']",
        ".clinic-name",
        ".hospital-name",
        ".practice-name",
    ],
    
    # Field 7: dp_score (rating)
    "rating": [
        "[data-qa-id='doctor_rating']",
        ".rating-percent",
        ".doctor-rating",
        ".rating-value",
    ],
    
    # Field 8: npv (patient stories)
    "patient_stories": [
        "[data-qa-id='patient_stories']",
        ".patient-stories",
        ".patient-feedback-count",
        "*[text()*='Patient Stories' i]",
    ],
    
    # Field 9: consultation_fee
    "consultation_fee": [
        "[data-qa-id='consultation_fee']",
        ".fee-amount",
        ".consultation-fee",
        "*[text()*='₹' i]",
    ],
}

# Pagination selectors
PAGINATION_SELECTORS = [
    "a[data-qa-id='next_page']",
    ".pagination .next",
    ".pagination a[aria-label='Next']",
    "a:contains('Next')",
    ".page-navigation .next",
]

# Quality assurance configuration
DATA_VALIDATION_RULES = {
    "name": {"min_length": 3, "required": True},
    "consultation_fee": {"min_value": 0, "max_value": 10000, "numeric": True},
    "year_of_experience": {"min_value": 0, "max_value": 50, "numeric": True},
    "dp_score": {"min_value": 0, "max_value": 5.0, "numeric": True},
}

# Output configuration
OUTPUT_CONFIG = {
    "directory": "data",
    "filename_template": "bangalore_doctors_comprehensive_{timestamp}.csv",
    "fields_order": [
        "name", "speciality", "degree", "year_of_experience", 
        "location", "city", "dp_score", "npv", "consultation_fee", 
        "profile_url", "scraped_at"
    ]
}

# Monitoring configuration
MONITORING_CONFIG = {
    "progress_log_interval": 50,  # Log progress every 50 doctors
    "checkpoint_interval": 100,   # Save checkpoint every 100 doctors
    "expected_total_doctors": 4500,  # Target from problem statement
    "min_acceptable_doctors": 2000,  # Minimum acceptable
}

# Error handling configuration
ERROR_HANDLING = {
    "max_retries": 3,
    "retry_delay": (5, 10),  # 5-10 seconds between retries
    "max_consecutive_failures": 5,
    "cooling_period": 3600,  # 1 hour cooling period if blocked
}

def get_random_user_agent():
    """Get a random user agent from the pool"""
    return random.choice(USER_AGENT_POOL)

def get_random_viewport():
    """Get a random viewport resolution"""
    return random.choice(VIEWPORT_RESOLUTIONS)

def get_download_delay(page_type="listing"):
    """Get random download delay based on page type"""
    delay_range = DOWNLOAD_DELAYS.get(f"{page_type}_pages", (2, 5))
    return random.uniform(delay_range[0], delay_range[1])

def get_timestamp():
    """Get current timestamp for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")