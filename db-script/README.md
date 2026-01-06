# DB Scripts 디렉토리

데이터베이스 스키마 및 데이터 import 스크립트 모음

## 📁 현재 파일 구조

```
db-script/
├── database_schema.dbml    # DBML 스키마 문서
├── database_schema.sql     # SQLite 스키마 (CREATE TABLE)
├── create_schema.py        # JSON → SQL 스키마 자동 생성 도구
├── import_data.py          # CSV → SQLite import 도구
├── README.md               # 이 파일
└── deprecated/             # 사용 안 하는 스크립트 보관
    ├── load_chembl_data.py      # (구) ChEMBL 로딩 스크립트
    ├── import_chembl.py         # (구) 특정 테이블 import
    └── update_schema_names.py   # (구) 테이블명 변경 도구
```

---

## 📄 파일 설명

### 1. `database_schema.dbml`
- **용도**: DB 스키마 문서 (DBML 형식)
- **기능**:
  - 테이블 구조 정의
  - FK 관계 정의
  - INDEX 정보
  - NULL 비율 및 주석
- **도구**: [dbdiagram.io](https://dbdiagram.io)에서 ERD 시각화 가능
- **업데이트**: 스키마 변경 시 수동 업데이트 필요

### 2. `database_schema.sql`
- **용도**: SQLite CREATE TABLE 스크립트
- **기능**:
  - 데이터베이스 스키마 생성
  - INDEX 생성
  - FK 제약 조건 설정
- **실행**: `sqlite3 database.db < database_schema.sql`
- **자동 생성**: `create_schema.py`로 자동 생성됨

### 3. `create_schema.py`
- **용도**: JSON 분석 파일 기반 SQL 스키마 자동 생성
- **입력**: `processed_analysis_filtered.json`
- **출력**: `database_schema.sql`
- **기능**:
  - pandas dtype → SQLite 타입 매핑
  - 테이블명 자동 매핑
  - 컬럼명 정리
  - INDEX 생성
  - FK 제약 조건 추가
- **실행**:
  ```bash
  python3 create_schema.py
  ```

### 4. `import_data.py`
- **용도**: CSV 파일을 SQLite DB로 import
- **기능**:
  - 대량 데이터 배치 insert
  - Progress bar (tqdm)
  - 에러 처리
  - 테이블명 자동 매핑
- **실행**:
  ```bash
  python3 import_data.py
  ```
- **주의**:
  - 메모리 사용량 높음 (chunk 처리 권장)
  - PubChem synonyms 같은 대용량 데이터는 시간 소요

---

## 🗑️ Deprecated 폴더

더 이상 사용하지 않는 스크립트들 (2026-01-06 정리)

### `load_chembl_data.py`
- **문제**:
  - 오래된 테이블명 사용 (`compounds`, `targets` 등)
  - 현재 스키마와 호환 안 됨
- **대체**: `import_data.py` 사용

### `import_chembl.py`
- **문제**:
  - 특정 ChEMBL 테이블만 import하는 특수 스크립트
  - `import_data.py`와 기능 중복
- **대체**: `import_data.py` 사용

### `update_schema_names.py`
- **문제**:
  - 테이블명 변경 마이그레이션 도구
  - 이미 변경 완료되어 더 이상 필요 없음
- **용도**: 히스토리 참고용으로만 보관

---

## 🔄 DB 스키마 업데이트 워크플로우

### 1. 새 테이블 추가 시

```bash
# 1단계: DBML 파일 수정
vim database_schema.dbml

# 2단계: SQL 스키마 업데이트 (수동 또는 자동)
# 방법 A: 수동
vim database_schema.sql

# 방법 B: create_schema.py 사용 (JSON 업데이트 필요)
python3 create_schema.py

# 3단계: DB에 적용
sqlite3 ../database/database.db < database_schema.sql
```

### 2. 데이터 Import

```bash
# CSV 파일을 DB로 import
python3 import_data.py

# 또는 특정 테이블만
# (import_data.py 수정 필요)
```

---

## 📊 현재 DB 상태

- **위치**: `/data/project/shinyoung/DB/database/database.db`
- **크기**: 42GB
- **테이블 수**: 20개
- **주요 테이블**:
  - ChEMBL: 7개 (compounds, targets, diseases, relations 등)
  - DrugBank: 3개 (drugs, targets, relations)
  - PubChem: 2개 (compounds, synonyms)
  - NCBI: 3개 (info, synonyms, ensembl)
  - Pathway: 2개 (KEGG, Reactome)
  - Reference: 2개 (taxon, uniprot)

---

## ⚙️ 설정 및 경로

### 경로 규칙
- **Raw 데이터**: `../data/*/raw/`
- **Processed 데이터**: `../processed/*/`
- **DB 파일**: `../database/database.db`
- **스키마 파일**: `./database_schema.sql`

### 테이블명 규칙
- 소문자 사용
- 언더스코어(`_`) 구분
- 명확한 이름 (예: `chembl_drug_disease_relations`)

---

## 🔍 참고 문서

- **DBML 스펙**: https://dbml.dbdiagram.io/docs
- **SQLite 공식 문서**: https://www.sqlite.org/docs.html
- **스키마 ERD**: database_schema.dbml을 dbdiagram.io에 붙여넣기

---

## 📝 History

- **2026-01-06**:
  - 사용 안 하는 스크립트 deprecated 폴더로 이동
  - README.md 작성
- **2026-01-05**:
  - database_schema.sql 생성
  - create_schema.py 작성
