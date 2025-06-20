from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel
import boto3
import uuid
import os
from datetime import datetime
from database.connection import get_db
from models import (
    User, Survey, Workspace, Question, Response, Answer, SimpleAnalytics,
    SurveyCategoryMapping
)
from schemas.survey import (
    SurveyCreate,
    Survey as SurveySchema,
    SurveyUpdate,
    SurveyStatusUpdate,
    PresignedUrlRequest,
    PresignedUrlResponse,
    UploadCompleteRequest,
    SurveyResponse,
    SurveyResponseCreate,
    AnalyticsResponse
)
from utils.auth import get_current_active_user
import pandas as pd
from statistics import mean, quantiles
from survey_submissions import SurveySubmissionManager

router = APIRouter()

# S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'competency-surveys')

def format_survey_response(survey: Survey) -> dict:
    """설문 응답을 OpenAPI 형식으로 변환"""
    return {
        "title": survey.title,
        "description": survey.description,
        "id": survey.id,
        "workspace_id": survey.workspace_id,
        "scale_min": survey.scale_min,
        "scale_max": survey.scale_max,
        "max_questions": survey.max_questions,
        "status": survey.status,
        "access_link": survey.access_link,
        "created_at": survey.created_at,
        "updated_at": survey.updated_at,
        "target": survey.target
    }

@router.get("/", response_model=List[SurveySchema])
async def get_all_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 모든 설문 조회
    surveys = db.query(Survey).all()
    
    return [format_survey_response(survey) for survey in surveys]

@router.get("/workspace/{workspace_id}", response_model=List[SurveySchema])
async def get_surveys_by_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 워크스페이스 존재 확인
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    surveys = db.query(Survey).filter(Survey.workspace_id == workspace_id).all()
    
    return [format_survey_response(survey) for survey in surveys]

@router.get("/{survey_id}", response_model=SurveySchema)
async def get_survey(
    survey_id: str,
    db: Session = Depends(get_db)
):
    survey = db.query(Survey).filter(
        Survey.id == survey_id
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
        Workspace.id == survey.workspace_id
        #Workspace.user_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # UUID 생성
    survey_id = str(uuid.uuid4())
    
    # 설문 생성
    db_survey = Survey(
        id=survey_id,
        **survey.dict(),
        status='active'  # 기본 상태
    )
    
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    
    return format_survey_response(db_survey)

@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 존재 여부 및 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
        #Workspace.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    try:
        # 설문-카테고리 매핑 삭제
        db.query(SurveyCategoryMapping).filter(
            SurveyCategoryMapping.survey_id == survey_id
        ).delete()
        
        # 설문 삭제
        db.delete(survey)
        db.commit()
        
        return {"success": True, "message": "Survey deleted successfully"}
    except Exception as e:
        db.rollback()
        error_str = str(e)
        
        # 외래 키 제약 조건 에러 감지
        if "foreign key constraint fails" in error_str.lower() or "1451" in error_str:
            if "survey_submissions" in error_str:
                raise HTTPException(
                    status_code=400, 
                    detail="이 설문은 응답 기록이 있어 삭제할 수 없습니다. 설문을 비활성화하거나 응답 기록을 먼저 삭제해주세요."
                )
            elif "simple_analytics" in error_str:
                raise HTTPException(
                    status_code=400, 
                    detail="이 설문은 분석 데이터가 있어 삭제할 수 없습니다. 관련 데이터를 먼저 삭제해주세요."
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="이 설문은 관련 데이터가 있어 삭제할 수 없습니다. 관련 데이터를 먼저 삭제하거나 설문을 비활성화해주세요."
                )
        else:
            raise HTTPException(status_code=500, detail=f"설문 삭제 중 오류가 발생했습니다: {str(e)}")

@router.post("/{survey_id}/upload")
async def upload_excel(
    survey_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
        #Workspace.user_id == current_user.id
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
    survey_id: str,
    request: PresignedUrlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
        #Workspace.user_id == current_user.id
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
    survey_id: str,
    request: UploadCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 설문 권한 확인
    survey = db.query(Survey).join(Workspace).filter(
        Survey.id == survey_id
        #Workspace.user_id == current_user.id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # 파일 URL 업데이트
    survey.excel_file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{request.file_key}"
    db.commit()
    
    return "Upload confirmed successfully"

@router.put("/{survey_id}/status", response_model=SurveySchema)
async def update_survey_status(
    survey_id: str,
    status_update: SurveyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # 설문 조회
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        # 워크스페이스 권한 확인
        workspace = db.query(Workspace).filter(
            Workspace.id == survey.workspace_id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # 상태 업데이트
        if status_update.status not in ['draft', 'active', 'inactive']:
            raise HTTPException(
                status_code=400,
                detail="Status must be one of: draft, active, inactive"
            )
        
        survey.status = status_update.status
        db.commit()
        db.refresh(survey)
        
        return format_survey_response(survey)
    except Exception as e:
        print(f"설문 상태 업데이트 중 오류: {e}")
        raise HTTPException(status_code=500, detail="Failed to update survey status")

@router.post("/{survey_id}/archive")
async def archive_survey(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """설문을 draft 상태로 변경하여 보관 처리"""
    try:
        # 설문 확인
        survey = db.query(Survey).filter(
            Survey.id == survey_id
        ).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="설문을 찾을 수 없습니다.")
        
        # 상태를 draft로 변경
        survey.status = 'draft'
        db.commit()
        db.refresh(survey)
        
        return {
            "success": True,
            "message": "설문이 보관 처리되었습니다.",
            "survey": format_survey_response(survey)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"설문 보관 처리 중 오류가 발생했습니다: {str(e)}"
        )

async def calculate_analytics(
    db: Session,
    survey_id: str,
    response_id: str,
    answers: List[Dict]
) -> Tuple[SimpleAnalytics, AnalyticsResponse]:
    """
    설문 응답에 대한 분석을 수행하고 결과를 저장
    """
    try:
        # 응답 정보 조회
        response = db.query(Response).filter(Response.id == response_id).first()
        if not response:
            return None, None

        # 답변 점수 계산
        total_score = 0
        total_questions = len(answers)
        
        for answer in answers:
            total_score += answer["score"]

        # 백분율 계산
        percentage = (total_score / (total_questions * 5)) * 100

        # simple_analytics 테이블에 저장
        analytics_db = SimpleAnalytics(
            id=str(uuid.uuid4()),
            survey_id=survey_id,
            respondent_name=response.respondent_name,
            total_score=total_score,
            total_questions=total_questions,
            percentage=percentage,
            created_at=datetime.now()
        )
        db.add(analytics_db)
        
        # 응답 스키마 생성
        analytics_schema = AnalyticsResponse(
            total_score=total_score,
            total_questions=total_questions,
            percentage=round(percentage, 1)
        )
        
        return analytics_db, analytics_schema
        
    except Exception as e:
        print(f"분석 데이터 계산 중 오류: {e}")
        db.rollback()
        return None, None

@router.post("/{survey_id}/responses", response_model=SurveyResponse)
async def submit_survey_response(
    survey_id: str,
    response: SurveyResponseCreate,
    db: Session = Depends(get_db)
):
    try:
        # 설문 존재 여부 확인
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if survey.status != 'active':
            raise HTTPException(
                status_code=400,
                detail="This survey is not currently active"
            )

        # 응답 데이터 생성
        response_id = str(uuid.uuid4())
        new_response = Response(
            id=response_id,
            survey_id=survey_id,
            respondent_name=response.respondent_name,
            respondent_email=response.respondent_email,
            completed=True,
            created_at=datetime.now()
        )
        db.add(new_response)

        # 답변 저장
        for answer in response.answers:
            answer_detail = Answer(
                id=str(uuid.uuid4()),
                response_id=response_id,
                question_id=answer.question_id,
                score=answer.score,
                created_at=datetime.now()
            )
            db.add(answer_detail)

        # 분석 데이터 계산 및 저장
        analytics_db, analytics_schema = await calculate_analytics(
            db,
            survey_id,
            response_id,
            [{"question_id": a.question_id, "score": a.score} for a in response.answers]
        )

        if not analytics_db or not analytics_schema:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate analytics"
            )

        db.commit()

        return {
            "id": response_id,
            "survey_id": survey_id,
            "message": "Survey response submitted successfully",
            "analytics": analytics_schema
        }
    except Exception as e:
        print(f"설문 응답 저장 중 오류: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save survey response"
        )

@router.get("/{survey_id}/responses", response_model=List[SurveyResponse])
async def get_survey_responses(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # 설문 및 권한 확인
        survey = db.query(Survey).join(Workspace).filter(
            Survey.id == survey_id
            #Workspace.user_id == current_user.id
        ).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # 응답 목록 조회
        responses = db.query(Response).filter(
            Response.workspace_id == survey.workspace_id
        ).all()

        result = []
        for response in responses:
            # 응답 상세 데이터 조회
            answers = db.query(Answer).filter(
                Answer.response_id == response.id
            ).all()

            result.append({
                "id": str(response.id),
                "respondent_name": response.respondent_name,
                "respondent_email": response.respondent_email,
                "respondent_organization": response.respondent_organization,
                "respondent_education": response.respondent_education,
                "respondent_major": response.respondent_major,
                "respondent_age": response.respondent_age,
                "completed": response.completed,
                "created_at": response.created_at,
                "answer_count": len(answers)
            })

        return result
    except Exception as e:
        print(f"설문 응답 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch survey responses"
        )

# ===== 설문 제출 로그 관련 엔드포인트 =====

class SubmissionLogCreate(BaseModel):
    respondent_name: str
    respondent_email: str

class SubmissionLogUpdate(BaseModel):
    completion_status: str  # 'completed', 'abandoned'
    completion_time: Optional[int] = None  # 완료 소요 시간(초)

class SubmissionLog(BaseModel):
    id: str
    workspace_id: str
    survey_id: str
    respondent_name: str
    respondent_email: str
    submission_date: datetime
    completion_status: str
    completion_time: Optional[int]

@router.post("/{survey_id}/submissions/start")
async def start_survey_submission(
    survey_id: str,
    submission_data: SubmissionLogCreate,
    db: Session = Depends(get_db)
):
    """설문 시작 로그 생성"""
    try:
        # 설문 존재 여부 확인
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if survey.status != 'active':
            raise HTTPException(
                status_code=400,
                detail="This survey is not currently active"
            )

        # 제출 로그 생성
        manager = SurveySubmissionManager()
        submission_id = manager.create_submission(
            workspace_id=survey.workspace_id,
            survey_id=survey_id,
            respondent_email=submission_data.respondent_email,
            respondent_name=submission_data.respondent_name
        )

        if not submission_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create submission log"
            )

        return {
            "submission_id": submission_id,
            "survey_id": survey_id,
            "workspace_id": survey.workspace_id,
            "message": "Survey submission started successfully"
        }

    except Exception as e:
        print(f"설문 시작 로그 생성 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start survey submission"
        )

@router.put("/{survey_id}/submissions/{submission_id}/complete")
async def complete_survey_submission(
    survey_id: str,
    submission_id: str,
    completion_data: SubmissionLogUpdate,
    db: Session = Depends(get_db)
):
    """설문 완료 로그 업데이트"""
    try:
        # 설문 존재 여부 확인
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # 제출 로그 업데이트
        manager = SurveySubmissionManager()
        success = manager.update_submission_status(
            submission_id=submission_id,
            status=completion_data.completion_status,
            completion_time=completion_data.completion_time
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update submission status"
            )

        return {
            "submission_id": submission_id,
            "survey_id": survey_id,
            "status": completion_data.completion_status,
            "completion_time": completion_data.completion_time,
            "message": f"Survey submission marked as {completion_data.completion_status}"
        }

    except Exception as e:
        print(f"설문 완료 로그 업데이트 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to complete survey submission"
        )

@router.get("/{survey_id}/submissions")
async def get_survey_submissions(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """특정 설문의 제출 로그 조회"""
    try:
        # 설문 및 권한 확인
        survey = db.query(Survey).join(Workspace).filter(
            Survey.id == survey_id
        ).first()
        
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        # 제출 로그 조회
        manager = SurveySubmissionManager()
        
        # 설문별 제출 기록 조회 (survey_submissions 테이블에서)
        submissions_sql = """
        SELECT * FROM survey_submissions 
        WHERE survey_id = %s 
        ORDER BY submission_date DESC
        """
        
        submissions = []
        try:
            with manager.connection.cursor() as cursor:
                cursor.execute(submissions_sql, (survey_id,))
                results = cursor.fetchall()
                
                for row in results:
                    submissions.append({
                        "id": row['id'],
                        "workspace_id": row['workspace_id'],
                        "survey_id": row['survey_id'],
                        "respondent_name": row['respondent_name'],
                        "respondent_email": row['respondent_email'],
                        "submission_date": row['submission_date'],
                        "completion_status": row['completion_status'],
                        "completion_time": row['completion_time']
                    })
        except Exception as e:
            print(f"제출 로그 조회 실패: {e}")
            return {"submissions": [], "total_count": 0}

        return {
            "survey_id": survey_id,
            "survey_title": survey.title,
            "submissions": submissions,
            "total_count": len(submissions),
            "completed_count": len([s for s in submissions if s['completion_status'] == 'completed']),
            "started_count": len([s for s in submissions if s['completion_status'] == 'started']),
            "abandoned_count": len([s for s in submissions if s['completion_status'] == 'abandoned'])
        }

    except Exception as e:
        print(f"설문 제출 로그 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch survey submissions"
        )

@router.get("/workspace/{workspace_id}/submissions")
async def get_workspace_submissions(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """워크스페이스의 모든 설문 제출 로그 조회"""
    try:
        # 워크스페이스 권한 확인
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # 제출 로그 조회
        manager = SurveySubmissionManager()
        
        # 워크스페이스별 제출 기록 조회
        submissions_sql = """
        SELECT ss.*, s.title as survey_title 
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        WHERE ss.workspace_id = %s 
        ORDER BY ss.submission_date DESC
        """
        
        submissions = []
        try:
            with manager.connection.cursor() as cursor:
                cursor.execute(submissions_sql, (workspace_id,))
                results = cursor.fetchall()
                
                for row in results:
                    submissions.append({
                        "id": row['id'],
                        "workspace_id": row['workspace_id'],
                        "survey_id": row['survey_id'],
                        "survey_title": row['survey_title'],
                        "respondent_name": row['respondent_name'],
                        "respondent_email": row['respondent_email'],
                        "submission_date": row['submission_date'],
                        "completion_status": row['completion_status'],
                        "completion_time": row['completion_time']
                    })
        except Exception as e:
            print(f"워크스페이스 제출 로그 조회 실패: {e}")
            return {"submissions": [], "total_count": 0}

        return {
            "workspace_id": workspace_id,
            "workspace_title": workspace.title,
            "submissions": submissions,
            "total_count": len(submissions),
            "completed_count": len([s for s in submissions if s['completion_status'] == 'completed']),
            "started_count": len([s for s in submissions if s['completion_status'] == 'started']),
            "abandoned_count": len([s for s in submissions if s['completion_status'] == 'abandoned'])
        }

    except Exception as e:
        print(f"워크스페이스 제출 로그 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch workspace submissions"
        )

@router.get("/submissions/student/{student_email}")
async def get_student_submissions(
    student_email: str,
    workspace_id: Optional[str] = Query(None, description="워크스페이스로 필터링"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """특정 학생의 설문 제출 로그 조회"""
    try:
        # 제출 로그 조회
        manager = SurveySubmissionManager()
        
        # 학생별 제출 기록 조회
        base_sql = """
        SELECT ss.*, s.title as survey_title, w.title as workspace_title
        FROM survey_submissions ss
        JOIN surveys s ON ss.survey_id = s.id
        JOIN workspace w ON ss.workspace_id = w.id
        WHERE ss.respondent_email = %s
        """
        
        params = [student_email]
        if workspace_id:
            base_sql += " AND ss.workspace_id = %s"
            params.append(workspace_id)
        
        base_sql += " ORDER BY ss.submission_date DESC"
        
        submissions = []
        try:
            with manager.connection.cursor() as cursor:
                cursor.execute(base_sql, params)
                results = cursor.fetchall()
                
                for row in results:
                    submissions.append({
                        "id": row['id'],
                        "workspace_id": row['workspace_id'],
                        "workspace_title": row['workspace_title'],
                        "survey_id": row['survey_id'],
                        "survey_title": row['survey_title'],
                        "respondent_name": row['respondent_name'],
                        "respondent_email": row['respondent_email'],
                        "submission_date": row['submission_date'],
                        "completion_status": row['completion_status'],
                        "completion_time": row['completion_time']
                    })
        except Exception as e:
            print(f"학생 제출 로그 조회 실패: {e}")
            return {"submissions": [], "total_count": 0}

        return {
            "student_email": student_email,
            "student_name": submissions[0]['respondent_name'] if submissions else None,
            "workspace_filter": workspace_id,
            "submissions": submissions,
            "total_count": len(submissions),
            "completed_count": len([s for s in submissions if s['completion_status'] == 'completed']),
            "started_count": len([s for s in submissions if s['completion_status'] == 'started']),
            "abandoned_count": len([s for s in submissions if s['completion_status'] == 'abandoned'])
        }

    except Exception as e:
        print(f"학생 제출 로그 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch student submissions"
        ) 