import mysql.connector
import pandas as pd
import numpy as np

# Database connection configuration
config = {
    'user': 'root',
    'password': 'Lynx_123@',
    'host': 'localhost',
    'database': 'library',
    'raise_on_warnings': True
}

# CSV file path
#csv_file_path = 'C:/Users/sivab/AppData/Local/Programs/Python/Python311/books_with_status.csv'
csv_file_path = 'books_with_descriptions.csv'
# Create a database connection
conn = mysql.connector.connect(**config)
cursor = conn.cursor()
"""cursor.execute(""
CREATE TABLE lib (
    barcode INT PRIMARY KEY,
    location VARCHAR(50),
    author VARCHAR(100),
    title VARCHAR(200),
    publisher_code VARCHAR(100),
    status VARCHAR(50),
    description TEXT
)
"")"""
# Read CSV file into a pandas DataFrame
df = pd.read_csv(csv_file_path)

# Replace NaN values with None (to insert as NULL in SQL)
df = df.where(pd.notnull(df), None)

# Assuming your SQL table has the same column names as the CSV
table_name = 'lib'
columns = ', '.join(df.columns)
placeholders = ', '.join(['%s'] * len(df.columns))

# SQL INSERT query
insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'

# Insert data into the SQL table
for row in df.itertuples(index=False, name=None):
    cursor.execute(insert_query, row)

# Commit the transaction
conn.commit()

# Close the connection
cursor.close()
conn.close()

print("Data imported successfully!")
