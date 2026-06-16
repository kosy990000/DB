# 🧬 생물정보학 지식그래프 DB

ChEMBL · DrugBank · KEGG · GO · PubChem · Reactome · UniProt · NCBI 데이터를
수집(download) → 가공(process) → 적재(load) 3단계 파이프라인으로 통합 SQLite DB를 구축.

> 코드 위치: `/data/project/shinyoung/DB` · 실행 환경: conda `DB`

---

## 1. 데이터 소스 & 버전

| 소스 | 버전 | 내용 | 다운로드 방식 |
|------|------|------|--------------|
| ChEMBL | v36 | 화합물·타겟·질병·bioactivity (SQLite, ~28GB) | EBI FTP tarball |
| DrugBank | 최신 | 약물·타겟 관계 (XML) | 계정 인증 필요 |
| KEGG | REST API | pathway·유전자 네트워크 (hsa, mmu) | KEGG REST |
| GO | go-basic.obo + GOA | Gene Ontology 그래프 + 유전자 주석 | OBO / current.geneontology |
| PubChem | FTP | 화합물 1.2억개 (~48GB) | NCBI FTP |
| Reactome | All_Levels | NCBI 유전자–pathway 매핑 | reactome.org |
| UniProt | FTP idmapping | Protein ID 매핑 (human, mouse) | UniProt FTP |
| NCBI | gene_info | 유전자 정보 (human, mouse) | NCBI FTP |
| Common | — | Taxonomy (taxon 기준 테이블) | — |

---

## 2. DB 테이블 현황 (총 31개 테이블)

### ChEMBL
| 테이블 | row 수 |
|--------|--------|
| chembl_compounds | 2,878,135 |
| chembl_drug_target_relations | 24,267,312 |
| chembl_drug_disease_relations | 55,025 |
| chembl_targets | 17,803 |
| chembl_diseases | 2,178 |
| chembl_synonyms | 132,937 |
| chembl_target_synonyms | 146,355 |
| chembl_target_uniprot_mappings | 16,675 |

### PubChem
| 테이블 | row 수 |
|--------|--------|
| pubchem_compounds | 123,429,971 |
| pubchem_compound_synonyms | 114,675,840 |

### KEGG
| 테이블 | row 수 |
|--------|--------|
| kegg_pathway | 734 |
| kegg_genes | 50,809 |
| kegg_compounds | 19,569 |
| kegg_nodes | 75,861 |
| kegg_edges | 43,139 |
| kegg_gene_synonyms | 166,044 |
| kegg_compound_synonyms | 33,246 |
| kegg_gene_group_members | 25,885 |

### NCBI / UniProt / GO / Reactome / DrugBank / Common
| 테이블 | row 수 |
|--------|--------|
| ncbi_info | 305,974 |
| ncbi_synonyms | 150,879 |
| ncbi_ensembl | 73,400 |
| uniprot | 248,430 |
| go_terms | 39,353 |
| go_hierarchy | 74,751 |
| go_genes | 789,726 |
| reactome_pathway | 4,635 |
| reactome_pathway_genes | 239,477 |
| drugbank_drugs | 17,430 |
| drugbank_targets | 4,917 |
| drugbank_drug_target_relations | 22,801 |
| taxon | 542 |

> 기준일: 2026-05-02 (reactome·chembl·ncbi·go 등 최근 재확인 시 수치 일치)

---

## 3. 파이프라인 구조 (3단계)

```
raw 데이터  →  [1_download]  →  raw/
processed   →  [2_process]   →  processed/  (정형 CSV)
DB          →  [3_load]      →  database/database.db
```

| 단계 | 디렉터리 | 역할 | 일괄 실행 |
|------|----------|------|-----------|
| 1. 다운로드 | `1_download/` | 외부 API/FTP에서 원본 수집 | `download_all.py` |
| 2. 가공 | `2_process/` | 원본 → 정형 CSV 변환 | `process_all.py` |
| 3. 적재 | `3_load/` | CSV → SQLite DB | `load_all.py` |
| 전체 | (루트) | 1→2→3 한 번에 | `run_pipeline.py` |

**핵심 설계**
- 경로는 `config.yaml` → `paths.py`로 중앙 관리 (스크립트는 import만)
- 공통 다운로드 헬퍼 `_common.py`: 진행률·중단 resume·skip-if-exists·gunzip/tar
- 적재 순서: schema → taxon(FK 기준) → 독립 소스 → PubChem(대용량, 마지막)
- SQLite 동시 쓰기 미지원 → 적재는 순차 실행

---

## 4. 실행 방법

```bash
conda activate DB   # 또는 conda run -n DB ...

# 전체 파이프라인 (가벼운 소스만)
python run_pipeline.py

# ChEMBL(~30GB) + PubChem(~48GB) 포함 전체
python run_pipeline.py --all

# 특정 단계만
python run_pipeline.py --from 2      # 2단계부터
python run_pipeline.py --stage 3     # 적재만

# 단계별 개별 실행
python 1_download/download_all.py            # 다운로드
python 2_process/process_all.py              # 가공
python 3_load/load_all.py                    # 적재

# 단계별 스텝 목록 확인
python 3_load/load_all.py --list
```

**DrugBank만 별도 인증 필요**
```bash
export DRUGBANK_EMAIL="you@example.com"
export DRUGBANK_PASSWORD="..."
```

---

## 5. 주의사항

- **대용량**: ChEMBL ~30GB, PubChem ~48GB — 디스크 여유 공간 확인 후 `--all`
- **DrugBank**: 익명 다운로드 불가, 계정/라이선스 필요
- **버전 고정**: ChEMBL은 `chembl_36`으로 고정 — 버전 변경 시 `download_chembl.py`의 `RELEASE`와 `config.yaml` 동시 수정
- **재실행 안전**: 다운로드는 skip-if-exists, 적재는 소스별 clear 후 재적재(idempotent)
