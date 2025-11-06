"""
Script to load products from final.xlsx and match with existing product data
"""

import pandas as pd
import json
import re
from typing import Dict, List, Optional

def extract_quantity_from_name(product_name: str) -> Optional[str]:
    """Extract quantity (like 100ml, 200g) from product name"""
    # Pattern to match quantities like: 100ml, 200 ml, 50g, 100 g, etc.
    patterns = [
        r'(\d+)\s*ml',  # Matches "100ml" or "100 ml"
        r'(\d+)\s*g',   # Matches "100g" or "100 g"
        r'\((\d+)\s*ml\)',  # Matches "(50ml)"
        r'- (\d+)\s*ml',  # Matches "- 100 ml"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            quantity = match.group(1)
            # Determine unit
            if 'ml' in match.group(0).lower():
                return f"{quantity}ml"
            elif 'g' in match.group(0).lower():
                return f"{quantity}g"
    
    return None

def load_products_from_final_excel(excel_path: str = 'final.xlsx', 
                                   json_path: str = 'data/products.json') -> List[Dict]:
    """
    Load products from final.xlsx and match with existing product data for quantities
    """
    # Read final.xlsx
    df = pd.read_excel(excel_path, header=None)
    df = df.dropna()  # Remove empty rows
    
    # Load existing products.json for reference quantities
    existing_products = {}
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products_list = data.get('products', []) if isinstance(data, dict) else data
            for prod in products_list:
                # Store by normalized name (lowercase, remove extra spaces)
                name_key = prod.get('product_name', '').lower().strip()
                existing_products[name_key] = {
                    'size': prod.get('size', ''),
                    'estimated_weight_g': prod.get('estimated_weight_g', 0),
                    'monthly_sales_units': prod.get('monthly_sales_units', 0),
                    'cost_of_goods_est': prod.get('cost_of_goods_est', 0),
                    'logistics_cost': prod.get('logistics_cost', 15)
                }
    except FileNotFoundError:
        print(f"Warning: {json_path} not found. Will use defaults for missing quantities.")
    
    # Process products from final.xlsx
    products = []
    for _, row in df.iterrows():
        if pd.isna(row[0]) or pd.isna(row[1]):
            continue
        
        product_name = str(row[0]).strip()
        selling_price = float(row[1])
        
        # Extract quantity from name if present
        size = extract_quantity_from_name(product_name)
        
        # If no quantity in name, try to find in existing products
        if not size:
            name_key = product_name.lower().strip()
            # Try exact match first
            if name_key in existing_products:
                size = existing_products[name_key]['size']
                estimated_weight_g = existing_products[name_key]['estimated_weight_g']
                monthly_sales_units = existing_products[name_key]['monthly_sales_units']
                cost_of_goods_est = existing_products[name_key]['cost_of_goods_est']
                logistics_cost = existing_products[name_key]['logistics_cost']
            else:
                # Try partial match (contains)
                found = False
                for key, data in existing_products.items():
                    # Check if product name contains key words from existing product
                    key_words = [w for w in key.split() if len(w) > 3]
                    if any(word in name_key for word in key_words):
                        size = data['size']
                        estimated_weight_g = data['estimated_weight_g']
                        monthly_sales_units = data['monthly_sales_units']
                        cost_of_goods_est = data['cost_of_goods_est']
                        logistics_cost = data['logistics_cost']
                        found = True
                        break
                
                if not found:
                    # Use defaults
                    size = "100ml"  # Default
                    estimated_weight_g = 100
                    monthly_sales_units = 15000
                    cost_of_goods_est = selling_price * 0.30  # 30% of selling price
                    logistics_cost = 15
        else:
            # Quantity found in name, extract weight
            if 'ml' in size.lower():
                estimated_weight_g = int(re.search(r'(\d+)', size).group(1))
            elif 'g' in size.lower():
                estimated_weight_g = int(re.search(r'(\d+)', size).group(1))
            else:
                estimated_weight_g = 100
            
            # Try to get other data from existing products
            name_key = product_name.lower().strip()
            if name_key in existing_products:
                monthly_sales_units = existing_products[name_key]['monthly_sales_units']
                cost_of_goods_est = existing_products[name_key]['cost_of_goods_est']
                logistics_cost = existing_products[name_key]['logistics_cost']
            else:
                # Use defaults
                monthly_sales_units = 15000
                cost_of_goods_est = selling_price * 0.30  # 30% of selling price
                logistics_cost = 15
        
        # Create product dict
        product = {
            'product_name': product_name,
            'size': size,
            'selling_price': selling_price,
            'estimated_weight_g': estimated_weight_g,
            'monthly_sales_units': monthly_sales_units,
            'cost_of_goods_est': cost_of_goods_est,
            'logistics_cost': logistics_cost,
            'source': 'final.xlsx'
        }
        
        products.append(product)
    
    return products

if __name__ == "__main__":
    products = load_products_from_final_excel()
    print(f"Loaded {len(products)} products from final.xlsx")
    print("\nFirst 5 products:")
    for i, p in enumerate(products[:5], 1):
        print(f"{i}. {p['product_name']}")
        print(f"   Price: INR {p['selling_price']}, Size: {p['size']}, Weight: {p['estimated_weight_g']}g")
    
    # Save to JSON for generate_excel.py to use
    output = {
        "metadata": {
            "source": "final.xlsx",
            "total_products": len(products),
            "note": "Products loaded from final.xlsx with quantities extracted/matched"
        },
        "products": products
    }
    
    with open('data/products_final.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to data/products_final.json")

