"""
KEGG pathway processing script
Converts KGML files to gene-gene interaction CSV files
"""

from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import yaml


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def kgml_to_gene_gene_csv(kgml_file: Path, out_dir: Path):
    """
    Parse KGML file and extract gene-gene relationships.

    Args:
        kgml_file: Path to KGML file
        out_dir: Output directory for CSV files

    Returns:
        Number of edges extracted
    """
    tree = ET.parse(kgml_file)
    root = tree.getroot()

    pathway_id = kgml_file.stem  # hsa00010

    # entry_id → gene list
    entry2genes = {}
    for entry in root.findall("entry"):
        if entry.attrib.get("type") == "gene":
            entry2genes[entry.attrib["id"]] = entry.attrib["name"].split()

    rows = []

    for rel in root.findall("relation"):
        e1 = rel.attrib.get("entry1")
        e2 = rel.attrib.get("entry2")
        rel_type = rel.attrib.get("type")

        # gene → gene 관계만
        if e1 in entry2genes and e2 in entry2genes:
            subtypes = [st.attrib["name"] for st in rel.findall("subtype")]
            subtype = "|".join(subtypes) if subtypes else "NA"

            for g1 in entry2genes[e1]:
                for g2 in entry2genes[e2]:
                    # "hsa:1234" -> "1234"로 변환
                    entrez_id1 = g1.split(":")[-1] if ":" in g1 else g1
                    entrez_id2 = g2.split(":")[-1] if ":" in g2 else g2

                    rows.append({
                        "source_entrez_id": entrez_id1,
                        "target_entrez_id": entrez_id2,
                        "relation_type": rel_type,
                        "subtype": subtype,
                        "pathway_id": pathway_id
                    })

    if not rows:
        return 0

    df = pd.DataFrame(rows)
    out_path = out_dir / f"{pathway_id}.csv"
    df.to_csv(out_path, index=False)

    return len(df)


def main():
    """Main processing function"""
    # Load configuration
    config = load_config()

    KGML_DIR = Path(config['kgml_dir'])
    OUT_DIR = Path(config['output_dir'])

    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_edges = 0
    used_files = 0

    # Process all KGML files
    for kgml_file in KGML_DIR.glob("*.kgml"):
        n = kgml_to_gene_gene_csv(kgml_file, OUT_DIR)
        if n > 0:
            used_files += 1
            total_edges += n

    print(f"CSV 생성된 pathway 수: {used_files}")
    print(f"총 gene-gene edge 수: {total_edges}")


if __name__ == "__main__":
    main()
