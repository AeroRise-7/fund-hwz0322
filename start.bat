@echo off
rem 先设置代码页为UTF-8
chcp 65001 >nul

echo ===================================
echo    基金管理分析工具 - 启动程序
echo ===================================
echo.

echo 正在检查Python环境...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python未安装，请安装Python 3.8或更高版本。
    echo 您可以从 https://www.python.org/downloads/ 下载安装。
    pause
    exit /b 1
)

echo 正在尝试启动基金分析工具...
echo 请稍候，应用程序窗口即将打开...
echo.

streamlit run main.py
if %errorlevel% neq 0 (
    echo 程序启动失败，尝试安装依赖...
    
    pip install -r requirements.txt
    
    if %errorlevel% neq 0 (
        echo 依赖安装失败，请手动执行: pip install -r requirements.txt
    ) else (
        echo 依赖安装完成！尝试再次启动程序...
        streamlit run main.py
    )
)

echo.
echo 按任意键退出...
pause >nul 