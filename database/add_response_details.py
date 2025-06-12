import pymysql
import uuid

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

# 테스트 응답 데이터
test_answers = [
    {"question_id": "q6", "score": 3},
    {"question_id": "q7", "score": 4},
    {"question_id": "q8", "score": 2},
    {"question_id": "q9", "score": 3},
    {"question_id": "q10", "score": 4},
    {"question_id": "q11", "score": 4},
    {"question_id": "q12", "score": 1},
    {"question_id": "q13", "score": 2},
    {"question_id": "q14", "score": 3},
    {"question_id": "q15", "score": 2},
    {"question_id": "q16", "score": 5},
    {"question_id": "q17", "score": 4},
    {"question_id": "q18", "score": 3},
    {"question_id": "q19", "score": 2},
    {"question_id": "q20", "score": 4},
    {"question_id": "q21", "score": 5},
    {"question_id": "q22", "score": 1},
    {"question_id": "q23", "score": 2},
    {"question_id": "q24", "score": 3},
    {"question_id": "q25", "score": 4},
    {"question_id": "q26", "score": 5},
    {"question_id": "q27", "score": 4},
    {"question_id": "q28", "score": 3},
    {"question_id": "q29", "score": 2},
    {"question_id": "q30", "score": 1},
    {"question_id": "q31", "score": 5},
    {"question_id": "q32", "score": 4},
    {"question_id": "q33", "score": 5},
    {"question_id": "q34", "score": 4},
    {"question_id": "q35", "score": 1},
    {"question_id": "q36", "score": 1},
    {"question_id": "q37", "score": 1},
    {"question_id": "q38", "score": 1},
    {"question_id": "q39", "score": 1}
]

def add_response_details():
    """response_details 테이블에 응답 데이터 추가"""
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
            
            # 응답 ID 가져오기
            cursor.execute("""
                SELECT id FROM responses 
                WHERE survey_id = 'a6b045fe-0d2c-40a3-bb51-55bcd572b854'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            response = cursor.fetchone()
            
            if not response:
                print("❌ 응답을 찾을 수 없습니다.")
                return
                
            response_id = response['id']
            print(f"📝 응답 ID: {response_id}")
            
            # response_details에 데이터 추가
            for answer in test_answers:
                detail_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO response_details 
                    (id, response_id, question_id, score)
                    VALUES (%s, %s, %s, %s)
                """, (
                    detail_id,
                    response_id,
                    answer['question_id'],
                    answer['score']
                ))
                print(f"✅ 응답 상세 추가: {answer['question_id']} -> {answer['score']}")
            
            connection.commit()
            print("✅ 응답 상세 데이터 추가 완료")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    add_response_details() 