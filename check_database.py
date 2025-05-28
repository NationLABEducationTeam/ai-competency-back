#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "GZGjuzwObS6CHW8Us7fD"

def connect_to_mysql():
    """MySQL 데이터베이스에 연결"""
    try:
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ MySQL 연결 성공!")
        return connection
    except Exception as e:
        print(f"❌ MySQL 연결 실패: {e}")
        return None

def show_databases(connection):
    """모든 데이터베이스 목록 조회"""
    print("\n" + "="*50)
    print("📁 데이터베이스 목록")
    print("="*50)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            for i, db in enumerate(databases, 1):
                print(f"{i}. {db['Database']}")
                
        return [db['Database'] for db in databases]
    except Exception as e:
        print(f"❌ 데이터베이스 목록 조회 실패: {e}")
        return []

def show_tables(connection, database_name):
    """특정 데이터베이스의 테이블 목록 조회"""
    print(f"\n" + "="*50)
    print(f"📋 '{database_name}' 데이터베이스의 테이블 목록")
    print("="*50)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"USE {database_name}")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if not tables:
                print("테이블이 없습니다.")
                return []
            
            table_names = []
            for i, table in enumerate(tables, 1):
                table_name = list(table.values())[0]
                table_names.append(table_name)
                print(f"{i}. {table_name}")
                
        return table_names
    except Exception as e:
        print(f"❌ 테이블 목록 조회 실패: {e}")
        return []

def describe_table(connection, database_name, table_name):
    """테이블 구조 조회"""
    print(f"\n" + "="*50)
    print(f"🔍 '{table_name}' 테이블 구조")
    print("="*50)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"USE {database_name}")
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            print(f"{'컬럼명':<20} {'타입':<20} {'NULL':<8} {'키':<8} {'기본값':<15}")
            print("-" * 80)
            
            for col in columns:
                print(f"{col['Field']:<20} {col['Type']:<20} {col['Null']:<8} {col['Key']:<8} {str(col['Default']):<15}")
                
    except Exception as e:
        print(f"❌ 테이블 구조 조회 실패: {e}")

def show_table_data(connection, database_name, table_name, limit=10):
    """테이블 데이터 조회 (상위 N개)"""
    print(f"\n" + "="*50)
    print(f"📊 '{table_name}' 테이블 데이터 (상위 {limit}개)")
    print("="*50)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"USE {database_name}")
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count_result = cursor.fetchone()
            total_rows = count_result['count']
            
            print(f"총 레코드 수: {total_rows}")
            
            if total_rows > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                rows = cursor.fetchall()
                
                if rows:
                    # pandas DataFrame으로 변환해서 예쁘게 출력
                    df = pd.DataFrame(rows)
                    print(df.to_string(index=False))
                else:
                    print("데이터가 없습니다.")
            else:
                print("테이블이 비어있습니다.")
                
    except Exception as e:
        print(f"❌ 테이블 데이터 조회 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 AWS RDS MySQL 데이터베이스 탐색기")
    print(f"연결 정보: {USER}@{HOST}:{PORT}")
    
    # MySQL 연결
    connection = connect_to_mysql()
    if not connection:
        return
    
    try:
        # 1. 데이터베이스 목록 조회
        databases = show_databases(connection)
        
        # 2. 각 데이터베이스별로 테이블 조회
        for db_name in databases:
            # 시스템 데이터베이스는 건너뛰기
            if db_name in ['information_schema', 'performance_schema', 'mysql', 'sys']:
                continue
                
            tables = show_tables(connection, db_name)
            
            # 3. 각 테이블의 구조와 데이터 조회
            for table_name in tables:
                describe_table(connection, db_name, table_name)
                show_table_data(connection, db_name, table_name, limit=5)
        
        # 4. 사용자 정의 데이터베이스가 없는 경우 mysql 데이터베이스 확인
        if not any(db not in ['information_schema', 'performance_schema', 'mysql', 'sys'] for db in databases):
            print("\n" + "="*50)
            print("사용자 정의 데이터베이스가 없습니다. 'mysql' 데이터베이스의 일부 테이블을 확인합니다.")
            print("="*50)
            
            tables = show_tables(connection, 'mysql')
            # mysql 데이터베이스의 주요 테이블만 확인
            important_tables = ['user', 'db', 'tables_priv', 'columns_priv']
            for table_name in tables:
                if table_name in important_tables:
                    describe_table(connection, 'mysql', table_name)
                    show_table_data(connection, 'mysql', table_name, limit=3)
    
    finally:
        connection.close()
        print("\n✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    main() 