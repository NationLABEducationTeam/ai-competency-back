from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from database.connection import get_db
from models import User, Workspace, Category, Survey, Response
from schemas.workspace import (
    WorkspaceCreate, 
    Workspace as WorkspaceSchema,
    WorkspaceUpdate,
    CategoryCreate,
    Category as CategorySchema,
    StandardResponse,
    WorkspaceVisibilityUpdate
)
from utils.auth import get_current_active_user
import traceback

router = APIRouter()

@router.get("/", response_model=List[WorkspaceSchema])
async def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    print(f"🏢 워크스페이스 조회 요청")
    
    # is_visible이 True(1)인 워크스페이스만 조회
    workspaces = db.query(Workspace).filter(Workspace.is_visible == True).all()
    
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

@router.get("/trash")
async def get_trash_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """보관함(휴지통)에 있는 설문들 조회 - draft 상태인 설문들"""
    try:
        # draft 상태인 설문들 조회
        trash_surveys = db.query(Survey).join(Workspace).filter(
            Survey.status == 'draft'
        ).all()
        
        result = []
        for survey in trash_surveys:
            # 각 설문의 응답 수 조회
            response_count = db.query(Response).filter(
                Response.survey_id == survey.id
            ).count()
            
            result.append({
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "workspace_id": survey.workspace_id,
                "workspace_name": survey.workspace.title if survey.workspace else "Unknown",
                "status": survey.status,
                "response_count": response_count,
                "created_at": survey.created_at,
                "updated_at": survey.updated_at
            })
        
        return {
            "surveys": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        print(f"보관함 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"보관함 조회 중 오류가 발생했습니다: {str(e)}"
        )

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
        Workspace.id == workspace_id
        #Workspace.user_id == current_user.id
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

@router.put("/{workspace_id}/hide", response_model=StandardResponse)
async def hide_workspace(
    workspace_id: str,
    visibility: WorkspaceVisibilityUpdate = WorkspaceVisibilityUpdate(is_visible=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"워크스페이스 숨김 처리 시작: {workspace_id}")
        print(f"current_user.id: {getattr(current_user, 'id', None)}")
        print(f"visibility: {visibility}")
        print(f"visibility.is_visible: {getattr(visibility, 'is_visible', None)}")

        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id
            #Workspace.user_id == current_user.id
        ).first()
        print(f"쿼리 결과 workspace: {workspace}")
        if workspace:
            print(f"workspace.id: {workspace.id}")
            print(f"workspace.title: {workspace.title}")
            print(f"workspace.is_visible(변경 전): {workspace.is_visible}")
        else:
            print("워크스페이스를 찾을 수 없음")
            raise HTTPException(status_code=404, detail="Workspace not found")

        workspace.is_visible = visibility.is_visible
        print(f"workspace.is_visible(변경 후): {workspace.is_visible}")
        db.commit()
        print(f"워크스페이스 숨김 처리 완료: {workspace_id}")

        return {
            "success": True,
            "message": "Workspace visibility updated successfully",
            "data": {}
        }
    except Exception as e:
        db.rollback()
        print("예외 발생! traceback:")
        traceback.print_exc()
        error_msg = f"Failed to update workspace visibility: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.put("/{workspace_id}/show", response_model=StandardResponse)
async def show_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        print(f"워크스페이스 표시 처리 시작: {workspace_id}")
        
        # 워크스페이스 확인
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id
            #Workspace.user_id == current_user.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # is_visible을 True(1)로 설정
        workspace.is_visible = True
        db.commit()
        print(f"워크스페이스 표시 처리 완료: {workspace_id}")
        
        return {
            "success": True,
            "message": "Workspace shown successfully",
            "data": {}
        }
    except Exception as e:
        db.rollback()
        error_msg = f"Failed to show workspace: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

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
        Workspace.id == workspace_id
        #Workspace.user_id == current_user.id
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