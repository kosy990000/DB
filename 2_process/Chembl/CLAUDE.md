# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains ChEMBL database (v36) extraction and analysis workflows. ChEMBL is a large-scale bioactivity database containing drug-like compounds, their biological targets, and disease indications. The codebase extracts and organizes compound-disease-target relationships into structured CSV files for downstream analysis.

## Database Structure

- **Source Database**: `chembl_36/chembl_36_sqlite/chembl_36.db` (28GB SQLite database)
- **ChEMBL Version**: 36
- **Data Organization**: Extracted data is stored in `chembl-data/` with subdirectories for each entity type and relationship type

## Key Data Entities

### 1. Compounds (Molecules)
- **Location**: `chembl-data/compound/`
- **Files**:
  - `compound_information.csv` - Main compound data (ChEMBL_ID, Name, Max_Phase, First_Approval, SMILES, InChI_Key)
  - `compound_synonym.csv` - Compound synonyms/aliases (ChEMBL_ID, Synonym, Synonym_Type)
- **Extraction**: `getChemblCompund.ipynb`
- **Key Tables**: `MOLECULE_DICTIONARY`, `COMPOUND_STRUCTURES`, `MOLECULE_SYNONYMS`

### 2. Diseases
- **Location**: `chembl-data/disease/`
- **Files**:
  - `disease_information.csv` - Disease mappings (MESH_ID, MESH_HEADING, EFO_ID, EFO_TERM)
- **Extraction**: `getChemblDisease.ipynb`
- **Key Tables**: `DRUG_INDICATION`
- **Note**: Uses MeSH (Medical Subject Headings) IDs as primary disease identifiers

### 3. Targets
- **Location**: `chembl-data/target/`
- **Files**:
  - `target_information.csv` - Main target data (TARGET_CHEMBL_ID, TARGET_NAME, TARGET_TYPE, ORGANISM, UNIPROT_ID)
  - `target_synonyms.csv` - Target synonyms (TARGET_CHEMBL_ID, SYNONYM, SYNONYM_TYPE)
- **Extraction**: `getChemblTarget.ipynb`
- **Key Tables**: `TARGET_DICTIONARY`, `TARGET_COMPONENTS`, `COMPONENT_SEQUENCES`, `COMPONENT_SYNONYMS`
- **Synonym Types**: GENE_SYMBOL, GENE_SYMBOL_OTHER, UNIPROT, EC_NUMBER

## Relationship Data

### 1. Compound-Disease Relationships
- **Location**: `chembl-data/compound-disease/`
- **Files**:
  - `compound-disease_informatation.csv` - Drug indications (DRUG_CHEMBL_ID, MESH_ID, MAX_PHASE)
- **Extraction**: `getDrug-Disase.ipynb`
- **Key Tables**: `DRUG_INDICATION`, `MOLECULE_DICTIONARY`, `MOLECULE_HIERARCHY`
- **Characteristics**:
  - Filtered for drugs with Homo sapiens targets
  - MAX_PHASE indicates clinical trial phase (-1, 0.5, 1, 2, 3, 4)
  - Duplicates removed by keeping highest MAX_PHASE per drug-disease pair
  - ~55,025 unique drug-disease pairs
  - High sparsity (~99.5%)

### 2. Compound-Target Relationships
- **Location**: `chembl-data/compound-target/`
- **Files**:
  - `compound-target_information.csv` - All bioactivity data (DRUG_CHEMBL_ID, TARGET_CHEMBL_ID, TARGET_NAME, TARGET_TYPE, ORGANISM, UNIPROT_ID, STANDARD_TYPE, STANDARD_RELATION, STANDARD_VALUE, STANDARD_UNITS, PCHEMBL_VALUE, CONFIDENCE_SCORE, ASSAY_DESCRIPTION)
- **Extraction**: `getDrug-Target.ipynb`
- **Key Tables**: `ACTIVITIES`, `ASSAYS`, `TARGET_DICTIONARY`, `MOLECULE_DICTIONARY`, `TARGET_COMPONENTS`, `COMPONENT_SEQUENCES`
- **Size**: ~25.5M records (9.3GB CSV file)
- **Activity Types**: IC50, Ki, EC50, Inhibition, etc.
- **Note**: Contains all experimental bioactivity data, not just validated mechanisms

## Common SQL Query Patterns

### Filtering for Human Targets
Always filter targets by organism when analyzing drug-target relationships:
```sql
WHERE td.organism = 'Homo sapiens'
```

### Joining Compound to Target
```sql
FROM MOLECULE_DICTIONARY md
JOIN DRUG_MECHANISM dm ON md.molregno = dm.molregno
JOIN TARGET_DICTIONARY td ON dm.tid = td.tid
```

### Getting UniProt IDs
```sql
LEFT JOIN TARGET_COMPONENTS tc ON td.tid = tc.tid
LEFT JOIN COMPONENT_SEQUENCES cs ON tc.component_id = cs.component_id
```
Note: Use LEFT JOIN since not all targets have UniProt mappings (e.g., CELL-LINE, UNCHECKED types)

### Deduplication Strategy
When multiple records exist for the same compound-disease or compound-target pair:
- Sort by MAX_PHASE (descending) or PCHEMBL_VALUE (descending)
- Use `drop_duplicates(subset=[...], keep='first')` in pandas
- Or use median aggregation for continuous values like pChEMBL

## Data Preprocessing Notes

### NaN Handling
All extracted dataframes use `df.replace({np.nan: None})` to convert pandas NaN to Python None for better CSV compatibility.

### Duplicate Removal
- **Compound-Disease**: Duplicates arise when drugs target multiple proteins for the same disease. Keep highest MAX_PHASE.
- **Compound-Target**: Duplicates from multiple assays. Median aggregation recommended for pChEMBL values.

### Data Cleaning
- Target synonyms have quotes removed: `TRIM(REPLACE(syn.component_synonym, '"', ''))`
- Disease headings have quotes removed: `df['MESH_HEADING'].str.replace('"', '', regex=False)`

## Key ChEMBL Tables Reference

| Table | Purpose |
|-------|---------|
| `MOLECULE_DICTIONARY` | Core compound information (chembl_id, pref_name, max_phase) |
| `COMPOUND_STRUCTURES` | Chemical structures (SMILES, InChI) |
| `MOLECULE_SYNONYMS` | Alternative compound names |
| `TARGET_DICTIONARY` | Target proteins/complexes (chembl_id, pref_name, organism, target_type) |
| `TARGET_COMPONENTS` | Links targets to protein sequences |
| `COMPONENT_SEQUENCES` | Protein sequences and UniProt accessions |
| `COMPONENT_SYNONYMS` | Gene symbols and alternative target names |
| `DRUG_INDICATION` | Disease indications (mesh_id, efo_id) |
| `DRUG_MECHANISM` | Validated mechanism of action data |
| `ACTIVITIES` | Experimental bioactivity measurements |
| `ASSAYS` | Assay protocols and confidence scores |
| `MOLECULE_HIERARCHY` | Parent-child molecule relationships |

## Working with the Database

### Connection Pattern
```python
import sqlite3
db_path = 'chembl_36/chembl_36_sqlite/chembl_36.db'
conn = sqlite3.connect(db_path)
# ... queries ...
conn.close()
```

### Reading Results
```python
import pandas as pd
df = pd.read_sql_query(query, conn)
df = df.replace({np.nan: None})  # Standardize NaN handling
```

## Data Characteristics

### Sparsity
Both compound-disease and compound-target relationship matrices are highly sparse:
- Compound-Disease: ~99.5% sparse
- Compound-Target: >99.9% sparse (vast majority of possible drug-target pairs are untested)

### Scale
- ~2.8M compounds in database
- ~21,581 targets
- ~2,804 diseases (unique MeSH IDs)
- ~25.5M bioactivity records

## Important File Mappings

- **Chembl.ipynb**: Original exploration notebook showing drug-disease-target joint analysis
- **getChemblCompund.ipynb**: Extracts compound information and synonyms
- **getChemblDisease.ipynb**: Extracts disease information from drug indications
- **getChemblTarget.ipynb**: Extracts target information and synonyms
- **getDrug-Disase.ipynb**: Extracts compound-disease relationships
- **getDrug-Target.ipynb**: Extracts all bioactivity data (compound-target relationships)
- **chembl_uniprot_mapping.txt**: External UniProt mapping reference file

## Notes on Data Quality

- **CONFIDENCE_SCORE**: In ASSAYS table, ranges 0-9. Higher is better. 9 = direct single protein assay from scientific literature.
- **Target Types**: SINGLE PROTEIN, PROTEIN FAMILY, PROTEIN COMPLEX, CELL-LINE, UNCHECKED, etc. Filter by type based on analysis needs.
- **MAX_PHASE**: -1 = withdrawn/discontinued, 0.5 = preclinical, 1-3 = clinical phases, 4 = approved
- **STANDARD_TYPE**: Normalized activity types (IC50, Ki, EC50, etc.). Check STANDARD_RELATION for inequality operators (<, >, =).
- **pChEMBL_VALUE**: -log10(molar IC50/Ki/EC50). Higher values = stronger binding. Standardized metric for comparing activities.
