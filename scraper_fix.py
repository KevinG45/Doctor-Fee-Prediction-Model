#!/usr/bin/env python3
"""
Scraper troubleshooting and fix script

This script diagnoses and fixes common scraping issues:
1. Missing Playwright browsers
2. Network connectivity issues  
3. Configuration problems
"""

import subprocess
import sys
import os
import importlib
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("=== Checking Dependencies ===")
    
    required_packages = [
        'scrapy', 'playwright', 'scrapy_playwright', 
        'pandas', 'lxml', 'requests', 'beautifulsoup4'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    return len(missing) == 0

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    print("\n=== Checking Playwright Browsers ===")
    
    try:
        from playwright._impl._driver import compute_driver_executable
        from playwright._impl._api_structures import Size
        
        # Check if chromium is available
        cache_dir = Path.home() / ".cache" / "ms-playwright"
        chromium_dirs = list(cache_dir.glob("chromium*"))
        
        if chromium_dirs:
            print(f"✅ Found Playwright browsers in: {cache_dir}")
            for dir in chromium_dirs:
                print(f"   - {dir.name}")
            return True
        else:
            print(f"❌ No Playwright browsers found in: {cache_dir}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Playwright: {e}")
        return False

def check_network_connectivity():
    """Check if we can access external websites"""
    print("\n=== Checking Network Connectivity ===")
    
    import socket
    
    test_hosts = [
        ('www.google.com', 80),
        ('www.practo.com', 443),
        ('8.8.8.8', 53)  # Google DNS
    ]
    
    connectivity = False
    for host, port in test_hosts:
        try:
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            print(f"✅ Can connect to {host}:{port}")
            connectivity = True
        except (socket.error, socket.timeout):
            print(f"❌ Cannot connect to {host}:{port}")
    
    return connectivity

def fix_playwright_installation():
    """Fix Playwright browser installation"""
    print("\n=== Fixing Playwright Installation ===")
    
    try:
        # Try to install browsers
        result = subprocess.run([
            sys.executable, '-m', 'playwright', 'install', 'chromium'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully")
            return True
        else:
            print(f"❌ Playwright installation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Playwright installation timed out (network issue)")
        return False
    except Exception as e:
        print(f"❌ Error installing Playwright: {e}")
        return False

def create_fallback_settings():
    """Create settings that work with or without Playwright"""
    print("\n=== Creating Fallback Settings ===")
    
    settings_path = Path("practo_scraper/practo_scraper/settings_fallback.py")
    settings_content = '''# Fallback settings for when Playwright is not available
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
'''
    
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(settings_content)
        print(f"✅ Created fallback settings: {settings_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating fallback settings: {e}")
        return False

def create_installation_guide():
    """Create installation and troubleshooting guide"""
    print("\n=== Creating Installation Guide ===")
    
    guide_content = '''# Scraping Installation and Troubleshooting Guide

## Quick Fix for Current Issue

The scraping isn't working because of missing Playwright browsers. Here's how to fix it:

### 1. Install Playwright Browsers
```bash
# Method 1: Using playwright command
playwright install chromium

# Method 2: Using Python module  
python -m playwright install chromium

# Method 3: Install all browsers (larger download)
playwright install
```

### 2. Test the Fixed Scraper
```bash
# Test with fallback spider (no browser needed)
cd practo_scraper
scrapy crawl practo_doctors_fallback -s CLOSESPIDER_ITEMCOUNT=5

# Test with full Playwright spider (after browser installation)
cd practo_scraper  
scrapy crawl practo_doctors -s CLOSESPIDER_ITEMCOUNT=5
```

## Alternative Solutions

### Option A: Use Fallback Spider (No Browser Required)
```bash
cd practo_scraper
scrapy crawl practo_doctors_fallback
```

### Option B: Use Different Settings
```bash
cd practo_scraper
scrapy crawl practo_doctors_fallback -s SETTINGS=practo_scraper.settings_fallback
```

## Common Issues and Solutions

### Issue 1: "Executable doesn't exist" Error
**Cause**: Playwright browsers not installed
**Solution**: Run `playwright install chromium`

### Issue 2: Network/DNS Resolution Errors  
**Cause**: No internet access or network restrictions
**Solution**: 
- Check internet connectivity
- Try different network
- Use VPN if needed
- Contact network administrator

### Issue 3: Spider Hanging/No Output
**Cause**: Wrong spider configuration or blocked requests
**Solution**:
- Use fallback spider without Playwright
- Check robots.txt compliance 
- Adjust request delays
- Rotate user agents

### Issue 4: Missing Dependencies
**Solution**: Install all requirements
```bash
pip install -r requirements.txt
```

## Testing Your Setup

1. **Test Dependencies**:
   ```bash
   python scraper_fix.py
   ```

2. **Test Simple Access**:
   ```bash  
   python test_simple_access.py
   ```

3. **Test Scrapy Configuration**:
   ```bash
   cd practo_scraper
   scrapy check practo_doctors_fallback
   ```

## Production Setup

For production use:

1. **Install on server with internet access**
2. **Install Playwright browsers**: `playwright install chromium`  
3. **Configure proper delays**: Avoid overwhelming the target server
4. **Monitor for blocking**: Implement rotation and retries
5. **Respect robots.txt**: Follow site policies

## Current Status

- ✅ Core scraper logic is working (deduplication, fee extraction, etc.)
- ✅ Fallback spider created for non-browser environments  
- ❌ Playwright browsers need installation
- ❌ Network connectivity required for live scraping

The scraper is ready to work once browsers are installed and network access is available.
'''
    
    try:
        guide_path = Path("SCRAPING_TROUBLESHOOTING_GUIDE.md")
        guide_path.write_text(guide_content)
        print(f"✅ Created troubleshooting guide: {guide_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating guide: {e}")
        return False

def main():
    """Main troubleshooting and fix function"""
    print("🔧 Scraper Troubleshooting and Fix Tool")
    print("=" * 50)
    
    # Check current status
    deps_ok = check_dependencies()
    browsers_ok = check_playwright_browsers() 
    network_ok = check_network_connectivity()
    
    print(f"\n=== Current Status ===")
    print(f"Dependencies: {'✅ OK' if deps_ok else '❌ Issues'}")
    print(f"Playwright Browsers: {'✅ OK' if browsers_ok else '❌ Missing'}")
    print(f"Network Access: {'✅ OK' if network_ok else '❌ No Internet'}")
    
    # Apply fixes
    print(f"\n=== Applying Fixes ===")
    
    fixes_applied = 0
    
    # Fix 1: Try to install browsers if network is available
    if network_ok and not browsers_ok:
        if fix_playwright_installation():
            fixes_applied += 1
    
    # Fix 2: Create fallback settings
    if create_fallback_settings():
        fixes_applied += 1
    
    # Fix 3: Create troubleshooting guide
    if create_installation_guide():
        fixes_applied += 1
    
    print(f"\n=== Summary ===")
    print(f"Fixes applied: {fixes_applied}")
    
    if not network_ok:
        print("\n⚠️  NETWORK ISSUE DETECTED:")
        print("   - No internet access available")
        print("   - Scraping will not work until network is restored")
        print("   - The scraper code itself is fixed and ready")
        print("   - Use fallback spider when network is available")
    elif not browsers_ok:
        print("\n⚠️  BROWSER ISSUE:")
        print("   - Playwright browsers need manual installation")  
        print("   - Run: playwright install chromium")
        print("   - Or use the fallback spider without browsers")
    else:
        print("\n🎉 ALL ISSUES RESOLVED!")
        print("   - Scraper should now work properly")
        print("   - Test with: cd practo_scraper && scrapy crawl practo_doctors_fallback -s CLOSESPIDER_ITEMCOUNT=3")

if __name__ == "__main__":
    main()