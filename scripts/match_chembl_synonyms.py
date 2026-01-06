#!/usr/bin/env python3
"""
ChEMBL Synonym으로 DrugBank/PubChem 매칭 스크립트
작성일: 2026-01-06
"""

import sqlite3
import argparse
from pathlib import Path


def match_by_synonym(cursor, chembl_id):
    """ChEMBL ID의 synonym으로 DrugBank 매칭"""
    # ChEMBL synonyms 가져오기
    cursor.execute("""
        SELECT synonym, synonym_type
        FROM chembl_synonyms
        WHERE chembl_id = ?
    """, (chembl_id,))

    synonyms = cursor.fetchall()

    # DrugBank 매칭
    drugbank_matches = []
    for syn, syn_type in synonyms:
        cursor.execute("""
            SELECT drugbank_id, name, groups, type
            FROM drugbank_drugs
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
            LIMIT 1
        """, (syn,))

        match = cursor.fetchone()
        if match:
            drugbank_matches.append({
                'synonym': syn,
                'synonym_type': syn_type,
                'drugbank_id': match[0],
                'drugbank_name': match[1],
                'groups': match[2],
                'type': match[3]
            })

    return synonyms, drugbank_matches


def match_by_inchi(cursor, chembl_id):
    """ChEMBL ID의 InChI Key로 DrugBank 매칭"""
    cursor.execute("""
        SELECT cc.inchi_key, dd.drugbank_id, dd.name, dd.groups
        FROM chembl_compounds cc
        LEFT JOIN drugbank_drugs dd ON cc.inchi_key = dd.inchi_key
        WHERE cc.chembl_id = ?
          AND cc.inchi_key IS NOT NULL
    """, (chembl_id,))

    return cursor.fetchone()


def analyze_single_compound(cursor, chembl_id, verbose=True):
    """단일 ChEMBL compound 분석"""
    # ChEMBL 정보 가져오기
    cursor.execute("""
        SELECT chembl_id, name, smiles, inchi_key, max_phase
        FROM chembl_compounds
        WHERE chembl_id = ?
    """, (chembl_id,))

    compound_info = cursor.fetchone()
    if not compound_info:
        print(f"❌ ChEMBL ID {chembl_id}를 찾을 수 없습니다.")
        return None

    chembl_id, name, _smiles, inchi_key, max_phase = compound_info

    if verbose:
        print(f"\n{'='*80}")
        print(f"🔬 ChEMBL Compound: {chembl_id}")
        print(f"{'='*80}")
        print(f"Name: {name}")
        print(f"Max Phase: {max_phase}")
        print(f"InChI Key: {inchi_key if inchi_key else 'N/A'}")

    # Synonym 매칭
    synonyms, syn_matches = match_by_synonym(cursor, chembl_id)

    if verbose:
        print(f"\n📝 Synonyms: {len(synonyms)}개")
        for syn, syn_type in synonyms[:10]:
            print(f"  - {syn} ({syn_type})")
        if len(synonyms) > 10:
            print(f"  ... and {len(synonyms) - 10} more")

    # DrugBank 매칭 결과
    if verbose:
        print(f"\n🔗 DrugBank 매칭:")

        # InChI Key 매칭
        inchi_match = match_by_inchi(cursor, chembl_id)
        if inchi_match and inchi_match[1]:
            print(f"\n  ✅ InChI Key 매칭:")
            print(f"     {inchi_match[1]}: {inchi_match[2]} ({inchi_match[3]})")

        # Synonym 매칭
        if syn_matches:
            print(f"\n  ✅ Synonym 매칭: {len(syn_matches)}개")
            for match in syn_matches:
                print(f"     '{match['synonym']}' → {match['drugbank_id']}: {match['drugbank_name']}")
                print(f"       Groups: {match['groups']}, Type: {match['type']}")

        if not inchi_match and not syn_matches:
            print(f"  ⚠️ DrugBank 매칭 없음")

    return {
        'chembl_id': chembl_id,
        'name': name,
        'synonyms': synonyms,
        'inchi_match': inchi_match,
        'synonym_matches': syn_matches
    }


def analyze_multiple_compounds(cursor, chembl_ids):
    """여러 ChEMBL compound 분석"""
    results = []

    for chembl_id in chembl_ids:
        result = analyze_single_compound(cursor, chembl_id, verbose=True)
        if result:
            results.append(result)
        print()  # 구분선

    # 전체 통계
    print(f"\n{'='*80}")
    print(f"📊 전체 통계")
    print(f"{'='*80}")

    total = len(results)
    inchi_matched = sum(1 for r in results if r['inchi_match'] and r['inchi_match'][1])
    syn_matched = sum(1 for r in results if r['synonym_matches'])

    print(f"전체 분석: {total}개")
    print(f"InChI Key 매칭: {inchi_matched}개 ({inchi_matched/total*100:.1f}%)")
    print(f"Synonym 매칭: {syn_matched}개 ({syn_matched/total*100:.1f}%)")

    return results


def search_by_name(cursor, compound_name, limit=10):
    """화합물 이름으로 ChEMBL 검색"""
    cursor.execute("""
        SELECT chembl_id, name, max_phase
        FROM chembl_compounds
        WHERE LOWER(name) LIKE LOWER(?)
        LIMIT ?
    """, (f'%{compound_name}%', limit))

    results = cursor.fetchall()

    print(f"\n🔍 '{compound_name}' 검색 결과: {len(results)}개\n")
    for chembl_id, name, max_phase in results:
        print(f"  {chembl_id}: {name} (Phase {max_phase})")

    return results


def search_by_cid(cursor, cid):
    """PubChem CID로 화합물 정보 조회 및 ChEMBL/DrugBank 매칭"""
    # PubChem 정보 가져오기
    cursor.execute("""
        SELECT cid, title, smiles, inchi_key
        FROM pubchem_compounds
        WHERE cid = ?
    """, (cid,))

    pubchem_info = cursor.fetchone()
    if not pubchem_info:
        print(f"❌ PubChem CID {cid}를 찾을 수 없습니다.")
        return None

    cid, title, smiles_pc, inchi_key = pubchem_info

    print(f"\n{'='*80}")
    print(f"🧪 PubChem Compound: CID {cid}")
    print(f"{'='*80}")
    print(f"Title: {title}")
    print(f"InChI Key: {inchi_key if inchi_key else 'N/A'}")

    # PubChem synonyms 가져오기
    cursor.execute("""
        SELECT synonym
        FROM pubchem_compound_synonyms
        WHERE cid = ?
        LIMIT 20
    """, (cid,))

    synonyms = [row[0] for row in cursor.fetchall()]
    print(f"\n📝 Synonyms: {len(synonyms)}개 (최대 20개 표시)")
    for syn in synonyms[:10]:
        print(f"  - {syn}")

    # ChEMBL 매칭 (InChI Key)
    print(f"\n🔗 ChEMBL 매칭:")
    if inchi_key:
        cursor.execute("""
            SELECT chembl_id, name, max_phase
            FROM chembl_compounds
            WHERE inchi_key = ?
        """, (inchi_key,))

        chembl_matches = cursor.fetchall()
        if chembl_matches:
            print(f"  ✅ InChI Key 매칭: {len(chembl_matches)}개")
            for chembl_id, name, phase in chembl_matches:
                print(f"     {chembl_id}: {name} (Phase {phase})")
        else:
            print(f"  ⚠️ InChI Key 매칭 없음")
    else:
        print(f"  ⚠️ InChI Key 없음")
        chembl_matches = []

    # DrugBank 매칭 (InChI Key)
    print(f"\n🔗 DrugBank 매칭:")
    if inchi_key:
        cursor.execute("""
            SELECT drugbank_id, name, groups, type
            FROM drugbank_drugs
            WHERE inchi_key = ?
        """, (inchi_key,))

        drugbank_matches = cursor.fetchall()
        if drugbank_matches:
            print(f"  ✅ InChI Key 매칭: {len(drugbank_matches)}개")
            for db_id, name, groups, dtype in drugbank_matches:
                print(f"     {db_id}: {name}")
                print(f"       Groups: {groups}, Type: {dtype}")
        else:
            print(f"  ⚠️ InChI Key 매칭 없음")
    else:
        drugbank_matches = []

    # Synonym으로 DrugBank 매칭
    syn_drugbank_matches = []
    for syn in synonyms[:10]:  # 처음 10개만
        cursor.execute("""
            SELECT drugbank_id, name, groups
            FROM drugbank_drugs
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
            LIMIT 1
        """, (syn,))

        match = cursor.fetchone()
        if match:
            syn_drugbank_matches.append((syn, match))

    if syn_drugbank_matches:
        print(f"\n  ✅ Synonym 매칭: {len(syn_drugbank_matches)}개")
        for syn, (db_id, name, groups) in syn_drugbank_matches:
            print(f"     '{syn}' → {db_id}: {name} ({groups})")

    return {
        'cid': cid,
        'title': title,
        'inchi_key': inchi_key,
        'synonyms': synonyms,
        'chembl_matches': chembl_matches,
        'drugbank_matches': drugbank_matches,
        'syn_drugbank_matches': syn_drugbank_matches
    }


def batch_match_statistics(cursor, sample_size=1000):
    """대량 샘플링으로 전체 통계 계산"""
    print(f"\n{'='*80}")
    print(f"📊 대량 샘플링 통계 (샘플: {sample_size}개)")
    print(f"{'='*80}\n")

    # 랜덤 샘플링
    cursor.execute("""
        SELECT chembl_id
        FROM chembl_compounds
        WHERE chembl_id IN (SELECT chembl_id FROM chembl_synonyms)
        ORDER BY RANDOM()
        LIMIT ?
    """, (sample_size,))

    sample_ids = [row[0] for row in cursor.fetchall()]

    inchi_matches = 0
    syn_matches = 0

    for i, chembl_id in enumerate(sample_ids):
        if (i + 1) % 100 == 0:
            print(f"진행 중... {i+1}/{sample_size}")

        # InChI 매칭
        inchi_match = match_by_inchi(cursor, chembl_id)
        if inchi_match and inchi_match[1]:
            inchi_matches += 1

        # Synonym 매칭
        _, syn_match = match_by_synonym(cursor, chembl_id)
        if syn_match:
            syn_matches += 1

    print(f"\n결과:")
    print(f"  InChI Key 매칭: {inchi_matches}/{sample_size} ({inchi_matches/sample_size*100:.2f}%)")
    print(f"  Synonym 매칭: {syn_matches}/{sample_size} ({syn_matches/sample_size*100:.2f}%)")


def main():
    parser = argparse.ArgumentParser(description='ChEMBL/PubChem Synonym으로 DrugBank 매칭')
    parser.add_argument('--db', default='database/database.db', help='DB 파일 경로')
    parser.add_argument('--chembl-id', nargs='+', help='분석할 ChEMBL ID (예: CHEMBL25)')
    parser.add_argument('--cid', type=int, help='PubChem CID로 검색 (예: 2244)')
    parser.add_argument('--search', help='화합물 이름으로 검색')
    parser.add_argument('--batch', action='store_true', help='대량 샘플링 통계')
    parser.add_argument('--sample-size', type=int, default=1000, help='샘플 크기 (기본: 1000)')

    args = parser.parse_args()

    # DB 연결
    db_path = Path(__file__).parent.parent / args.db
    if not db_path.exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if args.cid:
            # PubChem CID로 검색
            search_by_cid(cursor, args.cid)

        elif args.search:
            # 이름으로 검색
            search_by_name(cursor, args.search)

        elif args.chembl_id:
            # 특정 ChEMBL ID 분석
            analyze_multiple_compounds(cursor, args.chembl_id)

        elif args.batch:
            # 대량 샘플링 통계
            batch_match_statistics(cursor, args.sample_size)

        else:
            # 기본: 유명 약물 예시
            print("기본 예시: 유명 약물들\n")
            default_drugs = ['CHEMBL25', 'CHEMBL1', 'CHEMBL941', 'CHEMBL2']
            analyze_multiple_compounds(cursor, default_drugs)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
