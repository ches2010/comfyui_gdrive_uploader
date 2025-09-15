import os
import folder_paths
import numpy as np
from PIL import Image
import torch

# Google Drive API libraries
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging
import json

# --- Configuration ---
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "service_account_key.json")
SCOPES = ['https://www.googleapis.com/auth/drive.file']  # Only file access
DEFAULT_FOLDER_ID = None  # Set to folder ID string if needed

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global Variables for Google Drive Auth ---
service = None
GDRIVE_AUTH_FAILED = False

# --- Initialize Google Drive Service (at module load) ---
try:
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account key file not found at {SERVICE_ACCOUNT_FILE}. Please download it from Google Cloud Console.")

    with open(SERVICE_ACCOUNT_FILE, 'r') as f:
        key_data = json.load(f)
        required_fields = ['type', 'client_email', 'token_uri', 'private_key']
        missing_fields = [field for field in required_fields if field not in key_data]
        if missing_fields:
            raise ValueError(f"Service account key is invalid. Missing fields: {missing_fields}")

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    logger.info("✅ Google Drive API authenticated successfully.")

except Exception as e:
    logger.error(f"❌ Failed to initialize Google Drive API: {e}")
    GDRIVE_AUTH_FAILED = True


class ComfyUIGDriveUploader:
    """
    A ComfyUI node to upload images to Google Drive.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": "GDriveUpload"}),
                "gdrive_folder_id": ("STRING", {"default": DEFAULT_FOLDER_ID or ""}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "upload"
    OUTPUT_NODE = True
    CATEGORY = "image/upload"

    def upload(self, images, filename_prefix="GDriveUpload", gdrive_folder_id="", prompt=None, extra_pnginfo=None):
        """
        Uploads images to Google Drive.
        """
        logger.info("Starting Google Drive upload process...")

        # ✅ 检查 Google Drive 是否准备好
        if GDRIVE_AUTH_FAILED or service is None:
            logger.error("🛑 Google Drive authentication failed or not initialized. Check 'service_account_key.json' and logs.")
            return { "ui": { "images": [] } }

        # ✅ 动态导入 PngInfo（避免顶层导入问题）
        try:
            from PIL.PngImagePlugin import PngInfo
            disable_metadata = False
        except ImportError:
            logger.warning("PIL PngInfo not available. Metadata will not be saved.")
            PngInfo = None
            disable_metadata = True

        results = []

        for batch_number, image in enumerate(images):
            # Convert tensor to PIL Image
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Prepare metadata
            metadata = None
            if not disable_metadata and PngInfo:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # Generate filename
            filename_with_batch_num = filename_prefix.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{batch_number:05}.png"
            local_file_path = os.path.join(self.output_dir, file)

            # Save locally
            img.save(local_file_path, pnginfo=metadata, compress_level=self.compress_level)
            logger.info(f"💾 Saved temporary image: {local_file_path}")

            # Upload to Google Drive
            try:
                file_metadata = {'name': file}
                if gdrive_folder_id:
                    file_metadata['parents'] = [gdrive_folder_id]

                media = MediaFileUpload(local_file_path, mimetype='image/png')
                uploaded_file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

                file_id = uploaded_file.get('id')
                logger.info(f"☁️ Uploaded successfully. File ID: {file_id}")

                # Optional: Make file public (uncomment if needed + adjust scope)
                # service.permissions().create(
                #     fileId=file_id,
                #     body={"role": "reader", "type": "anyone"}
                # ).execute()
                # logger.info(f"🌐 File {file_id} is now publicly readable.")

                results.append({
                    "filename": file,
                    "subfolder": "",
                    "type": self.type
                })

                # Optional: Clean up local file
                # os.remove(local_file_path)
                # logger.info(f"🗑️ Deleted local file: {local_file_path}")

            except Exception as upload_e:
                error_msg = f"❌ Failed to upload {file}: {upload_e}"
                logger.error(error_msg)
                results.append({
                    "filename": file + "_FAILED",
                    "subfolder": "",
                    "type": self.type
                })

        # Return UI update for ComfyUI frontend
        return { "ui": { "images": results } }


# --- Node Registration ---
NODE_CLASS_MAPPINGS = {
    "GDriveUploader": ComfyUIGDriveUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GDriveUploader": "📤 Upload to Google Drive"
}
