from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional
from database.connection import get_db
from models import User, Survey, Workspace, SimpleAnalytics
from utils.auth import get_current_active_user
from survey_submissions import SurveySubmissionManager
import logging

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """대시보드 상단 요약 통계"""
    try:
        submission_manager = SurveySubmissionManager()
        
        # 전체 누적 참여자 수와 완료율 계산
        sql = """
        SELECT 
            COUNT(*) as total_submissions,
            SUM(CASE WHEN completion_status = 'completed' THEN 1 ELSE 0 END) as completed_submissions
        FROM survey_submissions
        """
        with submission_manager.connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
            
        total_submissions = result['total_submissions']
        completed_submissions = result['completed_submissions']
        completion_rate = (completed_submissions / total_submissions * 100) if total_submissions > 0 else 0
        
        # 전체 평균 점수
        avg_score = db.query(func.avg(SimpleAnalytics.percentage)).scalar() or 0
        
        return {
            "total_submissions": total_submissions,
            "completion_rate": round(completion_rate, 1),
            "average_score": round(avg_score, 1)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard summary: {str(e)}"
        )

@router.get("/survey-stats")
async def get_survey_participation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """설문별 참여율 통계"""
    try:
        logger.info(f"Fetching survey stats for user: {current_user.email}")
        submission_manager = SurveySubmissionManager()
        
        sql = """
        SELECT 
            s.id,
            s.title,
            s.target,
            s.status,
            w.title as workspace_title,
            COUNT(ss.id) as completed_count
        FROM surveys s
        JOIN workspace w ON s.workspace_id = w.id
        LEFT JOIN survey_submissions ss ON ss.survey_id = s.id AND ss.completion_status = 'completed'
        GROUP BY s.id, s.title, s.target, s.status, w.title
        """
        
        with submission_manager.connection.cursor() as cursor:
            cursor.execute(sql)
            surveys = cursor.fetchall()
            
        result = []
        for survey in surveys:
            try:
                achievement_rate = (survey['completed_count'] / survey['target'] * 100) if survey['target'] > 0 else 0
                result.append({
                    "survey_id": survey['id'],
                    "title": survey['title'],
                    "target": survey['target'],
                    "completed_count": survey['completed_count'],
                    "achievement_rate": round(achievement_rate, 1),
                    "status": survey['status'],
                    "workspace_title": survey['workspace_title']
                })
            except Exception as calc_error:
                logger.error(f"Error processing survey {survey['id']}: {str(calc_error)}")
                raise
        
        return result
    except Exception as e:
        logger.error(f"Failed to fetch survey statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch survey statistics: {str(e)}"
        )

@router.get("/recent-submissions")
async def get_recent_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = 10
):
    """최근 응답 현황"""
    try:
        submission_manager = SurveySubmissionManager()
        
        sql = """
        SELECT 
            ss.respondent_name,
            ss.submission_date,
            ss.completion_status,
            s.title as survey_title,
            w.title as workspace_title
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        JOIN workspace w ON s.workspace_id = w.id
        ORDER BY ss.submission_date DESC
        LIMIT %s
        """
        
        with submission_manager.connection.cursor() as cursor:
            cursor.execute(sql, (limit,))
            recent = cursor.fetchall()
        
        return [{
            "respondent_name": r['respondent_name'],
            "survey_title": r['survey_title'],
            "workspace_title": r['workspace_title'],
            "submitted_at": r['submission_date'],
            "status": r['completion_status']
        } for r in recent]
    except Exception as e:
        logger.error(f"Failed to fetch recent submissions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent submissions: {str(e)}"
        )

@router.get("/time-stats")
async def get_time_based_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_id: Optional[str] = None,
    survey_id: Optional[str] = None,
    days: Optional[int] = 30
):
    """시간 기반 통계 - raw data 제공"""
    try:
        submission_manager = SurveySubmissionManager()
        
        sql = """
        SELECT 
            ss.submission_date,
            ss.id,
            ss.completion_status,
            s.title as survey_title,
            w.title as workspace_title
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        JOIN workspace w ON s.workspace_id = w.id
        WHERE 1=1
        """
        params = []
        
        if workspace_id:
            sql += " AND s.workspace_id = %s"
            params.append(workspace_id)
        if survey_id:
            sql += " AND ss.survey_id = %s"
            params.append(survey_id)
        if days:
            sql += " AND ss.submission_date >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            params.append(days)
            
        sql += " ORDER BY ss.submission_date"
        
        with submission_manager.connection.cursor() as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()

        return [{
            "timestamp": r['submission_date'],
            "response_id": r['id'],
            "survey_title": r['survey_title'],
            "workspace_title": r['workspace_title'],
            "status": r['completion_status']
        } for r in results]

    except Exception as e:
        logger.error(f"Failed to fetch time-based statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch time-based statistics: {str(e)}"
        ) 