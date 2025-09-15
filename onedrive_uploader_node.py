import os
import folder_paths
import numpy as np
from PIL import Image
import torch
import requests
import json
import logging
import time
import uuid # For generating unique filenames if needed

# --- Configuration ---
# These should ideally be configurable by the user or loaded from a secure config file/env
CLIENT_ID = os.environ.get("ONEDRIVE_CLIENT_ID", "YOUR_ONEDRIVE_APP_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ONEDRIVE_CLIENT_SECRET", "YOUR_ONEDRIVE_APP_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080" # Standard for device code flow example, adjust if needed

# Token file path (store securely, e.g., in user's home directory or node config)
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "onedrive_token.json")

# --- Logging ---
logging.basicConfig(level=logging.INFO) # Change to WARNING or ERROR in production
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def save_token(token_data):
    """Saves token data to a file."""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
        logger.info(f"Tokens saved to {TOKEN_FILE}")
    except Exception as e:
        logger.error(f"Failed to save tokens: {e}")

def load_token():
    """Loads token data from a file."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            logger.info(f"Tokens loaded from {TOKEN_FILE}")
            return token_data
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
    return None

def refresh_access_token(refresh_token):
    """Refreshes the access token using the refresh token."""
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()
        # Update the refresh token if a new one is provided
        if 'refresh_token' in token_data:
             # The new refresh token should be saved
             save_token(token_data)
        return token_data.get('access_token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to refresh access token: {e}")
        return None

def get_access_token():
    """Gets a valid access token, refreshing if necessary."""
    token_data = load_token()
    if not token_data:
        logger.error("No token found. Please initiate the authentication flow first.")
        return None

    access_token = token_data.get('access_token')
    expires_at = token_data.get('expires_at', 0)
    refresh_token = token_data.get('refresh_token')

    # Check if token is expired (with a small buffer)
    if time.time() > (expires_at - 300): # 5 minutes buffer
        if refresh_token:
            logger.info("Access token expired, refreshing...")
            access_token = refresh_access_token(refresh_token)
            if access_token:
                return access_token
            else:
                logger.error("Failed to refresh token.")
                return None
        else:
            logger.error("Token expired and no refresh token available.")
            return None
    return access_token

def initiate_auth_flow():
    """Initiates the device code flow for authentication."""
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
    data = {
        'client_id': CLIENT_ID,
        'scope': 'Files.ReadWrite.All offline_access' # offline_access is needed for refresh tokens
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        device_code_data = response.json()

        print("\n" + "="*50)
        print("OneDrive Authentication Required")
        print("="*50)
        print(f"1. Go to: {device_code_data['verification_uri']}")
        print(f"2. Enter the code: {device_code_data['user_code']}")
        print("3. Approve the request.")
        print("="*50 + "\n")

        # Poll for the token
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'device_code': device_code_data['device_code']
        }

        while True:
            token_response = requests.post(token_url, data=token_data)
            if token_response.status_code == 200:
                token_json = token_response.json()
                # Add expiration time
                token_json['expires_at'] = time.time() + token_json.get('expires_in', 3600)
                save_token(token_json)
                print("Authentication successful! Tokens saved.")
                return True
            elif token_response.status_code == 400:
                error = token_response.json().get('error')
                if error == 'authorization_pending':
                    # Wait before polling again
                    time.sleep(device_code_data.get('interval', 5))
                    continue
                elif error == 'slow_down':
                    # Server asked to slow down
                    time.sleep(device_code_data.get('interval', 5) + 5)
                    continue
                elif error == 'expired_token':
                    print("Authentication timed out. Please try again.")
                    return False
                elif error == 'authorization_declined':
                    print("Authorization was declined.")
                    return False
                else:
                    print(f"Authentication error: {error}")
                    return False
            else:
                print(f"Unexpected error during token polling: {token_response.status_code} - {token_response.text}")
                return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to initiate auth flow: {e}")
        return False

def upload_to_onedrive(file_path, access_token, folder_path="/ComfyUI Uploads"):
    """Uploads a file to OneDrive."""
    # 1. Get Drive Item ID for the target folder (or root if not specified)
    folder_id = "root" # Default to root
    if folder_path and folder_path != "/":
        # This is a simplified path resolution. For complex nested paths,
        # you'd need to iterate through each folder level.
        # We'll assume it's a direct child of root for simplicity here.
        # A more robust solution would parse the path and navigate.
        # For now, we'll just use the folder name as an item name under root.
        # This means it won't create nested folders automatically.
        folder_name = os.path.basename(folder_path.rstrip('/'))
        if folder_name:
             # Try to find the folder ID by name under root
             search_url = f"https://graph.microsoft.com/v1.0/me/drive/root/children"
             headers = {'Authorization': f'Bearer {access_token}'}
             try:
                 response = requests.get(search_url, headers=headers)
                 response.raise_for_status()
                 items = response.json().get('value', [])
                 for item in items:
                     if item.get('name') == folder_name and item.get('folder'):
                         folder_id = item['id']
                         logger.info(f"Found folder '{folder_name}' with ID: {folder_id}")
                         break
                 else:
                     # Folder not found, create it
                     logger.info(f"Folder '{folder_name}' not found, creating it...")
                     create_folder_url = f"https://graph.microsoft.com/v1.0/me/drive/root/children"
                     folder_metadata = {
                         "name": folder_name,
                         "folder": {}
                     }
                     create_response = requests.post(create_folder_url, headers=headers, json=folder_metadata)
                     create_response.raise_for_status()
                     folder_id = create_response.json()['id']
                     logger.info(f"Created folder '{folder_name}' with ID: {folder_id}")

             except requests.exceptions.RequestException as e:
                  logger.error(f"Error finding/creating folder '{folder_path}': {e}. Uploading to root.")
                  folder_id = "root" # Fallback to root

    # 2. Upload the file
    filename = os.path.basename(file_path)
    # Using PUT /me/drive/items/{parent-id}:/{filename}:/content
    upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}:/{filename}:/content"

    headers = {
        'Authorization': f'Bearer {access_token}',
        # 'Content-Type' will be set automatically by requests based on the file
    }
    try:
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, headers=headers, data=f)
        response.raise_for_status()
        uploaded_file_info = response.json()
        logger.info(f"File uploaded successfully. ID: {uploaded_file_info.get('id')}, Name: {uploaded_file_info.get('name')}")
        return uploaded_file_info
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload file '{file_path}': {e}")
        # Print response text for more details on the error
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response text: {e.response.text}")
        return None

# --- Node Class ---

class ComfyUIOneDriveUploader:
    """
    A ComfyUI node to upload images to OneDrive and preview them.
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
                "filename_prefix": ("STRING", {"default": "OneDriveUpload"}),
                "onedrive_folder_path": ("STRING", {"default": "/ComfyUI Uploads"}), # Path like /MyFolder/SubFolder
                "authenticate": ("BOOLEAN", {"default": False}), # Button to trigger auth
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "process"
    OUTPUT_NODE = True
    CATEGORY = "image/upload"

    def process(self, images, filename_prefix="OneDriveUpload", onedrive_folder_path="/ComfyUI Uploads", authenticate=False, prompt=None, extra_pnginfo=None):
        """
        Processes images: saves locally, uploads to OneDrive, prepares preview.
        """
        logger.info("Starting OneDrive upload and preview process...")

        # --- Handle Authentication Trigger ---
        if authenticate:
            logger.info("Authentication trigger received.")
            auth_success = initiate_auth_flow()
            if not auth_success:
                 logger.error("Authentication failed or cancelled.")
                 # Return empty UI update on auth failure
                 return { "ui": { "images": [] } }

        # --- Get Access Token ---
        access_token = get_access_token()
        if not access_token:
            error_msg = "No valid access token available. Please authenticate first."
            logger.error(error_msg)
            # Return empty UI update if no token
            return { "ui": { "images": [] } }


        # --- Process and Upload Images ---
        results = [] # For UI preview
        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            # Note: Saving metadata like prompt is more complex with OneDrive API for direct content upload
            # It's often done via creating an upload session and then patching metadata afterwards.
            # For simplicity here, we focus on the image data upload.

            # Generate filename
            filename_with_batch_num = filename_prefix.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{batch_number:05}_{uuid.uuid4().hex[:8]}.png" # Add unique part
            local_file_path = os.path.join(self.output_dir, file)

            # Save locally first
            img.save(local_file_path, pnginfo=metadata, compress_level=self.compress_level)
            logger.info(f"Saved temporary image locally: {local_file_path}")

            # --- Upload to OneDrive ---
            uploaded_file_info = upload_to_onedrive(local_file_path, access_token, onedrive_folder_path)
            if uploaded_file_info:
                logger.info(f'Image uploaded successfully to OneDrive.')
                # Prepare UI update info for preview (standard for output nodes)
                # This tells ComfyUI frontend to display the image from the output directory
                results.append({
                    "filename": file,
                    "subfolder": "", # Assuming saved in main output dir
                    "type": self.type
                })
                # Optional: Delete the local temporary file after successful upload
                # os.remove(local_file_path)
                # logger.info(f"Deleted temporary local file: {local_file_path}")
            else:
                error_msg = f"Failed to upload image {file} to OneDrive."
                logger.error(error_msg)
                results.append({
                    "filename": file + "_FAILED",
                    "subfolder": "",
                    "type": self.type
                })

        # Return UI update info (enables preview in node)
        return { "ui": { "images": results } }

# Node Registration
NODE_CLASS_MAPPINGS = {
    "OneDriveUploader": ComfyUIOneDriveUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OneDriveUploader": "Upload to OneDrive"
}

# --- Initial Setup Check ---
# This could be placed in __init__.py instead
if not CLIENT_ID or not CLIENT_SECRET or CLIENT_ID == "YOUR_ONEDRIVE_APP_CLIENT_ID":
    logger.warning("OneDrive Client ID or Secret not configured. Please set ONEDRIVE_CLIENT_ID and ONEDRIVE_CLIENT_SECRET environment variables or update the node code.")
