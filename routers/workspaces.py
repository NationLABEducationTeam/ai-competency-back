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
    Category as CategorySchema,
    StandardResponse
)
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[WorkspaceSchema])
async def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspaces = db.query(Workspace).filter(Workspace.owner_id == current_user.id).all()
    
    # 응답 형식을 OpenAPI에 맞게 변환
    result = []
    for workspace in workspaces:
        result.append({
            "id": str(workspace.id),
            "user_id": workspace.owner_id,
            "title": workspace.name,
            "description": workspace.description,
            "university_name": workspace.university_name,
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at
        })
    
    return result

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
    
    return {
        "id": str(workspace.id),
        "user_id": workspace.owner_id,
        "title": workspace.name,
        "description": workspace.description,
        "university_name": workspace.university_name,
        "created_at": workspace.created_at,
        "updated_at": workspace.updated_at
    }

@router.post("/", response_model=WorkspaceSchema, status_code=201)
async def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_workspace = Workspace(
        name=workspace.title,  # title -> name으로 매핑
        description=workspace.description,
        university_name=workspace.university_name,
        owner_id=current_user.id
    )
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    
    return {
        "id": str(db_workspace.id),
        "user_id": db_workspace.owner_id,
        "title": db_workspace.name,
        "description": db_workspace.description,
        "university_name": db_workspace.university_name,
        "created_at": db_workspace.created_at,
        "updated_at": db_workspace.updated_at
    }

@router.put("/{workspace_id}", response_model=StandardResponse)
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
    
    # 업데이트 데이터 처리
    if workspace_update.title is not None:
        workspace.name = workspace_update.title
    if workspace_update.description is not None:
        workspace.description = workspace_update.description
    if workspace_update.university_name is not None:
        workspace.university_name = workspace_update.university_name
    
    db.commit()
    
    return {
        "success": True,
        "message": "Workspace updated successfully",
        "data": {}
    }

@router.delete("/{workspace_id}", response_model=StandardResponse)
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
    
    return {
        "success": True,
        "message": "Workspace deleted successfully",
        "data": {}
    }

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
    
    # 응답 형식을 OpenAPI에 맞게 변환
    result = []
    for category in categories:
        result.append({
            "id": str(category.id),
            "workspace_id": str(category.workspace_id),
            "name": category.name,
            "description": category.description,
            "created_at": category.created_at
        })
    
    return result

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
        name=category.name,
        description=category.description,
        workspace_id=workspace_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return {
        "id": str(db_category.id),
        "workspace_id": str(db_category.workspace_id),
        "name": db_category.name,
        "description": db_category.description,
        "created_at": db_category.created_at
    } 