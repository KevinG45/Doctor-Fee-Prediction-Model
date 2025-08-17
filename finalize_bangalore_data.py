#!/usr/bin/env python3
"""
Final data processing script to filter Bangalore doctors only and fix Google Maps links
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_bangalore_doctors():
    """Filter for Bangalore doctors only and fix Google Maps links"""
    
    # Load cleaned data
    df = pd.read_csv("bangalore_doctors_cleaned_20250817_151657.csv")
    logger.info(f"Loaded {len(df)} total records")
    
    # Filter for Bangalore only
    bangalore_df = df[df['city'] == 'Bangalore'].copy()
    logger.info(f"Filtered to {len(bangalore_df)} Bangalore records")
    
    # Fix Google Maps links to use correct city
    def fix_google_maps_link(row):
        location = str(row['location']).strip()
        if location and location != 'nan':
            search_query = f"{location}, Bangalore, Karnataka, India"
            return f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        return ""
    
    bangalore_df['google_map_link'] = bangalore_df.apply(fix_google_maps_link, axis=1)
    
    # Final cleanup - remove records with nan locations
    bangalore_df = bangalore_df[bangalore_df['location'] != 'nan'].copy()
    logger.info(f"Final count after removing nan locations: {len(bangalore_df)}")
    
    # Save final dataset
    output_file = "bangalore_doctors_final.csv"
    bangalore_df.to_csv(output_file, index=False)
    logger.info(f"Saved final dataset to {output_file}")
    
    # Generate final report
    logger.info("\n=== FINAL DATASET SUMMARY ===")
    logger.info(f"Total Bangalore doctors: {len(bangalore_df)}")
    logger.info(f"Specialities covered: {bangalore_df['speciality'].nunique()}")
    logger.info(f"Records with Google Maps: {(bangalore_df['google_map_link'] != '').sum()}")
    logger.info(f"Records with location: {(bangalore_df['location'] != '').sum()}")
    logger.info(f"Records with consultation fee: {(bangalore_df['consultation_fee'] > 0).sum()}")
    
    logger.info("\nTop 10 specialities:")
    for spec, count in bangalore_df['speciality'].value_counts().head(10).items():
        logger.info(f"  {spec}: {count}")
    
    logger.info("\nTop 10 locations:")
    for loc, count in bangalore_df['location'].value_counts().head(10).items():
        logger.info(f"  {loc}: {count}")
    
    return output_file

if __name__ == "__main__":
    filter_bangalore_doctors()