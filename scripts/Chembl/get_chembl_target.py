import sqlite3
import pandas as pd
import numpy as np
import os


def extract_chembl_targets(db_path, output_dir):
    """
    ChEMBL 데이터베이스에서 타겟 정보를 추출합니다.

    Parameters:
    -----------
    db_path : str
        ChEMBL SQLite 데이터베이스 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    tuple: (df_targets, df_synonyms)
    """

    if not os.path.exists(db_path):
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print(f"ChEMBL 데이터베이스를 먼저 다운로드해주세요.")
        return None, None

    print(f"\n{'='*70}")
    print(f"ChEMBL Target 정보 추출 시작")
    print(f"{'='*70}")
    print(f"데이터베이스: {db_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(db_path)

    # =========================================================
    # 1. 타겟 정보 추출
    # =========================================================
    query_targets = """
        SELECT DISTINCT
            td.chembl_id AS target_chembl_id,
            td.pref_name AS target_name,
            td.target_type AS target_type,
            td.organism AS species,
            cs.accession AS uniprot_id
        FROM
            TARGET_DICTIONARY td
        LEFT JOIN
            TARGET_COMPONENTS tc ON td.tid = tc.tid
        LEFT JOIN
            COMPONENT_SEQUENCES cs ON tc.component_id = cs.component_id
        WHERE
            td.chembl_id IS NOT NULL
    """

    print("\n1. 타겟 정보 추출 중...")
    df_targets = pd.read_sql_query(query_targets, conn)

    # =========================================================
    # 2. 타겟 동의어(Synonyms) 정보 추출
    # =========================================================
    query_synonyms = """
        SELECT
            td.chembl_id AS target_chembl_id,
            TRIM(REPLACE(syn.component_synonym, '"', '')) AS synonym,
            syn.syn_type AS synonym_type
        FROM
            TARGET_DICTIONARY td
        JOIN
            TARGET_COMPONENTS tc ON td.tid = tc.tid
        JOIN
            COMPONENT_SYNONYMS syn ON tc.component_id = syn.component_id
        WHERE
            td.chembl_id IS NOT NULL
            AND syn.component_synonym IS NOT NULL
    """

    print("2. 타겟 동의어(Synonyms) 정보 추출 중...")
    df_synonyms = pd.read_sql_query(query_synonyms, conn)

    conn.close()

    # =========================================================
    # 데이터 전처리
    # =========================================================
    df_targets = df_targets.replace({np.nan: None})
    df_synonyms = df_synonyms.replace({np.nan: None})

    print(f"\n{'='*70}")
    print(f"추출 완료")
    print(f"{'='*70}")
    print(f"타겟 테이블: {df_targets.shape[0]:,} rows, {df_targets.shape[1]} columns")
    print(f"  - Columns: {list(df_targets.columns)}")
    print(f"  - UniProt ID 있음: {df_targets['uniprot_id'].notna().sum():,}")
    print(f"  - Target Types: {df_targets['target_type'].unique().tolist()[:10]}")

    print(f"\n동의어 테이블: {df_synonyms.shape[0]:,} rows, {df_synonyms.shape[1]} columns")
    print(f"  - Columns: {list(df_synonyms.columns)}")
    print(f"  - 고유 타겟 수: {df_synonyms['target_chembl_id'].nunique():,}")
    print(f"  - 동의어 타입:")
    for syn_type, count in df_synonyms['synonym_type'].value_counts().items():
        print(f"    - {syn_type}: {count:,}")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    targets_file = os.path.join(output_dir, "targets.csv")
    synonyms_file = os.path.join(output_dir, "target_synonyms.csv")

    df_targets.to_csv(targets_file, index=False)
    print(f"[저장 완료] {targets_file} ({len(df_targets):,} rows)")

    df_synonyms.to_csv(synonyms_file, index=False)
    print(f"[저장 완료] {synonyms_file} ({len(df_synonyms):,} rows)")

    print(f"\n{'='*70}")
    print(f"모든 작업 완료!")
    print(f"{'='*70}")

    return df_targets, df_synonyms


if __name__ == "__main__":
    # 경로 설정 (스크립트 위치 기준 상대경로)
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_ROOT = os.path.join(SCRIPT_DIR, "../..")

    RAW_DB = os.path.join(DB_ROOT, "raw/chembl/chembl_36/chembl_36_sqlite/chembl_36.db")
    PROCESSED_DIR = os.path.join(DB_ROOT, "processed/Chembl/target")

    # 데이터 추출 및 저장
    df_targets, df_synonyms = extract_chembl_targets(RAW_DB, PROCESSED_DIR)

    if df_targets is not None:
        print("\n--- Targets Preview ---")
        print(df_targets.head())
        print("\n--- Synonyms Preview ---")
        print(df_synonyms.head())
