# Database Design for KEGG Pathway Integration

## 날짜: 2026-01-06

## 현재 데이터 구조

### 1. KEGG Pathway Edges
**위치:** `processed/Kegg/pathway_edges/*.csv`

**구조:**
```csv
source, source_type, target, target_type, relation_type, relation_subtype, pathway_id, pathway_name, organism
hsa:130589, gene, hsa:3098_hsa:3099, gene, ECrel, compound, hsa00010, Glycolysis / Gluconeogenesis, hsa
hsa:5236_hsa:55276, gene, path:hsa00500, map, maplink, compound, hsa00010, Glycolysis / Gluconeogenesis, hsa
path:hsa00061, map, path:hsa00062, map, maplink, compound, hsa00020, Citrate cycle (TCA cycle), hsa
```

**노드 타입:**
- `gene`: 유전자 (예: hsa:123, mmu:456)
- `compound` (실제 ID는 없지만 relation_subtype으로 표시됨)
- `map`: pathway (예: path:hsa00010)

**관계 타입:**
- `ECrel`: Enzyme-enzyme relation
- `maplink`: Pathway 간 연결 또는 gene-pathway 연결

### 2. KEGG Gene Mapping
**위치:** `raw/kegg/kegg-mapping/`

**파일:**
- `hsa_gene_mapping.csv`: 24,684 genes
- `mmu_gene_mapping.csv`: 26,125 genes
- `hsa_kegg_synonyms.csv`: 83,180 synonyms
- `mmu_kegg_synonyms.csv`: 82,874 synonyms

**구조:**
```csv
# gene_mapping.csv
gene_id, entrez_id, organism, gene_type, chromosome, description
hsa:101954268, 101954268, hsa, ncRNA, 1q21.2, "RNA, variant U1 small nuclear 20"

# kegg_synonyms.csv
gene_id, entrez_id, organism, synonym
hsa:101954268, 101954268, hsa, RNVU1-20
```

### 3. KEGG Compound Mapping
**위치:** `raw/kegg/kegg-mapping/`

**파일:**
- `compound_mapping.csv`: 19,569 compounds
- `compound_synonyms.csv`: 33,247 synonyms

**구조:**
```csv
# compound_mapping.csv
compound_id, primary_name, description
cpd:C00001, H2O, Water

# compound_synonyms.csv
compound_id, synonym
cpd:C00001, H2O
cpd:C00001, Water
```

### 4. NCBI Gene Data
**위치:** `processed/NCBI/`

**파일:**
- `ncbi_genes.csv`: 305,972 genes (모든 species)
- `ncbi_synonyms.csv`: synonyms

**구조:**
```csv
entrez_id, taxon_id, species, gene_symbol, description, gene_type
11287, 10090, Mus musculus, Pzp, ..., protein-coding
```

---

## DB 설계 옵션

### 옵션 1: 통합 Node 테이블 (Graph Database Style)

#### 테이블 구조:

**Nodes**
```sql
CREATE TABLE nodes (
    node_id VARCHAR(50) PRIMARY KEY,  -- hsa:123, cpd:C00001, path:hsa00010
    node_type VARCHAR(20),             -- gene, compound, pathway
    organism VARCHAR(10)                -- hsa, mmu, NULL for compounds
);
```

**Edges**
```sql
CREATE TABLE edges (
    edge_id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) REFERENCES nodes(node_id),
    target_id VARCHAR(50) REFERENCES nodes(node_id),
    relation_type VARCHAR(20),         -- ECrel, maplink, etc.
    relation_subtype VARCHAR(20),      -- compound, etc.
    pathway_id VARCHAR(50) REFERENCES nodes(node_id)
);
```

**Node_Metadata** (JSON 또는 Key-Value)
```sql
CREATE TABLE node_metadata (
    node_id VARCHAR(50) REFERENCES nodes(node_id),
    key VARCHAR(50),
    value TEXT
);
```

**장점:**
- 간단한 그래프 구조
- 쿼리가 직관적
- 새로운 노드 타입 추가 용이

**단점:**
- Gene, Compound, Pathway의 서로 다른 메타데이터 저장 어려움
- 타입별 쿼리 시 필터링 필요

---

### 옵션 2: 타입별 분리 테이블 (Relational Database Style)

#### 테이블 구조:

**Genes**
```sql
CREATE TABLE genes (
    gene_id VARCHAR(50) PRIMARY KEY,   -- hsa:123
    entrez_id INTEGER,
    organism VARCHAR(10),
    gene_type VARCHAR(20),
    chromosome VARCHAR(20),
    description TEXT
);
```

**Compounds**
```sql
CREATE TABLE compounds (
    compound_id VARCHAR(50) PRIMARY KEY,  -- cpd:C00001
    primary_name VARCHAR(100),
    description TEXT
);
```

**Pathways**
```sql
CREATE TABLE pathways (
    pathway_id VARCHAR(50) PRIMARY KEY,   -- path:hsa00010
    pathway_name VARCHAR(200),
    organism VARCHAR(10)
);
```

**Edges**
```sql
CREATE TABLE edges (
    edge_id SERIAL PRIMARY KEY,
    source_id VARCHAR(50),
    source_type VARCHAR(20),              -- gene, compound, pathway
    target_id VARCHAR(50),
    target_type VARCHAR(20),
    relation_type VARCHAR(20),
    relation_subtype VARCHAR(20),
    pathway_id VARCHAR(50) REFERENCES pathways(pathway_id)
);
```

**Gene_Synonyms**
```sql
CREATE TABLE gene_synonyms (
    gene_id VARCHAR(50) REFERENCES genes(gene_id),
    synonym VARCHAR(100)
);
```

**Compound_Synonyms**
```sql
CREATE TABLE compound_synonyms (
    compound_id VARCHAR(50) REFERENCES compounds(compound_id),
    synonym VARCHAR(100)
);
```

**장점:**
- 각 타입별 메타데이터 명확히 저장
- SQL 표준에 부합
- 타입 안전성

**단점:**
- 테이블이 많아짐
- Edge 테이블에서 FK 설정 복잡 (polymorphic association)
- 그래프 쿼리 시 여러 테이블 JOIN 필요

---

### 옵션 3: 하이브리드 방식 ⭐ **추천**

#### 테이블 구조:

**1. Core: Nodes (최소 정보)**
```sql
CREATE TABLE nodes (
    node_id VARCHAR(50) PRIMARY KEY,
    node_type VARCHAR(20) NOT NULL,    -- gene, compound, pathway
    organism VARCHAR(10)
);

CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_organism ON nodes(organism);
```

**2. Type-Specific: Genes**
```sql
CREATE TABLE genes (
    gene_id VARCHAR(50) PRIMARY KEY REFERENCES nodes(node_id),
    entrez_id INTEGER,
    gene_type VARCHAR(20),
    chromosome VARCHAR(20),
    description TEXT
);

CREATE INDEX idx_genes_entrez ON genes(entrez_id);
```

**3. Type-Specific: Compounds**
```sql
CREATE TABLE compounds (
    compound_id VARCHAR(50) PRIMARY KEY REFERENCES nodes(node_id),
    primary_name VARCHAR(100),
    description TEXT
);
```

**4. Type-Specific: Pathways**
```sql
CREATE TABLE pathways (
    pathway_id VARCHAR(50) PRIMARY KEY REFERENCES nodes(node_id),
    pathway_name VARCHAR(200)
);
```

**5. Edges (그래프 연결)**
```sql
CREATE TABLE edges (
    edge_id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) REFERENCES nodes(node_id),
    target_id VARCHAR(50) REFERENCES nodes(node_id),
    relation_type VARCHAR(20),
    relation_subtype VARCHAR(20),
    pathway_id VARCHAR(50) REFERENCES pathways(pathway_id)
);

CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_pathway ON edges(pathway_id);
```

**6. Synonyms (통합)**
```sql
CREATE TABLE synonyms (
    node_id VARCHAR(50) REFERENCES nodes(node_id),
    synonym VARCHAR(100),
    PRIMARY KEY (node_id, synonym)
);

CREATE INDEX idx_synonyms_synonym ON synonyms(synonym);
```

**7. NCBI Integration**
```sql
CREATE TABLE ncbi_mapping (
    gene_id VARCHAR(50) REFERENCES genes(gene_id),
    entrez_id INTEGER,
    ncbi_symbol VARCHAR(100),
    taxon_id INTEGER,
    species VARCHAR(100),
    ncbi_description TEXT
);

CREATE INDEX idx_ncbi_entrez ON ncbi_mapping(entrez_id);
```

**장점:**
- ✅ 그래프 쿼리 간단 (nodes + edges)
- ✅ 타입별 상세 정보 저장 가능
- ✅ 확장성 좋음
- ✅ Foreign Key 일관성 유지

**단점:**
- 중간 수준의 복잡도

---

## 쿼리 예시 (옵션 3 기준)

### 1. 특정 pathway의 모든 노드 찾기
```sql
SELECT DISTINCT n.node_id, n.node_type
FROM nodes n
JOIN edges e ON n.node_id = e.source_id OR n.node_id = e.target_id
WHERE e.pathway_id = 'path:hsa00010';
```

### 2. Gene 정보와 함께 찾기
```sql
SELECT n.node_id, n.node_type, g.description, g.entrez_id
FROM nodes n
LEFT JOIN genes g ON n.node_id = g.gene_id
JOIN edges e ON n.node_id = e.source_id OR n.node_id = e.target_id
WHERE e.pathway_id = 'path:hsa00010' AND n.node_type = 'gene';
```

### 3. Pathway 간 연결 찾기
```sql
SELECT e.source_id, e.target_id, p1.pathway_name, p2.pathway_name
FROM edges e
JOIN pathways p1 ON e.source_id = p1.pathway_id
JOIN pathways p2 ON e.target_id = p2.pathway_id
WHERE e.relation_type = 'maplink';
```

### 4. Synonym으로 gene 검색
```sql
SELECT n.node_id, g.description
FROM synonyms s
JOIN nodes n ON s.node_id = n.node_id
JOIN genes g ON n.node_id = g.gene_id
WHERE s.synonym = 'GAPDH' AND n.node_type = 'gene';
```

### 5. NCBI entrez_id로 KEGG gene 찾기
```sql
SELECT g.gene_id, g.description, nm.ncbi_symbol
FROM genes g
JOIN ncbi_mapping nm ON g.entrez_id = nm.entrez_id
WHERE nm.entrez_id = 2597;
```

---

## 데이터 Import 순서

1. **Nodes 테이블 채우기**
   - Gene IDs from KEGG gene_mapping
   - Compound IDs from compound_mapping
   - Pathway IDs from pathway_list

2. **Type-specific 테이블 채우기**
   - Genes 테이블 ← KEGG gene_mapping
   - Compounds 테이블 ← compound_mapping
   - Pathways 테이블 ← pathway_list

3. **Synonyms 테이블 채우기**
   - Gene synonyms ← KEGG kegg_synonyms
   - Compound synonyms ← compound_synonyms

4. **NCBI Mapping 채우기**
   - ncbi_mapping ← NCBI genes (filtered by taxon_id)

5. **Edges 테이블 채우기**
   - Pathway edges ← processed/Kegg/pathway_edges/*.csv

---

## 다음 단계

- [ ] DB 스키마 최종 결정
- [ ] PostgreSQL/MySQL 선택
- [ ] 테이블 생성 SQL 스크립트 작성
- [ ] 데이터 import 스크립트 작성
- [ ] 인덱스 최적화
- [ ] 쿼리 성능 테스트

---

## 메모

### KEGG vs NCBI Synonym 비교
- **Human**: KEGG 83,180개 > NCBI 74,961개 (KEGG가 8,219개 더 많음)
- **Mouse**: KEGG 82,874개 > NCBI 75,918개 (KEGG가 6,956개 더 많음)
- **결론**: KEGG가 약 10% 더 많은 synonym 제공

### Gene ID 매칭
- KEGG gene_id (hsa:xxx)의 숫자 부분 = NCBI entrez_id
- 매칭률: 99.99% (human, mouse 모두)
- KEGG gene_names의 첫 번째 이름 = NCBI gene_symbol (99.3%)
