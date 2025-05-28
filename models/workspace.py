from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base
from .category import Category  # Category 모델 import

class Workspace(Base):
    __tablename__ = "workspace"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    university_name = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    # 관계 설정
    surveys = relationship("Survey", back_populates="workspace")
    categories = relationship("Category", back_populates="workspace", cascade="all, delete-orphan")

