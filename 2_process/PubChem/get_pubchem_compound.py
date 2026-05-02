import pandas as pd
import numpy as np
import os


def extract_pubchem_compounds(raw_dir, output_dir):
    """
    PubChem 원본 데이터에서 화합물 정보를 추출합니다.

    Parameters:
    -----------
    raw_dir : str
        PubChem 원본 데이터 디렉토리 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리

    Returns:
    --------
    tuple: (df_compounds, df_synonyms)
    """

    print(f"\n{'='*70}")
    print(f"PubChem Compound 정보 추출 시작")
    print(f"{'='*70}")
    print(f"원본 데이터: {raw_dir}")
    print(f"출력 디렉토리: {output_dir}")

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # =========================================================
    # 1. 원본 파일 로드
    # =========================================================
    print("\n1. 원본 파일 로드 중...")

    # InChI Key 파일
    print("   - CID-InChI-Key 로드 중...")
    df_inchi = pd.read_csv(
        os.path.join(raw_dir, "CID-InChI-Key"),
        sep='\t',
        names=['cid', 'inchi', 'inchi_key'],
        usecols=['cid', 'inchi_key'],
        index_col='cid',
        dtype={'cid': str},
        low_memory=False
    )
    print(f"      로드 완료: {len(df_inchi):,} rows")

    # SMILES 파일
    print("   - CID-SMILES 로드 중...")
    df_smiles = pd.read_csv(
        os.path.join(raw_dir, "CID-SMILES"),
        sep='\t',
        names=['cid', 'smiles'],
        index_col='cid',
        dtype={'cid': str},
        low_memory=False
    )
    print(f"      로드 완료: {len(df_smiles):,} rows")

    # Title 파일
    print("   - CID-Title 로드 중...")
    df_title = pd.read_csv(
        os.path.join(raw_dir, "CID-Title"),
        sep='\t',
        names=['cid', 'title'],
        index_col='cid',
        dtype={'cid': str},
        low_memory=False
    )
    print(f"      로드 완료: {len(df_title):,} rows")

    # =========================================================
    # 2. Full Outer Join으로 통합
    # =========================================================
    print("\n2. 데이터 통합 중 (Full Outer Join)...")
    df_compounds = df_inchi.join([df_smiles, df_title], how='outer')

    # NaN 처리
    df_compounds = df_compounds.replace({np.nan: None})

    # 인덱스를 컬럼으로 변경
    df_compounds = df_compounds.reset_index()

    print(f"   통합 완료: {len(df_compounds):,} rows")

    # =========================================================
    # 3. Synonyms 로드
    # =========================================================
    print("\n3. Synonyms 로드 중...")
    df_synonyms = pd.read_csv(
        os.path.join(raw_dir, "CID-Synonym-filtered"),
        sep='\t',
        names=['cid', 'synonym'],
        header=None,
        dtype={'cid': str, 'synonym': str},
        low_memory=False
    )

    # NaN 처리
    df_synonyms = df_synonyms.replace({np.nan: None})

    print(f"   로드 완료: {len(df_synonyms):,} rows")

    # =========================================================
    # 통계 정보 출력
    # =========================================================
    print(f"\n{'='*70}")
    print(f"추출 완료")
    print(f"{'='*70}")

    print(f"\n화합물 테이블: {df_compounds.shape[0]:,} rows, {df_compounds.shape[1]} columns")
    print(f"  - Columns: {list(df_compounds.columns)}")
    print(f"  - 고유 CID 수: {df_compounds['cid'].nunique():,}")

    # Null 통계
    print(f"\n  Null 통계:")
    for col in df_compounds.columns:
        null_count = df_compounds[col].isna().sum()
        null_pct = (null_count / len(df_compounds)) * 100
        print(f"    {col:15s}: {null_count:10,} ({null_pct:5.2f}%)")

    print(f"\nSynonyms 테이블: {df_synonyms.shape[0]:,} rows, {df_synonyms.shape[1]} columns")
    print(f"  - Columns: {list(df_synonyms.columns)}")
    print(f"  - 고유 CID 수: {df_synonyms['cid'].nunique():,}")
    print(f"  - CID당 평균 synonym: {len(df_synonyms) / df_synonyms['cid'].nunique():.2f}")

    # Synonym 길이 통계
    synonym_lengths = df_synonyms['synonym'].str.len()
    print(f"\n  Synonym 길이 통계:")
    print(f"    평균: {synonym_lengths.mean():.1f} 문자")
    print(f"    최소: {synonym_lengths.min()} 문자")
    print(f"    최대: {synonym_lengths.max()} 문자")
    print(f"    중앙값: {synonym_lengths.median():.0f} 문자")

    # =========================================================
    # 파일 저장
    # =========================================================
    print(f"\n파일 저장 중...")

    compounds_file = os.path.join(output_dir, "pubchem_compounds.csv")
    synonyms_file = os.path.join(output_dir, "pubchem_synonyms.csv")

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
    from paths import RAW_PUBCHEM, PROC_PUBCHEM

    RAW_DIR = str(RAW_PUBCHEM)
    PROCESSED_DIR = str(PROC_PUBCHEM)

    # 데이터 추출 및 저장
    df_compounds, df_synonyms = extract_pubchem_compounds(RAW_DIR, PROCESSED_DIR)

    if df_compounds is not None:
        print("\n--- Compounds Preview ---")
        print(df_compounds.head(10))

        print("\n--- Synonyms Preview (CID=1) ---")
        print(df_synonyms[df_synonyms['cid'] == '1'].head(10))
