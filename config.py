from pydantic.v1 import BaseSettings


class UploadConfig(BaseSettings):
    chunk_size: int = 1024 * 1024
    session_timeout: int = 60
    retry_status: int = 5
    retry_delay: int = 1


cfg = UploadConfig()
