"""add target to survey

Revision ID: add_target_to_survey
Revises: 
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
import pymysql
from dotenv import load_dotenv
import os

# AWS RDS MySQL 연결 정보
HOST = "competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com"
PORT = 3306
USER = "admin"
PASSWORD = "GZGjuzwObS6CHW8Us7fD"
DATABASE = "survey_db"

# revision identifiers, used by Alembic.
revision = 'add_target_to_survey'
down_revision = None
branch_labels = None
depends_on = None

def connect_to_mysql():
    """MySQL 데이터베이스에 연결"""
    try:
        connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        # print("✅ MySQL 연결 성공!")
        return connection
    except Exception as e:
        print(f"❌ MySQL 연결 실패: {e}")
        return None

def upgrade():
    # MySQL 직접 연결
    connection = connect_to_mysql()
    if not connection:
        raise Exception("데이터베이스 연결 실패")
    
    try:
        with connection.cursor() as cursor:
            # Survey 테이블에 target 컬럼 추가
            cursor.execute("""
                ALTER TABLE surveys 
                ADD COLUMN target INT DEFAULT 10
            """)
            
            # 기존 데이터의 target 값을 10으로 업데이트
            cursor.execute("""
                UPDATE surveys 
                SET target = 10 
                WHERE target IS NULL
            """)
            
            # target 컬럼을 NOT NULL로 변경
            cursor.execute("""
                ALTER TABLE surveys 
                MODIFY COLUMN target INT NOT NULL DEFAULT 10
            """)
            
            connection.commit()
            print("✅ target 컬럼 추가 및 데이터 업데이트 완료!")
            
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close()

def downgrade():
    # MySQL 직접 연결
    connection = connect_to_mysql()
    if not connection:
        raise Exception("데이터베이스 연결 실패")
    
    try:
        with connection.cursor() as cursor:
            # target 컬럼 제거
            cursor.execute("""
                ALTER TABLE surveys 
                DROP COLUMN target
            """)
            
            connection.commit()
            print("✅ target 컬럼 제거 완료!")
            
    except Exception as e:
        print(f"❌ 마이그레이션 롤백 실패: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close() 