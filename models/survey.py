from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from database.connection import Base

class Survey(Base):
    __tablename__ = "surveys"
    
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    workspace_id = Column(String(36), ForeignKey("workspace.id"))
    category_id = Column(String(36), ForeignKey("categories.id"))
    status = Column(String(50), default="draft")  # draft, active, completed
    excel_file_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String(36), primary_key=True, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # multiple_choice, text, rating
    options = Column(JSON)  # 선택지 저장
    order_idx = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspace.id"))  # survey_id 대신 workspace_id 사용
    respondent_name = Column(String(100))
    respondent_email = Column(String(100))  # 255 -> 100으로 변경
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    respondent_age = Column(Integer)  # 추가 필드
    respondent_organization = Column(String(255))  # 추가 필드
    respondent_education = Column(String(50))  # 추가 필드
    respondent_major = Column(String(255))  # 추가 필드

class Answer(Base):
    __tablename__ = "response_details"  # 실제 테이블명으로 변경
    
    id = Column(String(36), primary_key=True, index=True)
    response_id = Column(String(36), ForeignKey("responses.id"))
    question_id = Column(String(36), ForeignKey("questions.id"))
    score = Column(Integer)  # answer_value -> score로 변경
    created_at = Column(DateTime, server_default=func.now()) 