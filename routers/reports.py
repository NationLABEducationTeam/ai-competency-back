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
    region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'competency-surveys')

class StudentResult(BaseModel):
    student_name: str
    file_key: str
    size: int
    last_modified: datetime
    download_url: str
    result_type: str  # "original" or "ai"

class SurveyResults(BaseModel):
    survey_name: str
    total_students: int
    original_results: List[StudentResult]
    ai_results: List[StudentResult]

@router.get("/workspaces")
async def get_report_workspaces(
    current_user: User = Depends(get_current_active_user)
):
    """리포트가 있는 워크스페이스 목록 조회"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='reports/',
            Delimiter='/'
        )
        
        workspaces = []
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                workspace_name = prefix['Prefix'].replace('reports/', '').rstrip('/')
                workspaces.append(workspace_name)
        
        return {
            "workspaces": workspaces,
            "total_count": len(workspaces)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch workspaces: {str(e)}"
        )

@router.get("/workspaces/{workspace_name}/surveys")
async def get_workspace_surveys(
    workspace_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """워크스페이스의 설문별 리포트 목록 조회"""
    try:
        prefix = f"reports/{workspace_name}/"
        
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=prefix,
            Delimiter='/'
        )
        
        surveys = []
        if 'CommonPrefixes' in response:
            for prefix_obj in response['CommonPrefixes']:
                survey_name = prefix_obj['Prefix'].replace(prefix, '').rstrip('/')
                
                # 설문별 학생 수 조회 (AI 폴더 기준)
                ai_prefix = f"{prefix_obj['Prefix']}AI/"
                ai_response = s3_client.list_objects_v2(
                    Bucket=BUCKET_NAME,
                    Prefix=ai_prefix
                )
                ai_student_count = ai_response.get('KeyCount', 0)
                
                # 일반 결과 파일 수 조회
                survey_response = s3_client.list_objects_v2(
                    Bucket=BUCKET_NAME,
                    Prefix=prefix_obj['Prefix']
                )
                # AI 폴더 제외한 직접 파일만 계산
                original_count = 0
                if 'Contents' in survey_response:
                    for obj in survey_response['Contents']:
                        relative_path = obj['Key'].replace(prefix_obj['Prefix'], '')
                        if '/' not in relative_path and relative_path.endswith('.json'):
                            original_count += 1
                
                surveys.append({
                    "survey_name": survey_name,
                    "original_results_count": original_count,
                    "ai_results_count": ai_student_count,
                    "total_students": max(original_count, ai_student_count)
                })
        
        return {
            "workspace_name": workspace_name,
            "surveys": surveys,
            "total_surveys": len(surveys)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch surveys: {str(e)}"
        )

@router.get("/workspaces/{workspace_name}/surveys/{survey_name}")
async def get_survey_results(
    workspace_name: str,
    survey_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """특정 설문의 학생별 결과 파일들 조회 (일반 + AI)"""
    try:
        base_prefix = f"reports/{workspace_name}/{survey_name}/"
        ai_prefix = f"{base_prefix}AI/"
        
        # AI 결과 파일들 조회
        ai_response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=ai_prefix
        )
        
        ai_results = []
        if 'Contents' in ai_response:
            for obj in ai_response['Contents']:
                if obj['Key'] != ai_prefix and obj['Key'].endswith('.json'):
                    student_name = obj['Key'].replace(ai_prefix, '').replace('.json', '')
                    download_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{obj['Key']}"
                    
                    ai_results.append({
                        "student_name": student_name,
                        "file_key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'],
                        "download_url": download_url,
                        "result_type": "ai"
                    })
        
        # 일반 결과 파일들 조회
        original_response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=base_prefix,
            Delimiter='/'
        )
        
        original_results = []
        if 'Contents' in original_response:
            for obj in original_response['Contents']:
                if obj['Key'] != base_prefix and obj['Key'].endswith('.json'):
                    relative_path = obj['Key'].replace(base_prefix, '')
                    # AI 폴더가 아닌 직접 파일만
                    if '/' not in relative_path:
                        student_name = relative_path.replace('.json', '')
                        download_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{obj['Key']}"
                        
                        original_results.append({
                            "student_name": student_name,
                            "file_key": obj['Key'],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'],
                            "download_url": download_url,
                            "result_type": "original"
                        })
        
        # 학생 이름별로 정렬
        ai_results.sort(key=lambda x: x['student_name'])
        original_results.sort(key=lambda x: x['student_name'])
        
        return {
            "workspace_name": workspace_name,
            "survey_name": survey_name,
            "total_students": len(set([r['student_name'] for r in ai_results + original_results])),
            "ai_results": ai_results,
            "original_results": original_results,
            "ai_results_count": len(ai_results),
            "original_results_count": len(original_results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch survey results: {str(e)}"
        )

@router.get("/workspaces/{workspace_name}/surveys/{survey_name}/ai")
async def get_ai_results_only(
    workspace_name: str,
    survey_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """AI 분석 결과만 조회 (프론트엔드에서 주로 사용)"""
    try:
        ai_prefix = f"reports/{workspace_name}/{survey_name}/AI/"
        
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=ai_prefix
        )
        
        ai_results = []
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'] != ai_prefix and obj['Key'].endswith('.json'):
                    student_name = obj['Key'].replace(ai_prefix, '').replace('.json', '')
                    download_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{obj['Key']}"
                    
                    ai_results.append({
                        "student_name": student_name,
                        "file_key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'],
                        "download_url": download_url
                    })
        
        # 학생 이름별로 정렬
        ai_results.sort(key=lambda x: x['student_name'])
        
        return {
            "workspace_name": workspace_name,
            "survey_name": survey_name,
            "ai_results": ai_results,
            "total_count": len(ai_results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch AI results: {str(e)}"
        )

@router.get("/workspaces/{workspace_name}/surveys/{survey_name}/students/{student_name}")
async def get_student_result(
    workspace_name: str,
    survey_name: str,
    student_name: str,
    result_type: str = Query("ai", description="결과 타입: 'ai' 또는 'original'"),
    current_user: User = Depends(get_current_active_user)
):
    """특정 학생의 결과 파일 직접 조회"""
    try:
        if result_type == "ai":
            file_key = f"reports/{workspace_name}/{survey_name}/AI/{student_name}.json"
        else:
            file_key = f"reports/{workspace_name}/{survey_name}/{student_name}.json"
        
        # 파일 존재 확인
        try:
            response = s3_client.head_object(Bucket=BUCKET_NAME, Key=file_key)
            download_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}"
            
            return {
                "student_name": student_name,
                "file_key": file_key,
                "size": response['ContentLength'],
                "last_modified": response['LastModified'],
                "download_url": download_url,
                "result_type": result_type
            }
            
        except s3_client.exceptions.NoSuchKey:
            raise HTTPException(
                status_code=404,
                detail=f"Result file not found for student '{student_name}' (type: {result_type})"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch student result: {str(e)}"
        ) 