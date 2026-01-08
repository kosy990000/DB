-- ============================================
-- SQLite Database Schema
-- ============================================
-- Auto-generated from processed_analysis_filtered.json
-- Generated on: 2026-01-06 08:10:59
-- Total tables: 20
-- ============================================

PRAGMA foreign_keys = ON;


-- ============================================
-- Taxon
-- ============================================

-- Source: taxon.csv
-- Rows: 542
CREATE TABLE taxon (
    taxon_id INTEGER NOT NULL,
    species TEXT,
    scientific_name TEXT NOT NULL
,
    PRIMARY KEY (taxon_id)

);


-- ============================================
-- ChEMBL
-- ============================================

-- Source: Chembl/compound/compounds.csv
-- Rows: 2,878,135
CREATE TABLE chembl_compounds (
    chembl_id TEXT NOT NULL,
    name TEXT,
    max_phase REAL,
    first_approval REAL,
    smiles TEXT,
    inchi_key TEXT
,
    PRIMARY KEY (chembl_id)

);

-- Source: Chembl/target/targets.csv
-- Rows: 17,803
CREATE TABLE chembl_targets (
    target_chembl_id TEXT NOT NULL,
    target_name TEXT NOT NULL,
    target_type TEXT NOT NULL,
    species TEXT
,
    PRIMARY KEY (target_chembl_id)

);

-- Source: Chembl/target/target_uniprot_mappings.csv
-- Rows: 16,675
CREATE TABLE chembl_target_uniprot_mappings (
    target_chembl_id TEXT NOT NULL,
    uniprot_id TEXT NOT NULL
,
    FOREIGN KEY (target_chembl_id) REFERENCES chembl_targets(target_chembl_id)

);
CREATE INDEX idx_chembl_target_uniprot_mappings_target_chembl_id ON chembl_target_uniprot_mappings(target_chembl_id);
CREATE INDEX idx_chembl_target_uniprot_mappings_uniprot_id ON chembl_target_uniprot_mappings(uniprot_id);

-- Source: Chembl/disease/disease.csv
-- Rows: 2,178
CREATE TABLE chembl_diseases (
    mesh_id TEXT NOT NULL,
    mesh_heading TEXT NOT NULL
,
    PRIMARY KEY (mesh_id)

);

-- Source: Chembl/compound/compound_synonyms.csv
-- Rows: 132,937
CREATE TABLE chembl_synonyms (
    chembl_id TEXT NOT NULL,
    synonym TEXT NOT NULL,
    synonym_type TEXT NOT NULL
,
    FOREIGN KEY (chembl_id) REFERENCES chembl_compounds(chembl_id)

);
CREATE INDEX idx_chembl_synonyms_chembl_id ON chembl_synonyms(chembl_id);

-- Source: Chembl/target/target_synonyms.csv
-- Rows: 146,355
CREATE TABLE chembl_target_synonyms (
    target_chembl_id TEXT NOT NULL,
    synonym TEXT,
    synonym_type TEXT NOT NULL
,
    FOREIGN KEY (target_chembl_id) REFERENCES chembl_targets(target_chembl_id)

);
CREATE INDEX idx_chembl_target_synonyms_target_chembl_id ON chembl_target_synonyms(target_chembl_id);

-- Source: Chembl/compound-disease/compound-disease_information.csv
-- Rows: 55,025
CREATE TABLE chembl_drug_disease_relations (
    drug_chembl_id TEXT NOT NULL,
    mesh_id TEXT NOT NULL,
    max_phase REAL NOT NULL
,
    FOREIGN KEY (drug_chembl_id) REFERENCES chembl_compounds(chembl_id)
,
    FOREIGN KEY (mesh_id) REFERENCES chembl_diseases(mesh_id)

);
CREATE INDEX idx_chembl_drug_disease_relations_drug_chembl_id ON chembl_drug_disease_relations(drug_chembl_id);
CREATE INDEX idx_chembl_drug_disease_relations_mesh_id ON chembl_drug_disease_relations(mesh_id);

-- Source: Chembl/compound-target/compound-target_information.csv
-- Rows: 24,267,312
CREATE TABLE chembl_drug_target_relations (
    drug_chembl_id TEXT NOT NULL,
    target_chembl_id TEXT NOT NULL,
    standard_type TEXT,
    standard_relation TEXT,
    standard_value REAL,
    standard_unit TEXT,
    pchembl_value REAL,
    confidence_score INTEGER NOT NULL,
    assay_description TEXT NOT NULL
,
    FOREIGN KEY (drug_chembl_id) REFERENCES chembl_compounds(chembl_id)
,
    FOREIGN KEY (target_chembl_id) REFERENCES chembl_targets(target_chembl_id)

);
CREATE INDEX idx_chembl_drug_target_relations_drug_chembl_id ON chembl_drug_target_relations(drug_chembl_id);
CREATE INDEX idx_chembl_drug_target_relations_target_chembl_id ON chembl_drug_target_relations(target_chembl_id);
CREATE INDEX idx_chembl_drug_target_relations_pchembl_value ON chembl_drug_target_relations(pchembl_value);


-- ============================================
-- DrugBank
-- ============================================

-- Source: Drugbank/drug_information/drug_information.csv
-- Rows: 17,430
CREATE TABLE drugbank_drugs (
    drugbank_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    cas_number TEXT,
    groups TEXT NOT NULL,
    smiles TEXT,
    inchi_key TEXT,
    description TEXT
,
    PRIMARY KEY (drugbank_id)

);

-- Source: Drugbank/target_information/target_information.csv
-- Rows: 4,917
CREATE TABLE drugbank_targets (
    gene_symbol TEXT,
    uniprot_id TEXT NOT NULL,
    organism TEXT NOT NULL,
    taxon_id REAL,
    target_name TEXT NOT NULL
,
    PRIMARY KEY (uniprot_id)
,
    FOREIGN KEY (taxon_id) REFERENCES taxon(taxon_id)

);
CREATE INDEX idx_drugbank_targets_taxon_id ON drugbank_targets(taxon_id);

-- Source: Drugbank/drug-target_information/drug_target.csv
-- Rows: 22,801
CREATE TABLE drugbank_drug_target_relations (
    drugbank_id TEXT NOT NULL,
    uniprot_id TEXT NOT NULL,
    actions TEXT,
    known_action TEXT NOT NULL
,
    FOREIGN KEY (drugbank_id) REFERENCES drugbank_drugs(drugbank_id)
,
    FOREIGN KEY (uniprot_id) REFERENCES drugbank_targets(uniprot_id)

);
CREATE INDEX idx_drugbank_drug_target_relations_drugbank_id ON drugbank_drug_target_relations(drugbank_id);
CREATE INDEX idx_drugbank_drug_target_relations_uniprot_id ON drugbank_drug_target_relations(uniprot_id);


-- ============================================
-- PubChem
-- ============================================

-- Source: PubChem/pubchem_compounds.csv
-- Rows: 123,429,971
CREATE TABLE pubchem_compounds (
    cid INTEGER NOT NULL,
    inchi_key TEXT,
    smiles TEXT NOT NULL,
    title TEXT NOT NULL
,
    PRIMARY KEY (cid)

);

-- Source: PubChem/pubchem_synonyms.csv
-- Rows: 114,675,840
CREATE TABLE pubchem_compound_synonyms (
    cid INTEGER NOT NULL,
    synonym TEXT NOT NULL
,
    FOREIGN KEY (cid) REFERENCES pubchem_compounds(cid)

);
CREATE INDEX idx_pubchem_compound_synonyms_cid ON pubchem_compound_synonyms(cid);


-- ============================================
-- KEGG
-- ============================================

-- Source: Kegg/pathway_list.csv
-- Rows: 734
CREATE TABLE kegg_pathway (
    pathway_id TEXT NOT NULL,
    pathway_number INTEGER NOT NULL,
    organism TEXT NOT NULL,
    taxon_id INTEGER NOT NULL,
    species TEXT NOT NULL,
    pathway_name TEXT NOT NULL,
    link TEXT NOT NULL
,
    PRIMARY KEY (pathway_id)
,
    FOREIGN KEY (taxon_id) REFERENCES taxon(taxon_id)

);
CREATE INDEX idx_kegg_pathway_taxon_id ON kegg_pathway(taxon_id);

-- Source: kegg-mapping/hsa_gene_mapping.csv, mmu_gene_mapping.csv
-- Rows: 50,809 (hsa: 24,684 + mmu: 26,125)
CREATE TABLE kegg_genes (
    gene_id TEXT NOT NULL,
    entrez_id INTEGER NOT NULL,
    organism TEXT NOT NULL,
    gene_type TEXT,
    chromosome TEXT,
    description TEXT
,
    PRIMARY KEY (gene_id)
,
    FOREIGN KEY (entrez_id) REFERENCES ncbi_info(entrez_id)

);
CREATE INDEX idx_kegg_genes_entrez_id ON kegg_genes(entrez_id);
CREATE INDEX idx_kegg_genes_organism ON kegg_genes(organism);

-- Source: kegg-mapping/compound_mapping.csv
-- Rows: 19,569
CREATE TABLE kegg_compounds (
    compound_id TEXT NOT NULL,
    primary_name TEXT,
    description TEXT
,
    PRIMARY KEY (compound_id)

);

-- Source: kegg-mapping/hsa_kegg_synonyms.csv, mmu_kegg_synonyms.csv
-- Rows: 166,054 (hsa: 83,180 + mmu: 82,874)
CREATE TABLE kegg_gene_synonyms (
    gene_id TEXT NOT NULL,
    synonym TEXT NOT NULL
,
    FOREIGN KEY (gene_id) REFERENCES kegg_genes(gene_id)

);
CREATE INDEX idx_kegg_gene_synonyms_gene_id ON kegg_gene_synonyms(gene_id);
CREATE INDEX idx_kegg_gene_synonyms_synonym ON kegg_gene_synonyms(synonym);

-- Source: kegg-mapping/compound_synonyms.csv
-- Rows: 33,247
CREATE TABLE kegg_compound_synonyms (
    compound_id TEXT NOT NULL,
    synonym TEXT NOT NULL
,
    FOREIGN KEY (compound_id) REFERENCES kegg_compounds(compound_id)

);
CREATE INDEX idx_kegg_compound_synonyms_compound_id ON kegg_compound_synonyms(compound_id);
CREATE INDEX idx_kegg_compound_synonyms_synonym ON kegg_compound_synonyms(synonym);

-- Source: Generated from genes, gene_groups, compounds, pathways
-- Rows: ~71,000
-- node_type: gene (individual + group), compound, map (pathway)
CREATE TABLE kegg_nodes (
    node_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    organism TEXT
,
    PRIMARY KEY (node_id)

);
CREATE INDEX idx_kegg_nodes_type ON kegg_nodes(node_type);
CREATE INDEX idx_kegg_nodes_organism ON kegg_nodes(organism);

-- Source: Kegg/pathway_edges/*.csv
-- Rows: TBD
CREATE TABLE kegg_edges (
    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    relation_subtype TEXT,
    pathway_id TEXT NOT NULL
,
    FOREIGN KEY (source_id) REFERENCES kegg_nodes(node_id)
,
    FOREIGN KEY (target_id) REFERENCES kegg_nodes(node_id)
,
    FOREIGN KEY (pathway_id) REFERENCES kegg_pathway(pathway_id)

);
CREATE INDEX idx_kegg_edges_source_id ON kegg_edges(source_id);
CREATE INDEX idx_kegg_edges_target_id ON kegg_edges(target_id);
CREATE INDEX idx_kegg_edges_pathway_id ON kegg_edges(pathway_id);
CREATE INDEX idx_kegg_edges_relation_type ON kegg_edges(relation_type);

-- Source: Extracted from KGML files
-- Rows: TBD
CREATE TABLE kegg_gene_group_members (
    group_id TEXT NOT NULL,
    member_gene_id TEXT NOT NULL
,
    FOREIGN KEY (group_id) REFERENCES kegg_nodes(node_id)
,
    FOREIGN KEY (member_gene_id) REFERENCES kegg_genes(gene_id)

);
CREATE INDEX idx_kegg_gene_group_members_group_id ON kegg_gene_group_members(group_id);
CREATE INDEX idx_kegg_gene_group_members_member_gene_id ON kegg_gene_group_members(member_gene_id);


-- ============================================
-- NCBI
-- ============================================

-- Source: NCBI/ncbi_genes.csv
-- Rows: 305,972
CREATE TABLE ncbi_info (
    entrez_id INTEGER NOT NULL,
    taxon_id INTEGER NOT NULL,
    species TEXT NOT NULL,
    gene_symbol TEXT NOT NULL,
    description TEXT NOT NULL,
    gene_type TEXT NOT NULL
,
    PRIMARY KEY (entrez_id)
,
    FOREIGN KEY (taxon_id) REFERENCES taxon(taxon_id)

);
CREATE INDEX idx_ncbi_info_taxon_id ON ncbi_info(taxon_id);

-- Source: NCBI/ncbi_synonyms.csv
-- Rows: 150,879
CREATE TABLE ncbi_synonyms (
    entrez_id INTEGER NOT NULL,
    taxon_id INTEGER NOT NULL,
    species TEXT NOT NULL,
    synonym TEXT
,
    FOREIGN KEY (entrez_id) REFERENCES ncbi_info(entrez_id)

);
CREATE INDEX idx_ncbi_synonyms_entrez_id ON ncbi_synonyms(entrez_id);
CREATE INDEX idx_ncbi_synonyms_taxon_id ON ncbi_synonyms(taxon_id);

-- Source: NCBI/ncbi_ensembl.csv
-- Rows: 73,400
CREATE TABLE ncbi_ensembl (
    entrez_id INTEGER NOT NULL,
    taxon_id INTEGER NOT NULL,
    species TEXT NOT NULL,
    ensembl_id TEXT NOT NULL
,
    PRIMARY KEY (entrez_id)
,
    FOREIGN KEY (entrez_id) REFERENCES ncbi_info(entrez_id)

);
CREATE INDEX idx_ncbi_ensembl_taxon_id ON ncbi_ensembl(taxon_id);
CREATE INDEX idx_ncbi_ensembl_ensembl_id ON ncbi_ensembl(ensembl_id);


-- ============================================
-- Reactome
-- ============================================

-- Source: Reactome/all_pathway.csv
-- Rows: 23,219
CREATE TABLE reactome_pathway (
    reactome_pathway_id TEXT NOT NULL,
    pathway_name TEXT NOT NULL,
    organism TEXT NOT NULL
,
    PRIMARY KEY (reactome_pathway_id)

);

-- Source: Reactome/all_pathway_genes.csv
-- Rows: 3,550,105
CREATE TABLE reactome_pathway_genes (
    reactome_pathway_id TEXT NOT NULL,
    ensembl_id TEXT NOT NULL,
    organism TEXT NOT NULL

);
CREATE INDEX idx_reactome_pathway_genes_reactome_pathway_id ON reactome_pathway_genes(reactome_pathway_id);
CREATE INDEX idx_reactome_pathway_genes_ensembl_id ON reactome_pathway_genes(ensembl_id);


-- ============================================
-- UniProt
-- ============================================

-- Source: Uniprot/uniprot_data_mouse_human.csv
-- Rows: 248,430
CREATE TABLE uniprot (
    uniprot_id TEXT NOT NULL,
    gene_symbol TEXT NOT NULL,
    taxon_id INTEGER NOT NULL,
    species TEXT NOT NULL
,
    FOREIGN KEY (taxon_id) REFERENCES taxon(taxon_id)

);
CREATE INDEX idx_uniprot_uniprot_id ON uniprot(uniprot_id);
CREATE INDEX idx_uniprot_taxon_id ON uniprot(taxon_id);


-- ============================================
-- Gene Ontology (GO)
-- ============================================

-- Source: Go/BP/BP_nodes.csv, Go/CC/CC_nodes.csv, Go/MF/MF_nodes.csv
-- Rows: ~39,000 (BP: 25,154 + CC: 4,058 + MF: 10,144)
CREATE TABLE go_terms (
    go_id TEXT NOT NULL,
    aspect TEXT NOT NULL,        -- 'BP', 'CC', 'MF'
    name TEXT NOT NULL,
    definition TEXT
,
    PRIMARY KEY (go_id)

);
CREATE INDEX idx_go_terms_aspect ON go_terms(aspect);

-- Source: Go/BP/BP_edges.csv, Go/CC/CC_edges.csv, Go/MF/MF_edges.csv
-- Rows: ~75,000 (BP: 55,804 + CC: 6,466 + MF: 12,484)
CREATE TABLE go_hierarchy (
    parent_go_id TEXT NOT NULL,
    child_go_id TEXT NOT NULL,
    relation_type TEXT NOT NULL  -- 'is_a', 'part_of', 'regulates', etc.
,
    FOREIGN KEY (parent_go_id) REFERENCES go_terms(go_id)
,
    FOREIGN KEY (child_go_id) REFERENCES go_terms(go_id)

);
CREATE INDEX idx_go_hierarchy_parent ON go_hierarchy(parent_go_id);
CREATE INDEX idx_go_hierarchy_child ON go_hierarchy(child_go_id);

-- Source: Go/goa_human.csv, Go/goa_mouse.csv (deduplicated)
-- Rows: ~800,000 (human: ~400,000 + mouse: ~400,000)
CREATE TABLE go_genes (
    go_id TEXT NOT NULL,
    gene_symbol TEXT NOT NULL,
    db_object_id TEXT,           -- UniProt ID for human, MGI ID for mouse
    aspect TEXT NOT NULL,        -- F/P/C (Function/Process/Component)
    tax_id INTEGER NOT NULL
,
    FOREIGN KEY (go_id) REFERENCES go_terms(go_id)

);
CREATE INDEX idx_go_genes_go_id ON go_genes(go_id);
CREATE INDEX idx_go_genes_symbol ON go_genes(gene_symbol);
CREATE INDEX idx_go_genes_db_object_id ON go_genes(db_object_id);
CREATE INDEX idx_go_genes_aspect ON go_genes(aspect);
CREATE INDEX idx_go_genes_tax_id ON go_genes(tax_id);

