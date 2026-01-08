#!/usr/bin/env python3
"""
데이터베이스 스키마 생성 스크립트
processed_analysis_filtered.json 파일을 기반으로 SQLite 스키마를
"""
import sqlite3

# DB 연결
conn = sqlite3.connect('/data/project/shinyoung/DB/database/database.db')
cursor = conn.cursor()

# 스키마 파일 읽어서 실행하기
with open('database_schema.sql', 'r', encoding='utf-8') as f:
    schema_sql = f.read()
    cursor.executescript(schema_sql)  # 여러 개의 SQL 문을 한 번에 실행
    print("모든 테이블이 성공적으로 생성되었습니다.")

conn.commit()
# 이후에 기존의 데이터 임포트 코드 실행...