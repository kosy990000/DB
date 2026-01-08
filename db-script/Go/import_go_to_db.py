#!/usr/bin/env python3
"""
Import Gene Ontology (GO) Data to SQLite Database
==================================================
processed/Go/*.csv → database.db

Tables:
  - go_terms          : GO term information (BP, CC, MF)
  - go_hierarchy      : GO term hierarchy (parent-child)
  - go_genes          : GO-Gene mapping

Usage:
    python3 import_go_to_db.py
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ============================================
# 설정: 여기만 수정하세요
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 데이터 경로
GO_DIR = BASE_DIR / "processed" / "Go"

# DB 파일 경로
DB_FILE = BASE_DIR / "database" / "database.db"

# ============================================

print("="*60)
print("Import Gene Ontology (GO) Data to Database")
print("="*60)

# DB 연결
print(f"\n[CONNECT] Connecting to database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Foreign keys 활성화
cursor.execute("PRAGMA foreign_keys = OFF;")  # DELETE 시 FK 체크 비활성화

# ============================================
# Clear existing GO data
# ============================================
print(f"\n[CLEAR] Clearing existing GO data...")

TABLES_TO_CLEAR = [
    'go_genes',
    'go_hierarchy',
    'go_terms',
]

for table in TABLES_TO_CLEAR:
    try:
        cursor.execute(f"DELETE FROM {table};")
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"  [OK] Cleared {table}: {deleted:,} rows deleted")
    except sqlite3.OperationalError:
        # 테이블이 없는 경우 (첫 실행)
        print(f"  [WARN] Table {table} does not exist (will be created)")

conn.commit()
cursor.execute("PRAGMA foreign_keys = ON;")  # FK 체크 재활성화

print(f"\n[INFO] Data source: {GO_DIR}")

# ============================================
# 1. Import GO Terms (BP, CC, MF)
# ============================================
print(f"\n[IMPORT] Step 1/3: Importing GO terms...")

go_terms_list = []

for aspect, aspect_name in [('BP', 'Biological Process'),
                             ('CC', 'Cellular Component'),
                             ('MF', 'Molecular Function')]:
    csv_path = GO_DIR / aspect / f"{aspect}_nodes.csv"

    if not csv_path.exists():
        print(f"  [WARN] File not found: {csv_path} (skipped)")
        continue

    print(f"  [LOAD] {aspect}_nodes.csv ({aspect_name})")
    df = pd.read_csv(csv_path)
    df['aspect'] = aspect
    go_terms_list.append(df)
    print(f"     Rows: {len(df):,}")

if go_terms_list:
    go_terms = pd.concat(go_terms_list, ignore_index=True)
    print(f"\n  [INSERT] Inserting {len(go_terms):,} GO terms...")
    go_terms.to_sql('go_terms', conn, if_exists='append', index=False)
    print(f"  [OK] GO terms imported successfully")
else:
    print(f"  [ERROR] No GO terms found")

# ============================================
# 2. Import GO Hierarchy (BP, CC, MF)
# ============================================
print(f"\n[IMPORT] Step 2/3: Importing GO hierarchy...")

go_hierarchy_list = []

for aspect in ['BP', 'CC', 'MF']:
    csv_path = GO_DIR / aspect / f"{aspect}_edges.csv"

    if not csv_path.exists():
        print(f"  [WARN] File not found: {csv_path} (skipped)")
        continue

    print(f"  [LOAD] {aspect}_edges.csv")
    df = pd.read_csv(csv_path)
    go_hierarchy_list.append(df)
    print(f"     Rows: {len(df):,}")

if go_hierarchy_list:
    go_hierarchy = pd.concat(go_hierarchy_list, ignore_index=True)
    print(f"\n  [INSERT] Inserting {len(go_hierarchy):,} GO hierarchy relationships...")
    go_hierarchy.to_sql('go_hierarchy', conn, if_exists='append', index=False)
    print(f"  [OK] GO hierarchy imported successfully")
else:
    print(f"  [ERROR] No GO hierarchy found")

# ============================================
# 3. Import GO-Gene Mapping (Human + Mouse)
# ============================================
print(f"\n[IMPORT] Step 3/3: Importing GO-Gene mapping...")

go_genes_list = []

for species, tax_id in [('human', 9606), ('mouse', 10090)]:
    csv_path = GO_DIR / f"goa_{species}.csv"

    if not csv_path.exists():
        print(f"  [WARN] File not found: {csv_path} (skipped)")
        continue

    print(f"  [LOAD] goa_{species}.csv (tax_id={tax_id})")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"     Total annotations: {len(df):,}")

    # 필요한 컬럼만 선택 & 중복 제거
    df_unique = df[['go_id', 'db_object_symbol', 'db_object_id', 'aspect', 'tax_id']].drop_duplicates()
    df_unique.columns = ['go_id', 'gene_symbol', 'db_object_id', 'aspect', 'tax_id']

    go_genes_list.append(df_unique)
    print(f"     Unique GO-Gene pairs: {len(df_unique):,}")

if go_genes_list:
    go_genes = pd.concat(go_genes_list, ignore_index=True)
    print(f"\n  [INSERT] Inserting {len(go_genes):,} GO-Gene mappings...")
    go_genes.to_sql('go_genes', conn, if_exists='append', index=False)
    print(f"  [OK] GO-Gene mapping imported successfully")
else:
    print(f"  [ERROR] No GO-Gene mapping found")

conn.commit()

# ============================================
# Verify import
# ============================================
print(f"\n[VERIFY] Verifying import...")

GO_TABLES = [
    'go_terms',
    'go_hierarchy',
    'go_genes',
]

print(f"\n[RESULT] GO tables in database:")
for table in GO_TABLES:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  - {table:40s} : {count:,} rows")
    except sqlite3.Error:
        print(f"  - {table:40s} : (table not found)")

# 추가 통계
print(f"\n[STATS] GO data statistics:")
try:
    cursor.execute("SELECT aspect, COUNT(*) FROM go_terms GROUP BY aspect;")
    for aspect, count in cursor.fetchall():
        print(f"  - GO terms ({aspect}): {count:,}")

    cursor.execute("SELECT tax_id, COUNT(DISTINCT gene_symbol) FROM go_genes GROUP BY tax_id;")
    for tax_id, count in cursor.fetchall():
        species = "Human" if tax_id == 9606 else "Mouse" if tax_id == 10090 else f"Unknown({tax_id})"
        print(f"  - Unique genes ({species}): {count:,}")
except sqlite3.Error as e:
    print(f"  [WARN] Could not get statistics: {e}")

conn.close()

# ============================================
# Summary
# ============================================
print("\n" + "="*60)
print("Import Summary")
print("="*60)
print(f"[OK] GO data imported successfully")
print(f"  - go_terms: GO term definitions")
print(f"  - go_hierarchy: parent-child relationships")
print(f"  - go_genes: GO-gene mappings")
print("\n" + "="*60)
print("[DONE] Import completed!")
print("="*60)
print(f"\nDatabase: {DB_FILE}")
