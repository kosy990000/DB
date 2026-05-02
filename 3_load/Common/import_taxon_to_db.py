#!/usr/bin/env python3
"""
Import Taxon Data to SQLite Database
=====================================
processed/taxon.csv → database.db

Usage:
    python3 import_taxon_to_db.py
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import DB_FILE, PROJECT_ROOT

# ============================================
# 설정
# ============================================

TAXON_FILE = PROJECT_ROOT / "processed" / "taxon.csv"

# ============================================

print("="*60)
print("Import Taxon Data to Database")
print("="*60)

# DB 연결
print(f"\n[CONNECT] Connecting to database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Foreign keys 활성화
cursor.execute("PRAGMA foreign_keys = OFF;")  # DELETE 시 FK 체크 비활성화

# ============================================
# Clear existing Taxon data
# ============================================
print(f"\n[CLEAR] Clearing existing Taxon data...")

try:
    cursor.execute("DELETE FROM taxon;")
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"  [OK] Cleared taxon: {deleted:,} rows deleted")
except sqlite3.OperationalError:
    # 테이블이 없는 경우 (첫 실행)
    print(f"  [WARN] Table taxon does not exist (will be created)")

conn.commit()
cursor.execute("PRAGMA foreign_keys = ON;")  # FK 체크 재활성화

print(f"\n[INFO] Data source: {TAXON_FILE}")

# ============================================
# Import Taxon data
# ============================================
print(f"\n[IMPORT] Importing Taxon data...")

success = False

if not TAXON_FILE.exists():
    print(f"  [ERROR] File not found: {TAXON_FILE}")
else:
    try:
        # CSV 읽기
        df = pd.read_csv(TAXON_FILE, low_memory=False)
        print(f"     Rows: {len(df):,}")

        # 칼럼명 정리
        df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_').str.lower()

        # DB에 insert
        df.to_sql('taxon', conn, if_exists='append', index=False)
        print(f"     [OK] Imported successfully")
        success = True

    except Exception as e:
        print(f"     [ERROR] {e}")
        conn.rollback()

conn.commit()

# ============================================
# Verify import
# ============================================
print(f"\n[VERIFY] Verifying import...")

try:
    cursor.execute("SELECT COUNT(*) FROM taxon;")
    count = cursor.fetchone()[0]
    print(f"\n[RESULT] taxon table: {count:,} rows")
except sqlite3.Error:
    print(f"\n[RESULT] taxon table: (table not found)")

conn.close()

# ============================================
# Summary
# ============================================
print("\n" + "="*60)
print("Import Summary")
print("="*60)
if success:
    print("[OK] Successfully imported taxon table")
else:
    print("[ERROR] Failed to import taxon table")
print("\n" + "="*60)
print("[DONE] Import completed!")
print("="*60)
print(f"\nDatabase: {DB_FILE}")
