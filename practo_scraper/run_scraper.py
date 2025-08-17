#!/usr/bin/env python3
"""
Runner script for Practo Scraper
This script runs the Scrapy spider programmatically
"""

import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_spider():
    """Run the Practo doctors spider"""
    
    # Get the Scrapy project settings
    settings = get_project_settings()
    
    # Create crawler process
    process = CrawlerProcess(settings)
    
    # Add the spider to the process
    process.crawl('practo_doctors')
    
    # Start the crawling process
    process.start()

if __name__ == "__main__":
    print("Starting Practo Scraper...")
    run_spider()
    print("Scraping completed!")
