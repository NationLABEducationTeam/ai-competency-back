from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from typing import List, Dict
from database.connection import get_db
from models import User, Workspace, Survey, Response, Answer, Question
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 사용자의 워크스페이스 수
    workspace_count = db.query(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).count()
    
    # 전체 설문 수
    survey_count = db.query(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).count()
    
    # 활성 설문 수
    active_survey_count = db.query(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Survey.status == "active"
    ).count()
    
    # 전체 응답 수
    response_count = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).count()
    
    return {
        "workspace_count": workspace_count,
        "survey_count": survey_count,
        "active_survey_count": active_survey_count,
        "response_count": response_count
    }

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 완료된 응답 수
    completed_responses = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.completed == True
    ).count()
    
    # 평균 완료율
    total_responses = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).count()
    
    completion_rate = (completed_responses / total_responses * 100) if total_responses > 0 else 0
    
    # 최근 7일 응답 수
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_responses = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.created_at >= seven_days_ago
    ).count()
    
    return {
        "completed_responses": completed_responses,
        "completion_rate": round(completion_rate, 2),
        "recent_responses": recent_responses
    }

@router.get("/analytics/daily")
async def get_daily_response_trend(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    start_date = date.today() - timedelta(days=days)
    
    # 일별 응답 수 집계
    daily_responses = db.query(
        func.date(Response.created_at).label('date'),
        func.count(Response.id).label('count')
    ).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.created_at >= start_date
    ).group_by(func.date(Response.created_at)).all()
    
    return [
        {"date": str(item.date), "count": item.count}
        for item in daily_responses
    ]

@router.get("/analytics/competencies")
async def get_competency_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 역량별 평균 점수 (예시)
    # 실제로는 질문 카테고리나 태그를 기반으로 계산
    return [
        {"competency": "리더십", "average_score": 4.2},
        {"competency": "커뮤니케이션", "average_score": 3.8},
        {"competency": "문제해결", "average_score": 4.0},
        {"competency": "팀워크", "average_score": 4.5},
        {"competency": "창의성", "average_score": 3.6}
    ]

@router.get("/analytics/demographics")
async def get_demographic_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 교육수준 분포 (예시)
    return [
        {"education_level": "고등학교", "count": 120},
        {"education_level": "대학교", "count": 280},
        {"education_level": "대학원", "count": 85}
    ]

@router.get("/realtime/today")
async def get_today_realtime_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    # 오늘의 응답 수
    today_responses = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.created_at >= today_start
    ).count()
    
    # 오늘의 완료 수
    today_completed = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.created_at >= today_start,
        Response.completed == True
    ).count()
    
    # 현재 진행 중인 응답 수
    in_progress = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Response.completed == False
    ).count()
    
    return {
        "today_responses": today_responses,
        "today_completed": today_completed,
        "in_progress": in_progress
    }

@router.get("/analytics/completion")
async def get_workspace_completion_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스별 완료율
    workspaces = db.query(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).all()
    
    completion_rates = []
    for workspace in workspaces:
        total = db.query(Response).join(Survey).filter(
            Survey.workspace_id == workspace.id
        ).count()
        
        completed = db.query(Response).join(Survey).filter(
            Survey.workspace_id == workspace.id,
            Response.completed == True
        ).count()
        
        rate = (completed / total * 100) if total > 0 else 0
        
        completion_rates.append({
            "workspace_name": workspace.name,
            "completion_rate": round(rate, 2),
            "total_responses": total,
            "completed_responses": completed
        })
    
    return completion_rates

@router.get("/responses/recent")
async def get_recent_responses(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 최근 응답자 목록
    recent_responses = db.query(Response).join(Survey).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).order_by(Response.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": response.id,
            "respondent_name": response.respondent_name,
            "respondent_email": response.respondent_email,
            "survey_title": response.survey.title,
            "completed": response.completed,
            "created_at": response.created_at.isoformat()
        }
        for response in recent_responses
    ] 