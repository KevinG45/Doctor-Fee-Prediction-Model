# Web Scraping Improvements: Playwright + Scrapy Implementation

## Overview

This repository now includes an improved web scraping solution that replaces the original Selenium-based approach with a more robust and scalable implementation using **Scrapy framework** and **Playwright** for browser automation.

## 🔧 Improvements Made

### 1. **Framework Upgrade**
- **From**: Basic Selenium script with BeautifulSoup
- **To**: Professional Scrapy framework with structured project organization

### 2. **Browser Automation**
- **From**: Selenium WebDriver
- **To**: Playwright (faster, more reliable, better JavaScript handling)

### 3. **Code Issues Fixed**
- ✅ Fixed deprecated `pandas.DataFrame.append()` method
- ✅ Added proper error handling and retry mechanisms
- ✅ Improved data validation and cleaning
- ✅ Better logging and monitoring

### 4. **Performance Improvements**
- Concurrent request handling
- Intelligent throttling and rate limiting
- HTTP caching for efficiency
- Automatic retry on failures

### 5. **Data Quality**
- Structured data pipelines for validation and cleaning
- Consistent data formatting
- Better extraction logic with fallbacks
- Timestamp tracking for data freshness

## 📁 New Project Structure

```
Doctor-Fee-Prediction-Model/
├── requirements.txt                    # Dependencies
├── config.py                          # Configuration settings
├── run_scraper.py                     # Easy-to-use runner script
├── improved_web_scraper.py            # Improved Selenium version (fallback)
├── practo_scraper/                    # Scrapy project
│   ├── scrapy.cfg
│   └── practo_scraper/
│       ├── __init__.py
│       ├── settings.py               # Scrapy configuration
│       ├── items.py                  # Data structure definitions
│       ├── pipelines.py              # Data processing pipelines
│       ├── middlewares.py            # Custom middlewares
│       └── spiders/
│           ├── __init__.py
│           ├── practo_doctors.py     # Playwright-based spider
│           └── practo_doctors_simple.py  # HTTP-based spider
└── data/                             # Output directory
    └── *.csv                        # Generated data files
```

## 🚀 Usage

### Method 1: Using the Easy Runner Script
```bash
# Run with default settings
python run_scraper.py

# Run with custom options
python run_scraper.py --spider=practo_doctors_simple --limit=100 --city=Bangalore

# Save to specific file
python run_scraper.py --output=my_doctors_data.csv
```

### Method 2: Using Scrapy Directly
```bash
cd practo_scraper
scrapy crawl practo_doctors_simple
```

### Method 3: Using the Improved Selenium Script (Fallback)
```bash
python improved_web_scraper.py
```

## 🔧 Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. For Playwright (if using the full-featured spider):
```bash
playwright install chromium
```

## ⚙️ Configuration

Edit `config.py` to customize:
- Cities to scrape
- Medical specialities
- Output settings
- Request delays and limits

## 📊 Data Output

The scrapers generate CSV files with the following structure:

| Column | Description |
|--------|-------------|
| name | Doctor's name |
| speciality | Medical speciality |
| degree | Educational qualifications |
| year_of_experience | Years of practice |
| location | Clinic/hospital location |
| city | City (Bangalore, Delhi, Mumbai) |
| dp_score | Doctor's rating score |
| npv | Number of patient votes/reviews |
| consultation_fee | Consultation fee amount |
| profile_url | Practo profile URL |
| scraped_at | Timestamp of data collection |

## 🚦 Features

### Data Quality Pipelines
- **ValidationPipeline**: Ensures required fields are present
- **CleaningPipeline**: Standardizes and cleans data formats
- **CsvExportPipeline**: Exports clean data to CSV

### Error Handling
- Automatic retry on failed requests
- Graceful handling of missing data
- Comprehensive logging
- Rate limiting to avoid being blocked

### Performance Optimizations
- Concurrent request processing
- Intelligent throttling
- HTTP caching
- Memory-efficient data processing

## 🔄 Migration from Old Implementation

The original web scraping implementation had several issues:

1. **Deprecated pandas methods**: Used `df.append()` which is deprecated
2. **Poor error handling**: No retry mechanisms or graceful failure handling
3. **Inefficient**: Sequential processing without concurrency
4. **Maintenance**: Difficult to modify and extend

The new implementation addresses all these issues while maintaining compatibility with the existing data format.

## 📈 Performance Comparison

| Metric | Old Implementation | New Implementation |
|--------|-------------------|-------------------|
| Framework | Selenium + BeautifulSoup | Scrapy + Playwright |
| Concurrency | None | Yes (configurable) |
| Error Handling | Basic | Comprehensive |
| Data Validation | None | Built-in pipelines |
| Retry Logic | Manual | Automatic |
| Caching | None | HTTP caching |
| Monitoring | Basic prints | Structured logging |

## 🛠️ Customization

### Adding New Cities or Specialities
Edit the lists in `config.py` or `practo_scraper/practo_scraper/spiders/practo_doctors_simple.py`

### Custom Data Processing
Modify the pipelines in `practo_scraper/practo_scraper/pipelines.py`

### Request Settings
Adjust delays, concurrency, and other settings in `practo_scraper/practo_scraper/settings.py`

## 🤝 Contributing

To extend this scraping solution:

1. Add new spiders in the `spiders/` directory
2. Create custom pipelines for additional data processing
3. Add new item fields in `items.py`
4. Configure new settings as needed

## 📝 Notes

- Always respect the website's robots.txt and terms of service
- Use appropriate delays between requests to avoid overwhelming the server
- Monitor your scraping to ensure it doesn't violate any usage policies
- The data is for educational and research purposes only