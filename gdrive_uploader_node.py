import os
import folder_paths
import numpy as np
from PIL import Image
import torch
import json
import requests

# Google Drive API libraries
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request as GoogleAuthRequest
import logging

# --- Configuration ---
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "service_account_key.json")
PROXY_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "proxy_config.json")
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load Proxy Config (可运行时重载) ---
def load_proxy_config():
    if not os.path.exists(PROXY_CONFIG_FILE):
        logger.warning(f"Proxy config not found. Creating default at {PROXY_CONFIG_FILE}")
        default_config = {
            "http_proxy": "http://127.0.0.1:10808",
            "https_proxy": "http://127.0.0.1:10808",
            "enabled": False
        }
        with open(PROXY_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
    else:
        with open(PROXY_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

# --- Helper: Create Drive Service with optional proxy ---
def create_drive_service(use_proxy=False):
    """
    Dynamically create a Google Drive service instance.
    If use_proxy=True, inject proxy session.
    """
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError("Service account key file not found.")

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        if use_proxy:
            proxy_config = load_proxy_config()
            proxy = {
                'http': proxy_config.get("http_proxy", ""),
                'https': proxy_config.get("https_proxy", "")
            }
            session = requests.Session()
            session.proxies = proxy
            session.verify = True

            # 注入代理 session 到 credentials
            credentials._request = GoogleAuthRequest(session=session)
            credentials.refresh(GoogleAuthRequest(session=session))
            logger.info(f"🌐 Using proxy: {proxy}")

        # 构建服务（只传 credentials）
        service = build('drive', 'v3', credentials=credentials)
        return service

    except Exception as e:
        logger.error(f"❌ Failed to create Drive service: {e}")
        return None


class ComfyUIGDriveUploader:
    """
    A ComfyUI node to upload images to Google Drive with DYNAMIC proxy switching.
    No restart needed!
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
                "gdrive_folder_id": ("STRING", {"default": ""}),
            },
            "optional": {
                "use_proxy": ("BOOLEAN", {"default": False}),  # ← 动态开关！
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

    def upload(self, images, filename_prefix="GDriveUpload", gdrive_folder_id="", use_proxy=False, prompt=None, extra_pnginfo=None):
        """
        Uploads images to Google Drive — proxy setting is DYNAMIC per call.
        """
        logger.info(f"Starting Google Drive upload process... (Proxy: {'ON' if use_proxy else 'OFF'})")

        # ✅ 动态创建 service —— 每次上传独立决定是否走代理！
        service = create_drive_service(use_proxy=use_proxy)
        if not service:
            logger.error("🛑 Google Drive service creation failed. Aborting upload.")
            return { "ui": { "images": [] } }

        # 动态导入 PngInfo
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

                results.append({
                    "filename": file,
                    "subfolder": "",
                    "type": self.type
                })

            except Exception as upload_e:
                error_msg = f"❌ Failed to upload {file}: {upload_e}"
                logger.error(error_msg)
                results.append({
                    "filename": file + "_FAILED",
                    "subfolder": "",
                    "type": self.type
                })

        return { "ui": { "images": results } }


# --- Node Registration ---
NODE_CLASS_MAPPINGS = {
    "GDriveUploader": ComfyUIGDriveUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GDriveUploader": "🔄 Upload to Google Drive (Dynamic Proxy)"
}
