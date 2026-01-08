#!/usr/bin/env python3
"""
Upload All Database Data - Master Import Script
================================================
모든 DB import 스크립트를 순차적으로 실행합니다.

Usage:
    python3 upload_db.py
    python3 upload_db.py --only kegg chembl  # 특정 DB만 import
    python3 upload_db.py --skip taxon        # 특정 DB 제외
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import argparse

# ============================================
# 설정
# ============================================

BASE_DIR = Path(__file__).resolve().parent

# Import 순서 (FK 제약조건 고려)
# Taxon이 가장 먼저 (모든 테이블이 참조)
IMPORT_SCRIPTS = [
    ('Common', 'import_taxon_to_db.py', 'Taxon (공통 데이터)'),
    ('Kegg', 'import_kegg_to_db.py', 'KEGG'),
    ('Chembl', 'import_chembl_to_db.py', 'ChEMBL'),
    ('Drugbank', 'import_drugbank_to_db.py', 'DrugBank'),
    ('PubChem', 'import_pubchem_to_db.py', 'PubChem'),
    ('NCBI', 'import_ncbi_to_db.py', 'NCBI'),
    ('Uniprot', 'import_uniprot_to_db.py', 'UniProt'),
    ('Reactome', 'import_reactome_to_db.py', 'Reactome'),
    ('Go', 'import_go_to_db.py', 'Gene Ontology (GO)'),
]

# ============================================
# 함수
# ============================================

def run_import_script(folder, script_name, db_name):
    """
    하나의 import 스크립트를 실행합니다.

    Returns:
        tuple: (success: bool, elapsed_time: float)
    """
    script_path = BASE_DIR / folder / script_name

    if not script_path.exists():
        print(f"  [ERROR] Script not found: {script_path}")
        return False, 0

    print(f"\n{'='*60}")
    print(f"[START] {db_name}")
    print(f"{'='*60}")

    start_time = datetime.now()

    try:
        # Python 스크립트 실행
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),
            check=True,
            capture_output=False,
            text=True
        )

        elapsed_time = (datetime.now() - start_time).total_seconds()

        print(f"\n[OK] {db_name} import completed in {elapsed_time:.1f}s")
        return True, elapsed_time

    except subprocess.CalledProcessError as e:
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"\n[ERROR] {db_name} import failed after {elapsed_time:.1f}s")
        print(f"[ERROR] Return code: {e.returncode}")
        return False, elapsed_time

    except Exception as e:
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"\n[ERROR] {db_name} import failed: {e}")
        return False, elapsed_time


def main():
    # ============================================
    # 인자 파싱
    # ============================================
    parser = argparse.ArgumentParser(
        description='Upload all database data to SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 upload_db.py                    # 모든 DB import
  python3 upload_db.py --only kegg chembl # KEGG, ChEMBL만 import
  python3 upload_db.py --skip taxon       # Taxon 제외하고 import
        """
    )
    parser.add_argument(
        '--only',
        nargs='+',
        help='Only import specified databases (e.g., kegg chembl)'
    )
    parser.add_argument(
        '--skip',
        nargs='+',
        help='Skip specified databases (e.g., taxon)'
    )

    args = parser.parse_args()

    # ============================================
    # 시작
    # ============================================
    start_time = datetime.now()

    print("="*60)
    print("Upload All Database Data")
    print("="*60)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Filter scripts based on arguments
    scripts_to_run = []

    for folder, script_name, db_name in IMPORT_SCRIPTS:
        db_key = folder.lower()

        # --only 옵션이 있으면 해당 DB만 실행
        if args.only:
            if db_key not in [x.lower() for x in args.only]:
                print(f"\n[SKIP] {db_name} (not in --only list)")
                continue

        # --skip 옵션이 있으면 해당 DB 제외
        if args.skip:
            if db_key in [x.lower() for x in args.skip]:
                print(f"\n[SKIP] {db_name} (in --skip list)")
                continue

        scripts_to_run.append((folder, script_name, db_name))

    print(f"\n[INFO] Total scripts to run: {len(scripts_to_run)}")

    # ============================================
    # Import 실행
    # ============================================
    results = []

    for folder, script_name, db_name in scripts_to_run:
        success, elapsed_time = run_import_script(folder, script_name, db_name)
        results.append({
            'db_name': db_name,
            'success': success,
            'elapsed_time': elapsed_time
        })

        # 실패 시 계속할지 물어보기
        if not success:
            response = input(f"\n[WARN] {db_name} import failed. Continue? (y/n): ")
            if response.lower() != 'y':
                print("\n[ABORT] Import process aborted by user")
                break

    # ============================================
    # 결과 요약
    # ============================================
    end_time = datetime.now()
    total_elapsed = (end_time - start_time).total_seconds()

    print("\n" + "="*60)
    print("Import Summary")
    print("="*60)
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print(f"\nResults:")

    success_count = 0
    failure_count = 0

    for result in results:
        status = "[OK]" if result['success'] else "[ERROR]"
        print(f"  {status} {result['db_name']:20s} : {result['elapsed_time']:.1f}s")

        if result['success']:
            success_count += 1
        else:
            failure_count += 1

    print(f"\n[INFO] Successfully imported: {success_count}/{len(results)} databases")

    if failure_count > 0:
        print(f"[WARN] Failed imports: {failure_count}")
        sys.exit(1)
    else:
        print("\n" + "="*60)
        print("[DONE] All imports completed successfully!")
        print("="*60)
        sys.exit(0)


if __name__ == '__main__':
    main()
