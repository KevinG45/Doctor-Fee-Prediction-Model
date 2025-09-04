#!/usr/bin/env python3
"""
Comprehensive Bangalore Doctors Scraper Runner
Following the detailed execution plan from the problem statement

This script implements the complete execution strategy with:
- Phase 1: Environment preparation and anti-detection
- Phase 2: Two-level scraping architecture
- Phase 3: Implementation with monitoring
- Phase 4: Staged execution approach
- Phase 5: Data validation and quality assurance
- Phase 6: Success criteria and deliverables

Usage:
    python run_comprehensive_scraper.py [--mode=MODE] [--limit=NUMBER] [--specialties=LIST]
    
Examples:
    python run_comprehensive_scraper.py --mode=proof                    # Proof of concept (limited)
    python run_comprehensive_scraper.py --mode=test                     # Single specialty test
    python run_comprehensive_scraper.py --mode=production               # Full production run
    python run_comprehensive_scraper.py --specialties="Cardiologist,Dentist" --limit=100
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveScrapeRunner:
    """
    Main runner class implementing the execution strategy from problem statement
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.project_dir = os.path.join(os.path.dirname(__file__), 'practo_scraper')
        
        # Expected results from problem statement
        self.targets = {
            'proof': {'doctors': 50, 'specialties': 1, 'description': 'Proof of concept'},
            'test': {'doctors': 200, 'specialties': 3, 'description': 'Single specialty test'}, 
            'production': {'doctors': 4500, 'specialties': 37, 'description': 'Full production run'}
        }
    
    def run(self, mode='production', limit=None, specialties=None, output=None):
        """
        Execute the comprehensive scraping strategy
        """
        logger.info("="*60)
        logger.info("COMPREHENSIVE BANGALORE DOCTORS SCRAPING PROJECT")
        logger.info("="*60)
        
        # Phase 1: Environment preparation
        self.prepare_environment()
        
        # Phase 4: Staged execution approach
        if mode == 'proof':
            return self.run_proof_of_concept(limit or 50)
        elif mode == 'test':
            return self.run_specialty_test(specialties or ['Cardiologist'], limit or 200)
        elif mode == 'production':
            return self.run_production(limit)
        else:
            logger.error(f"Unknown mode: {mode}")
            return False
    
    def prepare_environment(self):
        """
        Phase 1: Environment preparation and dependency check
        """
        logger.info("Phase 1: Environment Preparation")
        
        # Check if we're in the right directory
        if not os.path.exists(self.project_dir):
            logger.error(f"Scrapy project directory not found: {self.project_dir}")
            sys.exit(1)
        
        # Change to project directory
        os.chdir(self.project_dir)
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Verify scrapy installation
        try:
            result = subprocess.run(['scrapy', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Scrapy version: {result.stdout.strip()}")
            else:
                logger.error("Scrapy not properly installed")
                sys.exit(1)
        except FileNotFoundError:
            logger.error("Scrapy command not found")
            sys.exit(1)
        
        # Create data directory
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Data directory ready: {data_dir}")
        
        logger.info("✅ Environment preparation completed")
    
    def run_proof_of_concept(self, limit=50):
        """
        Stage 1: Proof of Concept (Phase 4)
        Test with single specialty and limited doctors
        """
        logger.info("Stage 1: Proof of Concept Execution")
        logger.info(f"Target: {limit} doctors from Cardiologist specialty")
        
        cmd = [
            'scrapy', 'crawl', 'comprehensive_bangalore_doctors',
            '-s', f'CLOSESPIDER_ITEMCOUNT={limit}',
            '-s', 'CONCURRENT_REQUESTS=1',
            '-s', 'DOWNLOAD_DELAY=2',
            '-o', f'data/proof_of_concept_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        ]
        
        success = self.execute_scrapy_command(cmd, "Proof of Concept")
        
        if success:
            self.validate_results(limit, 1, "proof of concept")
        
        return success
    
    def run_specialty_test(self, specialties, limit=200):
        """
        Stage 2: Full Specialty Test (Phase 4)
        Test with specific specialties
        """
        logger.info("Stage 2: Specialty Test Execution")
        logger.info(f"Target: {limit} doctors from {len(specialties)} specialties: {', '.join(specialties)}")
        
        cmd = [
            'scrapy', 'crawl', 'comprehensive_bangalore_doctors',
            '-s', f'CLOSESPIDER_ITEMCOUNT={limit}',
            '-s', 'CONCURRENT_REQUESTS=1',
            '-s', 'DOWNLOAD_DELAY=3',
            '-o', f'data/specialty_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        ]
        
        success = self.execute_scrapy_command(cmd, "Specialty Test")
        
        if success:
            self.validate_results(limit, len(specialties), "specialty test")
        
        return success
    
    def run_production(self, limit=None):
        """
        Stage 3: Production Run (Phase 4)
        Execute all specialties for comprehensive scraping
        """
        logger.info("Stage 3: Production Run Execution")
        logger.info("Target: 4500+ doctors from 37 specialties")
        logger.info("Expected duration: 12-24 hours")
        
        cmd = [
            'scrapy', 'crawl', 'comprehensive_bangalore_doctors',
            '-s', 'CONCURRENT_REQUESTS=1',
            '-s', 'DOWNLOAD_DELAY=3',
            '-s', 'RANDOMIZE_DOWNLOAD_DELAY=True',
            '-s', 'AUTOTHROTTLE_ENABLED=True',
            '-o', f'data/bangalore_doctors_comprehensive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            '-L', 'INFO'
        ]
        
        if limit:
            cmd.extend(['-s', f'CLOSESPIDER_ITEMCOUNT={limit}'])
        
        logger.info("🚀 Starting comprehensive production scraping...")
        logger.info("Monitor progress in real-time with:")
        logger.info("tail -f scrapy.log | grep 'PROGRESS\\|Found\\|SUCCESS\\|ERROR'")
        
        success = self.execute_scrapy_command(cmd, "Production Run", monitor=True)
        
        if success:
            target_doctors = limit or self.targets['production']['doctors']
            target_specialties = self.targets['production']['specialties']
            self.validate_results(target_doctors, target_specialties, "production")
            self.generate_final_report()
        
        return success
    
    def execute_scrapy_command(self, cmd, stage_name, monitor=False):
        """
        Execute scrapy command with monitoring and error handling
        """
        logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            if monitor:
                # For production runs, show real-time output
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor progress in real-time
                for line in iter(process.stdout.readline, ''):
                    if line:
                        # Filter important messages
                        if any(keyword in line for keyword in ['PROGRESS', 'Found', 'SUCCESS', 'ERROR', 'Spider closed']):
                            print(line.rstrip())
                
                process.wait()
                success = process.returncode == 0
            else:
                # For smaller runs, wait for completion
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                success = result.returncode == 0
                
                if not success:
                    logger.error(f"Scrapy command failed: {result.stderr}")
                else:
                    logger.info(f"✅ {stage_name} completed successfully")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout after 1 hour: {stage_name}")
            return False
        except Exception as e:
            logger.error(f"Error executing {stage_name}: {e}")
            return False
    
    def validate_results(self, expected_doctors, expected_specialties, stage_name):
        """
        Phase 5: Data validation and quality assurance
        """
        logger.info(f"Phase 5: Validating {stage_name} results")
        
        # Find the most recent CSV file
        data_dir = 'data'
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            logger.error("No CSV output files found")
            return False
        
        latest_file = max(csv_files, key=lambda f: os.path.getctime(os.path.join(data_dir, f)))
        file_path = os.path.join(data_dir, latest_file)
        
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            actual_doctors = len(df)
            actual_specialties = df['speciality'].nunique() if 'speciality' in df.columns else 0
            
            logger.info(f"Results validation for {latest_file}:")
            logger.info(f"  Doctors found: {actual_doctors} (target: {expected_doctors})")
            logger.info(f"  Specialties: {actual_specialties} (target: {expected_specialties})")
            
            # Quality metrics
            if 'name' in df.columns:
                non_empty_names = df['name'].notna().sum()
                logger.info(f"  Names completion: {non_empty_names}/{actual_doctors} ({(non_empty_names/actual_doctors)*100:.1f}%)")
            
            if 'consultation_fee' in df.columns:
                non_zero_fees = (df['consultation_fee'] > 0).sum()
                logger.info(f"  Fees specified: {non_zero_fees}/{actual_doctors} ({(non_zero_fees/actual_doctors)*100:.1f}%)")
            
            # Success criteria evaluation
            min_acceptable = max(expected_doctors * 0.5, 100)  # At least 50% of target or 100 minimum
            
            if actual_doctors >= expected_doctors:
                logger.info(f"✅ SUCCESS: Exceeded target of {expected_doctors} doctors!")
                return True
            elif actual_doctors >= min_acceptable:
                logger.info(f"✅ ACCEPTABLE: Met minimum threshold ({min_acceptable} doctors)")
                return True
            else:
                logger.warning(f"⚠️  BELOW TARGET: Only {actual_doctors} doctors (minimum: {min_acceptable})")
                return False
                
        except Exception as e:
            logger.error(f"Error validating results: {e}")
            return False
    
    def generate_final_report(self):
        """
        Phase 6: Success criteria and deliverables
        """
        logger.info("Phase 6: Generating Final Report")
        
        elapsed_time = datetime.now() - self.start_time
        
        logger.info("="*60)
        logger.info("COMPREHENSIVE SCRAPING PROJECT - FINAL REPORT")
        logger.info("="*60)
        logger.info(f"Total execution time: {elapsed_time}")
        logger.info(f"Start time: {self.start_time}")
        logger.info(f"End time: {datetime.now()}")
        
        # List all generated files
        data_dir = 'data'
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            logger.info(f"\nGenerated deliverables ({len(csv_files)} files):")
            for file in sorted(csv_files):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path)
                logger.info(f"  📄 {file} ({file_size:,} bytes)")
        
        logger.info("\n🎯 Project completed successfully!")
        logger.info("Review the CSV files in the 'data' directory for complete results.")


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive Bangalore Doctors Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_comprehensive_scraper.py --mode=proof
  python run_comprehensive_scraper.py --mode=test --specialties="Cardiologist,Dentist"
  python run_comprehensive_scraper.py --mode=production
  python run_comprehensive_scraper.py --mode=production --limit=1000
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['proof', 'test', 'production'],
        default='production',
        help='Execution mode (default: production)'
    )
    
    parser.add_argument(
        '--limit', 
        type=int,
        help='Limit number of doctors to scrape'
    )
    
    parser.add_argument(
        '--specialties',
        help='Comma-separated list of specialties (for test mode)'
    )
    
    parser.add_argument(
        '--output',
        help='Custom output file path'
    )
    
    args = parser.parse_args()
    
    # Parse specialties if provided
    specialties_list = None
    if args.specialties:
        specialties_list = [s.strip() for s in args.specialties.split(',')]
    
    # Create and run scraper
    runner = ComprehensiveScrapeRunner()
    
    try:
        success = runner.run(
            mode=args.mode,
            limit=args.limit,
            specialties=specialties_list,
            output=args.output
        )
        
        if success:
            logger.info("🎉 Scraping project completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Scraping project failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()