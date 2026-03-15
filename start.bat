@echo off
chcp 65001 >nul
title Financial Data Analysis System
echo ==========================================
echo    金融数据分析与洗钱风险监测系统
echo ==========================================
echo.

:: Get the directory where this batch file is located and convert to short path name
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%") do set "SHORT_DIR=%%~sI"
set "HOU_DIR=%SHORT_DIR%hou"

echo [INFO] 项目目录：%SCRIPT_DIR%
echo [INFO] 后端目录：%HOU_DIR%
echo.

:: Check if Python is installed
echo [STEP 1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未检测到 Python 环境！
    echo [INFO] 请先安装 Python 3.8 或更高版本，并添加到系统 PATH
    echo [INFO] 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python 已安装：%PYTHON_VERSION%
echo.

:: Check and install required packages
echo [STEP 2/3] 检查和安装依赖包...
if exist "%HOU_DIR%\requirements.txt" (
    echo [INFO] 发现 requirements.txt，开始检查依赖...
    
    :: Try to import all required packages
    python -c "import flask, flask_cors, pandas, numpy, openpyxl" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] 检测到缺少依赖包，正在自动安装...
        echo [INFO] 使用 pip 安装 requirements.txt 中的依赖...
        echo.
        
        :: Upgrade pip first
        echo [INFO] 升级 pip 到最新版本...
        python -m pip install --upgrade pip --quiet
        
        :: Install from requirements.txt
        echo [INFO] 安装依赖包...
        pip install -r "%HOU_DIR%\requirements.txt"
        
        if errorlevel 1 (
            echo [ERROR] 依赖包安装失败！
            echo [INFO] 请尝试手动运行以下命令：
            echo   pip install -r "%HOU_DIR%\requirements.txt"
            echo.
            pause
            exit /b 1
        )
        
        echo [OK] 所有依赖包安装成功！
    ) else (
        echo [OK] 所有依赖包已安装，无需重复安装
    )
) else (
    echo [WARNING] 未发现 requirements.txt 文件
    echo [INFO] 尝试使用默认依赖列表安装...
    
    python -c "import flask, flask_cors, pandas, numpy, openpyxl" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] 检测到缺少依赖包，正在安装...
        pip install flask flask-cors pandas numpy openpyxl
        
        if errorlevel 1 (
            echo [ERROR] 依赖包安装失败！
            echo [INFO] 请手动运行：pip install flask flask-cors pandas numpy openpyxl
            pause
            exit /b 1
        )
        
        echo [OK] 依赖包安装成功！
    ) else (
        echo [OK] 依赖包检查通过
    )
)
echo.

echo [STEP 3/3] 启动 Flask 后端服务...
echo [INFO] 服务地址：http://localhost:5000
echo [INFO] 浏览器将在 3 秒后自动打开...
echo.

:: Verify hou directory exists
if not exist "%HOU_DIR%" (
    echo [ERROR] 目录不存在：%HOU_DIR%
    echo [INFO] 请确保项目结构正确：
    echo   - start.bat 应在项目根目录
    echo   - hou\app.py 应存在
    pause
    exit /b 1
)

:: Change to hou directory
cd /d %HOU_DIR%

:: Verify app.py exists
if not exist "app.py" (
    echo [ERROR] app.py 未找到：%CD%
    echo [INFO] 当前目录内容:
    dir
    pause
    exit /b 1
)

:: Start Flask and open browser after 3 seconds
set "QIAN_DIR=%SCRIPT_DIR%qian"
:: Convert backslashes to forward slashes for file URI
set "QIAN_DIR_URI=%QIAN_DIR:\=/%
start /b cmd /c "timeout /t 3 /nobreak >nul && start file:///%QIAN_DIR_URI%/index.html"

:: Run Flask (this will block until Ctrl+C)
python app.py

echo.
echo [INFO] Server stopped.
pause
