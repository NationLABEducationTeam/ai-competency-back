import pymysql
from datetime import datetime

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "26yXkiBsEaCF1rMyoW6o"

def update_responses():
    """기존 응답들의 survey_id 업데이트"""
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
            
            # workspace별로 첫 번째 survey를 찾아서 해당 workspace의 responses에 연결
            cursor.execute("""
                UPDATE responses r
                JOIN (
                    SELECT w.id as workspace_id, s.id as survey_id
                    FROM workspace w
                    JOIN surveys s ON s.workspace_id = w.id
                    WHERE s.created_at = (
                        SELECT MIN(created_at)
                        FROM surveys s2
                        WHERE s2.workspace_id = w.id
                    )
                ) ws ON r.workspace_id = ws.workspace_id
                SET r.survey_id = ws.survey_id
                WHERE r.survey_id IS NULL
            """)
            
            connection.commit()
            print("✅ 응답 데이터 업데이트 완료")
            
            # 업데이트된 행 수 확인
            cursor.execute("SELECT COUNT(*) as count FROM responses WHERE survey_id IS NOT NULL")
            result = cursor.fetchone()
            print(f"✅ 업데이트된 응답 수: {result['count']}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        connection.close()
        print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    update_responses() 