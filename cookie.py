# -*- coding:utf-8 -*-

import logging
import os
import time
import requests
from http.cookies import SimpleCookie
from utils import COMMON_HEADERS
from threading import Thread

logger = logging.getLogger(__name__)


class SunoCookie:
    """Клиент для работы с апи Suno."""

    def __init__(self, session_id: str, cookie_value: str):
        self.cookie = SimpleCookie()
        self.session_id = session_id
        self.token = None
        self.cookie_value = cookie_value
        self.load_cookie(self.cookie_value)

    def load_cookie(self, cookie_str):
        self.cookie.load(cookie_str)

    def get_cookie(self):
        return ";".join(
            [f"{i}={self.cookie.get(i).value}" for i in self.cookie.keys()]
        )

    def set_session_id(self, session_id):
        self.session_id = session_id

    def get_session_id(self):
        return self.session_id

    def get_token(self):
        return self.token

    def set_token(self, token: str):
        self.token = token

    def update_token(self):
        headers = {"cookie": self.get_cookie()}
        headers.update(COMMON_HEADERS)
        session_id = self.get_session_id()
        renew_url = (
            f"https://clerk.suno.ai/v1/client/sessions/{session_id}/"
            "tokens?_clerk_js_version=4.70.5"
        )

        resp = requests.post(
            url=renew_url,
            headers=headers
        )
        print(resp.json(), resp.headers)

        resp_headers = dict(resp.headers)
        set_cookie = resp_headers.get("Set-Cookie")
        self.load_cookie(set_cookie)
        token = resp.json().get("jwt")
        self.set_token(token)
        logger.info(f'Suno token updated -> {self.token}.')
        # print(set_cookie)
        # print(f"*** token -> {token} ***")
        return self.token


suno_auth = SunoCookie(
    session_id=os.getenv("SESSION_ID"), cookie_value=os.getenv("COOKIE")
)
# suno_auth.set_session_id(os.getenv("SESSION_ID"))
# suno_auth.load_cookie(os.getenv("COOKIE"))


def keep_alive(suno_cookie: SunoCookie):
    while True:
        try:
            suno_cookie.update_token()
        except Exception as e:
            logger.error(f'Error keep alive token {e}', exc_info=True)
        finally:
            time.sleep(5)


def start_keep_alive(suno_cookie: SunoCookie):
    t = Thread(target=keep_alive, args=(suno_cookie,))
    t.start()


# start_keep_alive(suno_auth)
