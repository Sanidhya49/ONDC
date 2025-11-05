# Quick Start Guide - Running the Scraper

## 🚀 Commands to Run

### Step 1: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 2: Run the Advanced Scraper

```bash
python scrape_advanced.py
```

### Step 3: Choose Your Mode

When prompted, choose:
- **1** = Visible browser (see what's happening) - **Best for learning!**
- **2** = Headless browser (faster, background)
- **3** = Requests only (fastest, may be blocked)

---

## 📋 Complete Command Sequence (Windows)

```powershell
# Navigate to project directory (if not already there)
cd D:\Sanskar_vault\sanskar_project\ONDC

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the advanced scraper
python scrape_advanced.py
```

---

## 📋 Complete Command Sequence (Linux/Mac)

```bash
# Navigate to project directory
cd /path/to/ONDC

# Activate virtual environment
source venv/bin/activate

# Run the advanced scraper
python scrape_advanced.py
```

---

## ⏱️ What to Expect

- **Time:** 15-30 minutes for 41 products
- **Output:** You'll see progress for each product
- **Result:** Data saved to `data/products.json` and `data/products.csv`

---

## 🎯 After Scraping Completes

Run this to generate Excel workbook:

```bash
python generate_excel.py
```

---

## 📝 Quick Reference

| Command | Purpose |
|---------|---------|
| `python scrape_advanced.py` | Run advanced scraper (3 sources) |
| `python scrape_real_data.py` | Run basic scraper (fallback) |
| `python generate_excel.py` | Generate Excel workbook |

---

**That's it! Just run `python scrape_advanced.py` and follow the prompts!** 🚀

