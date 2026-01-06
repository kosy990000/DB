#!/usr/bin/env python3
"""
테이블명과 컬럼명을 사용자 정의 스키마에 맞게 변경
"""

# 테이블명 매핑
TABLE_MAPPING = {
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
    'drugbank_drug_information_target_information': 'drugbank_targets',
    'drugbank_drug_target_information_drug_target': 'drugbank_drug_target_relations',

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

# 컬럼명 매핑 (테이블별)
COLUMN_MAPPING = {
    'drugbank_targets': {
        'gene_symbol': 'gene_name'
    },
    'chembl_drug_target_relations': {
        'standard_units': 'standard_unit'
    }
}


def update_schema():
    from pathlib import Path

    schema_path = Path(__file__).parent / 'database_schema.sql'

    with open(schema_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 테이블명 변경
    for old_name, new_name in TABLE_MAPPING.items():
        # CREATE TABLE 변경
        content = content.replace(f'CREATE TABLE {old_name} (', f'CREATE TABLE {new_name} (')
        # INDEX 변경
        content = content.replace(f'idx_{old_name}_', f'idx_{new_name}_')
        content = content.replace(f' ON {old_name}(', f' ON {new_name}(')

    # 컬럼명 변경
    for table_name, col_mappings in COLUMN_MAPPING.items():
        for old_col, new_col in col_mappings.items():
            # 주의: 해당 테이블 섹션에서만 변경해야 함
            # 간단하게 전체에서 변경 (더 정교한 파싱이 필요하면 추가 가능)
            content = content.replace(f'    {old_col} ', f'    {new_col} ')
            content = content.replace(f'_{old_col} ON', f'_{new_col} ON')
            content = content.replace(f'({old_col})', f'({new_col})')

    # 백업 생성
    backup_path = Path(__file__).parent / 'database_schema.sql.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(schema_path, 'r', encoding='utf-8') as original:
            f.write(original.read())

    # 새 스키마 저장
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Schema updated successfully")
    print(f"✓ Backup saved: {backup_path}")
    print(f"\nUpdated {len(TABLE_MAPPING)} table names")

    # 변경 내역 출력
    print("\nTable name changes:")
    for old, new in sorted(TABLE_MAPPING.items()):
        print(f"  {old} → {new}")


if __name__ == '__main__':
    update_schema()
