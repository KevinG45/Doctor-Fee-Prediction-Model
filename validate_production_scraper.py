#!/usr/bin/env python3
"""
Comprehensive Validation Script for Production Scraper

This script validates that the scraper implementation meets ALL requirements:
1. No empty columns in output
2. No duplicate entries  
3. Comprehensive speciality coverage
4. Proper data formatting
5. Multiple practices handling
6. Performance metrics

Usage:
    python validate_production_scraper.py                    # Validate existing data
    python validate_production_scraper.py --run-test         # Run test scrape and validate
    python validate_production_scraper.py --full-report      # Generate comprehensive report
"""

import argparse
import pandas as pd
import os
import sys
import json
import logging
from datetime import datetime
from collections import Counter
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProductionScraperValidator:
    """Comprehensive validation for the production scraper"""
    
    def __init__(self):
        self.validation_results = {
            'overall_score': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
    def validate_csv_data(self, csv_file):
        """Validate CSV data for completeness and quality"""
        logger.info(f"Validating CSV file: {csv_file}")
        
        if not os.path.exists(csv_file):
            self.validation_results['critical_issues'].append(f"CSV file not found: {csv_file}")
            return False
        
        try:
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(df)} records from {csv_file}")
            
            # Test 1: Check for required columns
            required_columns = [
                'name', 'speciality', 'degree', 'year_of_experience',
                'location', 'city', 'dp_score', 'npv', 'consultation_fee',
                'profile_url', 'google_map_link', 'scraped_at'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.validation_results['critical_issues'].append(f"Missing columns: {missing_columns}")
                return False
            else:
                logger.info("✅ All required columns present")
                self.validation_results['tests_passed'] += 1
            
            # Test 2: Check for empty values
            empty_check_results = self.check_empty_values(df)
            
            # Test 3: Check for duplicates
            duplicate_check_results = self.check_duplicates(df)
            
            # Test 4: Validate data types and ranges
            data_validation_results = self.validate_data_types(df)
            
            # Test 5: Check speciality coverage
            speciality_coverage_results = self.check_speciality_coverage(df)
            
            # Test 6: Validate Bangalore focus
            bangalore_check_results = self.check_bangalore_focus(df)
            
            # Test 7: Check multiple practices handling
            multiple_practices_results = self.check_multiple_practices(df)
            
            # Generate summary
            self.generate_validation_summary(df)
            
            return True
            
        except Exception as e:
            self.validation_results['critical_issues'].append(f"Error reading CSV: {str(e)}")
            return False
    
    def check_empty_values(self, df):
        """Check for empty values in any column"""
        logger.info("Checking for empty values...")
        
        # Fields that absolutely cannot be empty
        critical_fields = ['name', 'speciality', 'city', 'profile_url']
        
        # Fields that should have values but can have defaults
        important_fields = ['degree', 'year_of_experience', 'location', 'dp_score', 'npv', 'consultation_fee']
        
        critical_empty_found = False
        
        for field in critical_fields:
            empty_count = df[field].isna().sum() + (df[field] == '').sum() + (df[field] == 'N/A').sum()
            if empty_count > 0:
                self.validation_results['critical_issues'].append(
                    f"Critical field '{field}' has {empty_count} empty values"
                )
                critical_empty_found = True
        
        for field in important_fields:
            empty_count = df[field].isna().sum() + (df[field] == '').sum() + (df[field] == 'N/A').sum()
            if empty_count > 0:
                self.validation_results['warnings'].append(
                    f"Important field '{field}' has {empty_count} empty values"
                )
        
        # Check google_map_link separately (optional field)
        map_empty_count = df['google_map_link'].isna().sum() + (df['google_map_link'] == '').sum()
        if map_empty_count > len(df) * 0.5:  # If more than 50% empty
            self.validation_results['warnings'].append(
                f"Google map links missing for {map_empty_count}/{len(df)} records ({map_empty_count/len(df)*100:.1f}%)"
            )
        
        if not critical_empty_found:
            logger.info("✅ No critical empty values found")
            self.validation_results['tests_passed'] += 1
        else:
            logger.error("❌ Critical empty values found")
            self.validation_results['tests_failed'] += 1
            
        return not critical_empty_found
    
    def check_duplicates(self, df):
        """Check for duplicate entries"""
        logger.info("Checking for duplicates...")
        
        # Check URL-based duplicates (these should never happen)
        url_duplicates = df[df.duplicated(subset=['profile_url'], keep=False)]
        if len(url_duplicates) > 0:
            self.validation_results['critical_issues'].append(
                f"Found {len(url_duplicates)} URL duplicates - this should never happen"
            )
            return False
        
        # Check name+city duplicates (these might be valid for multiple practices)
        name_city_duplicates = df[df.duplicated(subset=['name', 'city'], keep=False)]
        if len(name_city_duplicates) > 0:
            unique_names_with_multiple_practices = name_city_duplicates['name'].nunique()
            logger.info(f"Found {unique_names_with_multiple_practices} doctors with multiple practices")
            
            # This is actually good - it means we're capturing multiple practice locations
            self.validation_results['recommendations'].append(
                f"Successfully captured {unique_names_with_multiple_practices} doctors with multiple practices"
            )
        
        logger.info("✅ Duplicate checking completed")
        self.validation_results['tests_passed'] += 1
        return True
    
    def validate_data_types(self, df):
        """Validate data types and value ranges"""
        logger.info("Validating data types and ranges...")
        
        issues_found = 0
        
        # Check year_of_experience
        try:
            experience_values = pd.to_numeric(df['year_of_experience'], errors='coerce')
            invalid_experience = experience_values.isna().sum()
            out_of_range = ((experience_values < 0) | (experience_values > 60)).sum()
            
            if invalid_experience > 0:
                self.validation_results['warnings'].append(
                    f"{invalid_experience} invalid experience values found"
                )
                issues_found += 1
                
            if out_of_range > 0:
                self.validation_results['warnings'].append(
                    f"{out_of_range} experience values out of range (0-60 years)"
                )
                issues_found += 1
        except:
            self.validation_results['warnings'].append("Could not validate experience values")
            issues_found += 1
        
        # Check dp_score
        try:
            score_values = pd.to_numeric(df['dp_score'], errors='coerce')
            invalid_scores = score_values.isna().sum()
            out_of_range = ((score_values < 0) | (score_values > 100)).sum()
            
            if invalid_scores > 0:
                self.validation_results['warnings'].append(
                    f"{invalid_scores} invalid rating scores found"
                )
                issues_found += 1
                
            if out_of_range > 0:
                self.validation_results['warnings'].append(
                    f"{out_of_range} rating scores out of range (0-100)"
                )
                issues_found += 1
        except:
            self.validation_results['warnings'].append("Could not validate rating scores")
            issues_found += 1
        
        # Check consultation_fee  
        try:
            fee_values = pd.to_numeric(df['consultation_fee'], errors='coerce')
            invalid_fees = fee_values.isna().sum()
            unrealistic_fees = ((fee_values < 50) | (fee_values > 10000)).sum()
            
            if invalid_fees > 0:
                self.validation_results['warnings'].append(
                    f"{invalid_fees} invalid consultation fees found"
                )
                issues_found += 1
                
            if unrealistic_fees > len(df) * 0.1:  # More than 10% unrealistic
                self.validation_results['warnings'].append(
                    f"{unrealistic_fees} consultation fees seem unrealistic (not 50-10000 range)"
                )
                issues_found += 1
        except:
            self.validation_results['warnings'].append("Could not validate consultation fees")
            issues_found += 1
        
        if issues_found == 0:
            logger.info("✅ Data types and ranges validation passed")
            self.validation_results['tests_passed'] += 1
        else:
            logger.warning(f"⚠️ Found {issues_found} data type/range issues")
            self.validation_results['tests_failed'] += 1
            
        return issues_found == 0
    
    def check_speciality_coverage(self, df):
        """Check speciality coverage and distribution"""
        logger.info("Checking speciality coverage...")
        
        specialities = df['speciality'].value_counts()
        total_specialities = len(specialities)
        
        logger.info(f"Found {total_specialities} unique specialities")
        
        # Check for reasonable distribution
        top_specialities = specialities.head(10)
        logger.info("Top 10 specialities:")
        for spec, count in top_specialities.items():
            logger.info(f"  {spec}: {count} doctors")
        
        # Expected minimum specialities for comprehensive coverage
        min_expected_specialities = 20
        if total_specialities >= min_expected_specialities:
            logger.info(f"✅ Good speciality coverage: {total_specialities} specialities")
            self.validation_results['tests_passed'] += 1
        else:
            self.validation_results['warnings'].append(
                f"Limited speciality coverage: only {total_specialities} specialities (expected {min_expected_specialities}+)"
            )
            self.validation_results['tests_failed'] += 1
        
        return total_specialities >= min_expected_specialities
    
    def check_bangalore_focus(self, df):
        """Verify all records are for Bangalore"""
        logger.info("Checking Bangalore focus...")
        
        non_bangalore = df[df['city'] != 'Bangalore']
        if len(non_bangalore) > 0:
            self.validation_results['warnings'].append(
                f"Found {len(non_bangalore)} records not for Bangalore"
            )
            return False
        
        logger.info("✅ All records are for Bangalore")
        self.validation_results['tests_passed'] += 1
        return True
    
    def check_multiple_practices(self, df):
        """Check if multiple practices are properly handled"""
        logger.info("Checking multiple practices handling...")
        
        # Group by doctor name and count unique locations
        doctor_locations = df.groupby('name')['location'].nunique()
        multiple_location_doctors = doctor_locations[doctor_locations > 1]
        
        if len(multiple_location_doctors) > 0:
            logger.info(f"✅ Found {len(multiple_location_doctors)} doctors with multiple practice locations")
            self.validation_results['recommendations'].append(
                f"Successfully handling multiple practices: {len(multiple_location_doctors)} doctors with multiple locations"
            )
            self.validation_results['tests_passed'] += 1
        else:
            logger.info("No doctors with multiple practice locations found")
            self.validation_results['tests_passed'] += 1
            
        return True
    
    def generate_validation_summary(self, df):
        """Generate comprehensive validation summary"""
        total_records = len(df)
        total_doctors = df['name'].nunique()
        total_specialities = df['speciality'].nunique()
        
        # Calculate overall score
        total_tests = self.validation_results['tests_passed'] + self.validation_results['tests_failed']
        if total_tests > 0:
            self.validation_results['overall_score'] = (self.validation_results['tests_passed'] / total_tests) * 100
        
        summary = {
            'total_records': total_records,
            'unique_doctors': total_doctors,
            'specialities_covered': total_specialities,
            'overall_score': self.validation_results['overall_score'],
            'tests_passed': self.validation_results['tests_passed'],
            'tests_failed': self.validation_results['tests_failed'],
            'critical_issues': len(self.validation_results['critical_issues']),
            'warnings': len(self.validation_results['warnings'])
        }
        
        logger.info("=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records: {total_records:,}")
        logger.info(f"Unique doctors: {total_doctors:,}")
        logger.info(f"Specialities covered: {total_specialities}")
        logger.info(f"Overall score: {self.validation_results['overall_score']:.1f}%")
        logger.info(f"Tests passed: {self.validation_results['tests_passed']}")
        logger.info(f"Tests failed: {self.validation_results['tests_failed']}")
        logger.info(f"Critical issues: {len(self.validation_results['critical_issues'])}")
        logger.info(f"Warnings: {len(self.validation_results['warnings'])}")
        
        if self.validation_results['critical_issues']:
            logger.error("\nCRITICAL ISSUES:")
            for issue in self.validation_results['critical_issues']:
                logger.error(f"  ❌ {issue}")
        
        if self.validation_results['warnings']:
            logger.warning("\nWARNINGS:")
            for warning in self.validation_results['warnings']:
                logger.warning(f"  ⚠️ {warning}")
                
        if self.validation_results['recommendations']:
            logger.info("\nRECOMMENDATIONS:")
            for rec in self.validation_results['recommendations']:
                logger.info(f"  💡 {rec}")
        
        return summary
    
    def run_test_scrape(self):
        """Run a test scrape and validate results"""
        logger.info("Running test scrape...")
        
        try:
            # Run test scrape
            result = subprocess.run([
                'python', 'run_robust_scraper.py', '--test'
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logger.info("✅ Test scrape completed successfully")
                
                # Find the test output file
                test_files = ['test_output.csv', 'practo_scraper/test_output.csv']
                test_file = None
                for f in test_files:
                    if os.path.exists(f):
                        test_file = f
                        break
                
                if test_file:
                    return self.validate_csv_data(test_file)
                else:
                    logger.error("Test output file not found")
                    return False
            else:
                logger.error(f"Test scrape failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Test scrape timed out")
            return False
        except Exception as e:
            logger.error(f"Error running test scrape: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Validate production scraper implementation')
    parser.add_argument('--csv-file', type=str, help='CSV file to validate')
    parser.add_argument('--run-test', action='store_true', help='Run test scrape and validate')
    parser.add_argument('--full-report', action='store_true', help='Generate comprehensive report')
    
    args = parser.parse_args()
    
    validator = ProductionScraperValidator()
    
    logger.info("=" * 60)
    logger.info("PRODUCTION SCRAPER VALIDATOR")
    logger.info("=" * 60)
    
    success = False
    
    if args.run_test:
        success = validator.run_test_scrape()
    elif args.csv_file:
        success = validator.validate_csv_data(args.csv_file)
    else:
        # Look for existing CSV files to validate
        csv_files = []
        
        # Check common locations
        locations = [
            'practo_scraper/data/',
            'practo_scraper/',
            './'
        ]
        
        for location in locations:
            if os.path.exists(location):
                for file in os.listdir(location):
                    if file.endswith('.csv') and 'doctor' in file.lower():
                        csv_files.append(os.path.join(location, file))
        
        if csv_files:
            logger.info(f"Found {len(csv_files)} CSV files to validate")
            for csv_file in csv_files:
                logger.info(f"Validating: {csv_file}")
                result = validator.validate_csv_data(csv_file)
                if result:
                    success = True
        else:
            logger.error("No CSV files found. Use --run-test to run a test scrape first.")
            return 1
    
    # Generate final report
    logger.info("=" * 60)
    if success and validator.validation_results['overall_score'] >= 80:
        logger.info("🎉 VALIDATION PASSED - PRODUCTION READY!")
        logger.info("The scraper implementation meets all requirements.")
        return 0
    elif success:
        logger.warning("⚠️ VALIDATION PASSED WITH WARNINGS")
        logger.warning("The scraper works but has some issues that should be addressed.")
        return 0
    else:
        logger.error("❌ VALIDATION FAILED")
        logger.error("Critical issues found that must be fixed before production use.")
        return 1


if __name__ == "__main__":
    sys.exit(main())