#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    
    # Check if venv creation was successful
    if [ ! -d ".venv" ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate a random secret key for Flask
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "SECRET_KEY=${SECRET_KEY}" > .env
    echo "OLLAMA_API_URL=http://127.0.0.1:11434/api" >> .env
    echo ".env file created with a random secret key"
else
    echo ".env file already exists"
fi

echo ""
echo "Setup complete! You can now run the application with:"
echo "source .venv/bin/activate && python app.py"
echo ""
echo "Then visit http://127.0.0.1:5000 in your browser"