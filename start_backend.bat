@echo off
echo =========================================
echo  Starting DeepShield AI Backend...
echo =========================================

echo Activating Python Virtual Environment...
call .venv\Scripts\activate

echo Starting Uvicorn Server...
uvicorn main:app --reload

pause
