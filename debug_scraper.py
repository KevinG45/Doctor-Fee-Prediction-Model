#!/usr/bin/env python3
"""
Debug script to test individual doctor profile extraction
"""
import subprocess
import sys
import os

def run_single_doctor_test():
    """Run scraper for just one doctor to debug field extraction"""
    
    # Change to the practo_scraper directory
    os.chdir('practo_scraper')
    
    # Run a single doctor profile extraction with debug settings
    cmd = [
        'scrapy', 'crawl', 'practo_doctors',
        '-a', 'city=Bangalore',
        '-a', 'speciality=Dentist', 
        '-s', 'CLOSESPIDER_ITEMCOUNT=1',  # Stop after 1 item
        '-s', 'LOG_LEVEL=DEBUG',  # Verbose logging
        '-o', 'debug_single.csv',  # Output file
        '--logfile=debug.log'  # Log to file
    ]
    
    print("Running debug scrape for single doctor...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
            
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        # Check if output file was created
        if os.path.exists('debug_single.csv'):
            print("\n=== DEBUG OUTPUT CSV ===")
            with open('debug_single.csv', 'r') as f:
                print(f.read())
        else:
            print("No output CSV file generated")
            
        # Check log file for errors
        if os.path.exists('debug.log'):
            print("\n=== LAST 20 LINES OF DEBUG LOG ===")
            with open('debug.log', 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.strip())
                    
    except subprocess.TimeoutExpired:
        print("Script timed out after 120 seconds")
    except Exception as e:
        print(f"Error running script: {e}")

if __name__ == "__main__":
    run_single_doctor_test()