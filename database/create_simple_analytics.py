import pymysql

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def create_and_save():
    """간단한 응답 분석 테이블 생성 및 데이터 저장"""
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
            
            # 1. 간단한 분석 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simple_analytics (
                    id VARCHAR(36) PRIMARY KEY,
                    survey_id VARCHAR(36),
                    respondent_name VARCHAR(100),
                    total_score FLOAT,
                    total_questions INT,
                    percentage FLOAT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ 테이블 생성 완료")
            
            # 2. 테스트 데이터 계산
            answers = [
                {"question_id": "q6", "score": 3}, {"question_id": "q7", "score": 4},
                {"question_id": "q8", "score": 2}, {"question_id": "q9", "score": 3},
                {"question_id": "q10", "score": 4}, {"question_id": "q11", "score": 4},
                {"question_id": "q12", "score": 1}, {"question_id": "q13", "score": 2},
                {"question_id": "q14", "score": 3}, {"question_id": "q15", "score": 2},
                {"question_id": "q16", "score": 5}, {"question_id": "q17", "score": 4},
                {"question_id": "q18", "score": 3}, {"question_id": "q19", "score": 2},
                {"question_id": "q20", "score": 4}, {"question_id": "q21", "score": 5},
                {"question_id": "q22", "score": 1}, {"question_id": "q23", "score": 2},
                {"question_id": "q24", "score": 3}, {"question_id": "q25", "score": 4},
                {"question_id": "q26", "score": 5}, {"question_id": "q27", "score": 4},
                {"question_id": "q28", "score": 3}, {"question_id": "q29", "score": 2},
                {"question_id": "q30", "score": 1}, {"question_id": "q31", "score": 5},
                {"question_id": "q32", "score": 4}, {"question_id": "q33", "score": 5},
                {"question_id": "q34", "score": 4}, {"question_id": "q35", "score": 1},
                {"question_id": "q36", "score": 1}, {"question_id": "q37", "score": 1},
                {"question_id": "q38", "score": 1}, {"question_id": "q39", "score": 1}
            ]
            
            total_score = sum(answer['score'] for answer in answers)
            total_questions = len(answers)
            percentage = (total_score / (total_questions * 5)) * 100
            
            # 3. 데이터 저장
            cursor.execute("""
                INSERT INTO simple_analytics 
                (id, survey_id, respondent_name, total_score, total_questions, percentage)
                VALUES (UUID(), %s, %s, %s, %s, %s)
            """, (
                'a6b045fe-0d2c-40a3-bb51-55bcd572b854',  # survey_id
                '민테익',
                total_score,
                total_questions,
                percentage
            ))
            
            print(f"""
✅ 점수 계산 완료:
- 총점: {total_score}
- 문항수: {total_questions}
- 백분율: {percentage:.1f}%
            """)
            
            connection.commit()
            print("✅ 분석 결과 저장 완료")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    create_and_save() 