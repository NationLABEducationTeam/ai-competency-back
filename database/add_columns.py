import pymysql

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def add_columns():
    """필요한 컬럼들 추가"""
    try:
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        # print("✅ MySQL 연결 성공!")
        
        with connection.cursor() as cursor:
            # competency 데이터베이스 선택
            cursor.execute("USE competency")
            
            # categories 테이블에 weight 컬럼 추가
            try:
                cursor.execute("""
                    ALTER TABLE categories 
                    ADD COLUMN weight FLOAT DEFAULT 1.0,
                    ADD COLUMN order_idx INT,
                    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                """)
                print("✅ categories 테이블 컬럼 추가 완료")
            except Exception as e:
                print(f"ℹ️ categories 테이블 수정 건너뜀: {e}")
            
            # questions 테이블에 컬럼 추가
            try:
                cursor.execute("""
                    ALTER TABLE questions 
                    ADD COLUMN question_type VARCHAR(50),
                    ADD COLUMN options JSON
                """)
                print("✅ questions 테이블 컬럼 추가 완료")
            except Exception as e:
                print(f"ℹ️ questions 테이블 수정 건너뜀: {e}")
            
            connection.commit()
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    add_columns() 