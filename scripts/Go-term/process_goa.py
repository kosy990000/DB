#!/usr/bin/env python3
"""
GOA (Gene Ontology Annotation) 데이터 처리
Human과 Mouse GOA 데이터를 전체 컬럼 그대로 저장
"""

import pandas as pd

# 데이터 경로
data_path = "../../data/Go-term"

# GAF 2.2 공식 스펙에 맞춘 컬럼명
gaf_2_2_cols = [
    "DB",                   # 1. DB (예: UniProtKB, MGI)
    "DB_Object_ID",         # 2. DB Object ID
    "DB_Object_Symbol",     # 3. DB Object Symbol (유전자 심볼)
    "Relation",             # 4. Relation
    "GO_ID",                # 5. GO ID
    "Reference",            # 6. Reference
    "Evidence_Code",        # 7. Evidence Code
    "With_From",            # 8. With (or) From
    "Aspect",               # 9. Aspect (P, F, C)
    "DB_Object_Name",       # 10. DB Object Name
    "DB_Object_Synonym",    # 11. DB Object Synonym
    "DB_Object_Type",       # 12. DB Object Type
    "Taxon",                # 13. Taxon
    "Date",                 # 14. Date
    "Assigned_By",          # 15. Assigned By
    "Annotation_Extension", # 16. Annotation Extension
    "Gene_Product_Form_ID"  # 17. Gene Product Form ID
]

def process_goa_file(filename, species_name):
    """GOA 파일을 읽어서 전체 데이터 저장"""

    print(f"\n{'='*60}")
    print(f"Processing {species_name.upper()}: {filename}")
    print(f"{'='*60}")

    # 데이터 로드
    df = pd.read_csv(
        f"{data_path}/raw/{filename}",
        sep="\t",
        comment="!",
        header=None,
        names=gaf_2_2_cols,
        dtype=str,
        low_memory=False
    )

    print(f"Total annotations: {len(df):,}")
    print(f"Unique genes: {df['DB_Object_Symbol'].nunique():,}")
    print(f"Unique GO terms: {df['GO_ID'].nunique():,}")

    # Aspect 분포
    print(f"\n[Aspect 분포]")
    aspect_map = {'P': 'BP', 'F': 'MF', 'C': 'CC'}
    for aspect, count in df['Aspect'].value_counts().items():
        print(f"  - {aspect_map.get(aspect, aspect)}: {count:,}")

    # Evidence Code Top 10
    print(f"\n[Evidence Code Top 10]")
    for code, count in df['Evidence_Code'].value_counts().head(10).items():
        print(f"  - {code}: {count:,}")

    # 8개 핵심 컬럼만 선택
    core_columns = [
        'DB_Object_ID',      # 유전자/단백질 ID
        'DB_Object_Symbol',  # 유전자 심볼
        'GO_ID',             # GO term
        'Aspect',            # BP/MF/CC
        'Evidence_Code',     # 신뢰도
        'Relation',          # 관계 유형
        'Reference',         # 출처
        'Taxon'              # 종 구분
    ]

    df_core = df[core_columns].copy()

    # 컬럼명을 snake_case로 변경
    df_core.columns = [
        'db_object_id',
        'db_object_symbol',
        'go_id',
        'aspect',
        'evidence_code',
        'relation',
        'reference',
        'taxon'
    ]

    # Taxon 정리 (taxon:9606 -> 9606)
    df_core['taxon'] = df_core['taxon'].str.replace('taxon:', '', regex=False)

    # 저장
    output_file = f"{data_path}/go-data/goa_{species_name}.csv"
    df_core.to_csv(output_file, index=False)
    print(f"\n✓ Saved: goa_{species_name}.csv ({len(df_core):,} rows, {len(df_core.columns)} columns - 핵심 8개만)")

    return df_core

def main():
    """Human과 Mouse GOA 데이터 처리"""

    # Human GOA
    df_human = process_goa_file('goa_human.gaf', 'human')

    # Mouse GOA
    df_mouse = process_goa_file('mgi.gaf', 'mouse')

    print("\n" + "="*60)
    print("COMPLETED!")
    print("="*60)
    print("\n생성된 파일 (핵심 8개 컬럼만):")
    print(f"  - goa_human.csv: {len(df_human):,} annotations")
    print(f"  - goa_mouse.csv: {len(df_mouse):,} annotations")
    print("\n포함된 컬럼 (8개, snake_case):")
    print("  - db_object_id, db_object_symbol, go_id, aspect")
    print("  - evidence_code, relation, reference, taxon")
    print("\n필터링 예시:")
    print("  - 고신뢰도만: df[df['evidence_code'].isin(['IDA','IMP','TAS','IC'])]")
    print("  - BP만: df[df['aspect'] == 'P']")
    print("  - Human만: df[df['taxon'] == '9606']")

if __name__ == '__main__':
    main()
