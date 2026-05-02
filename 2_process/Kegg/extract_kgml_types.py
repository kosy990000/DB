"""
KGML 파일들에서 entity type과 relation type 정보 추출
"""

from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

def analyze_kgml_files(kgml_dir: Path):
    """모든 KGML 파일 분석"""

    # 통계 수집
    entry_types = Counter()
    relation_types = Counter()
    relation_subtypes = Counter()
    relation_type_subtype_pairs = Counter()

    # 예시 수집
    entry_type_examples = defaultdict(list)
    relation_type_examples = defaultdict(list)

    kgml_files = list(kgml_dir.glob("*.kgml"))

    for kgml_file in kgml_files:
        try:
            tree = ET.parse(kgml_file)
            root = tree.getroot()
            pathway_id = kgml_file.stem

            # Entry types 수집
            for entry in root.findall('entry'):
                entry_type = entry.attrib.get('type', 'unknown')
                entry_types[entry_type] += 1

                # 처음 3개 예시만 저장
                if len(entry_type_examples[entry_type]) < 3:
                    entry_info = {
                        'pathway_id': pathway_id,
                        'id': entry.attrib.get('id'),
                        'name': entry.attrib.get('name', '')[:50],  # 너무 길면 자르기
                        'link': entry.attrib.get('link', '')
                    }
                    entry_type_examples[entry_type].append(entry_info)

            # Relation types 수집
            for rel in root.findall('relation'):
                rel_type = rel.attrib.get('type', 'unknown')
                relation_types[rel_type] += 1

                # Subtypes 수집
                subtypes = [st.attrib['name'] for st in rel.findall('subtype')]
                for subtype in subtypes:
                    relation_subtypes[subtype] += 1
                    relation_type_subtype_pairs[(rel_type, subtype)] += 1

                # 처음 3개 예시만 저장
                if len(relation_type_examples[rel_type]) < 3:
                    rel_info = {
                        'pathway_id': pathway_id,
                        'entry1': rel.attrib.get('entry1'),
                        'entry2': rel.attrib.get('entry2'),
                        'type': rel_type,
                        'subtypes': subtypes
                    }
                    relation_type_examples[rel_type].append(rel_info)

        except Exception as e:
            print(f"Error parsing {kgml_file.name}: {e}")

    return {
        'total_files': len(kgml_files),
        'entry_types': entry_types,
        'relation_types': relation_types,
        'relation_subtypes': relation_subtypes,
        'relation_type_subtype_pairs': relation_type_subtype_pairs,
        'entry_type_examples': dict(entry_type_examples),
        'relation_type_examples': dict(relation_type_examples)
    }


def print_results(results):
    """결과 출력"""

    print("=" * 80)
    print(f"KEGG PATHWAY KGML FILES ANALYSIS")
    print(f"Total files analyzed: {results['total_files']}")
    print("=" * 80)

    # Entity Types
    print("\n" + "=" * 80)
    print("ENTRY TYPES")
    print("=" * 80)
    print(f"{'Type':<20} {'Count':<15} {'Percentage':<15}")
    print("-" * 80)

    total_entries = sum(results['entry_types'].values())
    for entry_type, count in results['entry_types'].most_common():
        percentage = (count / total_entries * 100)
        print(f"{entry_type:<20} {count:<15,} {percentage:<15.2f}%")

    print(f"\nTotal entries: {total_entries:,}")

    # Entry Type Examples
    print("\n" + "=" * 80)
    print("ENTRY TYPE EXAMPLES")
    print("=" * 80)

    for entry_type in results['entry_types'].keys():
        examples = results['entry_type_examples'].get(entry_type, [])
        print(f"\n{entry_type.upper()}:")
        for i, ex in enumerate(examples[:3], 1):
            print(f"  Example {i}:")
            print(f"    Pathway: {ex['pathway_id']}")
            print(f"    ID: {ex['id']}")
            print(f"    Name: {ex['name']}")
            if ex['link']:
                print(f"    Link: {ex['link']}")

    # Relation Types
    print("\n" + "=" * 80)
    print("RELATION TYPES")
    print("=" * 80)
    print(f"{'Type':<20} {'Count':<15} {'Percentage':<15}")
    print("-" * 80)

    total_relations = sum(results['relation_types'].values())
    for rel_type, count in results['relation_types'].most_common():
        percentage = (count / total_relations * 100)
        print(f"{rel_type:<20} {count:<15,} {percentage:<15.2f}%")

    print(f"\nTotal relations: {total_relations:,}")

    # Relation Type Examples
    print("\n" + "=" * 80)
    print("RELATION TYPE EXAMPLES")
    print("=" * 80)

    for rel_type in results['relation_types'].keys():
        examples = results['relation_type_examples'].get(rel_type, [])
        print(f"\n{rel_type.upper()}:")
        for i, ex in enumerate(examples[:3], 1):
            print(f"  Example {i}:")
            print(f"    Pathway: {ex['pathway_id']}")
            print(f"    Entry1 → Entry2: {ex['entry1']} → {ex['entry2']}")
            print(f"    Subtypes: {', '.join(ex['subtypes']) if ex['subtypes'] else 'None'}")

    # Relation Subtypes
    print("\n" + "=" * 80)
    print("RELATION SUBTYPES")
    print("=" * 80)
    print(f"{'Subtype':<30} {'Count':<15} {'Percentage':<15}")
    print("-" * 80)

    total_subtypes = sum(results['relation_subtypes'].values())
    for subtype, count in results['relation_subtypes'].most_common():
        percentage = (count / total_subtypes * 100)
        print(f"{subtype:<30} {count:<15,} {percentage:<15.2f}%")

    print(f"\nTotal subtypes: {total_subtypes:,}")

    # Relation Type + Subtype Pairs
    print("\n" + "=" * 80)
    print("RELATION TYPE + SUBTYPE COMBINATIONS (Top 20)")
    print("=" * 80)
    print(f"{'Relation Type':<20} {'Subtype':<30} {'Count':<15}")
    print("-" * 80)

    for (rel_type, subtype), count in results['relation_type_subtype_pairs'].most_common(20):
        print(f"{rel_type:<20} {subtype:<30} {count:<15,}")


def save_markdown_summary(results, output_file: Path):
    """Markdown 형식으로 저장 (노션에 붙여넣기 용이)"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# KEGG PATHWAY KGML Analysis\n\n")
        f.write(f"Total files analyzed: **{results['total_files']}**\n\n")

        # Entry Types
        f.write("## Entry Types\n\n")
        f.write("| Type | Count | Percentage |\n")
        f.write("|------|-------|------------|\n")

        total_entries = sum(results['entry_types'].values())
        for entry_type, count in results['entry_types'].most_common():
            percentage = (count / total_entries * 100)
            f.write(f"| {entry_type} | {count:,} | {percentage:.2f}% |\n")

        f.write(f"\n**Total entries:** {total_entries:,}\n\n")

        # Entry Type Descriptions
        f.write("### Entry Type Descriptions\n\n")

        entry_descriptions = {
            'gene': 'Gene product (protein, enzyme)',
            'compound': 'Chemical compound, metabolite',
            'map': 'Link to another pathway map',
            'ortholog': 'Ortholog group (KO)',
            'group': 'Complex of genes/proteins',
            'other': 'Other biological entities'
        }

        for entry_type in results['entry_types'].keys():
            desc = entry_descriptions.get(entry_type, 'Unknown type')
            examples = results['entry_type_examples'].get(entry_type, [])

            f.write(f"**{entry_type}**: {desc}\n\n")
            if examples:
                f.write("Examples:\n")
                for ex in examples[:2]:
                    f.write(f"- Pathway: `{ex['pathway_id']}`, Name: `{ex['name']}`\n")
                f.write("\n")

        # Relation Types
        f.write("## Relation Types\n\n")
        f.write("| Type | Count | Percentage |\n")
        f.write("|------|-------|------------|\n")

        total_relations = sum(results['relation_types'].values())
        for rel_type, count in results['relation_types'].most_common():
            percentage = (count / total_relations * 100)
            f.write(f"| {rel_type} | {count:,} | {percentage:.2f}% |\n")

        f.write(f"\n**Total relations:** {total_relations:,}\n\n")

        # Relation Type Descriptions
        f.write("### Relation Type Descriptions\n\n")

        relation_descriptions = {
            'PPrel': 'Protein-Protein interaction (enzyme-enzyme relation)',
            'ECrel': 'Enzyme-Compound relation',
            'GErel': 'Gene Expression interaction',
            'PCrel': 'Protein-Compound interaction',
            'maplink': 'Link between pathway maps'
        }

        for rel_type in results['relation_types'].keys():
            desc = relation_descriptions.get(rel_type, 'Unknown relation type')
            examples = results['relation_type_examples'].get(rel_type, [])

            f.write(f"**{rel_type}**: {desc}\n\n")
            if examples:
                f.write("Examples:\n")
                for ex in examples[:2]:
                    subtypes_str = ', '.join(ex['subtypes']) if ex['subtypes'] else 'None'
                    f.write(f"- Pathway: `{ex['pathway_id']}`, Subtypes: `{subtypes_str}`\n")
                f.write("\n")

        # Subtypes
        f.write("## Relation Subtypes\n\n")
        f.write("| Subtype | Count | Percentage |\n")
        f.write("|---------|-------|------------|\n")

        total_subtypes = sum(results['relation_subtypes'].values())
        for subtype, count in results['relation_subtypes'].most_common():
            percentage = (count / total_subtypes * 100)
            f.write(f"| {subtype} | {count:,} | {percentage:.2f}% |\n")

        f.write(f"\n**Total subtypes:** {total_subtypes:,}\n\n")

        # Top combinations
        f.write("## Top Relation Type + Subtype Combinations\n\n")
        f.write("| Relation Type | Subtype | Count |\n")
        f.write("|---------------|---------|-------|\n")

        for (rel_type, subtype), count in results['relation_type_subtype_pairs'].most_common(15):
            f.write(f"| {rel_type} | {subtype} | {count:,} |\n")


if __name__ == "__main__":
    kgml_dir = Path("data-human/kgml_hsa")

    print("Analyzing KGML files...")
    results = analyze_kgml_files(kgml_dir)

    print_results(results)

    # Save markdown summary
    output_file = Path("kgml_analysis_summary.md")
    save_markdown_summary(results, output_file)
    print(f"\n\nMarkdown summary saved to: {output_file}")
