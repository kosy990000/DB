import pandas as pd

def check_all_columns(df):
    result = []
    n = len(df)
    for col in df.columns:
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique(dropna=True)
        dtype = df[col].dtype
        ratio = unique_count / n

        if dtype in ["object", "category"]:
            cat_type = "문자열/카테고리형"
        elif ratio < 0.05:
            cat_type = "카테고리형 가능"
        else:
            cat_type = "연속형 가능"

        result.append({
            "칼럼명": col,
            "결측치 개수": null_count,
            "결측치 비율(%)": round(null_count / n * 100, 2),
            "dtype": str(dtype),
            "고유값 수": unique_count,
            "고유값 비율": round(ratio, 3),
            "변수유형 추정": cat_type
        })
    return pd.DataFrame(result)

# 🔸 CSV 경로 입력
file_path = input("CSV 파일 경로를 입력하세요: ")

# 🔸 경로를 읽어서 DataFrame으로 변환
df = pd.read_csv(file_path)

# 🔸 전체 칼럼 점검 실행
summary_df = check_all_columns(df)
print(summary_df)

