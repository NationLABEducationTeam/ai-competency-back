from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from database.connection import get_db
from models import Survey, Question, Response, Answer, Workspace
from pydantic import BaseModel
from datetime import datetime
from utils.auth import get_current_active_user, User

router = APIRouter()

class SurveyInfo(BaseModel):
    id: int
    title: str
    description: str
    questions: List[Dict]

class StartAssessmentRequest(BaseModel):
    respondent_name: str
    respondent_email: str

class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer_text: str = None
    answer_value: int = None

class SubmitAssessmentRequest(BaseModel):
    response_id: int
    answers: List[SubmitAnswerRequest]

class ResponseDetail(BaseModel):
    id: int
    respondent_name: str
    respondent_email: str
    completed: bool
    created_at: datetime
    answers: List[Dict] = []

@router.get("/{survey_id}/info", response_model=SurveyInfo)
async def get_survey_info(
    survey_id: str,
    db: Session = Depends(get_db)
):
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.status == "active"
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found or not active")
    
    questions = db.query(Question).filter(
        Question.survey_id == survey_id
    ).order_by(Question.order).all()
    
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "questions": [
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options
            } for q in questions
        ]
    }

@router.post("/{survey_id}/start")
async def start_assessment(
    survey_id: str,
    request: StartAssessmentRequest,
    db: Session = Depends(get_db)
):
    # 설문 확인
    survey = db.query(Survey).filter(
        Survey.id == survey_id,
        Survey.status == "active"
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found or not active")
    
    # 응답 생성
    response = Response(
        survey_id=survey_id,
        respondent_name=request.respondent_name,
        respondent_email=request.respondent_email,
        completed=False
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    
    return "Assessment started successfully"

@router.post("/{survey_id}/submit")
async def submit_assessment(
    survey_id: str,
    request: SubmitAssessmentRequest,
    db: Session = Depends(get_db)
):
    # 응답 확인
    response = db.query(Response).filter(
        Response.id == request.response_id,
        Response.survey_id == survey_id,
        Response.completed == False
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found or already completed")
    
    # 답변 저장
    for answer_data in request.answers:
        answer = Answer(
            response_id=response.id,
            question_id=answer_data.question_id,
            answer_text=answer_data.answer_text,
            answer_value=answer_data.answer_value
        )
        db.add(answer)
    
    # 응답 완료 처리
    response.completed = True
    db.commit()
    
    return "Assessment submitted successfully"

@router.get("/{survey_id}/scores")
async def get_assessment_scores(
    survey_id: str,
    response_id: int = Query(...),
    db: Session = Depends(get_db)
):
    # 응답 확인
    response = db.query(Response).filter(
        Response.id == response_id,
        Response.survey_id == survey_id,
        Response.completed == True
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Completed response not found")
    
    # 점수 계산
    answers = db.query(Answer).filter(Answer.response_id == response_id).all()
    
    total_score = 0
    answer_count = 0
    
    for answer in answers:
        if answer.answer_value is not None:
            total_score += answer.answer_value
            answer_count += 1
    
    average_score = total_score / answer_count if answer_count > 0 else 0
    
    return f"Total Score: {total_score}, Average: {average_score:.2f}, Questions: {answer_count}"

# 관리자용 엔드포인트
@router.get("/{survey_id}/responses")
async def get_survey_responses(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """설문별 응답 목록 조회 (관리자용)"""
    # 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    responses = db.query(Response).filter(
        Response.survey_id == survey_id
    ).order_by(Response.created_at.desc()).all()
    
    response_list = []
    for r in responses:
        response_list.append({
            "id": r.id,
            "respondent_name": r.respondent_name,
            "respondent_email": r.respondent_email,
            "completed": r.completed,
            "created_at": r.created_at.isoformat()
        })
    
    return f"Found {len(response_list)} responses for survey {survey_id}"

@router.get("/{survey_id}/responses/{response_id}", response_model=ResponseDetail)
async def get_response_detail(
    survey_id: str,
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """특정 응답 상세 조회 (관리자용)"""
    # 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    response = db.query(Response).filter(
        Response.id == response_id,
        Response.survey_id == survey_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # 답변 정보 조회
    answers = db.query(Answer).join(Question).filter(
        Answer.response_id == response_id
    ).all()
    
    answer_list = []
    for answer in answers:
        answer_list.append({
            "question_id": answer.question_id,
            "question_text": answer.question.question_text,
            "answer_text": answer.answer_text,
            "answer_value": answer.answer_value
        })
    
    return {
        "id": response.id,
        "respondent_name": response.respondent_name,
        "respondent_email": response.respondent_email,
        "completed": response.completed,
        "created_at": response.created_at,
        "answers": answer_list
    }

@router.put("/{survey_id}/status")
async def update_survey_status(
    survey_id: str,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """설문 상태 업데이트 (관리자용) - /surveys/{id}/status와 중복"""
    # 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if status not in ["draft", "active", "completed", "archived"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    survey.status = status
    db.commit()
    
    return f"Survey status updated to {status}" 