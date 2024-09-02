import logging
import posixpath
import urllib
from typing import Dict

import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
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

    logger.info('%s, %s, %s, %s', data, method, headers, url)

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


def get_file_info(url: str):
    """Раздеяет URL на имя файла и расширение."""
    parse_obj = urllib.parse.urlparse(url)
    file_name = posixpath.basename(parse_obj.path)
    return posixpath.splitext(file_name)
