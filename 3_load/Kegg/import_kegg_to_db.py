#!/usr/bin/env python3
"""
Import KEGG Normalized Data to SQLite Database
===============================================
processed/kegg/normalized/*.csv → database.db


Usage:
    python3 import_kegg_to_db.py
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import DB_FILE, PROC_KEGG

# ============================================
# 설정
# ============================================

NORMALIZED_DIR = PROC_KEGG / "normalized"
EDGES_DIR      = PROC_KEGG / "pathway_edges"
PATHWAY_FILE   = PROC_KEGG / "pathway_list.csv"

# ============================================

print("="*60)
print("Import KEGG Data to Database")
print("="*60)

# DB 연결
print(f"\n[CONNECT] Connecting to database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Foreign keys 활성화
cursor.execute("PRAGMA foreign_keys = OFF;")  # DELETE 시 FK 체크 비활성화

# Import 순서 (FK 제약조건 고려)
IMPORT_ORDER = [
    # 1. 부모 테이블 (FK 없음)
    ('kegg_genes.csv', 'kegg_genes'),
    ('kegg_compounds.csv', 'kegg_compounds'),
    ('kegg_nodes.csv', 'kegg_nodes'),

    # 2. 자식 테이블 (FK 참조)
    ('kegg_gene_synonyms.csv', 'kegg_gene_synonyms'),
    ('kegg_compound_synonyms.csv', 'kegg_compound_synonyms'),
    ('kegg_gene_group_members.csv', 'kegg_gene_group_members'),
]

# Pathway import (별도 처리)
PATHWAY_IMPORT = ('pathway_list.csv', 'kegg_pathway')

# ============================================
# Clear existing KEGG data (except kegg_pathway)
# ============================================
print(f"\n[CLEAR] Clearing existing KEGG data...")

TABLES_TO_CLEAR = [
    'kegg_edges',
    'kegg_gene_group_members',
    'kegg_compound_synonyms',
    'kegg_gene_synonyms',
    'kegg_nodes',
    'kegg_compounds',
    'kegg_genes',
    'kegg_pathway',
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

print(f"\n[INFO] Data source: {NORMALIZED_DIR}")
print(f"[INFO] Tables to import: {len(IMPORT_ORDER) + 1}")

# ============================================
# Import pathway data (먼저 import - FK 참조 때문)
# ============================================
print(f"\n[IMPORT] Step 0: Importing pathway data...")

if PATHWAY_FILE.exists():
    print(f"\n  [IMPORT] {PATHWAY_FILE.name} -> kegg_pathway")
    try:
        df = pd.read_csv(PATHWAY_FILE)
        print(f"     Rows: {len(df):,}")
        df.to_sql('kegg_pathway', conn, if_exists='append', index=False)
        print(f"     [OK] Imported successfully")
        conn.commit()
    except Exception as e:
        print(f"     [ERROR] {e}")
        conn.rollback()
else:
    print(f"  [WARN] Pathway file not found: {PATHWAY_FILE}")

# ============================================
# Import normalized data
# ============================================
print(f"\n[IMPORT] Step 1: Importing normalized data...")

for csv_file, table_name in IMPORT_ORDER:
    csv_path = NORMALIZED_DIR / csv_file

    if not csv_path.exists():
        print(f"  [WARN] File not found: {csv_file} (skipped)")
        continue

    print(f"\n  [IMPORT] {csv_file} -> {table_name}")

    try:
        # CSV 읽기
        df = pd.read_csv(csv_path)
        print(f"     Rows: {len(df):,}")

        # DB에 insert
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"     [OK] Imported successfully")

    except Exception as e:
        print(f"     [ERROR] {e}")
        conn.rollback()

conn.commit()


# ============================================
# Import pathway edges
# ============================================
print(f"\n[IMPORT] Step 2: Importing pathway edges...")
print(f"[INFO] Data source: {EDGES_DIR}")

if EDGES_DIR.exists():
    edge_files = list(EDGES_DIR.glob("*.csv"))
    print(f"[INFO] Edge files found: {len(edge_files)}")

    edge_count = 0

    for edge_file in tqdm(edge_files, desc="  Importing edges"):
        try:
            df = pd.read_csv(edge_file)

            # BOM 제거 (﻿source → source)
            df.columns = df.columns.str.replace('﻿', '')

            # 컬럼명 변경: CSV의 source/target을 DB의 source_id/target_id로 매핑
            column_mapping = {
                'source': 'source_id',
                'target': 'target_id'
            }
            df = df.rename(columns=column_mapping)

            # pathway_id가 없으면 파일명에서 추출
            if 'pathway_id' not in df.columns:
                pathway_id = 'path:' + edge_file.stem
                df['pathway_id'] = pathway_id

            # DB 스키마에 맞는 컬럼만 선택
            required_cols = ['source_id', 'source_type', 'target_id', 'target_type',
                           'relation_type', 'relation_subtype', 'pathway_id']
            df_filtered = df[required_cols]

            # DB에 insert
            df_filtered.to_sql('kegg_edges', conn, if_exists='append', index=False)
            edge_count += len(df_filtered)

        except Exception as e:
            print(f"\n     [ERROR] Error in {edge_file.name}: {e}")

    conn.commit()
    print(f"\n  [OK] Total edges imported: {edge_count:,}")
else:
    print(f"  [WARN] Edge directory not found: {EDGES_DIR}")


# ============================================
# Verify import
# ============================================
print(f"\n[VERIFY] Verifying import...")

KEGG_TABLES = [
    'kegg_pathway',
    'kegg_genes',
    'kegg_compounds',
    'kegg_gene_synonyms',
    'kegg_compound_synonyms',
    'kegg_nodes',
    'kegg_edges',
    'kegg_gene_group_members',
]

print(f"\n[RESULT] KEGG tables in database:")
for table in KEGG_TABLES:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  - {table:35s} : {count:,} rows")
    except sqlite3.Error:
        print(f"  - {table:35s} : (table not found)")

# Foreign keys 재활성화
cursor.execute("PRAGMA foreign_keys = ON;")
conn.close()

print("\n" + "="*60)
print("[DONE] Import completed!")
print("="*60)
print(f"\nDatabase: {DB_FILE}")
