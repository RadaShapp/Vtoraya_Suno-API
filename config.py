from pydantic.v1 import BaseSettings


class UploadConfig(BaseSettings):
    chunk_size: int = 1024 * 1024
    session_timeout: int = 60
    retry_status: int = 10
    retry_delay: int = 2

    min_audio_duration: int = 5
    max_audio_duration: int = 60
    file_ext: list = ['wav', 'mp3', 'ogg', 'oga']
    default_audio_format = 'wav'
    converted_audio_format = 'oga'


cfg = UploadConfig()
