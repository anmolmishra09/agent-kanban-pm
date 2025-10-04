#!/bin/bash
# Setup script for Agent Kanban PM

echo "========================================="
echo "Agent Kanban PM - Setup Script"
echo "========================================="
echo ""

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.9 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Install python3-venv if needed (for Ubuntu/Debian)
if ! python3 -m venv --help &> /dev/null; then
    echo "Installing python3-venv..."
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3-venv
    else
        echo "Warning: Could not install python3-venv automatically."
        echo "Please install it manually for your system."
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     python main.py"
echo ""
echo "  3. Access the API documentation:"
echo "     http://localhost:8000/docs"
echo ""
echo "========================================="
