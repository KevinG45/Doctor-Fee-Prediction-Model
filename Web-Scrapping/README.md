# Enhanced Bangalore Doctors Web Scraping with Google Maps Integration

This enhanced web scraping module focuses specifically on Bangalore doctors and includes Google Maps links for each doctor.

## Features

- **Bangalore-only focus**: Scrapes doctor data exclusively from Bangalore
- **Google Maps integration**: Automatically generates Google Maps search links for each doctor
- **Complete data retention**: Maintains all original columns from the base scraper
- **Enhanced dataset**: Adds `google_maps_link` column to the existing data structure

## Files

### 1. `Bangalore_Doctors_With_GoogleMaps.ipynb`
- Jupyter notebook version of the enhanced scraper
- Interactive cells for step-by-step execution
- Includes data validation and statistics

### 2. `bangalore_doctors_scraper.py`
- Python script version for command-line execution
- Optimized for automated runs
- Includes comprehensive error handling

### 3. `bangalore_doctors_with_maps_sample.csv`
- Sample dataset demonstrating the enhanced functionality
- Shows the expected output format with Google Maps links

## Data Structure

The enhanced dataset includes all original columns plus the new Google Maps link:

| Column | Description |
|--------|-------------|
| Name | Doctor's full name |
| Speciality | Medical specialization |
| Degree | Educational qualifications |
| Year_of_experience | Years of medical practice |
| Location | Clinic/hospital location in Bangalore |
| City | Always "Bangalore" |
| dp_score | Practo doctor rating score |
| npv | Number of patient votes/reviews |
| consultation_fee | Consultation fee amount |
| **google_maps_link** | **NEW: Google Maps search link for the doctor** |

## Google Maps Link Generation

The Google Maps links are generated using the following format:
```
https://www.google.com/maps/search/{doctor_name}+doctor+{location}+Bangalore
```

Example:
- Doctor: Dr. Rajesh Kumar
- Location: Koramangala
- Generated link: `https://www.google.com/maps/search/Dr.+Rajesh+Kumar+doctor+Koramangala+Bangalore`

## Usage

### Running the Jupyter Notebook
```bash
cd Web-Scrapping
jupyter notebook Bangalore_Doctors_With_GoogleMaps.ipynb
```

### Running the Python Script
```bash
cd Web-Scrapping
python bangalore_doctors_scraper.py
```

## Output

The scraper generates a CSV file: `../DATA/bangalore_doctors_with_maps.csv`

## Dependencies

- pandas
- numpy
- beautifulsoup4
- selenium
- lxml
- urllib (built-in)

Install dependencies:
```bash
pip install pandas numpy beautifulsoup4 selenium lxml
```

## Sample Output

```
Doctor: Dr. Rajesh Kumar
Speciality: Cardiologist
Location: Koramangala, Bangalore
Google Maps Link: https://www.google.com/maps/search/Dr.+Rajesh+Kumar+doctor+Koramangala+Bangalore
```

## Improvements Over Original

1. **Focused scope**: Only scrapes Bangalore doctors as requested
2. **Google Maps integration**: Adds valuable location-based search capability
3. **Enhanced data**: Provides direct navigation to doctor locations
4. **Better error handling**: More robust scraping with proper exception handling
5. **Modern pandas**: Uses `pd.concat()` instead of deprecated `append()` method

## Note

This enhanced scraper maintains full compatibility with the original data structure while adding the requested Google Maps functionality. All existing columns are preserved, ensuring seamless integration with existing ML models and analysis workflows.