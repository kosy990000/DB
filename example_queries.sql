-- ============================================
-- 예시 쿼리 모음: UniProt ID로 Compound 찾기
-- ============================================
-- 작성일: 2026-01-06
-- ============================================

-- ============================================
-- 쿼리 1: ChEMBL에서 Target → Compound 찾기
-- ============================================
-- 설명: UniProt ID로 ChEMBL target을 찾고, 그 target과 반응하는 compound 조회
-- NULL 처리: LEFT JOIN 사용 (chembl_targets.uniprot_id는 22% NULL)

SELECT
    u.uniprot_id,
    u.gene_symbol,
    u.species,
    ct.target_chembl_id,
    ct.target_name,
    ct.target_type,
    cc.chembl_id,
    cc.name as compound_name,
    cc.max_phase,
    cc.smiles,
    cc.inchi_key,
    rel.pchembl_value,
    rel.standard_type,
    rel.standard_value,
    rel.standard_unit,
    rel.confidence_score
FROM uniprot u
LEFT JOIN chembl_targets ct ON u.uniprot_id = ct.uniprot_id
LEFT JOIN chembl_drug_target_relations rel ON ct.target_chembl_id = rel.target_chembl_id
LEFT JOIN chembl_compounds cc ON rel.drug_chembl_id = cc.chembl_id
WHERE u.uniprot_id = 'P31946'  -- 예시: YWHAB
  AND cc.chembl_id IS NOT NULL  -- compound가 있는 것만
ORDER BY rel.pchembl_value DESC NULLS LAST
LIMIT 20;


-- ============================================
-- 쿼리 2: DrugBank에서 Target → Drug 찾기
-- ============================================
-- 설명: UniProt ID로 DrugBank target과 drug 조회
-- NULL 처리: drugbank_targets.uniprot_id는 PK이므로 NULL 없음

SELECT
    u.uniprot_id,
    u.gene_symbol,
    u.species,
    dt.target_name,
    dt.organism,
    dd.drugbank_id,
    dd.name as drug_name,
    dd.type as drug_type,
    dd.groups,
    dd.smiles,
    dd.inchi_key,
    rel.actions,
    rel.known_action
FROM uniprot u
INNER JOIN drugbank_targets dt ON u.uniprot_id = dt.uniprot_id
LEFT JOIN drugbank_drug_target_relations rel ON dt.uniprot_id = rel.uniprot_id
LEFT JOIN drugbank_drugs dd ON rel.drugbank_id = dd.drugbank_id
WHERE u.uniprot_id = 'P31946'  -- 예시: YWHAB
  AND dd.drugbank_id IS NOT NULL  -- drug가 있는 것만
ORDER BY dd.groups
LIMIT 20;


-- ============================================
-- 쿼리 3: ChEMBL + DrugBank 통합 조회 (UNION)
-- ============================================
-- 설명: 한 번에 두 DB의 결과를 모두 조회

SELECT
    'ChEMBL' as source,
    u.uniprot_id,
    u.gene_symbol,
    ct.target_name,
    cc.chembl_id as compound_id,
    cc.name as compound_name,
    cc.max_phase,
    'pChEMBL=' || COALESCE(CAST(rel.pchembl_value AS TEXT), 'N/A') as activity_info,
    cc.inchi_key
FROM uniprot u
LEFT JOIN chembl_targets ct ON u.uniprot_id = ct.uniprot_id
LEFT JOIN chembl_drug_target_relations rel ON ct.target_chembl_id = rel.target_chembl_id
LEFT JOIN chembl_compounds cc ON rel.drug_chembl_id = cc.chembl_id
WHERE u.uniprot_id = 'P31946'
  AND cc.chembl_id IS NOT NULL

UNION ALL

SELECT
    'DrugBank' as source,
    u.uniprot_id,
    u.gene_symbol,
    dt.target_name,
    dd.drugbank_id as compound_id,
    dd.name as compound_name,
    dd.type as max_phase,
    'Groups=' || dd.groups as activity_info,
    dd.inchi_key
FROM uniprot u
INNER JOIN drugbank_targets dt ON u.uniprot_id = dt.uniprot_id
LEFT JOIN drugbank_drug_target_relations rel ON dt.uniprot_id = rel.uniprot_id
LEFT JOIN drugbank_drugs dd ON rel.drugbank_id = dd.drugbank_id
WHERE u.uniprot_id = 'P31946'
  AND dd.drugbank_id IS NOT NULL

ORDER BY source, compound_id;


-- ============================================
-- 쿼리 4: InChI Key로 ChEMBL ↔ DrugBank Compound 매칭
-- ============================================
-- 설명: ChEMBL compound와 DrugBank drug를 InChI Key로 매칭
-- 주의: inchi_key는 NULL이 많으므로 (ChEMBL 0.81%, DrugBank 29%) LEFT JOIN 사용

SELECT
    cc.chembl_id,
    cc.name as chembl_name,
    cc.max_phase as chembl_phase,
    dd.drugbank_id,
    dd.name as drugbank_name,
    dd.groups as drugbank_groups,
    cc.inchi_key,
    CASE
        WHEN cc.inchi_key IS NULL THEN 'ChEMBL NULL'
        WHEN dd.drugbank_id IS NULL THEN 'DrugBank 매칭 없음'
        ELSE 'Matched'
    END as match_status
FROM chembl_compounds cc
LEFT JOIN drugbank_drugs dd ON cc.inchi_key = dd.inchi_key AND cc.inchi_key IS NOT NULL
WHERE cc.chembl_id IN (
    -- 특정 UniProt ID와 관련된 ChEMBL compound만
    SELECT drug_chembl_id
    FROM chembl_drug_target_relations rel
    JOIN chembl_targets ct ON rel.target_chembl_id = ct.target_chembl_id
    WHERE ct.uniprot_id = 'P31946'
)
ORDER BY match_status, cc.chembl_id
LIMIT 20;


-- ============================================
-- 쿼리 5: Gene Symbol로 다중 DB 연결
-- ============================================
-- 설명: gene_symbol을 이용해서 UniProt, NCBI, DrugBank 연결
-- 주의: gene_symbol은 INDEX이지 PK가 아니므로 중복 가능

SELECT
    u.uniprot_id,
    u.gene_symbol,
    u.species,
    n.entrez_id,
    n.description as gene_description,
    dt.target_name as drugbank_target_name,
    COUNT(DISTINCT dd.drugbank_id) as drugbank_drug_count,
    COUNT(DISTINCT cc.chembl_id) as chembl_compound_count
FROM uniprot u
LEFT JOIN ncbi_info n ON u.gene_symbol = n.gene_symbol AND u.taxon_id = n.taxon_id
LEFT JOIN drugbank_targets dt ON u.uniprot_id = dt.uniprot_id
LEFT JOIN drugbank_drug_target_relations drel ON dt.uniprot_id = drel.uniprot_id
LEFT JOIN drugbank_drugs dd ON drel.drugbank_id = dd.drugbank_id
LEFT JOIN chembl_targets ct ON u.uniprot_id = ct.uniprot_id
LEFT JOIN chembl_drug_target_relations crel ON ct.target_chembl_id = crel.target_chembl_id
LEFT JOIN chembl_compounds cc ON crel.drug_chembl_id = cc.chembl_id
WHERE u.gene_symbol = 'YWHAB'  -- 예시 gene symbol
GROUP BY u.uniprot_id, u.gene_symbol, u.species, n.entrez_id, n.description, dt.target_name;


-- ============================================
-- 쿼리 6: UniProt → Pathway 연결 (Gene 경로)
-- ============================================
-- 설명: UniProt → NCBI → Reactome Pathway 연결
-- 경로: uniprot.gene_symbol → ncbi_info.gene_symbol → ncbi_ensembl.ensembl_id → reactome_pathway_genes

SELECT
    u.uniprot_id,
    u.gene_symbol,
    u.species,
    n.entrez_id,
    ne.ensembl_id,
    rp.reactome_pathway_id,
    rp.pathway_name,
    rp.organism
FROM uniprot u
INNER JOIN ncbi_info n ON u.gene_symbol = n.gene_symbol AND u.taxon_id = n.taxon_id
INNER JOIN ncbi_ensembl ne ON n.entrez_id = ne.entrez_id
INNER JOIN reactome_pathway_genes rpg ON ne.ensembl_id = rpg.ensembl_id
INNER JOIN reactome_pathway rp ON rpg.reactome_pathway_id = rp.reactome_pathway_id
WHERE u.uniprot_id = 'P31946'
ORDER BY rp.pathway_name
LIMIT 20;


-- ============================================
-- 쿼리 7: 통계 쿼리 - UniProt ID별 Compound 수
-- ============================================
-- 설명: 각 UniProt ID가 몇 개의 compound/drug와 연결되어 있는지 확인

SELECT
    u.uniprot_id,
    u.gene_symbol,
    u.species,
    COUNT(DISTINCT cc.chembl_id) as chembl_compounds,
    COUNT(DISTINCT dd.drugbank_id) as drugbank_drugs,
    COUNT(DISTINCT cc.chembl_id) + COUNT(DISTINCT dd.drugbank_id) as total_compounds
FROM uniprot u
LEFT JOIN chembl_targets ct ON u.uniprot_id = ct.uniprot_id
LEFT JOIN chembl_drug_target_relations crel ON ct.target_chembl_id = crel.target_chembl_id
LEFT JOIN chembl_compounds cc ON crel.drug_chembl_id = cc.chembl_id
LEFT JOIN drugbank_targets dt ON u.uniprot_id = dt.uniprot_id
LEFT JOIN drugbank_drug_target_relations drel ON dt.uniprot_id = drel.uniprot_id
LEFT JOIN drugbank_drugs dd ON drel.drugbank_id = dd.drugbank_id
WHERE u.uniprot_id IN ('P31946', 'P62258', 'Q04917')  -- 여러 UniProt ID 한 번에 조회
GROUP BY u.uniprot_id, u.gene_symbol, u.species
ORDER BY total_compounds DESC;


-- ============================================
-- 쿼리 8: High Activity Compounds 찾기
-- ============================================
-- 설명: pChEMBL value가 높은 (활성이 강한) compound 찾기
-- 기준: pChEMBL >= 7.0 (IC50/Kd < 100nM에 해당)

SELECT
    u.uniprot_id,
    u.gene_symbol,
    ct.target_name,
    cc.chembl_id,
    cc.name,
    rel.pchembl_value,
    rel.standard_type,
    rel.standard_value,
    rel.standard_unit,
    rel.confidence_score
FROM uniprot u
LEFT JOIN chembl_targets ct ON u.uniprot_id = ct.uniprot_id
LEFT JOIN chembl_drug_target_relations rel ON ct.target_chembl_id = rel.target_chembl_id
LEFT JOIN chembl_compounds cc ON rel.drug_chembl_id = cc.chembl_id
WHERE u.uniprot_id = 'P31946'
  AND rel.pchembl_value >= 7.0  -- High activity
  AND rel.confidence_score >= 5  -- High confidence
ORDER BY rel.pchembl_value DESC
LIMIT 20;


-- ============================================
-- 쿼리 9: Approved Drugs만 찾기 (DrugBank)
-- ============================================
-- 설명: FDA 승인된 약물만 조회

SELECT
    u.uniprot_id,
    u.gene_symbol,
    dt.target_name,
    dd.drugbank_id,
    dd.name,
    dd.type,
    dd.groups,
    rel.actions,
    dd.description
FROM uniprot u
INNER JOIN drugbank_targets dt ON u.uniprot_id = dt.uniprot_id
LEFT JOIN drugbank_drug_target_relations rel ON dt.uniprot_id = rel.uniprot_id
LEFT JOIN drugbank_drugs dd ON rel.drugbank_id = dd.drugbank_id
WHERE u.uniprot_id = 'P31946'
  AND dd.groups LIKE '%approved%'  -- approved 포함
ORDER BY dd.name;


-- ============================================
-- 쿼리 10: NULL 처리 예시 - ChEMBL Target에 UniProt 없는 경우
-- ============================================
-- 설명: ChEMBL target 중 uniprot_id가 NULL인 경우 확인 (22%)

SELECT
    ct.target_chembl_id,
    ct.target_name,
    ct.target_type,
    ct.species,
    ct.uniprot_id,
    CASE
        WHEN ct.uniprot_id IS NULL THEN 'UniProt 매핑 없음'
        WHEN u.uniprot_id IS NULL THEN 'UniProt 테이블에 없음'
        ELSE 'OK'
    END as mapping_status,
    COUNT(rel.drug_chembl_id) as compound_count
FROM chembl_targets ct
LEFT JOIN uniprot u ON ct.uniprot_id = u.uniprot_id
LEFT JOIN chembl_drug_target_relations rel ON ct.target_chembl_id = rel.target_chembl_id
WHERE ct.target_name LIKE '%kinase%'  -- 예시: kinase만
GROUP BY ct.target_chembl_id, ct.target_name, ct.target_type, ct.species, ct.uniprot_id, mapping_status
ORDER BY mapping_status, compound_count DESC
LIMIT 20;


-- ============================================
-- 사용 팁
-- ============================================
-- 1. LEFT JOIN vs INNER JOIN:
--    - LEFT JOIN: NULL 허용 컬럼이나 매칭이 없을 수도 있는 경우
--    - INNER JOIN: 반드시 매칭이 있어야 하는 경우
--
-- 2. NULL 체크:
--    - WHERE column IS NOT NULL: NULL 제외
--    - WHERE column IS NULL: NULL만 조회
--    - COALESCE(column, 'default'): NULL일 때 기본값
--
-- 3. INDEX 활용:
--    - uniprot_id, gene_symbol, inchi_key, ensembl_id 등은 INDEX가 있어 빠름
--    - LIKE '%keyword%'는 INDEX를 못 써서 느림 (앞에 %가 있으면)
--
-- 4. 성능 최적화:
--    - LIMIT 사용: 대량 데이터 조회 시 필수
--    - COUNT(*) 대신 COUNT(DISTINCT column) 사용
--    - 필요한 컬럼만 SELECT (SELECT * 지양)
