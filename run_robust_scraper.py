#!/usr/bin/env python3
"""
Robust Bangalore Doctor Scraper Runner

This script runs the improved, production-ready spider that:
1. Is fast and reliable (no Playwright, just HTTP requests)
2. Ensures no empty columns in output
3. Handles all specialities comprehensively  
4. Has robust error handling and recovery
5. Provides detailed progress tracking

Usage:
    python run_robust_scraper.py                    # Full scraping
    python run_robust_scraper.py --limit 100        # Test with limited results
    python run_robust_scraper.py --speciality dentist   # Single speciality
    python run_robust_scraper.py --output custom.csv    # Custom output file
"""

import argparse
import os
import sys
import subprocess
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_spider(spider_name='robust_bangalore_doctors', **kwargs):
    """Run the scrapy spider with given parameters"""
    
    # Change to the scrapy project directory
    scrapy_dir = os.path.join(os.getcwd(), 'practo_scraper')
    if not os.path.exists(scrapy_dir):
        logger.error(f"Scrapy project directory not found: {scrapy_dir}")
        return False
    
    os.chdir(scrapy_dir)
    
    # Build scrapy command
    cmd = ['scrapy', 'crawl', spider_name]
    
    # Add spider arguments
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend(['-a', f'{key}={value}'])
    
    # Add settings overrides
    if 'limit' in kwargs and kwargs['limit']:
        cmd.extend(['-s', f'CLOSESPIDER_ITEMCOUNT={kwargs["limit"]}'])
    
    # Set output file
    output_file = kwargs.get('output', f'data/bangalore_doctors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    cmd.extend(['-o', output_file])
    
    # Add verbose logging
    cmd.extend(['-L', 'INFO'])
    
    logger.info(f"Running command: {' '.join(cmd)}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    try:
        # Run the spider
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Spider completed in {duration:.1f} seconds")
        logger.info(f"Return code: {result.returncode}")
        
        if result.stdout:
            logger.info("STDOUT:")
            logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("STDERR:")
            logger.warning(result.stderr)
        
        # Check if output file was created
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"Output file created: {output_file} ({file_size:,} bytes)")
            
            # Count lines in output file
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for line in f)
                logger.info(f"Total records: {line_count - 1}")  # Subtract header
                
                # Show sample data
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        logger.info("Sample records:")
                        for i, line in enumerate(lines[:3]):  # Show header + 2 records
                            logger.info(f"  {i}: {line.strip()}")
                            
            except Exception as e:
                logger.error(f"Error reading output file: {e}")
                
        else:
            logger.error(f"Output file was not created: {output_file}")
            return False
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.error("Spider timed out after 2 hours")
        return False
    except Exception as e:
        logger.error(f"Error running spider: {e}")
        return False


def validate_scraper_setup():
    """Validate that the scraper is properly set up"""
    logger.info("Validating scraper setup...")
    
    # Check if scrapy is installed
    try:
        result = subprocess.run(['scrapy', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Scrapy version: {result.stdout.strip()}")
        else:
            logger.error("Scrapy is not properly installed")
            return False
    except FileNotFoundError:
        logger.error("Scrapy command not found. Please install scrapy: pip install scrapy")
        return False
    
    # Check if scrapy project exists
    scrapy_dir = os.path.join(os.getcwd(), 'practo_scraper')
    if not os.path.exists(scrapy_dir):
        logger.error(f"Scrapy project directory not found: {scrapy_dir}")
        return False
    
    # Check if spider file exists
    spider_file = os.path.join(scrapy_dir, 'practo_scraper', 'spiders', 'robust_bangalore_doctors.py')
    if not os.path.exists(spider_file):
        logger.error(f"Spider file not found: {spider_file}")
        return False
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(scrapy_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    logger.info("Scraper setup validation passed")
    return True


def main():
    parser = argparse.ArgumentParser(description='Run the robust Bangalore doctors scraper')
    parser.add_argument('--limit', type=int, help='Limit number of results (for testing)')
    parser.add_argument('--speciality', type=str, help='Scrape only specific speciality')
    parser.add_argument('--output', type=str, help='Output CSV filename')
    parser.add_argument('--test', action='store_true', help='Run in test mode (limit 50 results)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.test:
        args.limit = 50
        args.output = 'test_output.csv'
    
    logger.info("=" * 60)
    logger.info("ROBUST BANGALORE DOCTORS SCRAPER")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now()}")
    
    if args.limit:
        logger.info(f"Running in test mode with limit: {args.limit}")
    else:
        logger.info("Running full scraping (all specialities)")
    
    # Validate setup
    if not validate_scraper_setup():
        logger.error("Setup validation failed. Please fix the issues and try again.")
        return 1
    
    # Prepare spider arguments
    spider_args = {}
    if args.speciality:
        spider_args['speciality'] = args.speciality
    if args.limit:
        spider_args['limit'] = args.limit
    if args.output:
        spider_args['output'] = args.output
    
    # Run the spider
    success = run_spider(**spider_args)
    
    if success:
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Check the output CSV file for completeness")
        logger.info("2. Verify no empty columns exist")
        logger.info("3. Check for reasonable data distribution across specialities")
        logger.info("4. Review the log file for any errors or warnings")
        return 0
    else:
        logger.error("=" * 60)
        logger.error("SCRAPING FAILED")
        logger.error("=" * 60)
        logger.error("Please check the log files for detailed error information")
        return 1


if __name__ == "__main__":
    sys.exit(main())