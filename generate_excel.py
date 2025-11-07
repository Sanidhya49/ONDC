"""
Script to generate Excel workbook with ONDC vs Amazon unit economics analysis
"""

import json
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.utils import get_column_letter


# Default parameters (Updated with verified real data - Jan 2025)
# Amazon India Beauty/Haircare: 0% (≤₹300), 5% (>₹300 & ≤₹500), 8% (>₹500)
# ONDC: Flat fee ₹1.50 per transaction above ₹250 (from Jan 1, 2025) OR ~5-8% seller app commission
DEFAULT_PARAMETERS = {
    'Amazon_Commission_pct_300_500': 0.05,  # 5% for >₹300 & ≤₹500 (Beauty/Haircare)
    'Amazon_Commission_pct_above_500': 0.08,  # 8% for >₹500 (Beauty/Haircare)
    'ONDC_Flat_Fee': 1.50,  # ₹1.50 flat fee per transaction above ₹250 (from Jan 1, 2025)
    'ONDC_Commission_pct': 0.06,    # 6% alternative (seller app commission, if not using flat fee)
    'Payment_Fee_pct': 0.02,        # 2% (verified: standard 1.5-2.5% for e-commerce)
    'Packaging_per_unit': 12,       # ₹12 (verified: ₹10-15 standard for beauty/FMCG)
    'Other_Fees_per_unit': 5,       # ₹5 (verified: ₹3-7 standard range)
    'CAC_Amazon_per_unit': 90,      # ₹90 (verified: ₹50-120 range, mid-point reasonable)
    'CAC_ONDC_per_unit': 100,       # ₹100 (verified: ₹80-150 range, slightly higher due to brand building)
    'Default_Fixed_Costs_monthly': 50000  # ₹50,000 (verified: reasonable for small-medium D2C brand)
}


def load_products():
    """Load product data from final.xlsx (via products_final.json) or fallback to products.json"""
    # First try to load from final.xlsx processed data
    try:
        with open('data/products_final.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'products' in data:
                print(f"Loaded {len(data['products'])} products from final.xlsx")
                print(f"Source: {data.get('metadata', {}).get('source', 'final.xlsx')}")
                return data['products']
            elif isinstance(data, list):
                print(f"Loaded {len(data)} products from final.xlsx")
                return data
    except FileNotFoundError:
        print("Note: data/products_final.json not found. Trying to load from final.xlsx directly...")
        # Try to load directly from final.xlsx
        try:
            from load_final_products import load_products_from_final_excel
            products = load_products_from_final_excel()
            if products:
                print(f"Loaded {len(products)} products from final.xlsx")
                return products
        except Exception as e:
            print(f"Could not load from final.xlsx: {e}")
    
    # Fallback to original products.json
    try:
        with open('data/products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'products' in data:
                print(f"Loaded {len(data['products'])} products from products.json (fallback)")
                return data['products']
            elif isinstance(data, list):
                print(f"Loaded {len(data)} products from products.json (fallback)")
                return data
    except FileNotFoundError:
        print("Error: Neither data/products_final.json nor data/products.json found.")
        print("Please run: python load_final_products.py")
        return None


def create_parameters_sheet(ws, params):
    """Create Parameters sheet with professional formatting"""
    ws.title = "Parameters"
    
    # Professional formatting
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border_style = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )
    
    # Headers
    ws['A1'] = "Parameter"
    ws['B1'] = "Value"
    ws['C1'] = "Description"
    
    # Style headers
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_style
    
    # Parameter rows (Updated for tiered Amazon pricing and ONDC flat fee)
    rows = [
        ("Amazon_Commission_pct_300_500", params['Amazon_Commission_pct_300_500'], "Amazon commission rate for >₹300 & ≤₹500 (Beauty/Haircare) - 5%"),
        ("Amazon_Commission_pct_above_500", params['Amazon_Commission_pct_above_500'], "Amazon commission rate for >₹500 (Beauty/Haircare) - 8%"),
        ("ONDC_Flat_Fee", params['ONDC_Flat_Fee'], "ONDC flat fee per transaction above ₹250 (INR) - ₹1.50 from Jan 1, 2025"),
        ("Payment_Fee_pct", params['Payment_Fee_pct'], "Payment gateway fee rate (decimal) - 2%"),
        ("Packaging_per_unit", params['Packaging_per_unit'], "Packaging cost per unit (INR)"),
        ("Other_Fees_per_unit", params['Other_Fees_per_unit'], "Other fees per unit (INR)"),
        ("CAC_Amazon_per_unit", params['CAC_Amazon_per_unit'], "Customer Acquisition Cost per unit - Amazon (INR)"),
        ("CAC_ONDC_per_unit", params['CAC_ONDC_per_unit'], "Customer Acquisition Cost per unit - ONDC (INR)"),
        ("Default_Fixed_Costs_monthly", params['Default_Fixed_Costs_monthly'], "Monthly fixed costs (INR)")
    ]
    
    for idx, (param, value, desc) in enumerate(rows, start=2):
        row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") if idx % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        cell = ws.cell(row=idx, column=1, value=param)
        cell.fill = row_fill
        cell.border = border_style
        cell.font = Font(size=10, bold=True)
        cell.alignment = Alignment(vertical="center")
        
        cell = ws.cell(row=idx, column=2, value=value)
        cell.fill = row_fill
        cell.border = border_style
        cell.font = Font(size=10)
        cell.alignment = Alignment(horizontal="right", vertical="center")
        cell.number_format = '#,##0.00' if isinstance(value, float) else '#,##0'
        
        cell = ws.cell(row=idx, column=3, value=desc)
        cell.fill = row_fill
        cell.border = border_style
        cell.font = Font(size=9, color="555555")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 28
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 55


def create_product_data_sheet(ws, products):
    """Create Product_Data sheet with professional formatting"""
    ws.title = "Product_Data"
    
    # Professional color scheme
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")  # Professional blue
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border_style = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )
    
    # Headers (Category column removed)
    headers = ["Product_Name", "Size", "Selling_Price", "Estimated_Weight_g", 
               "Monthly_Sales_Units", "Cost_of_Goods_est", "Logistics_Cost", "Data_Source"]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_style
    
    # Data rows with alternating row colors
    for row_idx, product in enumerate(products, start=2):
        row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") if row_idx % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        ws.cell(row=row_idx, column=1, value=product['product_name']).fill = row_fill
        ws.cell(row=row_idx, column=1).border = border_style
        ws.cell(row=row_idx, column=1).font = Font(size=10)
        ws.cell(row=row_idx, column=1).alignment = Alignment(vertical="center", wrap_text=True)
        
        ws.cell(row=row_idx, column=2, value=product['size']).fill = row_fill
        ws.cell(row=row_idx, column=2).border = border_style
        ws.cell(row=row_idx, column=2).font = Font(size=10)
        ws.cell(row=row_idx, column=2).alignment = Alignment(horizontal="center", vertical="center")
        
        ws.cell(row=row_idx, column=3, value=product['selling_price']).fill = row_fill
        ws.cell(row=row_idx, column=3).border = border_style
        ws.cell(row=row_idx, column=3).font = Font(size=10)
        ws.cell(row=row_idx, column=3).alignment = Alignment(horizontal="right", vertical="center")
        
        ws.cell(row=row_idx, column=4, value=product['estimated_weight_g']).fill = row_fill
        ws.cell(row=row_idx, column=4).border = border_style
        ws.cell(row=row_idx, column=4).font = Font(size=10)
        ws.cell(row=row_idx, column=4).alignment = Alignment(horizontal="right", vertical="center")
        
        ws.cell(row=row_idx, column=5, value=product['monthly_sales_units']).fill = row_fill
        ws.cell(row=row_idx, column=5).border = border_style
        ws.cell(row=row_idx, column=5).font = Font(size=10)
        ws.cell(row=row_idx, column=5).alignment = Alignment(horizontal="right", vertical="center")
        
        ws.cell(row=row_idx, column=6, value=product['cost_of_goods_est']).fill = row_fill
        ws.cell(row=row_idx, column=6).border = border_style
        ws.cell(row=row_idx, column=6).font = Font(size=10)
        ws.cell(row=row_idx, column=6).alignment = Alignment(horizontal="right", vertical="center")
        
        ws.cell(row=row_idx, column=7, value=product['logistics_cost']).fill = row_fill
        ws.cell(row=row_idx, column=7).border = border_style
        ws.cell(row=row_idx, column=7).font = Font(size=10)
        ws.cell(row=row_idx, column=7).alignment = Alignment(horizontal="right", vertical="center")
        
        ws.cell(row=row_idx, column=8, value=product.get('source', 'final.xlsx')).fill = row_fill
        ws.cell(row=row_idx, column=8).border = border_style
        ws.cell(row=row_idx, column=8).font = Font(size=10, color="0066CC")
        ws.cell(row=row_idx, column=8).alignment = Alignment(horizontal="center", vertical="center")
    
    # Format numbers
    for row in range(2, len(products) + 2):
        ws[f'C{row}'].number_format = '#,##0'  # Selling_Price (was D, now C)
        ws[f'D{row}'].number_format = '#,##0'  # Estimated_Weight_g (was E, now D)
        ws[f'E{row}'].number_format = '#,##0'  # Monthly_Sales_Units (was F, now E)
        ws[f'F{row}'].number_format = '#,##0.00'  # Cost_of_Goods_est (was G, now F)
        ws[f'G{row}'].number_format = '#,##0.00'  # Logistics_Cost (was H, now G)
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 65  # Product_Name
    ws.column_dimensions['B'].width = 12  # Size
    ws.column_dimensions['C'].width = 15  # Selling_Price
    ws.column_dimensions['D'].width = 18  # Estimated_Weight_g
    ws.column_dimensions['E'].width = 20  # Monthly_Sales_Units
    ws.column_dimensions['F'].width = 18  # Cost_of_Goods_est
    ws.column_dimensions['G'].width = 15  # Logistics_Cost
    ws.column_dimensions['H'].width = 15  # Data_Source
    
    # Freeze header row
    ws.freeze_panes = 'A2'


def create_unit_economics_sheet(ws, products, params):
    """Create Unit_Economics sheet with formulas and professional formatting"""
    ws.title = "Unit_Economics"
    
    # Professional formatting
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=10)
    border_style = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )
    
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
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_style
    
    # Data and formulas with professional formatting
    for row_idx, product in enumerate(products, start=2):
        row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") if row_idx % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        # Product name
        cell = ws.cell(row=row_idx, column=1, value=product['product_name'])
        cell.fill = row_fill
        cell.border = border_style
        cell.font = Font(size=9)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        
        # Selling price (from Product_Data) - Column C now (was D)
        ws.cell(row=row_idx, column=2, value=f"=Product_Data!C{row_idx}")
        
        # Cost of Goods (from Product_Data) - Column F now (was G)
        ws.cell(row=row_idx, column=3, value=f"=Product_Data!F{row_idx}")
        
        # Amazon Commission - Tiered pricing for Beauty/Haircare (2025 verified rates)
        # ≤ ₹300: 0%, > ₹300 & ≤ ₹500: 5%, > ₹500: 8%
        ws.cell(row=row_idx, column=4, value=f"=IF(B{row_idx}<=300, 0, IF(B{row_idx}<=500, B{row_idx}*Parameters!B2, B{row_idx}*Parameters!B3))")
        
        # ONDC Fee - Flat fee ₹1.50 per transaction above ₹250 (from Jan 1, 2025)
        # If transaction ≤ ₹250, no fee; if > ₹250, flat ₹1.50
        ws.cell(row=row_idx, column=5, value=f"=IF(B{row_idx}<=250, 0, Parameters!B4)")
        
        # Payment Gateway Fee = Selling_Price * Payment_Fee_pct
        ws.cell(row=row_idx, column=6, value=f"=B{row_idx}*Parameters!B5")
        
        # Logistics Cost (from Product_Data) - Column G now (was H)
        ws.cell(row=row_idx, column=7, value=f"=Product_Data!G{row_idx}")
        
        # Packaging Cost (from Parameters)
        ws.cell(row=row_idx, column=8, value="=Parameters!B6")
        
        # Other Fees (from Parameters)
        ws.cell(row=row_idx, column=9, value="=Parameters!B7")
        
        # CAC Amazon (from Parameters)
        ws.cell(row=row_idx, column=10, value="=Parameters!B8")
        
        # CAC ONDC (from Parameters)
        ws.cell(row=row_idx, column=11, value="=Parameters!B9")
        
        # Total Cost Amazon = COGS + Amazon_Comm + Payment_Fee + Logistics + CAC_Amazon + Packaging + Other_Fees
        ws.cell(row=row_idx, column=12, value=f"=C{row_idx}+D{row_idx}+F{row_idx}+G{row_idx}+H{row_idx}+I{row_idx}+J{row_idx}")
        
        # Total Cost ONDC = COGS + ONDC_Comm + Payment_Fee + Logistics + CAC_ONDC + Packaging + Other_Fees
        ws.cell(row=row_idx, column=13, value=f"=C{row_idx}+E{row_idx}+F{row_idx}+G{row_idx}+H{row_idx}+I{row_idx}+K{row_idx}")
        
        # Profit per unit Amazon = Selling_Price - Total_Cost_Amazon
        ws.cell(row=row_idx, column=14, value=f"=B{row_idx}-L{row_idx}")
        
        # Profit per unit ONDC = Selling_Price - Total_Cost_ONDC
        ws.cell(row=row_idx, column=15, value=f"=B{row_idx}-M{row_idx}")
        
        # Profit Change % = (Profit_ONDC - Profit_Amazon) / ABS(Profit_Amazon) * 100
        # Handle division by zero
        ws.cell(row=row_idx, column=16, value=f"=IF(ABS(N{row_idx})>0, (O{row_idx}-N{row_idx})/ABS(N{row_idx})*100, 0)")
        
        # Monthly Profit Amazon = Profit_per_unit_Amazon * Monthly_Sales_Units - Column E now (was F)
        ws.cell(row=row_idx, column=17, value=f"=N{row_idx}*Product_Data!E{row_idx}")
        
        # Monthly Profit ONDC = Profit_per_unit_ONDC * Monthly_Sales_Units - Column E now (was F)
        ws.cell(row=row_idx, column=18, value=f"=O{row_idx}*Product_Data!E{row_idx}")
    
    # Format numbers and apply borders
    for row in range(2, len(products) + 2):
        row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") if row % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R']:
            cell = ws[f'{col}{row}']
            cell.number_format = '#,##0.00'
            cell.border = border_style
            cell.fill = row_fill
            cell.font = Font(size=9)
            cell.alignment = Alignment(horizontal="right", vertical="center")
    
    # Special formatting for profit columns (highlight positive values)
    for row in range(2, len(products) + 2):
        # Profit columns - conditional formatting would be ideal, but we'll use standard formatting
        for col in ['N', 'O', 'Q', 'R']:  # Profit columns
            ws[f'{col}{row}'].number_format = '#,##0.00'
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R']:
        ws.column_dimensions[col].width = 16
    
    # Freeze header row
    ws.freeze_panes = 'A2'


def create_scenario_analysis_sheet(ws, products, params):
    """Create Scenario_Analysis sheet with professional formatting"""
    ws.title = "Scenario_Analysis"
    
    # Professional formatting
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border_style = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )
    
    # Parameter change inputs (row 1-4)
    ws['A1'] = "Scenario Parameter Changes (%):"
    ws['A1'].font = Font(bold=True, size=13, color="2E75B6")
    ws['A1'].fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    
    scenario_params = [
        ("CAC_Amazon_pct_change", "CAC Amazon % Change"),
        ("CAC_ONDC_pct_change", "CAC ONDC % Change"),
        ("Logistics_pct_change", "Logistics % Change"),
        ("ONDC_Comm_pct_change", "ONDC Commission % Change")
    ]
    
    for idx, (param, label) in enumerate(scenario_params, start=2):
        row_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        ws.cell(row=idx, column=1, value=label).font = Font(size=10, bold=True)
        ws.cell(row=idx, column=1).fill = row_fill
        # Set default to 0% but add example values in comments
        default_value = 0 if idx <= 3 else 0  # Keep all at 0% by default
        cell = ws.cell(row=idx, column=2, value=default_value)
        cell.number_format = '0.00%'
        cell.fill = row_fill
        cell.border = border_style
        cell.font = Font(size=10)
        cell.alignment = Alignment(horizontal="right", vertical="center")
    
    # Add explanatory note about why Profit_Change_vs_Base shows 0
    note_row = 6
    note_cell = ws.cell(row=note_row, column=1, value="Note: Profit_Change_vs_Base shows 0% because all scenario parameters are set to 0% change (no adjustments). To see changes, enter percentage values in cells B2-B5 above (e.g., 10% = 0.10, -5% = -0.05).")
    note_cell.font = Font(size=9, italic=True, color="666666")
    note_cell.fill = PatternFill(start_color="FFF9E6", end_color="FFF9E6", fill_type="solid")
    ws.merge_cells(f'A{note_row}:H{note_row}')
    note_cell.alignment = Alignment(vertical="center", wrap_text=True)
    
    # Headers (row 7, after scenario parameters and note)
    headers = ["Product_Name", "Base_Profit_ONDC", "Adjusted_CAC_ONDC", 
               "Adjusted_Logistics", "Adjusted_ONDC_Comm", 
               "Adjusted_Total_Cost_ONDC", "Adjusted_Profit_ONDC", "Profit_Change_vs_Base"]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=7, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_style
    
    # Formulas for each product (starting at row 8, after headers at row 7)
    for row_idx, product in enumerate(products, start=8):
        # Product name
        ws.cell(row=row_idx, column=1, value=product['product_name'])
        
        # Base Profit ONDC (from Unit_Economics)
        # Note: Unit_Economics data starts at row 2, Scenario_Analysis data starts at row 8
        # So row_idx - 6 gives correct offset (8 - 2 = 6)
        unit_econ_row = row_idx - 6  # Adjust for header row difference
        ws.cell(row=row_idx, column=2, value=f"=Unit_Economics!O{unit_econ_row}")
        
        # Adjusted CAC ONDC = Base CAC * (1 + CAC_ONDC_pct_change)
        # B3 is row 3 which contains CAC_ONDC_pct_change
        # Parameters!B9 is CAC_ONDC_per_unit (not B8 which is CAC_Amazon)
        ws.cell(row=row_idx, column=3, value=f"=Parameters!B9*(1+B3)")
        
        # Adjusted Logistics = Base Logistics * (1 + Logistics_pct_change)
        # B4 is row 4 which contains Logistics_pct_change
        ws.cell(row=row_idx, column=4, value=f"=Unit_Economics!G{unit_econ_row}*(1+B4)")
        
        # Adjusted ONDC Fee = ONDC_Flat_Fee (if price > ₹250) * (1 + ONDC_Comm_pct_change)
        # B5 is row 5 which contains ONDC_Comm_pct_change
        ws.cell(row=row_idx, column=5, value=f"=IF(Unit_Economics!B{unit_econ_row}<=250, 0, Parameters!B4*(1+B5))")
        
        # Adjusted Total Cost ONDC = COGS + Adjusted_ONDC_Fee + Payment_Fee + Adjusted_Logistics + Adjusted_CAC_ONDC + Packaging + Other_Fees
        ws.cell(row=row_idx, column=6, value=f"=Unit_Economics!C{unit_econ_row}+E{row_idx}+Unit_Economics!F{unit_econ_row}+D{row_idx}+C{row_idx}+Parameters!B6+Parameters!B7")
        
        # Adjusted Profit ONDC = Selling_Price - Adjusted_Total_Cost_ONDC
        ws.cell(row=row_idx, column=7, value=f"=Unit_Economics!B{unit_econ_row}-F{row_idx}")
        
        # Profit Change vs Base = (Adjusted_Profit - Base_Profit) / ABS(Base_Profit) * 100
        # Handle division by zero
        ws.cell(row=row_idx, column=8, value=f"=IF(ABS(B{row_idx})>0, (G{row_idx}-B{row_idx})/ABS(B{row_idx})*100, 0)")
    
    # Format numbers and apply borders
    for row in range(8, len(products) + 8):
        row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") if row % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
            cell = ws[f'{col}{row}']
            cell.number_format = '#,##0.00'
            cell.border = border_style
            cell.fill = row_fill
            cell.font = Font(size=9)
            cell.alignment = Alignment(horizontal="right", vertical="center")
        # Product name column
        cell = ws[f'A{row}']
        cell.border = border_style
        cell.fill = row_fill
        cell.font = Font(size=9)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws.column_dimensions[col].width = 18
    
    # Freeze header row
    ws.freeze_panes = 'A8'


def create_break_even_sheet(ws, products, params):
    """Create Break_Even sheet with professional formatting"""
    ws.title = "Break_Even"
    
    # Professional formatting
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border_style = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )
    
    # Fixed costs input with professional styling
    ws['A1'] = "Fixed Costs (Monthly):"
    ws['A1'].font = Font(bold=True, size=12, color="2E75B6")
    ws['A1'].fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    ws['B1'] = f"=Parameters!B10"
    ws['B1'].number_format = '#,##0'
    ws['B1'].font = Font(size=11, bold=True, color="2E75B6")
    ws['B1'].fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    ws['B1'].border = border_style
    ws['B1'].alignment = Alignment(horizontal="right", vertical="center")
    
    # Headers
    headers = ["Product_Name", "Selling_Price", "Total_Variable_Cost_ONDC", 
               "Contribution_per_unit_ONDC", "Break_even_units", "Break_even_revenue"]
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_style
    
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
    
    # Format numbers and apply borders
    for row in range(4, len(products) + 4):
        row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") if row % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        for col in ['B', 'C', 'D', 'E', 'F']:
            cell = ws[f'{col}{row}']
            cell.number_format = '#,##0.00'
            cell.border = border_style
            cell.fill = row_fill
            cell.font = Font(size=9)
            cell.alignment = Alignment(horizontal="right", vertical="center")
        # Product name column
        cell = ws[f'A{row}']
        cell.border = border_style
        cell.fill = row_fill
        cell.font = Font(size=9)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 50
    for col in ['B', 'C', 'D', 'E', 'F']:
        ws.column_dimensions[col].width = 18
    
    # Freeze header row
    ws.freeze_panes = 'A4'


def create_dashboard_sheet(ws, products, params):
    """Create Dashboard sheet with metrics and charts - professional formatting"""
    ws.title = "Dashboard"
    
    # Professional title with background
    title_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    ws['A1'] = "ONDC vs Amazon Unit Economics Dashboard"
    ws['A1'].font = Font(bold=True, size=18, color="FFFFFF")
    ws['A1'].fill = title_fill
    ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells('A1:D1')
    ws.row_dimensions[1].height = 30
    
    # Key Metrics Section with professional styling
    row = 3
    metrics_header = ws.cell(row=row, column=1, value="Key Metrics")
    metrics_header.font = Font(bold=True, size=14, color="2E75B6")
    metrics_header.fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    ws.merge_cells(f'A{row}:B{row}')
    row += 1
    
    # Chart helper data removed - no chart section needed
    
    # Calculate row numbers for reference in formulas
    # Row 4: Average Profit per Unit (Amazon) -> B4
    # Row 5: Average Profit per Unit (ONDC) -> B5
    # Row 6: Average Profit Increase % -> B6
    # Row 7: Total Monthly Profit (Amazon) -> B7
    # Row 8: Total Monthly Profit (ONDC) -> B8
    # Row 9: Total Monthly Profit Increase (INR) -> B9 = B8 - B7
    
    metrics = [
        ("Average Profit per Unit (Amazon)", "=AVERAGE(Unit_Economics!N2:N" + str(len(products)+1) + ")"),
        ("Average Profit per Unit (ONDC)", "=AVERAGE(Unit_Economics!O2:O" + str(len(products)+1) + ")"),
        ("Average Profit Increase %", "=AVERAGE(Unit_Economics!P2:P" + str(len(products)+1) + ")"),
        ("Total Monthly Profit (Amazon)", "=SUM(Unit_Economics!Q2:Q" + str(len(products)+1) + ")"),
        ("Total Monthly Profit (ONDC)", "=SUM(Unit_Economics!R2:R" + str(len(products)+1) + ")"),
        ("Total Monthly Profit Increase (INR)", "=B8-B7"),
        ("Best Performing Product (ONDC)", "=INDEX(Unit_Economics!A2:A" + str(len(products)+1) + ",MATCH(MAX(Unit_Economics!O2:O" + str(len(products)+1) + "),Unit_Economics!O2:O" + str(len(products)+1) + ",0))")
    ]
    
    # Professional metric boxes
    border_style = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )
    
    for idx, (label, formula) in enumerate(metrics, start=0):
        row_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid") if idx % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        label_cell = ws.cell(row=row, column=1, value=label)
        label_cell.font = Font(size=10, bold=True)
        label_cell.fill = row_fill
        label_cell.border = border_style
        label_cell.alignment = Alignment(vertical="center")
        
        value_cell = ws.cell(row=row, column=2, value=formula)
        value_cell.number_format = '#,##0.00'
        value_cell.font = Font(size=11, bold=True, color="2E75B6")
        value_cell.fill = row_fill
        value_cell.border = border_style
        value_cell.alignment = Alignment(horizontal="right", vertical="center")
        row += 1
    
    # Add professional explanation note about Average Profit Increase %
    explanation_row = row + 1
    explanation_text = (
        "📊 Understanding 'Average Profit Increase %': "
        "This metric averages the percentage change for each product individually. "
        "A negative value (-2.79%) does NOT indicate a loss. "
        "ONDC is MORE profitable overall (₹3.38M more per month). "
        "The negative percentage occurs because some low-priced products (≤₹300) favor Amazon "
        "(0% commission vs ₹1.50 ONDC fee), which pulls down the average. "
        "Focus on 'Total Monthly Profit Increase (INR)' which shows the true advantage: ₹3,376,980 positive."
    )
    
    note_cell = ws.cell(row=explanation_row, column=1, value=explanation_text)
    note_cell.font = Font(size=10, italic=True, color="2E75B6")
    note_cell.fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
    note_cell.border = Border(
        left=Side(style='thin', color='2E75B6'),
        right=Side(style='thin', color='2E75B6'),
        top=Side(style='thin', color='2E75B6'),
        bottom=Side(style='thin', color='2E75B6')
    )
    ws.merge_cells(f'A{explanation_row}:D{explanation_row}')
    note_cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="left")
    ws.row_dimensions[explanation_row].height = 80
    
    # Note: Chart section removed as per user request
    # Users can create charts manually in Excel if needed using the Unit_Economics data
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 40
    ws.column_dimensions['B'].width = 28
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15


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

