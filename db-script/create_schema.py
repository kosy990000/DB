#!/usr/bin/env python3
"""
데이터베이스 스키마 생성 스크립트
processed_analysis_filtered.json 파일을 기반으로 SQLite 스키마를 자동 생성
"""

import json
from pathlib import Path
from datetime import datetime


def map_dtype_to_sql(dtype, column_info):
    """pandas dtype을 SQLite 데이터 타입으로 매핑"""
    if dtype == 'object':
        return 'TEXT'
    elif dtype == 'int64':
        return 'INTEGER'
    elif dtype == 'float64':
        return 'REAL'
    elif dtype == 'bool':
        return 'INTEGER'  # SQLite에서는 BOOLEAN이 없으므로 INTEGER 사용
    else:
        return 'TEXT'


def sanitize_table_name(file_path):
    """파일 경로를 테이블 이름으로 변환"""
    path_without_ext = file_path.replace('.csv', '')
    default_name = path_without_ext.replace('/', '_').replace('-', '_').lower()

    # 테이블명 매핑
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

    # 테이블별 컬럼명 매핑
    COLUMN_MAPPING = {
        'chembl_drug_target_relations': {
            'standard_units': 'standard_unit'
        }
    }

    if table_name and table_name in COLUMN_MAPPING:
        return COLUMN_MAPPING[table_name].get(default_name, default_name)

    return default_name


def generate_create_table_statement(table_name, columns_info, file_info):
    """CREATE TABLE 문 생성"""
    lines = [f"CREATE TABLE {table_name} ("]
    column_defs = []
    primary_keys = []
    unique_columns = []
    index_columns = []
    foreign_keys = []

    for col in columns_info:
        col_name = sanitize_column_name(col['칼럼명'], table_name)
        dtype = col['dtype']
        sql_type = map_dtype_to_sql(dtype, col)

        # NULL 제약조건
        null_constraint = '' if col['결측치 개수'] > 0 else ' NOT NULL'
        column_def = f"    {col_name} {sql_type}{null_constraint}"
        column_defs.append(column_def)

        # PK와 UNIQUE 후보 수집
        if col.get('PK 후보 여부', False):
            primary_keys.append(col_name)
        elif col.get('UNIQUE 후보 여부', False):
            unique_columns.append(col_name)
        # ID 계열 칼럼은 인덱스 추가 (PK, UNIQUE 제외)
        elif any(keyword in col_name for keyword in ['_id', 'chembl', 'uniprot', 'entrez', 'cid']):
            index_columns.append(col_name)

    lines.append(',\n'.join(column_defs))

    # Primary Key 추가
    if primary_keys:
        lines.append(f",\n    PRIMARY KEY ({', '.join(primary_keys)})")

    # Foreign Key 정의
    FK_MAPPING = {
        # Taxon FK (다른 테이블들이 taxon 참조)
        'uniprot': [
            ('taxon_id', 'taxon', 'taxon_id')
        ],
        'drugbank_targets': [
            ('taxon_id', 'taxon', 'taxon_id')
        ],
        'ncbi_info': [
            ('taxon_id', 'taxon', 'taxon_id')
        ],
        'ncbi_synonyms': [
            ('entrez_id', 'ncbi_info', 'entrez_id'),
            ('taxon_id', 'taxon', 'taxon_id')
        ],
        'ncbi_ensembl': [
            ('taxon_id', 'taxon', 'taxon_id')
        ],
        'kegg_pathway': [
            ('taxon_id', 'taxon', 'taxon_id')
        ],

        # ChEMBL
        'chembl_synonyms': [
            ('chembl_id', 'chembl_compounds', 'chembl_id')
        ],
        'chembl_target_synonyms': [
            ('target_chembl_id', 'chembl_targets', 'target_chembl_id')
        ],
        'chembl_drug_disease_relations': [
            ('drug_chembl_id', 'chembl_compounds', 'chembl_id'),
            ('mesh_id', 'chembl_diseases', 'mesh_id')
        ],
        'chembl_drug_target_relations': [
            ('drug_chembl_id', 'chembl_compounds', 'chembl_id'),
            ('target_chembl_id', 'chembl_targets', 'target_chembl_id')
        ],
        # DrugBank
        'drugbank_drug_target_relations': [
            ('drugbank_id', 'drugbank_drugs', 'drugbank_id'),
            ('uniprot_id', 'drugbank_targets', 'uniprot_id')
        ],
        # PubChem
        'pubchem_compound_synonyms': [
            ('cid', 'pubchem_compounds', 'cid')
        ],
        # NCBI
        'ncbi_synonyms': [
            ('entrez_id', 'ncbi_info', 'entrez_id')
        ],
        'ncbi_ensembl': [
            ('entrez_id', 'ncbi_info', 'entrez_id')
        ],
    }

    # Foreign Key 추가
    if table_name in FK_MAPPING:
        for fk_col, ref_table, ref_col in FK_MAPPING[table_name]:
            lines.append(f",\n    FOREIGN KEY ({fk_col}) REFERENCES {ref_table}({ref_col})")

    lines.append("\n);")
    result = '\n'.join(lines)

    # 인덱스 추가
    indexes = []

    # Unique 인덱스
    for unique_col in unique_columns:
        indexes.append(f"CREATE UNIQUE INDEX idx_{table_name}_{unique_col} ON {table_name}({unique_col});")

    # 일반 인덱스
    for idx_col in index_columns:
        indexes.append(f"CREATE INDEX idx_{table_name}_{idx_col} ON {table_name}({idx_col});")

    if indexes:
        result += '\n' + '\n'.join(indexes)

    return result


def get_table_creation_order():
    """Foreign Key 의존성을 고려한 테이블 생성 순서 반환"""
    # 각 카테고리 내에서 부모 테이블을 먼저, 자식 테이블을 나중에
    order = [
        # Taxon (가장 먼저 - 많은 테이블이 참조)
        'taxon',

        # ChEMBL - 부모 테이블 먼저
        'chembl_compounds',
        'chembl_targets',
        'chembl_diseases',
        # ChEMBL - 자식 테이블
        'chembl_synonyms',
        'chembl_target_synonyms',
        'chembl_drug_disease_relations',
        'chembl_drug_target_relations',

        # UniProt
        'uniprot',

        # DrugBank - 부모 테이블 먼저
        'drugbank_drugs',
        'drugbank_targets',
        # DrugBank - 자식 테이블
        'drugbank_drug_target_relations',

        # PubChem - 부모 테이블 먼저
        'pubchem_compounds',
        # PubChem - 자식 테이블
        'pubchem_compound_synonyms',

        # NCBI - 부모 테이블 먼저
        'ncbi_info',
        # NCBI - 자식 테이블
        'ncbi_synonyms',
        'ncbi_ensembl',

        # KEGG
        'kegg_pathway',

        # Reactome - 부모 테이블 먼저
        'reactome_pathway',
        # Reactome - 자식 테이블
        'reactome_pathway_genes',
    ]
    return {table: idx for idx, table in enumerate(order)}


def main():
    # JSON 파일 읽기
    json_path = Path(__file__).parent.parent / 'processed_analysis_filtered.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 스키마 파일 경로
    schema_output_path = Path(__file__).parent / 'database_schema.sql'

    with open(schema_output_path, 'w', encoding='utf-8') as f:
        f.write("-- ============================================\n")
        f.write("-- SQLite Database Schema\n")
        f.write("-- ============================================\n")
        f.write("-- Auto-generated from processed_analysis_filtered.json\n")
        f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total tables: {len(data)}\n")
        f.write("-- ============================================\n\n")
        f.write("PRAGMA foreign_keys = ON;\n\n")

        # 테이블 생성 순서 가져오기
        table_order = get_table_creation_order()

        # 카테고리별로 정리
        categories = {
            'Taxon': [],
            'ChEMBL': [],
            'DrugBank': [],
            'PubChem': [],
            'KEGG': [],
            'NCBI': [],
            'Reactome': [],
            'UniProt': []
        }

        for file_path, file_info in data.items():
            if file_path == 'taxon.csv':
                categories['Taxon'].append((file_path, file_info))
            elif 'Chembl' in file_path:
                categories['ChEMBL'].append((file_path, file_info))
            elif 'Drugbank' in file_path:
                categories['DrugBank'].append((file_path, file_info))
            elif 'PubChem' in file_path:
                categories['PubChem'].append((file_path, file_info))
            elif 'Kegg' in file_path:
                categories['KEGG'].append((file_path, file_info))
            elif 'NCBI' in file_path:
                categories['NCBI'].append((file_path, file_info))
            elif 'Reactome' in file_path:
                categories['Reactome'].append((file_path, file_info))
            elif 'Uniprot' in file_path:
                categories['UniProt'].append((file_path, file_info))

        # 카테고리별로 스키마 생성
        for category, items in categories.items():
            if not items:
                continue

            f.write(f"\n-- ============================================\n")
            f.write(f"-- {category}\n")
            f.write(f"-- ============================================\n\n")

            # Foreign Key 의존성을 고려하여 정렬
            sorted_items = sorted(items, key=lambda x: table_order.get(sanitize_table_name(x[0]), 999))

            for file_path, file_info in sorted_items:
                table_name = sanitize_table_name(file_path)
                columns_info = file_info['columns']

                create_stmt = generate_create_table_statement(table_name, columns_info, file_info)

                f.write(f"-- Source: {file_path}\n")
                f.write(f"-- Rows: {file_info['rows']:,}\n")
                f.write(create_stmt + "\n\n")

    print(f"✓ Database schema generated: {schema_output_path}")
    print(f"✓ Total tables: {len(data)}")

    # 카테고리별 통계 출력
    print("\nTables by category:")
    for category, items in categories.items():
        if items:
            print(f"  - {category}: {len(items)} tables")


if __name__ == '__main__':
    main()
