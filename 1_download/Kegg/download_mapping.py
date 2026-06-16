import sys
import requests
import pandas as pd
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from paths import RAW_KEGG_MAPPING

output_dir = RAW_KEGG_MAPPING
output_dir.mkdir(parents=True, exist_ok=True)

def download_gene_list(organism_code, organism_name):
    """
    Download gene list from KEGG for a given organism
    Creates two files:
    1. gene_mapping.csv: gene info with gene_id (hsa:xxx format)
    2. kegg_synonyms.csv: synonym table (one synonym per row)

    Args:
        organism_code: KEGG organism code (e.g., 'mmu', 'hsa')
        organism_name: Organism name for display (e.g., 'mouse', 'human')
    """
    print(f"Downloading {organism_name} ({organism_code}) gene list...")

    url = f"http://rest.kegg.jp/list/{organism_code}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error downloading {organism_name} data: {response.status_code}")
        return None, None

    # Parse the data
    lines = response.text.strip().split('\n')
    gene_data = []
    synonym_data = []

    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 3:
            gene_id = parts[0]
            gene_type = parts[1] if len(parts) > 1 else ""
            chromosome = parts[2] if len(parts) > 2 else ""
            gene_info = parts[3] if len(parts) > 3 else ""

            # Extract entrez_id from gene_id (e.g., 'mmu:12345' -> '12345')
            entrez_id = gene_id.split(':')[1] if ':' in gene_id else ""

            # Extract gene names from gene_info (before semicolon)
            gene_names = ""
            description = ""
            if gene_info:
                if ';' in gene_info:
                    gene_names = gene_info.split(';')[0].strip()
                    description = gene_info.split(';', 1)[1].strip() if len(gene_info.split(';')) > 1 else ""
                else:
                    description = gene_info.strip()

            # Add to gene_data
            gene_data.append({
                'gene_id': gene_id,
                'entrez_id': entrez_id,
                'organism': organism_code,
                'gene_type': gene_type,
                'chromosome': chromosome,
                'description': description
            })

            # Split gene_names and add to synonym_data
            if gene_names:
                for synonym in gene_names.split(','):
                    synonym = synonym.strip()
                    # Filter out empty strings and invalid values (NaN, NA, N/A, -, etc.)
                    if synonym and synonym.lower() not in ['nan', 'na', 'n/a', '-', 'null', 'none']:
                        synonym_data.append({
                            'gene_id': gene_id,
                            'entrez_id': entrez_id,
                            'organism': organism_code,
                            'synonym': synonym
                        })

    # Save gene mapping
    df_genes = pd.DataFrame(gene_data)
    gene_output_file = output_dir / f"{organism_code}_gene_mapping.csv"
    df_genes.to_csv(str(gene_output_file), index=False)

    print(f"Saved {len(df_genes)} genes to {gene_output_file}")
    print(f"Gene mapping columns: {list(df_genes.columns)}")
    print(f"Sample:\n{df_genes.head()}\n")

    # Save synonyms
    df_synonyms = pd.DataFrame(synonym_data)
    synonym_output_file = output_dir / f"{organism_code}_kegg_synonyms.csv"
    df_synonyms.to_csv(str(synonym_output_file), index=False)

    print(f"Saved {len(df_synonyms)} synonyms to {synonym_output_file}")
    print(f"Synonym columns: {list(df_synonyms.columns)}")
    print(f"Sample:\n{df_synonyms.head()}\n")

    return df_genes, df_synonyms

def download_compound_list():
    """
    Download compound list from KEGG
    Creates two files:
    1. compound_mapping.csv: compound info
    2. compound_synonyms.csv: synonym table (one synonym per row)
    """
    print(f"Downloading KEGG compound list...")

    url = "http://rest.kegg.jp/list/compound"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error downloading compound data: {response.status_code}")
        return None, None

    # Parse the data
    lines = response.text.strip().split('\n')
    compound_data = []
    synonym_data = []

    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 2:
            compound_id = parts[0]  # e.g., 'cpd:C00001' or 'C00001'
            compound_info = parts[1] if len(parts) > 1 else ""

            # Ensure compound_id has 'cpd:' prefix
            if not compound_id.startswith('cpd:'):
                compound_id = f"cpd:{compound_id}"

            # Split compound names by semicolon
            compound_names = []
            if compound_info:
                compound_names = [name.strip() for name in compound_info.split(';')]

            # Use first name as primary name, rest as description
            primary_name = compound_names[0] if compound_names else ""
            description = "; ".join(compound_names[1:]) if len(compound_names) > 1 else ""

            # Add to compound_data
            compound_data.append({
                'compound_id': compound_id,
                'primary_name': primary_name,
                'description': description
            })

            # Add all names to synonym_data
            for name in compound_names:
                name = name.strip()
                # Filter out empty strings and invalid values (NaN, NA, N/A, -, etc.)
                if name and name.lower() not in ['nan', 'na', 'n/a', '-', 'null', 'none']:
                    synonym_data.append({
                        'compound_id': compound_id,
                        'synonym': name
                    })

    # Save compound mapping
    df_compounds = pd.DataFrame(compound_data)
    compound_output_file = output_dir / "compound_mapping.csv"
    df_compounds.to_csv(str(compound_output_file), index=False)

    print(f"Saved {len(df_compounds)} compounds to {compound_output_file}")
    print(f"Compound mapping columns: {list(df_compounds.columns)}")
    print(f"Sample:\n{df_compounds.head()}\n")

    # Save compound synonyms
    df_synonyms = pd.DataFrame(synonym_data)
    synonym_output_file = output_dir / "compound_synonyms.csv"
    df_synonyms.to_csv(str(synonym_output_file), index=False)

    print(f"Saved {len(df_synonyms)} compound synonyms to {synonym_output_file}")
    print(f"Synonym columns: {list(df_synonyms.columns)}")
    print(f"Sample:\n{df_synonyms.head()}\n")

    return df_compounds, df_synonyms

if __name__ == "__main__":
    # Download human genes
    print("=" * 60)
    df_hsa = download_gene_list("hsa", "human")

    # Wait to avoid overwhelming the server
    time.sleep(2)

    # Download mouse genes
    print("=" * 60)
    df_mmu = download_gene_list("mmu", "mouse")

    # Wait to avoid overwhelming the server
    time.sleep(2)

    # Download compounds
    print("=" * 60)
    df_cpd, df_cpd_syn = download_compound_list()

    print("=" * 60)
    print("Download complete!")
