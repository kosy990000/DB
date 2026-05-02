import sqlite3
import pandas as pd
import numpy as np
import os


def extract_compound_disease(db_path, output_dir):
    """
    ChEMBL 데이터베이스에서 화합물-질병 관계를 추출합니다.

    Parameters:
    -----------
    db_path : str
        ChEMBL SQLite 데이터베이스 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    pd.DataFrame: 화합물-질병 관계 데이터
    """

    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print(f"   ChEMBL 데이터베이스를 먼저 다운로드해주세요.")
        return None

    print(f"\n{'='*70}")
    print(f"ChEMBL Compound-Disease 관계 추출 시작")
    print(f"{'='*70}")
    print(f"데이터베이스: {db_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(db_path)

    # =========================================================
    # 약물-질병 적응증(Indication) 정보 추출
    # =========================================================
    print("\n1. 약물-질병 적응증(Indication) 정보 추출 중...")

    query_indication = """
        SELECT
            md.chembl_id AS drug_chembl_id,
            di.mesh_id AS mesh_id,
            di.max_phase_for_ind AS max_phase
        FROM
            MOLECULE_DICTIONARY md
        JOIN
            DRUG_INDICATION di ON md.molregno = di.molregno
        WHERE
            di.mesh_id IS NOT NULL
    """

    df_indication = pd.read_sql_query(query_indication, conn)
    conn.close()

    # NaN 처리
    df_indication = df_indication.replace({np.nan: None})

    print(f"   추출된 적응증 데이터: {df_indication.shape[0]:,} rows, {df_indication.shape[1]} columns")

    # =========================================================
    # 중복 제거 (같은 Drug-Disease 쌍에서 max_phase가 높은 것만 유지)
    # =========================================================
    print("\n2. 중복 제거 중...")
    print(f"   전략: max_phase가 높은 순서로 정렬 후 Drug-Disease 쌍 중복 제거")

    df_clean = df_indication.sort_values(by='max_phase', ascending=False).drop_duplicates(
        subset=['drug_chembl_id', 'mesh_id'],
        keep='first'
    )

    removed_count = len(df_indication) - len(df_clean)
    print(f"   제거된 중복 행 수: {removed_count:,}")
    print(f"   최종 데이터 크기: {len(df_clean):,} rows")

    # =========================================================
    # 통계 정보 출력
    # =========================================================
    print(f"\n{'='*70}")
    print(f"추출 완료")
    print(f"{'='*70}")
    print(f"화합물-질병 관계: {df_clean.shape[0]:,} rows, {df_clean.shape[1]} columns")
    print(f"  - Columns: {list(df_clean.columns)}")
    print(f"  - 고유 화합물 수: {df_clean['drug_chembl_id'].nunique():,}")
    print(f"  - 고유 질병 수: {df_clean['mesh_id'].nunique():,}")

    print(f"\nMax Phase 분포:")
    phase_counts = df_clean['max_phase'].value_counts().sort_index(ascending=False)
    for phase, count in phase_counts.items():
        phase_label = {
            4.0: "Phase 4 (Approved)",
            3.0: "Phase 3",
            2.0: "Phase 2",
            1.0: "Phase 1",
            0.5: "Phase 0.5 (Preclinical)",
            -1.0: "Phase -1 (Withdrawn)"
        }.get(phase, f"Phase {phase}")
        print(f"  {phase_label:30s}: {count:,}")

    # =========================================================
    # 희소성(Sparsity) 분석
    # =========================================================
    n_drugs = df_clean['drug_chembl_id'].nunique()
    n_diseases = df_clean['mesh_id'].nunique()
    total_elements = n_drugs * n_diseases
    n_interactions = len(df_clean)
    n_zeros = total_elements - n_interactions
    sparsity = (n_zeros / total_elements) * 100
    density = (n_interactions / total_elements) * 100

    print(f"\n희소성 분석:")
    print(f"  전체 가능한 조합 수: {total_elements:,}")
    print(f"  실제 연결된 상호작용 수: {n_interactions:,}")
    print(f"  연결되지 않은 조합 수: {n_zeros:,}")
    print(f"  📌 데이터 희소성 (Sparsity): {sparsity:.4f}%")
    print(f"  📌 데이터 밀도 (Density): {density:.4f}%")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    output_file = os.path.join(output_dir, "compound-disease_information.csv")
    df_clean.to_csv(output_file, index=False)
    print(f"[저장 완료] {output_file} ({len(df_clean):,} rows)")

    print(f"\n{'='*70}")
    print(f"모든 작업 완료!")
    print(f"{'='*70}")

    return df_clean


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from paths import RAW_CHEMBL_DB, PROC_CHEMBL

    RAW_DB = str(RAW_CHEMBL_DB)
    PROCESSED_DIR = str(PROC_CHEMBL / "compound-disease")

    # 데이터 추출 및 저장
    df_compound_disease = extract_compound_disease(RAW_DB, PROCESSED_DIR)

    if df_compound_disease is not None:
        print("\n--- Compound-Disease Preview ---")
        print(df_compound_disease.head(10))
        print("\n--- Sample by Max Phase ---")
        print(df_compound_disease.groupby('max_phase').head(2))
