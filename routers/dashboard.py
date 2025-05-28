from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from database.connection import get_db
from models import (
    User, Workspace, Survey, Response, Answer, Question,
    Category, SimpleAnalytics
)
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """대시보드 개요"""
    try:
        # 워크스페이스 정보 조회
        workspace = db.query(Workspace).filter(
            Workspace.user_id == current_user.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # 최근 30일 응답 통계
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_analytics = db.query(SimpleAnalytics).join(Survey).filter(
            Survey.workspace_id == workspace.id,
            SimpleAnalytics.created_at >= thirty_days_ago
        ).all()
        
        # 응답자 수
        total_responses = len(recent_analytics)
        
        # 평균 점수
        if total_responses > 0:
            avg_score = sum(a.percentage for a in recent_analytics) / total_responses
        else:
            avg_score = 0
        
        # 최근 응답 목록 (상위 5개)
        recent_responses = db.query(SimpleAnalytics).join(Survey).filter(
            Survey.workspace_id == workspace.id
        ).order_by(
            desc(SimpleAnalytics.created_at)
        ).limit(5).all()
        
        recent_list = []
        for analytics in recent_responses:
            recent_list.append({
                "respondent_name": analytics.respondent_name,
                "total_score": analytics.total_score,
                "percentage": analytics.percentage,
                "created_at": analytics.created_at
            })
        
        return {
            "total_responses": total_responses,
            "average_score": round(avg_score, 1),
            "recent_responses": recent_list
        }
        
    except Exception as e:
        print(f"대시보드 개요 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch dashboard overview"
        )

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """전체 통계 개요"""
    try:
        # 전체 설문 수
        total_surveys = db.query(Survey).count()
        
        # 활성 설문 수
        active_surveys = db.query(Survey).filter(
            Survey.status == 'active'
        ).count()
        
        # 전체 응답 수
        total_responses = db.query(Response).count()
        
        # 오늘의 응답 수
        today = datetime.now().date()
        today_responses = db.query(Response).filter(
            func.date(Response.created_at) == today
        ).count()
        
        # 전체 워크스페이스 수
        total_workspaces = db.query(Workspace).count()
        
        return {
            "total_surveys": total_surveys,
            "active_surveys": active_surveys,
            "total_responses": total_responses,
            "today_responses": today_responses,
            "total_workspaces": total_workspaces
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trend")
async def get_response_trend(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # 워크스페이스 정보 조회
        workspace = db.query(Workspace).filter(
            Workspace.user_id == current_user.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # 기간별 응답 추세
        start_date = datetime.now() - timedelta(days=days)
        analytics = db.query(SimpleAnalytics).join(Survey).filter(
            Survey.workspace_id == workspace.id,
            SimpleAnalytics.created_at >= start_date
        ).all()

        # 일자별 데이터 집계
        daily_data = {}
        for analytic in analytics:
            date_key = analytic.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "response_count": 0,
                    "total_score": 0
                }
            daily_data[date_key]["response_count"] += 1
            daily_data[date_key]["total_score"] += analytic.percentage

        # 결과 포맷팅
        trend_data = []
        current_date = start_date
        while current_date <= datetime.now():
            date_key = current_date.strftime("%Y-%m-%d")
            if date_key in daily_data:
                avg_score = daily_data[date_key]["total_score"] / daily_data[date_key]["response_count"]
                trend_data.append({
                    "date": date_key,
                    "response_count": daily_data[date_key]["response_count"],
                    "average_score": round(avg_score, 1)
                })
            else:
                trend_data.append({
                    "date": date_key,
                    "response_count": 0,
                    "average_score": 0
                })
            current_date += timedelta(days=1)

        return trend_data

    except Exception as e:
        print(f"응답 추세 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch response trend"
        )

@router.get("/analytics/daily")
async def get_daily_analytics(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """일별 응답 추이"""
    try:
        # 날짜별 응답 수 집계
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_responses = db.query(
            func.date(Response.created_at).label('date'),
            func.count().label('count')
        ).filter(
            Response.created_at >= start_date,
            Response.created_at <= end_date
        ).group_by(
            func.date(Response.created_at)
        ).all()
        
        # 평균 점수 집계
        daily_scores = db.query(
            func.date(SimpleAnalytics.created_at).label('date'),
            func.avg(SimpleAnalytics.percentage).label('avg_score')
        ).filter(
            SimpleAnalytics.created_at >= start_date,
            SimpleAnalytics.created_at <= end_date
        ).group_by(
            func.date(SimpleAnalytics.created_at)
        ).all()
        
        return {
            "daily_responses": [
                {"date": str(r.date), "count": r.count}
                for r in daily_responses
            ],
            "daily_scores": [
                {"date": str(s.date), "average_score": float(s.avg_score)}
                for s in daily_scores
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/demographics")
async def get_demographics_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """응답자 인구통계학적 분석"""
    try:
        # 나이대별 분포
        age_distribution = db.query(
            Response.respondent_age,
            func.count().label('count')
        ).filter(
            Response.respondent_age.isnot(None)
        ).group_by(
            Response.respondent_age
        ).all()
        
        # 학력별 분포
        education_distribution = db.query(
            Response.respondent_education,
            func.count().label('count')
        ).filter(
            Response.respondent_education.isnot(None)
        ).group_by(
            Response.respondent_education
        ).all()
        
        # 전공별 분포
        major_distribution = db.query(
            Response.respondent_major,
            func.count().label('count')
        ).filter(
            Response.respondent_major.isnot(None)
        ).group_by(
            Response.respondent_major
        ).all()
        
        return {
            "age_distribution": [
                {"age": a.respondent_age, "count": a.count}
                for a in age_distribution
            ],
            "education_distribution": [
                {"education": e.respondent_education, "count": e.count}
                for e in education_distribution
            ],
            "major_distribution": [
                {"major": m.respondent_major, "count": m.count}
                for m in major_distribution
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/completion")
async def get_completion_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """설문 완료율 분석"""
    try:
        # 설문별 응답 수와 완료율
        survey_stats = []
        surveys = db.query(Survey).all()
        
        for survey in surveys:
            total_responses = db.query(Response).filter(
                Response.survey_id == survey.id
            ).count()
            
            completed_responses = db.query(Response).filter(
                Response.survey_id == survey.id,
                Response.completed == True
            ).count()
            
            completion_rate = (completed_responses / total_responses * 100) if total_responses > 0 else 0
            
            survey_stats.append({
                "survey_id": survey.id,
                "title": survey.title,
                "total_responses": total_responses,
                "completed_responses": completed_responses,
                "completion_rate": round(completion_rate, 2)
            })
        
        return survey_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/responses/recent")
async def get_recent_responses(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """최근 응답 목록"""
    try:
        # 최근 응답 조회 (워크스페이스 필터링 없이)
        recent_responses = db.query(
            Response, Survey, SimpleAnalytics
        ).join(
            Survey, Response.survey_id == Survey.id
        ).outerjoin(
            SimpleAnalytics, and_(
                SimpleAnalytics.survey_id == Survey.id,
                SimpleAnalytics.respondent_name == Response.respondent_name
            )
        ).order_by(
            desc(Response.created_at)
        ).limit(limit).all()
        
        return [{
            "response_id": r.Response.id,
            "survey_title": r.Survey.title,
            "respondent_name": r.Response.respondent_name,
            "respondent_email": r.Response.respondent_email,
            "score": r.SimpleAnalytics.percentage if r.SimpleAnalytics else None,
            "completed": r.Response.completed,
            "created_at": r.Response.created_at
        } for r in recent_responses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime/today")
async def get_today_realtime(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """오늘의 실시간 통계"""
    try:
        today = datetime.now().date()
        
        # 시간대별 응답 수
        hourly_responses = db.query(
            func.hour(Response.created_at).label('hour'),
            func.count().label('count')
        ).filter(
            func.date(Response.created_at) == today
        ).group_by(
            func.hour(Response.created_at)
        ).all()
        
        # 오늘의 평균 점수
        today_scores = db.query(
            func.avg(SimpleAnalytics.percentage).label('avg_score'),
            func.min(SimpleAnalytics.percentage).label('min_score'),
            func.max(SimpleAnalytics.percentage).label('max_score')
        ).filter(
            func.date(SimpleAnalytics.created_at) == today
        ).first()
        
        return {
            "hourly_responses": [
                {"hour": h.hour, "count": h.count}
                for h in hourly_responses
            ],
            "today_scores": {
                "average": float(today_scores.avg_score) if today_scores.avg_score else 0,
                "minimum": float(today_scores.min_score) if today_scores.min_score else 0,
                "maximum": float(today_scores.max_score) if today_scores.max_score else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 