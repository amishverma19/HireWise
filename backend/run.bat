@echo off
set "PYTHON_PATH=C:\Users\Acer\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if exist "%PYTHON_PATH%" (
    "%PYTHON_PATH%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)
pause

