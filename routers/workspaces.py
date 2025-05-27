from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from models import User, Workspace, Category
from schemas.workspace import (
    WorkspaceCreate, 
    Workspace as WorkspaceSchema,
    WorkspaceUpdate,
    CategoryCreate,
    Category as CategorySchema
)
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[WorkspaceSchema])
async def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspaces = db.query(Workspace).filter(Workspace.owner_id == current_user.id).all()
    return workspaces

@router.get("/{workspace_id}", response_model=WorkspaceSchema)
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return workspace

@router.post("/", response_model=WorkspaceSchema)
async def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_workspace = Workspace(
        **workspace.dict(),
        owner_id=current_user.id
    )
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@router.put("/{workspace_id}", response_model=WorkspaceSchema)
async def update_workspace(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    update_data = workspace_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    db.commit()
    db.refresh(workspace)
    return workspace

@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db.delete(workspace)
    db.commit()
    return {"message": "Workspace deleted successfully"}

@router.get("/{workspace_id}/categories", response_model=List[CategorySchema])
async def get_categories(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스 권한 확인
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    categories = db.query(Category).filter(Category.workspace_id == workspace_id).all()
    return categories

@router.post("/{workspace_id}/categories", response_model=CategorySchema)
async def create_category(
    workspace_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스 권한 확인
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db_category = Category(
        **category.dict(),
        workspace_id=workspace_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category 