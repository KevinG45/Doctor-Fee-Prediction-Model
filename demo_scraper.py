#!/usr/bin/env python3
"""
Demo script to show the Doctor Fee Prediction Scraper functionality
This creates sample data with Google Maps links and saves to both CSV and database
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

def create_sample_data_with_maps():
    """Create sample doctor data with Google Maps links for demonstration"""
    
    sample_doctors = [
        {
            'name': 'Dr. Rajesh Kumar',
            'speciality': 'Cardiologist',
            'degree': 'MBBS, MD (Cardiology)',
            'year_of_experience': '15 years',
            'location': 'Koramangala, Bangalore',
            'city': 'Bangalore',
            'dp_score': '4.5',
            'npv': '150 patient votes',
            'consultation_fee': '800',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-rajesh-kumar-cardiologist',
            'google_map_link': 'https://www.google.com/maps/search/Dr.+Rajesh+Kumar+Koramangala+Bangalore',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'name': 'Dr. Priya Sharma',
            'speciality': 'Gynecologist',
            'degree': 'MBBS, MS (Gynecology)',
            'year_of_experience': '12 years',
            'location': 'Whitefield, Bangalore',
            'city': 'Bangalore',
            'dp_score': '4.7',
            'npv': '200 patient votes',
            'consultation_fee': '600',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-priya-sharma-gynecologist',
            'google_map_link': 'https://www.google.com/maps?q=12.9698,77.7499',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'name': 'Dr. Arun Naik',
            'speciality': 'Orthopedist',
            'degree': 'MBBS, MS (Orthopedics)',
            'year_of_experience': '18 years',
            'location': 'HSR Layout, Bangalore',
            'city': 'Bangalore',
            'dp_score': '4.3',
            'npv': '85 patient votes',
            'consultation_fee': '700',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-arun-naik-orthopedist',
            'google_map_link': 'https://www.google.com/maps/place/HSR+Layout,+Bengaluru,+Karnataka/@12.9142,77.6311,14z',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'name': 'Dr. Meera Reddy',
            'speciality': 'Dermatologist',
            'degree': 'MBBS, DVD (Dermatology)',
            'year_of_experience': '10 years',
            'location': 'Indiranagar, Bangalore',
            'city': 'Bangalore',
            'dp_score': '4.6',
            'npv': '120 patient votes',
            'consultation_fee': '500',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-meera-reddy-dermatologist',
            'google_map_link': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3887.889!2d77.64115!3d12.9719!2z',
            'scraped_at': datetime.now().isoformat()
        },
        {
            'name': 'Dr. Karthik Rao',
            'speciality': 'Neurologist',
            'degree': 'MBBS, DM (Neurology)',
            'year_of_experience': '22 years',
            'location': 'JP Nagar, Bangalore',
            'city': 'Bangalore',
            'dp_score': '4.8',
            'npv': '300 patient votes',
            'consultation_fee': '1000',
            'profile_url': 'https://www.practo.com/bangalore/doctor/dr-karthik-rao-neurologist',
            'google_map_link': 'https://www.google.com/maps/search/Dr.+Karthik+Rao+JP+Nagar+Bangalore',
            'scraped_at': datetime.now().isoformat()
        }
    ]
    
    return sample_doctors

def save_to_csv(data, filename='data/demo_doctors_data.csv'):
    """Save data to CSV file"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"✅ Saved {len(data)} doctors to {filename}")
    
    return df

def save_to_database(data, db_path='data/demo_doctors_database.db'):
    """Save data to SQLite database"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
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
    
    # Insert data
    for doctor in data:
        cursor.execute('''
            INSERT OR REPLACE INTO doctors (
                name, speciality, degree, year_of_experience, location, city,
                dp_score, npv, consultation_fee, profile_url, google_map_link, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doctor['name'],
            doctor['speciality'], 
            doctor['degree'],
            doctor['year_of_experience'],
            doctor['location'],
            doctor['city'],
            doctor['dp_score'],
            doctor['npv'],
            doctor['consultation_fee'],
            doctor['profile_url'],
            doctor['google_map_link'],
            doctor['scraped_at']
        ))
    
    conn.commit()
    
    # Get count
    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]
    
    conn.close()
    print(f"✅ Saved {len(data)} doctors to database. Total records: {count}")

def demonstrate_google_maps_functionality():
    """Show the different types of Google Maps links the scraper can extract"""
    
    print("\n🗺️  Google Maps Link Extraction Demo")
    print("=" * 50)
    
    google_maps_examples = [
        {
            "type": "Search-based URL",
            "description": "Generated when we have doctor name and location",
            "example": "https://www.google.com/maps/search/Dr.+Rajesh+Kumar+Koramangala+Bangalore",
            "use_case": "When no direct map link found but we have location info"
        },
        {
            "type": "Coordinate-based URL", 
            "description": "Generated from latitude/longitude found in JavaScript",
            "example": "https://www.google.com/maps?q=12.9698,77.7499",
            "use_case": "When coordinates are embedded in page JavaScript"
        },
        {
            "type": "Place-based URL",
            "description": "Direct link to a specific place on Google Maps",
            "example": "https://www.google.com/maps/place/HSR+Layout,+Bengaluru,+Karnataka/@12.9142,77.6311,14z",
            "use_case": "When area/locality-specific map links are found"
        },
        {
            "type": "Embedded Map URL",
            "description": "From iframe src attributes on doctor profile pages",
            "example": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3887.889!2d77.64115!3d12.9719!2z",
            "use_case": "When Google Maps is embedded directly in the page"
        }
    ]
    
    for i, example in enumerate(google_maps_examples, 1):
        print(f"\n{i}. {example['type']}")
        print(f"   Description: {example['description']}")
        print(f"   Example: {example['example']}")
        print(f"   Use Case: {example['use_case']}")

def show_scraper_features():
    """Display the key features of the implemented scraper"""
    
    print("\n🕷️  Scraper Features Overview")
    print("=" * 50)
    
    features = [
        "✅ Fixed scrapy-playwright middleware error",
        "✅ Created fallback HTTP-based spider (no browser required)",
        "✅ Multiple selector strategies for robust data extraction",
        "✅ Comprehensive Google Maps link extraction (4 different methods)",
        "✅ Both CSV and SQLite database storage",
        "✅ Data validation and cleaning pipelines", 
        "✅ Focused on Bangalore doctors as requested",
        "✅ Error handling and retry mechanisms",
        "✅ Configurable speciality and location filtering",
        "✅ Structured data output with consistent schema"
    ]
    
    for feature in features:
        print(f"  {feature}")

def main():
    """Main demo function"""
    
    print("🏥 Doctor Fee Prediction Model - Scraper Demo")
    print("=" * 60)
    
    print("\nThis demo shows how the enhanced scraper works:")
    print("- Extracts doctor data from Practo")
    print("- Adds Google Maps links for each doctor") 
    print("- Saves data to both CSV and SQLite database")
    print("- Focuses on Bangalore doctors with multiple specialities")
    
    # Show scraper features
    show_scraper_features()
    
    # Show Google Maps functionality
    demonstrate_google_maps_functionality()
    
    print("\n📊 Creating Sample Data")
    print("=" * 30)
    
    # Create sample data
    sample_data = create_sample_data_with_maps()
    
    # Save to CSV
    df = save_to_csv(sample_data)
    
    # Save to database
    save_to_database(sample_data)
    
    print("\n📋 Sample Data Summary")
    print("=" * 25)
    print(f"Total Doctors: {len(sample_data)}")
    print(f"Specialities: {len(set(d['speciality'] for d in sample_data))}")
    print(f"All from: Bangalore")
    print(f"All have Google Maps links: ✅")
    
    # Show sample data
    print(f"\n📄 First 3 Records Preview:")
    print("-" * 40)
    for i, doctor in enumerate(sample_data[:3], 1):
        print(f"{i}. {doctor['name']} ({doctor['speciality']})")
        print(f"   Fee: ₹{doctor['consultation_fee']} | Rating: {doctor['dp_score']}")
        print(f"   Location: {doctor['location']}")
        print(f"   Google Maps: {doctor['google_map_link'][:50]}...")
        print()
    
    print("🎯 How to use the real scraper:")
    print("=" * 35)
    print("1. With internet access, run: cd practo_scraper && python run_scraper.py")
    print("2. Or use specific spider: scrapy crawl practo_doctors_simple")
    print("3. Data will be saved to data/ directory in both CSV and SQLite formats")
    print("4. Each doctor record includes Google Maps links for location")
    
    print("\n✨ Demo completed successfully!")

if __name__ == "__main__":
    main()