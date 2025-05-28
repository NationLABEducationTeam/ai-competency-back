"""
새로 추가된 테이블 생성 스크립트
"""
from database.connection import engine
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Float,
    JSON
)
from sqlalchemy.sql import func

def create_new_tables():
    """새로 추가된 테이블 생성"""
    print("Creating new tables...")
    
    # 기존 테이블들의 메타데이터 로드
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # 테이블 존재 여부 확인을 위한 기존 테이블 목록
    existing_tables = metadata.tables.keys()
    print("Existing tables:", existing_tables)
    
    # categories 테이블
    if 'categories' not in existing_tables:
        categories = Table(
            'categories',
            metadata,
            Column('id', String(36), primary_key=True, index=True),
            Column('workspace_id', String(36), ForeignKey('workspace.id'), nullable=False),
            Column('name', String(100), nullable=False),
            Column('description', Text),
            Column('weight', Float, default=1.0),
            Column('order_idx', Integer),
            Column('created_at', DateTime, server_default=func.now()),
            Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now())
        )
        print("Creating table: categories")
        categories.create(bind=engine)
    else:
        print("Table categories already exists, skipping...")
    
    # survey_category_mapping 테이블
    if 'survey_category_mapping' not in existing_tables:
        survey_category_mapping = Table(
            'survey_category_mapping',
            metadata,
            Column('id', String(36), primary_key=True, index=True),
            Column('survey_id', String(36), ForeignKey('surveys.id'), nullable=False),
            Column('category_id', String(36), ForeignKey('categories.id'), nullable=False),
            Column('weight', Float, default=1.0),
            Column('order_idx', Integer),
            Column('created_at', DateTime, server_default=func.now())
        )
        print("Creating table: survey_category_mapping")
        survey_category_mapping.create(bind=engine)
    else:
        print("Table survey_category_mapping already exists, skipping...")
    
    # response_analytics 테이블
    if 'response_analytics' not in existing_tables:
        response_analytics = Table(
            'response_analytics',
            metadata,
            Column('id', String(36), primary_key=True, index=True),
            Column('response_id', String(36), ForeignKey('responses.id'), nullable=False),
            Column('workspace_id', String(36), ForeignKey('workspace.id'), nullable=False),
            Column('total_score', Float, nullable=False),
            Column('category_scores', JSON),
            Column('strengths', JSON),
            Column('weaknesses', JSON),
            Column('percentile', Float),
            Column('created_at', DateTime, server_default=func.now())
        )
        print("Creating table: response_analytics")
        response_analytics.create(bind=engine)
    else:
        print("Table response_analytics already exists, skipping...")
    
    # category_analytics 테이블
    if 'category_analytics' not in existing_tables:
        category_analytics = Table(
            'category_analytics',
            metadata,
            Column('id', String(36), primary_key=True, index=True),
            Column('workspace_id', String(36), ForeignKey('workspace.id'), nullable=False),
            Column('category_id', String(36), ForeignKey('categories.id'), nullable=False),
            Column('response_count', Integer, default=0),
            Column('average_score', Float),
            Column('max_score', Float),
            Column('min_score', Float),
            Column('score_distribution', JSON),
            Column('updated_at', DateTime, server_default=func.now(), onupdate=func.now())
        )
        print("Creating table: category_analytics")
        category_analytics.create(bind=engine)
    else:
        print("Table category_analytics already exists, skipping...")
    
    print("New tables created successfully!")

if __name__ == "__main__":
    create_new_tables() 