#!/usr/bin/env python3
"""
GOA 데이터 컬럼 분석: 각 컬럼의 중요도와 null 비율 확인
"""

import pandas as pd

data_path = "../../data/Go-term"

def analyze_columns(filename, species_name):
    """컬럼별 null 비율과 고유값 분석"""

    print(f"\n{'='*80}")
    print(f"{species_name.upper()} GOA 데이터 컬럼 분석")
    print(f"{'='*80}\n")

    df = pd.read_csv(f"{data_path}/go-data/{filename}")

    print(f"총 데이터 개수: {len(df):,}\n")

    # 컬럼 중요도 분류
    importance = {
        '필수 (Essential)': [
            'DB_Object_ID',      # 유전자/단백질 고유 ID
            'DB_Object_Symbol',  # 유전자 심볼 (가독성)
            'GO_ID',             # GO term ID
            'Aspect',            # BP/MF/CC 구분
            'Evidence_Code',     # 신뢰도 판단
        ],
        '중요 (Important)': [
            'Relation',          # GO term과의 관계
            'Reference',         # 출처 (논문 등)
            'Taxon',             # 종 구분
            'DB',                # 데이터베이스 소스
        ],
        '선택적 (Optional)': [
            'DB_Object_Name',    # 유전자 전체 이름 (Symbol로 충분)
            'With_From',         # 추가 증거 (복잡하고 null 많음)
            'Date',              # 주석 날짜 (버전 관리용)
            'Assigned_By',       # 주석 제공자
        ],
        '거의 불필요 (Rarely Used)': [
            'DB_Object_Synonym', # 동의어 (거의 사용 안함)
            'DB_Object_Type',    # 객체 타입 (거의 다 protein)
            'Annotation_Extension',  # 추가 주석 (대부분 null)
            'Gene_Product_Form_ID',  # 특정 형태 ID (대부분 null)
        ]
    }

    # 각 카테고리별 분석
    for category, columns in importance.items():
        print(f"\n[{category}]")
        print(f"{'-'*80}")
        for col in columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                null_pct = (null_count / len(df)) * 100
                unique_count = df[col].nunique()

                # 샘플 값
                sample_values = df[col].dropna().head(3).tolist()
                sample_str = ', '.join(str(v)[:30] for v in sample_values)

                print(f"\n  {col}:")
                print(f"    - Null: {null_count:,} ({null_pct:.1f}%)")
                print(f"    - 고유값: {unique_count:,}")
                print(f"    - 샘플: {sample_str}")

    # 추천 컬럼 세트
    print(f"\n{'='*80}")
    print("💡 추천 컬럼 세트")
    print(f"{'='*80}\n")

    print("1️⃣ 최소 필수 컬럼 (분석용):")
    minimal = ['DB_Object_ID', 'DB_Object_Symbol', 'GO_ID', 'Aspect', 'Evidence_Code']
    print(f"   {minimal}")
    print(f"   → {len(minimal)}개 컬럼\n")

    print("2️⃣ 추천 컬럼 (대부분의 분석):")
    recommended = ['DB_Object_ID', 'DB_Object_Symbol', 'GO_ID', 'Aspect',
                   'Evidence_Code', 'Relation', 'Reference', 'Taxon']
    print(f"   {recommended}")
    print(f"   → {len(recommended)}개 컬럼\n")

    print("3️⃣ 확장 컬럼 (상세 분석):")
    extended = recommended + ['DB', 'DB_Object_Name', 'Date', 'Assigned_By']
    print(f"   {extended}")
    print(f"   → {len(extended)}개 컬럼\n")

    print("4️⃣ 제거 추천 (거의 불필요):")
    remove = ['DB_Object_Synonym', 'DB_Object_Type', 'With_From',
              'Annotation_Extension', 'Gene_Product_Form_ID']
    print(f"   {remove}")
    print(f"   → 이 컬럼들은 대부분의 분석에서 사용하지 않습니다\n")

# Human과 Mouse 데이터 분석
analyze_columns('goa_human_all.csv', 'human')
analyze_columns('goa_mouse_all.csv', 'mouse')
