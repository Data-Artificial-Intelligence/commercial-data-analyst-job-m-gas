import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

# --- CONFIGURATION ---
DB_NAME = 'data/mgas_warehouse.db'
NUM_CUSTOMERS = 1000
START_DATE = datetime(2026, 1, 1)

fake = Faker('en_US') # Using US locale but we will customize for Kenya context

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # DIMENSION TABLES
    cursor.execute('''CREATE TABLE IF NOT EXISTS Dim_Customer (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        location TEXT,
        agent_id INTEGER,
        signup_date TEXT,
        segment TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Dim_Agent (
        agent_id INTEGER PRIMARY KEY,
        name TEXT,
        region TEXT,
        commission_rate REAL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Dim_Product (
        product_id INTEGER PRIMARY KEY,
        cylinder_size TEXT,
        tank_capacity_liters REAL
    )''')

    # FACT TABLES
    cursor.execute('''CREATE TABLE IF NOT EXISTS Fact_Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        transaction_date TEXT,
        amount_kes REAL,
        payment_method TEXT,
        status TEXT,
        FOREIGN KEY(customer_id) REFERENCES Dim_Customer(customer_id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Fact_IoT_Telemetry (
        telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        timestamp TEXT,
        tank_level_pct REAL,
        valve_status TEXT,
        FOREIGN KEY(customer_id) REFERENCES Dim_Customer(customer_id)
    )''')

    conn.commit()
    return conn

def generate_mock_data(conn):
    cursor = conn.cursor()
    
    # 1. Generate Agents (The "Last Mile" Network)
    agents = [(i, fake.name(), random.choice(['Nairobi East', 'Nairobi West', 'Kiambu']), 0.05) for i in range(1, 21)]
    cursor.executemany("INSERT INTO Dim_Agent VALUES (?, ?, ?, ?)", agents)
    
    # 2. Generate Customers (The "Leaky Bucket")
    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        agent_id = random.randint(1, 20)
        # Simulate segments: High Value, At Risk, Churned
        segment = random.choices(['High Value', 'At Risk', 'Churned'], weights=[60, 25, 15])[0]
        signup = START_DATE + timedelta(days=random.randint(0, 200))
        customers.append((i, fake.name(), f"+2547{random.randint(10000000,99999999)}", 
                          random.choice(['Kibera', 'Mathare', 'Kawangware', 'Ruai']), 
                          agent_id, signup.strftime('%Y-%m-%d'), segment))
    cursor.executemany("INSERT INTO Dim_Customer VALUES (?, ?, ?, ?, ?, ?, ?)", customers)
    
    # 3. Generate Products
    products = [(1, '6kg Smart Cylinder', 6.0), (2, '13kg Smart Cylinder', 13.0)]
    cursor.executemany("INSERT INTO Dim_Product VALUES (?, ?, ?)", products)

    # 4. Generate Transactions (M-Pesa Simulation)
    transactions = []
    for _ in range(NUM_CUSTOMERS * 15): # Avg 15 txns per customer
        cust_id = random.randint(1, NUM_CUSTOMERS)
        date = START_DATE + timedelta(days=random.randint(0, 240))
        amount = random.choice([500, 1000, 1500, 2000])
        status = random.choices(['Success', 'Failed', 'Pending'], weights=[90, 8, 2])[0]
        transactions.append((cust_id, date.strftime('%Y-%m-%d %H:%M:%S'), amount, 'M-Pesa', status))
    cursor.executemany("INSERT INTO Fact_Transactions (customer_id, transaction_date, amount_kes, payment_method, status) VALUES (?, ?, ?, ?, ?)", transactions)

    # 5. Generate IoT Telemetry (Tank Levels)
    telemetry = []
    for _ in range(NUM_CUSTOMERS * 30): # Daily readings
        cust_id = random.randint(1, NUM_CUSTOMERS)
        ts = START_DATE + timedelta(days=random.randint(0, 240), hours=random.randint(0,23))
        level = round(random.uniform(0, 100), 2)
        valve = 'Open' if level > 5 else 'Closed'
        telemetry.append((cust_id, ts.strftime('%Y-%m-%d %H:%M:%S'), level, valve))
    cursor.executemany("INSERT INTO Fact_IoT_Telemetry (customer_id, timestamp, tank_level_pct, valve_status) VALUES (?, ?, ?, ?)", telemetry)

    conn.commit()
    print(f"✅ Successfully ingested {NUM_CUSTOMERS} customers and related telemetry/transactions.")

if __name__ == "__main__":
    print("🚀 Starting Project BlueFlame Data Ingestion...")
    conn = create_database()
    generate_mock_data(conn)
    conn.close()
    print("💾 Data Warehouse ready at data/mgas_warehouse.db")