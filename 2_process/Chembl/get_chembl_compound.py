import sqlite3
import pandas as pd
import numpy as np
import os


def extract_chembl_compounds(db_path, output_dir):
    """
    ChEMBL 데이터베이스에서 화합물 정보를 추출합니다.

    Parameters:
    -----------
    db_path : str
        ChEMBL SQLite 데이터베이스 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    tuple: (df_compounds, df_synonyms)
    """

    if not os.path.exists(db_path):
        print(f" 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print(f" ChEMBL 데이터베이스를 먼저 다운로드해주세요.")
        return None, None

    print(f"\n{'='*70}")
    print(f"ChEMBL Compound 정보 추출 시작")
    print(f"{'='*70}")
    print(f"데이터베이스: {db_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(db_path)

    # =========================================================
    # 1. 화합물 정보 추출 (구조 정보 포함)
    # =========================================================
    query_main = """
        SELECT
            md.chembl_id AS chembl_id,
            md.pref_name AS name,
            md.max_phase AS max_phase,
            md.first_approval AS first_approval,
            cs.canonical_smiles AS smiles,
            cs.standard_inchi_key AS inchi_key
        FROM
            MOLECULE_DICTIONARY md
        LEFT JOIN
            COMPOUND_STRUCTURES cs ON md.molregno = cs.molregno
    """

    print("\n1. 화합물 정보 추출 중...")
    df_compounds = pd.read_sql_query(query_main, conn)

    # =========================================================
    # 2. 동의어(Synonyms) 정보 추출
    # =========================================================
    query_synonyms = """
        SELECT
            md.chembl_id AS chembl_id,
            ms.synonyms AS synonym,
            ms.syn_type AS synonym_type
        FROM
            MOLECULE_DICTIONARY md
        JOIN
            MOLECULE_SYNONYMS ms ON md.molregno = ms.molregno
        WHERE
            md.chembl_id IS NOT NULL
    """

    print("2. 동의어(Synonyms) 정보 추출 중...")
    df_synonyms = pd.read_sql_query(query_synonyms, conn)

    conn.close()

    # =========================================================
    # 데이터 전처리
    # =========================================================
    df_compounds = df_compounds.replace({np.nan: None})
    df_synonyms = df_synonyms.replace({np.nan: None})

    print(f"\n{'='*70}")
    print(f"추출 완료")
    print(f"{'='*70}")
    print(f"화합물 테이블: {df_compounds.shape[0]:,} rows, {df_compounds.shape[1]} columns")
    print(f"  - Columns: {list(df_compounds.columns)}")
    print(f"  - 구조 정보 있음: SMILES={df_compounds['smiles'].notna().sum():,}, InChI={df_compounds['inchi_key'].notna().sum():,}")

    print(f"\n동의어 테이블: {df_synonyms.shape[0]:,} rows, {df_synonyms.shape[1]} columns")
    print(f"  - Columns: {list(df_synonyms.columns)}")
    print(f"  - 고유 화합물 수: {df_synonyms['chembl_id'].nunique():,}")
    print(f"  - 동의어 타입: {df_synonyms['synonym_type'].unique().tolist()}")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    compounds_file = os.path.join(output_dir, "compounds.csv")
    synonyms_file = os.path.join(output_dir, "compound_synonyms.csv")

    df_compounds.to_csv(compounds_file, index=False)
    print(f"[저장 완료] {compounds_file} ({len(df_compounds):,} rows)")

    df_synonyms.to_csv(synonyms_file, index=False)
    print(f"[저장 완료] {synonyms_file} ({len(df_synonyms):,} rows)")

    print(f"\n{'='*70}")
    print(f"모든 작업 완료!")
    print(f"{'='*70}")

    return df_compounds, df_synonyms


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from paths import RAW_CHEMBL_DB, PROC_CHEMBL

    RAW_DB = str(RAW_CHEMBL_DB)
    PROCESSED_DIR = str(PROC_CHEMBL / "compound")

    # 데이터 추출 및 저장
    df_compounds, df_synonyms = extract_chembl_compounds(RAW_DB, PROCESSED_DIR)

    if df_compounds is not None:
        print("\n--- Compounds Preview ---")
        print(df_compounds.head())
        print("\n--- Synonyms Preview ---")
        print(df_synonyms.head())
