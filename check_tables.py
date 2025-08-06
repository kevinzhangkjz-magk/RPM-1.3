#!/usr/bin/env python3
"""Check available tables in Redshift"""

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
    'sslmode': 'require'
}

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # Get all schemas
    cursor.execute("""
        SELECT DISTINCT schemaname 
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname
    """)
    schemas = cursor.fetchall()
    print(f"Available schemas: {[s[0] for s in schemas]}")
    
    # Get all tables
    cursor.execute("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename
        LIMIT 50
    """)
    
    tables = cursor.fetchall()
    print(f"\n📊 Found {len(tables)} tables:\n")
    
    current_schema = None
    for schema, table in tables:
        if schema != current_schema:
            current_schema = schema
            print(f"\n{schema}:")
        print(f"  - {table}")
    
    # Look for tables with 'site' in the name
    cursor.execute("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename ILIKE '%site%'
        AND schemaname NOT IN ('pg_catalog', 'information_schema')
    """)
    
    site_tables = cursor.fetchall()
    if site_tables:
        print(f"\n🔍 Tables containing 'site':")
        for schema, table in site_tables:
            print(f"  - {schema}.{table}")
    
    # Look for tables with 'solar' in the name
    cursor.execute("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename ILIKE '%solar%'
        AND schemaname NOT IN ('pg_catalog', 'information_schema')
    """)
    
    solar_tables = cursor.fetchall()
    if solar_tables:
        print(f"\n☀️ Tables containing 'solar':")
        for schema, table in solar_tables:
            print(f"  - {schema}.{table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")