import pymysql

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def cleanup_tables():
    """불필요한 테이블 정리"""
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
        
        with connection.cursor() as cursor:
            # competency 데이터베이스 선택
            cursor.execute("USE competency")
            
            # 삭제할 테이블 목록
            tables_to_drop = [
                'response_analytics',
                'response_details',
                'category_analytics'
            ]
            
            # 테이블 삭제
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"✅ {table} 테이블 삭제 완료")
                except Exception as e:
                    print(f"❌ {table} 테이블 삭제 실패: {e}")
            
            connection.commit()
            print("✅ 테이블 정리 완료")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    cleanup_tables() 