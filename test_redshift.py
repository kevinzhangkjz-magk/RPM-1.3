#!/usr/bin/env python3
"""Test Redshift connection and query sites"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/backend/.env')

# Redshift connection parameters
conn_params = {
    'host': os.getenv('REDSHIFT_HOST'),
    'port': int(os.getenv('REDSHIFT_PORT', 5439)),
    'database': os.getenv('REDSHIFT_DATABASE'),
    'user': os.getenv('REDSHIFT_USER'),
    'password': os.getenv('REDSHIFT_PASSWORD'),
    'sslmode': 'require' if os.getenv('REDSHIFT_SSL', 'true').lower() == 'true' else 'prefer'
}

print("Testing Redshift connection...")
print(f"Host: {conn_params['host']}")
print(f"Database: {conn_params['database']}")
print(f"User: {conn_params['user']}")

try:
    # Connect to Redshift
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    print("✅ Connected to Redshift successfully!")
    
    # Test query - get sites
    query = """
    SELECT DISTINCT site_id, site_name 
    FROM solar_sites 
    LIMIT 5
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"\n📊 Found {len(results)} sites:")
    for site_id, site_name in results:
        print(f"  - {site_id}: {site_name}")
    
    # Check total number of sites
    cursor.execute("SELECT COUNT(DISTINCT site_id) FROM solar_sites")
    total = cursor.fetchone()[0]
    print(f"\n📈 Total sites in database: {total}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error connecting to Redshift: {e}")
    print("\nPossible issues:")
    print("1. Check if Redshift cluster is running")
    print("2. Verify credentials are correct")
    print("3. Check if your IP is whitelisted in Redshift security group")
    print("4. Ensure the database and table exist")