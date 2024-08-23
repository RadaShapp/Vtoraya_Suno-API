import asyncio
import logging
from typing import Dict
from fastapi.concurrency import run_in_threadpool
import aiohttp

from config import cfg
from execption import UploaderS3Error, UploaderGetStatusError, \
    UploaderFileExtensionError, IncorrectStream
from services.coverter import StreamLister
from utils import BASE_URL, fetch, get_file_info

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def stream_upload(url: str):
    """Скачивает файл чанками, используя стрим."""
    logger.info("Stream file data from %s", url)

    timeout = aiohttp.ClientTimeout(total=cfg.session_timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            async for chunk in resp.content.iter_chunked(cfg.chunk_size):
                yield chunk


async def speed_sender(stream_url: str, upload_url: str, credentials: dict):
    """Быстрая отправка файла без загрузки на сервер.

    Функция выполнят роль передатчика потока файла сразу на S3 сервер Suno.
    Читаем файл сразу в память, так при 48000HZ, 16.bit, 2stereo, 60s
    Не компрессированный файл занимает ~12МЬ.
    Можно улучшить: Получать и сразу передавать поток чанками, но aiohttp плохо
    поддерживает данный функционал. Лучше использовать httpx.

    Калькулятор размера аудиофайла:
    https://toolstud.io/video/audiosize.php ?samplerate=48000&sampledepth=16&channelcount=2&timeduration=60&timeunit=seconds

    """
    logger.info(
        "Stage_2: Upload on Amazone S3: stream_url=%s, upload_url=%s",
        stream_url,
        upload_url
    )
    logger.debug("credentails: %s", credentials)

    s3_headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/123.0.0.0 Safari/537.36'
        ),
        "Referer": "https://suno.com/",
        "Origin": "https://suno.com",
    }

    data = aiohttp.FormData()
    for k, v in credentials.items():
        data.add_field(k, v)

    stream_in = b''
    async for chunk in stream_upload(stream_url):
        stream_in += chunk

    stream_listener = StreamLister(stream_url)
    stream_out = await run_in_threadpool(stream_listener, stream_in)

    data.add_field('file', stream_out)

    async with aiohttp.ClientSession() as session:
        resp = await session.post(upload_url, data=data, headers=s3_headers)
        logger.info('Stage_2: post status: %s', resp.status)

    if resp.status != 204:
        logger.error("Stage_2: Response status %d", resp.status)
        raise UploaderS3Error('upload on S3 failed')


async def get_upload_status(upload_id: str, token: str):
    """Получает статус загрузки файла.

    Файл проходит несколько стадий проверки, в зависимости от стадии, можно в дальнейшем
    пробрасывать определенную ошибку;
    status:
    ["processing", "passed_artist_moderation", "complete", "error", "passed_audio_processing]

    """
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/{upload_id}"

    upload_status = None
    retry = cfg.retry_status
    delay = cfg.retry_delay
    while retry:
        resp = await fetch(api_url, headers, method="GET")
        upload_status = resp.get('status')
        if upload_status == 'complete':
            break

        logger.warning("Stage_4: upload status: %s", upload_status)

        retry -= 1
        await asyncio.sleep(delay)

    if upload_status != 'complete':
        logger.error("Stage_4: upload status: %s", upload_status)
        raise UploaderGetStatusError('Get upload status failed: %s', upload_status)

    logger.info('Stage_4: get_upload_status: %s', upload_status)


def init_upload_file(stream_url: str):
    """Изменят расширение файла."""
    f_name, ext = get_file_info(stream_url)
    ext = ext.strip(".")
    if ext not in cfg.file_ext:
        logger.error('Incorrect file extension: %s', ext)
        raise IncorrectStream('Incorrect file extension %s', ext)

    if ext in cfg.converted_audio_format:
        logger.info('file extension: %s -> %s', ext, cfg.default_audio_format)
        ext = cfg.default_audio_format
    return f_name, ext


async def get_s3_credentials(stream_url: str, token: str) -> Dict:
    """Инициирует загрузку в облачное хранилище.

    Функция получает загрузочные данные и url для загрузки в S3 хранилище.
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }
    f_name, ext = init_upload_file(stream_url)
    data = {"extension": ext}
    api_url = f"{BASE_URL}/api/uploads/audio/"

    logger.info("Stage_1: Getting S3 credentials: %s%s", f_name, ext)

    resp = await fetch(api_url, headers, data=data)
    if resp and resp.get('detail', '') == 'Unsupported file extension.':
        logger.error("Stage_1: Unsupported file extension: %s", ext)
        raise UploaderFileExtensionError('upload on S3 failed')
    return resp


async def finish_upload(stream_url: str, upload_id: str, token: str):
    """Сообщает что файл загружен в S3 хранилище."""
    logger.info('Finish upload started.')

    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/{upload_id}/upload-finish/"

    f_name = ''.join(get_file_info(stream_url))
    data = {
        "upload_type": "file_upload",
        "upload_filename": f_name,
    }

    resp = await fetch(api_url, headers, data)

    logger.info(
        'Stage_3: Finish upload, file: %s, ulpload_id: %s', f_name, upload_id)
    return resp


async def initialize_clip(upload_id: str, token: str):
    """Финализирует загрузку. Ответ содержит clip_id в сервисе Suno."""
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/{upload_id}/initialize-clip/"
    resp = await fetch(api_url, headers)
    logger.info("Stage_5: Initialize clip success, clip_id: %s", resp.get('clip_id'))
    return resp
