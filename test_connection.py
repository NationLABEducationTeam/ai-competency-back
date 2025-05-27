#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import sys

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def test_connection():
    """MySQL 연결 테스트"""
    print("🔍 MySQL 연결 테스트 시작...")
    print(f"호스트: {HOST}")
    print(f"포트: {PORT}")
    print(f"사용자: {USER}")
    print(f"비밀번호: {'*' * len(PASSWORD)}")
    print("-" * 50)
    
    # 1. 기본 데이터베이스 없이 연결 시도
    print("1️⃣ 기본 데이터베이스 없이 연결 시도...")
    try:
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        print("✅ 연결 성공!")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"MySQL 버전: {version['VERSION()']}")
            
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("📁 데이터베이스 목록:")
            for db in databases:
                print(f"  - {db['Database']}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        print(f"오류 타입: {type(e).__name__}")
        
    # 2. mysql 데이터베이스로 연결 시도
    print("\n2️⃣ mysql 데이터베이스로 연결 시도...")
    try:
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database='mysql',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        print("✅ mysql 데이터베이스 연결 성공!")
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ mysql 데이터베이스 연결 실패: {e}")
        
    # 3. information_schema 데이터베이스로 연결 시도
    print("\n3️⃣ information_schema 데이터베이스로 연결 시도...")
    try:
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database='information_schema',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        print("✅ information_schema 데이터베이스 연결 성공!")
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ information_schema 데이터베이스 연결 실패: {e}")
        
    return False

def check_network():
    """네트워크 연결 확인"""
    print("\n🌐 네트워크 연결 확인...")
    import socket
    
    try:
        # DNS 해석 확인
        ip = socket.gethostbyname(HOST)
        print(f"✅ DNS 해석 성공: {HOST} -> {ip}")
        
        # 포트 연결 확인
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((HOST, PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ 포트 {PORT} 연결 가능")
            return True
        else:
            print(f"❌ 포트 {PORT} 연결 불가")
            return False
            
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AWS RDS MySQL 연결 진단 도구")
    print("=" * 50)
    
    # 네트워크 확인
    network_ok = check_network()
    
    if network_ok:
        # 데이터베이스 연결 확인
        connection_ok = test_connection()
        
        if connection_ok:
            print("\n🎉 연결 테스트 완료! 데이터베이스에 성공적으로 연결되었습니다.")
        else:
            print("\n❌ 모든 연결 시도가 실패했습니다.")
            print("\n🔧 해결 방법:")
            print("1. AWS RDS 보안 그룹에서 현재 EC2 인스턴스의 IP 허용 확인")
            print("2. RDS 인스턴스의 퍼블릭 액세스 설정 확인")
            print("3. 사용자 계정 권한 확인")
            print("4. 비밀번호 정확성 확인")
    else:
        print("\n❌ 네트워크 연결에 문제가 있습니다.")
        print("\n🔧 해결 방법:")
        print("1. 인터넷 연결 확인")
        print("2. AWS RDS 엔드포인트 주소 확인")
        print("3. 보안 그룹 설정 확인")
        print("4. VPC 및 서브넷 설정 확인") 