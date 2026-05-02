# KEGG PATHWAY KGML Analysis

Total files analyzed: **369**

## Entry Types

| Type | Count | Percentage |
|------|-------|------------|
| gene | 24,809 | 50.86% |
| compound | 12,530 | 25.69% |
| ortholog | 7,781 | 15.95% |
| map | 2,756 | 5.65% |
| group | 900 | 1.85% |

**Total entries:** 48,776

### Entry Type Descriptions

**gene**: Gene product (protein, enzyme)

Examples:
- Pathway: `hsa04640`, Name: `hsa:102723407`
- Pathway: `hsa04640`, Name: `hsa:3655 hsa:3672 hsa:3673 hsa:3675 hsa:3676 hsa:3`

**map**: Link to another pathway map

Examples:
- Pathway: `hsa04640`, Name: `path:hsa04640`
- Pathway: `hsa03060`, Name: `path:hsa03060`

**ortholog**: Ortholog group (KO)

Examples:
- Pathway: `hsa03060`, Name: `ko:K03425`
- Pathway: `hsa03060`, Name: `ko:K01983`

**compound**: Chemical compound, metabolite

Examples:
- Pathway: `hsa05135`, Name: `cpd:C04637`
- Pathway: `hsa05135`, Name: `cpd:C01245`

**group**: Complex of genes/proteins

Examples:
- Pathway: `hsa05135`, Name: `undefined`
- Pathway: `hsa05135`, Name: `undefined`

## Relation Types

| Type | Count | Percentage |
|------|-------|------------|
| PPrel | 11,259 | 51.36% |
| ECrel | 5,046 | 23.02% |
| PCrel | 2,134 | 9.74% |
| GErel | 2,098 | 9.57% |
| maplink | 1,383 | 6.31% |

**Total relations:** 21,920

### Relation Type Descriptions

**PPrel**: Protein-Protein interaction (enzyme-enzyme relation)

Examples:
- Pathway: `hsa05135`, Subtypes: `activation`
- Pathway: `hsa05135`, Subtypes: `activation`

**PCrel**: Protein-Compound interaction

Examples:
- Pathway: `hsa05135`, Subtypes: `activation`
- Pathway: `hsa05135`, Subtypes: `activation`

**GErel**: Gene Expression interaction

Examples:
- Pathway: `hsa05135`, Subtypes: `expression`
- Pathway: `hsa05135`, Subtypes: `expression`

**ECrel**: Enzyme-Compound relation

Examples:
- Pathway: `hsa04975`, Subtypes: `compound`
- Pathway: `hsa04975`, Subtypes: `compound`

**maplink**: Link between pathway maps

Examples:
- Pathway: `hsa00053`, Subtypes: `compound`
- Pathway: `hsa00053`, Subtypes: `compound`

## Relation Subtypes

| Subtype | Count | Percentage |
|---------|-------|------------|
| activation | 8,701 | 35.20% |
| compound | 6,574 | 26.59% |
| expression | 2,021 | 8.18% |
| inhibition | 1,929 | 7.80% |
| phosphorylation | 1,874 | 7.58% |
| binding/association | 1,655 | 6.70% |
| indirect effect | 1,123 | 4.54% |
| missing interaction | 307 | 1.24% |
| dephosphorylation | 187 | 0.76% |
| dissociation | 108 | 0.44% |
| ubiquitination | 89 | 0.36% |
| repression | 63 | 0.25% |
| state change | 54 | 0.22% |
| indirect | 21 | 0.08% |
| glycosylation | 11 | 0.04% |
| methylation | 2 | 0.01% |

**Total subtypes:** 24,719

## Top Relation Type + Subtype Combinations

| Relation Type | Subtype | Count |
|---------------|---------|-------|
| PPrel | activation | 7,107 |
| ECrel | compound | 5,037 |
| GErel | expression | 2,021 |
| PPrel | phosphorylation | 1,855 |
| PPrel | inhibition | 1,749 |
| PCrel | activation | 1,586 |
| PPrel | binding/association | 1,478 |
| maplink | compound | 1,378 |
| PPrel | indirect effect | 904 |
| PPrel | missing interaction | 243 |
| PCrel | binding/association | 176 |
| PCrel | inhibition | 176 |
| PPrel | dephosphorylation | 173 |
| PPrel | compound | 157 |
| PCrel | indirect effect | 121 |
