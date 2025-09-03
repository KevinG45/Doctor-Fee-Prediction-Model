#!/usr/bin/env python3
"""
Enhanced Bangalore Scraper with Reactor Fix
"""

# Install asyncio reactor FIRST, before any other imports
import sys
if 'twisted.internet.reactor' not in sys.modules:
    try:
        import twisted.internet.asyncioreactor
        twisted.internet.asyncioreactor.install()
        print("✅ AsyncIO reactor installed")
    except Exception as e:
        print(f"⚠️  Reactor installation warning: {e}")

import os
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Run Bangalore Practo doctor data scraper (Fixed Version)')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--headless', default='true', 
                       help='Run browser in headless mode (true/false)')
    parser.add_argument('--delay', type=int, default=3,
                       help='Download delay in seconds (default: 3)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--limit', type=int,
                       help='Limit number of doctors to scrape (for testing)')
    
    args = parser.parse_args()
    
    # Navigate to the scrapy project directory
    project_dir = Path(__file__).parent / 'practo_scraper'
    if not project_dir.exists():
        print(f"Error: Scrapy project directory not found: {project_dir}")
        sys.exit(1)
    
    # Change to the scrapy project directory
    os.chdir(project_dir)
    
    # Prepare the scrapy command
    cmd = ['scrapy', 'crawl', 'bangalore_doctors']
    
    # Add custom settings
    settings = []
    
    if args.headless.lower() == 'false':
        settings.append('PLAYWRIGHT_LAUNCH_OPTIONS={"headless": false}')
    
    if args.delay:
        settings.append(f'DOWNLOAD_DELAY={args.delay}')
    
    if args.verbose:
        settings.append('LOG_LEVEL=DEBUG')
    else:
        settings.append('LOG_LEVEL=INFO')
    
    if args.limit:
        settings.append(f'CLOSESPIDER_ITEMCOUNT={args.limit}')
    
    # Force asyncio reactor
    settings.append('TWISTED_REACTOR=twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    
    # Add settings to command
    for setting in settings:
        cmd.extend(['-s', setting])
    
    # Add output file if specified
    if args.output:
        cmd.extend(['-o', args.output])
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    print("="*60)
    
    try:
        # Run the scrapy command
        result = subprocess.run(cmd, check=True)
        print("\n" + "="*60)
        print("✅ Scraping completed successfully!")
        
        # Show output files
        data_dir = Path('data')
        if data_dir.exists():
            csv_files = list(data_dir.glob('*.csv'))
            if csv_files:
                print(f"\n📊 Output files created:")
                for csv_file in csv_files:
                    print(f"  - {csv_file}")
            else:
                print("\n⚠️  No CSV files found in data directory")
        
        # Also check for any CSV files in current directory
        current_csv = list(Path('.').glob('*.csv'))
        if current_csv:
            print(f"\n📊 CSV files in current directory:")
            for csv_file in current_csv:
                print(f"  - {csv_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Scraping failed with exit code: {e.returncode}")
        print("💡 Try checking the log file: scrapy.log")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ Error: 'scrapy' command not found. Please install Scrapy:")
        print("   pip install scrapy scrapy-playwright")
        sys.exit(1)

if __name__ == '__main__':
    main()
