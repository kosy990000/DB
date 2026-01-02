#!/usr/bin/env python3
"""
PubChem Compound 전체 파일 빈 값 확인 (청크 단위 처리)
"""

import pandas as pd

data_path = "/data/project/shinyoung/DB/data/PudChem/pudchem-data"

print("="*80)
print("PubChem Compound 전체 파일 빈 값 분석")
print("="*80)

# 청크 단위로 읽기
chunk_size = 1000000  # 한 번에 100만 행씩
total_rows = 0
null_counts = {
    'cid': 0,
    'inchi_key': 0,
    'smiles': 0,
    'title': 0
}
empty_str_counts = {
    'cid': 0,
    'inchi_key': 0,
    'smiles': 0,
    'title': 0
}

# 빈 값이 있는 행 샘플 저장
null_samples = {col: [] for col in ['cid', 'inchi_key', 'smiles', 'title']}

print(f"\n청크 크기: {chunk_size:,} 행씩 처리")
print("처리 중...\n")

chunk_num = 0
for chunk in pd.read_csv(
    f"{data_path}/pubchem_compound.csv",
    chunksize=chunk_size,
    dtype=str,
    keep_default_na=True
):
    chunk_num += 1
    total_rows += len(chunk)

    # 각 컬럼별 빈 값 카운트
    for col in chunk.columns:
        # NaN 카운트
        null_count = chunk[col].isna().sum()
        null_counts[col] += null_count

        # 빈 문자열 카운트
        empty_count = (chunk[col] == '').sum()
        empty_str_counts[col] += empty_count

        # 빈 값이 있는 행 샘플 저장 (각 컬럼당 최대 5개)
        if null_count > 0 and len(null_samples[col]) < 5:
            null_rows = chunk[chunk[col].isna()].head(5 - len(null_samples[col]))
            for idx, row in null_rows.iterrows():
                null_samples[col].append({
                    'row_num': total_rows - len(chunk) + idx,
                    'cid': row['cid'],
                    'inchi_key': row['inchi_key'][:30] if pd.notna(row['inchi_key']) else 'NaN',
                    'smiles': row['smiles'][:30] if pd.notna(row['smiles']) else 'NaN',
                    'title': row['title'][:30] if pd.notna(row['title']) else 'NaN'
                })

    if chunk_num % 10 == 0:
        print(f"  처리됨: {total_rows:,} 행 ({chunk_num} 청크)")

print(f"\n총 처리된 행: {total_rows:,}\n")

print("="*80)
print("전체 파일 빈 값 분석 결과")
print("="*80)

for col in ['cid', 'inchi_key', 'smiles', 'title']:
    null_count = null_counts[col]
    empty_count = empty_str_counts[col]
    total_null = null_count + empty_count

    null_pct = (null_count / total_rows) * 100
    empty_pct = (empty_count / total_rows) * 100
    total_pct = (total_null / total_rows) * 100

    print(f"\n[{col}]")
    print(f"  - NaN/Null: {null_count:,} ({null_pct:.4f}%)")
    print(f"  - 빈 문자열 (''): {empty_count:,} ({empty_pct:.4f}%)")
    print(f"  - 총 빈 값: {total_null:,} ({total_pct:.4f}%)")

    # 샘플 출력
    if null_samples[col]:
        print(f"\n  빈 값이 있는 행 샘플 (최대 5개):")
        for sample in null_samples[col]:
            print(f"    Row {sample['row_num']}: cid={sample['cid']}, "
                  f"inchi={sample['inchi_key']}..., "
                  f"title={sample['title']}...")

print("\n" + "="*80)
print("요약")
print("="*80)
print(f"총 데이터 행: {total_rows:,}")
print(f"\n필수 컬럼 빈 값:")
print(f"  - cid: {null_counts['cid']:,}")
print(f"  - smiles: {null_counts['smiles']:,}")
print(f"  - inchi_key: {null_counts['inchi_key']:,}")
print(f"\n선택적 컬럼 빈 값:")
print(f"  - title: {null_counts['title']:,}")

if null_counts['cid'] == 0 and null_counts['smiles'] == 0 and null_counts['inchi_key'] == 0:
    print("\n✅ 필수 컬럼 (cid, smiles, inchi_key)은 100% 완벽합니다!")
else:
    print("\n⚠️ 필수 컬럼에 빈 값이 있습니다!")

print("\n" + "="*80)
print("✅ 전체 분석 완료!")
print("="*80)
