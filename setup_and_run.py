#!/usr/bin/env python3
"""
One-Click Setup and Run Script for Production Bangalore Doctors Scraper

This script handles:
1. Dependency verification
2. Environment setup
3. Quick test run
4. Full production run options

Usage:
    python setup_and_run.py                    # Setup and quick test
    python setup_and_run.py --full             # Setup and full production run  
    python setup_and_run.py --validate-only    # Just validate existing data
"""

import subprocess
import sys
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("Python 3.8+ required. Current version: {}.{}.{}".format(
            version.major, version.minor, version.micro))
        return False
    
    logger.info(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✅ Dependencies installed successfully")
            return True
        else:
            logger.error(f"Failed to install dependencies: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Dependency installation timed out")
        return False
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return False


def verify_setup():
    """Verify that scraper setup is correct"""
    logger.info("Verifying scraper setup...")
    
    # Check required files
    required_files = [
        'practo_scraper/scrapy.cfg',
        'practo_scraper/practo_scraper/spiders/robust_bangalore_doctors.py',
        'practo_scraper/practo_scraper/pipelines.py',
        'practo_scraper/practo_scraper/settings.py',
        'run_robust_scraper.py',
        'validate_production_scraper.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    # Check scrapy installation
    try:
        result = subprocess.run(['scrapy', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Scrapy installed: {result.stdout.strip()}")
        else:
            logger.error("Scrapy not properly installed")
            return False
    except FileNotFoundError:
        logger.error("Scrapy command not found")
        return False
    
    # Create data directories
    os.makedirs('practo_scraper/data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logger.info("✅ Setup verification completed")
    return True


def run_quick_test():
    """Run a quick test to verify scraper works"""
    logger.info("Running quick test (5 doctors)...")
    
    try:
        result = subprocess.run([
            sys.executable, 'run_robust_scraper.py', '--limit', '5', '--output', 'quick_test.csv'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✅ Quick test completed successfully")
            
            # Check if output file was created
            if os.path.exists('practo_scraper/quick_test.csv'):
                logger.info("✅ Test output file created")
                
                # Validate the test results
                validation_result = subprocess.run([
                    sys.executable, 'validate_production_scraper.py', '--csv-file', 'practo_scraper/quick_test.csv'
                ], capture_output=True, text=True)
                
                if validation_result.returncode == 0:
                    logger.info("✅ Test data validation passed")
                    return True
                else:
                    logger.warning("⚠️ Test data validation had warnings (check logs)")
                    return True
            else:
                logger.error("❌ Test output file not created")
                return False
        else:
            logger.error(f"Quick test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Quick test timed out")
        return False
    except Exception as e:
        logger.error(f"Error running quick test: {e}")
        return False


def run_full_production():
    """Run full production scraping"""
    logger.info("Starting FULL PRODUCTION SCRAPING...")
    logger.info("This will scrape ALL doctors in Bangalore across ALL specialities")
    logger.info("Estimated time: 2-4 hours depending on network speed")
    
    confirm = input("Continue with full production run? (y/N): ")
    if confirm.lower() != 'y':
        logger.info("Production run cancelled by user")
        return False
    
    try:
        # Run with timestamp-based output file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'bangalore_doctors_complete_{timestamp}.csv'
        
        logger.info(f"Starting production run - output: {output_file}")
        
        result = subprocess.run([
            sys.executable, 'run_robust_scraper.py', '--output', output_file, '--verbose'
        ], timeout=14400)  # 4 hour timeout
        
        if result.returncode == 0:
            logger.info("🎉 PRODUCTION RUN COMPLETED SUCCESSFULLY!")
            
            # Validate results
            logger.info("Validating production results...")
            validation_result = subprocess.run([
                sys.executable, 'validate_production_scraper.py', '--csv-file', f'practo_scraper/{output_file}'
            ])
            
            return True
        else:
            logger.error("Production run failed")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Production run timed out after 4 hours")
        return False
    except KeyboardInterrupt:
        logger.info("Production run interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Error in production run: {e}")
        return False


def validate_existing_data():
    """Validate existing data files"""
    logger.info("Looking for existing data files to validate...")
    
    csv_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.csv') and ('doctor' in file.lower() or 'bangalore' in file.lower()):
                csv_files.append(os.path.join(root, file))
    
    if not csv_files:
        logger.info("No CSV files found to validate")
        return True
    
    logger.info(f"Found {len(csv_files)} CSV files to validate:")
    for i, file in enumerate(csv_files, 1):
        logger.info(f"  {i}. {file}")
    
    for csv_file in csv_files:
        logger.info(f"\nValidating: {csv_file}")
        result = subprocess.run([
            sys.executable, 'validate_production_scraper.py', '--csv-file', csv_file
        ])
        
        if result.returncode == 0:
            logger.info(f"✅ {csv_file} validation passed")
        else:
            logger.warning(f"⚠️ {csv_file} validation had issues")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup and run production Bangalore doctors scraper')
    parser.add_argument('--full', action='store_true', help='Run full production scraping')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing data')
    parser.add_argument('--skip-test', action='store_true', help='Skip quick test')
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🏥 BANGALORE DOCTORS SCRAPER - PRODUCTION SETUP")
    logger.info("=" * 70)
    logger.info(f"Started at: {datetime.now()}")
    
    # Step 1: Check Python version
    if not check_python_version():
        return 1
    
    # Step 2: Validate-only mode
    if args.validate_only:
        return 0 if validate_existing_data() else 1
    
    # Step 3: Install dependencies
    if not install_dependencies():
        logger.error("Setup failed at dependency installation")
        return 1
    
    # Step 4: Verify setup
    if not verify_setup():
        logger.error("Setup verification failed")
        return 1
    
    # Step 5: Quick test (unless skipped)
    if not args.skip_test:
        if not run_quick_test():
            logger.error("Quick test failed - check configuration")
            return 1
    
    # Step 6: Full production run (if requested)
    if args.full:
        if not run_full_production():
            logger.error("Production run failed")
            return 1
    else:
        logger.info("=" * 70)
        logger.info("🎉 SETUP COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("Ready for production! Next steps:")
        logger.info("1. Run full scraping: python setup_and_run.py --full")
        logger.info("2. Or use manual runner: python run_robust_scraper.py")
        logger.info("3. Validate results: python validate_production_scraper.py")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)