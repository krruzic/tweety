import functools
import re
from typing import Literal, Optional, Union

from .exceptions import *
from .http import Request
from .types.n_types import Proxy
from .types.search import Search
from .types.twDataTypes import Trends, Tweet, User
from .types.usertweet import UserTweets


def AuthRequired(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.user is None:
            raise AuthenticationRequired(200, "GenericForbidden", None)

        return f(self, *args, **kwargs)

    return wrapper


class Twitter:
    def __init__(
        self,
        max_retries: int = 10,
        proxy: Optional[Union[dict, Proxy]] = None,
    ):
        """
        Constructor of the Twitter Public class

        :param max_retries: (`int`) Number of retries the script would make , if the guest token wasn't found
        :param proxy: (`dict` or `Proxy`) Provide the proxy you want to use while making a request
        """

        self.request = Request(max_retries=max_retries, proxy=proxy)

    def get_user_info(
        self,
        username: str,
        banner_extensions: bool = False,
        image_extensions: bool = False,
    ):
        """
        Get the User Info of the specified username

        :param username: (`str`) username to get information of
        :param banner_extensions: (`boolean`) Get the Banner extension on the user page
        :param image_extensions: (`boolean`) Get the Image extension on the user page

        :return: .types.twDataTypes.User
        """

        user_raw = self.request.get_user(username)

        if not banner_extensions or banner_extensions is False:
            try:
                del user_raw["data"]["user"]["result"]["legacy"][
                    "profile_banner_extensions"
                ]
            except KeyError:
                pass

        if not image_extensions or image_extensions is False:
            try:
                del user_raw["data"]["user"]["result"]["legacy"][
                    "profile_image_extensions"
                ]
            except KeyError:
                pass

        return User(user_raw["data"]["user"]["result"])

    def _get_user_id(
        self,
        username: Union[str, int, User],
    ):
        if isinstance(username, User):
            user_id = username.rest_id
        elif isinstance(username, int):
            user_id = username
        elif isinstance(username, str) and str(username).isdigit():
            user_id = int(username)
        else:
            user_id = self.get_user_info(username).rest_id

        return user_id

    def get_tweets(
        self,
        username: Union[str, int, User],
        pages: int = 1,
        replies: bool = False,
        wait_time: int = 2,
        cursor: Optional[str] = None,
    ):
        """
         Get the tweets from a user

        :param: username: (`str` | `int` | `User`) username of the user whom to get the tweets of
        :param: pages: (`int`) number of pages to be scraped
        :param: replies: (`boolean`) get the replied tweets of the user too
        :param: wait_time: (`int`) seconds to wait between multiple requests
        :param: cursor: Pagination cursor if you want to get the pages
                        from that cursor up-to (This cursor is different from actual API cursor)

        :return: .types.usertweet.UserTweets
        """
        if wait_time is None:
            wait_time = 0

        user_id = self._get_user_id(username)

        userTweets = UserTweets(
            user_id, self.request, pages, replies, wait_time, cursor
        )

        # TODO : Find proper way to run the generator
        results = [i for i in userTweets.generator()]

        return userTweets

    def iter_tweets(
        self,
        username: Union[str, int, User],
        pages: int = 1,
        replies: bool = False,
        wait_time: int = 2,
        cursor: Optional[str] = None,
    ):
        """
         Generator for getting the tweets from a user

        :param: username: (`str` | `int` | `User`) username of the user whom to get the tweets of
        :param: pages: (`int`) number of pages to be scraped
        :param: replies: (`boolean`) get the replied tweets of the user too
        :param: wait_time: (`int`) seconds to wait between multiple requests
        :param: cursor: Pagination cursor if you want to get the pages from that cursor up-to (This cursor is different from actual API cursor)

        :return: (.types.usertweet.UserTweets, list[.types.twDataTypes.Tweet])
        """
        if wait_time is None:
            wait_time = 0

        user_id = self._get_user_id(username)

        userTweets = UserTweets(
            user_id, self.request, pages, replies, wait_time, cursor
        )

        return userTweets.generator()

    def get_trends(self):
        """
        Get the Trends from you locale

        :return:list of .types.twDataTypes.Trends
        """
        trends = []
        response = self.request.get_trends()
        for i in response.json()["timeline"]["instructions"][1]["addEntries"][
            "entries"
        ][1]["content"]["timelineModule"]["items"]:
            data = {
                "name": i["item"]["content"]["trend"]["name"],
                "url": str(i["item"]["content"]["trend"]["url"]["url"])
                .replace("twitter://", "https://twitter.com/")
                .replace("query", "q"),
            }
            try:
                if i["item"]["content"]["trend"]["trendMetadata"]["metaDescription"]:
                    data["tweet_count"] = i["item"]["content"]["trend"][
                        "trendMetadata"
                    ]["metaDescription"]
            except BaseException:
                pass
            trends.append(Trends(data))
        return trends

    def search(
        self,
        query: str,
        pages: int = 1,
        search_type: Literal["Latest", "users", "photos", "videos"] = "Latest",
        wait_time: int = 2,
        cursor: Optional[str] = None,
    ):
        """
        Search for a keyword or hashtag on Twitter

        :param query: (`str`) The keyword which is supposed to be searched
        :param pages: (`int`) The number of pages to get
        :param search_type: (`str`) The type of search to perform (Latest,user,photos,videos)
        :param wait_time : (`int`) seconds to wait between multiple requests
        :param cursor: (`str`) Pagination cursor if you want to get the pages from that cursor up-to (This cursor is different from actual API cursor)


        :return: list[.types.twDataTypes.Tweet]
        """
        response = self.request.perform_search(query, cursor, search_type)
        tweets = []
        for i in response["data"]["search_by_raw_query"]["search_timeline"]["timeline"][
            "instructions"
        ][0]["entries"]:
            if "itemContent" not in i["content"]:
                continue
            tweet_data = i["content"]["itemContent"]["tweet_results"]["result"]
            tweets.append(Tweet(response, tweet_data, self.request))
        return tweets

    def tweet_detail(self, identifier: str):
        """
        Get Detail of a single tweet

        :param identifier: (`str`) The unique identifier of the tweet , either the `Tweet id` or `Tweet Link`

        :return: .types.twDataTypes.Tweet
        """

        tweet_id = re.findall(r"\d+", identifier)[0]

        r = self.request.get_tweet_detail(tweet_id)

        try:
            for entry in r["data"]["threaded_conversation_with_injections_v2"][
                "instructions"
            ][0]["entries"]:
                if str(entry["entryId"]).split("-")[0] == "tweet":
                    raw_tweet = entry["content"]["itemContent"]["tweet_results"][
                        "result"
                    ]

                    if raw_tweet["rest_id"] == str(tweet_id):
                        return Tweet(r, raw_tweet, self.request, True, False, True)

        except KeyError:
            raise InvalidTweetIdentifier(144, "StatusNotFound", r)
