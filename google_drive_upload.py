# 保留原有导入（省略，包括google API、PIL、torch等）
import os
import io
from PIL import Image
import torch
from google.oauth2.credentials import Credentials
# ... 其他原有导入


# 原有图片上传节点和视频节点保持不变...


class GoogleDriveUploadWithPreviewNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图片
                "folder_id": ("STRING", {"default": ""}),  # 目标文件夹ID
                "file_name": ("STRING", {"default": "comfyui_preview_output"}),  # 文件名
            }
        }
    
    # 关键：返回图片数据用于预览，同时返回上传状态
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("preview_image", "status")
    FUNCTION = "upload_with_preview"
    CATEGORY = "Custom/Upload"

    def upload_with_preview(self, image, folder_id, file_name):
        try:
            # 1. 先保存原始图片数据（用于预览返回）
            preview_image = image  # 直接复用输入的IMAGE数据，ComfyUI会自动渲染
            
            # 2. 处理图片并上传（逻辑与原有图片节点一致）
            img = image[0].cpu().numpy()
            img = (img * 255).astype("uint8")
            pil_img = Image.fromarray(img)
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            # 3. Google Drive授权（复用已有逻辑）
            creds = None
            creds_path = os.path.expanduser("~/.comfyui_googledrive_creds.json")
            if os.path.exists(creds_path):
                creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
            
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secret.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open(creds_path, "w") as f:
                    f.write(creds.to_json())

            # 4. 上传文件
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': f"{file_name}.png",
                'mimeType': 'image/png'
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaIoBaseUpload(img_byte_arr, mimetype='image/png')
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # 返回预览图片和成功状态
            return (preview_image, f"Success (with preview): File ID {file.get('id')}")
        
        except Exception as e:
            # 即使上传失败，仍返回预览图方便排查
            return (image, f"Error (preview available): {str(e)}")


# 更新节点注册，加入带预览的节点
NODE_CLASS_MAPPINGS = {
    "GoogleDriveUpload": GoogleDriveUploadNode,
    "GoogleDriveVideoUpload": GoogleDriveVideoUploadNode,
    "GoogleDriveUploadWithPreview": GoogleDriveUploadWithPreviewNode  # 新增预览节点
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleDriveUpload": "Google Drive Image Upload",
    "GoogleDriveVideoUpload": "Google Drive Video Upload",
    "GoogleDriveUploadWithPreview": "Google Drive Image Upload (with Preview)"  # 显示名称
}
