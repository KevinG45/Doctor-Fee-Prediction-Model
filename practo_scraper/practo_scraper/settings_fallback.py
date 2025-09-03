# Fallback settings for when Playwright is not available
BOT_NAME = "practo_scraper"

SPIDER_MODULES = ["practo_scraper.spiders"]
NEWSPIDER_MODULE = "practo_scraper.spiders"

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies
COOKIES_ENABLED = False

# Standard HTTP handlers (no Playwright)
DOWNLOAD_HANDLERS = {
    "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
    "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
}

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Enable spider middlewares
SPIDER_MIDDLEWARES = {
    "practo_scraper.middlewares.PractoScraperSpiderMiddleware": 543,
}

# Enable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "practo_scraper.middlewares.PractoScraperDownloaderMiddleware": 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "practo_scraper.pipelines.DeduplicationPipeline": 200,
    "practo_scraper.pipelines.ValidationPipeline": 300,
    "practo_scraper.pipelines.CleaningPipeline": 400,
    "practo_scraper.pipelines.CsvExportPipeline": 500,
    "practo_scraper.pipelines.DatabasePipeline": 600,
}

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Retry configuration
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Logging configuration
LOG_LEVEL = "INFO"

# Custom settings for feeds
FEEDS = {
    "data/doctors_fallback_%(time)s.csv": {
        "format": "csv",
        "encoding": "utf8",
        "store_empty": False,
        "fields": ["name", "speciality", "degree", "year_of_experience", "location", "city", "dp_score", "npv", "consultation_fee", "profile_url", "scraped_at", "google_map_link"],
    },
}

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
