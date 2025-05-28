from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
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
    print(f"🏢 워크스페이스 조회 요청")
    
    workspaces = db.query(Workspace).all()
    
    print(f"📊 찾은 워크스페이스 수: {len(workspaces)}")
    
    # 응답 형식을 OpenAPI에 맞게 변환
    result = []
    for workspace in workspaces:
        result.append({
            "id": str(workspace.id),
            "user_id": workspace.user_id,
            "title": workspace.title,
            "description": workspace.description,
            "university_name": workspace.university_name,
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at
        })
    
    return result

@router.get("/{workspace_id}", response_model=WorkspaceSchema)
async def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    print(f"🔍 워크스페이스 상세 조회: {workspace_id}")
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        print(f"❌ 워크스페이스를 찾을 수 없음: {workspace_id}")
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    print(f"✅ 워크스페이스 찾음: {workspace.title}")
    
    return {
        "id": str(workspace.id),
        "user_id": workspace.user_id,
        "title": workspace.title,
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
    workspace_id = str(uuid.uuid4())
    db_workspace = Workspace(
        id=workspace_id,
        title=workspace.title,
        description=workspace.description,
        university_name=workspace.university_name,
        user_id=current_user.id
    )
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    
    return {
        "id": str(db_workspace.id),
        "user_id": db_workspace.user_id,
        "title": db_workspace.title,
        "description": db_workspace.description,
        "university_name": db_workspace.university_name,
        "created_at": db_workspace.created_at,
        "updated_at": db_workspace.updated_at
    }

@router.put("/{workspace_id}", response_model=StandardResponse)
async def update_workspace(
    workspace_id: str,
    workspace_update: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # 업데이트 데이터 처리
    if workspace_update.title is not None:
        workspace.title = workspace_update.title
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
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
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
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스 존재 확인
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
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
    workspace_id: str,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스 권한 확인
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
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