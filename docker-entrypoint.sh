#!/bin/bash
set -e

# Function to check if MySQL is ready
check_mysql() {
  echo "Checking MySQL connection..."
  python -c "
import mysql.connector
import time
import os
import sys

host = os.environ.get('DB_HOST')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
database = os.environ.get('DB_NAME')

for i in range(30):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if conn.is_connected():
            print('MySQL connection successful')
            conn.close()
            sys.exit(0)
    except Exception as e:
        print(f'Attempt {i+1}: MySQL connection failed - {e}')
        time.sleep(2)

print('Failed to connect to MySQL after multiple attempts')
sys.exit(1)
"
}

# Check MySQL connection
check_mysql

# Execute the provided command
exec "$@"
