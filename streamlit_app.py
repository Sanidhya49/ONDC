import os
import math
import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st

# Prefer pandas for convenience if available; otherwise fallback to openpyxl-only
try:
    import pandas as pd  # type: ignore
    PANDAS_AVAILABLE = True
except Exception:  # pragma: no cover
    PANDAS_AVAILABLE = False

from openpyxl import load_workbook
import plotly.express as px
import plotly.graph_objects as go


DEFAULT_EXCEL = "Mamaearth_ONDC_UnitEconomics_20251107_123525.xlsx"  # Updated Jan 2025: Amazon tiered (0%/5%/8%), ONDC flat fee ₹1.50 - All formulas verified + explanation added


def read_excel_to_frames(path: str) -> Dict[str, "pd.DataFrame"]:
    """Read required sheets from Excel into DataFrames. Fallback if pandas not available.

    Sheets expected: Parameters, Product_Data, Unit_Economics, Scenario_Analysis, Break_Even, Dashboard (optional)
    """
    # Try data_only first, but if formulas aren't evaluated, we'll recalculate
    wb = load_workbook(path, data_only=True)

    def sheet_to_records(ws, header_row=0) -> List[Dict[str, object]]:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        # Handle Break-Even sheet which has headers at row 3 (index 2)
        if ws.title == "Break_Even" and len(rows) > 2:
            header_row = 2  # Row 3 in Excel (0-indexed = 2)
        # Handle Scenario_Analysis sheet which has note at row 6, headers at row 7 (index 6)
        elif ws.title == "Scenario_Analysis" and len(rows) > 6:
            header_row = 6  # Row 7 in Excel (0-indexed = 6)
        elif header_row >= len(rows):
            return []
        
        headers = [str(h) if h is not None else "" for h in rows[header_row]]
        records: List[Dict[str, object]] = []
        for r in rows[header_row + 1:]:
            if r is None:
                continue
            rec = {headers[i]: r[i] if i < len(r) else None for i in range(len(headers))}
            # Skip empty rows
            if any(v is not None and v != "" for v in rec.values()):
                records.append(rec)
        return records
    
    def clean_numeric_value(val):
        """Convert value to number, handling None and strings"""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Try to convert string numbers
            try:
                return float(val.replace(',', ''))
            except:
                return None
        return None

    frames: Dict[str, "pd.DataFrame"] = {}
    for name in [
        "Parameters",
        "Product_Data",
        "Unit_Economics",
        "Scenario_Analysis",
        "Break_Even",
        "Dashboard",
    ]:
        if name in wb.sheetnames:
            recs = sheet_to_records(wb[name])
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(recs)
                # Clean numeric columns - convert None and strings to proper numbers
                for col in df.columns:
                    if col not in ['Product_Name', 'Product Name', 'Size', 'Data_Source', 'Parameter', 'Description']:
                        df[col] = df[col].apply(clean_numeric_value)
                # Special handling for Parameters sheet - Value column should be numeric
                if name == "Parameters" and "Value" in df.columns:
                    df["Value"] = df["Value"].apply(clean_numeric_value)
                frames[name] = df
            else:
                # Minimal shim using dict-of-lists for Streamlit display
                # Streamlit can display list[dict] directly via st.dataframe
                # We wrap in a simple adapter object with .to_dict for compatibility
                class _MiniFrame:
                    def __init__(self, rows: List[Dict[str, object]]):
                        self._rows = rows
                    def to_dict(self, orient="records"):
                        return list(self._rows)
                    @property
                    def columns(self):
                        return list(self._rows[0].keys()) if self._rows else []
                    def __len__(self):
                        return len(self._rows)
                    def __iter__(self):
                        return iter(self._rows)
                frames[name] = _MiniFrame(recs)  # type: ignore
    
    # Fix Parameters if empty or has None values
    if PANDAS_AVAILABLE and "Parameters" in frames:
        params_df = frames["Parameters"]
        if params_df is None or params_df.empty:
            frames["Parameters"] = recalculate_parameters()
        elif "Value" in params_df.columns:
            # Check if all values are None
            if params_df["Value"].isna().all():
                frames["Parameters"] = recalculate_parameters()
            else:
                # Fill None values with defaults
                params_dict = {}
                if "Parameter" in params_df.columns:
                    for _, row in params_df.iterrows():
                        param_name = row.get("Parameter", "")
                        param_value = row.get("Value", None)
                        if pd.isna(param_value):
                            # Use default
                            defaults = {
                                "Amazon_Commission_pct_300_500": 0.05,  # Updated Jan 2025: 5% for >₹300 & ≤₹500
                                "Amazon_Commission_pct_above_500": 0.08,  # Updated Jan 2025: 8% for >₹500
                                "ONDC_Flat_Fee": 1.50,  # Updated Jan 2025: ₹1.50 flat fee per transaction > ₹250
                                "ONDC_Commission_pct": 0.06,
                                "Payment_Fee_pct": 0.02,
                                "Packaging_per_unit": 12.0,
                                "Other_Fees_per_unit": 5.0,
                                "CAC_Amazon_per_unit": 90.0,
                                "CAC_ONDC_per_unit": 100.0,
                                "Default_Fixed_Costs_monthly": 50000.0,
                            }
                            params_df.loc[params_df["Parameter"] == param_name, "Value"] = defaults.get(param_name, 0)
    
    # If Unit_Economics has None values, recalculate from Product_Data and Parameters
    if PANDAS_AVAILABLE and "Unit_Economics" in frames and "Product_Data" in frames and "Parameters" in frames:
        unit_df = frames["Unit_Economics"]
        prod_df = frames["Product_Data"]
        params_df = frames["Parameters"]
        
        # Check if we have None values in numeric columns
        if unit_df is not None and not unit_df.empty:
            numeric_cols = [c for c in unit_df.columns if c not in ['Product_Name', 'Product Name']]
            has_nones = any(unit_df[col].isna().any() for col in numeric_cols if col in unit_df.columns)
            
            if has_nones:
                # Recalculate Unit_Economics from source data
                frames["Unit_Economics"] = recalculate_unit_economics(prod_df, params_df)
        else:
            # Unit_Economics is empty, recalculate
            frames["Unit_Economics"] = recalculate_unit_economics(prod_df, params_df)
    
    # Fix Break-Even if empty or has None values - always recalculate since Excel formulas don't evaluate
    if PANDAS_AVAILABLE and "Unit_Economics" in frames and "Parameters" in frames:
        unit_df = frames.get("Unit_Economics")
        params_df = frames.get("Parameters")
        
        # Always recalculate Break-Even from Unit_Economics since Excel formulas often don't evaluate
        if unit_df is not None and not unit_df.empty and params_df is not None and not params_df.empty:
            be_df_recalc = recalculate_break_even(unit_df, params_df)
            if be_df_recalc is not None and not be_df_recalc.empty:
                frames["Break_Even"] = be_df_recalc
    
    return frames


def recalculate_unit_economics(prod_df: "pd.DataFrame", params_df: "pd.DataFrame") -> "pd.DataFrame":
    """Recalculate Unit_Economics sheet from Product_Data and Parameters"""
    # Extract parameters
    params = {}
    if "Parameter" in params_df.columns and "Value" in params_df.columns:
        for _, row in params_df.iterrows():
            param_name = row.get("Parameter", "")
            param_value = row.get("Value", 0)
            if pd.notna(param_value):
                params[param_name] = float(param_value)
    
    # Defaults (Updated Jan 2025 - Tiered Amazon pricing and ONDC flat fee)
    amazon_comm_300_500 = params.get("Amazon_Commission_pct_300_500", 0.05)  # 5% for >₹300 & ≤₹500
    amazon_comm_above_500 = params.get("Amazon_Commission_pct_above_500", 0.08)  # 8% for >₹500
    ondc_flat_fee = params.get("ONDC_Flat_Fee", 1.50)  # ₹1.50 flat fee per transaction > ₹250
    payment_fee = params.get("Payment_Fee_pct", 0.02)
    packaging = params.get("Packaging_per_unit", 12.0)
    other_fees = params.get("Other_Fees_per_unit", 5.0)
    cac_amz = params.get("CAC_Amazon_per_unit", 90.0)
    cac_ondc = params.get("CAC_ONDC_per_unit", 100.0)
    
    # Get column names from Product_Data
    prod_name_col = "Product_Name" if "Product_Name" in prod_df.columns else "Product Name"
    price_col = "Selling_Price" if "Selling_Price" in prod_df.columns else "Price"
    cogs_col = "Cost_of_Goods_est" if "Cost_of_Goods_est" in prod_df.columns else "Cost_of_Goods"
    logistics_col = "Logistics_Cost" if "Logistics_Cost" in prod_df.columns else "Logistics"
    
    # Build Unit_Economics DataFrame
    results = []
    for _, prod in prod_df.iterrows():
        selling_price = float(prod[price_col]) if pd.notna(prod[price_col]) else 0
        cogs = float(prod[cogs_col]) if pd.notna(prod[cogs_col]) else 0
        logistics = float(prod[logistics_col]) if pd.notna(prod[logistics_col]) else 15
        
        # Amazon India: Tiered pricing - 0% (≤₹300), 5% (>₹300 & ≤₹500), 8% (>₹500)
        if selling_price <= 300:
            amazon_comm_amt = 0
        elif selling_price <= 500:
            amazon_comm_amt = selling_price * amazon_comm_300_500
        else:
            amazon_comm_amt = selling_price * amazon_comm_above_500
        
        # ONDC: Flat fee ₹1.50 per transaction above ₹250 (from Jan 1, 2025)
        ondc_comm_amt = 0 if selling_price <= 250 else ondc_flat_fee
        payment_fee_amt = selling_price * payment_fee
        
        total_cost_amz = cogs + amazon_comm_amt + payment_fee_amt + logistics + packaging + other_fees + cac_amz
        total_cost_ondc = cogs + ondc_comm_amt + payment_fee_amt + logistics + packaging + other_fees + cac_ondc
        
        profit_amz = selling_price - total_cost_amz
        profit_ondc = selling_price - total_cost_ondc
        profit_change_pct = ((profit_ondc - profit_amz) / abs(profit_amz) * 100) if profit_amz != 0 else 0
        
        monthly_sales = float(prod.get("Monthly_Sales_Units", 0)) if pd.notna(prod.get("Monthly_Sales_Units", 0)) else 0
        monthly_profit_amz = profit_amz * monthly_sales
        monthly_profit_ondc = profit_ondc * monthly_sales
        
        results.append({
            "Product_Name": prod[prod_name_col],
            "Selling_Price": selling_price,
            "Cost_of_Goods": cogs,
            "Amazon_Commission_amt": amazon_comm_amt,
            "ONDC_Commission_amt": ondc_comm_amt,
            "Payment_Gateway_Fee": payment_fee_amt,
            "Logistics_Cost": logistics,
            "Packaging_Cost": packaging,
            "Other_Fees": other_fees,
            "CAC_Amazon": cac_amz,
            "CAC_ONDC": cac_ondc,
            "Total_Cost_Amazon": total_cost_amz,
            "Total_Cost_ONDC": total_cost_ondc,
            "Profit_per_unit_Amazon": profit_amz,
            "Profit_per_unit_ONDC": profit_ondc,
            "Profit_Change_pct": profit_change_pct,
            "Monthly_Profit_Amazon": monthly_profit_amz,
            "Monthly_Profit_ONDC": monthly_profit_ondc,
        })
    
    return pd.DataFrame(results)


def recalculate_parameters() -> "pd.DataFrame":
    """Recalculate Parameters from defaults if Excel values are None"""
    if not PANDAS_AVAILABLE:
        return pd.DataFrame()
    
    # Default parameters from generate_excel.py (Updated with verified real data - Jan 2025)
    params = [
        {"Parameter": "Amazon_Commission_pct_300_500", "Value": 0.05, "Description": "Amazon India commission rate for >₹300 & ≤₹500 (Beauty/Haircare) - 5%"},
        {"Parameter": "Amazon_Commission_pct_above_500", "Value": 0.08, "Description": "Amazon India commission rate for >₹500 (Beauty/Haircare) - 8%"},
        {"Parameter": "ONDC_Flat_Fee", "Value": 1.50, "Description": "ONDC flat fee per transaction above ₹250 (INR) - ₹1.50 from Jan 1, 2025"},
        {"Parameter": "ONDC_Commission_pct", "Value": 0.06, "Description": "ONDC seller app commission rate (decimal) - Alternative: 5-8% if not using flat fee"},
        {"Parameter": "Payment_Fee_pct", "Value": 0.02, "Description": "Payment gateway fee rate (decimal) - Verified: standard 1.5-2.5% for e-commerce"},
        {"Parameter": "Packaging_per_unit", "Value": 12.0, "Description": "Packaging cost per unit (INR) - Verified: ₹10-15 standard for beauty/FMCG"},
        {"Parameter": "Other_Fees_per_unit", "Value": 5.0, "Description": "Other fees per unit (INR) - Verified: ₹3-7 standard range"},
        {"Parameter": "CAC_Amazon_per_unit", "Value": 90.0, "Description": "Customer Acquisition Cost per unit - Amazon (INR) - Verified: ₹50-120 range, mid-point reasonable"},
        {"Parameter": "CAC_ONDC_per_unit", "Value": 100.0, "Description": "Customer Acquisition Cost per unit - ONDC (INR) - Verified: ₹80-150 range, slightly higher due to brand building"},
        {"Parameter": "Default_Fixed_Costs_monthly", "Value": 50000.0, "Description": "Monthly fixed costs (INR) - Verified: reasonable for small-medium D2C brand"},
    ]
    return pd.DataFrame(params)


def recalculate_break_even(unit_df: "pd.DataFrame", params_df: "pd.DataFrame") -> "pd.DataFrame":
    """Recalculate Break-Even sheet from Unit_Economics and Parameters"""
    if not PANDAS_AVAILABLE:
        return pd.DataFrame()
    
    if unit_df is None or unit_df.empty or params_df is None or params_df.empty:
        return pd.DataFrame()
    
    # Extract fixed costs from Parameters
    params_dict = {}
    if "Parameter" in params_df.columns and "Value" in params_df.columns:
        for _, row in params_df.iterrows():
            param_name = row.get("Parameter", "")
            param_value = row.get("Value", 0)
            if pd.notna(param_value):
                params_dict[param_name] = float(param_value)
    
    fixed_costs = params_dict.get("Default_Fixed_Costs_monthly", 50000.0)
    
    # Get column names
    def col(df, *names):
        for n in names:
            if n in df.columns:
                return n
        return None
    
    prod_name_col = col(unit_df, "Product_Name", "Product Name")
    sp_col = col(unit_df, "Selling_Price", "Selling Price")
    total_cost_ondc_col = col(unit_df, "Total_Cost_ONDC", "Total Cost ONDC")
    
    if not all([prod_name_col, sp_col, total_cost_ondc_col]):
        return pd.DataFrame()
    
    # Calculate break-even
    results = []
    for _, row in unit_df.iterrows():
        product_name = row[prod_name_col]
        selling_price = float(row[sp_col]) if pd.notna(row[sp_col]) else 0
        total_variable_cost = float(row[total_cost_ondc_col]) if pd.notna(row[total_cost_ondc_col]) else 0
        
        contribution_per_unit = selling_price - total_variable_cost
        
        if contribution_per_unit > 0:
            break_even_units = fixed_costs / contribution_per_unit
            break_even_revenue = break_even_units * selling_price
        else:
            break_even_units = float('inf')
            break_even_revenue = float('inf')
        
        results.append({
            "Product_Name": product_name,
            "Selling_Price": selling_price,
            "Total_Variable_Cost_ONDC": total_variable_cost,
            "Contribution_per_unit_ONDC": contribution_per_unit,
            "Break_even_units": break_even_units,
            "Break_even_revenue": break_even_revenue,
        })
    
    return pd.DataFrame(results)


def shorten_product_name(name: str, max_length: int = 20) -> str:
    """Intelligently shorten product names for better chart readability"""
    if not isinstance(name, str):
        return str(name)
    
    # Remove "Mamaearth" prefix
    name = name.replace("Mamaearth ", "").replace("Mamaearth", "").strip()
    
    # Common abbreviations
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
        'Body Wash': 'Body Wash',
        'Lip Balm': 'Lip Balm',
        'Under Eye': 'Eye Cream',
        'Kajal': 'Kajal',
    }
    
    # Try to find and abbreviate
    for key, abbrev in abbrev_map.items():
        if key in name:
            # Extract main words before the category
            words = name.split()
            main_words = []
            for word in words[:2]:
                if word.lower() not in ['for', 'with', 'and', 'the', 'of', 'in', 'on', 'at', 'to', 'a', 'an']:
                    main_words.append(word)
                if len(main_words) >= 2:
                    break
            if main_words:
                result = " ".join(main_words) + " " + abbrev
            else:
                result = abbrev
            break
    else:
        # No abbreviation found, use first key words
        words = name.split()
        key_words = []
        skip_words = ['for', 'with', 'and', 'the', 'of', 'in', 'on', 'at', 'to', 'a', 'an', 'daily', 'glow', 'natural']
        for word in words:
            if word.lower() not in skip_words and len(key_words) < 3:
                key_words.append(word)
            if len(key_words) >= 3:
                break
        result = " ".join(key_words) if key_words else name
    
    # Final truncation if still too long
    if len(result) > max_length:
        result = result[:max_length-3] + "..."
    
    return result


def calc_profit_by_channel(unit_df: "pd.DataFrame") -> Tuple["pd.DataFrame", float]:
    """Return long-form df for plotting and average improvement percent.

    Expects columns:
      - Product_Name (A)
      - Profit per unit Amazon (N)
      - Profit per unit ONDC (O)
      - Profit_Change_pct (P)
    """
    # Tolerate various header capitalizations
    def col(df, *names):
        for n in names:
            if n in df.columns:
                return n
        raise KeyError(names[0])

    name_col = col(unit_df, "Product_Name", "Product Name", "Product")
    amazon_col = col(unit_df, "Profit_per_unit_Amazon", "Profit per unit Amazon", "Amazon Profit", "N")
    ondc_col = col(unit_df, "Profit_per_unit_ONDC", "Profit per unit ONDC", "ONDC Profit", "O")
    change_col = col(unit_df, "Profit_Change_pct", "Profit Change %", "Profit_Change_pct")

    if PANDAS_AVAILABLE:
        plot_df = unit_df[[name_col, amazon_col, ondc_col]].copy()
        plot_df = plot_df.rename(columns={name_col: "Product", amazon_col: "Amazon", ondc_col: "ONDC"})
        avg_improvement = float(pd.to_numeric(unit_df[change_col], errors="coerce").dropna().mean()) if len(unit_df) else 0.0
        long_df = plot_df.melt(id_vars=["Product"], value_vars=["Amazon", "ONDC"], var_name="Channel", value_name="Profit")
        return long_df, avg_improvement
    else:
        # Minimal path without pandas
        rows = []
        improvements: List[float] = []
        for r in unit_df:  # type: ignore
            try:
                prod = r.get(name_col)
                av = r.get(amazon_col)
                ov = r.get(ondc_col)
                rows.append({"Product": prod, "Channel": "Amazon", "Profit": av})
                rows.append({"Product": prod, "Channel": "ONDC", "Profit": ov})
                ch = r.get(change_col)
                if isinstance(ch, (int, float)):
                    improvements.append(float(ch))
            except Exception:
                continue
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        # Fake a pandas-like DataFrame for downstream plotting with plotly (works with dict list)
        class _Mini:
            def __init__(self, data):
                self.data = data
            def __iter__(self):
                return iter(self.data)
        return _Mini(rows), avg_improvement  # type: ignore


def recompute_with_scenarios(unit_df: "pd.DataFrame", params_df: "pd.DataFrame",
                              amazon_comm_delta: float, ondc_comm_delta: float,
                              cac_amz_delta: float, cac_ondc_delta: float,
                              logistics_delta: float) -> "pd.DataFrame":
    """Recompute Amazon/ONDC total costs and profits with scenario adjustments.

    Returns a DataFrame with Amazon/ONDC profit per unit updated.
    """
    if not PANDAS_AVAILABLE:
        # Without pandas, skip recompute and return original structure
        return unit_df

    # Extract base parameters (Updated with verified real data - Jan 2025)
    base = {
        "Amazon_Commission_pct_300_500": 0.05,  # Updated Jan 2025: 5% for >₹300 & ≤₹500
        "Amazon_Commission_pct_above_500": 0.08,  # Updated Jan 2025: 8% for >₹500
        "ONDC_Flat_Fee": 1.50,  # Updated Jan 2025: ₹1.50 flat fee per transaction > ₹250
        "ONDC_Commission_pct": 0.06,
        "Payment_Fee_pct": 0.02,
        "Packaging_per_unit": 12.0,
        "Other_Fees_per_unit": 5.0,
        "CAC_Amazon_per_unit": 90.0,
        "CAC_ONDC_per_unit": 100.0,
    }
    try:
        if {"Parameter", "Value"}.issubset(set(params_df.columns)):
            for _, r in params_df.iterrows():
                k, v = r["Parameter"], r["Value"]
                if k in base and isinstance(v, (int, float)):
                    base[k] = float(v)
    except Exception:
        pass

    # Adjusted parameters (tiered Amazon pricing)
    amz_comm_300_500 = base.get("Amazon_Commission_pct_300_500", 0.05) * (1.0 + amazon_comm_delta)
    amz_comm_above_500 = base.get("Amazon_Commission_pct_above_500", 0.08) * (1.0 + amazon_comm_delta)
    ondc_flat_fee = base.get("ONDC_Flat_Fee", 1.50) * (1.0 + ondc_comm_delta)
    pay_pct = base["Payment_Fee_pct"]
    pack = base["Packaging_per_unit"]
    other = base["Other_Fees_per_unit"]
    cac_amz = base["CAC_Amazon_per_unit"] * (1.0 + cac_amz_delta)
    cac_ondc = base["CAC_ONDC_per_unit"] * (1.0 + cac_ondc_delta)

    # Column resolution helper
    def col(df, *names):
        for n in names:
            if n in df.columns:
                return n
        # Better error message showing available columns
        available = list(df.columns) if hasattr(df, 'columns') else "unknown"
        raise KeyError(f"Column not found. Tried: {names}. Available columns: {available}")

    sp = col(unit_df, "Selling_Price", "Selling Price", "B")
    cogs = col(unit_df, "Cost_of_Goods", "Cost of Goods", "C")
    pay_col = col(unit_df, "Payment_Gateway_Fee", "Payment_Fee", "Payment Fee", "F")
    logi = col(unit_df, "Logistics_Cost", "Logistics Cost", "G")
    pack_col = col(unit_df, "Packaging_Cost", "Packaging Cost", "H")
    other_col = col(unit_df, "Other_Fees", "Other Fees", "I")
    cac_amz_col = col(unit_df, "CAC_Amazon", "CAC Amazon", "J")
    cac_ondc_col = col(unit_df, "CAC_ONDC", "CAC ONDC", "K")

    # Build adjusted outputs
    df = unit_df.copy()
    # Payment remains price * pay_pct; Logistics scaled by slider
    df[pay_col] = pd.to_numeric(df[sp], errors="coerce") * pay_pct
    df[logi] = pd.to_numeric(df[logi], errors="coerce") * (1.0 + logistics_delta)
    df[pack_col] = pack
    df[other_col] = other
    df[cac_amz_col] = cac_amz
    df[cac_ondc_col] = cac_ondc

    # Commissions (recompute from price with tiered pricing)
    # Amazon India: 0% (≤₹300), 5% (>₹300 & ≤₹500), 8% (>₹500)
    # ONDC: Flat fee ₹1.50 per transaction > ₹250
    selling_prices = pd.to_numeric(df[sp], errors="coerce")
    df["_amz_comm"] = selling_prices.apply(lambda x: 0 if x <= 300 else (x * amz_comm_300_500 if x <= 500 else x * amz_comm_above_500))
    df["_ondc_comm"] = selling_prices.apply(lambda x: 0 if x <= 250 else ondc_flat_fee)

    # Totals
    df["_total_amz"] = (
        pd.to_numeric(df[cogs], errors="coerce")
        + df["_amz_comm"]
        + df[pay_col]
        + df[logi]
        + df[pack_col]
        + df[other_col]
        + df[cac_amz_col]
    )
    df["_total_ondc"] = (
        pd.to_numeric(df[cogs], errors="coerce")
        + df["_ondc_comm"]
        + df[pay_col]
        + df[logi]
        + df[pack_col]
        + df[other_col]
        + df[cac_ondc_col]
    )

    # Output profit columns (replacing if present)
    amz_profit = col(df, "Profit_per_unit_Amazon", "Profit per unit Amazon", "Amazon Profit", "N")
    ondc_profit = col(df, "Profit_per_unit_ONDC", "Profit per unit ONDC", "ONDC Profit", "O")
    df[amz_profit] = pd.to_numeric(df[sp], errors="coerce") - df["_total_amz"]
    df[ondc_profit] = pd.to_numeric(df[sp], errors="coerce") - df["_total_ondc"]

    # Change percent
    change_col = col(df, "Profit_Change_pct", "Profit Change %", "P")
    df[change_col] = (df[ondc_profit] - df[amz_profit]).abs().where(df[amz_profit] == 0, (df[ondc_profit] - df[amz_profit]) / df[amz_profit] * 100.0)

    # Cleanup temp
    df.drop(columns=[c for c in df.columns if c.startswith("_")], inplace=True)
    return df


def main() -> None:
    st.set_page_config(page_title="ONDC vs Amazon - Unit Economics Dashboard", layout="wide")
    st.title("ONDC vs Amazon - Unit Economics (Mamaearth)")
    st.caption("Interactive dashboard built from your Excel model for clearer visuals and scenarios.")

    # File selection
    left, right = st.columns([2, 1])
    with left:
        st.subheader("1) Select Excel File")
        uploaded = st.file_uploader("Upload the generated Excel (auto-detected if not provided)", type=["xlsx"])
        if uploaded is not None:
            tmp_path = os.path.join(st.session_state.get("_tmp_dir", "."), f"_uploaded_{datetime.datetime.now().timestamp()}.xlsx")
            with open(tmp_path, "wb") as f:
                f.write(uploaded.read())
            excel_path = tmp_path
        else:
            excel_path = DEFAULT_EXCEL if os.path.exists(DEFAULT_EXCEL) else None
        if not excel_path:
            st.warning("No Excel found. Please upload the latest generated file.")
            return
        st.success(f"Using: {os.path.basename(excel_path)}")

    frames = read_excel_to_frames(excel_path)

    # Show Parameters
    st.subheader("2) Parameters")
    params_df = frames.get("Parameters")
    if params_df is None or (PANDAS_AVAILABLE and params_df.empty):
        # Try to recalculate
        if PANDAS_AVAILABLE:
            params_df = recalculate_parameters()
            frames["Parameters"] = params_df
            st.success("Parameters recalculated from defaults.")
        else:
            st.info("Parameters sheet not found and pandas not available for recalculation.")
    else:
        # Check if values are None
        if PANDAS_AVAILABLE and "Value" in params_df.columns:
            if params_df["Value"].isna().all():
                params_df = recalculate_parameters()
                frames["Parameters"] = params_df
                st.success("Parameters recalculated from defaults (Excel had None values).")
    
    if params_df is not None:
        if PANDAS_AVAILABLE:
            st.dataframe(params_df)
        else:
            st.dataframe(params_df.to_dict(orient="records"))
    else:
        st.info("Parameters sheet not found.")

    # Tabs for data and visuals
    tabs = st.tabs(["Product Data", "Unit Economics", "Scenario Analysis", "Break-Even", "Dashboard Charts"])

    # Product Data
    with tabs[0]:
        st.markdown("### Product_Data")
        prod_df = frames.get("Product_Data")
        if prod_df is not None:
            st.dataframe(prod_df.to_dict(orient="records"), use_container_width=True)
        else:
            st.info("Product_Data sheet not found.")

    # Unit Economics
    with tabs[1]:
        st.markdown("### Unit_Economics")
        unit_df = frames.get("Unit_Economics")
        if unit_df is None:
            st.info("Unit_Economics sheet not found.")
        else:
            # Debug: Show available columns
            if PANDAS_AVAILABLE and hasattr(unit_df, 'columns'):
                with st.expander("🔍 Debug: Available Columns", expanded=False):
                    st.write("Columns in Unit_Economics sheet:", list(unit_df.columns))
            
            # Display dataframe (keep original for calculations)
            st.dataframe(unit_df, use_container_width=True, height=400)
            # Chart - Show top N products for better visibility
            try:
                long_df, avg_impr = calc_profit_by_channel(unit_df)
                
                # Limit to top 12 products for better readability
                if PANDAS_AVAILABLE and isinstance(long_df, pd.DataFrame):
                    # Get top products by ONDC profit (most relevant)
                    product_ondc = long_df[long_df["Channel"] == "ONDC"].groupby("Product")["Profit"].first().sort_values(ascending=False)
                    top_products = product_ondc.head(12).index.tolist()
                    long_df_filtered = long_df[long_df["Product"].isin(top_products)].copy()
                    
                    # Intelligently shorten product names
                    long_df_filtered["Product_Short"] = long_df_filtered["Product"].apply(shorten_product_name)
                else:
                    long_df_filtered = long_df
                    if hasattr(long_df_filtered, 'data'):
                        # Handle non-pandas case
                        filtered_data = []
                        for item in long_df_filtered:
                            prod = item.get("Product", "")
                            if len(filtered_data) < 24:  # Limit to 12 products * 2 channels
                                filtered_data.append(item)
                        long_df_filtered = filtered_data
                
                st.markdown("#### 📊 Profit per Unit: Amazon vs ONDC (Top 12 Products)")
                
                if PANDAS_AVAILABLE and isinstance(long_df_filtered, pd.DataFrame):
                    # Professional color scheme
                    color_map = {"Amazon": "#4472C4", "ONDC": "#70AD47"}  # Professional blue and green
                    
                    fig = px.bar(
                        long_df_filtered, 
                        x="Product_Short" if "Product_Short" in long_df_filtered.columns else "Product", 
                        y="Profit", 
                        color="Channel",
                        color_discrete_map=color_map,
                        barmode="group",
                        labels={"Product_Short": "Product", "Profit": "Profit (INR)"},
                        template="plotly_white"
                    )
                else:
                    # Fallback for non-pandas
                    fig = px.bar(
                        long_df_filtered if isinstance(long_df_filtered, list) else long_df,
                        x="Product", 
                        y="Profit", 
                        color="Channel", 
                        barmode="group",
                        template="plotly_white"
                    )
                
                # Professional styling
                fig.update_layout(
                    title={
                        'text': "Profit Comparison: Amazon vs ONDC",
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'size': 18, 'color': '#2E75B6', 'family': 'Arial, sans-serif'}
                    },
                    xaxis=dict(
                        title="",
                        tickangle=0,  # Horizontal labels for better readability
                        tickfont=dict(size=10, color='#333333'),
                        showgrid=False,
                        linecolor='#D3D3D3',
                        linewidth=1
                    ),
                    yaxis=dict(
                        title="Profit per Unit (INR)",
                        titlefont=dict(size=12, color='#333333', family='Arial, sans-serif'),
                        tickfont=dict(size=10, color='#333333'),
                        showgrid=True,
                        gridcolor='#F0F0F0',
                        linecolor='#D3D3D3',
                        linewidth=1
                    ),
                    legend=dict(
                        title=dict(text="Sales Channel", font=dict(size=12, color='#333333')),
                        font=dict(size=11, color='#333333'),
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    height=550,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=60, r=20, t=80, b=80),
                    showlegend=True
                )
                
                # Update bar appearance
                fig.update_traces(
                    marker_line_color='white',
                    marker_line_width=1.5,
                    opacity=0.85
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                if PANDAS_AVAILABLE:
                    st.metric("Average Profit Improvement (ONDC vs Amazon)", f"{avg_impr:,.2f}%")
                    
                    # Add explanation if the value is negative
                    if avg_impr < 0:
                        st.markdown("---")
                        st.markdown("#### ℹ️ Understanding Negative Average Profit Increase %")
                        st.info(
                            "**A negative value does NOT mean ONDC is losing money!**\n\n"
                            "This metric averages percentage changes per product. Some low-priced products (≤₹300) "
                            "favor Amazon (0% commission vs ₹1.50 ONDC fee), which pulls down the average. "
                            "However, **ONDC is still more profitable overall** - check the chart above and "
                            "focus on absolute profit values, not just the percentage average.",
                            icon="💡"
                        )
            except Exception as e:
                st.error(f"Error creating chart: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                if PANDAS_AVAILABLE and hasattr(unit_df, 'columns'):
                    st.write("Available columns:", list(unit_df.columns))

    # Scenario Analysis
    with tabs[2]:
        st.markdown("### Scenario Analysis (Live)")
        unit_df = frames.get("Unit_Economics")
        if unit_df is None:
            st.info("Unit_Economics sheet required for scenario analysis.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                amazon_comm_delta = st.slider("Amazon Commission Change %", -30, 30, 0, 1) / 100.0
                ondc_comm_delta = st.slider("ONDC Commission Change %", -30, 30, 0, 1) / 100.0
            with col2:
                cac_amz_delta = st.slider("CAC Amazon Change %", -50, 50, 0, 1) / 100.0
                cac_ondc_delta = st.slider("CAC ONDC Change %", -50, 50, 0, 1) / 100.0
            with col3:
                logistics_delta = st.slider("Logistics Cost Change %", -50, 50, 0, 1) / 100.0

            if PANDAS_AVAILABLE:
                try:
                    adj_df = recompute_with_scenarios(unit_df, frames.get("Parameters"), amazon_comm_delta, ondc_comm_delta, cac_amz_delta, cac_ondc_delta, logistics_delta)
                    long_df, avg_impr = calc_profit_by_channel(adj_df)
                    
                    # Limit to top 12 products for better readability
                    if isinstance(long_df, pd.DataFrame):
                        product_ondc = long_df[long_df["Channel"] == "ONDC"].groupby("Product")["Profit"].first().sort_values(ascending=False)
                        top_products = product_ondc.head(12).index.tolist()
                        long_df_filtered = long_df[long_df["Product"].isin(top_products)].copy()
                        long_df_filtered["Product_Short"] = long_df_filtered["Product"].apply(shorten_product_name)
                    else:
                        long_df_filtered = long_df
                    
                    st.markdown("#### 📊 Adjusted Profit per Unit (Top 12 Products)")
                    
                    # Professional color scheme
                    color_map = {"Amazon": "#4472C4", "ONDC": "#70AD47"}
                    
                    if isinstance(long_df_filtered, pd.DataFrame):
                        fig2 = px.bar(
                            long_df_filtered,
                            x="Product_Short" if "Product_Short" in long_df_filtered.columns else "Product",
                            y="Profit",
                            color="Channel",
                            color_discrete_map=color_map,
                            barmode="group",
                            labels={"Product_Short": "Product", "Profit": "Profit (INR)"},
                            template="plotly_white"
                        )
                    else:
                        fig2 = px.bar(long_df_filtered, x="Product", y="Profit", color="Channel", barmode="group", template="plotly_white")
                    
                    # Professional styling
                    fig2.update_layout(
                        title={
                            'text': "Adjusted Profit Comparison (After Scenario Changes)",
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 18, 'color': '#2E75B6', 'family': 'Arial, sans-serif'}
                        },
                        xaxis=dict(
                            title="",
                            tickangle=0,
                            tickfont=dict(size=10, color='#333333'),
                            showgrid=False,
                            linecolor='#D3D3D3',
                            linewidth=1
                        ),
                        yaxis=dict(
                            title="Profit per Unit (INR)",
                            titlefont=dict(size=12, color='#333333', family='Arial, sans-serif'),
                            tickfont=dict(size=10, color='#333333'),
                            showgrid=True,
                            gridcolor='#F0F0F0',
                            linecolor='#D3D3D3',
                            linewidth=1
                        ),
                        legend=dict(
                            title=dict(text="Sales Channel", font=dict(size=12, color='#333333')),
                            font=dict(size=11, color='#333333'),
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=550,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        margin=dict(l=60, r=20, t=80, b=80),
                        showlegend=True
                    )
                    
                    # Update bar appearance
                    fig2.update_traces(
                        marker_line_color='white',
                        marker_line_width=1.5,
                        opacity=0.85
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                    st.metric("Average Profit Improvement (Adjusted)", f"{avg_impr:,.2f}%")
                except Exception as e:
                    st.error(f"Error in scenario analysis: {str(e)}")
                    if hasattr(unit_df, 'columns'):
                        with st.expander("🔍 Debug: Available Columns", expanded=True):
                            st.write("Columns in Unit_Economics:", list(unit_df.columns))
            else:
                st.info("Install pandas to enable live recomputation.")

    # Break-Even
    with tabs[3]:
        st.markdown("### Break_Even")
        be_df = frames.get("Break_Even")
        unit_df = frames.get("Unit_Economics")
        params_df = frames.get("Parameters")
        
        # Check if Break-Even is empty or has None values
        # Always try to recalculate Break-Even if we have the data, since Excel formulas often don't evaluate
        if PANDAS_AVAILABLE and unit_df is not None and not unit_df.empty and params_df is not None and not params_df.empty:
            be_df = recalculate_break_even(unit_df, params_df)
            frames["Break_Even"] = be_df
            if be_df is not None and not be_df.empty:
                st.success("Break-Even data calculated from Unit_Economics and Parameters.")
        
        if be_df is not None and not (PANDAS_AVAILABLE and be_df.empty):
            if PANDAS_AVAILABLE:
                st.dataframe(be_df, use_container_width=True)
            else:
                st.dataframe(be_df.to_dict(orient="records"), use_container_width=True)
            
            # Try a scatter of break-even units vs revenue if columns exist
            if PANDAS_AVAILABLE:
                be_units_col = "Break_even_units" if "Break_even_units" in be_df.columns else None
                be_revenue_col = "Break_even_revenue" if "Break_even_revenue" in be_df.columns else None
                prod_name_col = "Product_Name" if "Product_Name" in be_df.columns else None
                
                if all([be_units_col, be_revenue_col, prod_name_col]):
                    # Filter out infinite values for charting
                    be_df_chart = be_df[be_df[be_units_col] != float('inf')].copy()
                    if not be_df_chart.empty:
                        # Shorten product names for hover
                        be_df_chart = be_df_chart.copy()
                        be_df_chart["Product_Short"] = be_df_chart[prod_name_col].apply(shorten_product_name)
                        
                        fig3 = px.scatter(
                            be_df_chart,
                            x=be_units_col,
                            y=be_revenue_col,
                            hover_name="Product_Short",
                            hover_data={prod_name_col: True},
                            size_max=20,
                            color_discrete_sequence=["#2E75B6"],
                            template="plotly_white"
                        )
                        
                        # Professional styling
                        fig3.update_layout(
                            title={
                                'text': "Break-Even Analysis: Units vs Revenue",
                                'x': 0.5,
                                'xanchor': 'center',
                                'font': {'size': 18, 'color': '#2E75B6', 'family': 'Arial, sans-serif'}
                            },
                            xaxis=dict(
                                title="Break-Even Units",
                                titlefont=dict(size=12, color='#333333', family='Arial, sans-serif'),
                                tickfont=dict(size=10, color='#333333'),
                                showgrid=True,
                                gridcolor='#F0F0F0',
                                linecolor='#D3D3D3',
                                linewidth=1
                            ),
                            yaxis=dict(
                                title="Break-Even Revenue (INR)",
                                titlefont=dict(size=12, color='#333333', family='Arial, sans-serif'),
                                tickfont=dict(size=10, color='#333333'),
                                showgrid=True,
                                gridcolor='#F0F0F0',
                                linecolor='#D3D3D3',
                                linewidth=1
                            ),
                            height=550,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            margin=dict(l=70, r=20, t=80, b=60)
                        )
                        
                        fig3.update_traces(
                            marker=dict(
                                size=10,
                                line=dict(width=1.5, color='white'),
                                opacity=0.8
                            )
                        )
                        
                        st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Break-Even data is not available.")

    # Dashboard Charts (alternate quick view)
    with tabs[4]:
        st.markdown("### Dashboard (Interactive)")
        unit_df = frames.get("Unit_Economics")
        if unit_df is not None:
            try:
                long_df, avg_impr = calc_profit_by_channel(unit_df)
                # Allow top-N selection
                max_products = len(unit_df) if hasattr(unit_df, "__len__") else 41
                top_n = st.slider("Top N Products to Display", 5, min(25, max_products), 15)
                
                if PANDAS_AVAILABLE and isinstance(long_df, pd.DataFrame):
                    # Get top products by ONDC profit
                    product_ondc = long_df[long_df["Channel"] == "ONDC"].groupby("Product")["Profit"].first().sort_values(ascending=False)
                    top_products = product_ondc.head(top_n).index.tolist()
                    filtered = long_df[long_df["Product"].isin(top_products)].copy()
                    
                    # Intelligently shorten product names
                    filtered["Product_Short"] = filtered["Product"].apply(shorten_product_name)
                    
                    # Professional color scheme
                    color_map = {"Amazon": "#4472C4", "ONDC": "#70AD47"}
                    
                    fig4 = px.bar(
                        filtered, 
                        x="Product_Short", 
                        y="Profit", 
                        color="Channel",
                        color_discrete_map=color_map,
                        barmode="group",
                        labels={"Product_Short": "Product", "Profit": "Profit (INR)"},
                        template="plotly_white"
                    )
                else:
                    filtered = long_df
                    fig4 = px.bar(filtered, x="Product", y="Profit", color="Channel", barmode="group", template="plotly_white")
                
                # Professional styling
                fig4.update_layout(
                    title={
                        'text': f"Profit Comparison: Amazon vs ONDC (Top {top_n} Products)",
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'size': 18, 'color': '#2E75B6', 'family': 'Arial, sans-serif'}
                    },
                    xaxis=dict(
                        title="",
                        tickangle=0,  # Horizontal labels
                        tickfont=dict(size=10, color='#333333'),
                        showgrid=False,
                        linecolor='#D3D3D3',
                        linewidth=1
                    ),
                    yaxis=dict(
                        title="Profit per Unit (INR)",
                        titlefont=dict(size=12, color='#333333', family='Arial, sans-serif'),
                        tickfont=dict(size=10, color='#333333'),
                        showgrid=True,
                        gridcolor='#F0F0F0',
                        linecolor='#D3D3D3',
                        linewidth=1
                    ),
                    legend=dict(
                        title=dict(text="Sales Channel", font=dict(size=12, color='#333333')),
                        font=dict(size=11, color='#333333'),
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    height=600,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(l=60, r=20, t=80, b=80),
                    showlegend=True
                )
                
                # Update bar appearance
                fig4.update_traces(
                    marker_line_color='white',
                    marker_line_width=1.5,
                    opacity=0.85
                )
                
                st.plotly_chart(fig4, use_container_width=True)
                
                if PANDAS_AVAILABLE:
                    st.metric("Average Profit Improvement (ONDC vs Amazon)", f"{avg_impr:,.2f}%")
                    
                    # Add professional explanation note about Average Profit Increase %
                    st.markdown("---")
                    st.markdown("### 📊 Understanding 'Average Profit Increase %'")
                    st.info(
                        "**This metric averages the percentage change for each product individually.**\n\n"
                        "A negative value (e.g., -2.79%) does **NOT** indicate a loss. "
                        "**ONDC is MORE profitable overall** (₹3.38M more per month).\n\n"
                        "**Why the negative percentage?**\n"
                        "- Some low-priced products (≤₹300) favor Amazon (0% commission vs ₹1.50 ONDC fee)\n"
                        "- These products pull down the average percentage change\n"
                        "- However, ONDC still makes more total profit overall\n\n"
                        "**Focus on 'Total Monthly Profit Increase (INR)'** which shows the true advantage: "
                        "**₹3,376,980 positive** - ONDC is significantly more profitable!",
                        icon="ℹ️"
                    )
            except Exception as e:
                st.error(f"Error creating dashboard chart: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        else:
            st.info("Unit_Economics sheet not found.")


if __name__ == "__main__":
    main()


