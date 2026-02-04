# Multi-Site Retail Webscraper

A production-ready webscraper for retrieving product prices and details from major retail websites (Walmart, Target, Best Buy, etc.) across different zipcodes nationwide.

## Features

- **Multi-site support**: Configurable framework for scraping multiple retail sites
- **Location-aware**: Set zipcode to get location-specific prices and availability
- **Full product data**: Extract price, availability, ratings, reviews, shipping info, and specs
- **Anti-bot measures**: Playwright stealth mode, user agent rotation, rate limiting
- **Session persistence**: Save and reuse cookies to avoid repeated location settings
- **Scalable**: Async architecture with configurable rate limiting
- **Configurable**: YAML-based site configs for easy addition of new sites

## Architecture

```
scraper/
├── core/               # Core services
│   ├── base_scraper.py        # Abstract base class
│   ├── browser_driver.py      # Playwright wrapper with stealth
│   ├── rate_limiter.py        # Token bucket rate limiting
│   ├── session_manager.py     # Cookie persistence
│   └── user_agent.py          # User agent rotation
├── scrapers/           # Site-specific implementations
│   └── walmart_scraper.py     # Walmart scraper
├── parsers/            # HTML parsing utilities
│   └── selector_engine.py     # CSS selector engine
├── models/             # Data models
│   └── product.py             # Product dataclass
├── config/             # Configuration files
│   └── sites/
│       └── walmart.yaml       # Walmart selectors & settings
└── utils/              # Utilities
    ├── logger.py              # Structured logging
    └── normalizers.py         # Data normalization
```

## Installation

1. Navigate to the scraper directory:
```bash
cd /home/bean/playgrounds/py/scraper
```

2. Install dependencies (already done if you followed the plan):
```bash
source ../venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Basic Example

Scrape 5 laptops from Walmart in San Francisco (zipcode 94102):

```bash
python main.py --site walmart --zipcode 94102 --query "laptop" --max-results 5
```

### Command-Line Options

```
--site          Site to scrape (walmart, target, bestbuy)
--zipcode       5-digit US zipcode for location
--query         Product search query
--max-results   Maximum number of products to scrape (default: 5)
--output        Output JSON file (default: products.json)
--headful       Run browser in visible mode (for debugging)
```

### Examples

```bash
# Scrape monitors from Walmart in New York
python main.py --site walmart --zipcode 10001 --query "monitor" --max-results 10

# Scrape with visible browser (for debugging)
python main.py --site walmart --zipcode 94102 --query "laptop" --headful

# Save to custom output file
python main.py --site walmart --zipcode 60601 --query "smartphone" --output chicago_phones.json
```

## Configuration

### Adding a New Site

1. Create a YAML config file in `config/sites/{site}.yaml`
2. Define selectors for location setting, product search, and product details
3. Implement a scraper class in `scrapers/{site}_scraper.py` that extends `BaseScraper`
4. Update `main.py` to include the new site

See [config/sites/walmart.yaml](config/sites/walmart.yaml) for a complete example.

### Site Configuration Structure

```yaml
site:
  name: walmart
  base_url: https://www.walmart.com
  requires_js: true

location:
  method: cookie  # How to set location (cookie, url_param, form)
  selectors:
    location_button: ['button[data-automation-id="header-delivery-selector"]']
    zipcode_input: ['input[name="zipcode"]']
    submit_button: ['button[type="submit"]']

product:
  selectors:
    name: ['h1[itemprop="name"]', 'h1.prod-ProductTitle']
    current_price: ['span[itemprop="price"]', '.price-current']
    # ... more selectors

rate_limiting:
  requests_per_minute: 10
  min_delay_seconds: 2
  max_delay_seconds: 5
```

## Output Format

Products are saved as JSON with the following structure:

```json
{
  "name": "Dell XPS 13 Laptop",
  "url": "https://www.walmart.com/ip/...",
  "site": "walmart",
  "zipcode": "94102",
  "scraped_at": "2026-02-04T12:00:00",
  "current_price": 899.99,
  "original_price": 1199.99,
  "discount_percent": 25.0,
  "in_stock": true,
  "rating_avg": 4.5,
  "rating_count": 1234,
  "free_shipping": true,
  "delivery_date": "Wed, Feb 7",
  "brand": "Dell",
  "specs": {
    "Screen Size": "13.3 inches",
    "RAM": "16 GB",
    "Storage": "512 GB SSD"
  }
}
```

## Anti-Bot Measures

The scraper implements several techniques to avoid bot detection:

1. **Playwright Stealth Mode**: Hides automation indicators
2. **User Agent Rotation**: Rotates between realistic user agents
3. **Rate Limiting**: Configurable requests per minute with random delays
4. **Session Persistence**: Reuses cookies to avoid repeated interactions
5. **Human-like Delays**: Random delays between actions (2-5 seconds)

## Rate Limiting

Default rate limits per site:
- **Walmart**: 10 requests/minute
- **Target**: 10 requests/minute
- **Best Buy**: 10 requests/minute

Rate limits can be customized in the site configuration YAML files.

## Session Management

The scraper automatically saves cookies after setting a location. Cached sessions are valid for 24 hours. This means:

1. First run for a zipcode: Sets location via UI, saves cookies
2. Subsequent runs (within 24h): Loads cookies, skips location setting
3. Faster scraping and less load on the site

Clear cached sessions:
```bash
rm -rf .cache/sessions/
```

## Troubleshooting

### Location Setting Fails

- Try running in headful mode (`--headful`) to see what's happening
- Check if Walmart's UI has changed (selectors may need updating)
- Verify the zipcode is valid

### No Products Found

- Check if search query returns results on the actual website
- Verify selectors in the YAML config are still valid
- Run in headful mode to debug

### Rate Limiting Errors (429/503)

- Reduce `requests_per_minute` in site config
- Increase `min_delay_seconds` and `max_delay_seconds`
- Wait a few minutes and try again

## Development

### Project Structure

- `core/`: Core services (browser, rate limiter, session manager)
- `scrapers/`: Site-specific scraper implementations
- `parsers/`: HTML parsing utilities
- `models/`: Data models (Product, ScrapeResult)
- `config/`: YAML configuration files
- `utils/`: Helper utilities (logging, normalization)

### Adding Features

1. **New data fields**: Update `models/product.py` and add selectors to site YAML
2. **New site**: Create YAML config and scraper class extending `BaseScraper`
3. **Storage backends**: Implement new storage classes in `storage/` directory

## Roadmap

- [ ] Add Target scraper
- [ ] Add Best Buy scraper
- [ ] Implement SQLite storage backend
- [ ] Add CSV export
- [ ] Implement cache manager for response caching
- [ ] Add progress tracker for resume capability
- [ ] Support for nationwide crawls (100+ zipcodes)
- [ ] Price history tracking
- [ ] Price alert system

## License

This project is for educational purposes. Always respect websites' Terms of Service and robots.txt files.

## Notes

- This scraper is designed for personal use and research
- Be respectful of rate limits and server load
- Some sites may block scraping - use responsibly
- Product data accuracy depends on site HTML structure remaining consistent
