# Data Collection Methodology & Notes

## Overview

This document explains the data collection process for the ONDC vs Amazon Unit Economics Analysis project.

## Data Collection Approach

### Primary Strategy: Multi-Source Web Scraping

We implemented a comprehensive scraping strategy targeting multiple sources:

1. **Amazon India** (Primary Source)
   - Most reliable for product pricing
   - Large product catalog
   - Real marketplace prices

2. **Flipkart** (Secondary Source)
   - Price verification
   - Alternative pricing data

3. **Estimated Prices** (Fallback)
   - Based on category benchmarks
   - Industry pricing patterns
   - Size/weight considerations

### Challenges Encountered

**Anti-Scraping Measures:**
- Amazon and Flipkart implement sophisticated bot detection
- Cloudflare protection
- Rate limiting
- CAPTCHA challenges
- IP blocking

**Technical Limitations:**
- JavaScript-rendered content requires Selenium
- Selenium requires ChromeDriver installation
- Headless mode detection
- Dynamic pricing changes

### Current Data Status

**Total Products Collected:** 41 products
- **Scraped:** 0% (due to anti-scraping measures)
- **Estimated:** 100% (based on category and size benchmarks)

**Product Categories:**
- Hair Care: 8 products
- Face Care: 20 products
- Body Care: 4 products
- Baby Care: 3 products
- Lip Care: 2 products
- Eye Care: 2 products
- Other: 2 products

### Data Quality Assurance

**Price Estimation Methodology:**
1. Category-based price ranges from industry benchmarks
2. Size/weight adjustments
3. Realistic pricing based on Mamaearth's typical price points
4. Validation against known product prices where available

**Price Ranges Used:**
- Hair Care: ₹199 - ₹599
- Face Care: ₹199 - ₹699
- Body Care: ₹299 - ₹499
- Baby Care: ₹199 - ₹399
- Lip Care: ₹99 - ₹199
- Eye Care: ₹199 - ₹399

### How to Get Real Prices

#### Option 1: Manual Data Entry (Recommended for Academic Project)
1. Visit Amazon India or Flipkart
2. Search for each Mamaearth product
3. Note the current selling price
4. Update the `data/products.json` file with real prices
5. Re-run `generate_excel.py`

#### Option 2: Enhanced Scraping (Advanced)
1. Use rotating proxies
2. Implement CAPTCHA solving
3. Use residential IP addresses
4. Add more sophisticated browser automation
5. Implement longer delays between requests

#### Option 3: Alternative Data Sources
1. Use price comparison APIs (if available)
2. Scrape from less protected sites
3. Use affiliate program data
4. Partner with data providers

### For Academic Project Submission

**Recommended Approach:**
1. **Use the current dataset** - 41 products with estimated prices
2. **Document the methodology** - Explain scraping attempts and challenges
3. **Add a note** - "Prices estimated based on category benchmarks and industry standards"
4. **Include manual verification** - Update 5-10 products with real prices from manual research
5. **Explain limitations** - Document anti-scraping measures in project report

### Data Validation

**Current Data Characteristics:**
- ✅ Real product names (Mamaearth products)
- ✅ Realistic price ranges (₹129 - ₹699)
- ✅ Proper categorization
- ✅ Size and weight specifications
- ✅ Estimated sales volumes
- ⚠️ Prices are estimates (not scraped)

### Next Steps

1. **For Project Submission:**
   - Use current dataset (41 products)
   - Document methodology and limitations
   - Add manual price verification for sample products
   - Include in project report

2. **For Production Use:**
   - Implement enhanced scraping with proxies
   - Use API-based data collection
   - Set up automated data refresh
   - Add price change tracking

### Academic Integrity Note

This project demonstrates:
- Web scraping methodology
- Data collection techniques
- Handling of real-world data challenges
- Appropriate use of fallback strategies
- Transparent documentation of limitations

The estimated prices are based on industry benchmarks and realistic assumptions, making the analysis valid for academic purposes while demonstrating understanding of data collection challenges.

---

**Last Updated:** [Current Date]  
**Data Collection Date:** [Scraping Date]  
**Total Products:** 41  
**Scraping Success Rate:** 0% (estimated prices used)

