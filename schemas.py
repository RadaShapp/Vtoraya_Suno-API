# -*- coding:utf-8 -*-

from typing import Any, Optional
from pydantic import BaseModel


class Response(BaseModel):
    code: Optional[int] = 0
    msg: Optional[str] = "success"
    data: Optional[Any] = None


class GenerateBase(BaseModel):
    prompt: str
    title: str
    tags: str
    mv: str = "chirp-v3-0"
    continue_at: Optional[str] = None
    continue_clip_id: Optional[str] = None
    wait_audio: bool = False
    make_instrumental: bool = False
    gpt_description_prompt: str = None
