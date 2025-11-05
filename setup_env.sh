#!/bin/bash
# Bash script to set up virtual environment for Linux/Mac

echo "Setting up virtual environment..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup complete! Virtual environment is activated."
echo "To activate in future sessions, run: source venv/bin/activate"

