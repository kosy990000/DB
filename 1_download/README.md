# 1_download — 원본 데이터 다운로드

외부 API / FTP에서 원본 데이터를 `raw/`로 내려받는 단계.
모든 스크립트는 `config.yaml` → `paths.py`의 raw 경로를 사용하며, **프로젝트 루트에서** 실행한다.

---

## 파일 구조

```
1_download/
├── _common.py                  # 공통 다운로드 헬퍼 (progress/resume/skip, gunzip, tar)
├── download_all.py             # 전체 소스 일괄 다운로드 오케스트레이터
│
├── Chembl/download_chembl.py   # ChEMBL SQLite tarball (~30GB, [heavy])
├── Drugbank/download_drugbank.py # DrugBank XML (계정 인증 필요)
├── Go/download_go.py           # go-basic.obo + goa_human.gaf + mgi.gaf
├── Kegg/download_mapping.py    # KEGG 유전자/화합물 매핑
├── Kegg/download_kgml.py       # KEGG KGML pathway 파일
├── NCBI/download_ncbi.py       # gene_info.gz
├── PubChem/download_pubchem.py # CID-InChI-Key/SMILES/Title/Synonym (~48GB, [heavy])
├── Reactome/download_reactome.py # NCBI2Reactome_All_Levels.txt
└── Uniprot/download_uniprot.py # HUMAN/MOUSE idmapping.dat.gz
```

---

## 빠른 시작

```bash
conda activate kg_env   # 또는 conda run -n kg_env ...

# 가벼운 소스 전체 (ChEMBL/PubChem 제외)
python 1_download/download_all.py

# 무거운 소스까지 전부
python 1_download/download_all.py --all

# 특정 소스만
python 1_download/download_all.py go reactome ncbi

# 소스 목록 보기
python 1_download/download_all.py --list
```

개별 실행도 가능:
```bash
python 1_download/Go/download_go.py
python 1_download/Reactome/download_reactome.py
```

---

## 소스별 메모

| 소스 | 산출물 (raw/) | 비고 |
|------|--------------|------|
| ChEMBL | `Chembl/chembl_36/chembl_36_sqlite/chembl_36.db` | tarball 다운로드 후 압축 해제, **~30GB** |
| DrugBank | `Drugbank/full database.xml` | **계정/라이선스 필요** (아래 참고) |
| GO | `Go/go-basic.obo`, `Go/goa_human.gaf`, `Go/mgi.gaf` | gaf는 .gz 다운로드 후 해제 |
| KEGG | `Kegg/kegg-mapping`, `Kegg/kgml_hsa`, `Kegg/kgml_mmu` | REST API |
| NCBI | `NCBI/gene_info.gz` | gz 그대로 사용 |
| PubChem | `PubChem/CID-*` 4종 | .gz 다운로드 후 해제, **~48GB** |
| Reactome | `Reactome/NCBI2Reactome_All_Levels.txt` | 평문 |
| UniProt | `Uniprot/HUMAN_9606_idmapping.dat.gz`, `Uniprot/MOUSE_10090_idmapping.dat.gz` | gz 그대로 사용 |

### DrugBank 인증
DrugBank XML은 익명 다운로드가 불가능하다. 계정 자격증명을 환경변수로 주거나 수동 배치한다.
```bash
export DRUGBANK_EMAIL="you@example.com"
export DRUGBANK_PASSWORD="..."
python 1_download/Drugbank/download_drugbank.py
```

---

## 동작 특징 (`_common.py`)

- **resume**: 중단 시 `.part` 파일에서 이어받기 (서버가 Range 지원 시)
- **skip-if-exists**: 최종 파일이 이미 있으면 건너뜀 → 재실행 안전
- **progress**: 1초 간격 진행률 출력
- **무결성**: `.part`로 받은 뒤 완료 시에만 최종 파일명으로 rename

> 대용량(ChEMBL/PubChem)은 디스크 여유 공간을 먼저 확인할 것.
