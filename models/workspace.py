from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    university_name = Column(String(255))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    owner = relationship("User", backref="workspaces")
    categories = relationship("Category", back_populates="workspace", cascade="all, delete-orphan")
    surveys = relationship("Survey", back_populates="workspace", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    workspace = relationship("Workspace", back_populates="categories") 