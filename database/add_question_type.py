import pymysql

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def add_question_columns():
    """questions 테이블에 필요한 컬럼 추가"""
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
            
            # question_type 컬럼 추가
            cursor.execute("""
                ALTER TABLE questions 
                ADD COLUMN question_type VARCHAR(50),
                ADD COLUMN options JSON
            """)
            
            connection.commit()
            print("✅ questions 테이블 컬럼 추가 완료")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    add_question_columns() 