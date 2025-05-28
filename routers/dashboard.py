from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, distinct
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from database.connection import get_db
from models import (
    User, Workspace, Survey, Response, Answer, Question,
    Category, SimpleAnalytics
)
from utils.auth import get_current_active_user
from survey_submissions import SurveySubmissionManager

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db)
):
    """대시보드 개요"""
    try:
        # 최근 30일 응답 통계 (모든 워크스페이스)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_analytics = db.query(SimpleAnalytics).join(Survey).filter(
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
        recent_responses = db.query(SimpleAnalytics).join(Survey).order_by(
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
    db: Session = Depends(get_db)
):
    """전체 통계 개요"""
    try:
        # 전체 설문 수
        total_surveys = db.query(Survey).count()
        
        # 활성 설문 수
        active_surveys = db.query(Survey).filter(
            Survey.status == 'active'
        ).count()
        
        # 전체 응답 수 (simple_analytics 기준)
        total_responses = db.query(SimpleAnalytics).count()
        
        # 오늘의 응답 수
        today = datetime.now().date()
        today_responses = db.query(SimpleAnalytics).filter(
            func.date(SimpleAnalytics.created_at) == today
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
    db: Session = Depends(get_db)
):
    try:
        # 기간별 응답 추세 (모든 워크스페이스)
        start_date = datetime.now() - timedelta(days=days)
        analytics = db.query(SimpleAnalytics).join(Survey).filter(
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
    db: Session = Depends(get_db)
):
    """일별 응답 추이"""
    try:
        # 날짜별 응답 수 집계 (simple_analytics 사용, 모든 워크스페이스)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_analytics = db.query(
            func.date(SimpleAnalytics.created_at).label('date'),
            func.count().label('count'),
            func.avg(SimpleAnalytics.percentage).label('avg_score')
        ).join(Survey, Survey.id == SimpleAnalytics.survey_id).filter(
            SimpleAnalytics.created_at >= start_date,
            SimpleAnalytics.created_at <= end_date
        ).group_by(
            func.date(SimpleAnalytics.created_at)
        ).all()
        
        return {
            "daily_responses": [
                {"date": str(r.date), "count": r.count}
                for r in daily_analytics
            ],
            "daily_scores": [
                {"date": str(r.date), "average_score": float(r.avg_score) if r.avg_score else 0}
                for r in daily_analytics
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/demographics")
async def get_demographics_analytics(
    db: Session = Depends(get_db)
):
    """응답자 인구통계학적 분석"""
    try:
        # 기본적인 통계만 제공 (상세 인구통계 데이터가 없으므로)
        return {
            "age_distribution": [],
            "education_distribution": [],
            "major_distribution": [],
            "message": "인구통계학적 데이터가 수집되지 않았습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/completion")
async def get_completion_analytics(
    db: Session = Depends(get_db)
):
    """설문 완료율 분석"""
    try:
        # 설문별 응답 수와 완료율 (survey_submissions 사용, 모든 워크스페이스)
        survey_stats = []
        surveys = db.query(Survey).all()
        
        manager = SurveySubmissionManager()
        
        for survey in surveys:
            # survey_submissions에서 통계 조회
            total_submissions = 0
            completed_submissions = 0
            
            try:
                with manager.connection.cursor() as cursor:
                    # 총 제출 수
                    cursor.execute(
                        "SELECT COUNT(*) as total FROM survey_submissions WHERE survey_id = %s",
                        (survey.id,)
                    )
                    total_result = cursor.fetchone()
                    total_submissions = total_result['total'] if total_result else 0
                    
                    # 완료된 제출 수
                    cursor.execute(
                        "SELECT COUNT(*) as completed FROM survey_submissions WHERE survey_id = %s AND completion_status = 'completed'",
                        (survey.id,)
                    )
                    completed_result = cursor.fetchone()
                    completed_submissions = completed_result['completed'] if completed_result else 0
            except Exception as e:
                print(f"설문 {survey.id} 통계 조회 실패: {e}")
                continue
            
            completion_rate = (completed_submissions / total_submissions * 100) if total_submissions > 0 else 0
            
            survey_stats.append({
                "survey_id": survey.id,
                "title": survey.title,
                "total_responses": total_submissions,
                "completed_responses": completed_submissions,
                "completion_rate": round(completion_rate, 2)
            })
        
        return survey_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/responses/recent")
async def get_recent_responses(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """최근 응답 목록"""
    try:
        # simple_analytics에서 최근 응답 조회 (모든 워크스페이스)
        recent_analytics = db.query(
            SimpleAnalytics, Survey
        ).join(
            Survey, SimpleAnalytics.survey_id == Survey.id
        ).order_by(
            desc(SimpleAnalytics.created_at)
        ).limit(limit).all()
        
        return [{
            "response_id": analytics.SimpleAnalytics.id,
            "survey_title": analytics.Survey.title,
            "respondent_name": analytics.SimpleAnalytics.respondent_name,
            "respondent_email": None,  # simple_analytics에는 이메일 정보가 없음
            "score": analytics.SimpleAnalytics.percentage,
            "completed": True,  # simple_analytics에 있다면 완료된 것으로 간주
            "created_at": analytics.SimpleAnalytics.created_at
        } for analytics in recent_analytics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime/today")
async def get_today_realtime(
    db: Session = Depends(get_db)
):
    """오늘의 실시간 통계"""
    try:
        today = datetime.now().date()
        
        # 시간대별 응답 수 (simple_analytics 사용, 모든 워크스페이스)
        hourly_analytics = db.query(
            func.hour(SimpleAnalytics.created_at).label('hour'),
            func.count().label('count')
        ).join(Survey, Survey.id == SimpleAnalytics.survey_id).filter(
            func.date(SimpleAnalytics.created_at) == today
        ).group_by(
            func.hour(SimpleAnalytics.created_at)
        ).all()
        
        # 오늘의 평균 점수
        today_scores = db.query(
            func.avg(SimpleAnalytics.percentage).label('avg_score'),
            func.min(SimpleAnalytics.percentage).label('min_score'),
            func.max(SimpleAnalytics.percentage).label('max_score')
        ).join(Survey, Survey.id == SimpleAnalytics.survey_id).filter(
            func.date(SimpleAnalytics.created_at) == today
        ).first()
        
        return {
            "hourly_responses": [
                {"hour": h.hour, "count": h.count}
                for h in hourly_analytics
            ],
            "today_scores": {
                "average": float(today_scores.avg_score) if today_scores.avg_score else 0,
                "minimum": float(today_scores.min_score) if today_scores.min_score else 0,
                "maximum": float(today_scores.max_score) if today_scores.max_score else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions/overview")
async def get_submissions_overview(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """워크스페이스의 설문 제출 현황 개요"""
    try:
        manager = SurveySubmissionManager()
        
        # workspace_id가 제공되지 않은 경우 첫 번째 워크스페이스 사용
        if not workspace_id:
            workspace = db.query(Workspace).first()
            
            if workspace:
                workspace_id = workspace.id
            else:
                return {
                    "recent_submissions": [],
                    "statistics": {
                        "total_submissions": 0,
                        "completed_submissions": 0,
                        "started_submissions": 0,
                        "abandoned_submissions": 0,
                        "completion_rate": 0
                    }
                }
        
        # 최근 제출 기록
        recent = manager.get_recent_submissions(workspace_id)
        
        # 통계 정보
        stats = manager.get_workspace_statistics(workspace_id)
        
        return {
            "recent_submissions": recent,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions/trend")
async def get_submissions_trend(
    workspace_id: Optional[str] = None,
    time_window: str = "day",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """시간대별 설문 제출 추이"""
    try:
        # workspace_id가 제공되지 않은 경우 첫 번째 워크스페이스 사용
        if not workspace_id:
            workspace = db.query(Workspace).first()
            
            if workspace:
                workspace_id = workspace.id
            else:
                return {
                    "trend_data": [],
                    "time_window": time_window
                }
            
        if time_window not in ['hour', 'day', 'week', 'month']:
            raise HTTPException(status_code=400, detail="Invalid time window")
        
        manager = SurveySubmissionManager()
        
        # 시간대별 제출 현황
        trend_data = manager.get_submission_counts_by_timeframe(
            workspace_id=workspace_id,
            start_date=start_date,
            end_date=end_date,
            group_by=time_window
        )
        
        return {
            "trend_data": trend_data,
            "time_window": time_window
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions/daily")
async def get_daily_submissions(
    workspace_id: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """일별 제출 현황"""
    try:
        # workspace_id가 제공되지 않은 경우 첫 번째 워크스페이스 사용
        if not workspace_id:
            workspace = db.query(Workspace).first()
            
            if workspace:
                workspace_id = workspace.id
            else:
                return {
                    "daily_trend": [],
                    "days": days
                }
        
        manager = SurveySubmissionManager()
        
        # 일별 제출 추이
        daily_trend = manager.get_submission_trend(
            workspace_id=workspace_id,
            days=days
        )
        
        return {
            "daily_trend": daily_trend,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions/recent")
async def get_recent_submissions(
    workspace_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """최근 설문 제출 목록"""
    try:
        # workspace_id가 제공되지 않은 경우 첫 번째 워크스페이스 사용
        if not workspace_id:
            workspace = db.query(Workspace).first()
            
            if workspace:
                workspace_id = workspace.id
            else:
                return []
        
        manager = SurveySubmissionManager()
        
        # 최근 제출 기록
        recent_submissions = manager.get_recent_submissions(
            workspace_id=workspace_id,
            limit=limit
        )
        
        return recent_submissions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/competencies")
async def get_competency_analytics(
    workspace_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """역량별 분석 데이터 조회"""
    try:
        # 모든 카테고리 조회
        categories = db.query(Category).all()

        if not categories:
            return {
                "competencies": [],
                "total_count": 0,
                "high_performing_count": 0,
                "needs_improvement_count": 0
            }

        # simple_analytics에서 응답 통계 조회 (모든 워크스페이스)
        analytics_query = db.query(
            func.count(SimpleAnalytics.id).label('total_responses'),
            func.avg(SimpleAnalytics.percentage).label('average_score')
        ).join(Survey, Survey.id == SimpleAnalytics.survey_id)

        # 날짜 필터링
        if start_date:
            analytics_query = analytics_query.filter(SimpleAnalytics.created_at >= start_date)
        if end_date:
            analytics_query = analytics_query.filter(SimpleAnalytics.created_at <= end_date)

        analytics_result = analytics_query.first()

        # 결과 포맷팅
        competencies = []
        for category in categories:
            # 각 카테고리에 대해 기본 정보 제공
            avg_score = float(analytics_result.average_score) if analytics_result.average_score else 0
            total_responses = analytics_result.total_responses or 0
            
            competencies.append({
                "name": category.name,
                "description": category.description or "",
                "total_responses": total_responses,
                "average_score": round(avg_score, 2),
                "status": "high" if avg_score >= 70 else 
                         "medium" if avg_score >= 50 else "low"
            })

        # 점수 기준으로 정렬
        competencies.sort(key=lambda x: x["average_score"], reverse=True)

        return {
            "competencies": competencies,
            "total_count": len(competencies),
            "high_performing_count": sum(1 for c in competencies if c["status"] == "high"),
            "needs_improvement_count": sum(1 for c in competencies if c["status"] == "low")
        }

    except Exception as e:
        print(f"역량 분석 데이터 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch competency analytics: {str(e)}"
        ) 