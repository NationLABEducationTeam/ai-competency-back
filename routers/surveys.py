from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import boto3
import uuid
import os
from database.connection import get_db
from models import User, Survey, Workspace, Question
from schemas.survey import (
    SurveyCreate,
    Survey as SurveySchema,
    SurveyUpdate,
    SurveyStatusUpdate,
    PresignedUrlRequest,
    PresignedUrlResponse,
    UploadCompleteRequest
)
from utils.auth import get_current_active_user
import pandas as pd

router = APIRouter()

# S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'survey-uploads')

def format_survey_response(survey: Survey) -> dict:
    """설문 응답을 OpenAPI 형식으로 변환"""
    return {
        "title": survey.title,
        "description": survey.description,
        "category_id": survey.category_id,
        "id": survey.id,
        "workspace_id": survey.workspace_id,
        "status": survey.status,
        "excel_file_url": survey.excel_file_url,
        "created_at": survey.created_at,
        "updated_at": survey.updated_at,
        "questions": [
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "order": q.order
            } for q in survey.questions
        ]
    }

@router.get("/", response_model=List[SurveySchema])
async def get_all_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 사용자의 모든 워크스페이스에서 설문 조회
    surveys = db.query(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).all()
    
    return [format_survey_response(survey) for survey in surveys]

@router.get("/workspace/{workspace_id}", response_model=List[SurveySchema])
async def get_surveys_by_workspace(
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
    
    surveys = db.query(Survey).filter(Survey.workspace_id == workspace_id).all()
    
    return [format_survey_response(survey) for survey in surveys]

@router.get("/{survey_id}", response_model=SurveySchema)
async def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    return format_survey_response(survey)

@router.post("/", response_model=SurveySchema)
async def create_survey(
    survey: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스 권한 확인
    workspace = db.query(Workspace).filter(
        Workspace.id == survey.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    db_survey = Survey(**survey.dict())
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    
    return format_survey_response(db_survey)

@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    db.delete(survey)
    db.commit()
    return "Survey deleted successfully"

@router.post("/{survey_id}/upload")
async def upload_excel(
    survey_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # 파일 확장자 확인
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")
    
    # S3에 업로드
    file_key = f"surveys/{survey_id}/{uuid.uuid4()}-{file.filename}"
    
    try:
        s3_client.upload_fileobj(file.file, BUCKET_NAME, file_key)
        
        # 엑셀 파일 파싱하여 질문 생성
        file.file.seek(0)
        df = pd.read_excel(file.file)
        
        # 기존 질문 삭제
        db.query(Question).filter(Question.survey_id == survey_id).delete()
        
        # 새 질문 생성 (예시 구조)
        for idx, row in df.iterrows():
            question = Question(
                survey_id=survey_id,
                question_text=row.get('question', ''),
                question_type=row.get('type', 'text'),
                order=idx
            )
            db.add(question)
        
        # 설문 파일 URL 업데이트
        survey.excel_file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}"
        db.commit()
        
        return "File uploaded successfully"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{survey_id}/presigned-upload", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    survey_id: int,
    request: PresignedUrlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    file_key = f"surveys/{survey_id}/{uuid.uuid4()}-{request.filename}"
    
    # Presigned URL 생성
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={'Bucket': BUCKET_NAME, 'Key': file_key},
        ExpiresIn=3600  # 1시간
    )
    
    return {"upload_url": presigned_url, "file_key": file_key}

@router.post("/{survey_id}/upload-complete")
async def confirm_upload_complete(
    survey_id: int,
    request: UploadCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # 파일 URL 업데이트
    survey.excel_file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{request.file_key}"
    db.commit()
    
    return "Upload confirmed successfully"

@router.put("/{survey_id}/status", response_model=SurveySchema)
async def update_survey_status(
    survey_id: int,
    status_update: SurveyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if status_update.status not in ["draft", "active", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    survey.status = status_update.status
    db.commit()
    db.refresh(survey)
    
    return format_survey_response(survey) 