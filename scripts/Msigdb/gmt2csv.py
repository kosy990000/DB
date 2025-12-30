import yaml
import pandas as pd
import os

def load_config(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)


def parse_gmt(gmt_file, pathway_col, gene_col):
    rows = []
    with open(gmt_file) as f:
        for line in f:
            parts = line.strip().split("\t")
            pathway = parts[0]
            genes = parts[2:]  # description skip
            for g in genes:
                rows.append([pathway, g])
    return pd.DataFrame(rows, columns=[pathway_col, gene_col])


def main(config_path):
    cfg = load_config(config_path)

    gmt_file = cfg["input"]["gmt_file"]
    output_csv = cfg["output"]["csv_file"]

    pathway_col = cfg["columns"].get("pathway_column", "pathway")
    gene_col = cfg["columns"].get("gene_column", "gene_symbol")

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    df = parse_gmt(gmt_file, pathway_col, gene_col)
    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise RuntimeError("Usage: python gmt_to_csv.py <config.yaml>")
    main(sys.argv[1])
