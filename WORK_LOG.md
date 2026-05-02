# DB 프로젝트 작업 로그

---

## 2026-05-02 — DB 구축 완료

### 작업 요약
- 폴더 구조 재편 (`scripts/`, `db-script/` → `1_download/`, `2_process/`, `3_load/`)
- 경로 중앙화: `config.yaml` + `paths.py` 도입, 전체 스크립트 하드코딩 제거
- 전체 스크립트 디버그 및 경로 수정
- 31개 테이블 DB 적재 완료 (0 row 테이블 없음)

### 변경 사항

#### 폴더 구조
```
구조 전: scripts/{소스}/    db-script/
구조 후: 1_download/  2_process/  3_load/
```

#### 경로 중앙화
- `config.yaml`: raw/processed 경로 전부 정의
- `paths.py`: config.yaml 로드 → `DB_FILE`, `RAW_*`, `PROC_*` Path 객체 export
- 모든 스크립트: `sys.path.insert(0, parent.parent.parent)` + `from paths import ...`

#### 버그 수정
| 파일 | 수정 내용 |
|------|----------|
| `2_process/Drugbank/get_drug_target_information.py` | output 경로 `target_information/`으로 수정, `gene_symbol` 컬럼명 통일 |
| `2_process/Kegg/normalize_kegg_mapping.py` | 잔존 `BASE_DIR` 참조 → `PROC_KEGG` |
| `3_load/schema/create_schema.py` | 경로 수정, `DB_FILE.parent.mkdir` 추가 |
| `3_load/schema/database_schema.sql` | 모든 `CREATE TABLE/INDEX` → `IF NOT EXISTS` 추가 |
| `3_load/Reactome/import_reactome_to_db.py` | 파일명 `all_pathway.csv` → `pathway.csv` 수정 |
| `3_load/schema/database_schema.sql` | `reactome_pathway_genes`에 `evidence_code TEXT` 컬럼 추가 |

### 최종 DB 현황
- 파일: `database/database.db`
- 테이블: 31개, 0 row 테이블 없음
- PubChem만 compounds 1.2억 / synonyms 1.1억 rows

---

## 2026-01-04 (토) - DrugBank 스크립트 변환 완료

### 📋 작업 요약
DrugBank 데이터베이스 추출 스크립트 생성 (Jupyter Notebook → Python)

---

## ✅ 완료된 작업

### 1. DrugBank Drug Information 추출
**작업**: Jupyter notebook을 Python 스크립트로 변환 및 경로 수정
**스크립트**: `2_process/Drugbank/get_drug_information.py`
**파일**: `processed/Drugbank/drug_information/drug_information.csv`

**결과**:
- 17,430개 약물 정보
- Small molecule: 13,166개 (75.5%)
- Biotech: 4,264개 (24.5%)

**컬럼** (8개):
- drugbank_id, name, type, cas_number
- groups, smiles, inchi_key, description

**결측치 정보**:
```
컬럼           결측 개수    비율
drugbank_id       0       0.00%
name              0       0.00%
type              0       0.00%
cas_number     6,663     38.23%
groups            0       0.00%
smiles         5,117     29.36%
inchi_key      5,114     29.34%  ← InChIKey 추가
description    7,405     42.48%
```

**특이사항**:
- SMILES와 InChI Key는 주로 biotech 약물에서 결측 (단백질 의약품은 구조식 없음)
- CAS Number 결측 38% (특히 investigational/experimental 약물)
- Description 결측 42% (오래된 데이터 또는 미승인 약물)

### 2. DrugBank Drug-Target Relationship 추출
**작업**: Jupyter notebook을 Python 스크립트로 변환 및 경로 수정
**스크립트**: `2_process/Drugbank/get_drug_target_information.py`
**파일**:
- `processed/Drugbank/drug-target_information/drug_in_target.csv`
- `processed/Drugbank/drug-target_information/target_information.csv`
- `processed/Drugbank/drug-target_information/drug_target.csv`

**결과**:
- 22,820개 drug-target 관계
- 9,241개 고유 약물 (타겟이 있는 약물만)
- 4,917개 고유 타겟
- 22,801개 고유 관계 (중복 제거)

**Drug 테이블** (drug_in_target.csv):
- drugbank_id, drug_name, drug_groups

**Target 테이블** (target_information.csv):
- gene_name, uniprot_id, organism, taxon_id, target_name
- **taxon_id**: NCBI Taxonomy ID (예: Humans = 9606) ← 추가

**Drug-Target 관계 테이블** (drug_target.csv):
- drugbank_id, uniprot_id, actions, known_action
- **actions**: 약물 작용 타입 (inhibitor, agonist, antagonist, binder, antibody 등) ← 추가
- **known_action**: 작용 메커니즘 알려짐 여부 (yes/no/unknown) ← 추가

**Organism 분포**:
- Humans: 2,981개 타겟 (60.6%)
- Escherichia coli: 317개
- Plasmodium falciparum: 100개 (말라리아)
- 기타 병원균 타겟

**Drug Groups 분포**:
- Experimental: 4,505개 (48.8%)
- Investigational: 2,044개 (22.1%)
- Approved: 889개 (9.6%)
- Approved; Investigational: 1,058개 (11.5%)

---

## 📋 DrugBank 데이터 상세 분석

### 1. drug_information.csv (17,430개)

**결측치**:
```
컬럼           결측 개수    비율
drugbank_id       0       0.00%
name              0       0.00%
type              0       0.00%
cas_number     6,663     38.23%
groups            0       0.00%
smiles         5,117     29.36%
inchi_key      5,114     29.34%
description    7,405     42.48%
```

**카테고리 분포**:
- **type**:
  - small molecule: 13,166개 (75.5%)
  - biotech: 4,264개 (24.5%)

- **groups** (상위 10개):
  - investigational: 6,241개 (35.8%)
  - experimental: 6,134개 (35.2%)
  - approved: 2,254개 (12.9%)
  - approved; investigational: 1,366개 (7.8%)
  - approved; experimental: 239개 (1.4%)

### 2. target_information.csv (4,917개)

**결측치**:
```
컬럼           결측 개수    비율
gene_name        381      7.75%
uniprot_id         0      0.00%
organism           0      0.00%
taxon_id          13      0.26%
target_name        0      0.00%
```

**카테고리 분포**:
- **organism** (상위 5개):
  - Humans: 2,981개 (60.6%)
  - Escherichia coli (K12): 317개 (6.4%)
  - Plasmodium falciparum: 100개 (2.0%)
  - Mycobacterium tuberculosis: 74개 (1.5%)
  - Bacillus subtilis: 66개 (1.3%)

- **taxon_id** (상위 3개):
  - 9606 (Humans): 2,981개
  - 83333 (E. coli K12): 317개
  - 36329 (P. falciparum): 100개

### 3. drug_target.csv (22,801개)

**결측치**:
```
컬럼           결측 개수    비율
drugbank_id       0       0.00%
uniprot_id        0       0.00%
actions        9,456     41.47%  ← 작용 메커니즘 미확인
known_action      0       0.00%
```

**카테고리 분포**:
- **actions** (상위 10개):
  - inhibitor: 6,114개 (26.8%) - 억제제
  - antagonist: 1,924개 (8.4%) - 길항제
  - agonist: 1,540개 (6.8%) - 작용제
  - modulator: 954개 (4.2%) - 조절제
  - binder: 463개 (2.0%) - 결합제
  - ligand: 454개 (2.0%) - 리간드
  - activator: 239개 (1.0%) - 활성제
  - cofactor: 193개 (0.8%) - 보조인자
  - potentiator: 147개 (0.6%) - 증강제
  - inducer: 115개 (0.5%) - 유도제

- **known_action**:
  - unknown: 13,262개 (58.2%) - 작용 메커니즘 불명
  - yes: 9,311개 (40.8%) - 작용 메커니즘 확인
  - no: 228개 (1.0%) - 작용 메커니즘 없음

**주요 인사이트**:
- actions 결측 41.5%는 주로 known_action="unknown"과 관련
- 전체 관계의 58%가 작용 메커니즘 불명 (약물 재창출 기회)
- Inhibitor가 가장 흔한 작용 방식 (26.8%)

---

## 2026-01-04 (토) - ChEMBL & PubChem 데이터 정리 완료

### 📋 작업 요약
ChEMBL 데이터베이스 추출 작업 완료 및 PubChem 데이터 정리

---

## ✅ 완료된 작업

### 1. ChEMBL Compound-Disease 관계 추출
**문제**: compound-disease 데이터가 12월 25일 버전으로 오래됨
**해결**:
- `2_process/Chembl/get_compound_disease.py` 스크립트 생성
- 최신 데이터로 재추출 (2026-01-03 23:06)
- 파일: `processed/Chembl/compound-disease/compound-disease_information.csv`

**결과**:
- 55,025개 compound-disease 관계
- 10,072개 고유 화합물
- 2,178개 고유 질병 (MeSH ID)
- 희소성: 99.75%

### 2. ChEMBL Target-GO Term 매핑 추출
**작업**: Target의 Gene Ontology term 매핑 데이터 추출
**스크립트**: `2_process/Chembl/get_target_go.py`
**파일**:
- `processed/Chembl/target-go/target_go_terms.csv` (34 MB)
- `processed/Chembl/target-go/target_go_summary.csv` (1.1 MB)

**결과**:
- 220,270개 target-GO 매핑
- 12,820개 GO term 있는 targets
- 280개 고유 GO terms
- Target당 평균 14.25개 GO terms
- GO Aspect 분포:
  - Biological Process (P): 87,666개 (39.8%)
  - Cellular Component (C): 66,933개 (30.4%)
  - Molecular Function (F): 65,671개 (29.8%)

**커버리지**:
- SINGLE PROTEIN: 99.63%
- PROTEIN COMPLEX: 100%
- Homo sapiens: 81.44%

### 3. PubChem 데이터 재정리
**문제**: 노트북으로 처리한 데이터, 컬럼명 불일치 (pudchem 오타)
**해결**:
- `2_process/PubChem/get_pubchem_compound.py` 스크립트 생성
- snake_case 컬럼명으로 통일
- 구버전 파일 삭제

**파일**:
- `processed/PubChem/pubchem_compounds.csv` (23 GB)
- `processed/PubChem/pubchem_synonyms.csv` (3.9 GB)

**결과**:
- **Compounds**: 123,429,971개 (1억 2천만!)
  - 컬럼: cid, inchi_key, smiles, title
  - Null: 거의 0% (inchi_key만 3개)
- **Synonyms**: 114,675,840개 (1억 1천만!)
  - 컬럼: cid, synonym
  - CID당 평균 1.86개 synonyms

---

## 📊 최종 데이터 현황

### ChEMBL (v36)
```
processed/Chembl/
├── compound/
│   ├── compounds.csv (286 MB) - 280만 화합물
│   └── compound_synonyms.csv (4.7 MB)
├── target/
│   ├── targets.csv (1.7 MB) - 2만 targets
│   └── target_synonyms.csv (6.0 MB)
├── disease/
│   └── disease.csv (172 KB) - 2,178개 질병
├── compound-disease/
│   └── compound-disease_information.csv (1.4 MB) - 5.5만 관계
├── compound-target/
│   └── compound-target_information.csv (7.1 GB) - 2천5백만 bioactivity
└── target-go/
    ├── target_go_terms.csv (34 MB) - 22만 매핑
    └── target_go_summary.csv (1.1 MB)
```

### PubChem
```
processed/PubChem/
├── pubchem_compounds.csv (23 GB) - 1억 2천만 화합물
└── pubchem_synonyms.csv (3.9 GB) - 1억 1천만 synonyms
```

**총 데이터 크기**: ~38 GB

---

## 🔧 생성된 스크립트

### ChEMBL 추출 스크립트 (2_process/Chembl/)
1. `get_chembl_compound.py` - 화합물 정보
2. `get_chembl_target.py` - 타겟 정보
3. `get_chembl_disease.py` - 질병 정보
4. `get_compound_disease.py` - 화합물-질병 관계 ✨ NEW
5. `get_drug_target.py` - 화합물-타겟 관계
6. `get_target_go.py` - 타겟-GO term 매핑 ✨ NEW

### PubChem 추출 스크립트 (2_process/PubChem/)
1. `get_pubchem_compound.py` - 화합물 및 synonyms ✨ NEW

---

## 📈 데이터 통계

### ChEMBL 엔티티
- **Compounds**: 2,858,458개
- **Targets**: 17,803개 (Homo sapiens 8,886개)
- **Diseases**: 2,178개 (MeSH ID)
- **GO Terms**: 280개

### 관계 데이터
- **Compound-Disease**: 55,025개 (희소성 99.75%)
- **Compound-Target**: 25,500,000개 (7.1GB)
- **Target-GO**: 220,270개 (평균 17 GO/target)

### PubChem
- **Compounds**: 123,429,971개
- **Synonyms**: 114,675,840개
- **CID당 평균 synonym**: 1.86개

---

## 🎯 데이터 품질

### ChEMBL
- ✅ 모든 테이블 snake_case 통일
- ✅ Null 처리 완료 (np.nan → None)
- ✅ 중복 제거 완료
- ✅ Foreign Key 관계 명확

### PubChem
- ✅ snake_case 통일
- ✅ Null 거의 없음 (99.99%+ 완성도)
- ✅ 표준화된 구조 (SMILES, InChI Key)

---

## 💡 주요 인사이트

### Target-GO Term 분석
- SINGLE PROTEIN 타입은 거의 완벽한 GO term 커버리지 (99.63%)
- CELL-LINE, ORGANISM, TISSUE는 GO term 없음 (예상됨)
- Homo sapiens targets의 81.44%가 GO term 보유
- Protein kinase C가 가장 많은 GO term 보유 (70개)

### 데이터 희소성
- Compound-Disease: 99.75% sparse
- Compound-Target: >99.9% sparse
- 대부분의 가능한 조합이 테스트되지 않음

---

## 🚀 다음 단계 제안

1. **데이터 통합**
   - ChEMBL-PubChem 매핑 (SMILES/InChI 기반)
   - CAS Number, UNII 등으로 ID 통합

2. **추가 데이터 추출 (ChEMBL)**
   - COMPOUND_PROPERTIES (물리화학적 성질) ⭐⭐⭐
   - DRUG_MECHANISM (작용 메커니즘) ⭐⭐⭐
   - MOLECULE_ATC_CLASSIFICATION (WHO 약물 분류) ⭐⭐⭐
   - DRUG_WARNING (안전성 정보) ⭐⭐
   - METABOLISM (대사 정보) ⭐

3. **데이터 분석**
   - Drug repurposing 후보 발굴
   - Target-Disease 네트워크 분석
   - GO term enrichment 분석

4. **그래프 데이터베이스 구축**
   - Neo4j 등으로 지식 그래프 구축
   - Compound-Target-Disease 관계 시각화

---

## 📝 참고 문서
- ChEMBL 가이드: `2_process/Chembl/CLAUDE.md`
- ChEMBL 버전: v36
- 데이터베이스 위치: `raw/chembl/chembl_36/chembl_36_sqlite/chembl_36.db` (28GB)

---

**작업 완료 시간**: 2026-01-04 00:30
**작업자**: Claude Code
**상태**: ✅ 완료
