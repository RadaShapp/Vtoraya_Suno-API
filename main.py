# -*- coding:utf-8 -*-
import aiohttp
import uvicorn

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from config import cfg
from utils import (
    generate_music, get_credits, get_feed, generate_lyrics, get_lyrics,
    get_s3_credentials, finish_upload, get_upload_status, initialize_clip
)
from deps import get_token

import schemas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_root():
    return schemas.Response()


@app.get("/uploads/{upload_id}")
async def get_upload_by_id(upload_id: str, token: str = Depends(get_token)):
    try:
        resp = await get_upload_status(upload_id, token)
        return resp
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def stream_upload(url: str):
    print('stream uploader', url)
    timeout = aiohttp.ClientTimeout(total=cfg.session_timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            print(cfg.chunk_size)
            async for chunk in resp.content.iter_chunked(cfg.chunk_size):
                # print(chunk)
                yield chunk


async def speed_sender(stream_url: str, upload_url: str, credentials: dict):
    print('stream_url', stream_url)
    print('upload_url', upload_url)

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

    file = b''
    async for chunk in stream_upload(stream_url):
        file += chunk
    data.add_field('file', file)

    async with aiohttp.ClientSession() as session:
        resp = await session.post(upload_url, data=data, headers=s3_headers)
        print(resp)
        print(resp.status)
    if resp.status == 204:
        return True

    return False


@app.post("/uploads/")
async def uploads(stream_url: str, token: str = Depends(get_token)):
    # Добавить обработку ошибок
    try:
        resp = await get_s3_credentials(stream_url, token=token)  # init upload
        upload_id, upload_url, credentials = resp['id'], resp['url'], resp['fields']
        await speed_sender(stream_url, upload_url, credentials=credentials) # upload
        await finish_upload(stream_url, upload_id=upload_id, token=token)  # finish
        resp = await initialize_clip(upload_id=upload_id, token=token)  # initialize
        return resp
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# @app.post("/uploads")
# async def uploads(image: UploadFile = File(...), token: str = Depends(get_token)):
#     print(image, type(image))
#     print(image.file)
#
#     # get credentials
#     file_ext = "mp3"
#     payload = {"extension": file_ext}
#     try:
#         resp = await get_s3_credentials(data=payload, token=token)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )
#
#     # upload on s3 cloud
#     print(resp, type(resp))
#     upload_id = resp.get("id")
#     url = resp.get("url")
#     print("url:", url)
#
#     print("upload_id:", upload_id)
#     payload = dict(resp.get("fields"))
#     payload['file'] = await image.read()
#
#     try:
#         is_uploaded = await upload_to_s3(url, form_data=payload)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )
#
#     print("is_uploaded", is_uploaded)
#
#     # finish upload
#     payload = {
#         "upload_type": "file_upload",
#         "upload_filename": image.filename
#     }
#     try:
#         resp = await finish_upload(data=payload, upload_id=upload_id, token=token)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )
#
#     print('finish upload:', resp)
#
#     # get status
#     retry = 5
#     upload_status = None
#     while retry:
#         try:
#             resp = await get_upload_status(upload_id=upload_id, token=token)
#             upload_status = resp.get("status")
#             if upload_status == 'complete':
#                 break
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=str(e)
#             )
#
#         print(upload_status)
#         retry -= 1
#         await asyncio.sleep(1)
#
#     if upload_status != 'complete':
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=upload_status
#         )
#
#     print('get_status:', resp)
#
#     # Initialize clip
#     try:
#         resp = await initialize_clip(upload_id=upload_id, token=token)
#         return resp
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )


@app.post("/generate")
async def generate(
        data: schemas.GenerateBase, token: str = Depends(get_token)
):
    try:
        resp = await generate_music(data.dict(), token)
        return resp
    except Exception as e:
        raise HTTPException(
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/feed/{aid}")
async def fetch_feed(aid: str, token: str = Depends(get_token)):
    try:
        resp = await get_feed(aid, token)
        return resp
    except Exception as e:
        raise HTTPException(
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.post("/generate/lyrics/")
async def generate_lyrics_post(
        request: Request, token: str = Depends(get_token)
):
    req = await request.json()
    prompt = req.get("prompt")
    if prompt is None:
        raise HTTPException(
            detail="prompt is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        resp = await generate_lyrics(prompt, token)
        return resp
    except Exception as e:
        raise HTTPException(
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/lyrics/{lid}")
async def fetch_lyrics(lid: str, token: str = Depends(get_token)):
    try:
        resp = await get_lyrics(lid, token)
        return resp
    except Exception as e:
        raise HTTPException(
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/get_credits")
async def get_limits(token: str = Depends(get_token)):
    try:
        resp = await get_credits(token)
        return resp
    except Exception as e:
        raise HTTPException(
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


if __name__ == "__main__":
    uvicorn.run(
        app='main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
