#!/usr/bin/env python3
"""
Bangalore Doctors Web Scraping with Google Maps Links

This script scrapes doctor information from Practo for Bangalore only 
and includes Google Maps links for each doctor.

Usage:
    python bangalore_doctors_scraper.py
"""

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import urllib.parse
import sys
import os

def generate_google_maps_link(doctor_name, location, city):
    """
    Generate a Google Maps search link for a doctor based on their name and location
    """
    # Clean and format the search query
    search_query = f"{doctor_name} doctor {location} {city}"
    # URL encode the search query
    encoded_query = urllib.parse.quote_plus(search_query)
    # Create Google Maps search URL
    maps_url = f"https://www.google.com/maps/search/{encoded_query}"
    return maps_url

def setup_chrome_driver():
    """Set up Chrome driver with optimized options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    return webdriver.Chrome(options=chrome_options)

def scrape_doctor_details(driver, link_full):
    """Extract individual doctor details from their profile page"""
    try:
        driver.get(link_full)
        time.sleep(2)
        soup2 = BeautifulSoup(driver.page_source, 'lxml')

        # Initialize variables with default values
        doctor_data = {
            'name': "N/A",
            'degree': "N/A", 
            'year_of_experience': "N/A",
            'location': "N/A",
            'dp_score': "N/A",
            'npv': "N/A",
            'consultant_fee': "N/A"
        }
        
        # Extract doctor information with error handling
        try:
            doctor_data['name'] = soup2.find('h1', class_='c-profile__title u-bold u-d-inlineblock').text.strip()
        except:
            pass
            
        try:
            doctor_data['degree'] = soup2.find('p', class_='c-profile__details').text.strip()
        except:
            pass
            
        try:
            doctor_data['year_of_experience'] = soup2.find('div', class_='c-profile__details').find_all('h2')[-1].text.strip()
        except:
            pass
            
        try:
            doctor_data['location'] = soup2.find('h4', class_='c-profile--clinic__location').text.strip()
        except:
            pass
            
        try:
            doctor_data['dp_score'] = soup2.find('span', class_='u-green-text u-bold u-large-font').text.strip()
        except:
            pass
            
        try:
            doctor_data['npv'] = soup2.find('span', class_='u-smallest-font u-grey_3-text').text.strip()
        except:
            pass
            
        try:
            doctor_data['consultant_fee'] = soup2.find('span', class_='u-strike').text.strip()
        except:
            try:
                doctor_data['consultant_fee'] = soup2.find('div', class_='u-f-right u-large-font u-bold u-valign--middle u-lheight-normal').text.strip()
            except:
                pass
        
        return doctor_data
        
    except Exception as e:
        print(f"Error extracting doctor details: {str(e)}")
        return None

def scrape_bangalore_doctors():
    """Main function to scrape Bangalore doctors with Google Maps links"""
    
    # Initialize dataframe with all columns including Google Maps link
    df = pd.DataFrame({
        'Name': [], 
        'Speciality': [], 
        'Degree': [], 
        'Year_of_experience': [], 
        'Location': [], 
        'City': [], 
        'dp_score': [], 
        'npv': [], 
        'consultation_fee': [],
        'google_maps_link': []
    })

    # Focus only on Bangalore
    city = 'Bangalore'

    # All specialities as in original code
    specialities = [
        'Cardiologist', 'Chiropractor', 'Dentist', 'Dermatologist', 
        'Dietitian/Nutritionist', 'Gastroenterologist', 'bariatric surgeon', 
        'Gynecologist', 'Infertility Specialist', 'Neurologist', 'Neurosurgeon', 
        'Ophthalmologist', 'Orthopedist', 'Pediatrician', 'Physiotherapist', 
        'Psychiatrist', 'Pulmonologist', 'Rheumatologist', 'Urologist'
    ]

    print(f"Starting web scraping for {city} doctors...")
    print(f"Total specialities to process: {len(specialities)}")

    total_doctors = 0

    # Main scraping loop - focused only on Bangalore
    for speciality in specialities:
        print(f"\nProcessing {speciality} specialists in {city}...")
        
        driver = None
        try:
            driver = setup_chrome_driver()
            url = f"https://www.practo.com/search/doctors?results_type=doctor&q=%5B%7B%22word%22%3A%22{speciality}%22%2C%22autocompleted%22%3Atrue%2C%22category%22%3A%22subspeciality%22%7D%5D&city={city}"
            driver.get(url)
            time.sleep(3)
            
            # Scroll to load all doctors
            scroll_pause_time = 2 
            screen_height = driver.execute_script("return window.screen.height;") 
            A = 1

            while True:
                driver.execute_script("window.scrollTo(0, {screen_height}*{A});".format(screen_height=screen_height, A=A))
                A += 1
                time.sleep(scroll_pause_time)
          
                scroll_height = driver.execute_script("return document.body.scrollHeight;")
           
                if (screen_height) * A > scroll_height:
                    break
         
            soup = BeautifulSoup(driver.page_source, 'lxml')
            postings = soup.find_all('div', class_='u-border-general--bottom')
            
            doctors_found = 0
            
            for post in postings:
                try:
                    link = post.find('div', class_='listing-doctor-card').find('a').get('href')
                    link_full = 'https://www.practo.com' + link
                    
                    # Extract doctor details
                    doctor_data = scrape_doctor_details(driver, link_full)
                    
                    if doctor_data and doctor_data['name'] != "N/A":
                        # Generate Google Maps link
                        google_maps_link = generate_google_maps_link(
                            doctor_data['name'], 
                            doctor_data['location'], 
                            city
                        )
                        
                        # Create new row for dataframe
                        new_row = pd.DataFrame({
                            'Name': [doctor_data['name']], 
                            'Speciality': [speciality], 
                            'Degree': [doctor_data['degree']], 
                            'Year_of_experience': [doctor_data['year_of_experience']], 
                            'Location': [doctor_data['location']], 
                            'City': [city], 
                            'dp_score': [doctor_data['dp_score']], 
                            'npv': [doctor_data['npv']], 
                            'consultation_fee': [doctor_data['consultant_fee']],
                            'google_maps_link': [google_maps_link]
                        })
                        
                        df = pd.concat([df, new_row], ignore_index=True)
                        doctors_found += 1
                        
                except Exception as e:
                    print(f"Error processing doctor: {str(e)}")
                    continue
            
            print(f"Found {doctors_found} {speciality} specialists in {city}")
            total_doctors += doctors_found
            
        except Exception as e:
            print(f"Error processing {speciality}: {str(e)}")
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
        # Small delay between specialities
        time.sleep(2)

    print(f"\nCompleted scraping! Total doctors found: {total_doctors}")
    return df

def main():
    """Main execution function"""
    try:
        # Run the scraping
        df = scrape_bangalore_doctors()
        
        if len(df) > 0:
            # Display summary
            print(f"\nFinal dataset shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Save the enhanced dataset
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'DATA')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'bangalore_doctors_with_maps.csv')
            
            df.to_csv(output_file, index=False)
            print(f"\nDataset saved to: {output_file}")
            print(f"Total records: {len(df)}")
            print(f"Columns included: {', '.join(df.columns)}")
            
            # Display sample of Google Maps links
            print("\nSample Google Maps links generated:")
            for i in range(min(3, len(df))):
                print(f"{df.iloc[i]['Name']} - {df.iloc[i]['google_maps_link']}")
            
            # Data validation and statistics
            print(f"\nDataset Statistics:")
            print(f"Total doctors: {len(df)}")
            print(f"\nSpeciality distribution:")
            print(df['Speciality'].value_counts().head(10))
            
        else:
            print("No data was scraped. Please check your internet connection and try again.")
            
    except Exception as e:
        print(f"An error occurred during execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()