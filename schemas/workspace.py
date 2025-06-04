from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: str
    workspace_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkspaceBase(BaseModel):
    title: str
    description: Optional[str] = None
    university_name: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    university_name: Optional[str] = None

class Workspace(WorkspaceBase):
    id: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: dict = {}

class WorkspaceVisibilityUpdate(BaseModel):
    is_visible: bool 