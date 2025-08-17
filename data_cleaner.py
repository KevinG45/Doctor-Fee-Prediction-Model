#!/usr/bin/env python3
"""
Data Cleaning and Enhancement Script for Bangalore Enhanced CSV
This script will:
1. Remove duplicate records
2. Fill missing data where possible
3. Add Google Maps links based on location
4. Generate a clean dataset
"""

import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = None
        
    def load_data(self):
        """Load the CSV data"""
        try:
            self.df = pd.read_csv(self.csv_file)
            logger.info(f"Loaded {len(self.df)} records from {self.csv_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def analyze_data_quality(self):
        """Analyze current data quality"""
        logger.info("\n=== DATA QUALITY ANALYSIS ===")
        logger.info(f"Total records: {len(self.df)}")
        
        for column in self.df.columns:
            empty_count = self.df[column].isna().sum() + (self.df[column] == '').sum()
            filled_percentage = ((len(self.df) - empty_count) / len(self.df)) * 100
            logger.info(f"{column}: {filled_percentage:.1f}% filled ({len(self.df) - empty_count}/{len(self.df)})")
        
        # Check for duplicates
        duplicates = self.df.duplicated(subset=['name', 'city', 'speciality']).sum()
        logger.info(f"Duplicate records: {duplicates}")
        
        # Check for name-only duplicates (different locations)
        name_duplicates = self.df.duplicated(subset=['name']).sum()
        logger.info(f"Doctors with same name: {name_duplicates}")
    
    def remove_duplicates(self):
        """Remove duplicate records intelligently"""
        logger.info("Removing duplicates...")
        
        original_count = len(self.df)
        
        # First remove exact duplicates
        self.df = self.df.drop_duplicates()
        
        # For records with same name and speciality, keep the one with most complete data
        def score_completeness(row):
            score = 0
            if row['location'] and str(row['location']).strip():
                score += 3
            if row['year_of_experience'] and str(row['year_of_experience']).strip():
                score += 2
            if row['consultation_fee'] and str(row['consultation_fee']).strip():
                score += 1
            return score
        
        self.df['completeness_score'] = self.df.apply(score_completeness, axis=1)
        
        # Keep the record with highest completeness score for each name+speciality combination
        self.df = self.df.sort_values('completeness_score', ascending=False)
        self.df = self.df.drop_duplicates(subset=['name', 'speciality'], keep='first')
        self.df = self.df.drop('completeness_score', axis=1)
        
        removed_count = original_count - len(self.df)
        logger.info(f"Removed {removed_count} duplicate records")
    
    def extract_experience_from_degree(self):
        """Try to extract experience from degree field"""
        logger.info("Extracting experience from degree field...")
        
        experience_patterns = [
            r'(\d+)\s*years?\s*of\s*experience',
            r'(\d+)\s*years?\s*experience', 
            r'(\d+)\s*yrs?\s*experience',
            r'experience:?\s*(\d+)\s*years?',
            r'(\d+)\+?\s*years?'
        ]
        
        extracted_count = 0
        for idx, row in self.df.iterrows():
            if pd.isna(row['year_of_experience']) or row['year_of_experience'] == '':
                degree_text = str(row['degree']).lower()
                for pattern in experience_patterns:
                    match = re.search(pattern, degree_text)
                    if match:
                        years = match.group(1)
                        self.df.at[idx, 'year_of_experience'] = f"{years} years"
                        extracted_count += 1
                        break
        
        logger.info(f"Extracted experience for {extracted_count} records")
    
    def enhance_locations(self):
        """Enhance location data"""
        logger.info("Enhancing location data...")
        
        # Common Bangalore locations mapping
        location_mappings = {
            'jp nagar': 'JP Nagar',
            'btm': 'BTM Layout',
            'hsr': 'HSR Layout', 
            'electronic city': 'Electronic City',
            'whitefield': 'Whitefield',
            'koramangala': 'Koramangala',
            'indiranagar': 'Indiranagar',
            'jayanagar': 'Jayanagar',
            'rajajinagar': 'Rajajinagar',
            'malleshwaram': 'Malleshwaram',
            'basavanagudi': 'Basavanagudi',
            'marathahalli': 'Marathahalli',
            'hebbal': 'Hebbal',
            'bannerghatta': 'Bannerghatta Road',
            'mg road': 'MG Road',
            'brigade road': 'Brigade Road',
            'commercial street': 'Commercial Street',
            'vijayanagar': 'Vijayanagar',
            'rt nagar': 'RT Nagar',
            'sarjapur': 'Sarjapur Road',
            'bellandur': 'Bellandur',
            'domlur': 'Domlur',
            'frazer town': 'Frazer Town',
            'banaswadi': 'Banaswadi'
        }
        
        enhanced_count = 0
        for idx, row in self.df.iterrows():
            location = str(row['location']).lower().strip()
            
            # If location is empty or just whitespace
            if not location or location == 'nan':
                # Try to extract from profile URL
                profile_url = str(row['profile_url'])
                for key, value in location_mappings.items():
                    if key.replace(' ', '-') in profile_url.lower():
                        self.df.at[idx, 'location'] = value
                        enhanced_count += 1
                        break
            else:
                # Standardize existing locations
                for key, value in location_mappings.items():
                    if key in location:
                        self.df.at[idx, 'location'] = value
                        enhanced_count += 1
                        break
        
        logger.info(f"Enhanced location data for {enhanced_count} records")
    
    def add_google_maps_links(self):
        """Add Google Maps links based on location"""
        logger.info("Adding Google Maps links...")
        
        # Add column if it doesn't exist
        if 'google_map_link' not in self.df.columns:
            self.df['google_map_link'] = ''
        
        maps_added = 0
        for idx, row in self.df.iterrows():
            # Skip if already has a maps link
            if 'google_map_link' in row and row['google_map_link'] and str(row['google_map_link']).strip():
                continue
                
            location = str(row['location']).strip()
            if location and location != 'nan':
                # Create Google Maps search link
                search_query = f"{location}, Bangalore, Karnataka, India"
                maps_link = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
                self.df.at[idx, 'google_map_link'] = maps_link
                maps_added += 1
        
        logger.info(f"Added Google Maps links for {maps_added} records")
    
    def fill_missing_consultation_fees(self):
        """Fill missing consultation fees with specialty-based averages"""
        logger.info("Filling missing consultation fees...")
        
        # Calculate average fees by speciality
        speciality_avg_fees = {}
        for speciality in self.df['speciality'].unique():
            speciality_data = self.df[self.df['speciality'] == speciality]
            valid_fees = pd.to_numeric(speciality_data['consultation_fee'], errors='coerce')
            valid_fees = valid_fees[valid_fees.notna()]
            if len(valid_fees) > 0:
                speciality_avg_fees[speciality] = int(valid_fees.median())
        
        filled_count = 0
        for idx, row in self.df.iterrows():
            if pd.isna(row['consultation_fee']) or row['consultation_fee'] == '':
                speciality = row['speciality']
                if speciality in speciality_avg_fees:
                    self.df.at[idx, 'consultation_fee'] = speciality_avg_fees[speciality]
                    filled_count += 1
        
        logger.info(f"Filled consultation fees for {filled_count} records")
        logger.info("Average fees by speciality:")
        for spec, fee in speciality_avg_fees.items():
            logger.info(f"  {spec}: ₹{fee}")
    
    def clean_and_validate_data(self):
        """Clean and validate all data"""
        logger.info("Cleaning and validating data...")
        
        # Clean numeric fields
        self.df['consultation_fee'] = pd.to_numeric(self.df['consultation_fee'], errors='coerce').fillna(0).astype(int)
        self.df['dp_score'] = pd.to_numeric(self.df['dp_score'], errors='coerce')
        self.df['npv'] = pd.to_numeric(self.df['npv'], errors='coerce').fillna(0).astype(int)
        
        # Clean text fields
        for column in ['name', 'degree', 'location']:
            self.df[column] = self.df[column].astype(str).str.strip()
        
        # Add missing columns if they don't exist
        required_columns = ['google_map_link']
        for col in required_columns:
            if col not in self.df.columns:
                self.df[col] = ''
        
        logger.info("Data cleaning completed")
    
    def generate_summary_report(self):
        """Generate a summary report of the cleaned data"""
        logger.info("\n=== CLEANED DATA SUMMARY ===")
        logger.info(f"Total records: {len(self.df)}")
        
        # Data completeness
        for column in self.df.columns:
            non_empty = self.df[column].notna().sum()
            if column in ['consultation_fee', 'npv']:
                non_zero = (self.df[column] != 0).sum()
                logger.info(f"{column}: {non_zero}/{len(self.df)} non-zero ({(non_zero/len(self.df)*100):.1f}%)")
            else:
                logger.info(f"{column}: {non_empty}/{len(self.df)} filled ({(non_empty/len(self.df)*100):.1f}%)")
        
        # Speciality distribution
        logger.info("\nSpeciality distribution:")
        spec_counts = self.df['speciality'].value_counts()
        for spec, count in spec_counts.head(10).items():
            logger.info(f"  {spec}: {count}")
        
        # Location distribution
        logger.info("\nTop locations:")
        location_counts = self.df[self.df['location'] != '']['location'].value_counts()
        for loc, count in location_counts.head(10).items():
            logger.info(f"  {loc}: {count}")
    
    def save_cleaned_data(self, output_file=None):
        """Save the cleaned data"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"bangalore_doctors_cleaned_{timestamp}.csv"
        
        try:
            self.df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"Cleaned data saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return None
    
    def process_all(self):
        """Run all cleaning steps"""
        if not self.load_data():
            return None
        
        self.analyze_data_quality()
        self.remove_duplicates()
        self.extract_experience_from_degree()
        self.enhance_locations()
        self.add_google_maps_links()
        self.fill_missing_consultation_fees()
        self.clean_and_validate_data()
        self.generate_summary_report()
        
        return self.save_cleaned_data()


def main():
    """Main function"""
    csv_file = "practo_scraper/bangalore_enhanced.csv"
    
    cleaner = DataCleaner(csv_file)
    output_file = cleaner.process_all()
    
    if output_file:
        logger.info(f"\n✅ Data cleaning completed successfully!")
        logger.info(f"📁 Output file: {output_file}")
    else:
        logger.error("❌ Data cleaning failed!")


if __name__ == "__main__":
    main()