#!/usr/bin/env python3
"""
Script to clean location data and remove garbage HTML tag values from scraped data
"""

import csv
import re
import os
import sys

def is_garbage_location(location):
    """Check if a location value is garbage (HTML tags, etc.)"""
    if not location or not location.strip():
        return False
    
    location = location.strip()
    
    # Pattern to detect garbage HTML tag sequences
    html_tag_pattern = r'^[a-z,]+$|^a,abbr,acronym|[a-z]+,[a-z]+,[a-z]+'
    
    # Check for known garbage patterns
    if re.match(html_tag_pattern, location):
        return True
    
    # Additional garbage checks
    if len(location) > 100:  # Suspiciously long
        return True
    
    if location.count(',') > 5:  # Too many commas
        return True
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9\s\-,.\(\)]+$', location):
        return True
    
    return False

def clean_location_value(location):
    """Clean a location value"""
    if not location:
        return ""
    
    location = location.strip()
    
    if is_garbage_location(location):
        return ""  # Return empty for garbage values
    
    return location

def clean_csv_file(input_file, output_file):
    """Clean the CSV file by removing garbage location values"""
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        return False
    
    print(f"Cleaning location data in {input_file}...")
    
    cleaned_count = 0
    total_count = 0
    
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        rows = []
        for row in reader:
            total_count += 1
            original_location = row.get('location', '')
            cleaned_location = clean_location_value(original_location)
            
            if original_location != cleaned_location:
                cleaned_count += 1
                if cleaned_count <= 5:  # Show first 5 examples
                    print(f"  Cleaned: '{original_location[:50]}...' -> '{cleaned_location}'")
            
            row['location'] = cleaned_location
            rows.append(row)
    
    # Write cleaned data
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nCleaning complete:")
    print(f"  Total records processed: {total_count}")
    print(f"  Records with location cleaned: {cleaned_count}")
    print(f"  Percentage cleaned: {cleaned_count/total_count*100:.1f}%")
    print(f"  Output saved to: {output_file}")
    
    return True

def analyze_location_data(csv_file):
    """Analyze location data to show statistics"""
    
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} does not exist")
        return
    
    print(f"\nAnalyzing location data in {csv_file}...")
    
    total_count = 0
    empty_count = 0
    garbage_count = 0
    valid_count = 0
    location_counts = {}
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        
        for row in reader:
            total_count += 1
            location = row.get('location', '').strip()
            
            if not location:
                empty_count += 1
            elif is_garbage_location(location):
                garbage_count += 1
            else:
                valid_count += 1
                location_counts[location] = location_counts.get(location, 0) + 1
    
    print(f"\nLocation Data Analysis:")
    print(f"  Total records: {total_count}")
    print(f"  Empty locations: {empty_count} ({empty_count/total_count*100:.1f}%)")
    print(f"  Garbage locations: {garbage_count} ({garbage_count/total_count*100:.1f}%)")
    print(f"  Valid locations: {valid_count} ({valid_count/total_count*100:.1f}%)")
    
    print(f"\nTop 10 most common valid locations:")
    sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
    for location, count in sorted_locations[:10]:
        print(f"  {location}: {count}")

if __name__ == "__main__":
    # Default file paths
    input_file = "practo_scraper/data/latest_doctors_data.csv"
    output_file = "practo_scraper/data/latest_doctors_data_cleaned.csv"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print("=== Location Data Cleaning Tool ===")
    
    # Analyze original data
    analyze_location_data(input_file)
    
    # Clean the data
    if clean_csv_file(input_file, output_file):
        # Analyze cleaned data
        analyze_location_data(output_file)
        
        print(f"\n✅ Data cleaning completed successfully!")
        print(f"   Original file: {input_file}")
        print(f"   Cleaned file: {output_file}")
    else:
        print("❌ Data cleaning failed!")
        sys.exit(1)