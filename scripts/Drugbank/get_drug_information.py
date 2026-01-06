#!/usr/bin/env python3
"""
DrugBank XML Parser - Drug Information Extraction
Extracts drug information from DrugBank XML database
"""

import xml.etree.ElementTree as ET
import pandas as pd
import os

# File paths
XML_FILE = 'raw/drugbank/full database.xml'
OUTPUT_DIR = 'processed/Drugbank/drug_information'
OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'drug_information.csv')

# Namespace
ns = {'db': 'http://www.drugbank.ca'}

def extract_text(element, path):
    """Safely extract text from XML element"""
    found = element.find(path, ns)
    return found.text if found is not None else None

def extract_drug_information():
    """Extract drug information from DrugBank XML"""

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Starting drug list extraction... ({XML_FILE})")

    rows = []
    context = ET.iterparse(XML_FILE, events=('end',))

    for event, elem in context:
        tag = elem.tag.replace(f"{{{ns['db']}}}", "")

        # Process each <drug> tag
        if event == 'end' and tag == 'drug':
            # Skip nested tags (only process root level drugs)
            if 'type' not in elem.attrib:
                elem.clear()
                continue

            try:
                # --- Basic identification ---
                # 1. DrugBank ID (Primary)
                drug_id_elem = elem.find("db:drugbank-id[@primary='true']", ns)
                drug_id = drug_id_elem.text if drug_id_elem is not None else None

                # 2. Drug name
                name = extract_text(elem, "db:name")

                # 3. Drug type (Small Molecule / Biotech)
                drug_type = elem.attrib.get('type')

                # 4. CAS Number (chemical identification number)
                cas_number = extract_text(elem, "db:cas-number")

                # --- Status information ---
                # 5. Groups (Approved, Investigational, etc.)
                groups = [g.text for g in elem.findall("db:groups/db:group", ns)]
                groups_str = "; ".join(groups) if groups else ""

                # --- Structure information ---
                # 6. SMILES and InChIKey (structural identifiers)
                smiles = None
                inchi_key = None

                if drug_type == 'small molecule':
                    for prop in elem.findall("db:calculated-properties/db:property", ns):
                        kind = prop.find("db:kind", ns)
                        if kind is not None:
                            if kind.text == "SMILES":
                                value_elem = prop.find("db:value", ns)
                                if value_elem is not None:
                                    smiles = value_elem.text
                            elif kind.text == "InChIKey":
                                value_elem = prop.find("db:value", ns)
                                if value_elem is not None:
                                    inchi_key = value_elem.text

                # --- Description ---
                # 7. Description (one-line summary)
                description = extract_text(elem, "db:description")
                if description:
                    description = description[:200].replace('\n', ' ') + "..."

                # Add to list (snake_case)
                rows.append({
                    'drugbank_id': drug_id,
                    'name': name,
                    'type': drug_type,
                    'cas_number': cas_number,
                    'groups': groups_str,
                    'smiles': smiles,
                    'inchi_key': inchi_key,
                    'description': description
                })

            except Exception as e:
                print(f"Error processing drug: {e}")

            # Memory cleanup (required)
            elem.clear()

    # Create DataFrame
    df_all_drugs = pd.DataFrame(rows)
    print(f"Total drugs extracted: {len(df_all_drugs)}")

    # Save to CSV
    df_all_drugs.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Saved: {OUTPUT_CSV}")
    print("-" * 50)
    print(df_all_drugs.head())

    # Display statistics
    print("\n--- Missing values (NaN) count ---")
    print(df_all_drugs.isnull().sum())

    print("\n--- Missing values ratio (%) ---")
    missing_ratio = (df_all_drugs.isnull().sum() / len(df_all_drugs)) * 100
    print(missing_ratio.round(2))

    print("\n--- Drug type distribution ---")
    print(df_all_drugs['type'].value_counts())

    return df_all_drugs

if __name__ == '__main__':
    df = extract_drug_information()
    print(f"\n✓ Processing complete: {len(df)} drugs")
