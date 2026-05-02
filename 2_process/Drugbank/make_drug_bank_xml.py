import zipfile
import os

# 1. 파일 이름 설정
zip_file_path = 'drugbank_all_full_database.xml.zip'  # 다운받은 압축 파일명
extract_path = '.'  # 현재 폴더에 압축 풀기

# 2. 압축 풀기 (파일이 없을 때만 수행)
target_xml = 'full database.xml' # 압축 풀면 나오는 파일명 (DrugBank 버전에 따라 다를 수 있음 확인 필요!)

if not os.path.exists(target_xml):
    print(f"'{zip_file_path}' 압축 해제 중...")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        # 압축 파일 내부의 파일 리스트 확인 (파일명이 full database.xml이 아닐 수도 있으므로)
        print(f"압축 해제된 파일들: {zip_ref.namelist()}")
    print("압축 해제 완료!")
else:
    print(f"'{target_xml}' 파일이 이미 존재합니다. 압축 해제를 건너뜁니다.")

# --- 이 밑으로 아까 드린 XML 파싱 코드가 이어지면 됩니다 ---
# xml_file = target_xml 
# ...