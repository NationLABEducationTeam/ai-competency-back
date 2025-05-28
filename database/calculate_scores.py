import pymysql
import uuid
from datetime import datetime

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

# 테스트 응답 데이터
test_response = {
    "respondent_name": "민테익",
    "respondent_email": "edu@aination.kr",
    "respondent_age": 99,
    "respondent_organization": "테스트대학교",
    "respondent_education": "석사재학",
    "respondent_major": "미래기술학과",
    "answers": [
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
}

def calculate_and_save():
    """응답 데이터로부터 점수 계산 및 저장"""
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
            
            # 1. 응답 점수 합계 계산
            total_score = sum(answer['score'] for answer in test_response['answers'])
            max_possible = len(test_response['answers']) * 5  # 각 문항 최대 점수는 5
            percentage = (total_score / max_possible) * 100
            
            # 2. response_analytics에 저장
            analytics_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO response_analytics 
                (id, workspace_id, total_score, percentile, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                analytics_id,
                '9e6b1a0d-bd77-4b73-8e15-ae49636f2e2a',  # workspace_id
                percentage,  # 백분율 점수로 저장
                percentage,  # 일단 백분위도 같은 값으로
                datetime.now()
            ))
            
            print(f"""
✅ 점수 계산 완료:
- 총점: {total_score}
- 최대가능점수: {max_possible}
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
    calculate_and_save() 