from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base
from .category import Category  # Category 모델 import

class Survey(Base):
    __tablename__ = "surveys"
    
    id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspace.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    scale_min = Column(Integer, default=1)
    scale_max = Column(Integer, default=5)
    max_questions = Column(Integer, default=100)
    status = Column(Enum('draft', 'active', 'inactive'), default='draft')
    access_link = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    workspace = relationship("Workspace", back_populates="surveys")
    responses = relationship("Response", back_populates="survey", cascade="all, delete-orphan")
    simple_analytics = relationship("SimpleAnalytics", back_populates="survey", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String(36), primary_key=True, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    order_idx = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    question_type = Column(String(50))
    options = Column(JSON)

    category = relationship("Category", back_populates="questions")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspace.id"), nullable=False)
    survey_id = Column(String(36), ForeignKey("surveys.id"))
    respondent_name = Column(String(100), nullable=False)
    respondent_email = Column(String(100), nullable=False)
    respondent_age = Column(Integer)
    respondent_organization = Column(String(255))
    respondent_education = Column(String(50))
    respondent_major = Column(String(255))
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    survey = relationship("Survey", back_populates="responses")
    workspace = relationship("Workspace", back_populates="responses")

class Answer(Base):
    __tablename__ = "response_details"
    
    id = Column(String(36), primary_key=True, index=True)
    response_id = Column(String(36), ForeignKey("responses.id"))
    question_id = Column(String(36), ForeignKey("questions.id"))
    score = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class ResponseAnalytics(Base):
    __tablename__ = "response_analytics"
    
    id = Column(String(36), primary_key=True, index=True)
    response_id = Column(String(36), ForeignKey("responses.id"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspace.id"), nullable=False)
    total_score = Column(Float, nullable=False)
    category_scores = Column(JSON)  # {"category_id": score, ...}
    strengths = Column(JSON)  # ["category_id1", "category_id2", "category_id3"]
    weaknesses = Column(JSON)  # ["category_id1", "category_id2", "category_id3"]
    percentile = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class CategoryAnalytics(Base):
    __tablename__ = "category_analytics"
    
    id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspace.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    response_count = Column(Integer, default=0)
    average_score = Column(Float)
    max_score = Column(Float)
    min_score = Column(Float)
    score_distribution = Column(JSON)  # {1: count, 2: count, ...}
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SurveyCategoryMapping(Base):
    __tablename__ = "survey_category_mapping"
    
    id = Column(String(36), primary_key=True, index=True)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    weight = Column(Float, default=1.0)  # 설문별 카테고리 가중치 (기본 카테고리 가중치 override)
    order_idx = Column(Integer)  # 설문내 표시 순서
    created_at = Column(DateTime, server_default=func.now()) 

class SimpleAnalytics(Base):
    __tablename__ = "simple_analytics"
    
    id = Column(String(36), primary_key=True, index=True)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False)
    respondent_name = Column(String(100))
    total_score = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    survey = relationship("Survey", back_populates="simple_analytics") 