"""
Script to generate Excel workbook with ONDC vs Amazon unit economics analysis
"""

import json
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.utils import get_column_letter


# Default parameters
DEFAULT_PARAMETERS = {
    'Amazon_Commission_pct': 0.18,  # 18%
    'ONDC_Commission_pct': 0.06,    # 6%
    'Payment_Fee_pct': 0.02,        # 2%
    'Packaging_per_unit': 12,       # ₹12
    'Other_Fees_per_unit': 5,       # ₹5
    'CAC_Amazon_per_unit': 90,      # ₹90
    'CAC_ONDC_per_unit': 100,       # ₹100
    'Default_Fixed_Costs_monthly': 50000  # ₹50,000
}


def load_products():
    """Load product data from JSON file"""
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both old format (list) and new format (dict with metadata)
            if isinstance(data, dict) and 'products' in data:
                print(f"Loaded {len(data['products'])} products")
                print(f"Metadata: {data.get('metadata', {}).get('scraped_date', 'N/A')}")
                print(f"Scraped: {data.get('metadata', {}).get('scraped_count', 0)} | Estimated: {data.get('metadata', {}).get('estimated_count', 0)}")
                return data['products']
            elif isinstance(data, list):
                return data
            else:
                print("Warning: Unexpected data format")
                return []
    except FileNotFoundError:
        print("Error: data/products.json not found. Please run scrape_real_data.py first.")
        return None


def create_parameters_sheet(ws, params):
    """Create Parameters sheet"""
    ws.title = "Parameters"
    
    # Headers
    ws['A1'] = "Parameter"
    ws['B1'] = "Value"
    ws['C1'] = "Description"
    
    # Style headers
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    # Parameter rows
    rows = [
        ("Amazon_Commission_pct", params['Amazon_Commission_pct'], "Amazon marketplace commission rate (decimal)"),
        ("ONDC_Commission_pct", params['ONDC_Commission_pct'], "ONDC network commission rate (decimal)"),
        ("Payment_Fee_pct", params['Payment_Fee_pct'], "Payment gateway fee rate (decimal)"),
        ("Packaging_per_unit", params['Packaging_per_unit'], "Packaging cost per unit (INR)"),
        ("Other_Fees_per_unit", params['Other_Fees_per_unit'], "Other fees per unit (INR)"),
        ("CAC_Amazon_per_unit", params['CAC_Amazon_per_unit'], "Customer Acquisition Cost per unit - Amazon (INR)"),
        ("CAC_ONDC_per_unit", params['CAC_ONDC_per_unit'], "Customer Acquisition Cost per unit - ONDC (INR)"),
        ("Default_Fixed_Costs_monthly", params['Default_Fixed_Costs_monthly'], "Monthly fixed costs (INR)")
    ]
    
    for idx, (param, value, desc) in enumerate(rows, start=2):
        ws[f'A{idx}'] = param
        ws[f'B{idx}'] = value
        ws[f'C{idx}'] = desc
        ws[f'B{idx}'].number_format = '#,##0.00' if isinstance(value, float) else '#,##0'
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 50


def create_product_data_sheet(ws, products):
    """Create Product_Data sheet"""
    ws.title = "Product_Data"
    
    # Headers
    headers = ["Product_Name", "Category", "Size", "Selling_Price", "Estimated_Weight_g", 
               "Monthly_Sales_Units", "Cost_of_Goods_est", "Logistics_Cost", "Data_Source"]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    
    # Data rows
    for row_idx, product in enumerate(products, start=2):
        ws.cell(row=row_idx, column=1, value=product['product_name'])
        ws.cell(row=row_idx, column=2, value=product.get('category', 'N/A'))
        ws.cell(row=row_idx, column=3, value=product['size'])
        ws.cell(row=row_idx, column=4, value=product['selling_price'])
        ws.cell(row=row_idx, column=5, value=product['estimated_weight_g'])
        ws.cell(row=row_idx, column=6, value=product['monthly_sales_units'])
        ws.cell(row=row_idx, column=7, value=product['cost_of_goods_est'])
        ws.cell(row=row_idx, column=8, value=product['logistics_cost'])
        ws.cell(row=row_idx, column=9, value=product.get('source', 'N/A'))
    
    # Format numbers
    for row in range(2, len(products) + 2):
        ws[f'D{row}'].number_format = '#,##0'
        ws[f'E{row}'].number_format = '#,##0'
        ws[f'F{row}'].number_format = '#,##0'
        ws[f'G{row}'].number_format = '#,##0.00'
        ws[f'H{row}'].number_format = '#,##0.00'
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 60
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    for col in ['D', 'E', 'F', 'G', 'H', 'I']:
        ws.column_dimensions[col].width = 18


def create_unit_economics_sheet(ws, products, params):
    """Create Unit_Economics sheet with formulas"""
    ws.title = "Unit_Economics"
    
    # Headers
    headers = [
        "Product_Name", "Selling_Price", "Cost_of_Goods", 
        "Amazon_Commission_amt", "ONDC_Commission_amt", 
        "Payment_Gateway_Fee", "Logistics_Cost", "Packaging_Cost", 
        "Other_Fees", "CAC_Amazon", "CAC_ONDC",
        "Total_Cost_Amazon", "Total_Cost_ONDC",
        "Profit_per_unit_Amazon", "Profit_per_unit_ONDC", 
        "Profit_Change_pct", "Monthly_Profit_Amazon", "Monthly_Profit_ONDC"
    ]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    
    # Data and formulas
    for row_idx, product in enumerate(products, start=2):
        # Product name
        ws.cell(row=row_idx, column=1, value=product['product_name'])
        
        # Selling price (from Product_Data)
        ws.cell(row=row_idx, column=2, value=f"=Product_Data!D{row_idx}")
        
        # Cost of Goods (from Product_Data)
        ws.cell(row=row_idx, column=3, value=f"=Product_Data!G{row_idx}")
        
        # Amazon Commission = Selling_Price * Amazon_Comm_pct
        ws.cell(row=row_idx, column=4, value=f"=B{row_idx}*Parameters!B2")
        
        # ONDC Commission = Selling_Price * ONDC_Comm_pct
        ws.cell(row=row_idx, column=5, value=f"=B{row_idx}*Parameters!B3")
        
        # Payment Gateway Fee = Selling_Price * Payment_Fee_pct
        ws.cell(row=row_idx, column=6, value=f"=B{row_idx}*Parameters!B4")
        
        # Logistics Cost (from Product_Data)
        ws.cell(row=row_idx, column=7, value=f"=Product_Data!H{row_idx}")
        
        # Packaging Cost (from Parameters)
        ws.cell(row=row_idx, column=8, value="=Parameters!B5")
        
        # Other Fees (from Parameters)
        ws.cell(row=row_idx, column=9, value="=Parameters!B6")
        
        # CAC Amazon (from Parameters)
        ws.cell(row=row_idx, column=10, value="=Parameters!B7")
        
        # CAC ONDC (from Parameters)
        ws.cell(row=row_idx, column=11, value="=Parameters!B8")
        
        # Total Cost Amazon = COGS + Amazon_Comm + Payment_Fee + Logistics + CAC_Amazon + Packaging + Other_Fees
        ws.cell(row=row_idx, column=12, value=f"=C{row_idx}+D{row_idx}+F{row_idx}+G{row_idx}+H{row_idx}+I{row_idx}+J{row_idx}")
        
        # Total Cost ONDC = COGS + ONDC_Comm + Payment_Fee + Logistics + CAC_ONDC + Packaging + Other_Fees
        ws.cell(row=row_idx, column=13, value=f"=C{row_idx}+E{row_idx}+F{row_idx}+G{row_idx}+H{row_idx}+I{row_idx}+K{row_idx}")
        
        # Profit per unit Amazon = Selling_Price - Total_Cost_Amazon
        ws.cell(row=row_idx, column=14, value=f"=B{row_idx}-L{row_idx}")
        
        # Profit per unit ONDC = Selling_Price - Total_Cost_ONDC
        ws.cell(row=row_idx, column=15, value=f"=B{row_idx}-M{row_idx}")
        
        # Profit Change % = (Profit_ONDC - Profit_Amazon) / ABS(Profit_Amazon) * 100
        ws.cell(row=row_idx, column=16, value=f"=(O{row_idx}-N{row_idx})/ABS(N{row_idx})*100")
        
        # Monthly Profit Amazon = Profit_per_unit_Amazon * Monthly_Sales_Units
        ws.cell(row=row_idx, column=17, value=f"=N{row_idx}*Product_Data!F{row_idx}")
        
        # Monthly Profit ONDC = Profit_per_unit_ONDC * Monthly_Sales_Units
        ws.cell(row=row_idx, column=18, value=f"=O{row_idx}*Product_Data!F{row_idx}")
    
    # Format numbers
    for row in range(2, len(products) + 2):
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R']:
            ws[f'{col}{row}'].number_format = '#,##0.00'
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R']:
        ws.column_dimensions[col].width = 18


def create_scenario_analysis_sheet(ws, products, params):
    """Create Scenario_Analysis sheet"""
    ws.title = "Scenario_Analysis"
    
    # Parameter change inputs (row 1-2)
    ws['A1'] = "Scenario Parameter Changes (%):"
    ws['A1'].font = Font(bold=True, size=12)
    
    scenario_params = [
        ("CAC_Amazon_pct_change", "CAC Amazon % Change"),
        ("CAC_ONDC_pct_change", "CAC ONDC % Change"),
        ("Logistics_pct_change", "Logistics % Change"),
        ("ONDC_Comm_pct_change", "ONDC Commission % Change")
    ]
    
    for idx, (param, label) in enumerate(scenario_params, start=2):
        ws.cell(row=idx, column=1, value=label)
        ws.cell(row=idx, column=2, value=0)  # Default 0% change
        ws.cell(row=idx, column=2).number_format = '0.00%'
    
    # Headers (row 4)
    headers = ["Product_Name", "Base_Profit_ONDC", "Adjusted_CAC_ONDC", 
               "Adjusted_Logistics", "Adjusted_ONDC_Comm", 
               "Adjusted_Total_Cost_ONDC", "Adjusted_Profit_ONDC", "Profit_Change_vs_Base"]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=5, column=col_idx, value=header)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    
    # Formulas for each product
    for row_idx, product in enumerate(products, start=6):
        # Product name
        ws.cell(row=row_idx, column=1, value=product['product_name'])
        
        # Base Profit ONDC (from Unit_Economics)
        ws.cell(row=row_idx, column=2, value=f"=Unit_Economics!O{row_idx}")
        
        # Adjusted CAC ONDC = Base CAC * (1 + CAC_ONDC_pct_change)
        ws.cell(row=row_idx, column=3, value=f"=Parameters!B8*(1+B4)")
        
        # Adjusted Logistics = Base Logistics * (1 + Logistics_pct_change)
        ws.cell(row=row_idx, column=4, value=f"=Unit_Economics!G{row_idx}*(1+B5)")
        
        # Adjusted ONDC Commission = Selling_Price * ONDC_Comm_pct * (1 + ONDC_Comm_pct_change)
        ws.cell(row=row_idx, column=5, value=f"=Unit_Economics!B{row_idx}*Parameters!B3*(1+B6)")
        
        # Adjusted Total Cost ONDC = COGS + Adjusted_ONDC_Comm + Payment_Fee + Adjusted_Logistics + Adjusted_CAC_ONDC + Packaging + Other_Fees
        ws.cell(row=row_idx, column=6, value=f"=Unit_Economics!C{row_idx}+E{row_idx}+Unit_Economics!F{row_idx}+D{row_idx}+C{row_idx}+Parameters!B5+Parameters!B6")
        
        # Adjusted Profit ONDC = Selling_Price - Adjusted_Total_Cost_ONDC
        ws.cell(row=row_idx, column=7, value=f"=Unit_Economics!B{row_idx}-F{row_idx}")
        
        # Profit Change vs Base = (Adjusted_Profit - Base_Profit) / ABS(Base_Profit) * 100
        ws.cell(row=row_idx, column=8, value=f"=(G{row_idx}-B{row_idx})/ABS(B{row_idx})*100")
    
    # Format numbers
    for row in range(6, len(products) + 6):
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws[f'{col}{row}'].number_format = '#,##0.00'
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws.column_dimensions[col].width = 18


def create_break_even_sheet(ws, products, params):
    """Create Break_Even sheet"""
    ws.title = "Break_Even"
    
    # Fixed costs input
    ws['A1'] = "Fixed Costs (Monthly):"
    ws['A1'].font = Font(bold=True)
    ws['B1'] = f"=Parameters!B9"
    ws['B1'].number_format = '#,##0'
    
    # Headers
    headers = ["Product_Name", "Selling_Price", "Total_Variable_Cost_ONDC", 
               "Contribution_per_unit_ONDC", "Break_even_units", "Break_even_revenue"]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    
    # Formulas for each product
    for row_idx, product in enumerate(products, start=4):
        # Product name
        ws.cell(row=row_idx, column=1, value=product['product_name'])
        
        # Selling Price (from Unit_Economics)
        ws.cell(row=row_idx, column=2, value=f"=Unit_Economics!B{row_idx}")
        
        # Total Variable Cost ONDC (from Unit_Economics Total_Cost_ONDC)
        ws.cell(row=row_idx, column=3, value=f"=Unit_Economics!M{row_idx}")
        
        # Contribution per unit ONDC = Selling_Price - Total_Variable_Cost_ONDC
        ws.cell(row=row_idx, column=4, value=f"=B{row_idx}-C{row_idx}")
        
        # Break-even units = Fixed_Costs / Contribution_per_unit (with error handling)
        ws.cell(row=row_idx, column=5, value=f"=IF(D{row_idx}>0, B1/D{row_idx}, 0)")
        
        # Break-even revenue = Break_even_units * Selling_Price
        ws.cell(row=row_idx, column=6, value=f"=E{row_idx}*B{row_idx}")
    
    # Format numbers
    for row in range(4, len(products) + 4):
        for col in ['B', 'C', 'D', 'E', 'F']:
            ws[f'{col}{row}'].number_format = '#,##0.00'
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    for col in ['B', 'C', 'D', 'E', 'F']:
        ws.column_dimensions[col].width = 18


def create_dashboard_sheet(ws, products, params):
    """Create Dashboard sheet with metrics and charts"""
    ws.title = "Dashboard"
    
    # Title
    ws['A1'] = "ONDC vs Amazon Unit Economics Dashboard"
    ws['A1'].font = Font(bold=True, size=16)
    ws.merge_cells('A1:D1')
    
    # Key Metrics Section
    row = 3
    ws.cell(row=row, column=1, value="Key Metrics").font = Font(bold=True, size=12)
    row += 1
    
    # Create helper data for chart with shortened product names (columns D-G, will be hidden)
    # This creates a clean data table for the chart with readable labels
    helper_start_row = row + 15
    ws.cell(row=helper_start_row, column=4, value="Chart Data").font = Font(bold=True, size=10)
    helper_start_row += 1
    
    # Headers
    ws.cell(row=helper_start_row, column=4, value="Product")
    ws.cell(row=helper_start_row, column=5, value="Amazon")
    ws.cell(row=helper_start_row, column=6, value="ONDC")
    helper_start_row += 1
    
    # Fill helper data - top 10 products with smart abbreviations
    top_n = min(10, len(products))
    
    # Create abbreviation map for common product types
    abbrev_map = {
        'Hair Oil': 'Hair Oil',
        'Shampoo': 'Shampoo',
        'Conditioner': 'Cond',
        'Face Wash': 'Face Wash',
        'Face Cream': 'Cream',
        'Face Serum': 'Serum',
        'Face Scrub': 'Scrub',
        'Face Mask': 'Mask',
        'Body Lotion': 'Body Lot',
        'Body Butter': 'Body But',
        'Body Wash': 'Body Wash',
        'Lip Balm': 'Lip Balm',
        'Under Eye': 'Eye Cream',
        'Kajal': 'Kajal',
    }
    
    for idx in range(top_n):
        product = products[idx]
        product_name = product['product_name']
        
        # Create smart abbreviation
        short_name = product_name.replace("Mamaearth ", "").replace("Mamaearth", "").strip()
        
        # Try to find abbreviation from map
        found_abbrev = False
        for key, abbrev in abbrev_map.items():
            if key in short_name:
                # Extract the main ingredient/category
                words = short_name.split()
                main_words = []
                for word in words[:2]:  # First 2 words usually contain key info
                    if word.lower() not in ['for', 'with', 'and', 'the', 'of']:
                        main_words.append(word)
                if main_words:
                    short_name = " ".join(main_words) + " " + abbrev
                else:
                    short_name = abbrev
                found_abbrev = True
                break
        
        # If no abbreviation found, use first 2-3 key words
        if not found_abbrev:
            words = short_name.split()
            key_words = []
            skip_words = ['for', 'with', 'and', 'the', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'daily', 'glow']
            for word in words:
                if word.lower() not in skip_words and len(key_words) < 3:
                    key_words.append(word)
                if len(key_words) >= 3:
                    break
            if key_words:
                short_name = " ".join(key_words)
        
        # Final limit to 18 characters
        if len(short_name) > 18:
            short_name = short_name[:15] + "..."
        
        # Write to helper table
        ws.cell(row=helper_start_row, column=4, value=short_name)
        ws.cell(row=helper_start_row, column=5, value=f"=Unit_Economics!N{idx+2}")
        ws.cell(row=helper_start_row, column=6, value=f"=Unit_Economics!O{idx+2}")
        helper_start_row += 1
    
    # Hide helper columns (they're just for chart data)
    ws.column_dimensions['D'].hidden = True
    ws.column_dimensions['E'].hidden = True
    ws.column_dimensions['F'].hidden = True
    
    metrics = [
        ("Average Profit per Unit (Amazon)", "=AVERAGE(Unit_Economics!N2:N" + str(len(products)+1) + ")"),
        ("Average Profit per Unit (ONDC)", "=AVERAGE(Unit_Economics!O2:O" + str(len(products)+1) + ")"),
        ("Average Profit Increase %", "=AVERAGE(Unit_Economics!P2:P" + str(len(products)+1) + ")"),
        ("Total Monthly Profit (Amazon)", "=SUM(Unit_Economics!Q2:Q" + str(len(products)+1) + ")"),
        ("Total Monthly Profit (ONDC)", "=SUM(Unit_Economics!R2:R" + str(len(products)+1) + ")"),
        ("Total Monthly Profit Increase (INR)", "=E7-E6"),
        ("Best Performing Product (ONDC)", "=INDEX(Unit_Economics!A2:A" + str(len(products)+1) + ",MATCH(MAX(Unit_Economics!O2:O" + str(len(products)+1) + "),Unit_Economics!O2:O" + str(len(products)+1) + ",0))")
    ]
    
    for label, formula in metrics:
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=2, value=formula)
        ws.cell(row=row, column=2).number_format = '#,##0.00'
        row += 1
    
    # Charts Section
    chart_row = row + 2
    ws.cell(row=chart_row, column=1, value="Charts").font = Font(bold=True, size=12)
    
    # Get reference to Unit_Economics sheet for chart data
    unit_economics_sheet = None
    for sheet in ws.parent.worksheets:
        if sheet.title == "Unit_Economics":
            unit_economics_sheet = sheet
            break
    
    if unit_economics_sheet:
        # Bar Chart: Profit per Unit Amazon vs ONDC - Top 10 Products
        chart1 = BarChart()
        chart1.type = "col"
        chart1.style = 10
        chart1.title = "Profit per Unit: Amazon vs ONDC (Top 10 Products)"
        chart1.y_axis.title = "Profit (INR)"
        chart1.x_axis.title = ""
        chart1.legend.position = 'r'  # Right side
        
        # Use helper data with shortened names
        # Helper data starts at row + 17 (after headers)
        chart_data_start = row + 17  # Start of data rows in helper section (after "Chart Data" header and column headers)
        top_n = min(10, len(products))
        chart_data_end = chart_data_start + top_n - 1  # 10 products
        
        # Data from helper columns (E = Amazon column 5, F = ONDC column 6)
        data = Reference(ws, min_col=5, min_row=chart_data_start, max_row=chart_data_end, max_col=6)
        # Categories from helper column D (shortened names, column 4)
        cats = Reference(ws, min_col=4, min_row=chart_data_start, max_row=chart_data_end)
        
        chart1.add_data(data, titles_from_data=True)
        chart1.set_categories(cats)
        
        # Better label formatting - angled labels for readability
        chart1.x_axis.tickLblAngle = -45  # 45 degree angle for readability
        chart1.x_axis.tickLblSkip = 0  # Show all labels
        chart1.x_axis.majorTickMark = "out"  # Show tick marks
        
        # Format Y-axis for better readability
        chart1.y_axis.majorGridlines = None  # Cleaner look
        
        chart1.height = 10
        chart1.width = 22
        ws.add_chart(chart1, "A" + str(chart_row + 2))
        
        # Add a note about product labels
        ws.cell(row=chart_row + 13, column=1, value="Note: Chart shows top 10 products with shortened names for readability. Full product names available in Unit_Economics sheet.")
        ws.cell(row=chart_row + 13, column=1).font = Font(italic=True, size=9)
    else:
        ws.cell(row=chart_row + 2, column=1, value="[Note: Chart will be generated when Unit_Economics sheet data is available]")
    
    # Note: Additional charts can be added here
    # For now, the Excel file will have the bar chart
    # Users can add more charts manually in Excel if needed
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 25


def main():
    print("=" * 60)
    print("ONDC vs Amazon Unit Economics Excel Generator")
    print("=" * 60)
    
    # Load products
    products = load_products()
    if not products:
        return
    
    print(f"\nLoaded {len(products)} products")
    
    # Create workbook
    wb = Workbook()
    
    # Remove default sheet
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])
    
    # Create all sheets
    print("\nCreating sheets...")
    create_parameters_sheet(wb.create_sheet("Parameters"), DEFAULT_PARAMETERS)
    print("  [OK] Parameters sheet created")
    
    create_product_data_sheet(wb.create_sheet("Product_Data"), products)
    print("  [OK] Product_Data sheet created")
    
    create_unit_economics_sheet(wb.create_sheet("Unit_Economics"), products, DEFAULT_PARAMETERS)
    print("  [OK] Unit_Economics sheet created")
    
    create_scenario_analysis_sheet(wb.create_sheet("Scenario_Analysis"), products, DEFAULT_PARAMETERS)
    print("  [OK] Scenario_Analysis sheet created")
    
    create_break_even_sheet(wb.create_sheet("Break_Even"), products, DEFAULT_PARAMETERS)
    print("  [OK] Break_Even sheet created")
    
    create_dashboard_sheet(wb.create_sheet("Dashboard"), products, DEFAULT_PARAMETERS)
    print("  [OK] Dashboard sheet created")
    
    # Save workbook
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Mamaearth_ONDC_UnitEconomics_{timestamp}.xlsx"
    try:
        wb.save(filename)
    except PermissionError:
        # If file is open, try with timestamp
        filename = f"Mamaearth_ONDC_UnitEconomics_NEW.xlsx"
        wb.save(filename)
        print(f"\n[WARNING] Original file may be open. Saved as: {filename}")
    
    print("\n" + "=" * 60)
    print(f"Excel workbook saved: {filename}")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open the Excel file to review the analysis")
    print("2. Adjust parameters in the Parameters sheet if needed")
    print("3. Test scenarios in the Scenario_Analysis sheet")
    print("4. Check the Dashboard for visualizations")


if __name__ == "__main__":
    main()

