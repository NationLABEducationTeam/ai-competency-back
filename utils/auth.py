from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
import os
import hashlib

# 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/oauth2")

def verify_password(plain_password, stored_password):
    """비밀번호 검증 - 여러 형식 지원"""
    try:
        # 1. bcrypt 해시 형식인지 확인
        if stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith('$2y$'):
            return pwd_context.verify(plain_password, stored_password)
        
        # 2. SHA256 해시 형식인지 확인 (64자리 hex)
        if len(stored_password) == 64 and all(c in '0123456789abcdef' for c in stored_password.lower()):
            sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            return sha256_hash == stored_password.lower()
        
        # 3. 평문 비교 (테스트 환경용)
        return plain_password == stored_password
        
    except Exception as e:
        print(f"비밀번호 검증 오류: {e}")
        # 최후의 수단으로 평문 비교
        return plain_password == stored_password

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user
    except:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # is_active 체크 제거, 단순히 현재 사용자 반환
    return current_user 