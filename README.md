# ComfyUI Google Drive 上传自定义节点

## 一、仓库概述
本仓库包含为ComfyUI定制的自定义节点，可实现将ComfyUI生成的图片和视频实时上传至Google Drive。此外，还提供了一个带图片预览功能的上传节点，方便用户在上传前确认图片内容。

## 二、功能特点
1. **图片上传**：将ComfyUI生成的图片上传至Google Drive指定文件夹。
2. **视频上传**：把ComfyUI生成的视频帧序列转换为MP4格式并上传至Google Drive。
3. **图片预览**：带预览功能的图片上传节点，可在ComfyUI界面中预览图片后再上传。
4. **自动安装**：提供初始化脚本，方便用户克隆仓库后一键安装依赖。

## 三、安装指南
### （一）前提条件
1. 已安装ComfyUI。确保ComfyUI运行环境配置正确，包括Python环境及相关依赖。
2. 拥有Google Cloud Console账号，并已启用Google Drive API，且下载了`client_secret.json`凭证文件。

### （二）克隆仓库
1. **Linux/MacOS**：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ches2010/comfyui-googledrive-upload.git
```
2. **Windows**：
```batch
cd ComfyUI\custom_nodes
git clone https://github.com/ches2010/comfyui-googledrive-upload.git
```

### （三）安装依赖
1. **通过初始化脚本（推荐）**：
    - **Linux/MacOS**：
      - 进入克隆的仓库目录：
```bash
cd <your - repository - directory>
```
      - 运行初始化脚本：
```bash
./install_dependencies.sh
```
    - **Windows**：
      - 进入克隆的仓库目录：
```batch
cd <your - repository - directory>
```
      - 运行初始化脚本：
```batch
install_dependencies.bat
```
    初始化脚本会自动检测是否在ComfyUI的`custom_nodes`目录下，并安装`requirements.txt`中列出的依赖。

2. **手动安装**：
    - 进入克隆的仓库目录。
    - 运行命令安装依赖：
```bash
pip install -r requirements.txt
```

## 四、使用说明
### （一）Google Drive授权配置
1. 前往 [Google Cloud Console](https://console.cloud.google.com/) 创建项目。
2. 启用「Google Drive API」。
3. 创建「OAuth客户端ID」，下载凭证文件（`client_secret.json`）。
4. 将 `client_secret.json` 放在ComfyUI的根目录（或节点所在目录）。首次使用节点时，会自动引导用户在浏览器中完成授权，后续无需重复操作。

### （二）节点使用
1. **Google Drive Image Upload**：
    - **输入**：连接ComfyUI图片生成节点的输出到该节点的`image`输入端口，可选择填写`folder_id`（Google Drive目标文件夹ID）和`file_name`（上传的文件名）。
    - **输出**：`status`输出端口返回上传结果状态。
2. **Google Drive Video Upload**：
    - **输入**：连接ComfyUI视频生成节点输出的视频帧序列到`video_frames`输入端口，设置`fps`（视频帧率），可选择填写`folder_id`和`file_name`。
    - **输出**：`status`输出端口返回上传结果状态。
3. **Google Drive Image Upload (with Preview)**：
    - **输入**：连接ComfyUI图片生成节点的输出到该节点的`image`输入端口，可选择填写`folder_id`和`file_name`。
    - **输出**：`preview_image`输出端口可连接到ComfyUI的预览窗口或其他需要图片输入的节点，用于预览图片；`status`输出端口返回上传结果状态。

## 五、初始化脚本说明
### （一）`install_dependencies.sh`（Linux/MacOS）
该脚本用于自动检测ComfyUI根目录，并安装本仓库所需的Python依赖。脚本内容如下：
```bash
#!/bin/bash

# 检查是否在ComfyUI的custom_nodes目录下
if [ -d "../../ComfyUI" ]; then
    echo "Detected ComfyUI root directory."
else
    echo "Please run this script from within the custom_nodes sub - directory of ComfyUI."
    exit 1
fi

# 安装Python依赖
pip install -r requirements.txt

echo "Dependencies installed successfully. You can now start ComfyUI."
```
运行前需确保脚本有可执行权限：
```bash
chmod +x install_dependencies.sh
```

### （二）`install_dependencies.bat`（Windows）
此批处理脚本功能与Linux/MacOS版本类似，用于在Windows系统下自动安装依赖：
```batch
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
```

## 六、注意事项
1. **凭证安全**：`client_secret.json`是用户个人的密钥，请勿上传到公共仓库，避免安全风险。
2. **权限范围**：本节点仅请求`drive.file`权限，仅能操作通过该应用上传的文件，避免过度授权。
3. **错误处理**：若出现网络问题或凭证过期等情况，节点会返回错误信息，用户可根据信息排查问题。
4. **版本兼容**：确保ComfyUI版本与本仓库的节点兼容，若ComfyUI版本更新导致节点无法使用，请关注仓库更新或提交issue。
