# Survey Backend API

FastAPI 기반의 설문조사 백엔드 API 서버입니다.

## 📝 주요 기능

-   **사용자 인증**: JWT 토큰 기반의 안전한 사용자 인증
-   **워크스페이스**: 프로젝트/팀 단위의 설문 관리를 위한 워크스페이스 기능
-   **설문 관리**: 설문 생성, 수정, 삭제 및 상태 관리
-   **엑셀 연동**: 엑셀 파일 업로드를 통한 설문 문항 일괄 생성
-   **온라인 평가**: 학생 및 평가자를 위한 온라인 설문 응답 시스템
-   **대시보드**: 설문 결과를 시각화하는 통계 및 대시보드
-   **리포트 생성**: 분석 리포트를 생성하여 AWS S3에 자동으로 저장

## 💻 기술 스택

-   **Backend**: FastAPI, Python 3
-   **Database**: MySQL (AWS RDS)
-   **ORM**: SQLAlchemy
-   **Cloud**: AWS (EC2, S3, RDS)
-   **Deployment**: Uvicorn, Shell Script (Blue-Green)

## 🏛️ 아키텍처 개요

이 프로젝트는 AWS 클라우드 환경 (서울 리전, ap-northeast-2) 에서 운영됩니다.

-   **Application Server**: AWS EC2 인스턴스(이름 : **survey22-dont-delete** (id : **i-04a562052fcb0700b** )| **`3.35.230.242`**)에서 FastAPI 애플리케이션이 실행됩니다.
-   **Database**: AWS RDS for MySQL을 사용하여 데이터를 안정적으로 저장하고 관리합니다.
-   **File Storage**: 생성된 리포트 및 파일들은 AWS S3 버킷에 저장됩니다.

## 🚀 시작하기

### 1. 의존성 설치

프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 참고하여 환경 변수를 설정합니다.

```env
# JWT
SECRET_KEY=your-secret-key-here-change-this-in-production

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=survey-uploads
```

**⚠️ 중요: 데이터베이스 연결 정보**

현재 데이터베이스 연결 정보(URL)가 `database/connection.py` 파일 내에 직접 작성되어 있습니다.
```python
# database/connection.py 예시
DATABASE_URL = "mysql+pymysql://admin:..." 
```
보안을 위해 이 정보를 코드에서 분리하여 `.env` 파일로 관리하는 것을 강력히 권장합니다.
만약 `database/connection.py`를 환경 변수를 사용하도록 수정한다면, 아래와 같이 `.env` 파일에 데이터베이스 정보를 추가할 수 있습니다.

```env
# .env (추가 권장)
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>
```

### 3. 서버 실행

서버는 **Production (배포용)**과 **Development (개발/테스트용)** 두 가지 모드로 실행할 수 있습니다.

#### Production (배포용 서버)

-   **Public IP**: `3.35.230.242`
-   **Port**: `8080`

프로덕션 서버 배포는 `deploy.sh` 스크립트를 통해 **무중단 배포(Blue-Green Deployment)** 방식으로 이루어집니다.

```bash
# 프로젝트 디렉토리로 이동
cd /home/ec2-user/survey-back 

# 배포 스크립트 실행
./deploy.sh
```

**스크립트 동작 과정:**
1.  Git 리포지토리에서 최신 코드를 가져옵니다 (`git pull`).
2.  의존성을 업데이트합니다 (`pip install`).
3.  새 버전을 스테이징 포트(`8081`)에서 먼저 실행합니다.
4.  헬스 체크(`/health`)를 통해 새 버전이 정상 동작하는지 확인합니다.
5.  정상 동작이 확인되면, 기존 프로덕션 프로세스를 종료하고 새 버전을 메인 포트(`8080`)에서 실행합니다.

#### Development (개발/테스트용 서버)

기능을 개발하거나 테스트할 때는 `--reload` 옵션을 사용하여 코드가 변경될 때마다 서버가 자동으로 재시작되도록 실행할 수 있습니다.

```bash
# 포트 8081에서 테스트 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

## 📚 API 문서

서버가 실행되면 아래 URL을 통해 API 문서를 확인할 수 있습니다.

**Production 서버 (`http://3.35.230.242:8080`)**
-   Swagger UI: http://3.35.230.242:8080/docs
-   ReDoc: http://3.35.230.242:8080/redoc

**Development 서버 (`http://3.35.230.242:8081`)**
-   Swagger UI: http://3.35.230.242:8081/docs
-   ReDoc: http://3.35.230.242:8081/redoc

## 프로젝트 구조

```
.
├── alembic/                # 데이터베이스 스키마 마이그레이션 (Alembic)
│   └── versions/           # 마이그레이션 스크립트 버전
├── database/               # 데이터베이스 관련 로직 및 일회성 스크립트
│   ├── connection.py       # DB 연결 및 세션 관리
│   └── ...                 # 데이터 추가/수정/정리용 스크립트
├── models/                 # SQLAlchemy ORM 모델
│   ├── __init__.py
│   ├── category.py
│   ├── survey.py
│   ├── user.py
│   └── workspace.py
├── routers/                # API 라우터 (엔드포인트)
│   ├── __init__.py
│   ├── assessment.py
│   ├── auth.py
│   ├── dashboard.py
│   ├── files.py
│   ├── reports.py
│   ├── surveys.py
│   └── workspaces.py
├── schemas/                # Pydantic 데이터 유효성 검사 스키마
│   ├── __init__.py
│   ├── auth.py
│   ├── survey.py
│   └── workspace.py
├── test/                   # 테스트 코드 디렉토리
├── utils/                  # 공통 유틸리티 함수
│   ├── __init__.py
│   └── auth.py
├── main.py                 # FastAPI 애플리케이션 진입점
├── deploy.sh               # 무중단 배포 스크립트
├── restart.sh              # 재시작 스크립트 (현재는 비어있음)
├── requirements.txt        # Python 의존성 목록
├── survey_submissions.py   # 설문 제출 데이터 처리 스크립트
└── README.md               # 본 문서
``` 
