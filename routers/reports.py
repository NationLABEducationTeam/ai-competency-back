from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import boto3
import json
import os
from datetime import datetime
from database.connection import get_db
from models import User, Workspace, Survey, Response, Answer, Question
from utils.auth import get_current_active_user
from pydantic import BaseModel

router = APIRouter()

# S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'survey-reports')

class Report(BaseModel):
    id: int
    title: str
    workspace_id: int
    workspace_name: str
    survey_id: str
    survey_title: str
    created_at: datetime
    report_url: Optional[str] = None

class SaveReportRequest(BaseModel):
    survey_id: str
    report_data: dict

@router.get("/", response_model=List[Report])
async def get_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 사용자의 모든 워크스페이스의 리포트 조회
    surveys = db.query(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).all()
    
    reports = []
    for survey in surveys:
        # 완료된 응답이 있는 설문만 리포트 생성
        completed_count = db.query(Response).filter(
            Response.survey_id == survey.id,
            Response.completed == True
        ).count()
        
        if completed_count > 0:
            reports.append({
                "id": survey.id,
                "title": f"{survey.title} 리포트",
                "workspace_id": survey.workspace_id,
                "workspace_name": survey.workspace.name,
                "survey_id": survey.id,
                "survey_title": survey.title,
                "created_at": survey.created_at,
                "report_url": survey.excel_file_url  # 기존 파일 URL 사용
            })
    
    return reports

@router.get("/workspace/{workspace_id}", response_model=List[Report])
async def get_workspace_reports(
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
    
    reports = []
    for survey in surveys:
        completed_count = db.query(Response).filter(
            Response.survey_id == survey.id,
            Response.completed == True
        ).count()
        
        if completed_count > 0:
            reports.append({
                "id": survey.id,
                "title": f"{survey.title} 리포트",
                "workspace_id": survey.workspace_id,
                "workspace_name": workspace.name,
                "survey_id": survey.id,
                "survey_title": survey.title,
                "created_at": survey.created_at,
                "report_url": survey.excel_file_url  # 기존 파일 URL 사용
            })
    
    return reports

@router.get("/students")
async def get_student_list(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """학생 목록 조회 (워크스페이스별 필터링 가능)"""
    query = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    )
    
    if workspace_id:
        query = query.filter(Survey.workspace_id == workspace_id)
    
    # 이메일로 그룹화하여 학생 목록 생성
    students_dict = {}
    responses = query.all()
    
    for response in responses:
        email = response.respondent_email
        if email not in students_dict:
            students_dict[email] = {
                "email": email,
                "name": response.respondent_name,
                "response_count": 0,
                "last_response_date": response.created_at
            }
        students_dict[email]["response_count"] += 1
        if response.created_at > students_dict[email]["last_response_date"]:
            students_dict[email]["last_response_date"] = response.created_at
    
    student_list = list(students_dict.values())
    return f"Found {len(student_list)} students with {len(responses)} total responses"

@router.get("/students/{student_email}/results")
async def get_student_results(
    student_email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """특정 학생의 모든 설문 결과 조회"""
    responses = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.respondent_email == student_email
    ).all()
    
    if not responses:
        raise HTTPException(status_code=404, detail="Student not found")
    
    results = []
    total_avg_score = 0
    completed_surveys = 0
    
    for response in responses:
        # 답변 정보 조회
        answers = db.query(Answer).filter(Answer.response_id == response.id).all()
        
        # 점수 계산
        total_score = 0
        score_count = 0
        for answer in answers:
            if answer.answer_value is not None:
                total_score += answer.answer_value
                score_count += 1
        
        avg_score = total_score / score_count if score_count > 0 else 0
        
        if response.completed:
            total_avg_score += avg_score
            completed_surveys += 1
        
        results.append({
            "response_id": response.id,
            "survey_id": response.survey_id,
            "survey_title": response.survey.title,
            "workspace_name": response.survey.workspace.name,
            "completed": response.completed,
            "created_at": response.created_at,
            "average_score": round(avg_score, 2),
            "total_questions": len(answers)
        })
    
    overall_avg = total_avg_score / completed_surveys if completed_surveys > 0 else 0
    
    return f"Student {student_email} ({responses[0].respondent_name if responses else 'Unknown'}): {len(responses)} responses, {completed_surveys} completed, Overall Average: {overall_avg:.2f}"

@router.post("/save-to-s3")
async def save_report_to_s3(
    request: SaveReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == request.survey_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # 리포트 데이터 생성
    report_data = generate_report_data(survey, db)
    
    # S3에 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_key = f"reports/{survey.workspace_id}/{survey.id}/report_{timestamp}.json"
    
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(report_data, ensure_ascii=False),
            ContentType='application/json'
        )
        
        report_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}"
        
        return f"Report saved successfully to S3: {report_url}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_report_data(survey: Survey, db: Session) -> dict:
    """설문 리포트 데이터 생성"""
    
    # 응답 통계
    total_responses = db.query(Response).filter(
        Response.survey_id == survey.id
    ).count()
    
    completed_responses = db.query(Response).filter(
        Response.survey_id == survey.id,
        Response.completed == True
    ).count()
    
    # 질문별 응답 분석
    questions = db.query(Question).filter(
        Question.survey_id == survey.id
    ).order_by(Question.order).all()
    
    question_analysis = []
    for question in questions:
        answers = db.query(Answer).filter(
            Answer.question_id == question.id
        ).all()
        
        # 점수형 질문의 경우 평균 계산
        if question.question_type == "rating":
            scores = [a.answer_value for a in answers if a.answer_value is not None]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            question_analysis.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "response_count": len(answers),
                "average_score": round(avg_score, 2)
            })
        else:
            # 텍스트형 응답은 샘플만 포함
            sample_answers = [a.answer_text for a in answers[:5] if a.answer_text]
            
            question_analysis.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "response_count": len(answers),
                "sample_answers": sample_answers
            })
    
    return {
        "survey_id": survey.id,
        "survey_title": survey.title,
        "workspace_id": survey.workspace_id,
        "workspace_name": survey.workspace.name,
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_responses": total_responses,
            "completed_responses": completed_responses,
            "completion_rate": round((completed_responses / total_responses * 100) if total_responses > 0 else 0, 2)
        },
        "question_analysis": question_analysis
    } 