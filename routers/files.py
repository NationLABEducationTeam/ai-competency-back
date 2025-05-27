from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import pandas as pd
import os
from io import BytesIO
from database.connection import get_db
from models import User
from utils.auth import get_current_active_user

router = APIRouter()

@router.post("/upload/excel")
async def upload_excel_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 파일 확장자 확인
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")
    
    try:
        # 엑셀 파일 읽기
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # 데이터 검증
        required_columns = ['question', 'type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # 데이터 요약 반환
        return {
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient='records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.get("/template/excel")
async def download_excel_template(
    current_user: User = Depends(get_current_active_user)
):
    # 템플릿 데이터 생성
    template_data = {
        'question': [
            '귀하의 리더십 역량은 어느 정도라고 생각하십니까?',
            '팀워크 능력을 평가해주세요.',
            '문제 해결 능력은 어떻습니까?',
            '의사소통 능력을 평가해주세요.',
            '추가 의견이 있으시면 작성해주세요.'
        ],
        'type': ['rating', 'rating', 'rating', 'rating', 'text'],
        'options': [
            '[1,2,3,4,5]',
            '[1,2,3,4,5]',
            '[1,2,3,4,5]',
            '[1,2,3,4,5]',
            ''
        ],
        'required': [True, True, True, True, False]
    }
    
    # DataFrame 생성
    df = pd.DataFrame(template_data)
    
    # 임시 파일로 저장
    temp_file = "survey_template.xlsx"
    df.to_excel(temp_file, index=False)
    
    try:
        # 파일 응답 반환
        return FileResponse(
            temp_file,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename='survey_template.xlsx'
        )
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file):
            os.remove(temp_file) 