import sqlite3
import sys

def run_quality_checks(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    issues_found = 0
    
    print("🔍 Running Data Quality Checks...")
    
    # Check 1: Negative Tank Levels (IoT Sensor Error)
    cursor.execute("SELECT COUNT(*) FROM Fact_IoT_Telemetry WHERE tank_level_pct < 0 OR tank_level_pct > 100")
    bad_telemetry = cursor.fetchone()[0]
    if bad_telemetry > 0:
        print(f"⚠️ CRITICAL: Found {bad_telemetry} invalid telemetry records (Level < 0 or > 100)")
        issues_found += 1
    else:
        print("✅ IoT Telemetry levels are within valid range [0-100]")

    # Check 2: Orphan Transactions (No matching customer)
    cursor.execute("""
        SELECT COUNT(*) FROM Fact_Transactions t 
        LEFT JOIN Dim_Customer c ON t.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL
    """)
    orphans = cursor.fetchone()[0]
    if orphans > 0:
        print(f"⚠️ WARNING: Found {orphans} transactions with no matching customer ID")
        issues_found += 1
    else:
        print("✅ Referential Integrity: All transactions link to valid customers")

    # Check 3: Future Dates (Data Pipeline Lag)
    cursor.execute("SELECT COUNT(*) FROM Fact_Transactions WHERE transaction_date > datetime('now')")
    future_txns = cursor.fetchone()[0]
    if future_txns > 0:
        print(f"⚠️ WARNING: Found {future_txns} transactions dated in the future")
        issues_found += 1
    else:
        print("✅ Temporal Integrity: No future-dated transactions found")

    conn.close()
    
    if issues_found == 0:
        print("\n🎉 DATA HEALTH CHECK PASSED: Warehouse is ready for analytics.")
    else:
        print(f"\n❌ DATA HEALTH CHECK FAILED: {issues_found} issues require engineering attention.")
        sys.exit(1)

if __name__ == "__main__":
    run_quality_checks('data/mgas_warehouse.db')