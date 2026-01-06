import sqlite3
import pandas as pd
import numpy as np
import os


def extract_target_go(db_path, output_dir):
    """
    ChEMBL 데이터베이스에서 Target-GO term 매핑을 추출합니다.

    Parameters:
    -----------
    db_path : str
        ChEMBL SQLite 데이터베이스 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    pd.DataFrame: Target-GO term 매핑 데이터
    """

    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        print(f"   ChEMBL 데이터베이스를 먼저 다운로드해주세요.")
        return None

    print(f"\n{'='*70}")
    print(f"ChEMBL Target-GO Term 매핑 추출 시작")
    print(f"{'='*70}")
    print(f"데이터베이스: {db_path}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(db_path)

    # =========================================================
    # Target-GO term 매핑 추출
    # =========================================================
    print("\n1. Target-GO term 매핑 정보 추출 중...")

    query = """
        SELECT
            td.chembl_id as target_chembl_id,
            td.pref_name as target_name,
            td.target_type,
            td.organism,
            cgo.go_id,
            gc.pref_name as go_term,
            gc.aspect as go_aspect,
            gc.path as go_path
        FROM TARGET_DICTIONARY td
        JOIN TARGET_COMPONENTS tc ON td.tid = tc.tid
        JOIN COMPONENT_GO cgo ON tc.component_id = cgo.component_id
        LEFT JOIN GO_CLASSIFICATION gc ON cgo.go_id = gc.go_id
        ORDER BY td.chembl_id, cgo.go_id
    """

    df_target_go = pd.read_sql_query(query, conn)
    conn.close()

    # NaN 처리
    df_target_go = df_target_go.replace({np.nan: None})

    print(f"   추출된 매핑 데이터: {df_target_go.shape[0]:,} rows, {df_target_go.shape[1]} columns")

    # =========================================================
    # 통계 정보 출력
    # =========================================================
    print(f"\n{'='*70}")
    print(f"추출 완료")
    print(f"{'='*70}")
    print(f"Target-GO 매핑: {df_target_go.shape[0]:,} rows, {df_target_go.shape[1]} columns")
    print(f"  - Columns: {list(df_target_go.columns)}")
    print(f"  - 고유 Target 수: {df_target_go['target_chembl_id'].nunique():,}")
    print(f"  - 고유 GO term 수: {df_target_go['go_id'].nunique():,}")

    print(f"\n타겟당 GO term 통계:")
    go_per_target = df_target_go.groupby('target_chembl_id')['go_id'].nunique()
    print(f"  - 평균: {go_per_target.mean():.2f} GO terms/target")
    print(f"  - 중앙값: {go_per_target.median():.2f} GO terms/target")
    print(f"  - 최소: {go_per_target.min()} GO terms/target")
    print(f"  - 최대: {go_per_target.max()} GO terms/target")

    print(f"\nGO Aspect 분포:")
    aspect_counts = df_target_go['go_aspect'].value_counts()
    aspect_names = {
        'P': 'Biological Process',
        'C': 'Cellular Component',
        'F': 'Molecular Function'
    }
    for aspect, count in aspect_counts.items():
        aspect_name = aspect_names.get(aspect, aspect)
        print(f"  {aspect} ({aspect_name:20s}): {count:,}")

    print(f"\nTarget Type 분포 (상위 10개):")
    type_counts = df_target_go['target_type'].value_counts().head(10)
    for target_type, count in type_counts.items():
        print(f"  {target_type:30s}: {count:,}")

    print(f"\nOrganism 분포 (상위 10개):")
    organism_counts = df_target_go['organism'].value_counts().head(10)
    for organism, count in organism_counts.items():
        org_str = organism if organism else "None"
        print(f"  {org_str:30s}: {count:,}")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    output_file = os.path.join(output_dir, "target_go_terms.csv")
    df_target_go.to_csv(output_file, index=False)
    print(f"[저장 완료] {output_file} ({len(df_target_go):,} rows)")

    # 추가: 간단한 요약 파일도 생성 (Target별 GO term 개수)
    summary_file = os.path.join(output_dir, "target_go_summary.csv")
    df_summary = df_target_go.groupby(['target_chembl_id', 'target_name', 'target_type', 'organism']).agg({
        'go_id': 'count'
    }).reset_index()
    df_summary.columns = ['target_chembl_id', 'target_name', 'target_type', 'organism', 'go_term_count']
    df_summary = df_summary.sort_values('go_term_count', ascending=False)
    df_summary.to_csv(summary_file, index=False)
    print(f"[저장 완료] {summary_file} ({len(df_summary):,} rows)")

    print(f"\n{'='*70}")
    print(f"모든 작업 완료!")
    print(f"{'='*70}")

    return df_target_go


if __name__ == "__main__":
    # 경로 설정 (스크립트 위치 기준 상대경로)
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_ROOT = os.path.join(SCRIPT_DIR, "../..")

    RAW_DB = os.path.join(DB_ROOT, "raw/chembl/chembl_36/chembl_36_sqlite/chembl_36.db")
    PROCESSED_DIR = os.path.join(DB_ROOT, "processed/Chembl/target-go")

    # 데이터 추출 및 저장
    df_target_go = extract_target_go(RAW_DB, PROCESSED_DIR)

    if df_target_go is not None:
        print("\n--- Target-GO Preview ---")
        print(df_target_go.head(15))

        print("\n--- GO term이 가장 많은 Target TOP 10 ---")
        top_targets = df_target_go.groupby(['target_chembl_id', 'target_name', 'organism']).size().reset_index(name='go_count')
        top_targets = top_targets.sort_values('go_count', ascending=False).head(10)
        print(top_targets.to_string(index=False))
