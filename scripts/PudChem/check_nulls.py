#!/usr/bin/env python3
"""
PubChem Compound 빈 값(Null) 확인
"""

import pandas as pd

data_path = "/data/project/shinyoung/DB/data/PudChem/pudchem-data"

print("="*80)
print("PubChem Compound 빈 값 분석")
print("="*80)

# 샘플 데이터 로드
print("\n샘플 데이터 로드 중 (첫 100만 행)...")
df = pd.read_csv(
    f"{data_path}/pubchem_compound.csv",
    nrows=1000000,
    dtype=str,  # 모든 컬럼을 문자열로 읽기
    keep_default_na=True
)

print(f"총 샘플: {len(df):,} rows")
print(f"컬럼: {list(df.columns)}\n")

print("="*80)
print("각 컬럼별 빈 값 분석")
print("="*80)

for col in df.columns:
    null_count = df[col].isna().sum()
    null_pct = (null_count / len(df)) * 100

    # 빈 문자열도 확인
    empty_str_count = (df[col] == '').sum()
    empty_str_pct = (empty_str_count / len(df)) * 100

    print(f"\n[{col}]")
    print(f"  - NaN/Null: {null_count:,} ({null_pct:.3f}%)")
    print(f"  - 빈 문자열 (''): {empty_str_count:,} ({empty_str_pct:.3f}%)")
    print(f"  - 총 빈 값: {null_count + empty_str_count:,} ({(null_count + empty_str_count)/len(df)*100:.3f}%)")

    # 빈 값이 있는 행 샘플 출력
    if null_count > 0:
        print(f"\n  빈 값(NaN)이 있는 행 샘플 (처음 3개):")
        null_rows = df[df[col].isna()].head(3)
        for idx, row in null_rows.iterrows():
            print(f"    Row {idx}: cid={row['cid']}, inchi_key={row['inchi_key'][:30] if pd.notna(row['inchi_key']) else 'NaN'}..., title={row['title'][:30] if pd.notna(row['title']) else 'NaN'}...")

    if empty_str_count > 0 and empty_str_count != null_count:
        print(f"\n  빈 문자열('')이 있는 행 샘플 (처음 3개):")
        empty_rows = df[df[col] == ''].head(3)
        for idx, row in empty_rows.iterrows():
            print(f"    Row {idx}: cid={row['cid']}, inchi_key={row['inchi_key'][:30] if pd.notna(row['inchi_key']) else 'NaN'}..., title={row['title'][:30] if pd.notna(row['title']) else 'NaN'}...")

# 모든 컬럼이 채워진 행 확인
print("\n" + "="*80)
print("데이터 완성도")
print("="*80)
complete_rows = df.dropna()
print(f"모든 컬럼 채워짐: {len(complete_rows):,} ({len(complete_rows)/len(df)*100:.2f}%)")

# 필수 컬럼만 확인 (cid, smiles, inchi_key)
essential_complete = df[['cid', 'smiles', 'inchi_key']].dropna()
print(f"필수 컬럼 채워짐 (cid, smiles, inchi_key): {len(essential_complete):,} ({len(essential_complete)/len(df)*100:.2f}%)")

# 최소 필수 (cid, smiles)
minimal_complete = df[['cid', 'smiles']].dropna()
print(f"최소 필수 채워짐 (cid, smiles): {len(minimal_complete):,} ({len(minimal_complete)/len(df)*100:.2f}%)")

print("\n" + "="*80)
print("✅ 분석 완료!")
print("="*80)
