# -*- coding:utf-8 -*-
import uvicorn

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from utils import (
    generate_music, get_credits, get_feed, generate_lyrics, get_lyrics
)
from deps import get_token

import schemas
from services.uploader import speed_sender, get_upload_status, get_s3_credentials, \
    finish_upload, initialize_clip

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


@app.post("/uploads/")
async def uploads(stream_url: str, token: str = Depends(get_token)):
    # добавить обработку ошибок
    # добавить конветацию аудио ['m4r', 'ogg']

    try:
        print('1')
        resp = await get_s3_credentials(stream_url, token=token)  # init upload
        print('2')
        upload_id, upload_url, credentials = resp['id'], resp['url'], resp['fields']
        await speed_sender(stream_url, upload_url, credentials=credentials)  # upload
        print('3')
        await finish_upload(stream_url, upload_id, token=token)  # finish
        print('4')
        await get_upload_status(upload_id, token=token)  # get status upload
        print('5')
        return await initialize_clip(upload_id, token=token)  # initialize
        print('finish')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
        reload=True,
    )
