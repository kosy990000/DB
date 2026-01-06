#!/usr/bin/env python3
"""
DrugBank XML Parser - Drug-Target Relationship Extraction
Extracts drug-target relationships from DrugBank XML database
"""

import xml.etree.ElementTree as ET
import pandas as pd
import os

# File paths
XML_FILE = 'raw/drugbank/full database.xml'
OUTPUT_DIR_DRUG_TARGET = 'processed/Drugbank/drug-target_information'
OUTPUT_DIR_DRUG_INFO = 'processed/Drugbank/drug_information'
OUTPUT_TARGET_INFO = os.path.join(OUTPUT_DIR_DRUG_INFO, 'target_information.csv')
OUTPUT_DRUG_TARGET = os.path.join(OUTPUT_DIR_DRUG_TARGET, 'drug_target.csv')

# Namespace
ns = {'db': 'http://www.drugbank.ca'}

def extract_detailed_data(xml_path):
    """Extract detailed drug-target relationship data from DrugBank XML"""

    rows = []
    context = ET.iterparse(xml_path, events=('end',))

    print(f"[{xml_path}] Starting detailed data extraction...")

    for event, elem in context:
        tag = elem.tag.replace(f"{{{ns['db']}}}", "")

        if event == 'end' and tag == 'drug':
            # Skip nested tags (only process root level drugs)
            if 'type' not in elem.attrib:
                elem.clear()
                continue

            try:
                # --- [Drug Info] ---
                drug_id_elem = elem.find("db:drugbank-id[@primary='true']", ns)
                drug_id = drug_id_elem.text if drug_id_elem is not None else None

                name_elem = elem.find("db:name", ns)
                drug_name = name_elem.text if name_elem is not None else None

                drug_type = elem.attrib.get('type')  # small molecule vs biotech

                # Get development stage (Groups)
                groups = [g.text for g in elem.findall("db:groups/db:group", ns)]
                groups_str = "; ".join(groups) if groups else "unknown"

                # --- [Target Info] ---
                target_types = {
                    'targets': 'Target',
                }

                for xml_tag, category_name in target_types.items():
                    items = elem.findall(f"db:{xml_tag}/db:{xml_tag[:-1]}", ns)

                    for item in items:
                        # Actions (at item level)
                        action_elems = item.findall("db:actions/db:action", ns)
                        actions = [a.text for a in action_elems if a.text]
                        actions_str = "; ".join(actions) if actions else None

                        # Known action (at item level)
                        known_action_elem = item.find("db:known-action", ns)
                        known_action = known_action_elem.text if known_action_elem is not None else None

                        polypeptide = item.find("db:polypeptide", ns)

                        if polypeptide is not None:
                            # Gene Name
                            gene_elem = polypeptide.find("db:gene-name", ns)
                            gene_name = gene_elem.text if gene_elem is not None else None

                            # UniProt ID
                            uniprot_id = None
                            for ext in polypeptide.findall("db:external-identifiers/db:external-identifier", ns):
                                res = ext.find("db:resource", ns)
                                if res is not None and res.text == 'UniProtKB':
                                    uniprot_id = ext.find("db:identifier", ns).text
                                    break

                            # Organism and Taxonomy ID
                            organism_elem = polypeptide.find("db:organism", ns)
                            organism = organism_elem.text if organism_elem is not None else None
                            taxon_id = organism_elem.get('ncbi-taxonomy-id') if organism_elem is not None else None

                            # Target Name
                            target_name_elem = polypeptide.find("db:name", ns)
                            target_name = target_name_elem.text if target_name_elem is not None else None

                            # Save information (snake_case)
                            if gene_name or uniprot_id:
                                rows.append({
                                    'drugbank_id': drug_id,
                                    'drug_name': drug_name,
                                    'drug_groups': groups_str,
                                    'gene_symbol': gene_name,
                                    'uniprot_id': uniprot_id,
                                    'organism': organism,
                                    'taxon_id': taxon_id,
                                    'target_name': target_name,
                                    'actions': actions_str,
                                    'known_action': known_action
                                })

            except Exception as e:
                pass

            elem.clear()

    return pd.DataFrame(rows)

def split_and_save_tables(df_detailed):
    """Split detailed data into separate tables and save"""

    # 1. Target table (remove duplicates)
    target_table = df_detailed[['gene_name', 'uniprot_id', 'organism', 'taxon_id', 'target_name']].drop_duplicates()
    print(f"\nTarget table: {len(target_table)} records")
    print(target_table.head())

    # 2. Drug-Target relationship table (remove duplicates)
    drug_target_table = df_detailed[['drugbank_id', 'uniprot_id', 'actions', 'known_action']].drop_duplicates()
    print(f"\nDrug-Target relationship: {len(drug_target_table)} records")
    print(drug_target_table.head())

    # 3. Create output directories
    os.makedirs(OUTPUT_DIR_DRUG_INFO, exist_ok=True)
    os.makedirs(OUTPUT_DIR_DRUG_TARGET, exist_ok=True)

    # 4. Save
    target_table.to_csv(OUTPUT_TARGET_INFO, index=False, encoding='utf-8-sig')
    drug_target_table.to_csv(OUTPUT_DRUG_TARGET, index=False, encoding='utf-8-sig')

    print(f"\nTable splitting complete!")
    print(f"- {OUTPUT_TARGET_INFO}")
    print(f"- {OUTPUT_DRUG_TARGET}")

    return target_table, drug_target_table

def main():
    """Main execution function"""

    # Execute extraction
    df_detailed = extract_detailed_data(XML_FILE)

    # Display results
    print(f"\nTotal data count: {len(df_detailed)}")
    print(df_detailed[['drug_name', 'drug_groups', 'gene_name', 'organism', 'actions', 'known_action']].head())

    # Split and save tables
    target_table, drug_target_table = split_and_save_tables(df_detailed)

    # Display statistics
    print(f"\n--- Statistics ---")
    print(f"Total Drug-Target relationships: {len(df_detailed)}")
    print(f"Unique drugs: {df_detailed['drugbank_id'].nunique()}")
    print(f"Unique targets: {len(target_table)}")
    print(f"Unique relationships: {len(drug_target_table)}")

    print(f"\n--- Organism distribution (top 10) ---")
    print(target_table['organism'].value_counts().head(10))

    print(f"\n--- Actions distribution (top 10) ---")
    print(drug_target_table['actions'].value_counts().head(10))

    return df_detailed, target_table, drug_target_table

if __name__ == '__main__':
    df_detailed, target_table, drug_target_table = main()
    print(f"\n✓ Processing complete!")
