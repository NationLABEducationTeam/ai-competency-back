#!/bin/bash

# 무중단 배포 스크립트 (Blue-Green Deployment)
# 사용법: ./deploy.sh

set -e

# 설정 변수
MAIN_PORT=8080
STAGING_PORT=8081
APP_DIR="/home/ec2-user/survey-back"
PYTHON_PATH="/home/ec2-user/.local/bin/uvicorn"

echo "🚀 무중단 배포를 시작합니다..."

# 현재 디렉토리로 이동
cd $APP_DIR

# Git에서 최신 코드 가져오기 (선택사항)
echo "📥 최신 코드를 가져옵니다..."
git pull origin main || echo "Git pull 실패 또는 변경사항 없음"

# 종속성 업데이트
echo "📦 종속성을 업데이트합니다..."
pip install -r requirements.txt

# 스테이징 포트에서 새 버전 실행
echo "🎭 스테이징 포트 $STAGING_PORT 에서 새 버전을 실행합니다..."
nohup $PYTHON_PATH main:app --host 0.0.0.0 --port $STAGING_PORT > staging.log 2>&1 &
STAGING_PID=$!

# 새 버전이 정상적으로 시작될 때까지 대기
echo "⏳ 새 버전이 시작될 때까지 대기합니다..."
sleep 10

# 헬스체크
echo "🏥 헬스체크를 수행합니다..."
if curl -f http://localhost:$STAGING_PORT/health > /dev/null 2>&1; then
    echo "✅ 새 버전이 정상적으로 실행되고 있습니다!"
else
    echo "❌ 새 버전 실행 실패. 배포를 중단합니다."
    kill $STAGING_PID 2>/dev/null || true
    exit 1
fi

# 기존 프로덕션 프로세스 종료
echo "🔄 기존 프로덕션 프로세스를 종료합니다..."
OLD_PID=$(ps aux | grep "uvicorn main:app.*--port $MAIN_PORT" | grep -v grep | awk '{print $2}' | head -1)
if [ ! -z "$OLD_PID" ]; then
    kill $OLD_PID
    echo "⏳ 기존 프로세스 종료 대기..."
    sleep 5
fi

# 새 버전을 메인 포트로 이동
echo "🔀 새 버전을 메인 포트 $MAIN_PORT 로 이동합니다..."
kill $STAGING_PID 2>/dev/null || true
sleep 2

nohup $PYTHON_PATH main:app --host 0.0.0.0 --port $MAIN_PORT > nohup.out 2>&1 &
NEW_PID=$!

# 최종 헬스체크
echo "⏳ 최종 헬스체크를 위해 대기합니다..."
sleep 10

if curl -f http://localhost:$MAIN_PORT/health > /dev/null 2>&1; then
    echo "🎉 배포가 성공적으로 완료되었습니다!"
    echo "📋 새 프로세스 PID: $NEW_PID"
    echo "🌐 서비스 URL: http://localhost:$MAIN_PORT"
else
    echo "❌ 최종 헬스체크 실패. 서비스를 확인해주세요."
    exit 1
fi

# 임시 파일 정리
rm -f staging.log

echo "✨ 배포 완료!" 