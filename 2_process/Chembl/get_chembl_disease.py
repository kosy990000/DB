import sqlite3
import pandas as pd
import os


def extract_chembl_diseases(db_path, output_dir):
    """
    ChEMBL 데이터베이스에서 질병(Disease) 정보를 추출합니다.

    Parameters:
    -----------
    db_path : str
        ChEMBL SQLite 데이터베이스 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    df_diseases: DataFrame
    """

    if not os.path.exists(db_path):
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print(f"ChEMBL 데이터베이스를 먼저 다운로드해주세요.")
        return None

    print(f"\n{'='*70}")
    print(f"ChEMBL Disease 정보 추출 시작")
    print(f"{'='*70}")
    print(f"데이터베이스: {db_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(db_path)

    # =========================================================
    # Disease 정보 추출
    # =========================================================
    print("\nDisease 정보 추출 중...")

    query = """
        SELECT DISTINCT
            mesh_id AS mesh_id,
            mesh_heading AS mesh_heading
        FROM
            drug_indication
        WHERE
            mesh_id IS NOT NULL
    """

    df_diseases = pd.read_sql_query(query, conn)
    conn.close()

    # 데이터 전처리: mesh_heading에서 따옴표 제거
    df_diseases["mesh_heading"] = df_diseases['mesh_heading'].str.replace('"', '', regex=False)

    print(f"추출 완료: {len(df_diseases):,} rows")

    # =========================================================
    # 결과 확인
    # =========================================================
    print(f"\n{'='*70}")
    print(f"데이터 확인")
    print(f"{'='*70}")
    print(f"Shape: {df_diseases.shape[0]:,} rows, {df_diseases.shape[1]} columns")
    print(f"Columns: {list(df_diseases.columns)}")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    disease_file = os.path.join(output_dir, "disease.csv")

    df_diseases.to_csv(disease_file, index=False)
    print(f"[저장 완료] {disease_file} ({len(df_diseases):,} rows)")

    print(f"\n{'='*70}")
    print(f"모든 작업 완료!")
    print(f"{'='*70}")

    return df_diseases


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from paths import RAW_CHEMBL_DB, PROC_CHEMBL

    RAW_DB = str(RAW_CHEMBL_DB)
    PROCESSED_DIR = str(PROC_CHEMBL / "disease")

    # 데이터 추출 및 저장
    df_diseases = extract_chembl_diseases(RAW_DB, PROCESSED_DIR)

    if df_diseases is not None:
        print("\n--- Data Preview ---")
        print(df_diseases.head())
