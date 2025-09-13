import os
import io
import tempfile
from PIL import Image
import torch
import numpy as np
# 新增视频处理相关依赖
import cv2
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload

# 原有图片上传节点保持不变...（省略，见上一次的GoogleDriveUploadNode）

# Google Drive API权限（仅需上传文件的权限）
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveUploadNode:
    # 节点信息（ComfyUI显示用）
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # 输入ComfyUI生成的图片
                "folder_id": ("STRING", {"default": ""}),  # Google Drive目标文件夹ID（可选）
                "file_name": ("STRING", {"default": "comfyui_output"}),  # 文件名
            }
        }
    
    # 输出类型（这里仅返回状态，无实际输出）
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "upload_to_drive"
    CATEGORY = "Custom/Upload"  # 节点在ComfyUI中的分类

    def upload_to_drive(self, image, folder_id, file_name):
        try:
            # 1. 处理图片：将ComfyUI的tensor格式转为PIL图片并保存到内存
            img = image[0].cpu().numpy()  # 取第一帧（如果是批量生成）
            img = (img * 255).astype("uint8")
            pil_img = Image.fromarray(img)
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')  # 保存为PNG格式
            img_byte_arr.seek(0)  # 重置文件指针

            # 2. Google Drive授权：优先读取已保存的凭证，无则生成
            creds = None
            # 凭证保存路径（用户目录下，避免权限问题）
            creds_path = os.path.expanduser("~/.comfyui_googledrive_creds.json")
            if os.path.exists(creds_path):
                creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
            
            # 如果凭证无效或不存在，引导用户授权（会自动打开浏览器）
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secret.json", SCOPES  # 需要用户下载的客户端密钥
                )
                creds = flow.run_local_server(port=0)
                # 保存凭证，下次无需重复授权
                with open(creds_path, "w") as f:
                    f.write(creds.to_json())

            # 3. 上传文件到Google Drive
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': f"{file_name}.png",
                'mimeType': 'image/png'
            }
            # 如果指定了文件夹ID，设置父目录
            if folder_id:
                file_metadata['parents'] = [folder_id]

            # 上传媒体内容
            media = MediaIoBaseUpload(img_byte_arr, mimetype='image/png')
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return (f"Success: File ID {file.get('id')}",)
        
        except HttpError as e:
            return (f"HTTP Error: {str(e)}",)
        except Exception as e:
            return (f"Error: {str(e)}",)

# 注册节点到ComfyUI
NODE_CLASS_MAPPINGS = {
    "GoogleDriveUpload": GoogleDriveUploadNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleDriveUpload": "Google Drive Upload"
}

class GoogleDriveVideoUploadNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_frames": ("IMAGE",),  # 输入视频帧序列（ComfyUI生成的帧列表）
                "fps": ("INT", {"default": 24, "min": 1, "max": 60}),  # 视频帧率
                "folder_id": ("STRING", {"default": ""}),  # 目标文件夹ID
                "file_name": ("STRING", {"default": "comfyui_video_output"}),  # 视频文件名
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "upload_video_to_drive"
    CATEGORY = "Custom/Upload"

    def upload_video_to_drive(self, video_frames, fps, folder_id, file_name):
        try:
            # 1. 将视频帧序列（IMAGE类型）转换为临时MP4文件
            # 获取帧尺寸（从第一帧获取）
            first_frame = video_frames[0].cpu().numpy()
            height, width = first_frame.shape[:2]
            # 创建临时文件保存视频
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 使用OpenCV写入视频
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4编码
            out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
            
            for frame in video_frames:
                # 转换帧格式：tensor -> numpy -> BGR（OpenCV默认格式）
                frame_np = frame.cpu().numpy()
                frame_np = (frame_np * 255).astype(np.uint8)
                frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)  # 转换为BGR
                out.write(frame_bgr)
            
            out.release()  # 释放资源

            # 2. Google Drive授权（复用图片节点的授权逻辑）
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

            # 3. 上传视频文件到Google Drive
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': f"{file_name}.mp4",
                'mimeType': 'video/mp4'
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]

            # 视频文件较大，使用文件路径上传（而非内存）
            media = MediaFileUpload(temp_path, mimetype='video/mp4')
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # 清理临时文件
            os.unlink(temp_path)

            return (f"Video Success: File ID {file.get('id')}",)
        
        except HttpError as e:
            return (f"Video HTTP Error: {str(e)}",)
        except Exception as e:
            return (f"Video Error: {str(e)}",)


# 更新节点注册，加入视频节点
NODE_CLASS_MAPPINGS = {
    "GoogleDriveUpload": GoogleDriveUploadNode,
    "GoogleDriveVideoUpload": GoogleDriveVideoUploadNode  # 新增视频节点
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "GoogleDriveUpload": "Google Drive Image Upload",
    "GoogleDriveVideoUpload": "Google Drive Video Upload"  # 显示名称
}


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
