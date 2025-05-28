from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL 연결 설정
DATABASE_URL = "mysql+pymysql://admin:GZGjuzwObS6CHW8Us7fD@competency-db.cjik2cuykhtl.ap-northeast-2.rds.amazonaws.com:3306/competency"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 