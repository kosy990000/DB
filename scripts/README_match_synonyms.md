# ChEMBL/PubChem Synonym 매칭 스크립트

화합물 synonym(동의어)을 사용해서 ChEMBL, DrugBank, PubChem 간 매칭을 찾는 스크립트입니다.

## 📋 기능

1. **ChEMBL ID로 분석**: ChEMBL compound의 synonym으로 DrugBank 매칭
2. **PubChem CID로 분석**: PubChem compound의 synonym과 InChI Key로 ChEMBL/DrugBank 매칭
3. **이름으로 검색**: 화합물 이름으로 ChEMBL 검색
4. **대량 샘플링 통계**: 전체 매칭 비율 통계

## 🚀 사용법

### 1. ChEMBL ID로 분석

```bash
# 단일 compound
python3 scripts/match_chembl_synonyms.py --chembl-id CHEMBL25

# 여러 compounds
python3 scripts/match_chembl_synonyms.py --chembl-id CHEMBL25 CHEMBL1 CHEMBL941
```

**출력:**
- ChEMBL compound 정보 (이름, max_phase, InChI Key)
- Synonyms 목록
- DrugBank 매칭 (InChI Key + Synonym)

**예시:**
```
🔬 ChEMBL Compound: CHEMBL25
Name: ACETYLSALICYLIC ACID
Max Phase: 4.0
InChI Key: BSYNRYMUTXBXSQ-UHFFFAOYSA-N

📝 Synonyms: 10개
  - 8-hour bayer (TRADE_NAME)
  - Acetylsalicylic acid (ATC)
  ...

🔗 DrugBank 매칭:
  ✅ Synonym 매칭: 1개
     'Acetylsalicylic acid' → DB00945: Acetylsalicylic acid (approved)
```

---

### 2. PubChem CID로 분석

```bash
# Aspirin (CID: 2244)
python3 scripts/match_chembl_synonyms.py --cid 2244

# Ibuprofen (CID: 3672)
python3 scripts/match_chembl_synonyms.py --cid 3672
```

**출력:**
- PubChem compound 정보
- Synonyms 목록
- ChEMBL 매칭 (InChI Key)
- DrugBank 매칭 (InChI Key + Synonym)

**예시:**
```
🧪 PubChem Compound: CID 2244
Title: Aspirin
InChI Key: BSYNRYMUTXBXSQ-UHFFFAOYSA-N

📝 Synonyms: 20개
  - Aspirin
  - Acetylsalicylic acid
  ...

🔗 ChEMBL 매칭:
  ✅ InChI Key 매칭: 1개
     CHEMBL25: ACETYLSALICYLIC ACID (Phase 4.0)

🔗 DrugBank 매칭:
  ✅ InChI Key 매칭: 1개
     DB00945: Acetylsalicylic acid
```

---

### 3. 화합물 이름으로 검색

```bash
python3 scripts/match_chembl_synonyms.py --search "aspirin"
```

**출력:**
- ChEMBL에서 이름이 매칭되는 compound 목록

---

### 4. 대량 샘플링 통계

```bash
# 기본 1000개 샘플
python3 scripts/match_chembl_synonyms.py --batch

# 샘플 크기 지정
python3 scripts/match_chembl_synonyms.py --batch --sample-size 5000
```

**출력:**
```
📊 대량 샘플링 통계 (샘플: 1000개)

진행 중... 100/1000
진행 중... 200/1000
...

결과:
  InChI Key 매칭: 50/1000 (5.00%)
  Synonym 매칭: 3/1000 (0.30%)
```

---

### 5. 기본 실행 (예시 약물들)

```bash
python3 scripts/match_chembl_synonyms.py
```

유명 약물 4개 (Aspirin, Imatinib, Metformin, Prazosin)로 자동 분석

---

## 📊 매칭 방법

### 1. InChI Key 매칭 (권장)
- **정확도**: ⭐⭐⭐⭐⭐ (매우 높음)
- **커버리지**: ChEMBL 0.81% NULL, DrugBank 29% NULL
- **사용**: 구조가 정확히 같은 화합물 찾기

### 2. Synonym 매칭
- **정확도**: ⭐⭐⭐ (중간, 이름 변형 가능)
- **커버리지**: ⭐⭐ (낮음, 약 0.3%)
- **사용**: InChI Key가 없거나 이름으로 매칭 필요할 때

### 3. 권장 전략
1. 먼저 **InChI Key**로 매칭 시도
2. 실패하면 **Synonym**으로 매칭
3. 둘 다 실패하면 수동 확인

---

## 🧪 실전 예시

### Aspirin 전체 분석

```bash
# ChEMBL 관점
python3 scripts/match_chembl_synonyms.py --chembl-id CHEMBL25

# PubChem 관점
python3 scripts/match_chembl_synonyms.py --cid 2244
```

### 여러 약물 비교

```bash
python3 scripts/match_chembl_synonyms.py \
  --chembl-id CHEMBL25 CHEMBL1 CHEMBL941 CHEMBL2
```

---

## ⚙️ 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--chembl-id` | ChEMBL ID (여러 개 가능) | `--chembl-id CHEMBL25 CHEMBL1` |
| `--cid` | PubChem CID | `--cid 2244` |
| `--search` | 이름으로 검색 | `--search "aspirin"` |
| `--batch` | 대량 샘플링 통계 | `--batch` |
| `--sample-size` | 샘플 크기 | `--sample-size 5000` |
| `--db` | DB 파일 경로 | `--db database/database.db` |

---

## 📈 예상 결과

### ChEMBL → DrugBank 매칭률
- **InChI Key**: ~5-10% (DrugBank가 작아서)
- **Synonym**: ~0.3% (이름 매칭이 어려움)

### PubChem → ChEMBL/DrugBank 매칭률
- **InChI Key**: ~1-5%
- **Synonym**: ~0.1%

---

## 💡 팁

1. **메모리 부족 에러 시**: `--sample-size`를 줄이거나, 단일 compound만 분석
2. **느린 경우**: PubChem synonyms가 1억개 이상이므로 시간 소요 가능
3. **매칭 안 되는 경우**:
   - InChI Key가 NULL인지 확인
   - Synonym 철자가 정확히 일치하는지 확인
   - 수동으로 SMILES 구조 비교 필요

---

## 🔍 출력 예시

```
================================================================================
🔬 ChEMBL Compound: CHEMBL25
================================================================================
Name: ACETYLSALICYLIC ACID
Max Phase: 4.0
InChI Key: BSYNRYMUTXBXSQ-UHFFFAOYSA-N

📝 Synonyms: 10개
  - 8-hour bayer (TRADE_NAME)
  - Acetyl salicylate (OTHER)
  - Acetylsalic acid (TRADE_NAME)
  - Acetylsalicylic acid (ATC)
  ...

🔗 DrugBank 매칭:

  ✅ InChI Key 매칭:
     DB00945: Acetylsalicylic acid (approved; vet_approved)

  ✅ Synonym 매칭: 2개
     'Acetylsalicylic acid' → DB00945: Acetylsalicylic acid
       Groups: approved; vet_approved, Type: small molecule
```

---

## 📝 참고

- 스크립트 위치: `/data/project/shinyoung/DB/scripts/match_chembl_synonyms.py`
- DB 위치: `/data/project/shinyoung/DB/database/database.db`
- 관련 SQL 쿼리: `/data/project/shinyoung/DB/example_queries.sql`
