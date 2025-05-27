from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class QuestionBase(BaseModel):
    question_text: str
    question_type: str
    options: Optional[List[Dict[str, Any]]] = None
    order: Optional[int] = None

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    survey_id: int
    
    class Config:
        from_attributes = True

class SurveyBase(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None

class SurveyCreate(SurveyBase):
    workspace_id: int

class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Survey(SurveyBase):
    id: int
    workspace_id: int
    status: str
    excel_file_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[Question] = []
    
    class Config:
        from_attributes = True

class SurveyStatusUpdate(BaseModel):
    status: str  # draft, active, completed

class PresignedUrlResponse(BaseModel):
    upload_url: str
    file_key: str

class UploadCompleteRequest(BaseModel):
    file_key: str 