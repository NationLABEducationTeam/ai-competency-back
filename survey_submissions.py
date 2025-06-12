import pymysql
import uuid
from datetime import datetime, timedelta

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "GZGjuzwObS6CHW8Us7fD"

class SurveySubmissionManager:
    def __init__(self):
        self.connection = self._connect_to_mysql()
        self._create_table_if_not_exists()

    def _connect_to_mysql(self):
        """MySQL 데이터베이스에 연결"""
        try:
            connection = pymysql.connect(
                host=HOST,
                port=PORT,
                user=USER,
                password=PASSWORD,
                database='competency',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            # print("✅ MySQL 연결 성공!")
            return connection
        except Exception as e:
            print(f"❌ MySQL 연결 실패: {e}")
            return None

    def _create_table_if_not_exists(self):
        """survey_submissions 테이블이 없으면 생성"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS survey_submissions (
            id VARCHAR(36) PRIMARY KEY,
            workspace_id VARCHAR(36) NOT NULL,
            survey_id VARCHAR(36) NOT NULL,
            respondent_email VARCHAR(100) NOT NULL,
            respondent_name VARCHAR(100) NOT NULL,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_status ENUM('started', 'completed', 'abandoned') DEFAULT 'started',
            completion_time INT,
            FOREIGN KEY (workspace_id) REFERENCES workspace(id),
            FOREIGN KEY (survey_id) REFERENCES surveys(id),
            INDEX idx_workspace_survey (workspace_id, survey_id),
            INDEX idx_submission_date (submission_date)
        )
        """
        with self.connection.cursor() as cursor:
            cursor.execute(create_table_sql)
        self.connection.commit()

    def create_submission(self, workspace_id, survey_id, respondent_email, respondent_name):
        """새로운 설문 제출 기록 생성"""
        sql = """
        INSERT INTO survey_submissions 
        (id, workspace_id, survey_id, respondent_email, respondent_name)
        VALUES (%s, %s, %s, %s, %s)
        """
        submission_id = str(uuid.uuid4())
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (submission_id, workspace_id, survey_id, 
                                   respondent_email, respondent_name))
            self.connection.commit()
            return submission_id
        except Exception as e:
            print(f"제출 기록 생성 실패: {e}")
            return None

    def update_submission_status(self, submission_id, status, completion_time=None):
        """설문 제출 상태 업데이트"""
        sql = """
        UPDATE survey_submissions 
        SET completion_status = %s, completion_time = %s
        WHERE id = %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (status, completion_time, submission_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"상태 업데이트 실패: {e}")
            return False

    def get_workspace_statistics(self, workspace_id):
        """워크스페이스별 설문 통계 조회"""
        sql = """
        SELECT 
            s.title as survey_title,
            COUNT(*) as total_submissions,
            SUM(CASE WHEN ss.completion_status = 'completed' THEN 1 ELSE 0 END) as completed_submissions,
            AVG(ss.completion_time) as avg_completion_time
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        WHERE ss.workspace_id = %s
        GROUP BY ss.survey_id, s.title
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (workspace_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"통계 조회 실패: {e}")
            return []

    def get_recent_submissions(self, workspace_id, limit=10):
        """최근 설문 제출 기록 조회"""
        sql = """
        SELECT 
            ss.*,
            s.title as survey_title
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        WHERE ss.workspace_id = %s
        ORDER BY ss.submission_date DESC
        LIMIT %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (workspace_id, limit))
                return cursor.fetchall()
        except Exception as e:
            print(f"최근 제출 기록 조회 실패: {e}")
            return []

    def get_submission_counts_by_timeframe(self, workspace_id, start_date=None, end_date=None, group_by='day'):
        """시간대별 제출 수 조회"""
        # MySQL의 DATE_FORMAT 함수에 맞는 포맷 문자열
        mysql_format = {
            'hour': '%%Y-%%m-%%d %%H:00',
            'day': '%%Y-%%m-%%d',
            'week': '%%Y-%%U',
            'month': '%%Y-%%m'
        }

        if group_by not in mysql_format:
            raise ValueError("group_by는 'hour', 'day', 'week', 'month' 중 하나여야 합니다")

        where_clause = "WHERE ss.workspace_id = %s"
        params = [workspace_id]

        if start_date:
            where_clause += " AND ss.submission_date >= %s"
            params.append(start_date)
        if end_date:
            where_clause += " AND ss.submission_date <= %s"
            params.append(end_date)

        sql = f"""
        SELECT 
            DATE_FORMAT(ss.submission_date, '{mysql_format[group_by]}') as time_period,
            COUNT(*) as total_submissions,
            COUNT(DISTINCT ss.respondent_email) as unique_respondents,
            s.title as survey_title,
            SUM(CASE WHEN ss.completion_status = 'completed' THEN 1 ELSE 0 END) as completed_submissions
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        {where_clause}
        GROUP BY time_period, s.id, s.title
        ORDER BY time_period DESC, s.title
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"시간대별 제출 수 조회 실패: {e}")
            return []

    def get_submission_trend(self, workspace_id, days=30):
        """최근 N일 동안의 제출 추이 조회"""
        start_date = datetime.now() - timedelta(days=days)
        
        sql = """
        SELECT 
            DATE(ss.submission_date) as submission_date,
            COUNT(*) as total_submissions,
            COUNT(DISTINCT ss.respondent_email) as unique_respondents,
            SUM(CASE WHEN ss.completion_status = 'completed' THEN 1 ELSE 0 END) as completed_submissions
        FROM survey_submissions ss
        WHERE ss.workspace_id = %s 
        AND ss.submission_date >= %s
        GROUP BY DATE(ss.submission_date)
        ORDER BY submission_date DESC
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (workspace_id, start_date))
                return cursor.fetchall()
        except Exception as e:
            print(f"제출 추이 조회 실패: {e}")
            return []

    def __del__(self):
        """연결 종료"""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()

# 사용 예시
if __name__ == "__main__":
    # 매니저 인스턴스 생성
    manager = SurveySubmissionManager()
    
    # 예시: 새로운 제출 기록 생성
    submission_id = manager.create_submission(
        workspace_id="158a25cb-3731-4394-aea3-73211e112302",
        survey_id="f9b7be74-593b-4683-8bbc-e9e3bc0669c8",
        respondent_email="test@example.com",
        respondent_name="테스트 사용자"
    )
    
    if submission_id:
        # 완료 상태로 업데이트
        manager.update_submission_status(
            submission_id=submission_id,
            status="completed",
            completion_time=300  # 5분 소요
        )
    
    # 워크스페이스 통계 조회
    stats = manager.get_workspace_statistics("158a25cb-3731-4394-aea3-73211e112302")
    print("워크스페이스 통계:", stats)
    
    # 최근 제출 기록 조회
    recent = manager.get_recent_submissions("158a25cb-3731-4394-aea3-73211e112302")
    print("최근 제출 기록:", recent)
    
    # 시간대별 제출 수 조회 예시
    # 일별 통계
    daily_stats = manager.get_submission_counts_by_timeframe(
        workspace_id="158a25cb-3731-4394-aea3-73211e112302",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        group_by='day'
    )
    print("일별 제출 통계:", daily_stats)
    
    # 월별 통계
    monthly_stats = manager.get_submission_counts_by_timeframe(
        workspace_id="158a25cb-3731-4394-aea3-73211e112302",
        group_by='month'
    )
    print("월별 제출 통계:", monthly_stats)
    
    # 최근 30일 추이
    trend = manager.get_submission_trend(
        workspace_id="158a25cb-3731-4394-aea3-73211e112302",
        days=30
    )
    print("최근 30일 제출 추이:", trend) 