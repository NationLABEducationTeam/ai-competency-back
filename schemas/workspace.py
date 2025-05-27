from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    workspace_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Workspace(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[Category] = []
    
    class Config:
        from_attributes = True 