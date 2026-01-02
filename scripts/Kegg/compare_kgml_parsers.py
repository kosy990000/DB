"""
BioPython KGML parser와 기존 xml.etree.ElementTree parser 비교 스크립트
"""

from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
from Bio.KEGG.KGML import KGML_parser


def parse_with_biopython(kgml_file: Path):
    """BioPython KGML parser로 파싱"""
    with open(kgml_file, 'r') as f:
        pathway = KGML_parser.read(f)

    # 기본 정보
    info = {
        'title': pathway.title,
        'name': pathway.name,
        'org': pathway.org,
        'number': pathway.number,
        'total_entries': len(pathway.entries),
        'gene_entries': len(pathway.genes),
        'total_relations': len(pathway.relations)
    }

    # Gene entries 추출
    genes = {}
    for entry in pathway.genes:
        # BioPython은 entry.id를 int로 반환하므로 str로 변환
        genes[str(entry.id)] = {
            'name': entry.name,
            'type': entry.type,
            'graphics_name': entry.graphics[0].name if entry.graphics else None
        }

    # Relations 추출
    relations = []
    for rel in pathway.relations:
        # BioPython subtypes는 (name, value) 튜플의 리스트
        # BioPython은 entry ID를 int로 반환하므로 str로 변환
        rel_info = {
            'entry1': str(rel.entry1.id),
            'entry2': str(rel.entry2.id),
            'type': rel.type,
            'subtypes': [st[0] if isinstance(st, tuple) else st for st in rel.subtypes]
        }
        relations.append(rel_info)

    return info, genes, relations


def parse_with_elementtree(kgml_file: Path):
    """xml.etree.ElementTree로 파싱 (기존 방식)"""
    tree = ET.parse(kgml_file)
    root = tree.getroot()

    # 기본 정보
    info = {
        'title': root.attrib.get('title', ''),
        'name': root.attrib.get('name', ''),
        'org': root.attrib.get('org', ''),
        'number': root.attrib.get('number', ''),
    }

    # Gene entries
    genes = {}
    all_entries = root.findall('entry')
    gene_entries = [e for e in all_entries if e.attrib.get('type') == 'gene']

    info['total_entries'] = len(all_entries)
    info['gene_entries'] = len(gene_entries)

    for entry in gene_entries:
        entry_id = entry.attrib['id']
        graphics = entry.find('graphics')
        genes[entry_id] = {
            'name': entry.attrib.get('name', ''),
            'type': entry.attrib.get('type', ''),
            'graphics_name': graphics.attrib.get('name') if graphics is not None else None
        }

    # Relations
    relations = []
    for rel in root.findall('relation'):
        rel_info = {
            'entry1': rel.attrib.get('entry1'),
            'entry2': rel.attrib.get('entry2'),
            'type': rel.attrib.get('type'),
            'subtypes': [st.attrib['name'] for st in rel.findall('subtype')]
        }
        relations.append(rel_info)

    info['total_relations'] = len(relations)

    return info, genes, relations


def convert_to_edges(kgml_file: Path, relations, genes):
    """Relations을 gene-gene edges로 변환 (기존 로직)"""
    pathway_id = kgml_file.stem

    # entry_id → gene list 매핑
    entry2genes = {}
    for entry_id, gene_info in genes.items():
        name = gene_info['name']
        entry2genes[entry_id] = name.split()

    rows = []
    for rel in relations:
        e1 = rel['entry1']
        e2 = rel['entry2']
        rel_type = rel['type']
        subtypes = rel['subtypes']

        if e1 in entry2genes and e2 in entry2genes:
            subtype = "|".join(subtypes) if subtypes else "NA"

            for g1 in entry2genes[e1]:
                for g2 in entry2genes[e2]:
                    entrez_id1 = g1.split(":")[-1] if ":" in g1 else g1
                    entrez_id2 = g2.split(":")[-1] if ":" in g2 else g2

                    rows.append({
                        "source_entrez_id": entrez_id1,
                        "target_entrez_id": entrez_id2,
                        "relation_type": rel_type,
                        "subtype": subtype,
                        "pathway_id": pathway_id
                    })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def compare_parsers(kgml_file: Path, csv_file: Path = None):
    """두 parser 비교"""
    print(f"\n{'='*80}")
    print(f"Comparing parsers for: {kgml_file.name}")
    print(f"{'='*80}\n")

    # BioPython으로 파싱
    print("1. Parsing with BioPython KGML_parser...")
    bio_info, bio_genes, bio_relations = parse_with_biopython(kgml_file)

    # ElementTree로 파싱
    print("2. Parsing with xml.etree.ElementTree...")
    et_info, et_genes, et_relations = parse_with_elementtree(kgml_file)

    # 기본 정보 비교
    print("\n" + "="*80)
    print("BASIC INFORMATION COMPARISON")
    print("="*80)
    print(f"{'Attribute':<20} {'BioPython':<30} {'ElementTree':<30} {'Match':<10}")
    print("-"*80)

    for key in ['title', 'name', 'org', 'number', 'total_entries', 'gene_entries', 'total_relations']:
        bio_val = bio_info.get(key, 'N/A')
        et_val = et_info.get(key, 'N/A')
        match = "✓" if bio_val == et_val else "✗"
        print(f"{key:<20} {str(bio_val):<30} {str(et_val):<30} {match:<10}")

    # Gene entries 비교
    print("\n" + "="*80)
    print("GENE ENTRIES COMPARISON")
    print("="*80)
    print(f"BioPython gene entries: {len(bio_genes)}")
    print(f"ElementTree gene entries: {len(et_genes)}")

    bio_gene_ids = set(bio_genes.keys())
    et_gene_ids = set(et_genes.keys())

    only_bio = bio_gene_ids - et_gene_ids
    only_et = et_gene_ids - bio_gene_ids
    common = bio_gene_ids & et_gene_ids

    print(f"Common gene entries: {len(common)}")
    print(f"Only in BioPython: {len(only_bio)}")
    print(f"Only in ElementTree: {len(only_et)}")

    if only_bio:
        print(f"\nGene IDs only in BioPython: {sorted(only_bio)[:10]}{'...' if len(only_bio) > 10 else ''}")
    if only_et:
        print(f"Gene IDs only in ElementTree: {sorted(only_et)[:10]}{'...' if len(only_et) > 10 else ''}")

    # Relations 비교
    print("\n" + "="*80)
    print("RELATIONS COMPARISON")
    print("="*80)
    print(f"BioPython relations: {len(bio_relations)}")
    print(f"ElementTree relations: {len(et_relations)}")

    # Relations을 튜플로 변환해서 비교
    bio_rel_set = set()
    for rel in bio_relations:
        rel_tuple = (rel['entry1'], rel['entry2'], rel['type'], tuple(sorted(rel['subtypes'])))
        bio_rel_set.add(rel_tuple)

    et_rel_set = set()
    for rel in et_relations:
        rel_tuple = (rel['entry1'], rel['entry2'], rel['type'], tuple(sorted(rel['subtypes'])))
        et_rel_set.add(rel_tuple)

    only_bio_rel = bio_rel_set - et_rel_set
    only_et_rel = et_rel_set - bio_rel_set
    common_rel = bio_rel_set & et_rel_set

    print(f"Common relations: {len(common_rel)}")
    print(f"Only in BioPython: {len(only_bio_rel)}")
    print(f"Only in ElementTree: {len(only_et_rel)}")

    if only_bio_rel:
        print(f"\nRelations only in BioPython (first 5):")
        for rel in list(only_bio_rel)[:5]:
            print(f"  {rel}")

    if only_et_rel:
        print(f"\nRelations only in ElementTree (first 5):")
        for rel in list(only_et_rel)[:5]:
            print(f"  {rel}")

    # Edge 변환 비교 (기존 CSV와 비교)
    print("\n" + "="*80)
    print("EDGE CONVERSION COMPARISON")
    print("="*80)

    # BioPython으로부터 edges 생성
    bio_edges = convert_to_edges(kgml_file, bio_relations, bio_genes)
    print(f"Edges from BioPython parser: {len(bio_edges)}")

    # ElementTree로부터 edges 생성
    et_edges = convert_to_edges(kgml_file, et_relations, et_genes)
    print(f"Edges from ElementTree parser: {len(et_edges)}")

    # 기존 CSV 읽기 (있으면)
    if csv_file and csv_file.exists():
        existing_edges = pd.read_csv(csv_file)
        print(f"Edges in existing CSV: {len(existing_edges)}")

        # DataFrame 비교
        print("\nComparing edge DataFrames...")

        # 데이터 타입 통일 (모두 문자열로)
        for df in [bio_edges, et_edges, existing_edges]:
            df['source_entrez_id'] = df['source_entrez_id'].astype(str)
            df['target_entrez_id'] = df['target_entrez_id'].astype(str)

        # 정렬해서 비교 (모든 컬럼으로 정렬)
        sort_cols = ['source_entrez_id', 'target_entrez_id', 'relation_type', 'subtype']
        bio_edges_sorted = bio_edges.sort_values(sort_cols).reset_index(drop=True)
        et_edges_sorted = et_edges.sort_values(sort_cols).reset_index(drop=True)
        existing_edges_sorted = existing_edges.sort_values(sort_cols).reset_index(drop=True)

        # ElementTree와 기존 CSV 비교
        if et_edges_sorted.equals(existing_edges_sorted):
            print("✓ ElementTree edges match existing CSV perfectly")
        else:
            print("✗ ElementTree edges differ from existing CSV")
            # 차이점 찾기
            merged = et_edges_sorted.merge(
                existing_edges_sorted,
                how='outer',
                indicator=True,
                on=['source_entrez_id', 'target_entrez_id', 'relation_type', 'subtype', 'pathway_id']
            )
            only_et = merged[merged['_merge'] == 'left_only']
            only_csv = merged[merged['_merge'] == 'right_only']
            print(f"  Edges only in ElementTree: {len(only_et)}")
            print(f"  Edges only in CSV: {len(only_csv)}")

        # BioPython과 기존 CSV 비교
        if bio_edges_sorted.equals(existing_edges_sorted):
            print("✓ BioPython edges match existing CSV perfectly")
        else:
            print("✗ BioPython edges differ from existing CSV")
            merged = bio_edges_sorted.merge(
                existing_edges_sorted,
                how='outer',
                indicator=True,
                on=['source_entrez_id', 'target_entrez_id', 'relation_type', 'subtype', 'pathway_id']
            )
            only_bio = merged[merged['_merge'] == 'left_only']
            only_csv = merged[merged['_merge'] == 'right_only']
            print(f"  Edges only in BioPython: {len(only_bio)}")
            print(f"  Edges only in CSV: {len(only_csv)}")

            if len(only_bio) > 0:
                print("\nSample edges only in BioPython (first 5):")
                print(only_bio[['source_entrez_id', 'target_entrez_id', 'relation_type', 'subtype']].head())

            if len(only_csv) > 0:
                print("\nSample edges only in CSV (first 5):")
                print(only_csv[['source_entrez_id', 'target_entrez_id', 'relation_type', 'subtype']].head())

    # BioPython vs ElementTree edges 비교
    if bio_edges_sorted.equals(et_edges_sorted):
        print("\n✓ BioPython and ElementTree produce identical edges")
    else:
        print("\n✗ BioPython and ElementTree produce different edges")
        merged = bio_edges_sorted.merge(
            et_edges_sorted,
            how='outer',
            indicator=True,
            on=['source_entrez_id', 'target_entrez_id', 'relation_type', 'subtype', 'pathway_id']
        )
        only_bio = merged[merged['_merge'] == 'left_only']
        only_et = merged[merged['_merge'] == 'right_only']
        print(f"  Edges only in BioPython: {len(only_bio)}")
        print(f"  Edges only in ElementTree: {len(only_et)}")

    print("\n" + "="*80 + "\n")

    return {
        'bio_info': bio_info,
        'et_info': et_info,
        'bio_genes': bio_genes,
        'et_genes': et_genes,
        'bio_relations': bio_relations,
        'et_relations': et_relations,
        'bio_edges': bio_edges,
        'et_edges': et_edges
    }


if __name__ == "__main__":
    # hsa04110 (Cell Cycle) pathway로 테스트
    kgml_file = Path("data-human/kgml_hsa/hsa04110.kgml")
    csv_file = Path("data-human/human_pathway_edges/hsa04110.csv")

    results = compare_parsers(kgml_file, csv_file)
