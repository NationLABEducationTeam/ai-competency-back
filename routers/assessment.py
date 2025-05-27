from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from database.connection import get_db
from models import Survey, Question, Response, Answer
from pydantic import BaseModel
from datetime import datetime

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

@router.get("/{survey_id}/info", response_model=SurveyInfo)
async def get_survey_info(
    survey_id: int,
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
    survey_id: int,
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
    
    return {"response_id": response.id, "message": "Assessment started"}

@router.post("/{survey_id}/submit")
async def submit_assessment(
    survey_id: int,
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
    
    return {"message": "Assessment submitted successfully"}

@router.get("/{survey_id}/scores")
async def get_assessment_scores(
    survey_id: int,
    response_id: int,
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
    
    return {
        "response_id": response_id,
        "total_score": total_score,
        "average_score": average_score,
        "answer_count": answer_count
    } 