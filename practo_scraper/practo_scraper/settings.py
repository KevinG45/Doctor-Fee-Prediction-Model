# Scrapy settings for practo_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "practo_scraper"

SPIDER_MODULES = ["practo_scraper.spiders"]
NEWSPIDER_MODULE = "practo_scraper.spiders"

ADDONS = {}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules - IMPORTANT: Set to True for production
ROBOTSTXT_OBEY = True

# Optimized concurrency and throttling settings for speed while being respectful
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2
DOWNLOAD_DELAY = 1  # Reduced for faster scraping
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (not needed for this scraping)
COOKIES_ENABLED = False

# Disable Telnet Console (not needed)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    "practo_scraper.middlewares.PractoScraperSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "practo_scraper.middlewares.PractoScraperDownloaderMiddleware": 543,
}

# Disable Playwright for the robust spider (not needed)
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }

# Configure item pipelines - CRITICAL ORDER for data quality
ITEM_PIPELINES = {
    'practo_scraper.pipelines.ValidationPipeline': 300,   # First: Validate and fill defaults
    'practo_scraper.pipelines.CleaningPipeline': 400,     # Second: Clean and normalize data  
    'practo_scraper.pipelines.DeduplicationPipeline': 500, # Third: Remove duplicates
    'practo_scraper.pipelines.DatabasePipeline': 600,     # Fourth: Save to database
    'practo_scraper.pipelines.CsvExportPipeline': 700,    # Fifth: Export to CSV
}

# Enable and configure the AutoThrottle extension for adaptive throttling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5  # Reduced maximum delay
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = True

# Enhanced retry configuration for reliability
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403, 404]

# Enable HTTP caching for efficiency
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403, 404]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "scrapy.log"

# Custom settings for feeds with comprehensive field list
FEEDS = {
    "data/doctors_%(time)s.csv": {
        "format": "csv",
        "encoding": "utf8",
        "store_empty": False,
        "fields": [
            "name", "speciality", "degree", "year_of_experience", 
            "location", "city", "dp_score", "npv", "consultation_fee", 
            "profile_url", "google_map_link", "scraped_at"
        ],
    },
}

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# Additional settings for robustness
DUPEFILTER_DEBUG = True
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Reactor setting to prevent SSL issues
REACTOR_THREADPOOL_MAXSIZE = 20
