import io
import logging

import pydub
from pydub.exceptions import PydubException

from config import cfg
from execption import IncorrectStream
from services.uploader import get_file_info

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StreamLister:
    """Проверяет аудио поток в памяти.

    Читает длительность файла. Конвертирует аудио файл в допустимый формат
    """
    _segment = pydub.AudioSegment

    def __init__(self, upload_id: str):
        self.file_ext = get_file_info(upload_id)[1].strip('.')
        self.file_name = get_file_info(upload_id)[0]

    def create_audio(self, stream: bytes):
        """Инициализирует аудио сегмент."""
        file = io.BytesIO(stream)
        try:
            audio = self._segment.from_file(file, file_ext=self.file_ext)
        except PydubException as exc:
            logger.error('Init converter filed.',str(exc))
            raise from exc

        return audio

    @staticmethod
    def ogg2wav(segment: pydub.AudioSegment) -> bytes:
        """Конвертирует файл в поддерживаемый формат."""
        logger.debug("Converting ogg to %s", cfg.default_audio_format)
        stream_out = io.BytesIO()
        segment.export(stream_out, format=cfg.default_audio_format)
        stream_out.seek(0)
        return stream_out.read()

    @staticmethod
    def check_duration(segment: pydub.AudioSegment) -> bool:
        """Проверяет длительность аудио."""
        if not (
                cfg.min_audio_duration <= segment.duration_seconds <= cfg.max_audio_duration):
            return False

        return True

    def __call__(self, stream: bytes):

        file_name = self.file_name + self.file_ext

        logger.info("Lisen stream started for %s", file_name)

        if self.file_ext not in cfg.file_ext:
            logger.error("Invalid file extension: %s", file_name)
            raise IncorrectStream

        audio_in = self.create_audio(stream)

        if self.check_duration(audio_in):
            logger.error("Duration check failed: %s",
                         self.file_name + self.file_ext)
            raise IncorrectStream

        if self.file_ext == cfg.converted_audio_format:
            return self.ogg2wav(audio_in)

        return stream
