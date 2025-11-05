"""
ADVANCED WEB SCRAPER - Learning Edition
Sophisticated Amazon/Flipkart Scraper with Anti-Detection Techniques

Based on techniques from successful scrapers like amazoncompareit
This scraper implements:
- Advanced Selenium configuration
- User agent rotation
- Human-like behavior simulation
- Multiple selector strategies
- Robust error handling
- Session management

Author: [Your Name]
Project: ONDC vs Amazon Unit Economics Analysis
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import csv

# User agents pool for rotation (makes us look like different browsers)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Load product list from the main scraper
from scrape_real_data import PRODUCT_SEARCH_TERMS


def get_random_user_agent():
    """Get a random user agent from the pool"""
    return random.choice(USER_AGENTS)


def human_like_delay(min_seconds=1, max_seconds=3):
    """Add random delays to simulate human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def setup_advanced_selenium_driver(headless=False):
    """
    Setup Selenium with advanced anti-detection techniques
    Based on successful Amazon scraping techniques
    """
    chrome_options = Options()
    
    # Basic options
    if headless:
        chrome_options.add_argument('--headless=new')  # New headless mode (less detectable)
    
    # Anti-detection options
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # Make browser look more real
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    
    # Additional preferences
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,  # Disable notifications
        },
        "profile.managed_default_content_settings": {
            "images": 2  # Can disable images for faster loading
        }
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property (anti-detection)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        # Set window size to look more human
        driver.set_window_size(random.randint(1200, 1920), random.randint(800, 1080))
        
        return driver
    except Exception as e:
        print(f"[ERROR] Selenium setup failed: {e}")
        return None


def scroll_page_smoothly(driver, scroll_pause_time=0.5):
    """
    Scroll page smoothly to simulate human behavior
    This helps load dynamic content
    """
    try:
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down gradually
        for i in range(3):
            # Scroll down
            driver.execute_script(f"window.scrollTo(0, {last_height * (i+1) / 3});")
            time.sleep(scroll_pause_time)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(scroll_pause_time)
    except:
        pass


def scrape_amazon_advanced(search_term, driver=None, retry_count=2):
    """
    Advanced Amazon scraping with multiple strategies
    Returns: (price, title, url, rating) or None
    """
    search_query = search_term.replace(" ", "+")
    amazon_url = f"https://www.amazon.in/s?k={search_query}&i=beauty"
    
    # Multiple selector strategies for price
    price_selectors = [
        "span.a-price-whole",  # Most common
        "span.a-price .a-offscreen",  # Alternative
        "span[data-a-color='price'] span",  # Another variant
        ".a-price-whole",  # Class-based
        "#priceblock_dealprice",  # Deal price
        "#priceblock_saleprice",  # Sale price
        "#priceblock_ourprice",  # Regular price
    ]
    
    # Title selectors
    title_selectors = [
        "h2.a-size-mini a span",  # Search results
        "h2.a-size-base-plus a span",  # Alternative
        "h2 span.a-text-normal",  # Another variant
        "#productTitle",  # Product page
        "span.a-size-large.product-title-word-break",  # Product page variant
    ]
    
    for attempt in range(retry_count):
        try:
            if driver:
                # Use Selenium with advanced techniques
                driver.get(amazon_url)
                
                # Human-like delay
                human_like_delay(2, 4)
                
                # Scroll to load content
                scroll_page_smoothly(driver)
                
                # Wait for page to load
                wait = WebDriverWait(driver, 10)
                
                # Try multiple price selectors
                price = None
                for selector in price_selectors:
                    try:
                        price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in price_elements[:3]:  # Check first 3 results
                            try:
                                price_text = elem.text.strip()
                                if price_text:
                                    # Extract number
                                    price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                                    if price_match:
                                        price = int(price_match.group())
                                        if 50 <= price <= 10000:  # Reasonable price range
                                            break
                            except:
                                continue
                        if price:
                            break
                    except:
                        continue
                
                # Try multiple title selectors
                title = None
                for selector in title_selectors:
                    try:
                        title_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in title_elements[:3]:  # Check first 3 results
                            try:
                                title_text = elem.text.strip()
                                if title_text and "mamaearth" in title_text.lower():
                                    title = title_text
                                    break
                            except:
                                continue
                        if title:
                            break
                    except:
                        continue
                
                if price and title:
                    print(f"    [SUCCESS] Amazon: {title[:50]}... - INR {price}")
                    return (price, title, amazon_url)
                
                # If no price found, check for CAPTCHA or blocking
                page_source = driver.page_source.lower()
                if "captcha" in page_source or "robot" in page_source or "blocked" in page_source:
                    print(f"    [WARNING] Possible CAPTCHA/blocking detected")
                    human_like_delay(5, 10)  # Longer delay
                
            else:
                # Fallback: Use requests with better headers
                headers = {
                    'User-Agent': get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                }
                
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(amazon_url, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple price selectors
                    for selector in price_selectors[:3]:  # Try first 3
                        price_elem = soup.select_one(selector)
                        if price_elem:
                            price_text = price_elem.text.strip()
                            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                            if price_match:
                                price = int(price_match.group())
                                if 50 <= price <= 10000:
                                    # Find title
                                    for title_sel in title_selectors[:3]:
                                        title_elem = soup.select_one(title_sel)
                                        if title_elem:
                                            title = title_elem.text.strip()
                                            if title:
                                                print(f"    [SUCCESS] Amazon (requests): {title[:50]}... - INR {price}")
                                                return price, title, amazon_url, None
                                    break
                    
                    # Check for blocking
                    if "captcha" in response.text.lower() or "robot" in response.text.lower():
                        print(f"    [WARNING] Possible blocking detected")
                        human_like_delay(5, 10)
                
        except TimeoutException:
            print(f"    [RETRY {attempt+1}/{retry_count}] Timeout, retrying...")
            human_like_delay(3, 5)
        except Exception as e:
            print(f"    [ERROR] Attempt {attempt+1}: {str(e)[:50]}")
            if attempt < retry_count - 1:
                human_like_delay(3, 5)
    
    return None


def scrape_mamaearth_website(product_name, driver=None):
    """
    Scrape directly from Mamaearth official website
    Returns: (price, title, url) or None
    """
    # Try to construct URL from product name
    # Mamaearth URLs are typically: https://mamaearth.in/product/[product-slug]
    
    # Convert product name to URL-friendly slug
    slug = product_name.lower().replace("mamaearth ", "").replace(" ", "-")
    mamaearth_url = f"https://mamaearth.in/product/{slug}"
    
    # Alternative: Try searching on Mamaearth website
    search_url = f"https://mamaearth.in/search?q={product_name.replace(' ', '+')}"
    
    price_selectors = [
        "span.price",  # Common price selector
        "div[class*='price']",
        "span[class*='selling']",
        ".product-price",
        "#price",
    ]
    
    title_selectors = [
        "h1.product-title",
        "h1[class*='product']",
        "h1",
        ".product-name",
    ]
    
    try:
        if driver:
            # Try direct product URL first
            driver.get(mamaearth_url)
            human_like_delay(2, 4)
            
            # Check if page loaded (not 404)
            if "404" not in driver.title.lower() and "not found" not in driver.page_source.lower():
                # Try to find price
                for selector in price_selectors:
                    try:
                        price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in price_elements:
                            price_text = elem.text.strip()
                            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                            if price_match:
                                price = int(price_match.group())
                                if 50 <= price <= 10000:
                                    # Find title
                                    for title_sel in title_selectors:
                                        try:
                                            title_elem = driver.find_element(By.CSS_SELECTOR, title_sel)
                                            title = title_elem.text.strip()
                                            if title:
                                                print(f"    [SUCCESS] Mamaearth Website: {title[:50]}... - INR {price}")
                                                return price, title, mamaearth_url
                                        except:
                                            continue
                    except:
                        continue
            
            # If direct URL failed, try search
            driver.get(search_url)
            human_like_delay(2, 4)
            scroll_page_smoothly(driver)
            
            # Try to find product in search results
            for selector in price_selectors:
                try:
                    price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in price_elements[:3]:  # Check first 3
                        price_text = elem.text.strip()
                        price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                        if price_match:
                            price = int(price_match.group())
                            if 50 <= price <= 10000:
                                print(f"    [SUCCESS] Mamaearth Website (search): INR {price}")
                                return price, product_name, search_url
                except:
                    continue
                    
        else:
            # Use requests
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            }
            
            response = requests.get(mamaearth_url, headers=headers, timeout=15)
            if response.status_code == 200 and "404" not in response.text.lower():
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for selector in price_selectors:
                    price_elem = soup.select_one(selector)
                    if price_elem:
                        price_text = price_elem.text.strip()
                        price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                        if price_match:
                            price = int(price_match.group())
                            if 50 <= price <= 10000:
                                title_elem = soup.select_one('h1')
                                title = title_elem.text.strip() if title_elem else product_name
                                print(f"    [SUCCESS] Mamaearth Website (requests): {title[:50]}... - INR {price}")
                                return price, title, mamaearth_url
                                
    except Exception as e:
        print(f"    [ERROR] Mamaearth website scrape failed: {str(e)[:50]}")
    
    return None


def scrape_flipkart_advanced(search_term, driver=None):
    """
    Advanced Flipkart scraping
    Returns: (price, title, url) or None
    """
    search_query = search_term.replace(" ", "%20")
    flipkart_url = f"https://www.flipkart.com/search?q={search_query}&otracker=search&otracker1=search&marketplace=FLIPKART"
    
    price_selectors = [
        "div._30jeq3",  # Main price selector
        "div._30jeq3._1_WHN1",  # Alternative
        "div[class*='_30jeq3']",  # Class contains
    ]
    
    title_selectors = [
        "a.s1Q9rs",
        "div._4rR01T",
        "a[class*='s1Q9rs']",
    ]
    
    try:
        if driver:
            driver.get(flipkart_url)
            human_like_delay(2, 4)
            scroll_page_smoothly(driver)
            
            wait = WebDriverWait(driver, 10)
            
            # Try to find price
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                    if price_match:
                        price = int(price_match.group())
                        if 50 <= price <= 10000:
                            # Find title
                            for title_sel in title_selectors:
                                try:
                                    title_elem = driver.find_element(By.CSS_SELECTOR, title_sel)
                                    title = title_elem.text.strip()
                                    if title and "mamaearth" in title.lower():
                                        print(f"    [SUCCESS] Flipkart: {title[:50]}... - INR {price}")
                                        return price, title, flipkart_url
                                except:
                                    continue
                except:
                    continue
        else:
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(flipkart_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                price_elem = soup.select_one('div._30jeq3')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                    if price_match:
                        price = int(price_match.group())
                        
                        title_elem = soup.select_one('a.s1Q9rs, div._4rR01T')
                        if title_elem:
                            title = title_elem.text.strip()
                            print(f"    [SUCCESS] Flipkart (requests): {title[:50]}... - INR {price}")
                            return price, title, flipkart_url
                            
    except Exception as e:
        print(f"    [ERROR] Flipkart scrape failed: {str(e)[:50]}")
    
    return None


def estimate_monthly_sales(price, category):
    """Estimate monthly sales based on price and category"""
    base_sales = {
        "Hair Care": 18000,
        "Face Care": 20000,
        "Body Care": 15000,
        "Baby Care": 12000,
        "Lip Care": 25000,
        "Eye Care": 10000,
    }
    
    category_base = base_sales.get(category, 15000)
    
    if price < 200:
        multiplier = 1.3
    elif price < 300:
        multiplier = 1.1
    elif price < 400:
        multiplier = 1.0
    elif price < 500:
        multiplier = 0.9
    else:
        multiplier = 0.8
    
    return int(category_base * multiplier)


def scrape_all_products_advanced(headless=False, use_selenium=True):
    """
    Main advanced scraping function with learning features
    """
    print("=" * 80)
    print("ADVANCED MAMAEARTH PRODUCT SCRAPER")
    print("Learning Edition - Sophisticated Techniques")
    print("=" * 80)
    print(f"\nScraping {len(PRODUCT_SEARCH_TERMS)} products...")
    print(f"Mode: {'Selenium (Advanced)' if use_selenium else 'Requests (Basic)'}")
    print(f"Headless: {headless}\n")
    
    # Setup driver
    driver = None
    if use_selenium:
        print("[INFO] Setting up advanced Selenium driver...")
        driver = setup_advanced_selenium_driver(headless=headless)
        if not driver:
            print("[WARNING] Selenium setup failed, falling back to requests")
            use_selenium = False
    
    products = []
    scraped_count = 0
    amazon_count = 0
    mamaearth_count = 0
    flipkart_count = 0
    estimated_count = 0
    
    try:
        for idx, product_template in enumerate(PRODUCT_SEARCH_TERMS, 1):
            search_term = product_template['name']
            print(f"\n[{idx}/{len(PRODUCT_SEARCH_TERMS)}] Processing: {search_term}")
            
            price = None
            title = None
            source = None
            url = None
            
            # Try multiple sources in priority order
            # 1. Amazon India (most reliable for marketplace prices)
            result = scrape_amazon_advanced(search_term, driver, retry_count=2)
            if result:
                price, title, url = result
                source = "Amazon India"
                scraped_count += 1
                amazon_count += 1
            else:
                # 2. Mamaearth Official Website (direct from brand)
                result = scrape_mamaearth_website(search_term, driver)
                if result:
                    price, title, url = result
                    source = "Mamaearth Website"
                    scraped_count += 1
                    mamaearth_count += 1
                else:
                    # 3. Flipkart (alternative marketplace)
                    result = scrape_flipkart_advanced(search_term, driver)
                    if result:
                        price, title, url = result
                        source = "Flipkart"
                        scraped_count += 1
                        flipkart_count += 1
            
            # Fallback to estimated prices
            if not price:
                price_ranges = {
                    "Hair Care": (199, 599),
                    "Face Care": (199, 699),
                    "Body Care": (299, 499),
                    "Baby Care": (199, 399),
                    "Lip Care": (99, 199),
                    "Eye Care": (199, 399),
                }
                
                min_price, max_price = price_ranges.get(product_template['category'], (199, 499))
                if product_template['weight_g'] < 50:
                    price = min_price + (max_price - min_price) * 0.3
                elif product_template['weight_g'] < 150:
                    price = min_price + (max_price - min_price) * 0.5
                else:
                    price = min_price + (max_price - min_price) * 0.7
                
                price = int(price)
                title = search_term
                source = "Estimated"
                estimated_count += 1
                print(f"    [ESTIMATED] Price: INR {price} (based on category)")
            
            # Build product data
            product = {
                "product_name": title or search_term,
                "category": product_template['category'],
                "size": product_template['size'],
                "selling_price": price,
                "estimated_weight_g": product_template['weight_g'],
                "monthly_sales_units": estimate_monthly_sales(price, product_template['category']),
                "source": source,
                "url": url or f"https://www.amazon.in/s?k={search_term.replace(' ', '+')}",
                "scraped": source != "Estimated"
            }
            
            # Calculate costs
            product['cost_of_goods_est'] = round(product['selling_price'] * 0.30, 2)
            logistics_per_100g = 2
            weight_factor = product['estimated_weight_g'] / 100
            product['logistics_cost'] = max(15, round(weight_factor * logistics_per_100g, 2))
            
            products.append(product)
            
            # Human-like delay between requests
            if idx < len(PRODUCT_SEARCH_TERMS):
                delay = random.uniform(2, 5) if use_selenium else random.uniform(1, 3)
                print(f"    [WAIT] {delay:.1f}s before next request...")
                time.sleep(delay)
    
    finally:
        # Close driver
        if driver:
            print("\n[INFO] Closing browser...")
            driver.quit()
    
    # Summary
    print("\n" + "=" * 80)
    print("SCRAPING SUMMARY")
    print("=" * 80)
    print(f"Total Products: {len(products)}")
    print(f"Successfully Scraped: {scraped_count} ({scraped_count/len(products)*100:.1f}%)")
    print(f"  - Amazon India: {amazon_count}")
    print(f"  - Mamaearth Website: {mamaearth_count}")
    print(f"  - Flipkart: {flipkart_count}")
    print(f"Estimated Prices: {estimated_count} ({estimated_count/len(products)*100:.1f}%)")
    print("=" * 80)
    
    return products


def save_products_to_json(products, filename='data/products.json'):
    """Save product data to JSON file"""
    import os
    os.makedirs('data', exist_ok=True)
    
    data = {
        "metadata": {
            "scraped_date": datetime.now().isoformat(),
            "total_products": len(products),
            "scraped_count": sum(1 for p in products if p.get('scraped', False)),
            "estimated_count": sum(1 for p in products if not p.get('scraped', False)),
            "project": "ONDC vs Amazon Unit Economics Analysis",
            "brand": "Mamaearth",
            "scraper_version": "Advanced v2.0"
        },
        "products": products
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Product data saved to {filename}")
    
    # Also save as CSV
    csv_filename = filename.replace('.json', '.csv')
    if products:
        fieldnames = products[0].keys()
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        print(f"[OK] Product data also saved to {csv_filename}")


def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("ADVANCED WEB SCRAPER - LEARNING MODE")
    print("=" * 80)
    print("\nThis scraper uses sophisticated techniques:")
    print("  - Advanced Selenium configuration")
    print("  - User agent rotation")
    print("  - Human-like behavior simulation")
    print("  - Multiple selector strategies")
    print("  - Robust error handling")
    print("\nNote: This may take 15-30 minutes for 41 products")
    print("      (due to rate limiting and delays)\n")
    
    # Ask user for preferences
    print("Options:")
    print("1. Run with Selenium (visible browser) - Recommended for learning")
    print("2. Run with Selenium (headless) - Faster but less visible")
    print("3. Run with requests only - Fastest but may be blocked")
    
    choice = input("\nEnter choice (1/2/3, default=1): ").strip() or "1"
    
    if choice == "1":
        use_selenium = True
        headless = False
        print("\n[INFO] Running with visible browser (Selenium)")
    elif choice == "2":
        use_selenium = True
        headless = True
        print("\n[INFO] Running with headless browser (Selenium)")
    else:
        use_selenium = False
        headless = False
        print("\n[INFO] Running with requests only")
    
    products = scrape_all_products_advanced(headless=headless, use_selenium=use_selenium)
    
    if products:
        save_products_to_json(products)
        
        print("\n" + "=" * 80)
        print("DATA COLLECTION COMPLETE")
        print("=" * 80)
        print("\nSample Products:")
        print("-" * 80)
        for i, product in enumerate(products[:5], 1):
            scraped_mark = "[SCRAPED]" if product.get('scraped') else "[ESTIMATED]"
            print(f"{i}. {scraped_mark} {product['product_name'][:50]}...")
            print(f"   Price: INR {product['selling_price']} | Source: {product['source']}")
        
        print(f"\n... and {len(products)-5} more products")
        print("\nNext step: Run 'python generate_excel.py' to create the analysis workbook")
        print("=" * 80)
    else:
        print("\n[ERROR] No products were collected.")


if __name__ == "__main__":
    main()

