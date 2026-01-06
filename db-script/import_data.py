#!/usr/bin/env python3
"""
CSV 파일들을 SQLite 데이터베이스로 import하는 스크립트
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from tqdm import tqdm


def sanitize_table_name(file_path):
    """파일 경로를 테이블 이름으로 변환"""
    path_without_ext = file_path.replace('.csv', '')
    default_name = path_without_ext.replace('/', '_').replace('-', '_').lower()

    # create_schema.py와 동일한 테이블명 매핑
    TABLE_MAPPING = {
        # Taxon
        'taxon': 'taxon',

        # ChEMBL
        'chembl_compound_compounds': 'chembl_compounds',
        'chembl_compound_compound_synonyms': 'chembl_synonyms',
        'chembl_disease_disease': 'chembl_diseases',
        'chembl_target_targets': 'chembl_targets',
        'chembl_target_target_synonyms': 'chembl_target_synonyms',
        'chembl_compound_disease_compound_disease_information': 'chembl_drug_disease_relations',
        'chembl_compound_target_compound_target_information': 'chembl_drug_target_relations',

        # UniProt
        'uniprot_uniprot_data_mouse_human': 'uniprot',

        # DrugBank
        'drugbank_drug_information_drug_information': 'drugbank_drugs',
        'drugbank_drug_target_information_drug_target': 'drugbank_drug_target_relations',
        'drugbank_target_information_target_information': 'drugbank_targets',

        # PubChem
        'pubchem_pubchem_compounds': 'pubchem_compounds',
        'pubchem_pubchem_synonyms': 'pubchem_compound_synonyms',

        # NCBI
        'ncbi_ncbi_genes': 'ncbi_info',
        'ncbi_ncbi_synonyms': 'ncbi_synonyms',
        'ncbi_ncbi_ensembl': 'ncbi_ensembl',

        # KEGG
        'kegg_pathway_list': 'kegg_pathway',

        # Reactome
        'reactome_all_pathway': 'reactome_pathway',
        'reactome_all_pathway_genes': 'reactome_pathway_genes',
    }

    return TABLE_MAPPING.get(default_name, default_name)


def sanitize_column_name(col_name, table_name=None):
    """칼럼명을 SQL 표준에 맞게 변환"""
    default_name = col_name.replace(' ', '_').replace('-', '_').lower()

    # create_schema.py와 동일한 컬럼명 매핑
    COLUMN_MAPPING = {
        'chembl_drug_target_relations': {
            'standard_units': 'standard_unit'
        }
    }

    if table_name and table_name in COLUMN_MAPPING:
        return COLUMN_MAPPING[table_name].get(default_name, default_name)

    return default_name


def get_import_order():
    """Foreign Key 제약조건을 고려한 import 순서 반환"""
    # 부모 테이블 먼저 (FK 참조 없음)
    parent_tables = [
        'taxon.csv',  # 가장 먼저 (모든 테이블이 참조)
        'Chembl/compound/compounds.csv',
        'Chembl/target/targets.csv',
        'Chembl/disease/disease.csv',
        'Drugbank/drug_information/drug_information.csv',
        'Drugbank/target_information/target_information.csv',
        'PubChem/pubchem_compounds.csv',
        'NCBI/ncbi_genes.csv',
        'Uniprot/uniprot_data_mouse_human.csv',
        'Kegg/pathway_list.csv',
        'Reactome/all_pathway.csv',
    ]

    # 자식 테이블 (FK 참조 있음)
    child_tables = [
        'Chembl/compound/compound_synonyms.csv',
        'Chembl/target/target_synonyms.csv',
        'Chembl/compound-disease/compound-disease_information.csv',
        'Chembl/compound-target/compound-target_information.csv',
        'Drugbank/drug-target_information/drug_target.csv',
        'PubChem/pubchem_synonyms.csv',
        'NCBI/ncbi_synonyms.csv',
        'NCBI/ncbi_ensembl.csv',
        'Reactome/all_pathway_genes.csv',
    ]

    return parent_tables + child_tables


def main():
    # 경로 설정
    base_dir = Path(__file__).parent.parent
    json_path = base_dir / 'processed_analysis_filtered.json'
    schema_path = Path(__file__).parent / 'database_schema.sql'
    db_path = base_dir / 'database' / 'database.db'

    # CSV 파일들의 base directory
    data_dir = base_dir / 'processed'  # CSV 파일들이 있는 디렉토리

    print("=" * 60)
    print("SQLite Database Import")
    print("=" * 60)

    # JSON 파일 읽기
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n✓ Found {len(data)} tables to import")

    # SQLite 데이터베이스 생성
    print(f"\n[1/3] Creating database: {db_path}")

    # 기존 DB 파일이 있으면 삭제 (선택사항)
    if db_path.exists():
        response = input(f"Database already exists. Overwrite? (y/n): ")
        if response.lower() == 'y':
            db_path.unlink()
            print("  ✓ Removed existing database")
        else:
            print("  ✗ Aborted")
            return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 스키마 적용
    print(f"\n[2/3] Applying schema from: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # executescript()를 사용하여 전체 스키마를 한번에 실행
    try:
        cursor.executescript(schema_sql)
        print("  ✓ Schema applied successfully")
    except sqlite3.Error as e:
        print(f"  ✗ Error applying schema: {e}")
        conn.close()
        return

    # CSV 파일 import (FK 순서 고려)
    print(f"\n[3/3] Importing CSV files (FK order)...")

    success_count = 0
    error_count = 0

    # import 순서 가져오기
    import_order = get_import_order()

    # 순서대로 import
    for file_path in tqdm(import_order, desc="Importing"):
        if file_path not in data:
            print(f"\n  ⚠ Skipping (not in filtered data): {file_path}")
            continue

        csv_path = data_dir / file_path
        table_name = sanitize_table_name(file_path)

        if not csv_path.exists():
            print(f"\n  ✗ File not found: {csv_path}")
            error_count += 1
            continue

        try:
            # CSV 읽기
            df = pd.read_csv(csv_path, low_memory=False)

            # 칼럼명 변환
            df.columns = [sanitize_column_name(col, table_name) for col in df.columns]

            # SQLite로 insert
            df.to_sql(table_name, conn, if_exists='append', index=False, chunksize=10000)

            success_count += 1

        except Exception as e:
            print(f"\n  ✗ Error importing {file_path}: {e}")
            error_count += 1

    conn.commit()
    conn.close()

    # 결과 출력
    print("\n" + "=" * 60)
    print("Import Summary")
    print("=" * 60)
    print(f"✓ Successfully imported: {success_count} tables")
    if error_count > 0:
        print(f"✗ Failed: {error_count} tables")
    print(f"\n✓ Database created: {db_path}")
    print(f"  Size: {db_path.stat().st_size / (1024**3):.2f} GB")

    # 데이터베이스 검증
    print("\n" + "=" * 60)
    print("Database Verification")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"\nTotal tables in database: {len(tables)}")
    print("\nRow counts:")
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count:,} rows")

    conn.close()


if __name__ == '__main__':
    main()
