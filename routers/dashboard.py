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
    try:
        # 워크스페이스 정보 조회
        workspace = db.query(Workspace).filter(
            Workspace.user_id == current_user.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # 통계 데이터 조회
        analytics = db.query(SimpleAnalytics).join(Survey).filter(
            Survey.workspace_id == workspace.id
        ).all()

        if not analytics:
            return {
                "total_responses": 0,
                "average_score": 0,
                "score_distribution": {},
                "trend_data": []
            }

        # 총 응답 수
        total_responses = len(analytics)

        # 평균 점수
        average_score = sum(a.percentage for a in analytics) / total_responses

        # 점수 분포 (10점 단위로 버킷팅)
        score_distribution = {}
        for a in analytics:
            bucket = int(a.percentage // 10) * 10
            score_distribution[str(bucket)] = score_distribution.get(str(bucket), 0) + 1

        # 최근 30일 추세
        thirty_days_ago = datetime.now() - timedelta(days=30)
        trend_data = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            day_analytics = [a for a in analytics if a.created_at.date() == date.date()]
            
            if day_analytics:
                avg_score = sum(a.percentage for a in day_analytics) / len(day_analytics)
            else:
                avg_score = 0
                
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "average_score": round(avg_score, 1),
                "response_count": len(day_analytics)
            })

        return {
            "total_responses": total_responses,
            "average_score": round(average_score, 1),
            "score_distribution": score_distribution,
            "trend_data": trend_data
        }

    except Exception as e:
        print(f"대시보드 통계 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch dashboard statistics"
        )

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