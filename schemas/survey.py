from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class QuestionBase(BaseModel):
    question_text: str
    question_type: str
    options: Optional[List[Dict[str, Any]]] = None
    order: Optional[int] = None

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: str
    survey_id: str
    
    class Config:
        from_attributes = True

class SurveyBase(BaseModel):
    title: str
    description: Optional[str] = None
    scale_min: Optional[int] = 1
    scale_max: Optional[int] = 5
    max_questions: Optional[int] = 100

class SurveyCreate(SurveyBase):
    workspace_id: str

class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal['draft', 'active', 'inactive']] = None
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    max_questions: Optional[int] = None
    access_link: Optional[str] = None

class Survey(SurveyBase):
    id: str
    workspace_id: str
    status: Literal['draft', 'active', 'inactive']
    access_link: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SurveyStatusUpdate(BaseModel):
    status: Literal['draft', 'active', 'inactive']

class PresignedUrlRequest(BaseModel):
    filename: str

class PresignedUrlResponse(BaseModel):
    upload_url: str
    file_key: str

class UploadCompleteRequest(BaseModel):
    file_key: str

class AnswerCreate(BaseModel):
    question_id: str
    score: int

class SurveyResponseCreate(BaseModel):
    respondent_name: str
    respondent_email: str
    answers: List[AnswerCreate]

class AnalyticsResponse(BaseModel):
    total_score: float
    total_questions: int
    percentage: float

class SurveyResponse(BaseModel):
    id: str
    survey_id: str
    message: str
    analytics: Optional[AnalyticsResponse] = None

    class Config:
        from_attributes = True 