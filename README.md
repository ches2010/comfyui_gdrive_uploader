# ComfyUI Google Drive 上传自定义节点

## 一、仓库概述
本仓库包含为ComfyUI定制的自定义节点，可实现将ComfyUI生成的图片和视频实时上传至Google Drive。此外，还提供了一个带图片预览功能的上传节点，方便用户在上传前确认图片内容。

## 二、功能特点
1. **图片上传**：将ComfyUI生成的图片上传至Google Drive指定文件夹。
2. **视频上传**：把ComfyUI生成的视频帧序列转换为MP4格式并上传至Google Drive。
3. **图片预览**：带预览功能的图片上传节点，可在ComfyUI界面中预览图片后再上传。
4. **自动安装**：提供初始化脚本，方便用户克隆仓库后一键安装依赖。
5. ✅ 将生成的图片实时发布到 **Telegram 群组**  
   ✅ 在节点 UI 中 **预览图片**（和默认 SaveImage 节点一致）  
   ✅ 支持自定义消息文本（可带变量）  
   ✅ 错误处理 + 日志提示  

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

## OneDrive 上传节点 (OneDrive Uploader Node)

此节点允许将图像直接上传到 Microsoft OneDrive，并在 ComfyUI 内提供实时预览。

### 先决条件 (Prerequisites)

1.  **在 Azure AD 中注册应用 (Register an App in Azure AD):**
    *   访问 [Azure 门户](https://portal.azure.com/)。
    *   导航到 "Azure Active Directory" -> "应用注册" -> "新注册"。
    *   为您的应用命名（例如，`ComfyUI OneDrive Uploader`）。
    *   对于受支持的帐户类型，选择 "任何组织目录(任何 Azure AD 目录 - 多租户)和个人 Microsoft 帐户(例如 Skype, Xbox)"。
    *   对于重定向 URI，选择 "公共客户端/移动和桌面应用" 并输入 `http://localhost:8080` (或者您喜欢的其他本地主机 URI，但需要相应地更新节点代码中的 `REDIRECT_URI`)。
    *   点击 "注册"。
2.  **配置应用权限 (Configure App Permissions):**
    *   转到您新创建的应用页面。
    *   在 "管理" 下，点击 "API 权限" -> "添加权限" -> "Microsoft Graph" -> "委派的权限"。
    *   搜索并添加以下权限：
        *   `Files.ReadWrite.All` (读写用户的所有文件)
        *   `offline_access` (获取刷新令牌，对于长时间运行或需要重新授权的任务至关重要)
    *   点击 "添加权限"。
    *   如果您的帐户需要管理员同意，您可能需要管理员为 `Files.ReadWrite.All` 授权。对于个人 Microsoft 帐户，您通常可以在稍后自行同意。
3.  **获取客户端 ID 和 (可选) 客户端密码 (Get Client ID and (Optional) Client Secret):**
    *   在 "管理" 下，点击 "概述"。复制 "应用程序(客户端) ID"。这就是您的 `CLIENT_ID`。
    *   **(可选但推荐，用于更好的安全性)** 在 "管理" 下，点击 "证书和密码" -> "客户端密码" -> "新建客户端密码"。创建一个密码并复制其值。这就是您的 `CLIENT_SECRET`。

### 配置 (Configuration)

您需要提供 `CLIENT_ID` 和 `CLIENT_SECRET`。推荐使用配置文件。

**方法 1: 使用配置文件 (推荐) (Method 1: Using Config File (Recommended))**
*   在节点目录下找到 `config.json` 文件。
*   用文本编辑器打开它。
*   将 `"YOUR_ONEDRIVE_APP_CLIENT_ID"` 和 `"YOUR_ONEDRIVE_APP_CLIENT_SECRET"` 替换为您在 Azure 门户上获得的实际值。
*   保存文件并重启 ComfyUI。

    ```json
    {
        "onedrive": {
            "client_id": "your_actual_client_id_here",
            "client_secret": "your_actual_client_secret_here"
        }
    }
    ```

**方法 2: 环境变量 (Method 2: Environment Variables)**
*   (仍然支持) 设置环境变量 `ONEDRIVE_CLIENT_ID` 和 `ONEDRIVE_CLIENT_SECRET`。
*   重启 ComfyUI。

**方法 3: 硬编码 (不推荐) (Method 3: Hardcode (Not Recommended))**
*   *此方法已不推荐，使用 `config.json` 更好。*

### 初始认证 (Initial Authentication)

首次使用节点上传文件前，您需要进行一次认证以获取访问令牌。

1.  将 "Upload to OneDrive" 节点添加到您的工作流中。
2.  勾选节点上的 `authenticate` (认证) 布尔输入框。
3.  运行工作流。
4.  ComfyUI 的控制台/日志将显示一条消息，其中包含一个 URL 和一个代码。
5.  在您的浏览器中打开该 URL 并输入代码。
6.  登录您的 Microsoft 帐户并授予所请求的权限。
7.  节点将自动接收令牌并将其保存在本地 (`onedrive_token.json`，位于节点目录下)。
8.  **后续运行时，请取消勾选 `authenticate` 框。**

### 使用方法 (Usage)

1.  将图像输出连接到 `images` 输入。
2.  如果需要，可以设置 `filename_prefix` (文件名前缀)。
3.  指定 `onedrive_folder_path` (OneDrive 文件夹路径，例如 `/MyFolder` 或 `/MyFolder/SubFolder`)。如果该文件夹在根目录下不存在，节点会尝试创建它。
4.  确保 `authenticate` (认证) 框 **未被勾选**。
5.  运行工作流。图像应该会出现在节点的预览窗口中，并且会被上传到您的 OneDrive。


## 六、注意事项
1. **凭证安全**：`client_secret.json`是用户个人的密钥，请勿上传到公共仓库，避免安全风险。
2. **权限范围**：本节点仅请求`drive.file`权限，仅能操作通过该应用上传的文件，避免过度授权。
3. **错误处理**：若出现网络问题或凭证过期等情况，节点会返回错误信息，用户可根据信息排查问题。
4. **版本兼容**：确保ComfyUI版本与本仓库的节点兼容，若ComfyUI版本更新导致节点无法使用，请关注仓库更新或提交issue。
