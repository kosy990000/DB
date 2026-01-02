#!/usr/bin/env python3
"""
PubChem Compound 데이터 분석
"""

import pandas as pd

data_path = "/data/project/shinyoung/DB/data/PudChem/pudchem-data"

print("="*80)
print("PubChem Compound 데이터 분석")
print("="*80)

# 샘플 데이터 로드 (첫 100만 행)
print("\n샘플 데이터 로드 중 (첫 100만 행)...")
df_sample = pd.read_csv(
    f"{data_path}/pubchem_compound.csv",
    nrows=1000000
)

print(f"\n총 샘플 데이터: {len(df_sample):,} rows")
print(f"컬럼: {list(df_sample.columns)}")

# 기본 정보
print("\n" + "="*80)
print("1. 컬럼 정보")
print("="*80)
for col in df_sample.columns:
    null_count = df_sample[col].isna().sum()
    null_pct = (null_count / len(df_sample)) * 100
    unique_count = df_sample[col].nunique()

    print(f"\n[{col}]")
    print(f"  - Null: {null_count:,} ({null_pct:.2f}%)")
    print(f"  - 고유값: {unique_count:,}")

    # 샘플 값
    if col == 'smiles' or col == 'inchi_key':
        sample = df_sample[col].dropna().head(3).tolist()
        for s in sample:
            print(f"  - {s[:80]}")
    else:
        sample = df_sample[col].dropna().head(5).tolist()
        for s in sample:
            s_str = str(s)[:80]
            print(f"  - {s_str}")

# 통계
print("\n" + "="*80)
print("2. CID (Compound ID) 통계")
print("="*80)
print(f"  - 최소 CID: {df_sample['cid'].min()}")
print(f"  - 최대 CID: {df_sample['cid'].max()}")
print(f"  - 평균 CID: {df_sample['cid'].mean():.0f}")

# SMILES 길이 분석
print("\n" + "="*80)
print("3. SMILES 길이 분석")
print("="*80)
smiles_lengths = df_sample['smiles'].dropna().str.len()
print(f"  - 평균 길이: {smiles_lengths.mean():.1f}")
print(f"  - 최소 길이: {smiles_lengths.min()}")
print(f"  - 최대 길이: {smiles_lengths.max()}")
print(f"  - 중간값: {smiles_lengths.median():.0f}")

# Title 분석
print("\n" + "="*80)
print("4. Title (화합물명) 분석")
print("="*80)
print(f"  - Title 있음: {df_sample['title'].notna().sum():,} ({(df_sample['title'].notna().sum()/len(df_sample)*100):.1f}%)")
print(f"  - Title 없음: {df_sample['title'].isna().sum():,} ({(df_sample['title'].isna().sum()/len(df_sample)*100):.1f}%)")

title_lengths = df_sample['title'].dropna().str.len()
print(f"  - 평균 이름 길이: {title_lengths.mean():.1f}")
print(f"  - 최대 이름 길이: {title_lengths.max()}")

# 전체 파일 크기 추정
print("\n" + "="*80)
print("5. 전체 파일 추정")
print("="*80)
import subprocess
result = subprocess.run(['wc', '-l', f'{data_path}/pubchem_compound.csv'],
                       capture_output=True, text=True)
total_lines = int(result.stdout.split()[0])
total_compounds = total_lines - 1  # 헤더 제외

print(f"  - 전체 라인 수: {total_lines:,}")
print(f"  - 전체 화합물 수: {total_compounds:,}")
print(f"  - 샘플 비율: {(len(df_sample)/total_compounds*100):.2f}%")

# 데이터 품질
print("\n" + "="*80)
print("6. 데이터 품질")
print("="*80)
complete_rows = df_sample.dropna()
print(f"  - 완전한 데이터 (모든 컬럼 채워짐): {len(complete_rows):,} ({(len(complete_rows)/len(df_sample)*100):.1f}%)")

# 필수 컬럼 (cid, smiles)만 있는 경우
essential_complete = df_sample[['cid', 'smiles']].dropna()
print(f"  - 필수 데이터 (cid + smiles): {len(essential_complete):,} ({(len(essential_complete)/len(df_sample)*100):.1f}%)")

print("\n" + "="*80)
print("✅ 분석 완료!")
print("="*80)
