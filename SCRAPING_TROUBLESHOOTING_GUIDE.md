# Scraping Installation and Troubleshooting Guide

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
