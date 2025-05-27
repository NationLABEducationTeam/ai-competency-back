#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql

def check_password_formats():
    """데이터베이스의 비밀번호 저장 형식 확인"""
    print("🔍 데이터베이스 비밀번호 저장 형식 확인...")
    
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
            cursor.execute("SELECT id, email, name, password FROM users")
            users = cursor.fetchall()
            
            print("등록된 사용자들의 비밀번호 형식:")
            print("-" * 80)
            
            for user in users:
                password = user['password']
                print(f"ID: {user['id']}")
                print(f"Email: {user['email']}")
                print(f"Name: {user['name']}")
                print(f"Password: {password}")
                print(f"Password Length: {len(password)}")
                print(f"Starts with $: {password.startswith('$')}")
                print(f"Is bcrypt format: {password.startswith('$2b$') or password.startswith('$2a$') or password.startswith('$2y$')}")
                print("-" * 40)
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 실패: {e}")
        return False

if __name__ == "__main__":
    check_password_formats() 