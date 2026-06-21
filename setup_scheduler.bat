@echo off
chcp 65001 > nul
echo.
echo ================================================
echo  저평가 레이더 - Windows 작업 스케줄러 등록
echo ================================================
echo.

:: Python 경로 자동 탐지
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set PYTHON_PATH=%%i
    goto :found_python
)
echo [오류] Python을 찾을 수 없습니다. PATH를 확인해주세요.
pause
exit /b 1

:found_python
echo Python 경로: %PYTHON_PATH%

:: 스크립트 경로 (이 .bat 파일 기준)
set SCRIPT=%~dp0backend\collect.py
echo 스크립트: %SCRIPT%
echo.

:: 기존 작업 삭제 (재등록 시 오류 방지)
schtasks /delete /tn "InvestDash_NASDAQ" /f > nul 2>&1
schtasks /delete /tn "InvestDash_KOSPI" /f > nul 2>&1

:: 나스닥: 매일 오전 7시 (미국 장 마감 후 → 전일 종가 확정)
schtasks /create ^
  /tn "InvestDash_NASDAQ" ^
  /tr "cmd /c \"%PYTHON_PATH%\" \"%SCRIPT%\" --market nasdaq >> \"%~dp0backend\collect.log\" 2>&1" ^
  /sc daily /st 07:00 ^
  /ru "%USERNAME%" ^
  /f > nul

if %ERRORLEVEL% == 0 (
    echo [OK] 나스닥 수집: 매일 오전 07:00 등록 완료
) else (
    echo [오류] 나스닥 작업 등록 실패
)

:: 코스피: 매일 오후 4시 (한국 장 마감 30분 후)
schtasks /create ^
  /tn "InvestDash_KOSPI" ^
  /tr "cmd /c \"%PYTHON_PATH%\" \"%SCRIPT%\" --market kospi >> \"%~dp0backend\collect.log\" 2>&1" ^
  /sc daily /st 16:00 ^
  /ru "%USERNAME%" ^
  /f > nul

if %ERRORLEVEL% == 0 (
    echo [OK] 코스피 수집: 매일 오후 04:00 등록 완료
) else (
    echo [오류] 코스피 작업 등록 실패
)

echo.
echo 등록된 작업 확인:
schtasks /query /tn "InvestDash_NASDAQ" /fo list 2>nul | findstr "작업 이름\|다음 실행"
schtasks /query /tn "InvestDash_KOSPI" /fo list 2>nul | findstr "작업 이름\|다음 실행"

echo.
echo 수동 테스트 실행:
echo   python backend\collect.py --market nasdaq
echo   python backend\collect.py --market kospi
echo.
pause
