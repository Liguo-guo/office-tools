@echo off
chcp 65001 >nul
echo ========================================
echo 番茄计时器 - 打包程序
echo ========================================
echo.

echo [1/3] 检查PyInstaller是否已安装...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo 安装失败！请检查网络连接或手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller已安装
)
echo.

echo [2/3] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist *.spec del /q *.spec
echo.

echo [3/3] 开始打包程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --name=番茄计时器 ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --hidden-import=win32timezone ^
    --hidden-import=win32api ^
    --hidden-import=win32con ^
    --hidden-import=win32gui ^
    --collect-all=win10toast ^
    pomodoro_timer.py

if errorlevel 1 (
    echo.
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\番茄计时器.exe
echo.
echo 你可以将 dist\番茄计时器.exe 复制到任何Windows电脑上使用
echo 不需要安装Python环境！
echo.
pause

