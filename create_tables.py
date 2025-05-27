"""
데이터베이스 테이블 생성 스크립트
"""
from database.connection import engine, Base
from models import User, Workspace, Category, Survey, Question, Response, Answer

def create_all_tables():
    """모든 테이블 생성"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_all_tables() 