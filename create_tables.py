"""
데이터베이스 테이블 생성 스크립트
"""
from sqlalchemy import create_engine
from models import (
    Base,
    User,
    Workspace,
    Category,
    Survey,
    Question,
    Response,
    Answer,
    SimpleAnalytics
)
from database.connection import SQLALCHEMY_DATABASE_URL

# 데이터베이스 엔진 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def create_all_tables():
    """모든 테이블 생성"""
    # 테이블 생성 순서
    tables = [
        User,           # 1. 사용자
        Workspace,      # 2. 워크스페이스
        Category,       # 3. 카테고리
        Survey,         # 4. 설문
        Question,       # 5. 질문
        Response,       # 6. 응답
        Answer,         # 7. 답변
        SimpleAnalytics # 8. 간단한 분석
    ]
    
    # 테이블 생성
    for table in tables:
        if not engine.dialect.has_table(engine, table.__tablename__):
            table.__table__.create(bind=engine)
            print(f"✅ {table.__tablename__} 테이블 생성 완료")
        else:
            print(f"⚠️ {table.__tablename__} 테이블이 이미 존재합니다")

def drop_all_tables():
    """모든 테이블 삭제 (주의: 데이터가 모두 삭제됨)"""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        user_input = input("WARNING: This will delete all data. Are you sure? (yes/no): ")
        if user_input.lower() == "yes":
            drop_all_tables()
            print("Recreating tables...")
            create_all_tables()
    else:
        create_all_tables() 