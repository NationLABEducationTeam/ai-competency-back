from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspace.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    weight = Column(Float, default=1.0)  # 카테고리 가중치
    order_idx = Column(Integer)  # 표시 순서
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계 설정
    workspace = relationship("Workspace", back_populates="categories") 