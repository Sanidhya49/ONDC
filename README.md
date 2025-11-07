# ONDC vs Amazon Unit Economics Analysis

A comprehensive unit economics comparison tool for D2C brands evaluating profitability between Amazon India and ONDC (Open Network for Digital Commerce) platforms.

## Overview

This project analyzes the financial impact of selling products through Amazon India vs ONDC, using real-world commission rates and fee structures verified as of January 2025. The analysis includes unit economics, scenario modeling, and break-even calculations.

## Study & Survey Information

### Amazon India Commission Structure (2025)

Based on verified data for **Beauty, Haircare, Bath & Shower** category:

- **Products ≤ ₹300**: 0% commission (zero referral fees for select categories)
- **Products > ₹300 and ≤ ₹500**: 5% commission
- **Products > ₹500**: 8% commission

*Source: Amazon Seller Central fee structure for Health, Beauty, Personal Care & Personal Care Appliances category*

### ONDC Fee Structure (2025)

- **Transaction ≤ ₹250**: No fee
- **Transaction > ₹250**: Flat fee of ₹1.50 per transaction (exclusive of taxes)

*Source: ONDC announcement effective January 1, 2025*

**Note**: Some seller apps on ONDC may charge additional commissions (typically 5-8%), but the base ONDC network fee is the flat ₹1.50 structure.

## Cost Parameters Used

The following parameters are used in the unit economics calculations:

### Platform Fees

| Parameter | Value | Description |
|-----------|-------|-------------|
| `Amazon_Commission_pct_300_500` | 5% | Commission for products >₹300 & ≤₹500 |
| `Amazon_Commission_pct_above_500` | 8% | Commission for products >₹500 |
| `ONDC_Flat_Fee` | ₹1.50 | Flat fee per transaction >₹250 |

### Standard Costs

| Parameter | Value | Description |
|-----------|-------|-------------|
| `Payment_Fee_pct` | 2% | Payment gateway fee (standard 1.5-2.5% for e-commerce) |
| `Packaging_per_unit` | ₹12 | Packaging cost per unit (standard ₹10-15 for beauty/FMCG) |
| `Other_Fees_per_unit` | ₹5 | Other fees per unit (standard ₹3-7 range) |

### Customer Acquisition Costs (CAC)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `CAC_Amazon_per_unit` | ₹90 | Customer acquisition cost for Amazon (range: ₹50-120) |
| `CAC_ONDC_per_unit` | ₹100 | Customer acquisition cost for ONDC (range: ₹80-150, slightly higher due to brand building) |

### Fixed Costs

| Parameter | Value | Description |
|-----------|-------|-------------|
| `Default_Fixed_Costs_monthly` | ₹50,000 | Monthly fixed costs (reasonable for small-medium D2C brand) |

## Project Structure

```
ONDC/
├── generate_excel.py          # Main script to generate Excel workbook
├── streamlit_app.py           # Interactive Streamlit dashboard
├── load_final_products.py     # Helper script to load product data
├── final.xlsx                # Source product data
├── requirements.txt           # Python dependencies
├── setup_env.ps1             # Windows setup script
├── setup_env.sh              # Linux/Mac setup script
├── data/                     # Product data directory
│   ├── products.json
│   └── products_final.json
└── venv/                     # Virtual environment (created during setup)
```

## Setup Instructions

### Windows (PowerShell)
```powershell
.\setup_env.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x setup_env.sh
./setup_env.sh
```

### Manual Setup
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

### 1. Generate Excel Workbook

```bash
python generate_excel.py
```

This generates a timestamped Excel file: `Mamaearth_ONDC_UnitEconomics_YYYYMMDD_HHMMSS.xlsx`

**Excel Workbook Contents:**
- **Parameters**: All cost parameters and assumptions
- **Product_Data**: Product information (name, price, COGS, sales volume)
- **Unit_Economics**: Detailed profit calculations for Amazon vs ONDC
- **Scenario_Analysis**: Interactive scenario modeling with adjustable parameters
- **Break_Even**: Break-even analysis for each product
- **Dashboard**: Key metrics and summary dashboard

### 2. Run Interactive Dashboard

```bash
streamlit run streamlit_app.py
```

The Streamlit app provides:
- Interactive visualization of profit comparisons
- Live scenario analysis with adjustable sliders
- Break-even analysis charts
- Real-time parameter adjustments

## Key Metrics Explained

### Average Profit per Unit
- **Amazon**: Average profit per unit sold on Amazon
- **ONDC**: Average profit per unit sold on ONDC

### Average Profit Increase %
- Averages the percentage change for each product individually
- **Note**: A negative value does NOT indicate a loss
- Some low-priced products (≤₹300) favor Amazon (0% commission vs ₹1.50 ONDC fee), which can pull down the average percentage
- **Focus on "Total Monthly Profit Increase (INR)"** for the true financial advantage

### Total Monthly Profit Increase (INR)
- The absolute difference in total monthly profit between ONDC and Amazon
- This is the key metric showing overall profitability advantage

## Methodology

1. **Product Data**: Loaded from `final.xlsx` containing product names, prices, COGS, and estimated monthly sales
2. **Cost Calculation**: 
   - Amazon: Tiered commission based on price + standard costs
   - ONDC: Flat fee for transactions >₹250 + standard costs
3. **Profit Calculation**: Selling Price - Total Costs (COGS + Commissions + Fees + Logistics + CAC + Packaging + Other)
4. **Monthly Profit**: Profit per unit × Monthly sales volume

## Dependencies

- `openpyxl` - Excel file generation and manipulation
- `pandas` - Data processing
- `streamlit` - Interactive dashboard
- `plotly` - Data visualization

See `requirements.txt` for complete list.

## Notes

- All commission rates and fees are based on verified data as of January 2025
- Parameters can be adjusted in the Excel "Parameters" sheet or via the Streamlit app
- The analysis assumes consistent pricing across platforms (standard D2C practice)
- Logistics costs are product-specific based on weight and shipping requirements
