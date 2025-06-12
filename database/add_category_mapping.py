import pymysql
import uuid

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def add_category_mapping():
    """survey_category_mapping 데이터 추가"""
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
            
            # 현재 설문의 카테고리 정보 가져오기
            cursor.execute("""
                SELECT DISTINCT c.id as category_id
                FROM categories c
                JOIN questions q ON q.category_id = c.id
                WHERE q.id IN (
                    SELECT question_id 
                    FROM response_details rd
                    JOIN responses r ON r.id = rd.response_id
                    WHERE r.survey_id = 'a6b045fe-0d2c-40a3-bb51-55bcd572b854'
                )
            """)
            categories = cursor.fetchall()
            
            # survey_category_mapping에 데이터 추가
            for idx, category in enumerate(categories, 1):
                mapping_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO survey_category_mapping 
                    (id, survey_id, category_id, weight, order_idx)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    mapping_id,
                    'a6b045fe-0d2c-40a3-bb51-55bcd572b854',
                    category['category_id'],
                    1.0,  # 기본 가중치
                    idx   # 순서
                ))
                print(f"✅ 카테고리 매핑 추가: {category['category_id']}")
            
            connection.commit()
            print("✅ 카테고리 매핑 완료")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    add_category_mapping() 