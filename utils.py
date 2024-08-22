import asyncio
import logging
import posixpath
import urllib

from typing import Dict

import os
import json
import aiohttp
from dotenv import load_dotenv

from config import cfg

load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL")

COMMON_HEADERS = {
    'Content-Type': 'application/json;charset=UTF-8',
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/123.0.0.0 Safari/537.36'
    ),
    "Referer": "https://suno.com/",
    "Origin": "https://suno.com",
}


async def fetch(url: str, headers=None, data=None, method="POST"):
    if headers is None:
        headers = {}
    headers.update(COMMON_HEADERS)
    if data is not None:
        data = json.dumps(data)

    logger.info(data, method, headers, url)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                    method=method, url=url, data=data, headers=headers
            ) as resp:
                return await resp.json()
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)


async def get_feed(ids, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    api_url = f"{BASE_URL}/api/feed/?ids={ids}"
    response = await fetch(api_url, headers, method="GET")
    return response


async def generate_music(data: Dict, token: str):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    api_url = f"{BASE_URL}/api/generate/v2/"
    response = await fetch(api_url, headers, data)
    return response


def get_file_info(url: str):
    parse_obj = urllib.parse.urlparse(url)
    file_name = posixpath.basename(parse_obj.path)
    return posixpath.splitext(file_name)


async def get_s3_credentials(stream_url: str, token: str) -> Dict:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    f_name, ext = get_file_info(stream_url)
    data = {"extension": ext.strip(".")}
    api_url = f"{BASE_URL}/api/uploads/audio/"
    logger.debug("Stage_1: Getting S3 credentials: %s%s", f_name, ext)
    return await fetch(api_url, headers, data)


async def finish_upload(stream_url: str, upload_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/{upload_id}/upload-finish/"

    data = {
        "upload_type": "file_upload",
        "upload_filename": get_file_info(stream_url)[0],
    }

    resp = await fetch(api_url, headers, data)
    print('get_upload_status response:', resp, api_url)
    return resp


async def get_upload_status(upload_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/{upload_id}"

    upload_status = None
    retry = cfg.retry_status
    delay = cfg.delay

    while retry:
        resp = await fetch(api_url, headers, method="GET")
        upload_status = resp.get('status')
        if upload_status == 'complete':
            break

        print(upload_status)
        retry -= 1
        await asyncio.sleep(delay)

    if upload_status != 'complete':
        raise Exception

    print('get_upload_status response:', resp, api_url)
    return resp


async def initialize_clip(upload_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/{upload_id}/initialize-clip/"
    resp = await fetch(api_url, headers)
    print('initialize_clip:', resp, api_url, upload_id)
    return resp


async def generate_lyrics(prompt, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    api_url = f"{BASE_URL}/api/generate/lyrics/"
    data = {"prompt": prompt}
    return await fetch(api_url, headers, data)


async def get_lyrics(lid, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    api_url = f"{BASE_URL}/api/generate/lyrics/{lid}"
    return await fetch(api_url, headers, method="GET")


async def custom_generate(
        prompt: str,
        tags: str,
        title: str,
        make_instrumental: bool = False,
        wait_audio: bool = False,
):
    """Настраиваемая генерация музыки."""
    pass


async def get_credits(token: str):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    api_url = f"{BASE_URL}/api/billing/info/"
    return await fetch(api_url, headers, method="GET")
