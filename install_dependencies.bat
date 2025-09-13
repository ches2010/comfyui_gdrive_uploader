@echo off

REM 检查是否在ComfyUI的custom_nodes目录下
if exist "..\..\ComfyUI" (
    echo Detected ComfyUI root directory.
) else (
    echo Please run this script from within the custom_nodes sub - directory of ComfyUI.
    pause
    exit /b 1
)

REM 安装Python依赖
pip install -r requirements.txt

echo Dependencies installed successfully. You can now start ComfyUI.
pause
