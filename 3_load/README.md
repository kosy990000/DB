# 3_load — DB 적재 스크립트

처리된 CSV(`processed/`) → SQLite DB(`database/database.db`) 적재.

---

## 파일 구조

```
3_load/
├── schema/
│   ├── create_schema.py        # DB 스키마 생성 (SQL 실행)
│   └── database_schema.sql     # 전체 테이블 DDL (31 테이블)
│
├── Common/
│   └── import_taxon_to_db.py   # taxon 적재 (가장 먼저 실행)
│
├── Chembl/
│   └── import_chembl_to_db.py
├── Drugbank/
│   └── import_drugbank_to_db.py
├── Go/
│   └── import_go_to_db.py
├── Kegg/
│   └── import_kegg_to_db.py
├── NCBI/
│   └── import_ncbi_to_db.py
├── PubChem/
│   └── import_pubchem_to_db.py
├── Reactome/
│   └── import_reactome_to_db.py
└── Uniprot/
    └── import_uniprot_to_db.py
```

---

## 실행 순서

반드시 프로젝트 루트(`/data/project/shinyoung/DB/`)에서 실행.

```bash
# 0. 스키마 생성 (최초 1회 또는 스키마 변경 시)
conda run -n kg_env python3 3_load/schema/create_schema.py

# 1. Taxon (FK 기준 테이블, 가장 먼저)
conda run -n kg_env python3 3_load/Common/import_taxon_to_db.py

# 2. 독립 테이블 (순서 무관)
conda run -n kg_env python3 3_load/NCBI/import_ncbi_to_db.py
conda run -n kg_env python3 3_load/Uniprot/import_uniprot_to_db.py
conda run -n kg_env python3 3_load/Chembl/import_chembl_to_db.py
conda run -n kg_env python3 3_load/Drugbank/import_drugbank_to_db.py
conda run -n kg_env python3 3_load/Go/import_go_to_db.py
conda run -n kg_env python3 3_load/Kegg/import_kegg_to_db.py
conda run -n kg_env python3 3_load/Reactome/import_reactome_to_db.py

# 3. PubChem (데이터 크기 23GB+, 오래 걸림)
conda run -n kg_env python3 3_load/PubChem/import_pubchem_to_db.py
```

> **주의**: SQLite는 동시 쓰기를 지원하지 않음. 스크립트를 병렬 실행하면 `database is locked` 오류 발생.

---

## 경로 설정

모든 스크립트는 프로젝트 루트의 `paths.py`를 import해 경로를 사용한다.

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import DB_FILE, PROC_CHEMBL   # 소스별로 다름
```

경로 정의는 `config.yaml` → `paths.py` 순으로 관리된다.

---

## 현재 DB 상태 (2026-05-02 기준)

**파일**: `database/database.db`

| 소스 | 테이블 | 주요 row 수 |
|------|--------|------------|
| ChEMBL | chembl_compounds | 2,878,135 |
| ChEMBL | chembl_drug_target_relations | 24,267,312 |
| ChEMBL | chembl_drug_disease_relations | 55,025 |
| ChEMBL | chembl_targets | 17,803 |
| ChEMBL | chembl_diseases | 2,178 |
| ChEMBL | chembl_synonyms | 132,937 |
| ChEMBL | chembl_target_synonyms | 146,355 |
| ChEMBL | chembl_target_uniprot_mappings | 16,675 |
| DrugBank | drugbank_drugs | 17,430 |
| DrugBank | drugbank_targets | 4,917 |
| DrugBank | drugbank_drug_target_relations | 22,801 |
| PubChem | pubchem_compounds | 123,429,971 |
| PubChem | pubchem_compound_synonyms | 114,675,840 |
| KEGG | kegg_pathway | 734 |
| KEGG | kegg_genes | 50,809 |
| KEGG | kegg_compounds | 19,569 |
| KEGG | kegg_nodes | 75,861 |
| KEGG | kegg_edges | 43,139 |
| KEGG | kegg_gene_synonyms | 166,044 |
| KEGG | kegg_compound_synonyms | 33,246 |
| KEGG | kegg_gene_group_members | 25,885 |
| NCBI | ncbi_info | 305,974 |
| NCBI | ncbi_synonyms | 150,879 |
| NCBI | ncbi_ensembl | 73,400 |
| Reactome | reactome_pathway | 4,635 |
| Reactome | reactome_pathway_genes | 239,477 |
| UniProt | uniprot | 248,430 |
| GO | go_terms | 39,353 |
| GO | go_hierarchy | 74,751 |
| GO | go_genes | 789,726 |
| Common | taxon | 542 |

**총 테이블**: 31개 (+ sqlite_sequence 1개)

---

## 스키마 변경 시

1. `3_load/schema/database_schema.sql` 직접 수정
2. `ALTER TABLE ... ADD COLUMN ...` 또는 `create_schema.py` 재실행
3. 해당 소스 import 스크립트 다시 실행 (`[CLEAR]` 단계에서 기존 데이터 삭제 후 재적재)
