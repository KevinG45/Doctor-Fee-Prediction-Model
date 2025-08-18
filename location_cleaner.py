#!/usr/bin/env python3
"""
Location Data Cleaner for Doctor Fee Prediction Model

This utility cleans location data from the scraped doctor information:
1. Detects and filters HTML garbage in location fields
2. Extracts coordinates from Google Maps links
3. Performs reverse geocoding to get proper addresses
4. Provides cleaned location data for all doctors
"""

import pandas as pd
import re
import requests
import time
from urllib.parse import unquote
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocationCleaner:
    def __init__(self):
        """Initialize the location cleaner"""
        pass
    
    def is_garbage_location(self, location):
        """
        Detect if a location field contains HTML garbage data
        
        Args:
            location (str): Location text to check
            
        Returns:
            bool: True if location appears to be garbage data
        """
        if not location or pd.isna(location):
            return True
            
        location = str(location).strip()
        
        # Check for HTML tag names pattern
        html_garbage_patterns = [
            r'^a,abbr,acronym,address,applet,article',  # Common garbage pattern
            r'[a-z]+,[a-z]+,[a-z]+,[a-z]+',  # Multiple comma-separated lowercase words
            r'^(a|abbr|acronym|address|applet|article|aside|audio|b|big|blockquote)$',  # Single HTML tags
        ]
        
        for pattern in html_garbage_patterns:
            if re.search(pattern, location, re.IGNORECASE):
                return True
        
        # Check if it's suspiciously long (garbage data tends to be very long)
        if len(location) > 200:
            return True
            
        # Check if it contains too many commas (likely tag list)
        if location.count(',') > 5:
            return True
            
        return False
    
    def extract_coordinates_from_map_link(self, map_link):
        """
        Extract latitude and longitude from Google Maps links
        
        Args:
            map_link (str): Google Maps URL
            
        Returns:
            tuple: (latitude, longitude) or (None, None) if not found
        """
        if not map_link or pd.isna(map_link):
            return None, None
            
        map_link = str(map_link)
        
        # Pattern 1: Direct coordinates in place URL
        # Example: http://www.google.com/maps/place/12.975938481932,77.654982741741
        coord_pattern = r'maps/place/(-?\d+\.?\d*),(-?\d+\.?\d*)'
        match = re.search(coord_pattern, map_link)
        if match:
            try:
                lat, lng = float(match.group(1)), float(match.group(2))
                return lat, lng
            except ValueError:
                pass
        
        # Pattern 2: Coordinates in query parameters
        # Example: ?q=12.975938481932,77.654982741741
        query_pattern = r'[?&]q=(-?\d+\.?\d*),(-?\d+\.?\d*)'
        match = re.search(query_pattern, map_link)
        if match:
            try:
                lat, lng = float(match.group(1)), float(match.group(2))
                return lat, lng
            except ValueError:
                pass
        
        # Pattern 3: @coordinates in URLs
        # Example: /@12.975938481932,77.654982741741,15z
        at_pattern = r'@(-?\d+\.?\d*),(-?\d+\.?\d*)'
        match = re.search(at_pattern, map_link)
        if match:
            try:
                lat, lng = float(match.group(1)), float(match.group(2))
                return lat, lng
            except ValueError:
                pass
        
        return None, None
    
    def reverse_geocode_nominatim(self, lat, lng):
        """
        Perform reverse geocoding using Nominatim (OpenStreetMap) API
        
        Args:
            lat (float): Latitude
            lng (float): Longitude
            
        Returns:
            str: Address string or None if not found
        """
        try:
            # Nominatim API endpoint
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'addressdetails': 1,
                'zoom': 16  # Street level detail
            }
            headers = {
                'User-Agent': 'Doctor-Fee-Prediction-Model/1.0 (Location Data Cleaning)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'address' in data:
                    address_parts = []
                    addr = data['address']
                    
                    # Build address from components
                    if 'house_number' in addr and 'road' in addr:
                        address_parts.append(f"{addr['house_number']} {addr['road']}")
                    elif 'road' in addr:
                        address_parts.append(addr['road'])
                    
                    if 'neighbourhood' in addr:
                        address_parts.append(addr['neighbourhood'])
                    elif 'suburb' in addr:
                        address_parts.append(addr['suburb'])
                    
                    if 'city' in addr:
                        address_parts.append(addr['city'])
                    elif 'town' in addr:
                        address_parts.append(addr['town'])
                    
                    if address_parts:
                        return ', '.join(address_parts)
                
                # Fallback to display_name if detailed address not available
                if 'display_name' in data:
                    # Clean up display_name to remove unnecessary details
                    display_name = data['display_name']
                    # Take first few parts before country
                    parts = display_name.split(', ')
                    if len(parts) > 3:
                        return ', '.join(parts[:3])
                    return display_name
            
        except Exception as e:
            logger.warning(f"Reverse geocoding failed for {lat}, {lng}: {e}")
        
        return None
    
    def clean_search_url(self, map_link):
        """
        Extract useful location information from Google Maps search URLs
        
        Args:
            map_link (str): Google Maps search URL
            
        Returns:
            str: Cleaned location string or None
        """
        if not map_link or pd.isna(map_link):
            return None
            
        map_link = str(map_link)
        
        # Check if it's a search URL
        if 'maps/search/' in map_link:
            try:
                # Extract the search query
                search_part = map_link.split('maps/search/')[1]
                search_query = unquote(search_part)
                
                # Look for city name at the end (after last +)
                parts = search_query.split('+')
                if len(parts) > 1:
                    # Check if the last part is a city name
                    last_part = parts[-1]
                    if last_part and len(last_part) > 3 and not self.is_garbage_location(last_part):
                        return last_part
                
                # If that fails, look for doctor name in the beginning (before garbage)
                if '+a,abbr,' in search_query:
                    # Extract doctor name part before the garbage
                    clean_part = search_query.split('+a,abbr,')[0]
                    # Remove "Dr.+" prefix if present
                    if clean_part.startswith('Dr.+'):
                        clean_part = clean_part[4:]
                    # Replace + with spaces
                    clean_part = clean_part.replace('+', ' ')
                    if clean_part and len(clean_part) > 3:
                        return f"Near {clean_part}"
                
                # If no garbage pattern, check if the whole query is clean
                clean_query = search_query.replace('+', ' ')
                if not self.is_garbage_location(clean_query) and len(clean_query) < 100:
                    return clean_query
                    
            except Exception as e:
                logger.debug(f"Failed to parse search URL: {e}")
        
        return None
    
    def process_csv_file(self, input_file, output_file=None):
        """
        Process a CSV file to clean location data
        
        Args:
            input_file (str): Path to input CSV file
            output_file (str): Path to output CSV file (optional)
            
        Returns:
            pandas.DataFrame: Processed dataframe with cleaned locations
        """
        logger.info(f"Loading data from {input_file}")
        df = pd.read_csv(input_file)
        
        logger.info(f"Processing {len(df)} records")
        
        # Add new columns for analysis
        df['original_location'] = df['location'].copy()
        df['location_is_garbage'] = df['location'].apply(self.is_garbage_location)
        df['extracted_coordinates'] = None
        df['geocoded_address'] = None
        df['cleaned_location'] = None
        
        # Extract coordinates from all Google Maps links
        logger.info("Extracting coordinates from Google Maps links...")
        coordinates_list = []
        for idx, map_link in df['google_map_link'].items():
            lat, lng = self.extract_coordinates_from_map_link(map_link)
            coordinates_list.append((lat, lng))
            if idx % 100 == 0:
                logger.info(f"Processed {idx}/{len(df)} map links")
        
        df['extracted_coordinates'] = coordinates_list
        
        # Count how many coordinates we extracted
        valid_coords = [(lat, lng) for lat, lng in coordinates_list if lat is not None and lng is not None]
        logger.info(f"Extracted coordinates for {len(valid_coords)} records")
        
        # Perform reverse geocoding for records with coordinates
        logger.info("Performing reverse geocoding...")
        geocoded_count = 0
        for idx, (lat, lng) in enumerate(coordinates_list):
            if lat is not None and lng is not None:
                address = self.reverse_geocode_nominatim(lat, lng)
                df.at[idx, 'geocoded_address'] = address
                if address:
                    geocoded_count += 1
                
                # Rate limiting for API
                if geocoded_count % 10 == 0:
                    time.sleep(1)  # Be respectful to Nominatim
                    logger.info(f"Geocoded {geocoded_count} addresses...")
        
        logger.info(f"Successfully geocoded {geocoded_count} addresses")
        
        # Determine the best location for each record
        logger.info("Determining best location for each record...")
        for idx in df.index:
            location = df.at[idx, 'location']
            is_garbage = df.at[idx, 'location_is_garbage']
            geocoded = df.at[idx, 'geocoded_address']
            city = df.at[idx, 'city']
            
            if not is_garbage and location and str(location).strip():
                # Use original location if it's good
                df.at[idx, 'cleaned_location'] = str(location).strip()
            elif geocoded:
                # Use geocoded address if available
                df.at[idx, 'cleaned_location'] = geocoded
            else:
                # Try to extract from search URL
                search_location = self.clean_search_url(df.at[idx, 'google_map_link'])
                if search_location:
                    df.at[idx, 'cleaned_location'] = search_location
                else:
                    # Fallback to city if nothing else works
                    df.at[idx, 'cleaned_location'] = city if city else "Location Unknown"
        
        # Update the main location column
        df['location'] = df['cleaned_location']
        
        # Generate summary statistics
        self.print_summary(df)
        
        # Save to output file if specified
        if output_file:
            logger.info(f"Saving cleaned data to {output_file}")
            # Keep only essential columns for output
            output_columns = [col for col in df.columns if not col.startswith('location_is_garbage') 
                             and not col.startswith('extracted_coordinates')
                             and not col.startswith('geocoded_address')
                             and not col.startswith('original_location')
                             and not col.startswith('cleaned_location')]
            df[output_columns].to_csv(output_file, index=False)
        
        return df
    
    def print_summary(self, df):
        """Print summary of the cleaning process"""
        total_records = len(df)
        garbage_before = df['location_is_garbage'].sum()
        
        # Check final quality
        final_empty = df['location'].isna().sum()
        final_garbage = df['location'].apply(self.is_garbage_location).sum()
        
        logger.info("\n" + "="*50)
        logger.info("LOCATION CLEANING SUMMARY")
        logger.info("="*50)
        logger.info(f"Total records processed: {total_records}")
        logger.info(f"Records with garbage locations (before): {garbage_before} ({garbage_before/total_records*100:.1f}%)")
        logger.info(f"Records with coordinates extracted: {sum(1 for coords in df['extracted_coordinates'] if coords[0] is not None)}")
        logger.info(f"Records successfully geocoded: {df['geocoded_address'].notna().sum()}")
        logger.info(f"Records with empty locations (after): {final_empty} ({final_empty/total_records*100:.1f}%)")
        logger.info(f"Records with garbage locations (after): {final_garbage} ({final_garbage/total_records*100:.1f}%)")
        logger.info(f"Improvement: {garbage_before - final_garbage} records fixed")
        logger.info("="*50)

def main():
    """Main function to run the location cleaner"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python location_cleaner.py <input_csv> [output_csv]")
        print("Example: python location_cleaner.py practo_scraper/data/latest_doctors_data.csv cleaned_doctors_data.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    cleaner = LocationCleaner()
    cleaner.process_csv_file(input_file, output_file)

if __name__ == "__main__":
    main()