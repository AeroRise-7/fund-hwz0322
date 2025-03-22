@echo off
chcp 65001 >nul
echo ===================================
echo    基金管理分析工具 - 依赖安装程序
echo ===================================
echo.

echo 正在检查Python环境...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python环境，请安装Python 3.8或更高版本。
    echo 您可以从 https://www.python.org/downloads/ 下载安装。
    pause
    exit /b 1
)

echo 尝试方法1：安装预编译的二进制包...
pip install --only-binary=:all: -r requirements.txt

if %errorlevel% neq 0 (
    echo 方法1失败，尝试方法2：单独安装每个包...
    
    echo 安装numpy...
    pip install numpy==1.24.3 --only-binary=:all:
    
    echo 安装pandas...
    pip install pandas==1.5.3 --only-binary=:all:
    
    echo 安装其他依赖...
    pip install streamlit==1.31.1 plotly==5.18.0 requests==2.31.0 python-dateutil==2.8.2 beautifulsoup4==4.12.2 tqdm==4.66.1 lxml==4.9.3
    
    if %errorlevel% neq 0 (
        echo [警告] 依赖安装可能不完整。
        echo 请尝试手动安装Wheel文件，可以从 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 下载适合您系统的预编译包。
        pause
    ) else (
        echo 依赖安装完成！
    )
) else (
    echo 所有依赖安装成功！
)

echo.
echo 现在可以尝试运行start.bat启动程序了。
pause 