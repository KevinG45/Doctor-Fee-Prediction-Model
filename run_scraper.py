#!/usr/bin/env python3
"""
Practo Doctor Data Scraper

This script runs the improved web scraping solution using Scrapy framework
to extract doctor information from Practo website.

Usage:
    python run_scraper.py [--spider=spider_name] [--limit=number]
    
Examples:
    python run_scraper.py                          # Run default spider
    python run_scraper.py --spider=practo_doctors_simple  # Run simple spider
    python run_scraper.py --limit=100             # Limit to 100 doctors
"""

import os
import sys
import argparse
from scrapy.cmdline import execute
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    parser = argparse.ArgumentParser(description='Run Practo doctor data scraper')
    parser.add_argument('--spider', default='practo_doctors_simple', 
                       help='Spider to run (default: practo_doctors_simple)')
    parser.add_argument('--limit', type=int, help='Limit number of doctors to scrape')
    parser.add_argument('--city', help='Scrape only specific city')
    parser.add_argument('--speciality', help='Scrape only specific speciality')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Change to the scrapy project directory
    project_dir = os.path.join(os.path.dirname(__file__), 'practo_scraper')
    os.chdir(project_dir)
    
    # Set up the command
    cmd = ['scrapy', 'crawl', args.spider]
    
    # Add custom settings if provided
    if args.limit:
        cmd.extend(['-s', f'CLOSESPIDER_ITEMCOUNT={args.limit}'])
    
    if args.output:
        cmd.extend(['-o', args.output])
    
    # Add spider arguments
    spider_args = []
    if args.city:
        spider_args.append(f'city={args.city}')
    if args.speciality:
        spider_args.append(f'speciality={args.speciality}')
    
    if spider_args:
        cmd.extend(['-a', ','.join(spider_args)])
    
    print(f"Running command: {' '.join(cmd)}")
    print("Starting Practo doctor data scraping...")
    print("This may take a while depending on the amount of data to scrape.")
    print("Check the logs for progress updates.")
    
    # Execute the scrapy command
    try:
        execute(cmd)
        print("\nScraping completed successfully!")
        print("Check the 'data' directory for output files.")
    except Exception as e:
        print(f"\nError running scraper: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()