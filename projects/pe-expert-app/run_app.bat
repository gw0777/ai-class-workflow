@echo off
echo 🏃 특수체육(APA) 프로그램 전문가 앱 시작
echo ======================================
echo.

REM 가상환경 활성화 (존재하는 경우)
if exist venv\Scripts\activate.bat (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 필요한 패키지 설치 확인
echo 패키지 확인 중...
pip install -q -r requirements.txt

echo.
echo 앱을 시작합니다...
echo 브라우저에서 http://localhost:8501 로 접속하세요
echo.

REM Streamlit 앱 실행
streamlit run apa_expert_app.py

pause
