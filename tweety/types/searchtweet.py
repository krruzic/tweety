import time
import urllib.parse
from typing import List, Optional

from tweety.http import RequestMaker
from tweety.types.n_types import SearchFilter

from . import Excel, Tweet, deprecated


class SearchTweets(dict):
    def __init__(
        self,
        query: str,
        search_filter: SearchFilter,
        http: RequestMaker,
        pages: int = 1,
        wait_time: int = 2,
        cursor: Optional[str] = None,
    ):
        super().__init__()
        self.tweets = []
        self.cursor = cursor
        self.is_next_page = True
        self.http = http
        self.query = query
        self.search_filter: SearchFilter = search_filter
        self.pages = pages
        self.wait_time = wait_time

    @staticmethod
    def _get_entries(response: dict) -> List[dict]:
        try:
            instructions = response["status"]["search_by_raw_query"]["search_timeline"][
                "timeline"
            ]["instructions"]
            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    return instruction["entries"]
        except KeyError:
            pass
        return response["statuses"]

    @staticmethod
    def _get_tweet_content_key(tweet: dict):
        return [tweet]

    def get_next_page(self):
        _tweets = []
        if self.is_next_page:
            response = self.http.get_search_tweets(
                self.query, search_filter=self.search_filter, cursor=self.cursor
            )
            entries = self._get_entries(response)

            for entry in entries:
                tweets = self._get_tweet_content_key(entry)
                for tweet in tweets:
                    try:
                        parsed = Tweet(response, tweet, self.http)
                        _tweets.append(parsed)
                        # yield parsed
                    except BaseException:
                        pass

            self.is_next_page = self._get_cursor(response)

            for tweet in _tweets:
                self.tweets.append(tweet)

            self["tweets"] = self.tweets
            self["is_next_page"] = self.is_next_page
            self["cursor"] = self.cursor
        return self, _tweets

    def generator(self):
        tweets = []
        for page in range(1, int(self.pages) + 1):
            _, new_tweets = self.get_next_page()
            tweets = tweets + new_tweets

            if self.is_next_page and page != self.pages:
                time.sleep(self.wait_time)
        yield self, tweets

    def _get_cursor(self, response: dict) -> bool:
        try:
            maybe_cursor = response["search_metadata"]["max_id"]
            if maybe_cursor != 0:
                new_cursor = str(maybe_cursor)
            else:
                new_cursor = (
                    response["search_metadata"]["next_results"]
                    .split("=")[1]
                    .split("&q")[0]
                )
            if new_cursor == self.cursor:
                return False
            self.cursor = new_cursor
            return True
        except KeyError:
            return False

    def to_xlsx(self):
        return Excel(self.tweets, urllib.parse.quote(self.query))

    def __getitem__(self, index: int) -> Tweet:
        return self.tweets[index]

    def __iter__(self):
        for __tweet in self.tweets:
            yield __tweet

    def __len__(self):
        return len(self.tweets)

    def __repr__(self):
        return f"SearchTweets(query={self.query}, search_filter={self.search_filter}, count={self.__len__()})"

    @deprecated
    def to_dict(self):
        return self.tweets
