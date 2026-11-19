$pythonPath = "C:\Users\Acer\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if (Test-Path $pythonPath) {
    & $pythonPath -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} else {
    try {
        & $pythonPath -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    } catch {
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    }
}
