import sys
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import RAW_REACTOME, PROC_REACTOME

PROC_REACTOME.mkdir(parents=True, exist_ok=True)

reactome = pd.read_csv(RAW_REACTOME / "NCBI2Reactome_All_Levels.txt",
                       sep="\t",
                       header=None,
                       names=[
                           "ensembl_id",
                           "reactome_pathway_id",
                           "pathway_url",
                           "pathway_name",
                           "evidence_code",
                           "organism"
                       ])

print(f"Total rows loaded: {len(reactome)}")
print("\nOrganism distribution:")
print(reactome["organism"].value_counts())

# Filter for human and mouse only
reactome_filtered = reactome[reactome["organism"].isin(["Homo sapiens", "Mus musculus"])]
print(f"\nFiltered rows (Human + Mouse): {len(reactome_filtered)}")

# Create pathway table
pathway_table = (
    reactome_filtered
    [["reactome_pathway_id", "pathway_name", "organism"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

print(f"\nUnique pathways: {len(pathway_table)}")

# Create pathway-gene edge table
pathway_ensembl_edge = (
    reactome_filtered
    [["reactome_pathway_id", "ensembl_id", "organism", "evidence_code"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

print(f"Pathway-gene edges: {len(pathway_ensembl_edge)}")

# Save to processed folder
pathway_table.to_csv(str(PROC_REACTOME / "pathway.csv"), index=False)
pathway_ensembl_edge.to_csv(str(PROC_REACTOME / "pathway_genes.csv"), index=False)

print(f"\nFiles saved successfully:")
print(f"- {PROC_REACTOME / 'pathway.csv'}")
print(f"- {PROC_REACTOME / 'pathway_genes.csv'}")
