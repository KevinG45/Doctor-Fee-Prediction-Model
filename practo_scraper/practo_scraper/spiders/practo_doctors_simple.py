import scrapy
from scrapy import Request
import time
import json
from urllib.parse import quote
from practo_scraper.items import DoctorItem


class PractoDoctorsSimpleSpider(scrapy.Spider):
    name = "practo_doctors_simple"
    allowed_domains = ["practo.com"]
    
    # Configuration
    cities = ['Bangalore', 'Delhi', 'Mumbai']
    specialities = [
        'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
        'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
        'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
        'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
        'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    }
    
    def start_requests(self):
        """Generate initial requests for all city-speciality combinations"""
        
        for city in self.cities:
            for speciality in self.specialities:
                # Build the search URL for Practo
                search_query = quote(f'[{{"word":"{speciality}","autocompleted":true,"category":"subspeciality"}}]')
                url = f"https://www.practo.com/search/doctors?results_type=doctor&q={search_query}&city={city}"
                
                yield Request(
                    url=url,
                    meta={
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctors_listing,
                    errback=self.handle_error,
                )
    
    def parse_doctors_listing(self, response):
        """Parse the doctors listing page and extract doctor profile URLs"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        # Extract doctor profile links
        doctor_links = response.css('div.u-border-general--bottom a[href*="/doctor/"]::attr(href)').getall()
        
        self.logger.info(f"Found {len(doctor_links)} doctors for {speciality} in {city}")
        
        for link in doctor_links:
            if link:
                profile_url = response.urljoin(link)
                
                yield Request(
                    url=profile_url,
                    meta={
                        "city": city,
                        "speciality": speciality,
                    },
                    callback=self.parse_doctor_profile,
                    errback=self.handle_error,
                )
    
    def parse_doctor_profile(self, response):
        """Parse individual doctor profile page"""
        
        city = response.meta['city']
        speciality = response.meta['speciality']
        
        try:
            item = DoctorItem()
            
            # Extract doctor information
            item['city'] = city
            item['speciality'] = speciality
            item['profile_url'] = response.url
            
            # Name
            name = response.css('h1.c-profile__title::text').get()
            if name:
                item['name'] = name.strip()
            
            # Degree
            degree = response.css('p.c-profile__details::text').get()
            if degree:
                item['degree'] = degree.strip()
            
            # Years of experience
            experience_elements = response.css('div.c-profile__details h2::text').getall()
            if experience_elements:
                item['year_of_experience'] = experience_elements[-1].strip()
            
            # Location
            location = response.css('h4.c-profile--clinic__location::text').get()
            if location:
                item['location'] = location.strip()
            
            # DP Score (rating)
            score = response.css('span.u-green-text.u-bold.u-large-font::text').get()
            if score:
                item['dp_score'] = score.strip()
            
            # Number of patient votes
            votes = response.css('span.u-smallest-font.u-grey_3-text::text').get()
            if votes:
                item['npv'] = votes.strip()
            
            # Consultation fee
            fee = response.css('span.u-strike::text').get()
            if fee:
                item['consultation_fee'] = fee.strip()
            else:
                # Try alternative selector
                fee = response.css('div.u-f-right.u-large-font.u-bold.u-valign--middle.u-lheight-normal::text').get()
                if fee:
                    item['consultation_fee'] = fee.strip()
            
            # Only yield if we have essential data
            if item.get('name') and item.get('consultation_fee'):
                yield item
            else:
                self.logger.warning(f"Skipping incomplete profile: {response.url}")
                
        except Exception as e:
            self.logger.error(f"Error parsing doctor profile {response.url}: {str(e)}")
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")