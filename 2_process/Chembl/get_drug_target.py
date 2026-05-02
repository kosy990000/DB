import sqlite3
import pandas as pd
import numpy as np
import os


def extract_drug_target_interactions(db_path, output_dir):
    """
    ChEMBL 데이터베이스에서 Drug-Target 상호작용 데이터를 추출합니다.

    Parameters:
    -----------
    db_path : str
        ChEMBL SQLite 데이터베이스 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    df_interactions: DataFrame
    """

    if not os.path.exists(db_path):
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print(f"ChEMBL 데이터베이스를 먼저 다운로드해주세요.")
        return None

    print(f"\n{'='*70}")
    print(f"ChEMBL Drug-Target Interaction 정보 추출 시작")
    print(f"{'='*70}")
    print(f"데이터베이스: {db_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(db_path)

    # =========================================================
    # Drug-Target Bioactivity 데이터 추출
    # =========================================================
    print("\nDrug-Target Bioactivity 데이터 추출 중...")
    print("(이 작업은 시간이 오래 걸릴 수 있습니다...)")

    query_interactions = """
        SELECT
            -- [Drug 정보]
            md.chembl_id AS drug_chembl_id,

            -- [Target 정보]
            td.chembl_id AS target_chembl_id,

            -- [Interaction (Label) 정보]
            act.standard_type AS standard_type,
            act.standard_relation AS standard_relation,
            act.standard_value AS standard_value,
            act.standard_units AS standard_units,
            act.pchembl_value AS pchembl_value,

            -- [메타 데이터]
            ass.confidence_score AS confidence_score,
            ass.description AS assay_description

        FROM
            ACTIVITIES act
        JOIN
            ASSAYS ass ON act.assay_id = ass.assay_id
        JOIN
            TARGET_DICTIONARY td ON ass.tid = td.tid
        JOIN
            MOLECULE_DICTIONARY md ON act.molregno = md.molregno

        WHERE
            md.chembl_id IS NOT NULL
            AND td.chembl_id IS NOT NULL
    """

    df_interactions = pd.read_sql_query(query_interactions, conn)
    df_interactions = df_interactions.replace({np.nan: None})

    conn.close()

    print(f"추출 완료: {len(df_interactions):,} rows")
    print(f"고유 약물 수: {df_interactions['drug_chembl_id'].nunique():,}")
    print(f"고유 타겟 수: {df_interactions['target_chembl_id'].nunique():,}")

    # =========================================================
    # 결과 확인
    # =========================================================
    print(f"\n{'='*70}")
    print(f"데이터 확인")
    print(f"{'='*70}")
    print(f"Shape: {df_interactions.shape[0]:,} rows, {df_interactions.shape[1]} columns")
    print(f"Columns: {list(df_interactions.columns)}")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    interactions_file = os.path.join(output_dir, "compound-target.csv")

    df_interactions.to_csv(interactions_file, index=False)
    print(f"[저장 완료] {interactions_file} ({len(df_interactions):,} rows)")

    print(f"\n{'='*70}")
    print(f"모든 작업 완료!")
    print(f"{'='*70}")

    return df_interactions


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from paths import RAW_CHEMBL_DB, PROC_CHEMBL

    RAW_DB = str(RAW_CHEMBL_DB)
    PROCESSED_DIR = str(PROC_CHEMBL / "compound-target")

    # 데이터 추출 및 저장
    df_interactions = extract_drug_target_interactions(RAW_DB, PROCESSED_DIR)

    if df_interactions is not None:
        print("\n--- Data Preview ---")
        print(df_interactions.head())
