# DB

생물정보학 지식 그래프 DB 구축 프로젝트.
ChEMBL, DrugBank, KEGG, GO, PubChem, Reactome, UniProt, NCBI 데이터를 수집·가공해 통합 DB로 적재한다.

---

## 프로젝트 구조

```
DB/
├── config.yaml          # 모든 raw/processed 경로 중앙 관리
├── paths.py             # config.yaml 로드 → Path 객체 제공 (스크립트에서 import)
│
├── 1_download/          # 외부 API / FTP에서 원본 데이터 다운로드
│   ├── _common.py                 # 공통 다운로드 헬퍼 (progress/resume/skip)
│   ├── download_all.py            # 전체 소스 일괄 다운로드
│   ├── Chembl/        # ChEMBL SQLite tarball (~30GB)
│   ├── Drugbank/      # DrugBank XML (계정 인증 필요)
│   ├── Go/            # go-basic.obo + GOA(.gaf)
│   ├── Kegg/          # KEGG KGML + 매핑
│   ├── NCBI/          # gene_info.gz
│   ├── PubChem/       # CID-* 4종 (~48GB)
│   ├── Reactome/      # NCBI2Reactome_All_Levels.txt
│   └── Uniprot/       # HUMAN/MOUSE idmapping
│
├── 2_process/           # 원본 데이터 → 정형 CSV 변환
│   ├── Chembl/          # ChEMBL v36 SQLite 추출
│   ├── Drugbank/        # DrugBank XML 파싱
│   ├── Go/              # GO-term OBO / GOA 처리
│   ├── Gene_mapping/    # 유전자 ID 매핑 (R 스크립트)
│   ├── Kegg/            # KEGG pathway 파싱 및 정규화
│   ├── NCBI/            # NCBI gene_info 다운로드 + 처리
│   ├── PubChem/         # PubChem FTP 데이터 처리
│   ├── Reactome/        # Reactome 경로-유전자 매핑
│   └── Uniprot/         # UniProt ID 매핑 다운로드 + 처리
│
├── 3_load/              # 처리된 CSV → DB 적재
│   ├── schema/          # 스키마 생성 SQL
│   ├── Chembl/          # ChEMBL import
│   ├── Drugbank/        # DrugBank import
│   ├── Go/              # GO import
│   ├── Kegg/            # KEGG import
│   ├── NCBI/            # NCBI import
│   ├── PubChem/         # PubChem import
│   ├── Reactome/        # Reactome import
│   ├── Uniprot/         # UniProt import
│   └── query/           # 조회 유틸리티
│
├── raw/                 # 원본 데이터 (git 미포함)
│   ├── Chembl/
│   ├── Drugbank/
│   ├── Go/
│   ├── Kegg/
│   ├── NCBI/
│   ├── PubChem/
│   ├── Reactome/
│   └── Uniprot/
│
├── processed/           # 가공된 CSV (git 미포함)
│   ├── Chembl/
│   ├── Drugbank/
│   ├── Gene_mapping/
│   ├── Go/
│   ├── Kegg/
│   ├── NCBI/
│   ├── PubChem/
│   ├── Reactome/
│   └── Uniprot/
│
└── database/            # 최종 DB 파일
```

---

## 빠른 시작

### 환경
```bash
# conda
conda env create -f environment.yml
conda activate DB

# 또는 Docker
docker build -t db .
docker run --rm -it -v $PWD:/work db
```

### 경로 설정 확인
```bash
conda run -n DB python3 -c "from paths import *; print(RAW_CHEMBL_DB)"
```

### 스크립트 실행 (프로젝트 루트에서)
```bash
# 1. 데이터 다운로드 (전체 일괄, ChEMBL/PubChem 제외)
conda run -n DB python3 1_download/download_all.py
# 무거운 소스까지: --all / 특정 소스만: download_all.py go reactome
# 자세한 내용은 1_download/README.md 참고

# 2. 데이터 처리
conda run -n DB python3 2_process/Kegg/normalize_kegg_mapping.py
conda run -n DB python3 2_process/Chembl/get_chembl_compound.py

# 3. DB 적재 (순서 중요: taxon 먼저, PubChem 마지막)
conda run -n DB python3 3_load/schema/create_schema.py
conda run -n DB python3 3_load/Common/import_taxon_to_db.py
conda run -n DB python3 3_load/Chembl/import_chembl_to_db.py
```

> 적재 전체 순서는 `3_load/README.md` 참고.

---

## 데이터 소스

| 소스 | 버전 | 설명 |
|------|------|------|
| 소스 | 버전 | 설명 | DB 테이블 수 |
|------|------|------|-------------|
| ChEMBL | v36 | 화합물·타겟·질병·bioactivity (SQLite, 28GB) | 8 |
| DrugBank | 최신 | 약물·타겟 관계 (XML) | 3 |
| KEGG | REST API | 경로·유전자 네트워크 (hsa, mmu) | 9 |
| GO | go-basic.obo | Gene Ontology 그래프 + GOA | 3 |
| PubChem | FTP | 화합물 1.2억개 | 2 |
| Reactome | All_Levels | 경로-유전자 매핑 | 2 |
| UniProt | FTP | Protein ID 매핑 | 1 |
| NCBI | gene_info | 유전자 정보 (Human, Mouse) | 3 |
| Common | — | Taxonomy (taxon_id 기준 테이블) | 1 |
