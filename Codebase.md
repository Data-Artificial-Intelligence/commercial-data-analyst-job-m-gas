# TIMSAdvantaged Codebase

Generated: 11/02/2026 14:45:06

---

## Table of Contents

- .gitignore
- Generate-Codebook-TIMSAdvantaged.ps1
- README.md
- requirements.txt
- src\commercial_metrics.sql
- src\data_quality_check.py
- src\generate_data.py

---


<div style='page-break-after: always;'></div>

# File: .gitignore

```gitignore
venv/
__pycache__/
*.db
.env
```


<div style='page-break-after: always;'></div>

# File: Generate-Codebook-TIMSAdvantaged.ps1

```ps1
<#
.EXAMPLE
.\Generate-Codebook-TIMSAdvantaged.ps1 -ProjectPath "C:\Data\commercial-data-analyst-job-m-gas"
#>

param(
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$GeneratePdf
)

# ============================================================
# Configuration
# ============================================================

$Root = (Resolve-Path $ProjectPath).Path

$MarkdownFile = Join-Path $Root "Codebase.md"
$PdfFile      = Join-Path $Root "Codebase.pdf"

# 1. Directories to completely ignore (Added TIMS specific folders)
$ExcludedDirectories = @(
    ".git", ".github", ".idea", ".vscode", ".cursor",
    "node_modules", "venv", ".venv", "env", "Lib", "Include", "site-packages",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov",
    "coverage", "dist", "build", "bin", "obj", "out", ".next",
    "migrations", "trash", "staticfiles", "media",
    ".cache", ".data", ".logs", ".reports" 
)

# 2. File extensions to ignore (Added Excel, Certs, CSVs)
$ExcludedExtensions = @(
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".svg",".webp",".avif",
    ".pdf",".zip",".7z",".rar",".tar",".gz",
    ".exe",".dll",".so",".dylib",".pyd",
    ".woff",".woff2",".ttf",".eot",
    ".pyc",".pyo",".class",
    ".db",".sqlite3",".sqlite",".log",
    ".map", ".mo", ".lock", ".pth", ".bak", ".tmp",
    ".xlsx", ".xls", ".csv", ".pem", ".crt", ".key", ".tpl", ".mp4", ".pbix"
)

# 3. Specific files to ignore (CRITICAL: Added .secrets.toml for security)
$ExcludedFiles = @(
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Pipfile.lock",
    "poetry.lock",
    "db.sqlite3",
    ".secrets.toml", 
    "Codebase.md",
    "Codebase.pdf"
)

# Delete old markdown if it exists
if (Test-Path $MarkdownFile) {
    Remove-Item $MarkdownFile -Force
}

# ============================================================
# Helper Function
# ============================================================

function Add-Line {
    param([string]$Text)
    Add-Content -Path $MarkdownFile -Value $Text -Encoding UTF8
}

# ============================================================
# Scan Files
# ============================================================

Write-Host ""
Write-Host "Scanning TIMSAdvantaged repository..."
Write-Host ""

$Files = Get-ChildItem -Path $Root -Recurse -File | Where-Object {
    $relative = $_.FullName.Substring($Root.Length).TrimStart('\', '/')
    $fileName = $_.Name

    # Check Directories (Windows and Linux/Mac path separators)
    $pathParts = $relative -split '[\\/]'
    foreach ($dir in $ExcludedDirectories) {
        if ($pathParts -contains $dir) {
            return $false
        }
    }

    # Check Extensions
    if ($ExcludedExtensions -contains $_.Extension.ToLower()) {
        return $false
    }

    # Check Exact Filenames
    if ($ExcludedFiles -contains $fileName) {
        return $false
    }

    return $true

} | Sort-Object FullName

Write-Host "Found $($Files.Count) valid source code files."
Write-Host ""

# ============================================================
# Markdown Header
# ============================================================

Add-Line "# TIMSAdvantaged Codebase"
Add-Line ""
Add-Line "Generated: $(Get-Date)"
Add-Line ""
Add-Line "---"
Add-Line ""

# ============================================================
# Table of Contents
# ============================================================

Add-Line "## Table of Contents"
Add-Line ""

foreach ($file in $Files) {
    $relative = $file.FullName.Substring($Root.Length).TrimStart('\', '/')
    Add-Line "- $relative"
}

Add-Line ""
Add-Line "---"
Add-Line ""

# ============================================================
# Add Every File
# ============================================================

$index = 1

foreach ($file in $Files) {
    $relative = $file.FullName.Substring($Root.Length).TrimStart('\', '/')

    Write-Host "[$index/$($Files.Count)] $relative"

    $language = $file.Extension.TrimStart('.')
    if ([string]::IsNullOrWhiteSpace($language)) { $language = "text" }
    
    # Map specific extensions to markdown code block languages
    switch ($language) {
        "py" { $language = "python" }
        "js" { $language = "javascript" }
        "ts" { $language = "typescript" }
        "tsx" { $language = "tsx" }
        "jsx" { $language = "jsx" }
        "yml" { $language = "yaml" }
        "sh" { $language = "bash" }
        "toml" { $language = "toml" }
    }

    Add-Line ""
    Add-Line "<div style='page-break-after: always;'></div>"
    Add-Line ""
    Add-Line "# File: $relative"
    Add-Line ""
    Add-Line ('```' + $language)

    try {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        Add-Content -Path $MarkdownFile -Value $content -Encoding UTF8
    }
    catch {
        Add-Line "[Unable to read file.]"
    }

    Add-Line '```'
    Add-Line ""
    $index++
}

Write-Host ""
Write-Host "Markdown created successfully!"
Write-Host $MarkdownFile



# ============================================================
# Optional PDF Generation
# ============================================================

if ($GeneratePdf) {

    $Pandoc = Get-Command pandoc -ErrorAction SilentlyContinue

    if ($Pandoc) {

        Write-Host ""
        Write-Host "Generating PDF..."

        & pandoc `
            $MarkdownFile `
            -o $PdfFile `
            --toc `
            --highlight-style=tango

        Write-Host ""
        Write-Host "PDF created:"
        Write-Host $PdfFile

    }
    else {

        Write-Host ""
        Write-Host "Pandoc was not found."
        Write-Host ""
        Write-Host "Install it from:"
        Write-Host "https://pandoc.org/installing.html"

    }

}
```


<div style='page-break-after: always;'></div>

# File: README.md

```md


```


<div style='page-break-after: always;'></div>

# File: requirements.txt

```txt
Faker==40.44.0
numpy==2.5.4
pandas==3.1.0
python-dateutil==4.0.0
tzdata==2026.6

```


<div style='page-break-after: always;'></div>

# File: src\commercial_metrics.sql

```sql
-- COMMERCIAL METRICS ENGINE
-- Calculates KPIs directly in the DB to optimize BI performance

-- 1. Customer Retention & Churn Analysis
WITH customer_activity AS (
    SELECT 
        c.customer_id,
        c.segment,
        c.signup_date,
        MAX(t.transaction_date) as last_txn_date,
        COUNT(t.transaction_id) as total_txns,
        SUM(t.amount_kes) as total_revenue
    FROM Dim_Customer c
    LEFT JOIN Fact_Transactions t ON c.customer_id = t.customer_id AND t.status = 'Success'
    GROUP BY c.customer_id
),
churn_flags AS (
    SELECT 
        *,
        CASE 
            WHEN julianday('now') - julianday(last_txn_date) > 30 THEN 'Churned'
            ELSE 'Active'
        END as current_status,
        -- Payment Velocity: Avg days between refills
        (julianday('now') - julianday(signup_date)) / NULLIF(total_txns, 0) as avg_days_between_refills
    FROM customer_activity
)

SELECT 
    segment,
    current_status,
    COUNT(*) as customer_count,
    ROUND(AVG(total_revenue), 2) as avg_ltv,
    ROUND(AVG(avg_days_between_refills), 1) as avg_refill_cycle_days
FROM churn_flags
GROUP BY segment, current_status;

-- 2. Agent Performance Quality Check (Fraud Detection)
SELECT 
    a.agent_id,
    a.name,
    COUNT(DISTINCT c.customer_id) as activations,
    SUM(CASE WHEN cf.current_status = 'Churned' THEN 1 ELSE 0 END) as early_churners,
    ROUND(100.0 * SUM(CASE WHEN cf.current_status = 'Churned' THEN 1 ELSE 0 END) / COUNT(DISTINCT c.customer_id), 2) as churn_rate_pct
FROM Dim_Agent a
JOIN Dim_Customer c ON a.agent_id = c.agent_id
JOIN (
    SELECT customer_id, 
           CASE WHEN julianday('now') - julianday(MAX(transaction_date)) > 30 THEN 'Churned' ELSE 'Active' END as current_status
    FROM Fact_Transactions 
    WHERE status = 'Success'
    GROUP BY customer_id
) cf ON c.customer_id = cf.customer_id
GROUP BY a.agent_id
HAVING churn_rate_pct > 20; -- Flag agents with >20% churn
```


<div style='page-break-after: always;'></div>

# File: src\data_quality_check.py

```python
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
```


<div style='page-break-after: always;'></div>

# File: src\generate_data.py

```python
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
```

