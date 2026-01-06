#!/usr/bin/env python3
"""
누락된 ChEMBL 테이블 데이터 import 스크립트
- chembl_drug_target_relations
- chembl_target_synonyms
"""

import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import sys


def sanitize_column_name(col_name, table_name=None):
    """칼럼명을 SQL 표준에 맞게 변환"""
    default_name = col_name.replace(' ', '_').replace('-', '_').lower()

    COLUMN_MAPPING = {
        'chembl_drug_target_relations': {
            'standard_units': 'standard_unit'
        }
    }

    if table_name and table_name in COLUMN_MAPPING:
        return COLUMN_MAPPING[table_name].get(default_name, default_name)

    return default_name


def import_drug_target_relations(conn, csv_path):
    """chembl_drug_target_relations 테이블 import"""
    table_name = 'chembl_drug_target_relations'

    print(f"\n[1/2] Importing {table_name}...")
    print(f"  Source: {csv_path}")
    print(f"  Size: {csv_path.stat().st_size / (1024**3):.2f} GB")

    # 기존 데이터 삭제
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name}")
    conn.commit()
    print(f"  ✓ Cleared existing data")

    # 청크 단위로 import (메모리 절약)
    chunk_size = 100000
    total_rows = 0

    print(f"  Importing in chunks of {chunk_size:,}...")

    for chunk_num, df_chunk in enumerate(tqdm(
        pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False),
        desc="  Progress"
    ), 1):
        # 컬럼명 변환
        df_chunk.columns = [sanitize_column_name(col, table_name) for col in df_chunk.columns]

        # 데이터 삽입
        df_chunk.to_sql(table_name, conn, if_exists='append', index=False)
        total_rows += len(df_chunk)

        # 주기적으로 commit (메모리 관리)
        if chunk_num % 10 == 0:
            conn.commit()

    conn.commit()
    print(f"  ✓ Imported {total_rows:,} rows")

    return total_rows


def import_target_synonyms(conn, csv_path):
    """chembl_target_synonyms 테이블 import"""
    table_name = 'chembl_target_synonyms'

    print(f"\n[2/2] Importing {table_name}...")
    print(f"  Source: {csv_path}")
    print(f"  Size: {csv_path.stat().st_size / (1024**2):.2f} MB")

    # 기존 데이터 삭제
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name}")
    conn.commit()
    print(f"  ✓ Cleared existing data")

    # CSV 읽기
    print(f"  Reading CSV...")
    df = pd.read_csv(csv_path, low_memory=False)

    # 컬럼명 변환
    df.columns = [sanitize_column_name(col, table_name) for col in df.columns]

    # 데이터 삽입
    print(f"  Inserting {len(df):,} rows...")
    df.to_sql(table_name, conn, if_exists='append', index=False, chunksize=10000)
    conn.commit()

    print(f"  ✓ Imported {len(df):,} rows")

    return len(df)


def main():
    print("=" * 70)
    print("Import Missing ChEMBL Tables")
    print("=" * 70)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / 'database' / 'database.db'
    data_dir = base_dir / 'processed' / 'Chembl'

    csv_files = {
        'drug_target': data_dir / 'compound-target' / 'compound-target_information.csv',
        'target_synonyms': data_dir / 'target' / 'target_synonyms.csv'
    }

    # 파일 존재 확인
    print("\nChecking files...")
    for name, path in csv_files.items():
        if not path.exists():
            print(f"  ✗ Not found: {path}")
            sys.exit(1)
        print(f"  ✓ {name}: {path.name}")

    # DB 연결
    print(f"\nDatabase: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        # Import
        total_drug_target = import_drug_target_relations(conn, csv_files['drug_target'])
        total_synonyms = import_target_synonyms(conn, csv_files['target_synonyms'])

        # 최종 확인
        print("\n" + "=" * 70)
        print("Import Complete!")
        print("=" * 70)

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM chembl_drug_target_relations")
        count1 = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chembl_target_synonyms")
        count2 = cursor.fetchone()[0]

        print(f"\nFinal row counts:")
        print(f"  - chembl_drug_target_relations: {count1:,} rows")
        print(f"  - chembl_target_synonyms: {count2:,} rows")

        # 전체 ChEMBL 통계
        print(f"\nAll ChEMBL tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chembl_%' ORDER BY name")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count:,} rows")

        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
