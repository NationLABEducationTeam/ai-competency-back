#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 서버 URL (로컬에서 테스트)
BASE_URL = "http://localhost:8080/api/v1"

def test_register():
    """회원가입 테스트"""
    print("🔐 회원가입 테스트...")
    
    register_data = {
        "email": "test_new@example.com",
        "name": "테스트 사용자",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 회원가입 실패: {e}")
        return False

def test_login():
    """로그인 테스트"""
    print("\n🔑 로그인 테스트...")
    
    # 기존 사용자로 로그인 시도
    login_data = {
        "username": "sk@sk.com",  # OAuth2PasswordRequestForm은 username 필드 사용
        "password": "sk123"  # 실제 비밀번호 추측
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            return token
        else:
            return None
    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        return None

def test_me(token):
    """현재 사용자 정보 조회 테스트"""
    print("\n👤 사용자 정보 조회 테스트...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 사용자 정보 조회 실패: {e}")
        return False

def test_database_users():
    """데이터베이스의 실제 사용자 확인"""
    print("\n📊 데이터베이스 사용자 확인...")
    
    import pymysql
    
    try:
        connection = pymysql.connect(
            host="competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com",
            port=3306,
            user="admin",
            password="26yXkiBsEaCF1rMyoW6o",
            database="competency",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email, name, LEFT(password, 20) as password_preview FROM users LIMIT 5")
            users = cursor.fetchall()
            
            print("등록된 사용자들:")
            for user in users:
                print(f"  ID: {user['id']}, Email: {user['email']}, Name: {user['name']}, Password: {user['password_preview']}...")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 로그인 시스템 테스트")
    print("=" * 50)
    
    # 1. 데이터베이스 사용자 확인
    test_database_users()
    
    # 2. 회원가입 테스트
    # test_register()
    
    # 3. 로그인 테스트
    token = test_login()
    
    # 4. 토큰으로 사용자 정보 조회
    if token:
        test_me(token)
    
    print("\n✅ 테스트 완료!") 