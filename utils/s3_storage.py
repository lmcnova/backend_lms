import os
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from typing import Optional, Tuple
from uuid import uuid4
import mimetypes


class S3Storage:
    """
    Utility class for handling S3 file uploads and management
    """

    def __init__(self):
        self.use_s3 = os.getenv("USE_S3", "false").lower() == "true"

        if self.use_s3:
            self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            self.aws_region = os.getenv("AWS_REGION", "us-east-1")
            self.bucket_name = os.getenv("S3_BUCKET_NAME")

            if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
                raise ValueError("AWS credentials and S3_BUCKET_NAME must be set when USE_S3=true")

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
        else:
            self.s3_client = None
            self.media_root = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "videos",
        custom_filename: Optional[str] = None
    ) -> Tuple[str, int, str]:
        """
        Upload file to S3 or local storage based on USE_S3 setting

        Args:
            file: The uploaded file
            folder: Folder/prefix for organizing files (e.g., "videos", "images", "thumbnails")
            custom_filename: Optional custom filename, otherwise uses original filename

        Returns:
            Tuple of (storage_key/url, file_size, mime_type)
        """
        # Get file details
        safe_name = os.path.basename(custom_filename or file.filename or "file")
        mime_type = file.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Reset file pointer for potential reuse
        await file.seek(0)

        if self.use_s3:
            # S3 upload
            unique_id = str(uuid4())
            s3_key = f"{folder}/{unique_id}/{safe_name}"

            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=mime_type,
                    # Make files private by default
                    ACL='private'
                )

                # Generate S3 URL
                s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"

                return s3_key, file_size, mime_type, s3_url

            except ClientError as e:
                raise Exception(f"Failed to upload to S3: {str(e)}")
        else:
            # Local storage
            unique_id = str(uuid4())
            rel_key = os.path.join(folder, unique_id, safe_name)
            abs_path = os.path.join(self.media_root, rel_key)

            # Ensure directory exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Save file
            with open(abs_path, "wb") as f:
                f.write(file_content)

            # For local storage, return the relative path (URL will be constructed by the endpoint)
            return rel_key.replace("\\", "/"), file_size, mime_type, None

    async def upload_video(
        self,
        file: UploadFile,
        video_uuid: str
    ) -> Tuple[str, int, str, Optional[str]]:
        """
        Upload video file

        Returns:
            Tuple of (storage_key, file_size, mime_type, s3_url)
        """
        safe_name = os.path.basename(file.filename or "video.mp4")
        return await self.upload_file(file, folder="videos", custom_filename=f"{video_uuid}/{safe_name}")

    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "images"
    ) -> Tuple[str, int, str, Optional[str]]:
        """
        Upload image file

        Returns:
            Tuple of (storage_key, file_size, mime_type, s3_url)
        """
        return await self.upload_file(file, folder=folder)

    async def upload_thumbnail(
        self,
        file: UploadFile,
        video_uuid: str
    ) -> Tuple[str, int, str, Optional[str]]:
        """
        Upload thumbnail image

        Returns:
            Tuple of (storage_key, file_size, mime_type, s3_url)
        """
        safe_name = os.path.basename(file.filename or "thumbnail.jpg")
        return await self.upload_file(file, folder="thumbnails", custom_filename=f"{video_uuid}/{safe_name}")

    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for private S3 objects

        Args:
            s3_key: The S3 key/path
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL or None if not using S3
        """
        if not self.use_s3:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3 or local storage

        Args:
            s3_key: The S3 key or local path

        Returns:
            True if deletion was successful
        """
        if self.use_s3:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                return True
            except ClientError as e:
                print(f"Error deleting from S3: {str(e)}")
                return False
        else:
            # Local storage deletion
            try:
                abs_path = os.path.join(self.media_root, s3_key)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    return True
                return False
            except Exception as e:
                print(f"Error deleting local file: {str(e)}")
                return False


# Singleton instance
_storage_instance = None

def get_s3_storage() -> S3Storage:
    """
    Get S3Storage singleton instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = S3Storage()
    return _storage_instance
