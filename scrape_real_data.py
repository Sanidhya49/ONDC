"""
Advanced Web Scraper for Mamaearth Product Data
For Final Year BMS Project: ONDC vs Amazon Unit Economics Analysis

This script scrapes real product data from:
1. Amazon India (primary source - more reliable)
2. Flipkart (secondary source)
3. Mamaearth official website (fallback)

Author: [Your Name]
Project: Simulating the Impact of ONDC on D2C Brand's Unit Economics
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
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import csv

# Extended product list - 40+ Mamaearth products with their Amazon/Flipkart search terms
PRODUCT_SEARCH_TERMS = [
    # Hair Care Products
    {"name": "Mamaearth Onion Hair Oil", "category": "Hair Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Onion Shampoo", "category": "Hair Care", "size": "250ml", "weight_g": 250},
    {"name": "Mamaearth Onion Conditioner", "category": "Hair Care", "size": "250ml", "weight_g": 250},
    {"name": "Mamaearth Rosemary Hair Oil", "category": "Hair Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Rosemary Shampoo", "category": "Hair Care", "size": "250ml", "weight_g": 250},
    {"name": "Mamaearth Argan Hair Mask", "category": "Hair Care", "size": "200g", "weight_g": 200},
    {"name": "Mamaearth Hair Serum", "category": "Hair Care", "size": "150ml", "weight_g": 150},
    {"name": "Mamaearth Onion Hair Growth Serum", "category": "Hair Care", "size": "150ml", "weight_g": 150},
    
    # Face Wash Products
    {"name": "Mamaearth Vitamin C Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Ubtan Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Tea Tree Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Aloe Vera Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Rice Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Charcoal Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    {"name": "Mamaearth Bye Bye Blemishes Face Wash", "category": "Face Care", "size": "100ml", "weight_g": 100},
    
    # Face Creams & Moisturizers
    {"name": "Mamaearth Vitamin C Face Cream", "category": "Face Care", "size": "50g", "weight_g": 50},
    {"name": "Mamaearth Ubtan Face Cream", "category": "Face Care", "size": "50g", "weight_g": 50},
    {"name": "Mamaearth Vitamin C Night Cream", "category": "Face Care", "size": "50g", "weight_g": 50},
    {"name": "Mamaearth Aqua Glow Face Cream", "category": "Face Care", "size": "50g", "weight_g": 50},
    {"name": "Mamaearth Honey Oats Face Cream", "category": "Face Care", "size": "50g", "weight_g": 50},
    {"name": "Mamaearth Bye Bye Blemishes Face Cream", "category": "Face Care", "size": "50g", "weight_g": 50},
    
    # Serums
    {"name": "Mamaearth Vitamin C Face Serum", "category": "Face Care", "size": "30ml", "weight_g": 30},
    {"name": "Mamaearth Retinol Face Serum", "category": "Face Care", "size": "30ml", "weight_g": 30},
    {"name": "Mamaearth Niacinamide Face Serum", "category": "Face Care", "size": "30ml", "weight_g": 30},
    {"name": "Mamaearth Hyaluronic Acid Serum", "category": "Face Care", "size": "30ml", "weight_g": 30},
    {"name": "Mamaearth AHA BHA Face Serum", "category": "Face Care", "size": "30ml", "weight_g": 30},
    
    # Face Scrubs & Masks
    {"name": "Mamaearth Rice Face Scrub", "category": "Face Care", "size": "100g", "weight_g": 100},
    {"name": "Mamaearth Ubtan Face Scrub", "category": "Face Care", "size": "100g", "weight_g": 100},
    {"name": "Mamaearth Charcoal Face Mask", "category": "Face Care", "size": "100g", "weight_g": 100},
    {"name": "Mamaearth Vitamin C Face Mask", "category": "Face Care", "size": "100g", "weight_g": 100},
    
    # Body Care
    {"name": "Mamaearth Vitamin C Body Lotion", "category": "Body Care", "size": "400ml", "weight_g": 400},
    {"name": "Mamaearth Ubtan Body Lotion", "category": "Body Care", "size": "400ml", "weight_g": 400},
    {"name": "Mamaearth Cocoa Body Butter", "category": "Body Care", "size": "200g", "weight_g": 200},
    {"name": "Mamaearth Tea Tree Body Wash", "category": "Body Care", "size": "400ml", "weight_g": 400},
    
    # Baby Care
    {"name": "Mamaearth Baby Shampoo", "category": "Baby Care", "size": "200ml", "weight_g": 200},
    {"name": "Mamaearth Baby Lotion", "category": "Baby Care", "size": "200ml", "weight_g": 200},
    {"name": "Mamaearth Baby Soap", "category": "Baby Care", "size": "75g", "weight_g": 75},
    
    # Lip Care
    {"name": "Mamaearth Lip Balm", "category": "Lip Care", "size": "4g", "weight_g": 4},
    {"name": "Mamaearth Tinted Lip Balm", "category": "Lip Care", "size": "4g", "weight_g": 4},
    
    # Eye Care
    {"name": "Mamaearth Under Eye Cream", "category": "Eye Care", "size": "20g", "weight_g": 20},
    {"name": "Mamaearth Kajal", "category": "Eye Care", "size": "0.35g", "weight_g": 1},
]


def setup_selenium_driver():
    """Setup Selenium Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"[WARNING] Selenium setup failed: {e}")
        print("[INFO] Will use requests-based scraping instead")
        return None


def scrape_amazon_product(search_term, driver=None):
    """
    Scrape product price from Amazon India
    Returns: (price, title, url) or None if failed
    """
    try:
        # Amazon India search URL
        search_query = search_term.replace(" ", "+")
        amazon_url = f"https://www.amazon.in/s?k={search_query}&i=beauty&ref=sr_pg_1"
        
        if driver:
            # Use Selenium for dynamic content
            driver.get(amazon_url)
            time.sleep(2)
            
            # Try to find price
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                price_text = price_element.text.strip()
                price = int(re.sub(r'[^\d]', '', price_text))
                
                title_element = driver.find_element(By.CSS_SELECTOR, "h2.a-size-mini a span")
                title = title_element.text.strip()
                
                return price, title, amazon_url
            except:
                pass
        else:
            # Use requests + BeautifulSoup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(amazon_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find price
                price_elem = soup.select_one('span.a-price-whole')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price = int(re.sub(r'[^\d]', '', price_text))
                    
                    # Find title
                    title_elem = soup.select_one('h2.a-size-mini span')
                    title = title_elem.text.strip() if title_elem else search_term
                    
                    return price, title, amazon_url
                    
    except Exception as e:
        print(f"    [ERROR] Amazon scrape failed for '{search_term}': {e}")
    
    return None


def scrape_flipkart_product(search_term, driver=None):
    """
    Scrape product price from Flipkart
    Returns: (price, title, url) or None if failed
    """
    try:
        search_query = search_term.replace(" ", "%20")
        flipkart_url = f"https://www.flipkart.com/search?q={search_query}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(flipkart_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find price
            price_elem = soup.select_one('div._30jeq3')
            if price_elem:
                price_text = price_elem.text.strip()
                price = int(re.sub(r'[^\d]', '', price_text))
                
                # Find title
                title_elem = soup.select_one('a.s1Q9rs, div._4rR01T')
                title = title_elem.text.strip() if title_elem else search_term
                
                return price, title, flipkart_url
                
    except Exception as e:
        print(f"    [ERROR] Flipkart scrape failed for '{search_term}': {e}")
    
    return None


def estimate_monthly_sales(price, category):
    """
    Estimate monthly sales based on price and category
    Higher volume for lower price items and popular categories
    """
    base_sales = {
        "Hair Care": 18000,
        "Face Care": 20000,
        "Body Care": 15000,
        "Baby Care": 12000,
        "Lip Care": 25000,
        "Eye Care": 10000,
    }
    
    category_base = base_sales.get(category, 15000)
    
    # Price adjustment: lower price = higher volume
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


def scrape_all_products():
    """
    Main function to scrape all products from multiple sources
    """
    print("=" * 80)
    print("MAMAEARTH PRODUCT DATA SCRAPER")
    print("Final Year BMS Project: ONDC vs Amazon Unit Economics Analysis")
    print("=" * 80)
    print(f"\nScraping {len(PRODUCT_SEARCH_TERMS)} products...")
    print("Source Priority: Amazon India > Flipkart > Estimated Prices\n")
    
    # Setup Selenium (optional)
    driver = setup_selenium_driver()
    use_selenium = driver is not None
    
    products = []
    scraped_count = 0
    estimated_count = 0
    
    for idx, product_template in enumerate(PRODUCT_SEARCH_TERMS, 1):
        search_term = product_template['name']
        print(f"[{idx}/{len(PRODUCT_SEARCH_TERMS)}] Processing: {search_term}")
        
        price = None
        title = None
        source = None
        url = None
        
        # Try Amazon first
        result = scrape_amazon_product(search_term, driver)
        if result:
            price, title, url = result
            source = "Amazon India"
            scraped_count += 1
            print(f"    [OK] Found on Amazon: INR {price}")
        else:
            # Try Flipkart
            result = scrape_flipkart_product(search_term)
            if result:
                price, title, url = result
                source = "Flipkart"
                scraped_count += 1
                print(f"    [OK] Found on Flipkart: INR {price}")
            else:
                # Use estimated price based on category and typical Mamaearth pricing
                price_ranges = {
                    "Hair Care": (199, 599),
                    "Face Care": (199, 699),
                    "Body Care": (299, 499),
                    "Baby Care": (199, 399),
                    "Lip Care": (99, 199),
                    "Eye Care": (199, 399),
                }
                
                min_price, max_price = price_ranges.get(product_template['category'], (199, 499))
                # Estimate based on size/weight
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
                print(f"    [ESTIMATED] Price: INR {price} (based on category and size)")
        
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
        
        # Calculate COGS and Logistics
        product['cost_of_goods_est'] = round(product['selling_price'] * 0.30, 2)
        logistics_per_100g = 2
        weight_factor = product['estimated_weight_g'] / 100
        product['logistics_cost'] = max(15, round(weight_factor * logistics_per_100g, 2))
        
        products.append(product)
        
        # Be respectful - add delay
        time.sleep(random.uniform(1, 3))
    
    # Close driver if used
    if driver:
        driver.quit()
    
    # Summary
    print("\n" + "=" * 80)
    print("SCRAPING SUMMARY")
    print("=" * 80)
    print(f"Total Products: {len(products)}")
    print(f"Successfully Scraped: {scraped_count} ({scraped_count/len(products)*100:.1f}%)")
    print(f"Estimated Prices: {estimated_count} ({estimated_count/len(products)*100:.1f}%)")
    print(f"Sources: Amazon India, Flipkart, Estimated")
    print("=" * 80)
    
    return products


def save_products_to_json(products, filename='data/products.json'):
    """Save product data to JSON file"""
    import os
    os.makedirs('data', exist_ok=True)
    
    # Add metadata
    data = {
        "metadata": {
            "scraped_date": datetime.now().isoformat(),
            "total_products": len(products),
            "scraped_count": sum(1 for p in products if p.get('scraped', False)),
            "estimated_count": sum(1 for p in products if not p.get('scraped', False)),
            "project": "ONDC vs Amazon Unit Economics Analysis",
            "brand": "Mamaearth"
        },
        "products": products
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Product data saved to {filename}")
    
    # Also save as CSV for easy viewing
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
    print("\nStarting data collection process...")
    print("This may take 10-15 minutes due to rate limiting and delays.\n")
    
    products = scrape_all_products()
    
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
            print(f"   Price: INR {product['selling_price']} | Source: {product['source']} | Category: {product['category']}")
        
        print(f"\n... and {len(products)-5} more products")
        print("\nNext step: Run 'python generate_excel.py' to create the analysis workbook")
        print("=" * 80)
    else:
        print("\n[ERROR] No products were collected. Please check your internet connection and try again.")


if __name__ == "__main__":
    main()

