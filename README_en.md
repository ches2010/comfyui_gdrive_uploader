# ComfyUI Google Drive Uploader Node

This custom node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) allows you to automatically upload generated images directly to your Google Drive.

## Features

*   Uploads images generated in a ComfyUI workflow to Google Drive.
*   Supports uploading to a specific folder within your Google Drive.
*   Integrates seamlessly with ComfyUI Manager for easy one-click installation and dependency management.
*   Automatically installs required Python dependencies when cloned and loaded by ComfyUI.

## Installation

### Option 1: Using ComfyUI Manager (Recommended)

1.  Ensure you have [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager) installed.
2.  Open ComfyUI Manager within ComfyUI.
3.  Search for "Google Drive Uploader" or navigate to the "Install Custom Nodes" section.
4.  Find this node and click "Install".
5.  Restart ComfyUI if prompted. The node should automatically install the necessary Python packages.

### Option 2: Manual Installation (`git clone`)

1.  Navigate to your ComfyUI `custom_nodes` directory.
    ```bash
    cd path/to/ComfyUI/custom_nodes
    ```
2.  Clone this repository:
    ```bash
    git clone https://github.com/yourusername/comfyui_gdrive_uploader.git
    ```
3.  **Set up Google Drive API Access (Crucial Step):**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Enable the Google Drive API for your project.
    *   Go to "Credentials".
    *   Click "Create Credentials" -> "Service Account".
    *   Follow the prompts to create a service account. You don't need to grant it specific roles for this basic upload access.
    *   Once created, click on the service account email.
    *   Go to the "Keys" tab.
    *   Click "Add Key" -> "Create new key".
    *   Select "JSON" as the key type and click "Create". This will download a `.json` file.
    *   **Rename the downloaded `.json` file to `service_account_key.json`.**
    *   **Place the `service_account_key.json` file inside the `comfyui_gdrive_uploader` directory** (the same folder as this `README.md`).
        **Security Note:** Keep this file secure and do not share it publicly.
4.  (Optional but Recommended) Restart ComfyUI. The node's `__init__.py` script should automatically detect and install the required Python dependencies (`google-api-python-client`, etc.) if they are missing. If it fails or you prefer manual control, you can install them yourself:
    ```bash
    # Navigate to the node directory
    cd comfyui_gdrive_uploader
    # Install dependencies using the same Python environment as ComfyUI
    pip install -r requirements.txt
    ```
5.  Start ComfyUI. The node should now be available.

## Usage

1.  In your ComfyUI workflow, add the "Upload to Google Drive" node (found under `image/upload` category).
2.  Connect an image output from another node to the `images` input of this node.
3.  (Optional) Specify a `filename_prefix`.
4.  (Optional) To upload to a specific folder:
    *   Go to your Google Drive in a web browser.
    *   Navigate to the desired folder.
    *   Copy the folder ID from the URL. It's the long string after `folders/`.
    *   Paste this ID into the `gdrive_folder_id` input field of the node.
5.  Run your workflow. The generated images should be saved locally (in your ComfyUI output directory) and simultaneously uploaded to your Google Drive.

## Configuration

*   **Service Account Key:** The `service_account_key.json` file is mandatory and must be placed in the node's directory.
*   **Default Folder:** You can set a default Google Drive folder ID by modifying the `DEFAULT_FOLDER_ID` variable in `gdrive_uploader_node.py`.
*   **Scopes:** The default scope `https://www.googleapis.com/auth/drive.file` allows the service account to manage files it creates. If you need broader access (e.g., to upload to *any* folder regardless of ownership), you might need to adjust the `SCOPES` list in `gdrive_uploader_node.py` and ensure your service account has the correct permissions, but this is generally not recommended for security.

## OneDrive Uploader Node

This node allows uploading images directly to Microsoft OneDrive and provides a live preview within ComfyUI.

### Prerequisites

1.  **Register an App in Azure AD:**
    *   Go to the [Azure Portal](https://portal.azure.com/).
    *   Navigate to "Azure Active Directory" -> "App registrations" -> "New registration".
    *   Give your app a name (e.g., `ComfyUI OneDrive Uploader`).
    *   Select "Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)" for supported account types.
    *   For Redirect URI, select "Public client/native (mobile & desktop)" and enter `http://localhost:8080` (or another localhost URI you prefer, but update `REDIRECT_URI` in the node code accordingly).
    *   Click "Register".
2.  **Configure App Permissions:**
    *   Go to your newly created app's page.
    *   Under "Manage", click "API permissions" -> "Add a permission" -> "Microsoft Graph" -> "Delegated permissions".
    *   Search for and add:
        *   `Files.ReadWrite.All`
        *   `offline_access` (Essential for refresh tokens)
    *   Click "Add permissions".
    *   You might need an admin to grant consent for `Files.ReadWrite.All` if your account requires it. For personal accounts, you can usually consent yourself later.
3.  **Get Client ID and (Optional) Client Secret:**
    *   Under "Manage", click "Overview". Copy the "Application (client) ID". This is your `CLIENT_ID`.
    *   (Optional but Recommended for better security) Under "Manage", click "Certificates & secrets" -> "Client secrets" -> "New client secret". Create a secret and copy its value. This is your `CLIENT_SECRET`.

### Configuration

You need to provide the `CLIENT_ID` and optionally `CLIENT_SECRET`.

**Method 1: Environment Variables (Recommended)**
*   Set the following environment variables before starting ComfyUI:
    ```bash
    export ONEDRIVE_CLIENT_ID=your_application_client_id_here
    export ONEDRIVE_CLIENT_SECRET=your_application_client_secret_here # Optional
    ```
*   Restart ComfyUI.

**Method 2: Hardcode (Less Secure)**
*   Open `onedrive_uploader_node.py`.
*   Find the lines:
    ```python
    CLIENT_ID = os.environ.get("ONEDRIVE_CLIENT_ID", "YOUR_ONEDRIVE_APP_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("ONEDRIVE_CLIENT_SECRET", "YOUR_ONEDRIVE_APP_CLIENT_SECRET")
    ```
*   Replace `"YOUR_ONEDRIVE_APP_CLIENT_ID"` and `"YOUR_ONEDRIVE_APP_CLIENT_SECRET"` with your actual values.
*   Save the file and restart ComfyUI.

### Initial Authentication

1.  Add the "Upload to OneDrive" node to your workflow.
2.  Check the `authenticate` boolean input box on the node.
3.  Run the workflow.
4.  The ComfyUI console/log will display a message with a URL and a code.
5.  Open the URL in your browser and enter the code.
6.  Sign in to your Microsoft account and grant the requested permissions.
7.  The node will automatically receive the tokens and save them locally (`onedrive_token.json` in the node's directory).
8.  Uncheck the `authenticate` box for subsequent runs.

### Usage

1.  Connect an image output to the `images` input.
2.  Set a `filename_prefix` if desired.
3.  Specify the `onedrive_folder_path` (e.g., `/MyFolder` or `/MyFolder/SubFolder`). The node will attempt to create the folder if it doesn't exist under the root.
4.  Ensure the `authenticate` box is **unchecked**.
5.  Run the workflow. The image should appear in the node's preview window and be uploaded to your OneDrive.

---

## 🆕 New: Telegram Image Poster Node

Automatically post generated images to your Telegram group/channel!

### 🔧 Setup

1. Create a bot via `@BotFather` on Telegram to get a `bot_token`
2. Get your `chat_id` (group or private chat) via `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Edit `config.json` in this folder:

```json
{
  "onedrive": {
    "client_id": "your-onedrive-client-id",
    "client_secret": ""
  },
  "telegram": {
    "bot_token": "your-telegram-bot-token",
    "chat_id": "your-chat-id"
  }
}
```

💡 Get Telegram bot_token from @BotFather, and chat_id via https://api.telegram.org/bot<TOKEN>/getUpdates

---

## ✅ 重启 ComfyUI 测试

1. 保存所有文件
2. 重启 ComfyUI
3. 拖入 `📤 Post Image to Telegram` 节点
4. 运行工作流 → 图片应正常发送到 Telegram + 本地预览

---

Install dependency:
```bash
pip install python-telegram-bot
```
Restart ComfyUI → Search node: 📤 Post Image to Telegram

## Troubleshooting

*   **Dependencies not installing:** Ensure ComfyUI is run with the correct Python environment. Check ComfyUI logs for errors during startup related to dependency installation.
*   **Authentication Error:** Double-check the path and validity of your `service_account_key.json` file.
*   **Upload Failures:** Verify the service account has write permissions to the specified Google Drive folder (or the root if no folder is specified). The service account effectively "owns" the files it uploads.
*   **Node not appearing:** Ensure the node was installed correctly and ComfyUI was restarted.

## Disclaimer

This node interacts with external services (Google Drive). Please ensure you understand the implications of granting access and storing your service account key securely. The author is not responsible for any issues arising from the use of this node.
