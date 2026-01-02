import pandas as pd
import gzip
import urllib.request
import os

def get_uniprot_mapping(
    url: str,
    file_path: str,
    target_type: str = 'Gene_Name',
    output_col_name: str = 'gene_symbol',
    taxon_id: int = None,
    organism_name: str = None
) -> pd.DataFrame:
    """
    UniProt ID 매핑 데이터를 다운로드하고 특정 ID 타입만 필터링하여 반환합니다.

    Args:
        url (str): 데이터 다운로드 URL
        file_path (str): 저장할 로컬 파일 경로 (gz 포함)
        target_type (str): 필터링할 ID 타입 (예: 'Gene_Name', 'Ensembl' 등)
        output_col_name (str): 결과 데이터프레임의 타겟 컬럼명 변경값
        taxon_id (int): NCBI Taxonomy ID (예: 9606, 10090)
        organism_name (str): 생물종 이름 (예: 'Homo sapiens', 'Mus musculus')

    Returns:
        pd.DataFrame: ['uniprot_id', output_col_name, 'taxon_id', 'species'] 컬럼을 가진 데이터프레임
    """

    # 1. 파일 다운로드 (없을 경우에만)
    if not os.path.exists(file_path):
        print(f" '{file_path}' 다운로드 중... (시간이 소요됩니다)")
        try:
            urllib.request.urlretrieve(url, file_path)
            print("다운로드 완료.")
        except Exception as e:
            print(f" 다운로드 실패: {e}")
            return pd.DataFrame()
    else:
        print(f"기존 파일 '{file_path}'을(를) 사용합니다.")

    # 2. 데이터 로드 및 필터링
    print(f"'{target_type}' 데이터 처리 중...")
    chunk_size = 100_000
    results = []

    try:
        with gzip.open(file_path, 'rt') as f:
            # 필요한 컬럼만 지정하여 읽기
            reader = pd.read_csv(
                f,
                sep='\t',
                header=None,
                names=['UniProtID', 'Type', 'Value'],
                chunksize=chunk_size
            )

            for chunk in reader:
                # 조건에 맞는 행만 추출 (메모리 절약)
                subset = chunk.loc[chunk['Type'] == target_type, ['UniProtID', 'Value']]
                results.append(subset)

    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return pd.DataFrame()

    # 3. 결과 병합 및 정리
    if results:
        df_final = pd.concat(results, ignore_index=True)

        # 컬럼 이름 변경 (사용자가 지정한 이름으로)
        df_final.columns = ['uniprot_id', output_col_name]

        # 중복 제거
        df_final.drop_duplicates(inplace=True)

        # taxon_id와 species 컬럼 추가
        if taxon_id is not None:
            df_final['taxon_id'] = taxon_id
        if organism_name is not None:
            df_final['species'] = organism_name

        print(f"✅ 처리 완료: {len(df_final)}개 매핑 발견")
        return df_final
    else:
        print("⚠️ 해당 타입의 데이터가 없습니다.")
        return pd.DataFrame()


if __name__ == "__main__":
    # ==========================================
    # 실행: Human과 Mouse 데이터 다운로드 및 처리
    # ==========================================

    # 경로 설정
    RAW_DIR = "/data/project/shinyoung/DB/raw/uniprot"  # raw 데이터 저장
    PROCESSED_DIR = "/data/project/shinyoung/DB/processed/Uniprot"  # 처리된 데이터 저장

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Human 데이터
    HUMAN_URL = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz"
    HUMAN_FILE = f"{RAW_DIR}/HUMAN_9606_idmapping.dat.gz"

    # Mouse 데이터
    MOUSE_URL = "https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/MOUSE_10090_idmapping.dat.gz"
    MOUSE_FILE = f"{RAW_DIR}/MOUSE_10090_idmapping.dat.gz"

    print("="*60)
    print("Human 데이터 처리")
    print("="*60)
    df_human = get_uniprot_mapping(
        HUMAN_URL, HUMAN_FILE,
        target_type='Gene_Name',
        output_col_name='gene_symbol',
        taxon_id=9606,
        organism_name='Homo sapiens'
    )
    print(f"\n[Human 데이터 미리보기]")
    print(df_human.head())

    print("\n" + "="*60)
    print("Mouse 데이터 처리")
    print("="*60)
    df_mouse = get_uniprot_mapping(
        MOUSE_URL, MOUSE_FILE,
        target_type='Gene_Name',
        output_col_name='gene_symbol',
        taxon_id=10090,
        organism_name='Mus musculus'
    )
    print(f"\n[Mouse 데이터 미리보기]")
    print(df_mouse.head())

    # ==========================================
    # 데이터 통합 (Human + Mouse)
    # ==========================================
    print("\n" + "="*60)
    print("데이터 통합 중...")
    print("="*60)

    df_integrated = pd.concat([df_human, df_mouse], ignore_index=True)

    print(f"✅ 통합 완료!")
    print(f"총 행 수: {len(df_integrated):,}개")
    print(f"컬럼 목록: {list(df_integrated.columns)}")

    print("\n[종별 데이터 분포]")
    print(df_integrated['species'].value_counts())

    # 파일 저장
    OUTPUT_FILE = f"{PROCESSED_DIR}/uniprot_data_mouse_human.csv"
    df_integrated.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 저장 완료: {OUTPUT_FILE}")

    print("\n[통합 데이터 미리보기]")
    print(df_integrated.head())
    print("...")
    print(df_integrated.tail())
