#!/usr/bin/env python3
"""
Analyze all processed CSV files using checkNull.py logic and generate SQLite schema
"""
import pandas as pd
from pathlib import Path
import json

def check_all_columns(df):
    result = []
    n = len(df)

    for col in df.columns:
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique(dropna=True)
        dtype = df[col].dtype
        ratio = unique_count / n if n > 0 else 0

        # 변수 유형 추정
        if dtype in ["object", "category"]:
            cat_type = "문자열/카테고리형"
        elif ratio < 0.05:
            cat_type = "카테고리형 가능"
        else:
            cat_type = "연속형 가능"

        # 🔑 키 가능성 판단
        is_pk_candidate = (
            null_count == 0 and
            unique_count == n and
            ("int" in str(dtype).lower() or "object" in str(dtype).lower())
        )

        is_unique_candidate = (
            null_count == 0 and
            unique_count == n
        )

        result.append({
            "칼럼명": col,
            "결측치 개수": null_count,
            "결측치 비율(%)": round(null_count / n * 100, 2),
            "dtype": str(dtype),
            "고유값 수": unique_count,
            "고유값 비율": round(ratio, 3),
            "변수유형 추정": cat_type,
            "PK 후보 여부": is_pk_candidate,
            "UNIQUE 후보 여부": is_unique_candidate
        })

    return pd.DataFrame(result)


def infer_sqlite_type(dtype_str, cat_type):
    """Infer SQLite type from pandas dtype and category type"""
    if 'int' in dtype_str.lower():
        return 'INTEGER'
    elif 'float' in dtype_str.lower():
        return 'REAL'
    else:
        return 'TEXT'

def analyze_all_files():
    """Analyze all CSV files in processed directory"""
    processed_dir = Path('./processed')
    csv_files = sorted(processed_dir.rglob('*.csv'))

    print(f"Found {len(csv_files)} CSV files in processed directory\n")
    print("=" * 100)

    all_results = {}

    for csv_file in csv_files:
        rel_path = csv_file.relative_to(processed_dir)
        print(f"\n📁 {rel_path}")

        try:
            # Read CSV file
            df = pd.read_csv(csv_file, low_memory=False)

            # Analyze columns
            summary_df = check_all_columns(df)

            # Display summary
            print(f"   총 행 수: {len(df):,}")
            print(f"   총 컬럼 수: {len(df.columns)}")
            print()

            # Show each column info
            for _, row in summary_df.iterrows():
                null_info = f"({row['결측치 비율(%)']}%)" if row['결측치 개수'] > 0 else ""
                print(f"   - {row['칼럼명']:<40} {row['dtype']:<15} {row['변수유형 추정']:<20} {null_info}")

            # Store results
            all_results[str(rel_path)] = {
                'rows': len(df),
                'columns': summary_df.to_dict('records')
            }

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_results[str(rel_path)] = {'error': str(e)}

        print("-" * 100)

    # Save results to JSON
    output_file = 'processed_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analysis completed! Results saved to {output_file}")

    return all_results

if __name__ == '__main__':
    analyze_all_files()
