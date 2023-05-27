import os
from typing import Any, Optional, Union

import httpx as s
from tqdm import tqdm

from tweety.types.search import SearchFilter

from .builder import UrlBuilder
from .exceptions import (
    GuestTokenNotFound,
    InvalidCredentials,
    UnknownError,
    UserNotFound,
)
from .types.n_types import GenericError


class Request:
    def __init__(
        self,
        max_retries: int = 10,
        proxy: Optional[Any] = None,
    ):
        self.__session = s.Client(proxies=proxy, timeout=60)
        self.__builder = UrlBuilder(self.__session.cookies)
        self.__guest_token = self._get_guest_token(max_retries)

    def __get_response__(self, **request_data) -> Any:
        response = self.__session.request(**request_data)
        try:
            response_json = response.json()
        except BaseException:
            response_json = None

        if not response_json:
            raise UnknownError(
                error_code=500,
                error_name="Server Error",
                response=response,
                message="Unknown Error Occurs on Twitter",
            )

        if response_json.get("errors") and not response_json.get("data"):
            error = response_json["errors"][0]
            return GenericError(
                response, error.get("code"), error.get("message")
            )._raise_exception()

        return response_json

    def _get_guest_token(self, max_retries: int = 10):
        for retry in range(max_retries):
            response = self.__get_response__(**self.__builder.get_guest_token())

            token = self.__builder.guest_token = response["guest_token"]  # noqa
            return token

        raise GuestTokenNotFound(
            None,
            None,
            None,
            f"Guest Token couldn't be found after {max_retries} retries.",
        )

    def _init_api(self):
        data = self.__builder.init_api()
        data["json"] = {}
        self.__get_response__(**data)

    def get_user(self, username: str):
        response = self.__get_response__(**self.__builder.user_by_screen_name(username))

        if response.get("data"):  # noqa
            return response

        raise UserNotFound(
            error_code=50, error_name="GenericUserNotFound", response=response
        )

    def get_tweets(
        self, user_id: int, replies: bool = False, cursor: Optional[str] = None
    ):
        request_data = self.__builder.user_tweets(
            user_id=user_id, replies=replies, cursor=cursor
        )
        response = self.__get_response__(**request_data)
        return response

    def get_trends(self):
        response = self.__get_response__(**self.__builder.trends())
        return response

    def perform_search(
        self, query: str, cursor: Optional[str], search_type: SearchFilter = "Latest"
    ):
        response = self.__get_response__(
            **self.__builder.search(query, search_type, cursor)
        )
        return response

    def get_tweet_detail(self, tweet_id: int):
        response = self.__get_response__(**self.__builder.tweet_detail(tweet_id))
        return response

    def download_media(
        self, media_url: str, filename: Optional[str] = None, show_progress: bool = True
    ):
        filename = (
            os.path.basename(media_url).split("?")[0] if not filename else filename
        )

        with self.__session.stream("GET", media_url) as response:
            response.raise_for_status()
            content_length = int(response.headers["Content-Length"])
            f = open(filename, "wb")
            if show_progress:
                with tqdm(
                    total=content_length,
                    unit="B",
                    unit_scale=True,
                    desc=f"[{filename}]",
                ) as pbar:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            else:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
            f.close()

        return filename
