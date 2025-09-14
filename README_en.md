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

## Troubleshooting

*   **Dependencies not installing:** Ensure ComfyUI is run with the correct Python environment. Check ComfyUI logs for errors during startup related to dependency installation.
*   **Authentication Error:** Double-check the path and validity of your `service_account_key.json` file.
*   **Upload Failures:** Verify the service account has write permissions to the specified Google Drive folder (or the root if no folder is specified). The service account effectively "owns" the files it uploads.
*   **Node not appearing:** Ensure the node was installed correctly and ComfyUI was restarted.

## Disclaimer

This node interacts with external services (Google Drive). Please ensure you understand the implications of granting access and storing your service account key securely. The author is not responsible for any issues arising from the use of this node.
