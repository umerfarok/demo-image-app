#!/bin/bash

# Deployment helper script for the Product Generator App

# Ensure script stops on first error
set -e

echo "🚀 Starting deployment process for Product Generator App..."

# Ensure environment variables are set
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create an .env file based on the .env.example template."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if MySQL is running
echo "🔍 Checking database connection..."
if python -c "import mysql.connector; mysql.connector.connect(host='$(grep DB_HOST .env | cut -d '=' -f2)', user='$(grep DB_USER .env | cut -d '=' -f2)', password='$(grep DB_PASSWORD .env | cut -d '=' -f2)')"; then
    echo "✅ Database connection successful!"
else
    echo "❌ Error: Could not connect to MySQL database."
    echo "Please check your database credentials in the .env file."
    exit 1
fi

# Create the database and tables if they don't exist
echo "🗄️ Setting up database tables..."
mysql -u "$(grep DB_USER .env | cut -d '=' -f2)" -p"$(grep DB_PASSWORD .env | cut -d '=' -f2)" < db_init.sql

# Ensure images directory exists
echo "📁 Creating required directories..."
mkdir -p images

# Run the application
echo "🌟 Setup complete! Starting the application..."
echo ""
echo "You can access the application at http://localhost:8501"
echo ""
streamlit run app.py
