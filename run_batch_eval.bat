@echo off
REM Batch Evaluation Runner for Windows
echo ============================================================
echo BATCH EVALUATION - Research Paper Analyzer
echo ============================================================

cd /d "%~dp0"

REM Set LLM mode to DeepSeek via OpenRouter
set LLM_MODE=openrouter::deepseek/deepseek-chat-v3.1:free

REM Load API key from .env file if it exists
if exist .env (
    echo Loading environment from .env file...
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="OPENROUTER_API_KEY" set OPENROUTER_API_KEY=%%b
    )
)

if not defined OPENROUTER_API_KEY (
    echo ERROR: OPENROUTER_API_KEY not found!
    echo Please create a .env file with: OPENROUTER_API_KEY=your_key_here
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the batch evaluation script
echo.
echo Starting batch evaluation...
echo.
python batch_eval_runner.py

echo.
echo ============================================================
echo Evaluation complete. Check batch_eval_results folder.
echo ============================================================
pause
