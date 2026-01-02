#!/usr/bin/env python3
"""
PubChem Synonyms 파일 분석
"""

import pandas as pd

data_path = "/data/project/shinyoung/DB/data/PudChem/pudchem-data"

print("="*80)
print("PubChem Synonyms 전체 파일 분석")
print("="*80)

# 청크 단위로 읽기
chunk_size = 1000000
total_rows = 0
null_counts = {'cid': 0, 'synonym': 0}
empty_str_counts = {'cid': 0, 'synonym': 0}

# 통계
unique_cids = set()
synonym_length_sum = 0
synonym_count = 0
max_synonym_length = 0
min_synonym_length = float('inf')

# 빈 값 샘플
null_samples = {'cid': [], 'synonym': []}

print(f"\n청크 크기: {chunk_size:,} 행씩 처리")
print("처리 중...\n")

chunk_num = 0
for chunk in pd.read_csv(
    f"{data_path}/pudchem_synonyms.csv",
    chunksize=chunk_size,
    dtype=str,
    keep_default_na=True
):
    chunk_num += 1
    total_rows += len(chunk)

    # 빈 값 카운트
    for col in chunk.columns:
        null_count = chunk[col].isna().sum()
        null_counts[col] += null_count

        empty_count = (chunk[col] == '').sum()
        empty_str_counts[col] += empty_count

        # 빈 값 샘플 저장
        if null_count > 0 and len(null_samples[col]) < 5:
            null_rows = chunk[chunk[col].isna()].head(5 - len(null_samples[col]))
            for idx, row in null_rows.iterrows():
                null_samples[col].append({
                    'row_num': total_rows - len(chunk) + idx,
                    'cid': row['cid'],
                    'synonym': str(row['synonym'])[:50] if pd.notna(row['synonym']) else 'NaN'
                })

    # 통계 수집
    unique_cids.update(chunk['cid'].dropna().unique())

    # synonym 길이 통계
    synonyms = chunk['synonym'].dropna()
    if len(synonyms) > 0:
        lengths = synonyms.str.len()
        synonym_length_sum += lengths.sum()
        synonym_count += len(synonyms)
        max_synonym_length = max(max_synonym_length, lengths.max())
        min_synonym_length = min(min_synonym_length, lengths.min())

    if chunk_num % 10 == 0:
        print(f"  처리됨: {total_rows:,} 행 ({chunk_num} 청크)")

print(f"\n총 처리된 행: {total_rows:,}\n")

print("="*80)
print("1. 빈 값 분석")
print("="*80)

for col in ['cid', 'synonym']:
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
        print(f"\n  빈 값이 있는 행 샘플:")
        for sample in null_samples[col][:3]:
            print(f"    Row {sample['row_num']}: cid={sample['cid']}, synonym={sample['synonym']}...")

print("\n" + "="*80)
print("2. 통계 정보")
print("="*80)

print(f"\n총 synonym 레코드: {total_rows:,}")
print(f"고유한 CID 개수: {len(unique_cids):,}")
print(f"CID당 평균 synonym 개수: {total_rows / len(unique_cids):.1f}")

print(f"\nSynonym 길이 통계:")
avg_length = synonym_length_sum / synonym_count if synonym_count > 0 else 0
print(f"  - 평균 길이: {avg_length:.1f} 문자")
print(f"  - 최소 길이: {min_synonym_length} 문자")
print(f"  - 최대 길이: {max_synonym_length} 문자")

print("\n" + "="*80)
print("3. 데이터 품질")
print("="*80)

complete_pct = ((total_rows - null_counts['cid'] - null_counts['synonym']) / total_rows) * 100
print(f"완전한 레코드 (cid + synonym): {complete_pct:.4f}%")

if null_counts['cid'] == 0 and null_counts['synonym'] == 0:
    print("\n✅ 모든 레코드가 완전합니다!")
else:
    print("\n⚠️ 일부 빈 값이 존재합니다.")

print("\n" + "="*80)
print("4. Foreign Key 관계")
print("="*80)

print("\n이 테이블의 구조:")
print("  - cid: pubchem_compound 테이블의 cid를 참조하는 Foreign Key")
print("  - synonym: 화합물의 다양한 이름/별칭")
print("  - 관계: 1개 compound → N개 synonyms (1:N)")

if null_counts['cid'] == 0:
    print("\n✅ cid에 NULL이 없어서 Foreign Key로 사용 가능합니다!")
else:
    print(f"\n⚠️ cid에 {null_counts['cid']:,}개의 NULL이 있습니다.")

print("\n" + "="*80)
print("✅ 분석 완료!")
print("="*80)
