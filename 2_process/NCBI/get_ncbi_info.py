import pandas as pd
import numpy as np
import sys
import os
import urllib.request

def download_ncbi_gene_info(raw_file_path):
    """
    NCBI gene_info.gz 파일을 다운로드합니다.

    Parameters:
    -----------
    raw_file_path : str
        다운로드할 파일 경로
    """
    URL = "https://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"

    if not os.path.exists(raw_file_path):
        print(f"📥 '{raw_file_path}' 다운로드 중... (시간이 소요됩니다)")
        try:
            os.makedirs(os.path.dirname(raw_file_path), exist_ok=True)
            urllib.request.urlretrieve(URL, raw_file_path)
            print(" 다운로드 완료.")
        except Exception as e:
            print(f" 다운로드 실패: {e}")
            raise
    else:
        print(f" 기존 파일 '{raw_file_path}'을(를) 사용합니다.")


def process_ncbi_gene_info_integrated(raw_file_path, output_dir, target_organisms=None):
    """
    NCBI gene_info 데이터를 처리하여 여러 종의 데이터를 통합하고
    3개의 정규화된 테이블로 분리하는 함수.

    Parameters:
    -----------
    raw_file_path : str
        gene_info.gz 파일 경로
    output_dir : str
        처리된 파일을 저장할 디렉토리
    target_organisms : dict
        {tax_id (int): organism_name (str)} 형태의 딕셔너리
        예: {9606: 'Homo sapiens', 10090: 'Mus musculus'}

    Returns:
    --------
    tuple: (df_main, df_synonyms, df_ensembl)
    """

    # 기본값 설정 (Human & Mouse)
    if target_organisms is None:
        target_organisms = {
            9606: 'Homo sapiens',
            10090: 'Mus musculus'
        }

    # 타겟 Tax ID 리스트 (문자열로 변환하여 비교 준비)
    target_tax_ids = [str(tid) for tid in target_organisms.keys()]

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 출력 파일명 정의
    FILE_MAIN = "ncbi_genes.csv"
    FILE_SYNONYMS = "ncbi_synonyms.csv"
    FILE_ENSEMBL = "ncbi_ensembl.csv"

    print(f"\n{'='*70}")
    print(f"NCBI Gene Info 통합 처리 시작")
    print(f"{'='*70}")
    print(f"대상 종: {target_organisms}")
    print(f"입력 파일: {raw_file_path}")
    print("\n[출력 파일]")
    print(f"1. 메인 정보: {FILE_MAIN}")
    print(f"2. Synonyms : {FILE_SYNONYMS}")
    print(f"3. Ensembl  : {FILE_ENSEMBL}\n")

    # 데이터 읽기 (Chunk 방식)
    chunk_iter = pd.read_csv(
        raw_file_path,
        sep='\t',
        compression='gzip',
        dtype=str,
        chunksize=200000
    )

    filtered_chunks = []
    processed_rows = 0

    try:
        print("데이터 스캔 및 필터링 중...")
        for chunk in chunk_iter:
            tax_col = chunk.columns[0]  # '#tax_id' 컬럼

            # 타겟 Tax ID에 해당하는 행만 필터링
            temp_df = chunk[chunk[tax_col].isin(target_tax_ids)]

            if not temp_df.empty:
                filtered_chunks.append(temp_df)

            processed_rows += len(chunk)
            sys.stdout.write(f"\r처리된 행 수: {processed_rows:,}")
            sys.stdout.flush()

        print("\n\n데이터 병합 및 정규화 작업 시작...")

        if not filtered_chunks:
            print(f"\n⚠️ 지정된 TaxID에 대한 데이터를 찾지 못했습니다.")
            return None, None, None

        full_df = pd.concat(filtered_chunks, ignore_index=True)

        # ==========================================
        # 0. 공통 전처리
        # ==========================================
        # 필요한 원본 컬럼만 선택 (#tax_id 포함)
        cols_needed = [full_df.columns[0], 'GeneID', 'Symbol', 'description', 'type_of_gene', 'Synonyms', 'dbXrefs']
        full_df = full_df[cols_needed].copy()

        rename_map = {
            full_df.columns[0]: 'taxon_id',  # #tax_id -> taxon_id
            'GeneID': 'entrez_id',
            'Symbol': 'gene_symbol',
            'description': 'description',
            'type_of_gene': 'gene_type',
            'Synonyms': 'synonyms_raw',
            'dbXrefs': 'db_xrefs'
        }
        full_df.rename(columns=rename_map, inplace=True)
        full_df.replace('-', np.nan, inplace=True)

        # [핵심] Species 이름 매핑 추가
        # taxon_id 컬럼을 int로 변환 후 매핑 (안전하게)
        full_df['taxon_id'] = full_df['taxon_id'].astype(int)
        full_df['species'] = full_df['taxon_id'].map(target_organisms)

        # ==========================================
        # 1. FILE 1: Main Info Table
        # (entrez_id, taxon_id, species, gene_symbol...)
        # ==========================================
        df_main = full_df[[
            'entrez_id', 'taxon_id', 'species', 'gene_symbol', 'description', 'gene_type'
        ]].drop_duplicates()

        # ==========================================
        # 2. FILE 2: Synonyms Table
        # ==========================================
        print("Synonyms 분리 중...")
        df_syn_temp = full_df[['entrez_id', 'taxon_id', 'species', 'synonyms_raw']].dropna()
        df_syn_temp['synonym'] = df_syn_temp['synonyms_raw'].str.split('|')

        df_synonyms = df_syn_temp.explode('synonym')[[
            'entrez_id', 'taxon_id', 'species', 'synonym'
        ]]

        df_synonyms['synonym'] = df_synonyms['synonym'].str.strip()
        df_synonyms = df_synonyms[df_synonyms['synonym'] != '']
        df_synonyms = df_synonyms.drop_duplicates()

        # ==========================================
        # 3. FILE 3: Ensembl Map Table
        # ==========================================
        print("Ensembl ID 추출 중...")
        df_ensembl_temp = full_df[['entrez_id', 'taxon_id', 'species', 'db_xrefs']].dropna()

        # 정규표현식으로 Ensembl ID 추출
        df_ensembl_temp['ensembl_id'] = df_ensembl_temp['db_xrefs'].str.extract(r'Ensembl:(ENS[A-Z0-9]+)')

        df_ensembl = df_ensembl_temp[[
            'entrez_id', 'taxon_id', 'species', 'ensembl_id'
        ]].dropna().drop_duplicates()

        # ==========================================
        # 4. 결과 저장
        # ==========================================
        path_main = os.path.join(output_dir, FILE_MAIN)
        path_syn = os.path.join(output_dir, FILE_SYNONYMS)
        path_ens = os.path.join(output_dir, FILE_ENSEMBL)

        df_main.to_csv(path_main, index=False)
        df_synonyms.to_csv(path_syn, index=False)
        df_ensembl.to_csv(path_ens, index=False)

        print(f"\n{'='*70}")
        print(f"처리 완료 및 저장 성공")
        print(f"{'='*70}")

        print(f"1. [Main]    {path_main} ({len(df_main):,} rows)")
        print(f"2. [Synonym] {path_syn} ({len(df_synonyms):,} rows)")
        print(f"3. [Ensembl] {path_ens} ({len(df_ensembl):,} rows)")

        # 데이터 분포 출력
        print("\n[데이터 분포 - Main Table]")
        print(df_main['species'].value_counts())

        return df_main, df_synonyms, df_ensembl

    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from paths import RAW_NCBI, PROC_NCBI
    RAW_FILE = RAW_NCBI / "gene_info.gz"
    PROCESSED_DIR = str(PROC_NCBI)

    # 원하는 종들을 딕셔너리로 정의 (TaxID : 이름)
    targets = {
        9606: 'Homo sapiens',   # Human
        10090: 'Mus musculus'   # Mouse
    }

    # 1. Raw 데이터 다운로드 (없으면)
    download_ncbi_gene_info(RAW_FILE)

    # 2. 데이터 처리
    df_main, df_syn, df_ens = process_ncbi_gene_info_integrated(
        raw_file_path=RAW_FILE,
        output_dir=PROCESSED_DIR,
        target_organisms=targets
    )

    if df_main is not None:
        print("\n--- Main Table Preview ---")
        print(df_main.head())
        print(df_main.tail())
