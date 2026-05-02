#!/usr/bin/env python3
"""
약물 이름으로 ChEMBL, DrugBank, PubChem에서 검색하고
타겟 유전자와 pathway 정보를 가져오는 스크립트
"""

import sqlite3
import json
from typing import Dict, List, Any
from collections import defaultdict


class DrugSearcher:
    def __init__(self, db_path: str):
        """SQLite 데이터베이스 연결 초기화"""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search_drug(self, drug_name: str) -> Dict[str, Any]:
        """
        약물 이름으로 검색하여 모든 정보 반환

        Args:
            drug_name: 검색할 약물 이름

        Returns:
            검색 결과 딕셔너리
        """
        result = {
            'query': drug_name,
            'chembl': self._search_chembl(drug_name),
            'drugbank': self._search_drugbank(drug_name),
            'pubchem': self._search_pubchem(drug_name),
            'targets': defaultdict(list),
            'pathways': defaultdict(list)
        }

        # ChEMBL targets 및 pathways
        if result['chembl']['found']:
            for drug in result['chembl']['drugs']:
                chembl_id = drug['chembl_id']
                targets = self._get_chembl_targets(chembl_id)
                result['targets']['chembl'].extend(targets)

                # 각 target의 pathway 정보 수집
                for target in targets:
                    if 'gene_symbol' in target and target['gene_symbol']:
                        pathways = self._get_pathways_by_gene(target['gene_symbol'])
                        for pw in pathways:
                            if pw not in result['pathways']['chembl']:
                                result['pathways']['chembl'].append(pw)

        # DrugBank targets 및 pathways
        if result['drugbank']['found']:
            for drug in result['drugbank']['drugs']:
                drugbank_id = drug['drugbank_id']
                targets = self._get_drugbank_targets(drugbank_id)
                result['targets']['drugbank'].extend(targets)

                # 각 target의 pathway 정보 수집
                for target in targets:
                    if 'gene_symbol' in target and target['gene_symbol']:
                        pathways = self._get_pathways_by_gene(target['gene_symbol'])
                        for pw in pathways:
                            if pw not in result['pathways']['drugbank']:
                                result['pathways']['drugbank'].append(pw)

        # PubChem은 target 정보가 없으므로 건너뜀

        return result

    def _search_chembl(self, drug_name: str) -> Dict[str, Any]:
        """ChEMBL에서 약물 검색"""
        cursor = self.conn.cursor()

        # 이름 또는 synonym으로 검색
        query = """
        SELECT DISTINCT c.chembl_id, c.name, c.max_phase, c.first_approval, c.smiles
        FROM chembl_compounds c
        LEFT JOIN chembl_synonyms s ON c.chembl_id = s.chembl_id
        WHERE LOWER(c.name) LIKE LOWER(?)
           OR LOWER(s.synonym) LIKE LOWER(?)
        LIMIT 50
        """

        search_term = f"%{drug_name}%"
        cursor.execute(query, (search_term, search_term))

        drugs = [dict(row) for row in cursor.fetchall()]

        return {
            'found': len(drugs) > 0,
            'count': len(drugs),
            'drugs': drugs
        }

    def _search_drugbank(self, drug_name: str) -> Dict[str, Any]:
        """DrugBank에서 약물 검색"""
        cursor = self.conn.cursor()

        query = """
        SELECT DISTINCT drugbank_id, name, type, groups, description
        FROM drugbank_drugs
        WHERE LOWER(name) LIKE LOWER(?)
        LIMIT 50
        """

        search_term = f"%{drug_name}%"
        cursor.execute(query, (search_term,))

        drugs = [dict(row) for row in cursor.fetchall()]

        return {
            'found': len(drugs) > 0,
            'count': len(drugs),
            'drugs': drugs
        }

    def _search_pubchem(self, drug_name: str) -> Dict[str, Any]:
        """PubChem에서 약물 검색"""
        cursor = self.conn.cursor()

        # title 또는 synonym으로 검색
        query = """
        SELECT DISTINCT c.cid, c.title, c.smiles
        FROM pubchem_compounds c
        LEFT JOIN pubchem_compound_synonyms s ON c.cid = s.cid
        WHERE LOWER(c.title) LIKE LOWER(?)
           OR LOWER(s.synonym) LIKE LOWER(?)
        LIMIT 50
        """

        search_term = f"%{drug_name}%"
        cursor.execute(query, (search_term, search_term))

        compounds = [dict(row) for row in cursor.fetchall()]

        return {
            'found': len(compounds) > 0,
            'count': len(compounds),
            'compounds': compounds
        }

    def _get_chembl_targets(self, chembl_id: str) -> List[Dict[str, Any]]:
        """ChEMBL 약물의 타겟 유전자 정보"""
        cursor = self.conn.cursor()

        query = """
        SELECT DISTINCT
            ct.target_chembl_id,
            ct.target_name,
            ct.target_type,
            ct.species,
            u.gene_symbol,
            u.uniprot_id,
            dtr.pchembl_value,
            dtr.standard_type,
            dtr.standard_value,
            dtr.standard_unit,
            dtr.confidence_score
        FROM chembl_drug_target_relations dtr
        JOIN chembl_targets ct ON dtr.target_chembl_id = ct.target_chembl_id
        LEFT JOIN chembl_target_uniprot_mappings ctum ON ct.target_chembl_id = ctum.target_chembl_id
        LEFT JOIN uniprot u ON ctum.uniprot_id = u.uniprot_id
        WHERE dtr.drug_chembl_id = ?
          AND dtr.confidence_score >= 7
        ORDER BY dtr.pchembl_value DESC NULLS LAST
        LIMIT 100
        """

        cursor.execute(query, (chembl_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_drugbank_targets(self, drugbank_id: str) -> List[Dict[str, Any]]:
        """DrugBank 약물의 타겟 유전자 정보"""
        cursor = self.conn.cursor()

        query = """
        SELECT DISTINCT
            dt.gene_symbol,
            dt.uniprot_id,
            dt.organism,
            dt.target_name,
            dtr.actions,
            dtr.known_action
        FROM drugbank_drug_target_relations dtr
        JOIN drugbank_targets dt ON dtr.uniprot_id = dt.uniprot_id
        WHERE dtr.drugbank_id = ?
        """

        cursor.execute(query, (drugbank_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_pathways_by_gene(self, gene_symbol: str) -> List[Dict[str, Any]]:
        """유전자 심볼로 KEGG 및 Reactome pathway 검색"""
        pathways = []

        # KEGG pathways
        kegg_pathways = self._get_kegg_pathways(gene_symbol)
        pathways.extend([{**pw, 'source': 'KEGG'} for pw in kegg_pathways])

        # Reactome pathways
        reactome_pathways = self._get_reactome_pathways(gene_symbol)
        pathways.extend([{**pw, 'source': 'Reactome'} for pw in reactome_pathways])

        return pathways

    def _get_kegg_pathways(self, gene_symbol: str) -> List[Dict[str, Any]]:
        """KEGG pathway 검색"""
        cursor = self.conn.cursor()

        # gene_symbol로 entrez_id를 찾고, KEGG genes를 찾은 후 pathway를 찾음
        query = """
        SELECT DISTINCT
            kp.pathway_id,
            kp.pathway_name,
            kp.organism,
            kp.species,
            kp.link
        FROM ncbi_info ni
        JOIN kegg_genes kg ON ni.entrez_id = kg.entrez_id
        LEFT JOIN kegg_gene_group_members kgm ON kg.gene_id = kgm.member_gene_id
        JOIN kegg_edges ke ON (ke.source_id = kg.gene_id OR ke.target_id = kg.gene_id
                               OR ke.source_id = kgm.group_id OR ke.target_id = kgm.group_id)
        JOIN kegg_pathway kp ON ke.pathway_id = kp.pathway_id
        WHERE LOWER(ni.gene_symbol) = LOWER(?)
        """

        cursor.execute(query, (gene_symbol,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_reactome_pathways(self, gene_symbol: str) -> List[Dict[str, Any]]:
        """Reactome pathway 검색"""
        cursor = self.conn.cursor()

        # gene_symbol로 ensembl_id를 찾고 reactome pathway를 찾음
        query = """
        SELECT DISTINCT
            rp.reactome_pathway_id,
            rp.pathway_name,
            rp.organism
        FROM ncbi_info ni
        JOIN ncbi_ensembl ne ON ni.entrez_id = ne.entrez_id
        JOIN reactome_pathway_genes rpg ON ne.ensembl_id = rpg.ensembl_id
        JOIN reactome_pathway rp ON rpg.reactome_pathway_id = rp.reactome_pathway_id
        WHERE LOWER(ni.gene_symbol) = LOWER(?)
        """

        cursor.execute(query, (gene_symbol,))
        return [dict(row) for row in cursor.fetchall()]

    def print_results(self, result: Dict[str, Any]):
        """검색 결과를 보기 좋게 출력"""
        print(f"\n{'='*80}")
        print(f"검색어: {result['query']}")
        print(f"{'='*80}\n")

        # ChEMBL
        print(f"[ChEMBL]")
        if result['chembl']['found']:
            print(f"  발견: {result['chembl']['count']}개")
            for drug in result['chembl']['drugs'][:5]:  # 상위 5개만 표시
                print(f"  - {drug['chembl_id']}: {drug['name']} (Phase: {drug['max_phase']})")
        else:
            print(f"  발견 안됨")

        # DrugBank
        print(f"\n[DrugBank]")
        if result['drugbank']['found']:
            print(f"  발견: {result['drugbank']['count']}개")
            for drug in result['drugbank']['drugs'][:5]:
                print(f"  - {drug['drugbank_id']}: {drug['name']} ({drug['type']}, {drug['groups']})")
        else:
            print(f"  발견 안됨")

        # PubChem
        print(f"\n[PubChem]")
        if result['pubchem']['found']:
            print(f"  발견: {result['pubchem']['count']}개")
            for comp in result['pubchem']['compounds'][:5]:
                print(f"  - CID {comp['cid']}: {comp['title']}")
        else:
            print(f"  발견 안됨")

        # Target Genes
        print(f"\n[Target Genes]")
        if result['targets']['chembl']:
            print(f"  ChEMBL Targets: {len(result['targets']['chembl'])}개")
            genes = set()
            for t in result['targets']['chembl']:
                if t.get('gene_symbol'):
                    genes.add(f"{t['gene_symbol']} ({t['target_name']})")
            for gene in sorted(genes)[:10]:
                print(f"    - {gene}")

        if result['targets']['drugbank']:
            print(f"  DrugBank Targets: {len(result['targets']['drugbank'])}개")
            genes = set()
            for t in result['targets']['drugbank']:
                if t.get('gene_symbol'):
                    genes.add(f"{t['gene_symbol']} ({t['target_name']})")
            for gene in sorted(genes)[:10]:
                print(f"    - {gene}")

        # Pathways
        print(f"\n[Pathways]")
        if result['pathways']['chembl']:
            print(f"  ChEMBL 관련 Pathways: {len(result['pathways']['chembl'])}개")
            for pw in result['pathways']['chembl'][:10]:
                print(f"    - [{pw['source']}] {pw.get('pathway_name', pw.get('reactome_pathway_id'))}")

        if result['pathways']['drugbank']:
            print(f"  DrugBank 관련 Pathways: {len(result['pathways']['drugbank'])}개")
            for pw in result['pathways']['drugbank'][:10]:
                print(f"    - [{pw['source']}] {pw.get('pathway_name', pw.get('reactome_pathway_id'))}")

        print(f"\n{'='*80}\n")

    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()


def main():
    """메인 함수"""
    import sys

    if len(sys.argv) < 2:
        print("사용법: python search_drug.py <약물이름> [데이터베이스경로]")
        print("예시: python search_drug.py aspirin")
        print("      python search_drug.py aspirin /path/to/database.db")
        sys.exit(1)

    drug_name = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "drugs.db"

    try:
        searcher = DrugSearcher(db_path)
        result = searcher.search_drug(drug_name)
        searcher.print_results(result)

        # JSON 파일로도 저장
        output_file = f"search_result_{drug_name.replace(' ', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"상세 결과가 {output_file}에 저장되었습니다.")

        searcher.close()

    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
