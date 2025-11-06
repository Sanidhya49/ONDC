# ONDC vs Amazon Unit Economics Analysis for D2C Brands

This project simulates the financial impact of a D2C brand (Mamaearth) selling via Amazon vs ONDC (Open Network for Digital Commerce).

## Project Structure

```
ONDC/
├── requirements.txt
├── README.md
├── setup_env.ps1          # PowerShell script to set up virtual environment
├── setup_env.sh           # Bash script to set up virtual environment
├── scrape_products.py     # Script to scrape Mamaearth product data
├── generate_excel.py      # Script to generate Excel workbook with all analysis
├── Mamaearth_ONDC_UnitEconomics.xlsx  # Generated Excel workbook
├── Strategic_Report.md    # Strategic analysis report
├── LinkedIn_Post.md       # LinkedIn-ready summary
└── data/
    └── products.json      # Scraped product data
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

1. **Scrape Product Data:**
   ```bash
   python scrape_products.py
   ```

2. **Generate Excel Workbook:**
   ```bash
   python generate_excel.py
   ```

3. Open `Mamaearth_ONDC_UnitEconomics.xlsx` (or the timestamped variant) to view the analysis

4. **Run Streamlit Dashboard (Interactive):**
   ```bash
   # Activate your venv first
   # Windows: venv\Scripts\activate
   # Linux/Mac: source venv/bin/activate

   streamlit run streamlit_app.py
   ```
   The app auto-loads the latest Excel (`Mamaearth_ONDC_UnitEconomics_20251106_032226.xlsx`) if present, or you can upload any generated Excel via the UI.

## Project Deliverables

1. Excel workbook with 6 sheets: Parameters, Product_Data, Unit_Economics, Scenario_Analysis, Break_Even, Dashboard
2. Strategic Report (Strategic_Report.md)
3. LinkedIn Post (LinkedIn_Post.md)
4. Python scripts for automation

