"""
M-Gas Commercial Analytics Mock-Data Generator
Scenario anchor: 2026-08-06

Generates:
- 1,000 customers
- 20 agents
- 2 LPG products
- 15 transactions per customer:
    1 guaranteed successful signup-month transaction
    14 additional transactions
- 30 IoT telemetry readings per customer

All transaction dates are between signup and the scenario anchor.
"""

from pathlib import Path
import random
import sqlite3
from datetime import datetime, timedelta

from faker import Faker


# ============================================================
# 1. CONFIGURATION
# ============================================================

DB_NAME = Path("data/mgas_warehouse.db")

NUM_CUSTOMERS = 1000
NUM_AGENTS = 20

START_DATE = datetime(2026, 1, 1)
SCENARIO_ANCHOR = datetime(2026, 8, 6, 23, 59, 59)

RANDOM_TXNS_PER_CUSTOMER = 14
TELEMETRY_READINGS_PER_CUSTOMER = 30

RANDOM_SEED = 42

# Synthetic average activity-decay assumptions in days.
SEGMENT_ACTIVITY_SCALE_DAYS = {
    "High Value": 45,
    "At Risk": 28,
    "Churned": 14
}

fake = Faker("en_KE")


# ============================================================
# 2. DATABASE CREATION
# ============================================================

def create_database():

    DB_NAME.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dim_Customer (
            customer_id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            location TEXT,
            agent_id INTEGER,
            signup_date TEXT,
            segment TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dim_Agent (
            agent_id INTEGER PRIMARY KEY,
            name TEXT,
            region TEXT,
            commission_rate REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dim_Product (
            product_id INTEGER PRIMARY KEY,
            cylinder_size TEXT,
            tank_capacity_liters REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Fact_Transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            transaction_date TEXT,
            amount_kes REAL,
            payment_method TEXT,
            status TEXT,
            FOREIGN KEY(customer_id)
                REFERENCES Dim_Customer(customer_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Fact_IoT_Telemetry (
            telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            timestamp TEXT,
            tank_level_pct REAL,
            valve_status TEXT,
            FOREIGN KEY(customer_id)
                REFERENCES Dim_Customer(customer_id)
        )
    """)

    conn.commit()

    return conn


# ============================================================
# 3. DATE HELPERS
# ============================================================

def random_timestamp(start, end):

    if end < start:
        raise ValueError("End date cannot be before start date.")

    seconds = int((end - start).total_seconds())

    return start + timedelta(
        seconds=random.randint(0, seconds)
    )


def get_signup_month_end(signup):

    next_month_start = (
        signup.replace(day=28) + timedelta(days=4)
    ).replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    return next_month_start - timedelta(seconds=1)


# ============================================================
# 4. GENERATE MOCK DATA
# ============================================================

def generate_mock_data(conn):

    random.seed(RANDOM_SEED)
    Faker.seed(RANDOM_SEED)

    cursor = conn.cursor()

    # --------------------------------------------------------
    # CLEAR OLD DATA
    # --------------------------------------------------------

    cursor.execute("DELETE FROM Fact_Transactions")
    cursor.execute("DELETE FROM Fact_IoT_Telemetry")
    cursor.execute("DELETE FROM Dim_Customer")
    cursor.execute("DELETE FROM Dim_Agent")
    cursor.execute("DELETE FROM Dim_Product")

    cursor.execute("""
        DELETE FROM sqlite_sequence
        WHERE name IN (
            'Fact_Transactions',
            'Fact_IoT_Telemetry'
        )
    """)

    # --------------------------------------------------------
    # A. GENERATE AGENTS
    # --------------------------------------------------------

    agents = [
        (
            i,
            fake.name(),
            random.choice([
                "Nairobi East",
                "Nairobi West",
                "Kiambu"
            ]),
            0.05
        )
        for i in range(1, NUM_AGENTS + 1)
    ]

    cursor.executemany(
        "INSERT INTO Dim_Agent VALUES (?, ?, ?, ?)",
        agents
    )

    # --------------------------------------------------------
    # B. GENERATE CUSTOMERS
    # --------------------------------------------------------

    customers = []

    customer_signup_dates = {}
    customer_segments = {}

    for customer_id in range(1, NUM_CUSTOMERS + 1):

        agent_id = random.randint(1, NUM_AGENTS)

        segment = random.choices(
            ["High Value", "At Risk", "Churned"],
            weights=[60, 25, 15]
        )[0]

        signup = START_DATE + timedelta(
            days=random.randint(0, 200)
        )

        customer_signup_dates[customer_id] = signup
        customer_segments[customer_id] = segment

        customers.append((
            customer_id,
            fake.name(),
            f"+2547{random.randint(10000000, 99999999)}",
            random.choice([
                "Kibera",
                "Mathare",
                "Kawangware",
                "Ruai"
            ]),
            agent_id,
            signup.strftime("%Y-%m-%d"),
            segment
        ))

    cursor.executemany("""
        INSERT INTO Dim_Customer
        (customer_id, name, phone, location,
         agent_id, signup_date, segment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, customers)

    # --------------------------------------------------------
    # C. GENERATE PRODUCTS
    # --------------------------------------------------------

    products = [
        (1, "6kg Smart Cylinder", 6.0),
        (2, "13kg Smart Cylinder", 13.0)
    ]

    cursor.executemany(
        "INSERT INTO Dim_Product VALUES (?, ?, ?)",
        products
    )

    # --------------------------------------------------------
    # D. GENERATE TRANSACTIONS
    # --------------------------------------------------------

    transactions = []

    for customer_id, signup in customer_signup_dates.items():

        # ================================================
        # TRANSACTION 1: GUARANTEED SUCCESSFUL M0
        # ================================================

        signup_month_end = get_signup_month_end(signup)

        guaranteed_end = min(
            signup + timedelta(days=3),
            signup_month_end,
            SCENARIO_ANCHOR
        )

        guaranteed_date = random_timestamp(
            signup,
            guaranteed_end
        )

        transactions.append((
            customer_id,
            guaranteed_date.strftime("%Y-%m-%d %H:%M:%S"),
            random.choice([500, 1000, 1500, 2000]),
            "M-Pesa",
            "Success"
        ))

        # ================================================
        # TRANSACTIONS 2-N: REALISTIC VARIABLE ACTIVITY
        # ================================================

        scale_days = SEGMENT_ACTIVITY_SCALE_DAYS[
            customer_segments[customer_id]
        ]

        max_days = (
            SCENARIO_ANCHOR.date() - signup.date()
        ).days

        # CRITICAL FIX: Not all customers make 14 more transactions.
        # Simulate realistic churn: some stop after 1 purchase, some become loyal.
        # We use a weighted random choice to determine how many MORE transactions they make.
        additional_txn_counts = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 14]
        additional_txn_weights = [15, 15, 15, 10, 10, 10, 8, 7, 5, 3, 2] # 15% churn immediately after signup!

        num_additional_txns = random.choices(
            additional_txn_counts,
            weights=additional_txn_weights,
            k=1
        )[0]

        for _ in range(num_additional_txns):

            # Exponential distribution:
            # More activity near signup, progressively less later.

            offset_days = int(
                random.expovariate(1.0 / scale_days)
            )

            offset_days = min(
                offset_days,
                max_days
            )

            transaction_day = signup + timedelta(
                days=offset_days
            )

            day_start = transaction_day.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

            day_end = min(
                day_start + timedelta(days=1)
                - timedelta(seconds=1),
                SCENARIO_ANCHOR
            )

            transaction_date = random_timestamp(
                day_start,
                day_end
            )

            status = random.choices(
                ["Success", "Failed", "Pending"],
                weights=[90, 8, 2]
            )[0]

            transactions.append((
                customer_id,
                transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
                random.choice([500, 1000, 1500, 2000]),
                "M-Pesa",
                status
            ))

    cursor.executemany("""
        INSERT INTO Fact_Transactions
        (customer_id, transaction_date, amount_kes,
         payment_method, status)
        VALUES (?, ?, ?, ?, ?)
    """, transactions)

    # --------------------------------------------------------
    # E. GENERATE IOT TELEMETRY
    # --------------------------------------------------------

    telemetry = []

    for customer_id, signup in customer_signup_dates.items():

        for _ in range(TELEMETRY_READINGS_PER_CUSTOMER):

            timestamp = random_timestamp(
                signup,
                SCENARIO_ANCHOR
            )

            level = round(
                random.uniform(0, 100),
                2
            )

            valve = "Open" if level > 5 else "Closed"

            telemetry.append((
                customer_id,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                level,
                valve
            ))

    cursor.executemany("""
        INSERT INTO Fact_IoT_Telemetry
        (customer_id, timestamp, tank_level_pct, valve_status)
        VALUES (?, ?, ?, ?)
    """, telemetry)

    conn.commit()

    # --------------------------------------------------------
    # F. DATA QUALITY VALIDATION
    # --------------------------------------------------------

    total_customers = cursor.execute(
        "SELECT COUNT(*) FROM Dim_Customer"
    ).fetchone()[0]

    total_transactions = cursor.execute(
        "SELECT COUNT(*) FROM Fact_Transactions"
    ).fetchone()[0]

    m0_customers = cursor.execute("""
        SELECT COUNT(DISTINCT c.customer_id)
        FROM Dim_Customer c
        INNER JOIN Fact_Transactions t
            ON c.customer_id = t.customer_id
        WHERE LOWER(TRIM(t.status)) = 'success'
          AND SUBSTR(c.signup_date, 1, 7)
              = SUBSTR(t.transaction_date, 1, 7)
    """).fetchone()[0]

    print("\n========== DATA GENERATION SUMMARY ==========")
    print(f"Customers generated: {total_customers:,}")
    print(f"Transaction records: {total_transactions:,}")
    print(f"Average transactions/customer: {total_transactions / total_customers:.1f}")
    print(f"Successful M0 customers: {m0_customers:,}/{total_customers:,}")
    print(f"M0 coverage: {m0_customers / total_customers * 100:.1f}%")
    print(f"Scenario anchor: {SCENARIO_ANCHOR:%Y-%m-%d}")
    print("=============================================\n")

    # CRITICAL FIX: We no longer expect a fixed number (15,000)
    # because we simulate realistic churn with variable activity.
    # We just check that we have at least the guaranteed M0 transactions.
    if total_transactions < NUM_CUSTOMERS:
        raise ValueError(
            "Transaction count validation failed. "
            "Expected at least 1 transaction per customer."
        )

    if m0_customers != total_customers:
        raise ValueError(
            "M0 validation failed. "
            "Some customers lack successful signup-month activity."
        )

# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "Starting M-Gas commercial analytics data generation..."
    )

    conn = create_database()

    try:
        generate_mock_data(conn)
    finally:
        conn.close()

    print(f"Warehouse ready: {DB_NAME}")