from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database.connection import get_db
from models.user import User
from schemas.auth import UserCreate, User as UserSchema, Token, UserLogin
from utils.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user
)

router = APIRouter()

@router.post("/register", response_model=UserSchema)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 확인
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # 새 사용자 생성
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 응답 형식
    return {
        "email": db_user.email,
        "name": db_user.name,
        "id": db_user.id,
        "created_at": db_user.created_at
    }

# JSON 형식 로그인 (프론트엔드용)
@router.post("/login", response_model=Token)
async def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """JSON 형식의 로그인 요청을 처리"""
    print(f"🔐 로그인 시도: {user_login.email}")
    
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user:
        print(f"❌ 사용자를 찾을 수 없음: {user_login.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ 사용자 찾음: {user.email}, 저장된 비밀번호 길이: {len(user.password)}")
    
    # 비밀번호 검증
    password_valid = verify_password(user_login.password, user.password)
    print(f"🔑 비밀번호 검증 결과: {password_valid}")
    
    if not password_valid:
        print(f"❌ 비밀번호 불일치")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ 로그인 성공: {user.email}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# OAuth2 형식 로그인 (표준 OAuth2 호환용)
@router.post("/login/oauth2", response_model=Token)
async def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 표준 form-data 로그인"""
    # OAuth2PasswordRequestForm은 username 필드를 사용하므로 email로 처리
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    return "Successfully logged out"

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # 응답 형식
    return {
        "email": current_user.email,
        "name": current_user.name,
        "id": current_user.id,
        "created_at": current_user.created_at
    } 