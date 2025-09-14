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

# --- Configuration ---
# Path to your Service Account JSON key file
# This should be placed securely, e.g., in the node's directory or specified via an environment variable
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "service_account_key.json")
# Scopes required for the operation
SCOPES = ['https://www.googleapis.com/auth/drive.file'] # Only file access for drive
# Default folder ID (optional, if you want to upload to a specific folder)
DEFAULT_FOLDER_ID = None # e.g., 'your_folder_id_here' or leave as None for root

# --- Logging ---
logging.basicConfig(level=logging.INFO) # Change to WARNING or ERROR in production
logger = logging.getLogger(__name__)

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
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": "GDriveUpload"}),
                "gdrive_folder_id": ("STRING", {"default": DEFAULT_FOLDER_ID or ""}), # Optional folder ID input
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
        Args:
            images: Tensor of images from ComfyUI.
            filename_prefix: Prefix for the uploaded filenames.
            gdrive_folder_id: (Optional) Google Drive folder ID to upload to.
            prompt: (Hidden) The prompt used to generate the image.
            extra_pnginfo: (Hidden) Extra PNG info.
        """
        logger.info("Starting Google Drive upload process...")

        # --- Authenticate and build the service ---
        try:
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                 error_msg = f"Service account key file not found at {SERVICE_ACCOUNT_FILE}. Please ensure the file exists and the path is correct."
                 logger.error(error_msg)
                 # In a real node, you might want to raise an exception or return an error status
                 # that ComfyUI can display. For now, we'll just log it.
                 return { "ui": { "images": [] } } # Return empty to avoid breaking the workflow

            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('drive', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Drive API.")
        except Exception as e:
             error_msg = f"Failed to authenticate with Google Drive API: {e}"
             logger.error(error_msg)
             return { "ui": { "images": [] } }

        # --- Process and Upload Images ---
        results = []
        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
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

            # Save locally first (optional, but good practice)
            img.save(local_file_path, pnginfo=metadata, compress_level=self.compress_level)
            logger.info(f"Saved temporary image locally: {local_file_path}")

            # --- Upload to Google Drive ---
            try:
                file_metadata = {'name': file}
                if gdrive_folder_id:
                    file_metadata['parents'] = [gdrive_folder_id]

                media = MediaFileUpload(local_file_path, mimetype='image/png')
                uploaded_file = service.files().create(body=file_metadata,
                                                       media_body=media,
                                                       fields='id').execute()
                file_id = uploaded_file.get('id')
                logger.info(f'Image uploaded successfully. File ID: {file_id}')

                # Optional: Make the file publicly accessible (requires different scope or ownership)
                # Uncomment the lines below if you add the 'https://www.googleapis.com/auth/drive' scope
                # and the service account has the necessary permissions on the folder.
                # try:
                #     service.permissions().create(
                #         fileId=file_id,
                #         body={"role": "reader", "type": "anyone"}
                #     ).execute()
                #     logger.info(f"Made file {file_id} publicly readable.")
                # except Exception as perm_e:
                #     logger.warning(f"Could not make file public: {perm_e}")

                results.append({
                    "filename": file,
                    "subfolder": "",
                    "type": self.type
                })

                # Optional: Delete the local temporary file after upload
                # os.remove(local_file_path)
                # logger.info(f"Deleted temporary local file: {local_file_path}")

            except Exception as upload_e:
                error_msg = f"Failed to upload image {file}: {upload_e}"
                logger.error(error_msg)
                # Depending on requirements, you might want to continue with other images
                # or stop the process. Here, we log and continue.
                results.append({
                    "filename": file + "_FAILED",
                    "subfolder": "",
                    "type": self.type
                })
        # Return UI update info (standard for output nodes)
        return { "ui": { "images": results } }

# Import necessary modules for saving PNG with metadata (if needed)
import json
try:
    from PIL.PngImagePlugin import PngInfo
    args = type('obj', (object,), {'disable_metadata': False})() # Mock args object
except ImportError:
    logger.warning("PIL PngInfo not available, metadata will not be saved.")
    PngInfo = None
    args = type('obj', (object,), {'disable_metadata': True})()

# Node Registration
NODE_CLASS_MAPPINGS = {
    "GDriveUploader": ComfyUIGDriveUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GDriveUploader": "Upload to Google Drive"
}
